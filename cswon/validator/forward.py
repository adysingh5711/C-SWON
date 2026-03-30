# C-SWON Validator — Forward Pass (v2)
# Implements the six-stage evaluation pipeline (readme §4.8).
# v2 additions:
#   - Synthetic task injection (15–20%) — readme §2.5 / issue 1.4
#   - Temporal consistency checks + audit flags — readme §2.5 / issue 1.5
#   - routing_policy passed through to executor — readme §3.3 / issue 1.3
#   - Monitoring server for audit flags — readme §3.6 / issue 3.6

"""
Validator forward pass: the main loop that runs every step.

Six-stage pipeline:
1. Deterministic task selection (VRF-keyed) + optional synthetic injection
2. Miner workflow collection (async query)
3. Sandboxed execution (executor — async parallel tiers)
4. Output quality evaluation (deterministic, no LLM judge)
5. Composite scoring (four-dimension formula)
6. Rolling window update + temporal consistency + lifecycle tracking + N_min logging
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional
import json
import random

import bittensor as bt
import numpy as np

from cswon.protocol import WorkflowSynapse
from cswon.validator.config import (
    SCORING_VERSION,
    QUERY_TIMEOUT_S,
    TEMPO,
    EXEC_SUPPORT_N_MIN,
)
from cswon.validator.miner_selection import (
    load_benchmark_tasks,
    select_task_for_block,
    select_miners_for_query,
)
from cswon.validator.query_loop import query_miners, validate_response
from cswon.validator.executor import execute_workflow_async
from cswon.validator.reward import (
    score_output_quality,
    compute_composite_score,
    get_miner_weight,
)
from cswon.validator.benchmark_lifecycle import BenchmarkLifecycleTracker


# ── Synthetic Task Injection Constants (readme §2.5, issue 1.4) ──────────────

# 15–20% of tasks should be synthetic; use midpoint 17.5%
SYNTHETIC_INJECTION_RATE = 0.175


import hashlib
import copy
import os

# Secret salt — set via env var, never hardcoded in repo
_SYNTHETIC_SALT = os.environ.get("CSWON_SYNTHETIC_SALT", "")

if not _SYNTHETIC_SALT:
    _is_mock_mode = os.environ.get("CSWON_MOCK_EXEC", "true").lower() == "true"
    _network = os.environ.get("CSWON_NETWORK", "local")
    if not _is_mock_mode:
        raise RuntimeError(
            "\n\nCRITICAL: CSWON_SYNTHETIC_SALT env var is not set.\n"
            "Running a live validator without a secret salt means miners can\n"
            "pre-identify synthetic tasks by replicating the derivation logic.\n\n"
            "Generate a secret salt with:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n\n"
            "Then set it in your environment:\n"
            "  export CSWON_SYNTHETIC_SALT=<your-secret-value>\n"
        )
    elif _network == "test":
        raise RuntimeError(
            "\n\nCRITICAL: CSWON_SYNTHETIC_SALT env var is not set.\n"
            "Testnet validators require a persistent salt for consistent\n"
            "synthetic task derivation across restarts and validators.\n\n"
            "Generate a secret salt with:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n\n"
            "Then set it in your environment:\n"
            "  export CSWON_SYNTHETIC_SALT=<your-secret-value>\n"
        )
    else:
        # Local devnet: ephemeral salt is acceptable
        import secrets as _secrets
        _SYNTHETIC_SALT = _secrets.token_hex(32)
        bt.logging.warning(
            "CSWON_SYNTHETIC_SALT not set — using ephemeral random salt for this "
            "local devnet session. Set the env var for stable cross-restart behavior."
        )

# ── Temporal Consistency Constants (readme §2.5, issue 1.5) ─────────────────

# A jump of >50% from the rolling average triggers an audit flag
TEMPORAL_JUMP_THRESHOLD = 0.50
# Minimum observations before we flag a jump (avoid false positives on new miners)
TEMPORAL_AUDIT_WINDOW = 3


# ── Module-level state ───────────────────────────────────────────────────────

_benchmark_cache = None
_synthetic_cache: List[dict] = []

_tasks_executed_this_tempo: int = 0
_last_lifecycle_tempo: int = -1

# uid -> deque of recent scores (for temporal consistency, issue 1.5)
_score_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))

# Audit flag log (issue 3.6) — kept in memory, exposed via HTTP
_AUDIT_FLAG_MAX = 500  # cap in-memory list
_audit_flags: deque = deque(maxlen=_AUDIT_FLAG_MAX)
_audit_flags_lock = threading.Lock()


# ── Monitoring HTTP Server (readme §3.6, issue 3.6) ────────────────────────

class _AuditHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/audit-flags":
            with _audit_flags_lock:
                body = json.dumps(list(_audit_flags)[-100:]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # suppress default HTTP logging


def _start_monitoring_server(port: int = 9090) -> None:
    """Start the audit flag monitoring server in a background daemon thread."""
    try:
        server = HTTPServer(("127.0.0.1", port), _AuditHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        bt.logging.info(f"Audit monitoring endpoint started: http://0.0.0.0:{port}/audit-flags")
    except OSError as e:
        bt.logging.warning(f"Could not start monitoring server on port {port}: {e}")


# Start monitoring server at module import (runs once)
_monitoring_started = False


def _ensure_monitoring_server() -> None:
    global _monitoring_started
    if not _monitoring_started:
        _start_monitoring_server()
        _monitoring_started = True


def _get_effective_tempo(self) -> int:
    """
    Use the live subnet tempo when available and fall back to the static config.
    This keeps local-chain tempo-boundary logic aligned with the actual chain.
    """
    current_block = int(self.block)
    cached_block = getattr(self, "_cached_tempo_block", -1)
    cached_tempo = getattr(self, "_cached_tempo_value", None)
    if cached_tempo is not None and cached_block == current_block:
        return cached_tempo

    try:
        params = self.subtensor.get_subnet_hyperparameters(self.config.netuid)
        tempo = int(getattr(params, "tempo", TEMPO) or TEMPO)
    except Exception as e:
        bt.logging.debug(f"Falling back to static tempo={TEMPO}: {e}")
        tempo = TEMPO

    tempo = max(1, tempo)
    self._cached_tempo_value = tempo
    self._cached_tempo_block = current_block
    return tempo


# ── Cache helpers ────────────────────────────────────────────────────────────

def _get_benchmark_tasks() -> List[dict]:
    """Load and cache active (non-synthetic) benchmark tasks."""
    global _benchmark_cache, _synthetic_cache
    if _benchmark_cache is None:
        all_tasks = load_benchmark_tasks()
        _synthetic_cache = [t for t in all_tasks if t.get("type") == "synthetic"]
        _benchmark_cache = [t for t in all_tasks if t.get("type") != "synthetic"]
        bt.logging.info(
            f"Benchmark cache: {len(_benchmark_cache)} real tasks, "
            f"{len(_synthetic_cache)} synthetic tasks"
        )
    return _benchmark_cache


# ── Synthetic Injection (readme §2.5, issue 1.4) ─────────────────────────────

def _generate_synthetic_task(validator_hotkey: str, block: int, real_task: dict) -> dict:
    """
    Derive a synthetic variant of a real task at runtime using a secret salt.
    The salt is known only to validators, so miners cannot identify synthetic tasks
    by task_id pattern-matching.
    """
    seed = f"{_SYNTHETIC_SALT}:{validator_hotkey}:{block}".encode()
    h = hashlib.sha256(seed).hexdigest()[:8]
    synthetic = copy.deepcopy(real_task)
    # Mutate task_id so it's unique but non-guessable
    synthetic["task_id"] = f"syn_{h}"
    synthetic["type"] = "synthetic"
    # Constraints: tighten slightly to stress-test miners
    constraints = synthetic.get("constraints", {})
    synthetic["constraints"] = {
        **constraints,
        "max_budget_tao": constraints.get("max_budget_tao", 0.02) * 0.85,
        "max_latency_seconds": constraints.get("max_latency_seconds", 15) * 0.85,
    }
    return synthetic


def _maybe_inject_synthetic(task: dict, validator_hotkey: str, block: int) -> dict:
    if random.random() < SYNTHETIC_INJECTION_RATE:
        synthetic = _generate_synthetic_task(validator_hotkey, block, task)
        bt.logging.debug(f"Synthetic injection: real={task.get('task_id')} → synthetic={synthetic['task_id']}")
        return synthetic
    return task


# ── Temporal Consistency Check (readme §2.5, issue 1.5) ──────────────────────

def _check_temporal_consistency(uid: int, score: float, current_block: int) -> None:
    """
    Compare a miner's new score against its rolling history.
    Flag sudden unexplained performance jumps for manual audit (readme §2.5).

    Args:
        uid: Miner UID.
        score: Current composite score.
        current_block: Current chain block height.
    """
    history = _score_history[uid]

    if len(history) >= TEMPORAL_AUDIT_WINDOW:
        prev_avg = sum(history) / len(history)
        jump = score - prev_avg
        if jump > TEMPORAL_JUMP_THRESHOLD:
            flag = {
                "uid":          uid,
                "block":        current_block,
                "score":        round(score, 4),
                "prev_avg":     round(prev_avg, 4),
                "jump":         round(jump, 4),
                "message":      (
                    f"TEMPORAL_AUDIT_FLAG uid={uid}: score={score:.3f} jumped "
                    f"+{jump:.3f} from rolling_avg={prev_avg:.3f} over "
                    f"{len(history)} observations. Manual review recommended."
                ),
            }
            bt.logging.warning(flag["message"])
            with _audit_flags_lock:
                _audit_flags.append(flag)
                # deque(maxlen=500) evicts oldest automatically — no pop(0) needed

    history.append(score)


# ── Forward pass ─────────────────────────────────────────────────────────────

async def forward(self):
    """
    Validator forward pass — six-stage evaluation pipeline (readme §4.8).

    Args:
        self: The validator neuron instance.
    """
    global _tasks_executed_this_tempo, _last_lifecycle_tempo

    _ensure_monitoring_server()

    benchmark_tasks = _get_benchmark_tasks()
    tracker = self.lifecycle_tracker

    # ── Stage 1: Deterministic task selection ────────────────────────────────
    if not benchmark_tasks:
        bt.logging.warning("No benchmark tasks loaded, skipping forward pass")
        time.sleep(5)
        return

    task = select_task_for_block(
        validator_hotkey=self.wallet.hotkey.ss58_address,
        current_block=self.block,
        benchmark_tasks=benchmark_tasks,
    )

    if task is None:
        bt.logging.warning("No task selected for this block, skipping")
        time.sleep(5)
        return

    # Synthetic injection (issue 1.4) — must happen AFTER VRF so miners
    # see the same task_id in the synapse but the validator scores against
    # the known ground truth.
    task = _maybe_inject_synthetic(task, self.wallet.hotkey.ss58_address, self.block)

    task_id   = task.get("task_id", "unknown")
    task_type = task.get("task_type", "unknown")
    is_synthetic = task.get("type") == "synthetic"
    bt.logging.info(
        f"Selected task: {task_id} type={task_type} "
        f"synthetic={is_synthetic} at block {self.block}"
    )

    # ── Stage 2: Miner workflow collection ───────────────────────────────────
    miner_uids = select_miners_for_query(
        metagraph=self.metagraph,
        k=self.config.neuron.sample_size,
        exclude=[self.uid],
        min_stake_tao=0.0 if self.config.subtensor.network == "local" else 1.0,
        subtensor=self.subtensor,           # ← chain immunity lookup (fix 2.5)
        netuid=self.config.netuid,           # ← chain immunity lookup (fix 2.5)
        current_block=self.block,            # ← chain immunity lookup (fix 2.5)
        subnet_launch_block=getattr(self, "subnet_launch_block", None),
    )

    if len(miner_uids) == 0:
        bt.logging.warning("No miners available to query")
        time.sleep(5)
        return

    synapse = WorkflowSynapse(
        task_id=task.get("task_id", ""),
        task_type=task_type,
        description=task.get("description", ""),
        quality_criteria=task.get("quality_criteria", {}),
        constraints=task.get("constraints", {}),
        available_tools=task.get("available_tools", {}),
        send_block=self.block,
    )

    responses = await query_miners(
        dendrite=self.dendrite,
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=synapse,
        send_block=self.block,
        timeout=QUERY_TIMEOUT_S,
    )

    bt.logging.info(f"Received {len(responses)} responses from {len(miner_uids)} miners")

    # Validate: dendrite.hotkey must match queried UID (readme §4.8 step 2)
    valid_responses = []
    valid_uids = []
    for response, uid in zip(responses, miner_uids):
        if response is None:
            continue
        expected_hotkey = self.metagraph.hotkeys[uid]
        if validate_response(response, expected_hotkey, self.metagraph):
            valid_responses.append(response)
            valid_uids.append(uid)

    bt.logging.info(f"Validated {len(valid_responses)} responses")

    if not valid_responses:
        bt.logging.warning("No valid responses received")
        time.sleep(5)
        return

    # ── Stages 3-5: Execution, Quality, Scoring ──────────────────────────────
    constraints   = task.get("constraints", {})
    reference     = task.get("reference", {})
    routing_policy = task.get("routing_policy", {})  # issue 1.3

    scores = []
    for response, uid in zip(valid_responses, valid_uids):
        # Stage 3: Sandboxed async execution (issue 2.8) with routing_policy (issue 1.3)
        try:
            exec_result = await asyncio.wait_for(
                execute_workflow_async(
                    workflow_plan=response.workflow_plan or {},
                    constraints=constraints,
                    total_estimated_cost=response.total_estimated_cost or 0.01,
                    routing_policy=routing_policy,
                    dendrite=self.dendrite,
                    metagraph=self.metagraph,
                ),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            bt.logging.warning(
                f"execute_workflow_async timed out for miner {uid}"
            )
            continue

        completion_ratio = (
            exec_result.steps_completed / exec_result.total_steps
            if exec_result.total_steps > 0 else 0.0
        )

        # Stage 4: Output quality evaluation
        output_quality = score_output_quality(
            task_type=task_type,
            output=exec_result.final_output,
            reference=reference,
        )

        # For synthetic tasks, blend structural match with standard quality score (fix 2.4)
        if is_synthetic and "optimal_workflow" in reference:
            optimal = reference["optimal_workflow"]
            miner_nodes = set(
                n.get("subnet") for n in (response.workflow_plan or {}).get("nodes", [])
            )
            optimal_nodes = set(n.get("subnet") for n in optimal.get("nodes", []))
            struct_score = len(miner_nodes & optimal_nodes) / max(1, len(optimal_nodes))
            # Blend: 50% standard quality + 50% structural DAG match
            output_quality = 0.5 * output_quality + 0.5 * struct_score
            bt.logging.debug(
                f"Synthetic task {task_id}: struct_score={struct_score:.3f} "
                f"blended_quality={output_quality:.3f}"
            )

        # Stage 5: Composite scoring
        score_breakdown = compute_composite_score(
            output_quality=output_quality,
            completion_ratio=completion_ratio,
            actual_cost=exec_result.actual_cost,
            max_budget=constraints.get("max_budget_tao", 1.0),
            actual_latency=exec_result.actual_latency,
            max_latency=constraints.get("max_latency_seconds", 30.0),
            unplanned_retries=exec_result.unplanned_retries,
            timeouts=exec_result.timeouts,
            hard_failures=exec_result.hard_failures,
            budget_aborted=exec_result.budget_aborted,
        )

        composite_score = score_breakdown["S_composite"]
        scores.append(composite_score)

        # Temporal consistency check (issue 1.5)
        _check_temporal_consistency(uid, composite_score, self.block)

        bt.logging.debug(
            f"Miner {uid}: S={composite_score:.4f} "
            f"(success={score_breakdown['S_success']:.3f}, "
            f"cost={score_breakdown['S_cost']:.3f}, "
            f"latency={score_breakdown['S_latency']:.3f}, "
            f"reliability={score_breakdown['S_reliability']:.3f})"
        )

    # ── Stage 6: Rolling window + lifecycle + N_min ───────────────────────────
    bt.logging.info(
        f"Scored {len(scores)} miners: mean={np.mean(scores):.4f}" if scores else "No scores"
    )

    # 6a. Update the score aggregator — apply immunity warm-up scale before adding (fix 1.1)
    if hasattr(self, "score_aggregator"):
        for uid, composite_score in zip(valid_uids, scores):
            weighted_score = get_miner_weight(
                miner_uid=uid,
                tasks_seen=self.score_aggregator.tasks_seen[uid],
                raw_score=composite_score,
                subtensor=self.subtensor,
                netuid=self.config.netuid,
                current_block=self.block,
            )
            self.score_aggregator.add_score(uid, weighted_score)
    else:
        bt.logging.warning("score_aggregator not initialised — cannot update rolling window")

    # 6b. Feed per-task scores into lifecycle tracker (readme §4.7)
    tracker.record_task_score(task_id, scores)

    # 6c. Increment N_min counter — use persisted value from score_aggregator (fix 2.8)
    # The counter is owned here in module state; save_state() persists it.
    _tasks_executed_this_tempo += 1
    # Sync back to score_aggregator so save_state() can persist it
    if hasattr(self, "score_aggregator"):
        self.score_aggregator.tasks_executed_this_tempo = _tasks_executed_this_tempo

    # 6d. At tempo boundary: flush lifecycle changes + log exec support eligibility
    current_tempo = self.block // _get_effective_tempo(self)
    if current_tempo > _last_lifecycle_tempo:
        _last_lifecycle_tempo = current_tempo

        eligible = _tasks_executed_this_tempo >= EXEC_SUPPORT_N_MIN
        bt.logging.info(
            f"TEMPO_BOUNDARY block={self.block}: "
            f"tasks_evaluated={_tasks_executed_this_tempo}/{EXEC_SUPPORT_N_MIN} — "
            f"EXEC_SUPPORT_ELIGIBLE: {eligible}"
        )
        _tasks_executed_this_tempo = 0
        if hasattr(self, "score_aggregator"):
            self.score_aggregator.tasks_executed_this_tempo = 0
        tracker.on_tempo_end()

    time.sleep(2)

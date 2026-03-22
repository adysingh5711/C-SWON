# C-SWON Validator — Forward Pass
# Implements the six-stage evaluation pipeline (readme §4.8).

"""
Validator forward pass: the main loop that runs every step.

Six-stage pipeline:
1. Deterministic task selection (VRF-keyed)
2. Miner workflow collection (async query)
3. Sandboxed execution (executor)
4. Output quality evaluation (deterministic, no LLM judge)
5. Composite scoring (four-dimension formula)
6. Rolling window update
"""

import time
from typing import Optional

import bittensor as bt

from cswon.protocol import WorkflowSynapse
from cswon.validator.config import (
    SCORING_VERSION,
    QUERY_TIMEOUT_S,
)
from cswon.validator.miner_selection import (
    load_benchmark_tasks,
    select_task_for_block,
    select_miners_for_query,
)
from cswon.validator.query_loop import query_miners, validate_response
from cswon.validator.executor import execute_workflow
from cswon.validator.reward import (
    score_output_quality,
    compute_composite_score,
)
from cswon.utils.uids import get_random_uids


# Cache benchmark tasks to avoid reloading every step
_benchmark_cache = None


def _get_benchmark_tasks():
    """Load and cache benchmark tasks."""
    global _benchmark_cache
    if _benchmark_cache is None:
        _benchmark_cache = load_benchmark_tasks()
    return _benchmark_cache


async def forward(self):
    """
    Validator forward pass — six-stage evaluation pipeline (readme §4.8).

    Args:
        self: The validator neuron instance.
    """
    benchmark_tasks = _get_benchmark_tasks()

    # ── Stage 1: Deterministic task selection ────────────────────
    if not benchmark_tasks:
        bt.logging.warning("No benchmark tasks loaded, using fallback query")
        # Fallback: just query miners with a generic task
        miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)
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

    bt.logging.info(
        f"Selected task: {task.get('task_id', 'unknown')} "
        f"type={task.get('task_type', 'unknown')} "
        f"at block {self.block}"
    )

    # ── Stage 2: Miner workflow collection ──────────────────────
    miner_uids = select_miners_for_query(
        metagraph=self.metagraph,
        k=self.config.neuron.sample_size,
        exclude=[self.uid],
    )

    if len(miner_uids) == 0:
        bt.logging.warning("No miners available to query")
        time.sleep(5)
        return

    # Build the WorkflowSynapse with task package
    synapse = WorkflowSynapse(
        task_id=task.get("task_id", ""),
        task_type=task.get("task_type", ""),
        description=task.get("description", ""),
        quality_criteria=task.get("quality_criteria", {}),
        constraints=task.get("constraints", {}),
        available_tools=task.get("available_tools", {}),
        send_block=self.block,
    )

    # Query miners
    responses = await query_miners(
        dendrite=self.dendrite,
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        synapse=synapse,
        send_block=self.block,
        timeout=QUERY_TIMEOUT_S,
    )

    bt.logging.info(f"Received {len(responses)} responses from {len(miner_uids)} miners")

    # Validate responses
    valid_responses = []
    valid_uids = []
    for i, (response, uid) in enumerate(zip(responses, miner_uids)):
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

    # ── Stages 3-5: Execution, Quality, Scoring ────────────────
    constraints = task.get("constraints", {})
    reference = task.get("reference", {})
    task_type = task.get("task_type", "code")

    scores = []
    for response, uid in zip(valid_responses, valid_uids):
        # Stage 3: Sandboxed execution
        exec_result = execute_workflow(
            workflow_plan=response.workflow_plan,
            constraints=constraints,
            total_estimated_cost=response.total_estimated_cost or 0.01,
        )

        # Stage 4: Output quality evaluation
        completion_ratio = (
            exec_result.steps_completed / exec_result.total_steps
            if exec_result.total_steps > 0
            else 0.0
        )

        output_quality = score_output_quality(
            task_type=task_type,
            output=exec_result.final_output,
            reference=reference,
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

        bt.logging.debug(
            f"Miner {uid}: S={composite_score:.4f} "
            f"(success={score_breakdown['S_success']:.3f}, "
            f"cost={score_breakdown['S_cost']:.3f}, "
            f"latency={score_breakdown['S_latency']:.3f}, "
            f"reliability={score_breakdown['S_reliability']:.3f})"
        )

    # ── Stage 6: Rolling window update ──────────────────────────
    import numpy as np

    rewards = np.array(scores, dtype=np.float32)
    bt.logging.info(f"Scored {len(rewards)} miners: mean={rewards.mean():.4f}")

    # Update scores using the base validator's update_scores method
    self.update_scores(rewards, valid_uids)

    # Also update the score aggregator if available
    if hasattr(self, "score_aggregator"):
        for uid, score in zip(valid_uids, scores):
            self.score_aggregator.add_score(uid, score)

    time.sleep(2)  # Brief pause between evaluation rounds

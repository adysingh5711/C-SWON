# C-SWON Validator — Benchmark Lifecycle Tracker
# Implements quarantine and deprecation logic per readme §4.7.

"""
BenchmarkLifecycleTracker maintains per-task score histories across tempos and
applies the lifecycle rules:
  - >70% miners score >0.90 for 3 consecutive tempos  → deprecate
  - >70% miners score <0.10 for 3 consecutive tempos  → quarantine
  - quarantined for 5 tempos without resolution        → auto-remove (deprecate)
"""

import json
import os
from collections import defaultdict, deque
from typing import Dict, List, Optional

import bittensor as bt

from cswon.validator.config import (
    DEPRECATION_SCORE_THRESHOLD,
    QUARANTINE_SCORE_THRESHOLD,
    DEPRECATION_TEMPO_COUNT,
    QUARANTINE_REMOVAL_TEMPOS,
    BENCHMARK_PATH,
)

# Fraction of miners that must be above/below threshold to trigger lifecycle
TRIGGER_FRACTION = 0.70


class BenchmarkLifecycleTracker:
    """
    Tracks per-task performance statistics across tempos and applies the
    benchmark lifecycle rules from readme §4.7.

    Usage:
        tracker = BenchmarkLifecycleTracker()
        # At the end of each scoring round, record per-task, per-miner scores:
        tracker.record_task_score("task-001", miner_scores=[0.95, 0.92, 0.98])
        # At each tempo boundary, evaluate and flush lifecycle changes:
        tracker.on_tempo_end(benchmark_path="benchmarks/v1.json")
    """

    def __init__(self, benchmark_path: Optional[str] = None):
        self.benchmark_path = benchmark_path or BENCHMARK_PATH

        # task_id → deque of per-tempo (above_threshold_fraction, below_threshold_fraction)
        # Each entry is a tuple (frac_above_deprecate, frac_below_quarantine)
        self._tempo_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max(DEPRECATION_TEMPO_COUNT, QUARANTINE_REMOVAL_TEMPOS))
        )

        # task_id → number of tempos in quarantine (without resolution)
        self._quarantine_duration: Dict[str, int] = defaultdict(int)

        # Accumulator for current tempo: task_id → list of miner composite scores
        self._current_tempo_scores: Dict[str, List[float]] = defaultdict(list)

    # ── Per-Round Score Recording ──────────────────────────────────────────

    def record_task_score(self, task_id: str, miner_scores: List[float]) -> None:
        """
        Record the composite scores received for a given task in this round.

        Call once per validator forward pass (one block) for each task evaluated.

        Args:
            task_id: The benchmark task ID being scored.
            miner_scores: List of composite S scores from miners responding to this task.
        """
        if miner_scores:
            self._current_tempo_scores[task_id].extend(miner_scores)

    # ── Tempo Boundary Processing ──────────────────────────────────────────

    def on_tempo_end(self, benchmark_path: Optional[str] = None) -> None:
        """
        Called once per tempo boundary. Evaluates lifecycle rules and flushes
        status changes to the benchmark JSON file.

        Args:
            benchmark_path: Path to benchmarks/v{N}.json. Defaults to config value.
        """
        path = benchmark_path or self.benchmark_path

        # Compute per-task fractions for this tempo
        for task_id, scores in self._current_tempo_scores.items():
            if not scores:
                continue
            n = len(scores)
            frac_above = sum(1 for s in scores if s > DEPRECATION_SCORE_THRESHOLD) / n
            frac_below = sum(1 for s in scores if s < QUARANTINE_SCORE_THRESHOLD) / n
            self._tempo_history[task_id].append((frac_above, frac_below))

        # Reset current tempo accumulator
        self._current_tempo_scores.clear()

        # Evaluate lifecycle rules
        status_changes = self._evaluate_lifecycle()

        # Flush changes to disk if there are any
        if status_changes:
            self._flush_status_changes(path, status_changes)
            bt.logging.info(
                f"Benchmark lifecycle: {len(status_changes)} status change(s) written to {path}"
            )

    def _evaluate_lifecycle(self) -> Dict[str, str]:
        """
        Apply lifecycle rules and return {task_id: new_status} for tasks
        whose status should change.
        """
        changes: Dict[str, str] = {}

        for task_id, history in self._tempo_history.items():
            if len(history) == 0:
                continue

            # -- Deprecation check: >70% above 0.90 for DEPRECATION_TEMPO_COUNT consecutive tempos
            if len(history) >= DEPRECATION_TEMPO_COUNT:
                recent = list(history)[-DEPRECATION_TEMPO_COUNT:]
                if all(frac_above >= TRIGGER_FRACTION for frac_above, _ in recent):
                    changes[task_id] = "deprecated"
                    bt.logging.info(
                        f"Task {task_id} DEPRECATED: >{TRIGGER_FRACTION*100:.0f}% miners "
                        f"scored >{DEPRECATION_SCORE_THRESHOLD} for "
                        f"{DEPRECATION_TEMPO_COUNT} consecutive tempos."
                    )
                    continue

            # -- Quarantine check
            if len(history) >= DEPRECATION_TEMPO_COUNT:
                recent = list(history)[-DEPRECATION_TEMPO_COUNT:]
                if all(frac_below >= TRIGGER_FRACTION for _, frac_below in recent):
                    self._quarantine_duration[task_id] += 1
                    if self._quarantine_duration[task_id] >= QUARANTINE_REMOVAL_TEMPOS:
                        changes[task_id] = "deprecated"
                        bt.logging.warning(
                            f"Task {task_id} AUTO-REMOVED after {QUARANTINE_REMOVAL_TEMPOS} "
                            f"tempos in quarantine."
                        )
                    else:
                        changes[task_id] = "quarantined"
                        bt.logging.warning(
                            f"Task {task_id} QUARANTINED: >{TRIGGER_FRACTION*100:.0f}% miners "
                            f"scored <{QUARANTINE_SCORE_THRESHOLD} for "
                            f"{DEPRECATION_TEMPO_COUNT} consecutive tempos. "
                            f"Quarantine tenure: {self._quarantine_duration[task_id]}/{QUARANTINE_REMOVAL_TEMPOS}"
                        )
                    continue

            # Quarantine condition NOT met this tempo — reset and revert to active (issue 2.10)
            if task_id in self._quarantine_duration and self._quarantine_duration[task_id] > 0:
                self._quarantine_duration[task_id] = 0
                changes[task_id] = "active"
                bt.logging.info(
                    f"Task {task_id} REVERTED to active: quarantine condition no longer met."
                )

        return changes

    def _flush_status_changes(self, path: str, changes: Dict[str, str]) -> None:
        """
        Write status changes back to the benchmark JSON file (readme §4.7).

        Updated task entries will have their "status" field set to "quarantined"
        or "deprecated". The file is read, modified in place, then written back.
        Quarantined tasks also get a "quarantine_since_tempo" counter reset.
        """
        if not os.path.exists(path):
            bt.logging.error(f"Benchmark file not found at {path}; cannot write lifecycle changes.")
            return

        try:
            with open(path, "r") as f:
                tasks = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            bt.logging.error(f"Failed to read benchmark file {path}: {e}")
            return

        modified = False
        for task in tasks:
            task_id = task.get("task_id")
            if task_id in changes:
                new_status = changes[task_id]
                old_status = task.get("status", "active")
                if old_status != new_status:
                    task["status"] = new_status
                    if new_status == "quarantined":
                        task["quarantine_since_tempo"] = self._quarantine_duration.get(task_id, 1)
                    elif new_status == "deprecated":
                        task["deprecation_reason"] = "auto-lifecycle"
                    elif new_status == "active":
                        # Revert: clear quarantine metadata (issue 2.10)
                        task["quarantine_since_tempo"] = None
                        task["deprecation_reason"] = None
                    modified = True

        if modified:
            try:
                with open(path, "w") as f:
                    json.dump(tasks, f, indent=2)
            except IOError as e:
                bt.logging.error(f"Failed to write benchmark lifecycle changes to {path}: {e}")

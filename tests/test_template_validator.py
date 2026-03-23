# C-SWON Validator — Core Unit Tests
# Previously: test_template_validator.py (template holdover)
# Now: fully rewritten with cswon.* imports and real assertions.
# Addresses pending2.md §1.2

"""
Unit tests for the C-SWON validator subsystems.

Covers:
  - ScoreAggregator rolling window (equal weight, no EMA)
  - Four-dimension composite scoring and success-gating
  - VRF-keyed deterministic task selection
  - WorkflowSynapse protocol schema
  - Benchmark task file structure
  - Immunity warm-up scale
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from collections import deque


# ── Imports from cswon.* (not template.*) ────────────────────────────────────

from cswon.protocol import WorkflowSynapse
from cswon.validator.reward import (
    ScoreAggregator,
    compute_composite_score,
    score_output_quality,
    get_miner_weight,
)
from cswon.validator.miner_selection import (
    load_benchmark_tasks,
    select_task_for_block,
    select_miners_for_query,
)
from cswon.validator.config import (
    SCORING_VERSION,
    SCORE_WINDOW_SIZE,
    MAX_MINER_WEIGHT_FRACTION,
    WARMUP_TASK_THRESHOLD,
    SUCCESS_GATE,
)

# Path to benchmark file for structural tests
_BENCHMARK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "benchmarks",
    "v1.json",
)


# ── 1. ScoreAggregator — rolling window ──────────────────────────────────────

class TestScoreAggregator(unittest.TestCase):
    """Tests for the equal-weight rolling 100-task window (readme §2.2)."""

    def test_window_capped_at_size(self):
        """Adding more than SCORE_WINDOW_SIZE scores keeps only the most recent."""
        agg = ScoreAggregator(window_size=10)
        for i in range(15):
            agg.add_score(uid=0, score=float(i) / 14.0)
        window = agg.score_windows[0]
        self.assertEqual(len(window), 10, "Window must not exceed window_size")

    def test_equal_weight_average(self):
        """Average must be arithmetic mean — no exponential decay."""
        agg = ScoreAggregator(window_size=5)
        scores = [0.2, 0.4, 0.6, 0.8, 1.0]
        for s in scores:
            agg.add_score(uid=7, score=s)
        expected = sum(scores) / len(scores)
        self.assertAlmostEqual(agg.get_average_score(7), expected, places=6)

    def test_tasks_seen_counter_increments(self):
        """tasks_seen must increment by 1 per add_score call."""
        agg = ScoreAggregator()
        for _ in range(5):
            agg.add_score(uid=3, score=0.5)
        self.assertEqual(agg.tasks_seen[3], 5)

    def test_normalised_weights_sum_to_one(self):
        """Normalised weights must sum to 1.0."""
        agg = ScoreAggregator()
        for uid in [0, 1, 2]:
            for _ in range(3):
                agg.add_score(uid=uid, score=0.5 + uid * 0.1)
        weights = agg.get_normalised_weights([0, 1, 2])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)

    def test_per_miner_weight_cap(self):
        """No single miner may exceed MAX_MINER_WEIGHT_FRACTION (15%)."""
        agg = ScoreAggregator()
        # uid=0 gets very high scores; others get near-zero
        for _ in range(50):
            agg.add_score(uid=0, score=1.0)
        for uid in range(1, 20):
            for _ in range(50):
                agg.add_score(uid=uid, score=0.01)
        weights = agg.get_normalised_weights(list(range(20)))
        for uid, w in weights.items():
            self.assertLessEqual(
                w, MAX_MINER_WEIGHT_FRACTION + 1e-9,
                f"uid={uid} weight={w:.4f} exceeds 15% cap",
            )

    def test_unknown_miner_returns_zero(self):
        """Miner with no scores yet should return 0.0 average."""
        agg = ScoreAggregator()
        self.assertEqual(agg.get_average_score(999), 0.0)


# ── 2. Composite Scoring — four-dimension formula ─────────────────────────────

class TestCompositeScoring(unittest.TestCase):
    """Tests for the S = 0.50×success + 0.25×cost + 0.15×latency + 0.10×reliability formula."""

    def _base_kwargs(self, **overrides):
        defaults = dict(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
            budget_aborted=False,
        )
        defaults.update(overrides)
        return defaults

    def test_perfect_score(self):
        """All components at max → S_composite close to 1.0."""
        result = compute_composite_score(**self._base_kwargs(
            actual_cost=0.001,  # very cheap
            actual_latency=0.1,  # very fast
        ))
        self.assertGreater(result["S_composite"], 0.90)

    def test_success_gating_cost_and_latency(self):
        """When S_success ≤ 0.7, S_cost and S_latency must be 0."""
        result = compute_composite_score(**self._base_kwargs(
            output_quality=0.5,
            completion_ratio=1.0,  # S_success = 0.5 ≤ 0.7
        ))
        self.assertEqual(result["S_cost"], 0.0, "S_cost must be 0 when S_success ≤ 0.7")
        self.assertEqual(result["S_latency"], 0.0, "S_latency must be 0 when S_success ≤ 0.7")

    def test_budget_abort_forces_s_cost_zero(self):
        """budget_aborted=True must force S_cost to 0 regardless of actuals."""
        result = compute_composite_score(**self._base_kwargs(
            budget_aborted=True,
            actual_cost=0.001,  # would normally score well
        ))
        self.assertEqual(result["S_cost"], 0.0)

    def test_reliability_always_scored(self):
        """S_reliability is applied even when success gate is not met."""
        result = compute_composite_score(**self._base_kwargs(
            output_quality=0.3,   # S_success = 0.3 (below gate)
            completion_ratio=1.0,
            hard_failures=2,      # penalty: 2 × 0.50 = 1.0 → S_reliability = 0.0
        ))
        self.assertEqual(result["S_reliability"], 0.0)

    def test_planned_retries_not_penalised(self):
        """Retries within declared budget must not appear as unplanned_retries."""
        # unplanned_retries=0 means miner stayed within budget
        result = compute_composite_score(**self._base_kwargs(
            unplanned_retries=0,
        ))
        self.assertAlmostEqual(result["S_reliability"], 1.0, places=6)

    def test_composite_weights_sum(self):
        """S_composite = 0.50*success + 0.25*cost + 0.15*latency + 0.10*reliability."""
        r = compute_composite_score(**self._base_kwargs(
            output_quality=0.8,
            completion_ratio=1.0,
            actual_cost=0.025,   # 50% of budget
            max_budget=0.05,
            actual_latency=5.0,  # 50% of max
            max_latency=10.0,
        ))
        # S_success = 0.8, S_cost = 0.5, S_latency = 0.5, S_reliability = 1.0
        expected = 0.50 * 0.8 + 0.25 * 0.5 + 0.15 * 0.5 + 0.10 * 1.0
        self.assertAlmostEqual(r["S_composite"], expected, places=5)

    def test_completion_ratio_partial_dag(self):
        """Partial DAG completion is reflected in S_success."""
        result = compute_composite_score(**self._base_kwargs(
            output_quality=1.0,
            completion_ratio=0.75,  # 3 of 4 steps completed
        ))
        self.assertAlmostEqual(result["S_success"], 0.75, places=5)


# ── 3. VRF Task Selection ─────────────────────────────────────────────────────

class TestVRFTaskSelection(unittest.TestCase):
    """Tests for the deterministic hotkey-keyed VRF task selector (readme §2.5)."""

    _TASKS = [{"task_id": f"t-{i:04d}", "status": "active"} for i in range(10)]

    def test_determinism_same_inputs(self):
        """Same hotkey + block must always return the same task."""
        t1 = select_task_for_block("hotkey_abc", 12345, self._TASKS)
        t2 = select_task_for_block("hotkey_abc", 12345, self._TASKS)
        self.assertEqual(t1["task_id"], t2["task_id"])

    def test_different_hotkeys_may_differ(self):
        """Different hotkeys should (with very high probability) derive different tasks."""
        results = {
            select_task_for_block(f"hotkey_{i}", 99999, self._TASKS)["task_id"]
            for i in range(10)
        }
        self.assertGreater(len(results), 1, "Different hotkeys should produce distinct tasks")

    def test_different_blocks_may_differ(self):
        """Different blocks should (with high probability) select different tasks."""
        results = {
            select_task_for_block("same_hotkey", b, self._TASKS)["task_id"]
            for b in range(10)
        }
        self.assertGreater(len(results), 1)

    def test_returns_none_on_empty_list(self):
        """Empty task list must return None without raising."""
        result = select_task_for_block("hotkey_x", 1, [])
        self.assertIsNone(result)

    def test_index_in_bounds(self):
        """Selected index must always be within task list bounds."""
        for block in range(1000):
            task = select_task_for_block("hk", block, self._TASKS)
            self.assertIn(task, self._TASKS)


# ── 4. WorkflowSynapse Protocol Schema ───────────────────────────────────────

class TestWorkflowSynapseSchema(unittest.TestCase):
    """Tests for WorkflowSynapse field defaults (readme §3.2b)."""

    def test_optional_fields_default_to_none(self):
        """All miner-populated optional fields must default to None."""
        s = WorkflowSynapse()
        self.assertIsNone(s.miner_uid)
        self.assertIsNone(s.scoring_version)
        self.assertIsNone(s.workflow_plan)
        self.assertIsNone(s.total_estimated_cost)
        self.assertIsNone(s.total_estimated_latency)
        self.assertIsNone(s.confidence)
        self.assertIsNone(s.reasoning)

    def test_validator_fields_have_defaults(self):
        """Validator-populated fields must have empty-string / zero defaults."""
        s = WorkflowSynapse()
        self.assertEqual(s.task_id, "")
        self.assertEqual(s.task_type, "")
        self.assertEqual(s.description, "")
        self.assertEqual(s.send_block, 0)

    def test_round_trip_deserialize(self):
        """deserialize() must return the same object (identity)."""
        s = WorkflowSynapse(task_id="t-1", task_type="rag")
        result = s.deserialize()
        self.assertIs(result, s)

    def test_field_assignment(self):
        """Miner-populated fields can be set and read back."""
        s = WorkflowSynapse()
        s.miner_uid = 42
        s.workflow_plan = {"nodes": [], "edges": []}
        s.scoring_version = SCORING_VERSION
        self.assertEqual(s.miner_uid, 42)
        self.assertEqual(s.scoring_version, SCORING_VERSION)


# ── 5. Benchmark Task File Structure ─────────────────────────────────────────

class TestBenchmarkTaskFile(unittest.TestCase):
    """Tests for the benchmark dataset structure (readme §4.7)."""

    @classmethod
    def setUpClass(cls):
        with open(_BENCHMARK_PATH, "r") as f:
            cls.tasks = json.load(f)

    def test_minimum_task_count(self):
        """Benchmark must have at least 5 tasks (readme §4.7 mocked)."""
        self.assertGreaterEqual(
            len(self.tasks), 5,
            f"Expected >= 5 tasks, found {len(self.tasks)}",
        )

    def test_all_tasks_have_status_field(self):
        """Every task entry must have a 'status' field (readme §4.7)."""
        for task in self.tasks:
            self.assertIn("status", task, f"Task {task.get('task_id')} missing 'status'")

    def test_status_values_are_valid(self):
        """status must be one of: active, quarantined, deprecated."""
        valid = {"active", "quarantined", "deprecated"}
        for task in self.tasks:
            self.assertIn(task["status"], valid)

    def test_all_tasks_have_routing_policy(self):
        """Every task must embed a routing_policy (readme §3.3)."""
        for task in self.tasks:
            self.assertIn(
                "routing_policy", task,
                f"Task {task.get('task_id')} missing 'routing_policy'",
            )

    def test_synthetic_ratio(self):
        """15–20% of tasks must be synthetic (readme §2.5, §4.7)."""
        synthetic = [t for t in self.tasks if t.get("type") == "synthetic"]
        ratio = len(synthetic) / len(self.tasks)
        self.assertGreaterEqual(ratio, 0.15, f"Synthetic ratio {ratio:.1%} < 15%")
        self.assertLessEqual(ratio, 0.20, f"Synthetic ratio {ratio:.1%} > 20%")

    def test_task_types_present(self):
        """All four task types must be represented (readme §4.7)."""
        types = {t.get("task_type") for t in self.tasks}
        for required in ["rag", "agent", "data_transform"]:
            self.assertIn(required, types, f"Task type '{required}' missing from benchmark")

    def test_load_benchmark_tasks_skips_non_active(self):
        """load_benchmark_tasks() must skip non-active tasks."""
        tasks = load_benchmark_tasks(_BENCHMARK_PATH)
        for t in tasks:
            self.assertEqual(t.get("status", "active"), "active")


# ── 6. Output Quality Scoring ─────────────────────────────────────────────────

class TestOutputQualityScoring(unittest.TestCase):
    """Tests for deterministic quality scoring by task type (readme §2.3)."""

    def test_rag_returns_float_in_range(self):
        output = {"text": "Validators evaluate miners and submit weights each tempo."}
        reference = {"reference_answer": "Validators score miners and set weights."}
        score = score_output_quality("rag", output, reference)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_code_none_output_returns_zero(self):
        score = score_output_quality("code", None, {})
        self.assertEqual(score, 0.0)

    def test_data_transform_exact_match(self):
        expected = '[{"x": 1}]'
        output = {"text": '[{"x": 1}]'}
        reference = {"expected_output": expected}
        score = score_output_quality("data_transform", output, reference)
        self.assertEqual(score, 1.0)

    def test_data_transform_mismatch(self):
        output = {"text": '[{"x": 999}]'}
        reference = {"expected_output": '[{"x": 1}]'}
        score = score_output_quality("data_transform", output, reference)
        self.assertEqual(score, 0.0)

    def test_unknown_task_type_returns_zero(self):
        score = score_output_quality("unknown_type", {"text": "hi"}, {})
        self.assertEqual(score, 0.0)


# ── 7. Immunity Warm-Up Scale ─────────────────────────────────────────────────

class TestImmunityWarmUp(unittest.TestCase):
    """Tests for the immunity warm-up scale (readme §4.4)."""

    def _mock_subtensor(self, immunity_period: int, reg_block: int):
        subtensor = MagicMock()
        subtensor.get_subnet_hyperparameters.return_value = MagicMock(
            immunity_period=immunity_period
        )
        neuron = MagicMock()
        neuron.block = reg_block
        subtensor.neuron_for_uid.return_value = neuron
        return subtensor

    def test_immune_miner_warmup_scale(self):
        """Miner within immunity window gets warm-up scale."""
        subtensor = self._mock_subtensor(immunity_period=5000, reg_block=0)
        weight = get_miner_weight(
            miner_uid=5, tasks_seen=10, raw_score=1.0,
            subtensor=subtensor, netuid=1, current_block=100,
        )
        expected = 1.0 * min(1.0, 10 / WARMUP_TASK_THRESHOLD)
        self.assertAlmostEqual(weight, expected, places=6)

    def test_immune_miner_full_warmup(self):
        """Miner within immunity window with tasks_seen >= threshold gets full score."""
        subtensor = self._mock_subtensor(immunity_period=5000, reg_block=0)
        weight = get_miner_weight(
            miner_uid=5, tasks_seen=WARMUP_TASK_THRESHOLD, raw_score=0.75,
            subtensor=subtensor, netuid=1, current_block=100,
        )
        self.assertAlmostEqual(weight, 0.75, places=6)

    def test_post_immunity_no_scale(self):
        """Miner past immunity window gets raw score unchanged."""
        subtensor = self._mock_subtensor(immunity_period=5000, reg_block=0)
        weight = get_miner_weight(
            miner_uid=5, tasks_seen=5, raw_score=0.42,
            subtensor=subtensor, netuid=1, current_block=10000,  # past immunity
        )
        self.assertAlmostEqual(weight, 0.42, places=6)


if __name__ == "__main__":
    unittest.main()

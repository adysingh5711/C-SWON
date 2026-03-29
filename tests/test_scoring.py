"""
Tests for the C-SWON scoring formula (cswon/validator/reward.py).
Validates the four-dimension composite score per readme §2.2.
"""

import pytest
from cswon.validator.reward import (
    compute_composite_score,
    ScoreAggregator,
    _apply_weight_cap,
    _lcs_f1,
)


class TestCompositeScore:
    """Tests for S = 0.50·success + 0.25·cost + 0.15·latency + 0.10·reliability"""

    def test_perfect_score(self):
        """A perfect workflow should score close to 1.0."""
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.001,
            max_budget=0.05,
            actual_latency=1.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_success"] == 1.0
        assert result["S_cost"] == pytest.approx(1.0 - 0.001 / 0.05, abs=0.01)
        assert result["S_latency"] == pytest.approx(1.0 - 1.0 / 10.0, abs=0.01)
        assert result["S_reliability"] == 1.0
        assert result["S_composite"] > 0.9

    def test_total_failure(self):
        """A completely failed workflow should score 0."""
        result = compute_composite_score(
            output_quality=0.0,
            completion_ratio=0.0,
            actual_cost=0.05,
            max_budget=0.05,
            actual_latency=10.0,
            max_latency=10.0,
            unplanned_retries=5,
            timeouts=3,
            hard_failures=2,
        )
        assert result["S_success"] == 0.0
        # S_cost and S_latency gated at S_success > 0.7
        assert result["S_cost"] == 0.0
        assert result["S_latency"] == 0.0
        assert result["S_reliability"] == 0.0
        assert result["S_composite"] == 0.0

    def test_success_gate_cost(self):
        """S_cost should be 0 when S_success <= 0.7."""
        # S_success = 0.6 (below gate)
        result = compute_composite_score(
            output_quality=0.6,
            completion_ratio=1.0,
            actual_cost=0.001,  # very cheap
            max_budget=0.05,
            actual_latency=1.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_success"] == 0.6
        assert result["S_cost"] == 0.0  # gated
        assert result["S_latency"] == 0.0  # gated

    def test_success_gate_passes(self):
        """S_cost and S_latency should be non-zero when S_success > 0.7."""
        result = compute_composite_score(
            output_quality=0.9,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_success"] == 0.9
        assert result["S_cost"] > 0.0  # gate passes
        assert result["S_latency"] > 0.0  # gate passes

    def test_partial_completion(self):
        """Partial DAG completion should reduce S_success proportionally."""
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=0.75,  # 3/4 steps completed
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_success"] == pytest.approx(0.75)

    def test_reliability_planned_retries_free(self):
        """Planned retries (within declared budget) should NOT be penalised."""
        # unplanned_retries=0 means all retries were within declared budget
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,  # all retries planned
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_reliability"] == 1.0

    def test_reliability_unplanned_retries_penalised(self):
        """Unplanned retries should be penalised at 0.10 each."""
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=3,  # 3 unplanned
            timeouts=0,
            hard_failures=0,
        )
        # 1.0 - 3*0.10 = 0.70
        assert result["S_reliability"] == pytest.approx(0.70, abs=0.01)

    def test_reliability_hard_failure_penalty(self):
        """Hard failures should be penalised at 0.50 each."""
        result = compute_composite_score(
            output_quality=0.5,
            completion_ratio=0.5,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=2,  # 2 hard failures
        )
        # 1.0 - 2*0.50 = 0.0
        assert result["S_reliability"] == 0.0

    def test_reliability_capped_at_one(self):
        """S_reliability should never exceed 1.0 (min guard)."""
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_reliability"] <= 1.0

    def test_budget_abort_forces_zero_cost(self):
        """Budget-aborted workflows should have S_cost forced to 0."""
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=0.5,
            actual_cost=0.08,  # over budget
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
            budget_aborted=True,
        )
        assert result["S_cost"] == 0.0

    def test_readme_example_cost_scoring(self):
        """
        Spot-check from readme §3.3 example:
        actual_cost=0.0072, max_budget=0.05 → S_cost = 1 - 0.0072/0.05 ≈ 0.856
        """
        result = compute_composite_score(
            output_quality=1.0,
            completion_ratio=1.0,
            actual_cost=0.0072,
            max_budget=0.05,
            actual_latency=4.3,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_cost"] == pytest.approx(1.0 - 0.0072 / 0.05, abs=0.001)


class TestScoreAggregator:
    """Tests for rolling window score aggregation."""

    def test_empty_window(self):
        agg = ScoreAggregator(window_size=100)
        assert agg.get_average_score(0) == 0.0

    def test_single_score(self):
        agg = ScoreAggregator(window_size=100)
        agg.add_score(0, 0.8)
        assert agg.get_average_score(0) == pytest.approx(0.8)

    def test_rolling_window_eviction(self):
        agg = ScoreAggregator(window_size=3)
        agg.add_score(0, 1.0)
        agg.add_score(0, 0.5)
        agg.add_score(0, 0.5)
        assert agg.get_average_score(0) == pytest.approx(2.0 / 3)

        # Add a 4th — should evict the first
        agg.add_score(0, 0.0)
        # Window: [0.5, 0.5, 0.0] → avg = 1.0/3
        assert agg.get_average_score(0) == pytest.approx(1.0 / 3, abs=0.01)

    def test_weight_cap_15_percent(self):
        """15% per-miner cap per readme §4.8."""
        # With 10 miners, 15% cap is achievable (1/10 = 10% < 15%)
        weights = {i: 0.05 for i in range(10)}
        weights[0] = 0.55  # one dominant miner
        capped = _apply_weight_cap(weights, 0.15)
        # Dominant miner should be capped
        assert capped[0] <= 0.15 + 0.01
        # Sum should still be 1.0
        assert pytest.approx(sum(capped.values()), abs=0.01) == 1.0

    def test_weight_cap_all_above(self):
        """When all miners exceed cap (too few miners), weights normalize equally."""
        weights = {0: 0.5, 1: 0.3, 2: 0.2}
        capped = _apply_weight_cap(weights, 0.15)
        # With 3 miners all capped at 15%, redistribution produces 1/3 each
        assert pytest.approx(sum(capped.values()), abs=0.01) == 1.0

    def test_normalised_weights(self):
        agg = ScoreAggregator(window_size=100)
        agg.add_score(0, 0.8)
        agg.add_score(1, 0.6)
        agg.add_score(2, 0.4)
        result = agg.get_normalised_weights([0, 1, 2])
        assert pytest.approx(sum(result.values()), abs=0.01) == 1.0


class TestLCSF1:
    """Tests for fallback LCS-based F1 scoring."""

    def test_identical_strings(self):
        assert _lcs_f1("hello world", "hello world") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert _lcs_f1("hello", "world") == 0.0

    def test_partial_overlap(self):
        score = _lcs_f1("the quick brown fox", "the brown fox jumped")
        assert 0 < score < 1

    def test_empty_strings(self):
        assert _lcs_f1("", "hello") == 0.0
        assert _lcs_f1("hello", "") == 0.0


class TestScoringVersionCompat:
    """Validators must tolerate one scoring version behind (CLAUDE.md rule)."""

    def test_version_one_behind_still_scores(self):
        """A miner with scoring_version='0.9.0' should still be scorable."""
        result = compute_composite_score(
            output_quality=0.9,
            completion_ratio=1.0,
            actual_cost=0.01,
            max_budget=0.05,
            actual_latency=2.0,
            max_latency=10.0,
            unplanned_retries=0,
            timeouts=0,
            hard_failures=0,
        )
        assert result["S_composite"] > 0.0
        assert result["S_success"] == pytest.approx(0.9)

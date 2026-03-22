"""
Tests for the C-SWON workflow executor (cswon/validator/executor.py).
Validates topological sort, DataRef resolution, and budget abort per readme §3.2.
"""

import pytest
from cswon.validator.executor import (
    topological_sort_tiers,
    resolve_datarefs,
    execute_workflow,
    DataRefError,
)


class TestTopologicalSort:
    """Tests for DAG topological sorting into execution tiers."""

    def test_linear_chain(self):
        """A→B→C should produce 3 tiers."""
        nodes = [
            {"id": "A"}, {"id": "B"}, {"id": "C"},
        ]
        edges = [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ]
        tiers = topological_sort_tiers(nodes, edges)
        assert len(tiers) == 3
        assert tiers[0] == ["A"]
        assert tiers[1] == ["B"]
        assert tiers[2] == ["C"]

    def test_parallel_branches(self):
        """A→C and B→C (A,B independent) should have A,B in tier 0."""
        nodes = [
            {"id": "A"}, {"id": "B"}, {"id": "C"},
        ]
        edges = [
            {"from": "A", "to": "C"},
            {"from": "B", "to": "C"},
        ]
        tiers = topological_sort_tiers(nodes, edges)
        assert len(tiers) == 2
        assert set(tiers[0]) == {"A", "B"}  # parallel
        assert tiers[1] == ["C"]

    def test_single_node(self):
        """Single node with no edges should be in one tier."""
        nodes = [{"id": "X"}]
        edges = []
        tiers = topological_sort_tiers(nodes, edges)
        assert tiers == [["X"]]

    def test_diamond_dag(self):
        """A→B, A→C, B→D, C→D"""
        nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}]
        edges = [
            {"from": "A", "to": "B"},
            {"from": "A", "to": "C"},
            {"from": "B", "to": "D"},
            {"from": "C", "to": "D"},
        ]
        tiers = topological_sort_tiers(nodes, edges)
        assert len(tiers) == 3
        assert tiers[0] == ["A"]
        assert set(tiers[1]) == {"B", "C"}
        assert tiers[2] == ["D"]

    def test_empty_dag(self):
        tiers = topological_sort_tiers([], [])
        assert tiers == []


class TestDataRefResolution:
    """Tests for ${step_id.output.field} pattern resolution."""

    def test_simple_text_ref(self):
        context = {
            "step_1": {
                "status": "success",
                "output": {"text": "Hello World"},
            }
        }
        result = resolve_datarefs("${step_1.output.text}", context)
        assert result == "Hello World"

    def test_nested_artifact_ref(self):
        context = {
            "step_2": {
                "status": "success",
                "output": {
                    "text": "review passed",
                    "artifacts": {"code": "def hello(): pass"},
                },
            }
        }
        result = resolve_datarefs("${step_2.output.artifacts.code}", context)
        assert result == "def hello(): pass"

    def test_ref_in_dict(self):
        context = {
            "step_1": {
                "status": "success",
                "output": {"text": "generated code"},
            }
        }
        params = {"code_input": "${step_1.output.text}", "review": True}
        result = resolve_datarefs(params, context)
        assert result["code_input"] == "generated code"
        assert result["review"] is True

    def test_ref_to_missing_node(self):
        context = {}
        with pytest.raises(DataRefError, match="not found in context"):
            resolve_datarefs("${missing.output.text}", context)

    def test_ref_to_failed_node(self):
        context = {
            "step_1": {"status": "failed", "output": None},
        }
        with pytest.raises(DataRefError, match="failed"):
            resolve_datarefs("${step_1.output.text}", context)

    def test_ref_to_missing_field(self):
        context = {
            "step_1": {
                "status": "success",
                "output": {"text": "hello"},
            }
        }
        with pytest.raises(DataRefError, match="not found"):
            resolve_datarefs("${step_1.output.nonexistent}", context)

    def test_no_refs_passthrough(self):
        """Strings without DataRef patterns should pass through unchanged."""
        result = resolve_datarefs("no refs here", {})
        assert result == "no refs here"

    def test_integer_passthrough(self):
        """Non-string values should pass through unchanged."""
        assert resolve_datarefs(42, {}) == 42
        assert resolve_datarefs(3.14, {}) == 3.14
        assert resolve_datarefs(True, {}) is True


class TestExecuteWorkflow:
    """Tests for the full workflow execution pipeline."""

    def test_simple_sequential_execution(self):
        """Execute a simple 2-step workflow in mock mode."""
        plan = {
            "nodes": [
                {"id": "step_1", "subnet": "SN1", "action": "generate",
                 "params": {"prompt": "test"}, "estimated_cost": 0.001, "estimated_latency": 0.5},
                {"id": "step_2", "subnet": "SN62", "action": "review",
                 "params": {"code": "${step_1.output.text}"}, "estimated_cost": 0.003, "estimated_latency": 1.0},
            ],
            "edges": [{"from": "step_1", "to": "step_2"}],
            "error_handling": {},
        }
        result = execute_workflow(
            workflow_plan=plan,
            constraints={"max_budget_tao": 0.05, "max_latency_seconds": 10.0},
            total_estimated_cost=0.004,
            mock_mode=True,
        )
        assert result.total_steps == 2
        assert result.steps_completed == 2
        assert result.actual_cost > 0
        assert result.budget_aborted is False

    def test_budget_abort(self):
        """Workflow should abort when cost exceeds ceiling."""
        plan = {
            "nodes": [
                {"id": "step_1", "subnet": "SN1", "action": "expensive",
                 "params": {}, "estimated_cost": 100.0, "estimated_latency": 0.5},
                {"id": "step_2", "subnet": "SN1", "action": "never_runs",
                 "params": {}, "estimated_cost": 100.0, "estimated_latency": 0.5},
            ],
            "edges": [{"from": "step_1", "to": "step_2"}],
            "error_handling": {},
        }
        result = execute_workflow(
            workflow_plan=plan,
            constraints={"max_budget_tao": 0.001},
            total_estimated_cost=0.001,
            mock_mode=True,
        )
        # Step 1 executes (cost is ~100 * [0.8, 1.2])
        # Step 2 should be budget-aborted since cumulative > ceiling
        assert result.budget_aborted is True
        assert result.steps_completed < result.total_steps

    def test_empty_workflow(self):
        """Empty workflow should return cleanly."""
        result = execute_workflow(
            workflow_plan={"nodes": [], "edges": []},
            constraints={},
            total_estimated_cost=0,
            mock_mode=True,
        )
        assert result.total_steps == 0
        assert result.steps_completed == 0

    def test_completion_ratio(self):
        """Verify completion_ratio = steps_completed / total_steps."""
        plan = {
            "nodes": [
                {"id": "s1", "subnet": "SN1", "action": "a", "params": {},
                 "estimated_cost": 0.001, "estimated_latency": 0.1},
                {"id": "s2", "subnet": "SN1", "action": "b", "params": {},
                 "estimated_cost": 0.001, "estimated_latency": 0.1},
                {"id": "s3", "subnet": "SN1", "action": "c", "params": {},
                 "estimated_cost": 0.001, "estimated_latency": 0.1},
            ],
            "edges": [
                {"from": "s1", "to": "s2"},
                {"from": "s2", "to": "s3"},
            ],
            "error_handling": {},
        }
        result = execute_workflow(
            workflow_plan=plan,
            constraints={"max_budget_tao": 1.0},
            total_estimated_cost=0.003,
            mock_mode=True,
        )
        ratio = result.steps_completed / result.total_steps
        assert ratio == pytest.approx(1.0)  # all 3 steps should complete in mock

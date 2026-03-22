"""
Tests for the C-SWON WorkflowSynapse protocol (cswon/protocol.py).
Validates synapse structure, field types, and serialization per readme §3.2b.
"""

import pytest
from cswon.protocol import WorkflowSynapse, Dummy


class TestWorkflowSynapse:
    """Tests for WorkflowSynapse per readme §3.2b."""

    def test_default_validator_fields(self):
        """Validator-populated fields should have sensible defaults."""
        s = WorkflowSynapse()
        assert s.task_id == ""
        assert s.task_type == ""
        assert s.description == ""
        assert s.quality_criteria == {}
        assert s.constraints == {}
        assert s.available_tools == {}
        assert s.send_block == 0

    def test_default_miner_fields_are_none(self):
        """All miner-populated Optional fields should default to None."""
        s = WorkflowSynapse()
        assert s.miner_uid is None
        assert s.scoring_version is None
        assert s.workflow_plan is None
        assert s.total_estimated_cost is None
        assert s.total_estimated_latency is None
        assert s.confidence is None
        assert s.reasoning is None

    def test_validator_populates_fields(self):
        """Validator should be able to set all task fields."""
        s = WorkflowSynapse(
            task_id="test-001",
            task_type="code_generation_pipeline",
            description="Generate a REST API",
            quality_criteria={"test_coverage": ">80%"},
            constraints={"max_budget_tao": 0.05, "max_latency_seconds": 10.0},
            available_tools={"SN1": {"type": "text_generation"}},
            send_block=12345,
        )
        assert s.task_id == "test-001"
        assert s.task_type == "code_generation_pipeline"
        assert s.constraints["max_budget_tao"] == 0.05
        assert s.send_block == 12345

    def test_miner_populates_response(self):
        """Miner should be able to set all response fields."""
        s = WorkflowSynapse(task_id="test-001")
        s.miner_uid = 42
        s.scoring_version = "1.0.0"
        s.workflow_plan = {
            "nodes": [{"id": "step_1", "subnet": "SN1", "action": "generate"}],
            "edges": [],
            "error_handling": {},
        }
        s.total_estimated_cost = 0.007
        s.total_estimated_latency = 4.3
        s.confidence = 0.88
        s.reasoning = "Sequential pipeline"

        assert s.miner_uid == 42
        assert s.scoring_version == "1.0.0"
        assert len(s.workflow_plan["nodes"]) == 1
        assert s.total_estimated_cost == 0.007
        assert s.confidence == 0.88

    def test_deserialize_returns_self(self):
        """deserialize() should return the synapse itself."""
        s = WorkflowSynapse(task_id="test-001")
        result = s.deserialize()
        assert result is s

    def test_workflow_plan_with_edges(self):
        """Test a multi-step workflow plan with DataRef edges."""
        plan = {
            "nodes": [
                {"id": "step_1", "subnet": "SN1", "action": "generate_code",
                 "params": {"prompt": "Generate FastAPI...", "max_tokens": 2000}},
                {"id": "step_2", "subnet": "SN62", "action": "review_code",
                 "params": {"code_input": "${step_1.output.text}"}},
                {"id": "step_3", "subnet": "SN45", "action": "generate_tests",
                 "params": {"code_input": "${step_2.output.artifacts.code}"}},
            ],
            "edges": [
                {"from": "step_1", "to": "step_2"},
                {"from": "step_2", "to": "step_3"},
            ],
            "error_handling": {
                "step_1": {"retry_count": 2},
                "step_2": {"retry_count": 1, "timeout_seconds": 3.0},
            },
        }

        s = WorkflowSynapse(task_id="test-002")
        s.workflow_plan = plan
        assert len(s.workflow_plan["nodes"]) == 3
        assert len(s.workflow_plan["edges"]) == 2
        assert s.workflow_plan["error_handling"]["step_1"]["retry_count"] == 2


class TestDummyBackCompat:
    """Ensure legacy Dummy synapse still works."""

    def test_dummy_basic(self):
        d = Dummy(dummy_input=5)
        assert d.dummy_input == 5
        assert d.dummy_output is None

    def test_dummy_deserialize(self):
        d = Dummy(dummy_input=5)
        d.dummy_output = 10
        assert d.deserialize() == 10

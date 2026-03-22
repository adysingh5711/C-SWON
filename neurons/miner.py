# The MIT License (MIT)
# Copyright © 2024 C-SWON Contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""
C-SWON Miner Neuron — entry point.

The miner receives task packages (WorkflowSynapse) from validators and returns
workflow plans: DAGs of subnet calls with estimated cost, latency, and error handling.

Run: python neurons/miner.py --netuid <netuid> --wallet.name <name> --subtensor.network <test|finney>
"""

import time
import typing

import bittensor as bt

import cswon
from cswon.protocol import WorkflowSynapse
from cswon.base.miner import BaseMinerNeuron
from cswon.validator.config import SCORING_VERSION
from cswon.miner.subnet_profiler import SubnetProfiler


class Miner(BaseMinerNeuron):
    """
    C-SWON Miner: designs optimal workflow DAGs for multi-subnet task execution.

    The miner's forward() receives a task package and returns a DataRef-compliant
    workflow plan with nodes, edges, error handling, and cost/latency estimates.
    """

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)
        # Subnet profiler: tracks historical cost/latency per partner subnet (readme §3.6)
        self.profiler = SubnetProfiler()
        bt.logging.info("C-SWON Miner initialised")

    async def forward(
        self, synapse: WorkflowSynapse
    ) -> WorkflowSynapse:
        """
        Process incoming task package and return a workflow plan (readme §3.3).

        The miner analyses the task, available tools (subnets), and constraints
        to design an optimal DAG of subnet calls.

        Args:
            synapse: WorkflowSynapse with validator-populated task fields.

        Returns:
            WorkflowSynapse with miner-populated workflow plan fields.
        """
        bt.logging.info(
            f"Received task: {synapse.task_id} type={synapse.task_type}"
        )

        # Refresh subnet profiles every 100 blocks (readme §3.6)
        self.profiler.refresh(self.metagraph, self.block)

        # Enrich available_tools with locally observed history before workflow design
        enriched_tools = self.profiler.enrich_tools(synapse.available_tools or {})

        # Build workflow plan based on task type and enriched tool profiles
        workflow_plan = self._design_workflow(synapse, enriched_tools)

        # Populate miner response fields
        synapse.miner_uid = self.uid
        synapse.scoring_version = SCORING_VERSION
        synapse.workflow_plan = workflow_plan
        synapse.total_estimated_cost = self._estimate_total_cost(workflow_plan)
        synapse.total_estimated_latency = self._estimate_total_latency(workflow_plan)
        synapse.confidence = self._compute_confidence(synapse, workflow_plan)
        synapse.reasoning = self._generate_reasoning(synapse, workflow_plan)

        bt.logging.info(
            f"Returning workflow plan for {synapse.task_id}: "
            f"{len(workflow_plan.get('nodes', []))} nodes, "
            f"est_cost={synapse.total_estimated_cost:.4f}τ"
        )

        # Fix 1.3: record execution observations so the profiler builds real history.
        # In this testnet implementation the executor is sandboxed/mock, so we record
        # the estimated values as a proxy until live execution is wired in (fix 1.4).
        for node in workflow_plan.get("nodes", []):
            subnet_id = node.get("subnet", "")
            if subnet_id:
                self.profiler.record_observation(
                    subnet_id=subnet_id,
                    cost=node.get("estimated_cost", 0.0),
                    latency=node.get("estimated_latency", 0.0),
                    success=True,
                )

        return synapse

    def _design_workflow(self, synapse: WorkflowSynapse, enriched_tools: dict = None) -> dict:
        """
        Design a workflow DAG based on task type and enriched tool profiles.

        This is the core miner intelligence — a simple heuristic planner
        that selects subnets based on task requirements and builds sequential
        or parallel DAGs.
        """
        available_tools = enriched_tools if enriched_tools is not None else (synapse.available_tools or {})
        constraints = synapse.constraints or {}
        allowed_subnets = constraints.get("allowed_subnets", list(available_tools.keys()))
        task_type = synapse.task_type

        nodes = []
        edges = []
        error_handling = {}

        if task_type in ("code_generation_pipeline", "code"):
            nodes, edges, error_handling = self._code_pipeline(
                synapse.description, available_tools, allowed_subnets
            )
        elif task_type in ("rag", "rag_pipeline"):
            nodes, edges, error_handling = self._rag_pipeline(
                synapse.description, available_tools, allowed_subnets
            )
        elif task_type in ("agent", "agent_task"):
            nodes, edges, error_handling = self._agent_pipeline(
                synapse.description, available_tools, allowed_subnets
            )
        elif task_type in ("data_transform", "data_transform_pipeline"):
            nodes, edges, error_handling = self._data_transform_pipeline(
                synapse.description, available_tools, allowed_subnets
            )
        else:
            # Generic fallback: single text generation step
            nodes, edges, error_handling = self._generic_pipeline(
                synapse.description, available_tools, allowed_subnets
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "error_handling": error_handling,
        }

    def _code_pipeline(self, description, tools, allowed):
        """Code generation pipeline: generate → review → test (readme §3.3 example)."""
        nodes = []
        edges = []
        error_handling = {}

        # Step 1: Code generation
        gen_subnet = self._pick_subnet(tools, allowed, ["text_generation", "inference", "code_generation"])
        if gen_subnet:
            cost_info = tools.get(gen_subnet, {})
            nodes.append({
                "id": "step_1", "subnet": gen_subnet, "action": "generate_code",
                "params": {"prompt": description, "max_tokens": 2000},
                "estimated_cost": cost_info.get("avg_cost", 0.001),
                "estimated_latency": cost_info.get("avg_latency", 0.5),
            })

        # Step 2: Code review
        review_subnet = self._pick_subnet(tools, allowed, ["code_review"])
        if review_subnet and nodes:
            cost_info = tools.get(review_subnet, {})
            nodes.append({
                "id": "step_2", "subnet": review_subnet, "action": "review_code",
                "params": {
                    "code_input": "${step_1.output.text}",
                    "review_criteria": ["security", "style", "correctness"],
                },
                "estimated_cost": cost_info.get("avg_cost", 0.003),
                "estimated_latency": cost_info.get("avg_latency", 1.2),
            })
            edges.append({"from": "step_1", "to": "step_2"})
            error_handling["step_1"] = {"retry_count": 2}
            error_handling["step_2"] = {"retry_count": 1, "timeout_seconds": 3.0}

        # Step 3: Testing
        test_subnet = self._pick_subnet(tools, allowed, ["code_testing", "testing"])
        if test_subnet and len(nodes) >= 2:
            cost_info = tools.get(test_subnet, {})
            nodes.append({
                "id": "step_3", "subnet": test_subnet, "action": "generate_tests",
                "params": {
                    "code_input": "${step_2.output.artifacts.code}",
                    "coverage_target": 0.85,
                },
                "estimated_cost": cost_info.get("avg_cost", 0.002),
                "estimated_latency": cost_info.get("avg_latency", 2.0),
            })
            edges.append({"from": "step_2", "to": "step_3"})

        return nodes, edges, error_handling

    def _rag_pipeline(self, description, tools, allowed):
        """RAG pipeline: retrieve → generate → fact-check."""
        nodes = []
        edges = []
        error_handling = {}

        gen_subnet = self._pick_subnet(tools, allowed, ["text_generation", "inference"])
        if gen_subnet:
            cost_info = tools.get(gen_subnet, {})
            nodes.append({
                "id": "step_1", "subnet": gen_subnet, "action": "generate_answer",
                "params": {"prompt": description, "max_tokens": 1000},
                "estimated_cost": cost_info.get("avg_cost", 0.001),
                "estimated_latency": cost_info.get("avg_latency", 0.5),
            })
            error_handling["step_1"] = {"retry_count": 1}

        fact_subnet = self._pick_subnet(tools, allowed, ["fact_checking"])
        if fact_subnet and nodes:
            cost_info = tools.get(fact_subnet, {})
            nodes.append({
                "id": "step_2", "subnet": fact_subnet, "action": "verify_facts",
                "params": {"text_input": "${step_1.output.text}"},
                "estimated_cost": cost_info.get("avg_cost", 0.0015),
                "estimated_latency": cost_info.get("avg_latency", 0.8),
            })
            edges.append({"from": "step_1", "to": "step_2"})

        return nodes, edges, error_handling

    def _agent_pipeline(self, description, tools, allowed):
        """Agent task: plan → execute → verify."""
        nodes = []
        edges = []
        error_handling = {}

        gen_subnet = self._pick_subnet(tools, allowed, ["text_generation", "inference", "agent"])
        if gen_subnet:
            cost_info = tools.get(gen_subnet, {})
            nodes.append({
                "id": "step_1", "subnet": gen_subnet, "action": "plan_and_execute",
                "params": {"task_description": description},
                "estimated_cost": cost_info.get("avg_cost", 0.002),
                "estimated_latency": cost_info.get("avg_latency", 1.0),
            })
            error_handling["step_1"] = {"retry_count": 2}

        return nodes, edges, error_handling

    def _data_transform_pipeline(self, description, tools, allowed):
        """Data transform: process → validate."""
        nodes = []
        edges = []
        error_handling = {}

        gen_subnet = self._pick_subnet(tools, allowed, ["text_generation", "inference", "data_processing"])
        if gen_subnet:
            cost_info = tools.get(gen_subnet, {})
            nodes.append({
                "id": "step_1", "subnet": gen_subnet, "action": "transform_data",
                "params": {"instruction": description},
                "estimated_cost": cost_info.get("avg_cost", 0.001),
                "estimated_latency": cost_info.get("avg_latency", 0.5),
            })

        return nodes, edges, error_handling

    def _generic_pipeline(self, description, tools, allowed):
        """Fallback single-step pipeline."""
        nodes = []
        edges = []
        error_handling = {}

        subnet = self._pick_subnet(tools, allowed, ["text_generation", "inference"])
        if subnet:
            cost_info = tools.get(subnet, {})
            nodes.append({
                "id": "step_1", "subnet": subnet, "action": "process",
                "params": {"prompt": description},
                "estimated_cost": cost_info.get("avg_cost", 0.001),
                "estimated_latency": cost_info.get("avg_latency", 0.5),
            })

        return nodes, edges, error_handling

    def _pick_subnet(self, tools, allowed, preferred_types, max_budget=None):
        """Pick the best available subnet ranked by avg_cost then avg_latency (fix 2.2)."""
        candidates = []
        for subnet_id, info in tools.items():
            if subnet_id in allowed and info.get("type") in preferred_types:
                candidates.append((
                    subnet_id,
                    info.get("avg_cost", 999),
                    info.get("avg_latency", 999),
                ))
        if not candidates:
            # Fallback: any allowed subnet regardless of type
            candidates = [
                (s, tools[s].get("avg_cost", 999), tools[s].get("avg_latency", 999))
                for s in allowed if s in tools
            ]
        if not candidates:
            return list(tools.keys())[0] if tools else None
        # Sort by cost (primary), then latency (secondary)
        candidates.sort(key=lambda x: (x[1], x[2]))
        return candidates[0][0]

    def _estimate_total_cost(self, workflow_plan):
        """Sum estimated costs across all nodes."""
        return sum(
            n.get("estimated_cost", 0.0) for n in workflow_plan.get("nodes", [])
        )

    def _estimate_total_latency(self, workflow_plan):
        """Estimate total latency using tier-max for parallel DAGs (fix 2.3).

        For nodes in the same parallel tier, the effective latency is max()
        not sum(), since they execute concurrently.
        """
        from cswon.validator.executor import topological_sort_tiers
        nodes = workflow_plan.get("nodes", [])
        edges = workflow_plan.get("edges", [])
        if not nodes:
            return 0.0
        node_map = {n["id"]: n for n in nodes}
        tiers = topological_sort_tiers(nodes, edges)
        total = 0.0
        for tier in tiers:
            tier_max = max(
                node_map[nid].get("estimated_latency", 0.0) for nid in tier
            )
            total += tier_max
        return total

    def _compute_confidence(self, synapse, plan):
        """Compute a confidence score based on plan quality."""
        nodes = plan.get("nodes", [])
        if not nodes:
            return 0.1

        # Higher confidence if more nodes cover the task
        coverage = min(1.0, len(nodes) / 3)  # 3 nodes is ideal
        # Higher confidence if costs are within budget
        total_cost = self._estimate_total_cost(plan)
        max_budget = synapse.constraints.get("max_budget_tao", 1.0)
        cost_ratio = 1.0 - min(1.0, total_cost / max_budget) if max_budget > 0 else 0.5

        return round(0.5 * coverage + 0.5 * cost_ratio, 2)

    def _generate_reasoning(self, synapse, plan):
        """Generate a brief reasoning explanation."""
        nodes = plan.get("nodes", [])
        if not nodes:
            return "No viable workflow found for the given constraints."

        steps = " → ".join(n.get("action", "?") for n in nodes)
        return f"Sequential pipeline: {steps}. Selected based on cost/latency profile."

    async def blacklist(
        self, synapse: WorkflowSynapse
    ) -> typing.Tuple[bool, str]:
        """
        Blacklist non-registered or non-validator entities.
        Only validators should query miners (readme §3.3).
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning("Request without dendrite or hotkey")
            return True, "Missing dendrite or hotkey"

        # Check if the requester is registered
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            if not self.config.blacklist.allow_non_registered:
                bt.logging.trace(
                    f"Blacklisting unregistered hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Unrecognized hotkey"

        # Optionally enforce validator permit
        if self.config.blacklist.force_validator_permit:
            uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            if not self.metagraph.validator_permit[uid]:
                bt.logging.warning(
                    f"Blacklisting non-validator hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Non-validator hotkey"

        bt.logging.trace(
            f"Accepting request from {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized"

    async def priority(self, synapse: WorkflowSynapse) -> float:
        """Priority based on stake — higher stake validators get priority."""
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            return 0.0

        try:
            caller_uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            priority = float(self.metagraph.S[caller_uid])
            bt.logging.trace(
                f"Priority for {synapse.dendrite.hotkey}: {priority}"
            )
            return priority
        except ValueError:
            return 0.0


# Entry point
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info(f"C-SWON Miner running... block={miner.block}")
            time.sleep(5)

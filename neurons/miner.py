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
from bittensor.core.axon import Axon

def _safe_axon_del(self):
    try:
        if hasattr(self, "fast_server") and self.fast_server is not None:
            self.stop()
    except Exception:
        pass

Axon.__del__ = _safe_axon_del


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
        await self.profiler.refresh_async(self.metagraph, self.block)

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
        available_tools = enriched_tools or synapse.available_tools or {}
        constraints = synapse.constraints or {}
        allowed_subnets = set(constraints.get("allowed_subnets", list(available_tools.keys())))
        desc = synapse.description.lower()

        # Decompose description into capability requirements
        required_caps = self._infer_required_capabilities(desc)

        nodes, edges, error_handling = [], [], {}
        prev_id = None

        for i, cap in enumerate(required_caps):
            node_id = f"step_{i+1}"
            subnet = self._pick_subnet_by_capability(available_tools, allowed_subnets, cap)
            if not subnet:
                continue
            info = available_tools.get(subnet, {})
            node = {
                "id": node_id,
                "subnet": subnet,
                "action": cap,
                "params": self._build_params(cap, desc, prev_id),
                "estimated_cost": info.get("avg_cost", 0.001),
                "estimated_latency": info.get("avg_latency", 0.5),
            }
            nodes.append(node)
            if prev_id:
                edges.append({"from": prev_id, "to": node_id})
            error_handling[node_id] = {"retry_count": 1 if i == 0 else 0, "timeout_seconds": 5.0}
            prev_id = node_id

        if not nodes:
            gnodes, gedges, gerr = self._generic_pipeline(synapse.description, available_tools, list(allowed_subnets))
            return {"nodes": gnodes, "edges": gedges, "error_handling": gerr}

        return {"nodes": nodes, "edges": edges, "error_handling": error_handling}

    def _infer_required_capabilities(self, desc: str) -> list:
        """
        Extract ordered capability chain from the task description.
        Returns a list of action strings that form the DAG nodes.
        Uses multi-token phrase matching to prevent keyword collisions (fix 6).
        """
        desc = desc.lower()
        caps = []
        # Retrieval signals
        if any(w in desc for w in ["retrieve context", "search web", "fetch data", "find documents", "lookup reference"]):
            caps.append("retrieve_context")
        # Code signals
        if any(w in desc for w in ["write source code", "implement function", "python class", "write script", "python program", "python code", "generate code"]):
            caps.append("generate_code")
            if any(w in desc for w in ["unit test", "write tests", "test coverage"]):
                caps.append("generate_tests")
            if any(w in desc for w in ["review code", "lint code", "style check", "code quality"]):
                caps.append("review_code")
        # Transform signals
        if any(w in desc for w in ["transform data", "convert format", "parse json", "extract fields", "format output", "data schema"]):
            caps.append("transform_data")
        # Fact-check signals
        if any(w in desc for w in ["verify claim", "fact check", "validate statement", "ground truth"]):
            caps.append("verify_facts")
        # Reasoning / generation signals (always add if nothing else matched)
        if any(w in desc for w in ["summarize text", "answer question", "explain concept", "generate report", "write essay", "describe image"]) or not caps:
            caps.append("generate_answer")
        return caps if caps else ["generate_answer"]

    def _build_params(self, action: str, desc: str, prev_id) -> dict:
        base = {"instruction": desc}
        if prev_id:
            base["input"] = f"${{{prev_id}.output.text}}"
        if action == "generate_code":
            base["max_tokens"] = 2000
        elif action == "generate_answer":
            base["max_tokens"] = 1000
        return base

    def _pick_subnet_by_capability(self, tools: dict, allowed: set, action: str) -> str:
        """
        Map action → preferred subnet type tags, then rank candidates by
        (avg_cost, avg_latency) from SubnetProfiler history.
        """
        action_type_map = {
            "generate_code":    ["code_generation", "text_generation", "inference"],
            "generate_tests":   ["code_testing", "testing", "text_generation"],
            "review_code":      ["code_review", "text_generation"],
            "retrieve_context": ["retrieval", "search", "text_generation"],
            "transform_data":   ["data_processing", "text_generation", "inference"],
            "generate_answer":  ["text_generation", "inference"],
            "verify_facts":     ["fact_checking", "text_generation"],
            "plan_and_execute": ["agent", "text_generation", "inference"],
        }
        preferred = action_type_map.get(action, ["text_generation", "inference"])
        candidates = [
            (sid, tools[sid].get("avg_cost", 999), tools[sid].get("avg_latency", 999))
            for sid in allowed if sid in tools and tools[sid].get("type") in preferred
        ]
        if not candidates:
            candidates = [
                (sid, tools[sid].get("avg_cost", 999), tools[sid].get("avg_latency", 999))
                for sid in allowed if sid in tools
            ]
        if not candidates:
            return list(tools.keys())[0] if tools else None
        candidates.sort(key=lambda x: (x[1], x[2]))
        return candidates[0][0]

    def _generic_pipeline(self, description, tools, allowed):
        """Fallback single-step pipeline."""
        nodes = []
        edges = []
        error_handling = {}

        subnet = self._pick_subnet_by_capability(tools, set(allowed), "generate_answer")
        if subnet:
            cost_info = tools.get(subnet, {})
            nodes.append({
                "id": "step_1", "subnet": subnet, "action": "process",
                "params": {"prompt": description},
                "estimated_cost": cost_info.get("avg_cost", 0.001),
                "estimated_latency": cost_info.get("avg_latency", 0.5),
            })

        return nodes, edges, error_handling

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

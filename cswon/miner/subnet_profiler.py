# C-SWON Miner — Subnet Profiler
# Implements independent cost/latency profiling of partner subnets (readme §3.6).

from collections import defaultdict, deque
from typing import Dict, List, Optional
import bittensor as bt

# How many observations to keep per subnet in the rolling history
_HISTORY_LEN = 50

# Minimum observations before local data overrides validator hints
_MIN_OBSERVATIONS = 5


class SubnetProfiler:
    """
    Tracks historical cost and latency data for partner subnets (readme §3.6).
    Simplified for MVP to remove metagraph probing (perplex_fix4 §6).
    """

    def __init__(self):
        self._cost_history = defaultdict(lambda: deque(maxlen=_HISTORY_LEN))
        self._latency_history = defaultdict(lambda: deque(maxlen=_HISTORY_LEN))
        self._reliability_history = defaultdict(lambda: deque(maxlen=_HISTORY_LEN))

    async def refresh_async(self, metagraph, current_block: int) -> None:
        """
        MVP: no probing, no synthetic partner discovery (perplex_fix4 §6).
        """
        return

    def record_observation(
        self, subnet_id: str, cost: float, latency: float, success: bool
    ) -> None:
        """
        Record a real observation from a completed subnet call.
        """
        subnet_id = subnet_id.lower()
        self._cost_history[subnet_id].append(cost)
        self._latency_history[subnet_id].append(latency)
        self._reliability_history[subnet_id].append(success)

    def enrich_tools(self, validator_tools: dict) -> dict:
        """
        Merge validator-provided tool hints with locally observed history.
        """
        if not validator_tools:
            return {}

        enriched = {}
        for subnet_id, hints in validator_tools.items():
            subnet_id = subnet_id.lower()
            enriched[subnet_id] = dict(hints)

            costs = list(self._cost_history.get(subnet_id, []))
            lats = list(self._latency_history.get(subnet_id, []))
            rels = list(self._reliability_history.get(subnet_id, []))

            if len(costs) >= _MIN_OBSERVATIONS:
                enriched[subnet_id]["avg_cost"] = sum(costs) / len(costs)
            if len(lats) >= _MIN_OBSERVATIONS:
                enriched[subnet_id]["avg_latency"] = sum(lats) / len(lats)
            if len(rels) >= _MIN_OBSERVATIONS:
                enriched[subnet_id]["reliability"] = sum(rels) / len(rels)

        return enriched

# C-SWON Miner — Subnet Profiler
# Implements independent cost/latency profiling of partner subnets (readme §3.6).

"""
SubnetProfiler maintains locally-tracked cost and latency history for partner
subnets. Miners refresh this cache every 100 blocks by sampling the metagraph.

In v1 (testnet), actual inter-subnet probe calls are not made — the profiler
enriches validator-provided hints with any locally observed history. Once a
miner has seen enough real execution feedback (future v2), local history will
replace validator hints entirely.
"""

import time
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

    Usage:
        profiler = SubnetProfiler()
        # In the miner run loop, every 100 blocks:
        profiler.refresh(metagraph, current_block)
        # Before designing a workflow:
        enriched_tools = profiler.enrich_tools(synapse.available_tools)
    """

    def __init__(self):
        # subnet_id → deque of observed costs
        self._cost_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_HISTORY_LEN)
        )
        # subnet_id → deque of observed latencies (seconds)
        self._latency_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_HISTORY_LEN)
        )
        # subnet_id → deque of reliability booleans (True=success)
        self._reliability_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_HISTORY_LEN)
        )

        self._last_refresh_block: int = -1

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self, metagraph: "bt.metagraph", current_block: int) -> None:
        """
        Refresh subnet profiles from the metagraph every 100 blocks (readme §3.6, fix 2.1).

        Iterates serving axons in the metagraph and records a lightweight latency
        probe observation for each. In v1 (testnet), a socket connect is used as
        a proxy for round-trip latency. In v2, a real HealthSynapse dendrite
        call will replace this.

        Args:
            metagraph: The current metagraph snapshot.
            current_block: The current Bittensor block number.
        """
        if current_block - self._last_refresh_block < 100:
            return  # Not yet time to refresh

        self._last_refresh_block = current_block

        bt.logging.info(
            f"SubnetProfiler: refreshing at block {current_block}. "
            f"Currently tracking {len(self._cost_history)} subnets."
        )

        import socket
        probed = 0
        for uid in range(int(metagraph.n)):
            axon = metagraph.axons[uid]
            if not axon.is_serving:
                continue
            subnet_id = f"SN{uid}"
            t0 = time.time()
            try:
                # Lightweight TCP connect probe — measures reachability + round-trip
                with socket.create_connection((axon.ip, axon.port), timeout=2.0):
                    pass
                latency = time.time() - t0
                self.record_observation(subnet_id, cost=0.0, latency=latency, success=True)
            except Exception:
                latency = time.time() - t0
                self.record_observation(subnet_id, cost=0.0, latency=latency, success=False)
            probed += 1

        bt.logging.debug(
            f"SubnetProfiler: probed {probed} serving axons at block {current_block}."
        )

    def record_observation(
        self,
        subnet_id: str,
        cost: float,
        latency: float,
        success: bool,
    ) -> None:
        """
        Record a real observation from a completed subnet call.

        Call this after each executor step completes to build local history.

        Args:
            subnet_id: The subnet identifier (e.g. "SN1", "SN62").
            cost: Actual TAO cost of this call.
            latency: Wall-clock seconds for this call.
            success: Whether the call succeeded.
        """
        self._cost_history[subnet_id].append(cost)
        self._latency_history[subnet_id].append(latency)
        self._reliability_history[subnet_id].append(success)

    # ── Enrichment ─────────────────────────────────────────────────────────

    def enrich_tools(self, validator_tools: dict) -> dict:
        """
        Merge validator-provided tool hints with locally observed history.

        Locally-measured averages override validator hints once we have
        at least MIN_OBSERVATIONS observations for a given subnet.

        Args:
            validator_tools: The available_tools dict from the WorkflowSynapse.

        Returns:
            An enriched copy of the tools dict with local data merged in.
        """
        if not validator_tools:
            return {}

        enriched = {}
        for subnet_id, hints in validator_tools.items():
            enriched[subnet_id] = dict(hints)  # copy validator hints

            # Override with local history if we have enough observations
            cost_history = list(self._cost_history.get(subnet_id, []))
            latency_history = list(self._latency_history.get(subnet_id, []))
            reliability_history = list(self._reliability_history.get(subnet_id, []))

            if len(cost_history) >= _MIN_OBSERVATIONS:
                local_avg_cost = sum(cost_history) / len(cost_history)
                bt.logging.trace(
                    f"SubnetProfiler: overriding {subnet_id} avg_cost "
                    f"{hints.get('avg_cost', '?')} → {local_avg_cost:.5f} "
                    f"(from {len(cost_history)} obs)"
                )
                enriched[subnet_id]["avg_cost"] = local_avg_cost

            if len(latency_history) >= _MIN_OBSERVATIONS:
                local_avg_latency = sum(latency_history) / len(latency_history)
                enriched[subnet_id]["avg_latency"] = local_avg_latency

            if len(reliability_history) >= _MIN_OBSERVATIONS:
                local_reliability = sum(reliability_history) / len(reliability_history)
                enriched[subnet_id]["reliability"] = local_reliability

        return enriched

    def get_profile_summary(self) -> Dict[str, dict]:
        """Return a summary of all tracked subnet profiles (for logging)."""
        summary = {}
        for subnet_id in set(
            list(self._cost_history.keys())
            + list(self._latency_history.keys())
        ):
            cost_h = list(self._cost_history.get(subnet_id, []))
            lat_h = list(self._latency_history.get(subnet_id, []))
            rel_h = list(self._reliability_history.get(subnet_id, []))
            summary[subnet_id] = {
                "observations": len(cost_h),
                "avg_cost": sum(cost_h) / len(cost_h) if cost_h else None,
                "avg_latency": sum(lat_h) / len(lat_h) if lat_h else None,
                "reliability": sum(rel_h) / len(rel_h) if rel_h else None,
            }
        return summary

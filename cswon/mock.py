"""
C-SWON Mock Classes

Provides mock implementations of Subtensor, Metagraph, and Dendrite
for local development and testing without a live Bittensor network.

Updated to use WorkflowSynapse instead of the legacy Dummy protocol.
"""

import time
import asyncio
import random
import copy

import bittensor as bt

from typing import List

from cswon.protocol import WorkflowSynapse
from cswon.validator.config import SCORING_VERSION


class MockSubtensor(bt.MockSubtensor):
    """Mock subtensor for local testing."""

    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)

        # Register ourself (the validator) as a neuron at uid=0
        if wallet is not None:
            self.force_register_neuron(
                netuid=netuid,
                hotkey=wallet.hotkey.ss58_address,
                coldkey=wallet.coldkey.ss58_address,
                balance=100000,
                stake=100000,
            )

        # Register n mock neurons who will be miners
        for i in range(1, n + 1):
            self.force_register_neuron(
                netuid=netuid,
                hotkey=f"miner-hotkey-{i}",
                coldkey="mock-coldkey",
                balance=100000,
                stake=100000,
            )


class MockMetagraph(bt.metagraph):
    """Mock metagraph for local testing."""

    def __init__(self, netuid=1, network="mock", subtensor=None):
        super().__init__(netuid=netuid, network=network, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        bt.logging.info(f"MockMetagraph: {self}")
        bt.logging.info(f"Mock Axons: {self.axons}")


class MockDendrite(bt.dendrite):
    """
    Mock dendrite that returns plausible WorkflowSynapse responses
    without making real network calls. Used for local testing.
    """

    def __init__(self, wallet):
        super().__init__(wallet)

    async def forward(
        self,
        axons: List[bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 12,
        deserialize: bool = True,
        run_async: bool = True,
        streaming: bool = False,
    ):
        if streaming:
            raise NotImplementedError("Streaming not implemented yet.")

        async def query_all_axons(streaming: bool):
            """Queries all axons for mock responses."""

            async def single_axon_response(i, axon):
                """Generate a mock response for a single axon."""
                start_time = time.time()
                s = synapse.copy()
                s = self.preprocess_synapse_for_request(axon, s, timeout)
                process_time = random.random()

                if process_time < timeout:
                    s.dendrite.process_time = str(time.time() - start_time)
                    s.dendrite.status_code = 200
                    s.dendrite.status_message = "OK"

                    # Handle WorkflowSynapse responses
                    if isinstance(s, WorkflowSynapse):
                        s.miner_uid = i
                        s.scoring_version = SCORING_VERSION
                        s.workflow_plan = _generate_mock_workflow(s)
                        s.total_estimated_cost = random.uniform(0.005, 0.02)
                        s.total_estimated_latency = random.uniform(1.0, 5.0)
                        s.confidence = random.uniform(0.7, 0.95)
                        s.reasoning = f"Mock sequential pipeline for {s.task_type}"
                    else:
                        # Legacy Dummy protocol support
                        if hasattr(s, "dummy_input") and hasattr(s, "dummy_output"):
                            s.dummy_output = s.dummy_input * 2
                else:
                    s.dendrite.status_code = 408
                    s.dendrite.status_message = "Timeout"

                    if isinstance(s, WorkflowSynapse):
                        pass  # Leave Optional fields as None
                    elif hasattr(s, "dummy_output"):
                        s.dummy_output = 0

                    s.dendrite.process_time = str(timeout)

                if deserialize:
                    return s.deserialize()
                else:
                    return s

            return await asyncio.gather(
                *(
                    single_axon_response(i, target_axon)
                    for i, target_axon in enumerate(axons)
                )
            )

        return await query_all_axons(streaming)

    def __str__(self) -> str:
        return "MockDendrite({})".format(self.keypair.ss58_address)


def _generate_mock_workflow(synapse: WorkflowSynapse) -> dict:
    """Generate a plausible mock workflow plan based on the task type."""
    task_type = synapse.task_type
    available = synapse.available_tools or {}
    subnets = list(available.keys()) or ["SN1"]

    if task_type in ("code_generation_pipeline", "code"):
        return {
            "nodes": [
                {
                    "id": "step_1", "subnet": subnets[0], "action": "generate_code",
                    "params": {"prompt": synapse.description, "max_tokens": 2000},
                    "estimated_cost": 0.001, "estimated_latency": 0.5,
                },
                {
                    "id": "step_2", "subnet": subnets[1] if len(subnets) > 1 else subnets[0],
                    "action": "review_code",
                    "params": {"code_input": "${step_1.output.text}"},
                    "estimated_cost": 0.003, "estimated_latency": 1.2,
                },
            ],
            "edges": [{"from": "step_1", "to": "step_2"}],
            "error_handling": {"step_1": {"retry_count": 2}},
        }
    else:
        return {
            "nodes": [
                {
                    "id": "step_1", "subnet": subnets[0], "action": "process",
                    "params": {"prompt": synapse.description},
                    "estimated_cost": 0.001, "estimated_latency": 0.5,
                },
            ],
            "edges": [],
            "error_handling": {},
        }

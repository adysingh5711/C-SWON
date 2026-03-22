# C-SWON Validator — Async Query Loop
# Implements async miner querying with sub-block timeout (readme §4.1).

"""
Async query loop with QUERY_TIMEOUT_S < 12s (1 block) ceiling.
Stamps send_block onto responses at dispatch time.
Validates dendrite.hotkey matches queried UID (readme §4.8 step 2).
"""

import asyncio
from typing import List, Optional

import bittensor as bt

from cswon.protocol import WorkflowSynapse
from cswon.validator.config import QUERY_TIMEOUT_S


async def query_miners(
    dendrite: bt.dendrite,
    axons: List[bt.AxonInfo],
    synapse: WorkflowSynapse,
    send_block: int,
    timeout: float = QUERY_TIMEOUT_S,
) -> List[WorkflowSynapse]:
    """
    Asynchronously query miners with sub-block timeout (readme §4.1).

    Args:
        dendrite: The dendrite client for network queries.
        axons: List of target miner axons.
        synapse: The WorkflowSynapse with task package populated.
        send_block: The block height at time of dispatch.
        timeout: Query timeout in seconds (default: 9s, must be < 12s per readme).

    Returns:
        List of WorkflowSynapse responses from miners.

    Note:
        send_block is stamped onto each response at dispatch time.
        The score aggregation pipeline reads response.send_block, not
        current_block, so a reply arriving 11s after send is still
        scored against the correct task.
    """
    # Stamp the send_block before dispatch
    synapse.send_block = send_block

    responses = await dendrite.forward(
        axons=axons,
        synapse=synapse,
        timeout=timeout,
        deserialize=False,  # keep full synapse for validation
    )

    # Attribute ALL responses to send_block, not receipt block
    for r in responses:
        if r is not None:
            r.send_block = send_block

    return responses


def validate_response(
    response: WorkflowSynapse,
    expected_hotkey: str,
    metagraph: "bt.metagraph",
) -> bool:
    """
    Validate a miner response before accepting (readme §4.8 step 2).

    For each response, validate that the signed dendrite.hotkey matches
    the queried UID in the metagraph. Discard any response whose hotkey
    does not match, even if the JSON is well-formed.

    Also checks that all required miner fields are populated.

    Args:
        response: The WorkflowSynapse response from a miner.
        expected_hotkey: The hotkey we expected based on the queried UID.
        metagraph: The metagraph for verification.

    Returns:
        True if the response is valid and should be accepted.
    """
    # Check dendrite hotkey matches expected
    if response.dendrite is None or response.dendrite.hotkey is None:
        bt.logging.debug("Response missing dendrite/hotkey, rejecting")
        return False

    if response.dendrite.hotkey != expected_hotkey:
        bt.logging.warning(
            f"Response hotkey mismatch: expected {expected_hotkey}, "
            f"got {response.dendrite.hotkey}. Rejecting."
        )
        return False

    # Check all required miner fields are populated (readme §3.2b)
    required_fields = [
        "miner_uid",
        "scoring_version",
        "workflow_plan",
        "total_estimated_cost",
        "total_estimated_latency",
        "confidence",
        "reasoning",
    ]
    for field in required_fields:
        if getattr(response, field, None) is None:
            bt.logging.debug(
                f"Response from {expected_hotkey} missing required field '{field}', rejecting"
            )
            return False

    # Validate workflow_plan has required structure
    plan = response.workflow_plan
    if not isinstance(plan, dict):
        return False
    if "nodes" not in plan or "edges" not in plan:
        bt.logging.debug("workflow_plan missing 'nodes' or 'edges', rejecting")
        return False

    return True

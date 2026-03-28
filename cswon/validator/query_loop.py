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
    dendrite: bt.Dendrite,
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


def _validate_workflow_plan(plan: dict) -> bool:
    """
    Structural integrity check for a miner's workflow_plan before execution.
    Returns False and logs the reason if the plan is structurally invalid.
    """
    nodes = plan.get("nodes", [])
    edges = plan.get("edges", [])

    if not nodes:
        bt.logging.debug("workflow_plan has no nodes")
        return False

    # 1. Node count cap — prevent runaway mock latency accumulation on testnet
    MAX_NODES = 10
    if len(nodes) > MAX_NODES:
        bt.logging.debug(f"workflow_plan has {len(nodes)} nodes, max is {MAX_NODES}")
        return False

    # 2. Every node must have a non-empty string id, subnet, and action
    node_ids = []
    for n in nodes:
        if not isinstance(n, dict):
            bt.logging.debug("Node is not a dict")
            return False
        nid = n.get("id", "")
        if not isinstance(nid, str) or not nid.strip():
            bt.logging.debug(f"Node missing or empty id: {n}")
            return False
        if not n.get("subnet") or not n.get("action"):
            bt.logging.debug(f"Node {nid} missing subnet or action")
            return False
        node_ids.append(nid)

    # 3. No duplicate node IDs
    if len(node_ids) != len(set(node_ids)):
        bt.logging.debug(f"workflow_plan has duplicate node ids: {node_ids}")
        return False

    node_id_set = set(node_ids)

    # 4. Every edge must reference valid node IDs
    for edge in edges:
        if not isinstance(edge, dict):
            bt.logging.debug("Edge is not a dict")
            return False
        src = edge.get("from", "")
        dst = edge.get("to", "")
        if src not in node_id_set:
            bt.logging.debug(f"Edge references unknown source node: {src}")
            return False
        if dst not in node_id_set:
            bt.logging.debug(f"Edge references unknown target node: {dst}")
            return False
        if src == dst:
            bt.logging.debug(f"Self-loop detected on node: {src}")
            return False

    # 5. Acyclicity: topological sort must account for ALL nodes
    from cswon.validator.executor import topological_sort_tiers
    tiers = topological_sort_tiers(nodes, edges)
    sorted_node_count = sum(len(t) for t in tiers)
    if sorted_node_count != len(nodes):
        bt.logging.debug(
            f"DAG is cyclic or has disconnected nodes: "
            f"topo_sort returned {sorted_node_count} of {len(nodes)} nodes"
        )
        return False

    return True


def validate_response(
    response: WorkflowSynapse,
    expected_hotkey: str,
    metagraph: "bt.Metagraph",
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
    # The responder identity lives on the axon; dendrite.hotkey is the caller.
    responder_hotkey = None
    if getattr(response, "axon", None) is not None:
        responder_hotkey = getattr(response.axon, "hotkey", None)
    if responder_hotkey is None and response.dendrite is not None:
        responder_hotkey = getattr(response.dendrite, "hotkey", None)

    if responder_hotkey is None:
        bt.logging.debug("Response missing responder hotkey, rejecting")
        return False

    if responder_hotkey != expected_hotkey:
        bt.logging.warning(
            f"Response hotkey mismatch: expected {expected_hotkey}, "
            f"got {responder_hotkey}. Rejecting."
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

    # NEW: deep structural integrity check
    if not _validate_workflow_plan(plan):
        bt.logging.debug(
            f"workflow_plan from {expected_hotkey} failed integrity check, rejecting"
        )
        return False

    return True

# C-SWON Validator — Workflow Executor
# Implements sandboxed DAG execution with DataRef resolution (readme §3.2).

"""
The executor takes a miner's workflow plan (DAG) and executes it step by step,
resolving DataRef patterns, enforcing budget ceilings, and tracking metrics.

In mock mode (CSWON_MOCK_EXEC=true), no real subnet calls are made.
"""

import os
import re
import time
import copy
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import bittensor as bt


# ── DataRef Resolution ──────────────────────────────────────────────

DATAREF_PATTERN = re.compile(r"\$\{(\w+)\.output\.([a-zA-Z0-9_.]+)\}")


def resolve_datarefs(value: Any, context: Dict[str, dict]) -> Any:
    """
    Resolve ${step_id.output.field_path} patterns in node params (readme §3.2).

    Args:
        value: The value to resolve (may be string, dict, or list).
        context: Mapping of node_id -> output dict from completed nodes.

    Returns:
        The resolved value with DataRef patterns substituted.

    Raises:
        DataRefError: If a referenced node hasn't completed or field doesn't exist.
    """
    if isinstance(value, str):
        def _replace(match):
            step_id = match.group(1)
            field_path = match.group(2)

            if step_id not in context:
                raise DataRefError(
                    f"Referenced node '{step_id}' not found in context"
                )
            node_output = context[step_id]
            if node_output.get("status") == "failed":
                raise DataRefError(
                    f"Referenced node '{step_id}' failed — cannot resolve DataRef"
                )

            # Navigate the field path (e.g., "artifacts.code")
            result = node_output.get("output", {})
            for part in field_path.split("."):
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    raise DataRefError(
                        f"Field '{field_path}' not found in node '{step_id}' output"
                    )
            return str(result)

        return DATAREF_PATTERN.sub(_replace, value)

    elif isinstance(value, dict):
        return {k: resolve_datarefs(v, context) for k, v in value.items()}

    elif isinstance(value, list):
        return [resolve_datarefs(item, context) for item in value]

    return value


class DataRefError(Exception):
    """Raised when a DataRef cannot be resolved."""
    pass


# ── Topological Sort ────────────────────────────────────────────────

def topological_sort_tiers(nodes: List[dict], edges: List[dict]) -> List[List[str]]:
    """
    Derive execution tiers by topological sort of DAG edges (readme §3.2).

    Nodes with no dependency on each other (no shared path in the DAG)
    are placed in the same execution tier and run concurrently.

    Returns:
        List of tiers, where each tier is a list of node IDs that can
        execute concurrently.
    """
    node_ids = [n["id"] for n in nodes]
    # Build adjacency and in-degree
    in_degree = {nid: 0 for nid in node_ids}
    successors = defaultdict(list)

    for edge in edges:
        from_id = edge["from"]
        to_id = edge["to"]
        successors[from_id].append(to_id)
        in_degree[to_id] = in_degree.get(to_id, 0) + 1

    # Kahn's algorithm producing tiers
    tiers = []
    current_tier = [nid for nid, deg in in_degree.items() if deg == 0]

    while current_tier:
        tiers.append(sorted(current_tier))  # sort for determinism
        next_tier = []
        for nid in current_tier:
            for succ in successors[nid]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    next_tier.append(succ)
        current_tier = next_tier

    return tiers


# ── Execution Result ────────────────────────────────────────────────

class ExecutionResult:
    """Holds the results of executing a workflow plan."""

    def __init__(self):
        self.context: Dict[str, dict] = {}           # node_id -> output
        self.actual_cost: float = 0.0                 # cumulative TAO cost
        self.actual_latency: float = 0.0              # wall-clock end-to-end (seconds)
        self.steps_completed: int = 0                 # successful steps
        self.total_steps: int = 0                     # total nodes in DAG
        self.retries: Dict[str, int] = {}             # node_id -> actual retry count
        self.timeouts: int = 0                        # total timeout events
        self.hard_failures: int = 0                   # total hard failure events
        self.unplanned_retries: int = 0               # retries beyond declared budget
        self.budget_aborted: bool = False             # if budget ceiling was hit
        self.final_output: Optional[dict] = None      # output from final node(s)


# ── Mock Executor ───────────────────────────────────────────────────

def _mock_execute_node(node: dict, resolved_params: dict) -> dict:
    """
    Mock execution of a single node (CSWON_MOCK_EXEC=true).
    Returns a plausible output without making real subnet calls.
    """
    action = node.get("action", "unknown")
    estimated_cost = node.get("estimated_cost", 0.001)
    estimated_latency = node.get("estimated_latency", 0.5)

    # Simulate some processing time (scaled down for mock)
    import random
    mock_latency = estimated_latency * random.uniform(0.5, 1.5)
    time.sleep(min(mock_latency, 0.1))  # cap actual sleep in mock

    return {
        "status": "success",
        "output": {
            "text": f"Mock output for action '{action}' with params: {list(resolved_params.keys())}",
            "artifacts": {
                "code": f"# Mock code generated by {action}",
                "metadata": {"mock": True, "action": action},
            },
        },
        "actual_cost": estimated_cost * random.uniform(0.8, 1.2),
        "actual_latency": mock_latency,
    }


# ── Main Executor ───────────────────────────────────────────────────

def execute_workflow(
    workflow_plan: dict,
    constraints: dict,
    total_estimated_cost: float,
    mock_mode: Optional[bool] = None,
) -> ExecutionResult:
    """
    Execute a miner's workflow plan (readme §3.2, §4.8 step 3).

    1. Derive execution plan by topological sort of edges.
    2. After each node completes, store output in context.
    3. Before executing each node, resolve DataRef patterns.
    4. Before dispatching, check cumulative TAO cost vs budget ceiling.

    Args:
        workflow_plan: Dict with "nodes", "edges", "error_handling".
        constraints: Dict with "max_budget_tao", "max_latency_seconds".
        total_estimated_cost: Miner's declared total estimated cost.
        mock_mode: If None, reads from CSWON_MOCK_EXEC env var.

    Returns:
        ExecutionResult with all tracked metrics.
    """
    if mock_mode is None:
        mock_mode = os.environ.get("CSWON_MOCK_EXEC", "true").lower() == "true"

    result = ExecutionResult()
    nodes = workflow_plan.get("nodes", [])
    edges = workflow_plan.get("edges", [])
    error_handling = workflow_plan.get("error_handling", {})

    result.total_steps = len(nodes)
    if not nodes:
        return result

    # Build node lookup
    node_map = {n["id"]: n for n in nodes}

    # Compute budget ceiling (readme §3.2 step 4)
    max_budget = constraints.get("max_budget_tao", float("inf"))
    budget_ceiling = min(max_budget, 1.5 * total_estimated_cost)

    # Topological sort into execution tiers
    tiers = topological_sort_tiers(nodes, edges)

    start_time = time.time()

    for tier in tiers:
        for node_id in tier:
            if node_id not in node_map:
                continue

            node = node_map[node_id]

            # Budget check before dispatch (readme §3.2 step 4)
            if result.actual_cost >= budget_ceiling:
                # Mark all remaining unexecuted nodes as "budget_abort"
                for remaining_id in _get_remaining_nodes(tiers, node_id, tier):
                    result.context[remaining_id] = {
                        "status": "budget_abort",
                        "output": None,
                    }
                result.budget_aborted = True
                bt.logging.info(
                    f"Budget abort at node {node_id}: "
                    f"cumulative={result.actual_cost:.4f} >= ceiling={budget_ceiling:.4f}"
                )
                break

            # Resolve DataRefs in node params
            try:
                resolved_params = resolve_datarefs(
                    copy.deepcopy(node.get("params", {})),
                    result.context,
                )
            except DataRefError as e:
                bt.logging.debug(f"DataRef resolution failed for {node_id}: {e}")
                result.context[node_id] = {
                    "status": "failed",
                    "output": None,
                    "error": str(e),
                }
                result.hard_failures += 1
                continue

            # Get retry budget for this node
            node_error_handling = error_handling.get(node_id, {})
            declared_retry_count = node_error_handling.get("retry_count", 0)
            timeout_seconds = node_error_handling.get("timeout_seconds", 30.0)

            # Execute node (with retries)
            node_result = None
            actual_retries = 0

            for attempt in range(declared_retry_count + 1):
                try:
                    if mock_mode:
                        node_result = _mock_execute_node(node, resolved_params)
                    else:
                        # Real execution would call partner subnet via dendrite
                        # For now, use mock mode
                        node_result = _mock_execute_node(node, resolved_params)

                    if node_result["status"] == "success":
                        break

                except Exception as e:
                    bt.logging.debug(
                        f"Node {node_id} attempt {attempt + 1} failed: {e}"
                    )

                if attempt < declared_retry_count:
                    actual_retries += 1

            # Record results
            if node_result and node_result["status"] == "success":
                result.context[node_id] = node_result
                result.actual_cost += node_result.get("actual_cost", 0.0)
                result.steps_completed += 1
                result.retries[node_id] = actual_retries
            else:
                result.context[node_id] = {
                    "status": "failed",
                    "output": None,
                    "error": "Exhausted retry budget",
                }
                result.hard_failures += 1
                result.retries[node_id] = actual_retries

            # Track unplanned retries (readme §2.2):
            # unplanned_retries = max(0, actual_retries - declared_retry_budget)
            unplanned = max(0, actual_retries - declared_retry_count)
            result.unplanned_retries += unplanned

        if result.budget_aborted:
            break

    result.actual_latency = time.time() - start_time

    # Set final output from the last completed node(s)
    if result.steps_completed > 0:
        # Find the final tier's completed nodes
        for tier in reversed(tiers):
            for node_id in tier:
                if node_id in result.context and result.context[node_id].get("status") == "success":
                    result.final_output = result.context[node_id].get("output")
                    break
            if result.final_output:
                break

    return result


def _get_remaining_nodes(
    tiers: List[List[str]],
    current_node_id: str,
    current_tier: List[str],
) -> List[str]:
    """Get all unexecuted nodes from current position forward."""
    remaining = []
    found_current = False

    for tier in tiers:
        if tier is current_tier or found_current:
            found_current = True
            for nid in tier:
                remaining.append(nid)

    return remaining

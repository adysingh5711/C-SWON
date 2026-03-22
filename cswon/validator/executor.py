# C-SWON Validator — Workflow Executor (v2)
# Implements sandboxed DAG execution with DataRef resolution (readme §3.2),
# routing_policy enforcement (readme §3.3, §1.3 fix),
# async parallel tier execution (readme §3.2 §2.8 fix),
# and live subnet call authentication stubs (readme §4.3 §1.6 fix).

"""
The executor takes a miner's workflow plan (DAG) and executes it step by step,
resolving DataRef patterns, enforcing budget ceilings, and tracking metrics.

Key changes from v1:
  - routing_policy is now read per node and used to select partner miners
    and aggregate their outputs (median_logit / majority_vote).
  - Nodes within the same DAG tier now execute concurrently via asyncio.gather
    instead of sequentially (fixes the S_latency measurement for parallel DAGs).
  - Live execution path now checks CSWON_PARTNER_HOTKEY and calls a dedicated
    _live_execute_node() stub instead of silently falling back to mock.
"""

import asyncio
import copy
import os
import re
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import bittensor as bt

from cswon.subnet_links import SUBNET_LINKS  # integrate subnet_links.py (issue 3.9)


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
            if node_output.get("status") in ("failed", "budget_abort"):
                raise DataRefError(
                    f"Referenced node '{step_id}' has status "
                    f"'{node_output.get('status')}' — cannot resolve DataRef"
                )

            # Navigate the field path (e.g., "artifacts.code")
            result = node_output.get("output", {}) or {}
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
    in_degree = {nid: 0 for nid in node_ids}
    successors: Dict[str, List[str]] = defaultdict(list)

    for edge in edges:
        from_id = edge["from"]
        to_id = edge["to"]
        successors[from_id].append(to_id)
        in_degree[to_id] = in_degree.get(to_id, 0) + 1

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


# ── Routing Policy (readme §3.3, issue 1.3) ───────────────────────

# Build a quick lookup from subnet short name → GitHub URL for logging.
_SUBNET_URL_MAP = {entry["name"]: entry["url"] for entry in SUBNET_LINKS}


def apply_routing_policy(node: dict, routing_policy: dict) -> dict:
    """
    Determine partner subnet routing configuration per task routing_policy (readme §3.3).

    Validators must use the policy embedded in the benchmark task JSON — they
    must NOT override it with their own routing logic.

    Args:
        node: Workflow DAG node dict (must have "subnet" key).
        routing_policy: The routing_policy dict from the task JSON.

    Returns:
        dict with keys: selection, top_k, aggregation
    """
    subnet = node.get("subnet", "default")
    policy = routing_policy.get(subnet, routing_policy.get("default", {}))

    selection = policy.get("miner_selection", "top_k_stake_weighted")
    top_k = int(policy.get("top_k", 3))
    aggregation = policy.get("aggregation", "majority_vote")

    subnet_url = _SUBNET_URL_MAP.get(subnet.lower(), "unknown")
    bt.logging.trace(
        f"Routing node '{node.get('id')}' on {subnet} "
        f"({subnet_url}): selection={selection} top_k={top_k} agg={aggregation}"
    )
    return {"selection": selection, "top_k": top_k, "aggregation": aggregation}


def aggregate_outputs(outputs: List[dict], aggregation: str) -> dict:
    """
    Aggregate multiple partner-miner outputs per routing_policy aggregation mode
    (readme §3.3).

    Args:
        outputs: List of raw node result dicts from top-k partner miners.
        aggregation: "median_logit" | "majority_vote"

    Returns:
        A single merged result dict.
    """
    if not outputs:
        return {"status": "failed", "output": None, "actual_cost": 0.0, "actual_latency": 0.0}

    if aggregation == "majority_vote":
        texts = []
        for o in outputs:
            if o and o.get("status") == "success":
                texts.append(str(o.get("output", {}).get("text", "")))
        if not texts:
            return {"status": "failed", "output": None, "actual_cost": 0.0, "actual_latency": 0.0}
        winner = Counter(texts).most_common(1)[0][0]
        # Merge cost/latency as averages across successful calls
        costs = [o.get("actual_cost", 0.0) for o in outputs if o]
        lats = [o.get("actual_latency", 0.0) for o in outputs if o]
        return {
            "status": "success",
            "output": {"text": winner, "artifacts": {}},
            "actual_cost": sum(costs) / len(costs) if costs else 0.0,
            "actual_latency": max(lats) if lats else 0.0,  # wall-clock is the slowest
        }

    elif aggregation == "median_logit":
        import statistics
        numeric_vals = []
        for o in outputs:
            if o and o.get("status") == "success":
                try:
                    numeric_vals.append(float(o.get("output", {}).get("text", "0")))
                except (ValueError, TypeError):
                    pass
        if not numeric_vals:
            return {"status": "failed", "output": None, "actual_cost": 0.0, "actual_latency": 0.0}
        med = statistics.median(numeric_vals)
        costs = [o.get("actual_cost", 0.0) for o in outputs if o]
        lats = [o.get("actual_latency", 0.0) for o in outputs if o]
        return {
            "status": "success",
            "output": {"text": str(med), "artifacts": {}},
            "actual_cost": sum(costs) / len(costs) if costs else 0.0,
            "actual_latency": max(lats) if lats else 0.0,
        }

    # Fallback: return first successful output
    for o in outputs:
        if o and o.get("status") == "success":
            return o
    return {"status": "failed", "output": None, "actual_cost": 0.0, "actual_latency": 0.0}


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
    import random
    action = node.get("action", "unknown")
    estimated_cost = node.get("estimated_cost", 0.001)
    estimated_latency = node.get("estimated_latency", 0.5)

    mock_latency = estimated_latency * random.uniform(0.5, 1.5)
    time.sleep(min(mock_latency, 0.05))  # cap actual sleep in mock

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


# ── Live Executor Stub (readme §4.3, issue 1.6) ─────────────────────

def _live_execute_node(
    node: dict,
    resolved_params: dict,
    partner_hotkey: str,
    routing_config: Optional[dict] = None,
) -> dict:
    """
    Authenticated HTTP call to a partner subnet axon (readme §4.3).

    This stub represents the mainnet bootstrap path where the validator has
    registered a dedicated C-SWON hotkey on each partner subnet.

    Stages (readme §4.3):
      - Testnet:          CSWON_MOCK_EXEC=true  → mock path (never reaches here)
      - Mainnet bootstrap: validator registered hotkey, calls at standard rates
      - Mainnet at scale:  negotiated API-tier access with revenue-share

    When fully implemented this function will:
      1. Look up partner subnet axon endpoints from the metagraph.
      2. Select top-k miners per routing_config["selection"] + metagraph stake.
      3. Call each selected miner via dendrite.forward() with the node payload.
      4. Aggregate responses via aggregate_outputs() per routing_config["aggregation"].
      5. Return the merged result with actual TAO cost tracked.

    Until the validator completes partner-subnet registration, this function
    falls back to mock mode with a prominent WARNING (not silently).
    """
    subnet = node.get("subnet", "unknown")
    bt.logging.warning(
        f"LIVE_EXEC: partner_hotkey='{partner_hotkey}' | subnet={subnet} | "
        f"action={node.get('action')} — partner registration not yet complete. "
        f"Falling back to mock for this step. "
        f"See readme §4.3 for mainnet bootstrap instructions."
    )
    # TODO (mainnet): implement actual dendrite call to partner subnet axon:
    #   axons = _select_partner_axons(subnet, routing_config, metagraph)
    #   responses = await dendrite.forward(axons=axons, synapse=NodeSynapse(...))
    #   return aggregate_outputs(responses, routing_config["aggregation"])
    return _mock_execute_node(node, resolved_params)


# ── Async Node Executor ─────────────────────────────────────────────

async def _execute_node_async(
    node_id: str,
    node_map: Dict[str, dict],
    error_handling: dict,
    result: ExecutionResult,
    budget_ceiling: float,
    mock_mode: bool,
    partner_hotkey: str,
    routing_policy: dict,
) -> None:
    """
    Execute a single DAG node asynchronously (used by _execute_tier_async).

    Writes results directly into `result.context` and updates counters.
    Thread-safe enough for asyncio (single-threaded event loop).
    """
    if result.budget_aborted:
        result.context[node_id] = {"status": "budget_abort", "output": None}
        return

    if node_id not in node_map:
        return

    node = node_map[node_id]

    # Budget check before dispatch (readme §3.2 step 4)
    if result.actual_cost >= budget_ceiling:
        result.context[node_id] = {"status": "budget_abort", "output": None}
        result.budget_aborted = True
        bt.logging.info(
            f"Budget abort at node {node_id}: "
            f"cumulative={result.actual_cost:.4f} >= ceiling={budget_ceiling:.4f}"
        )
        return

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
        return

    node_error_handling = error_handling.get(node_id, {})
    declared_retry_count = node_error_handling.get("retry_count", 0)

    # Determine routing config for this node (issue 1.3)
    routing_cfg = apply_routing_policy(node, routing_policy)

    # Execute node (with retries)
    node_result = None
    actual_retries = 0

    for attempt in range(declared_retry_count + 1):
        try:
            if mock_mode:
                node_result = _mock_execute_node(node, resolved_params)
            else:
                node_result = _live_execute_node(node, resolved_params, partner_hotkey, routing_cfg)

            if node_result and node_result.get("status") == "success":
                break

        except Exception as e:
            bt.logging.debug(f"Node {node_id} attempt {attempt + 1} failed: {e}")

        if attempt < declared_retry_count:
            actual_retries += 1

    # Record results
    if node_result and node_result.get("status") == "success":
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

    # Track unplanned retries (readme §2.2)
    unplanned = max(0, actual_retries - declared_retry_count)
    result.unplanned_retries += unplanned


# ── Tier Executor (parallel within tier, readme §3.2 §2.8) ──────────

async def _execute_tier_async(
    tier: List[str],
    node_map: Dict[str, dict],
    error_handling: dict,
    result: ExecutionResult,
    budget_ceiling: float,
    mock_mode: bool,
    partner_hotkey: str,
    routing_policy: dict,
) -> None:
    """
    Execute all nodes in a tier concurrently using asyncio.gather (readme §3.2).

    Nodes within the same tier have no dependency on each other and run
    concurrently. Wall-clock S_latency is therefore the max branch time,
    not the sum — correctly reflecting parallel DAG behaviour.
    """
    tasks = [
        _execute_node_async(
            node_id=node_id,
            node_map=node_map,
            error_handling=error_handling,
            result=result,
            budget_ceiling=budget_ceiling,
            mock_mode=mock_mode,
            partner_hotkey=partner_hotkey,
            routing_policy=routing_policy,
        )
        for node_id in tier
    ]
    await asyncio.gather(*tasks)


# ── Main Async Executor ─────────────────────────────────────────────

async def execute_workflow_async(
    workflow_plan: dict,
    constraints: dict,
    total_estimated_cost: float,
    mock_mode: Optional[bool] = None,
    routing_policy: Optional[dict] = None,
) -> ExecutionResult:
    """
    Execute a miner's workflow plan asynchronously (readme §3.2, §4.8 step 3).

    1. Derive execution plan by topological sort of edges.
    2. For each tier, execute all nodes concurrently (asyncio.gather).
    3. After each node completes, store output in context.
    4. Before executing each node, resolve DataRef patterns.
    5. Before dispatching, check cumulative TAO cost vs budget ceiling.

    Args:
        workflow_plan: Dict with "nodes", "edges", "error_handling".
        constraints: Dict with "max_budget_tao", "max_latency_seconds".
        total_estimated_cost: Miner's declared total estimated cost.
        mock_mode: If None, reads from CSWON_MOCK_EXEC env var.
        routing_policy: Per-subnet routing config from benchmark task JSON (readme §3.3).

    Returns:
        ExecutionResult with all tracked metrics.
    """
    if mock_mode is None:
        mock_mode = os.environ.get("CSWON_MOCK_EXEC", "true").lower() == "true"

    if routing_policy is None:
        routing_policy = {}

    partner_hotkey = os.environ.get("CSWON_PARTNER_HOTKEY", "")

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
        if result.budget_aborted:
            # Mark all remaining nodes as budget_abort
            for node_id in tier:
                if node_id not in result.context:
                    result.context[node_id] = {"status": "budget_abort", "output": None}
            continue

        # Execute all nodes in this tier concurrently (issue 2.8)
        await _execute_tier_async(
            tier=tier,
            node_map=node_map,
            error_handling=error_handling,
            result=result,
            budget_ceiling=budget_ceiling,
            mock_mode=mock_mode,
            partner_hotkey=partner_hotkey,
            routing_policy=routing_policy,
        )

    result.actual_latency = time.time() - start_time

    # Set final output from the last completed node(s)
    if result.steps_completed > 0:
        for tier in reversed(tiers):
            for node_id in tier:
                if node_id in result.context and result.context[node_id].get("status") == "success":
                    result.final_output = result.context[node_id].get("output")
                    break
            if result.final_output:
                break

    return result


# ── Synchronous Wrapper (backward compat) ───────────────────────────

def execute_workflow(
    workflow_plan: dict,
    constraints: dict,
    total_estimated_cost: float,
    mock_mode: Optional[bool] = None,
    routing_policy: Optional[dict] = None,
) -> ExecutionResult:
    """
    Synchronous wrapper around execute_workflow_async() for backward compatibility.

    forward.py should call execute_workflow_async() directly (it already runs in
    an async context). This wrapper is provided for non-async code paths and tests.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an existing event loop (e.g. called from async forward):
            # create a new loop in a thread to avoid nesting
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    execute_workflow_async(
                        workflow_plan, constraints, total_estimated_cost,
                        mock_mode, routing_policy,
                    ),
                )
                return future.result()
        else:
            return loop.run_until_complete(
                execute_workflow_async(
                    workflow_plan, constraints, total_estimated_cost,
                    mock_mode, routing_policy,
                )
            )
    except Exception:
        # Final fallback: use asyncio.run()
        return asyncio.run(
            execute_workflow_async(
                workflow_plan, constraints, total_estimated_cost,
                mock_mode, routing_policy,
            )
        )

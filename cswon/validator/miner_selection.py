# C-SWON Validator — Miner Selection & Task Selection
# Implements VRF-keyed task selection (readme §2.5, §4.8 step 1)
# and early miner boost logic (readme §3.5).

"""
Deterministic task selection using a VRF-style hash of (validator_hotkey, block).
Early participation boost: first 50 miners get 3× query frequency.
"""

import hashlib
import json
import os
import random
from typing import List, Optional

import bittensor as bt
import numpy as np

from cswon.validator.config import (
    EARLY_MINER_BOOST_MULTIPLIER,
    EARLY_MINER_LIMIT,
    BENCHMARK_PATH,
)

# 6-month boost window in blocks (~12 s/block, 30 days/month → 6×30×24×300 = 1,296,000)
EARLY_MINER_BOOST_WINDOW = 1_296_000

REQUIRED_TASK_FIELDS = {
    "task_id",
    "task_type",
    "description",
    "constraints",
    "available_tools",
    "reference",
}


def _validate_task_schema(task: dict) -> None:
    missing = REQUIRED_TASK_FIELDS - set(task.keys())
    if missing:
        raise ValueError(
            f"Task {task.get('task_id', '<unknown>')} missing fields: {sorted(missing)}"
        )

    if task["task_type"] not in {"code", "rag", "agent", "data_transform"}:
        raise ValueError(f"Unsupported task_type: {task['task_type']}")

    if not isinstance(task["available_tools"], dict) or not task["available_tools"]:
        raise ValueError(f"Task {task['task_id']} has empty available_tools")

    allowed = set(task.get("constraints", {}).get("allowed_subnets", []))
    if allowed and not allowed.issubset(set(task["available_tools"].keys())):
        raise ValueError(
            f"Task {task['task_id']} has allowed_subnets outside available_tools: "
            f"{sorted(allowed - set(task['available_tools'].keys()))}"
        )


def _normalise_task(task: dict) -> dict:
    task = dict(task)
    task["quality_criteria"] = task.get("quality_criteria", {})
    task["constraints"] = task.get("constraints", {})
    task["available_tools"] = task.get("available_tools", {})
    task["routing_policy"] = task.get(
        "routing_policy",
        {
            "default": {
                "miner_selection": "top_k_stake_weighted",
                "top_k": 1,
                "aggregation": "majority_vote",
            }
        },
    )

    allowed = task["constraints"].get("allowed_subnets")
    if not allowed:
        task["constraints"]["allowed_subnets"] = list(task["available_tools"].keys())
    else:
        task["constraints"]["allowed_subnets"] = [
            s for s in allowed if s in task["available_tools"]
        ]

    if not task["constraints"]["allowed_subnets"]:
        raise ValueError(f"Task {task['task_id']} has no usable allowed_subnets")

    task["description"] = str(task.get("description", "")).strip()
    if not task["description"]:
        raise ValueError(f"Task {task['task_id']} has empty description")

    return task


def load_benchmark_tasks(benchmark_path: Optional[str] = None) -> List[dict]:
    path = benchmark_path or BENCHMARK_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Benchmark file not found at {path}")

    try:
        with open(path, "r") as f:
            all_tasks = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        bt.logging.warning(f"Benchmark file {path} is corrupted ({e}). Attempting recovery from .bak")
        bak_path = path + ".bak"
        if os.path.exists(bak_path):
            with open(bak_path, "r") as f:
                all_tasks = json.load(f)
        else:
            raise ValueError(f"Benchmark file {path} is corrupted and no .bak found.") from e

    if not isinstance(all_tasks, list) or not all_tasks:
        raise ValueError(f"Benchmark file at {path} must be a non-empty list")

    active_tasks = [t for t in all_tasks if t.get("status", "active") == "active"]
    if not active_tasks:
        raise ValueError(f"No active benchmark tasks found in {path}")

    validated_tasks = []
    for task in active_tasks:
        _validate_task_schema(task)
        validated_tasks.append(_normalise_task(task))

    bt.logging.info(f"Loaded {len(validated_tasks)} validated benchmark tasks from {path}")
    return validated_tasks


def select_task_for_block(
    validator_hotkey: str,
    current_block: int,
    benchmark_tasks: List[dict],
) -> Optional[dict]:
    """
    Deterministic task selection using VRF-keyed hash (readme §2.5, §4.8 step 1).

    Different validators derive different tasks from the same block via their
    hotkey-keyed VRF. Cross-validator consensus uses distributional statistics
    over the rolling window, not identical-task point comparisons.

    Returns None if no tasks are available.
    """
    if not benchmark_tasks:
        return None

    seed = f"{validator_hotkey}:{current_block}".encode()
    h = hashlib.sha256(seed).digest()
    task_index = int.from_bytes(h, "big") % len(benchmark_tasks)
    return benchmark_tasks[task_index]


# ── Immunity helper (issue 2.4) ─────────────────────────────────────────────

def _is_within_immunity(
    uid: int,
    subtensor,
    netuid: int,
    current_block: int,
) -> bool:
    """
    True if the miner is still within its immunity_period (readme §3.1, §4.4).
    Fetches registration block and immunity_period from chain — NOT a UID proxy.
    Falls back to False (assume not immune) if the chain is unreachable.
    """
    try:
        params = subtensor.get_subnet_hyperparameters(netuid)
        immunity_period = params.immunity_period
        neuron = subtensor.neuron_for_uid(uid=uid, netuid=netuid)
        reg_block = neuron.block
        return (current_block - reg_block) < immunity_period
    except Exception as e:
        bt.logging.trace(f"Could not check immunity for uid={uid}: {e}")
        return False  # conservative: assume not immune


def select_miners_for_query(
    metagraph: "bt.Metagraph",
    k: int = 10,
    exclude: Optional[List[int]] = None,
    min_stake_tao: float = 1.0,
    subtensor=None,
    netuid: Optional[int] = None,
    current_block: Optional[int] = None,
    subnet_launch_block: Optional[int] = None,
) -> np.ndarray:
    """
    Select miners to query with early participation boost (readme §3.5).

    Args:
        metagraph: The metagraph object.
        k: Number of miners to select.
        exclude: UIDs to exclude from selection.
        min_stake_tao: Minimum active TAO stake required (readme §3.1).
        subtensor: If provided, used for real immunity chain lookup (issue 2.4).
        netuid: Subnet UID — required when subtensor is provided.
        current_block: Current block height — required when subtensor is provided.
        subnet_launch_block: Block the subnet launched at; limits the 6-month boost (issue 3.7).
    """
    exclude = exclude or []
    n = metagraph.n.item()

    # Determine if the 6-month early boost is still active (issue 3.7)
    early_boost_active = (
        subnet_launch_block is not None
        and current_block is not None
        and (current_block - subnet_launch_block) < EARLY_MINER_BOOST_WINDOW
    )

    candidates = []
    weights = []

    for uid in range(n):
        # Skip non-serving axons
        if not metagraph.axons[uid].is_serving:
            continue
        # Skip excluded UIDs
        if uid in exclude:
            continue
        # Skip validators (those with validator permits and high stake)
        if metagraph.validator_permit[uid] and metagraph.S[uid] > 1024:
            continue

        # Strict immunity check: real chain lookup only (issue 2.4/Fix 7).
        # No more UID-ordinal proxy so miners can't squat on low UIDs.
        if subtensor is None or netuid is None or current_block is None:
            is_immune = False  # strict: no boost if chain unreachable
        else:
            is_immune = _is_within_immunity(uid, subtensor, netuid, current_block)
        miner_stake = float(metagraph.S[uid])
        if miner_stake < min_stake_tao and not is_immune:
            bt.logging.trace(
                f"Skipping miner uid={uid}: stake={miner_stake:.3f} < "
                f"min_stake_tao={min_stake_tao}"
            )
            continue

        candidates.append(uid)

        # Early miner boost: 3× selection weight within 6-month window, strict immunity only
        if early_boost_active and is_immune:
            weights.append(float(EARLY_MINER_BOOST_MULTIPLIER))
        else:
            weights.append(1.0)

    if not candidates:
        return np.array([], dtype=int)

    # Normalise weights to probabilities
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]

    # Sample without replacement
    k = min(k, len(candidates))
    selected = np.random.choice(
        candidates, size=k, replace=False, p=probabilities
    )
    return selected


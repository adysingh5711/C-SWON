# C-SWON Validator — Weight Setter
# Implements tempo-aligned weight submission (readme §4.1).

"""
Weight submission once per tempo with dual-condition guard:
- current_block - last_set_block >= TEMPO
- current_block - last_set_block >= WEIGHTS_RATE_LIMIT

Weights are capped at 15% per miner before submission.
"""

from typing import List, Tuple

import bittensor as bt
import numpy as np

from cswon.validator.config import TEMPO, MAX_MINER_WEIGHT_FRACTION
from cswon.validator.reward import ScoreAggregator


def should_set_weights(
    current_block: int,
    last_set_block: int,
    subtensor: "bt.subtensor",
    netuid: int,
) -> bool:
    """
    Check if weights should be submitted this block (readme §4.1).

    Dual-condition guard ensures:
    1. At least one full tempo has elapsed.
    2. WeightsRateLimit is respected.
    """
    try:
        params = subtensor.get_subnet_hyperparameters(netuid)
        tempo = params.tempo if params.tempo else TEMPO
        weights_rate_limit = params.weights_rate_limit if hasattr(params, "weights_rate_limit") else tempo
    except Exception:
        tempo = TEMPO
        weights_rate_limit = TEMPO

    blocks_since = current_block - last_set_block
    return blocks_since >= tempo and blocks_since >= weights_rate_limit


def compute_weights(
    score_aggregator: ScoreAggregator,
    miner_uids: List[int],
) -> Tuple[List[int], List[float]]:
    """
    Compute normalised weights with 15% cap per miner (readme §4.8 step 6).

    Returns:
        Tuple of (uids, weights) lists ready for set_weights().
    """
    normalised = score_aggregator.get_normalised_weights(miner_uids)

    uids = []
    weights = []
    for uid in sorted(normalised.keys()):
        uids.append(uid)
        weights.append(normalised[uid])

    return uids, weights


def set_weights_on_chain(
    subtensor: "bt.subtensor",
    wallet: "bt.wallet",
    netuid: int,
    miner_uids: List[int],
    normalised_weights: List[float],
    spec_version: int,
) -> bool:
    """
    Submit weights to chain (readme §4.1).

    Uses wait_for_inclusion=False to avoid blocking the event loop.

    Returns:
        True if submission was accepted.
    """
    try:
        result, msg = subtensor.set_weights(
            wallet=wallet,
            netuid=netuid,
            uids=np.array(miner_uids, dtype=np.int64),
            weights=np.array(normalised_weights, dtype=np.float32),
            wait_for_finalization=False,
            wait_for_inclusion=False,
            version_key=spec_version,
        )

        if result is True:
            bt.logging.info("set_weights on chain successfully!")
            return True
        else:
            bt.logging.error(f"set_weights failed: {msg}")
            return False

    except Exception as e:
        bt.logging.error(f"set_weights exception: {e}")
        return False

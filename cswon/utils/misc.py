"""
C-SWON Miscellaneous Utilities

Provides helper functions used throughout the codebase.
"""

import time
from functools import lru_cache
from typing import Any, Callable

import bittensor as bt


_block_cache: dict = {}
_block_cache_ttl: float = 12.0  # one Bittensor block is ~12 seconds


def ttl_get_block(subtensor: "bt.Subtensor") -> int:
    """
    Get the current block number with TTL caching to avoid excessive RPC calls.
    Cache expires every 12 seconds (one block period).
    """
    now = time.time()
    cached = _block_cache.get("block")

    if cached is not None:
        value, timestamp = cached
        if now - timestamp < _block_cache_ttl:
            return value

    try:
        block = subtensor.get_current_block()
    except Exception:
        block = 0

    _block_cache["block"] = (block, now)
    return block

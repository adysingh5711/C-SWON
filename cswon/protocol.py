# The MIT License (MIT)
# Copyright © 2024 C-SWON Contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""
C-SWON Protocol Definition

WorkflowSynapse is the Bittensor synapse that carries task packages from validators
to miners and workflow plans back. Defined per readme §3.2b.
"""

import bittensor as bt
from typing import Optional


class WorkflowSynapse(bt.Synapse):
    """
    Validator → Miner: carries the task package.
    Miner → Validator: carries the workflow plan (populated by miner).

    Validator-populated fields are set before dispatching via dendrite.forward().
    Miner-populated fields (all Optional) are filled by the miner's forward() handler.
    Any Optional field left as None by the miner is treated as an invalid response.
    """

    # ── Validator-populated fields (sent to miner) ──────────────────
    task_id:          str  = ""
    task_type:        str  = ""
    description:      str  = ""
    quality_criteria: dict = {}
    constraints:      dict = {}    # max_budget_tao, max_latency_seconds, allowed_subnets
    available_tools:  dict = {}    # per-subnet cost/latency hints
    send_block:       int  = 0     # stamped by query_loop before dispatch

    # ── Miner-populated fields (returned to validator) ───────────────
    miner_uid:               Optional[int]   = None
    scoring_version:         Optional[str]   = None
    workflow_plan:           Optional[dict]  = None   # nodes, edges, error_handling
    total_estimated_cost:    Optional[float] = None
    total_estimated_latency: Optional[float] = None
    confidence:              Optional[float] = None
    reasoning:               Optional[str]   = None

    def deserialize(self) -> "WorkflowSynapse":
        """Return self — the synapse is the container for all response data."""
        return self



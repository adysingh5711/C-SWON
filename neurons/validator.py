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
C-SWON Validator Neuron — entry point.

The validator selects benchmark tasks, queries miners for workflow plans,
executes them in a sandbox, scores results, and submits weights.

Run: python neurons/validator.py --netuid <netuid> --wallet.name <name> --subtensor.network <test|finney>
"""

import time
import sys
import signal

import bittensor as bt

from cswon.base.validator import BaseValidatorNeuron
from cswon.validator import forward
from cswon.validator.reward import ScoreAggregator
from cswon.validator.benchmark_lifecycle import BenchmarkLifecycleTracker
from bittensor.core.axon import Axon

def _safe_axon_del(self):
    try:
        if hasattr(self, "fast_server") and self.fast_server is not None:
            self.stop()
    except Exception:
        pass

Axon.__del__ = _safe_axon_del

class Validator(BaseValidatorNeuron):
    """
    C-SWON Validator: evaluates miner workflow plans using the six-stage pipeline.

    This class inherits from BaseValidatorNeuron which handles registration,
    metagraph sync, weight setting, and other boilerplate.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        # Initialise the score aggregator BEFORE load_state() so restored data
        # is not silently discarded (fix 1.2 Bug B: init order correction).
        self.score_aggregator = ScoreAggregator()
        self.lifecycle_tracker = BenchmarkLifecycleTracker()

        bt.logging.info("load_state()")
        self.load_state()

        # Startup preflight (perplex_fix4 §4)
        self._startup_preflight()

        bt.logging.info("C-SWON Validator initialised")

    def _startup_preflight(self):
        """
        Aborts startup if no serving miners found (perplex_fix4 §4).
        """
        serving_miners = [
            uid
            for uid in range(int(self.metagraph.n))
            if self.metagraph.axons[uid].is_serving
            and not self.metagraph.validator_permit[uid]
            and uid != self.uid
        ]
        if not serving_miners:
            raise RuntimeError(
                "No serving miners found on subnet; start at least one miner before validator."
            )

    async def forward(self):
        """
        Validator forward pass — six-stage evaluation pipeline (readme §4.8).

        1. Deterministic task selection (VRF-keyed)
        2. Miner workflow collection (async query)
        3. Sandboxed execution
        4. Output quality evaluation (deterministic, no LLM judge)
        5. Composite scoring (four-dimension formula)
        6. Rolling window update + weight submission
        """
        return await forward(self)


# Entry point
if __name__ == "__main__":
    with Validator() as validator:
        def sig_handler(signum, frame):
            bt.logging.info(f"Received signal {signum}, saving state and exiting...")
            validator.save_state()
            sys.exit(0)

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        while True:
            bt.logging.info(
                f"C-SWON Validator running... block={validator.block}"
            )
            time.sleep(5)

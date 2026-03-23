# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2024 C-SWON Contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import copy
import os
import numpy as np
import asyncio
import argparse
import threading
import bittensor as bt

from typing import List, Union
from traceback import print_exception

from cswon.base.neuron import BaseNeuron
from cswon.base.utils.weight_utils import (
    process_weights_for_netuid,
    convert_weights_and_uids_for_emit,
)
from cswon.mock import MockDendrite
from cswon.utils.config import add_validator_args
from cswon.validator import weight_setter as ws
from cswon.validator.config import (
    SCORING_VERSION,
    __spec_version__ as CSWON_SPEC_VERSION,
)

# Benchmark version broadcast (readme §4.7, issue 2.2)
BENCHMARK_VERSION = "v1"


class BaseValidatorNeuron(BaseNeuron):
    """
    Base class for Bittensor validators. Your validator should inherit from this class.
    """

    neuron_type: str = "ValidatorNeuron"

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        super().add_args(parser)
        add_validator_args(cls, parser)

    def __init__(self, config=None):
        super().__init__(config=config)

        # Save a copy of the hotkeys to local memory.
        self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)

        # Dendrite lets us send messages to other nodes (axons) in the network.
        if self.config.mock:
            self.dendrite = MockDendrite(wallet=self.wallet)
        else:
            self.dendrite = bt.dendrite(wallet=self.wallet)
        bt.logging.info(f"Dendrite: {self.dendrite}")

        # Set up initial scoring weights for validation
        bt.logging.info("Building validation weights.")
        self.scores = np.zeros(self.metagraph.n, dtype=np.float32)

        # Track the last block at which weights were submitted (issue 2.9)
        # Used alongside metagraph.last_update to guard restart edge cases.
        self._last_set_block: int = 0

        # Init sync with the network. Updates the metagraph.
        self.sync()

        # Serve axon to enable external connections.
        if not self.config.neuron.axon_off:
            self.serve_axon()
        else:
            bt.logging.warning("axon off, not serving ip to chain.")

        # Create asyncio event loop to manage async tasks.
        self.loop = asyncio.get_event_loop()

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: Union[threading.Thread, None] = None
        self.lock = asyncio.Lock()

    def serve_axon(self):
        """Serve axon to enable external connections.

        Broadcasts SCORING_VERSION via axon.info per readme §4.5:
          - version (int) = __spec_version__
          - description (str) = "cswon-scoring:<SCORING_VERSION>"
        """
        bt.logging.info("serving ip to chain...")
        try:
            # Broadcast scoring version in axon metadata (readme §4.5)
            try:
                self.axon = bt.axon(
                    wallet=self.wallet,
                    config=self.config,
                    info=bt.AxonInfo(
                        version=CSWON_SPEC_VERSION,
                        ip="0.0.0.0",
                        port=0,
                        ip_type=4,
                        placeholder1=0,
                        placeholder2=0,
                        protocol=4,
                        hotkey=self.wallet.hotkey.ss58_address,
                        coldkey=self.wallet.coldkeypub.ss58_address,
                    ),
                )
                # Broadcast both scoring version AND benchmark version (readme §4.5/§4.7, issue 2.2)
                try:
                    self.axon.info.description = (
                        f"cswon-scoring:{SCORING_VERSION};cswon-bench:{BENCHMARK_VERSION}"
                    )
                except AttributeError:
                    pass  # older SDK
            except TypeError:
                # Fallback for SDKs that don't support info= parameter
                self.axon = bt.axon(wallet=self.wallet, config=self.config)

            try:
                self.subtensor.serve_axon(
                    netuid=self.config.netuid,
                    axon=self.axon,
                )
                bt.logging.info(
                    f"Running validator {self.axon} on network: "
                    f"{self.config.subtensor.chain_endpoint} with netuid: {self.config.netuid} "
                    f"(scoring_version={SCORING_VERSION})"
                )
            except Exception as e:
                bt.logging.error(f"Failed to serve Axon with exception: {e}")
                pass

        except Exception as e:
            bt.logging.error(
                f"Failed to create Axon initialize with exception: {e}"
            )
            pass

    async def concurrent_forward(self):
        coroutines = [
            self.forward()
            for _ in range(self.config.neuron.num_concurrent_forwards)
        ]
        await asyncio.gather(*coroutines)

    def run(self):
        """
        Initiates and manages the main loop for the miner on the Bittensor network. The main loop handles graceful shutdown on keyboard interrupts and logs unforeseen errors.

        This function performs the following primary tasks:
        1. Check for registration on the Bittensor network.
        2. Continuously forwards queries to the miners on the network, rewarding their responses and updating the scores accordingly.
        3. Periodically resynchronizes with the chain; updating the metagraph with the latest network state and setting weights.

        The essence of the validator's operations is in the forward function, which is called every step. The forward function is responsible for querying the network and scoring the responses.

        Note:
            - The function leverages the global configurations set during the initialization of the miner.
            - The miner's axon serves as its interface to the Bittensor network, handling incoming and outgoing requests.

        Raises:
            KeyboardInterrupt: If the miner is stopped by a manual interruption.
            Exception: For unforeseen errors during the miner's operation, which are logged for diagnosis.
        """

        # Check that validator is registered on the network.
        self.sync()

        bt.logging.info(f"Validator starting at block: {self.block}")

        # This loop maintains the validator's operations until intentionally stopped.
        try:
            while True:
                bt.logging.info(f"step({self.step}) block({self.block})")

                # Run multiple forwards concurrently.
                self.loop.run_until_complete(self.concurrent_forward())

                # Check if we should exit.
                if self.should_exit:
                    break

                # Sync metagraph and potentially set weights.
                self.sync()

                if self.step % 10 == 0:
                    self.save_state()

                self.step += 1

        # If someone intentionally stops the validator, it'll safely terminate operations.
        except KeyboardInterrupt:
            self.axon.stop()
            bt.logging.success("Validator killed by keyboard interrupt.")
            exit()

        # In case of unforeseen errors, the validator will log the error and continue operations.
        except Exception as err:
            bt.logging.error(f"Error during validation: {str(err)}")
            bt.logging.debug(
                str(print_exception(type(err), err, err.__traceback__))
            )

    def run_in_background_thread(self):
        """
        Starts the validator's operations in a background thread upon entering the context.
        This method facilitates the use of the validator in a 'with' statement.
        """
        if not self.is_running:
            bt.logging.debug("Starting validator in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            bt.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the validator's operations that are running in the background thread.
        """
        if self.is_running:
            bt.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def __enter__(self):
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the validator's background operations upon exiting the context.
        This method facilitates the use of the validator in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        if self.is_running:
            bt.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def set_weights(self):
        """
        Submit weights once per tempo using the spec-compliant pipeline (readme §4.1, §4.8):
          1. Fetch normalised weights from ScoreAggregator (rolling 100-task window, equal weight).
          2. Apply 15% per-miner cap and redistribute excess.
          3. Submit via subtensor.set_weights() with wait_for_inclusion=False.

        Falls back to the raw self.scores array if score_aggregator is not available
        (e.g. during the very first tempo before any scores have been recorded).
        """
        miner_uids = [
            uid for uid in range(int(self.metagraph.n))
            if not self.metagraph.validator_permit[uid]
        ]

        if hasattr(self, "score_aggregator") and miner_uids:
            # ── Spec-compliant path: rolling window + 15% cap ─────────────────
            uids, weights = ws.compute_weights(
                score_aggregator=self.score_aggregator,
                miner_uids=miner_uids,
            )
        else:
            # ── Fallback path: L1-normalise self.scores ───────────────────────
            bt.logging.warning(
                "score_aggregator not ready; falling back to L1-norm self.scores"
            )
            if np.isnan(self.scores).any():
                bt.logging.warning("Scores contain NaN — replacing with 0.")
            raw = np.nan_to_num(self.scores, nan=0.0)
            norm = np.linalg.norm(raw, ord=1)
            if norm == 0:
                norm = 1.0
            normalised = raw / norm
            uids = list(range(len(normalised)))
            weights = normalised.tolist()

        if not uids:
            bt.logging.warning("No miner UIDs to set weights for; skipping.")
            return

        bt.logging.debug(f"set_weights uids={uids} weights={weights}")

        ws.set_weights_on_chain(
            subtensor=self.subtensor,
            wallet=self.wallet,
            netuid=self.config.netuid,
            miner_uids=uids,
            normalised_weights=weights,
            spec_version=CSWON_SPEC_VERSION,
        )
        # Record the block at which we submitted (issue 2.9: restart guard)
        self._last_set_block = self.block

    def should_set_weights(self) -> bool:
        """
        Check if weights should be set this block (readme §4.1).

        Uses dual-condition guard from weight_setter.py:
          1. At least one full tempo has elapsed since last submission.
          2. WeightsRateLimit on-chain is respected.
        """
        if self.step == 0:
            return False
        if self.neuron_type == "MinerNeuron":
            return False
        if self.config.neuron.disable_set_weights:
            return False

        # Use max of on-chain last_update and local _last_set_block (issue 2.9)
        # Prevents premature weight submission after a restart.
        chain_last = int(self.metagraph.last_update[self.uid])
        last_update = max(chain_last, self._last_set_block)
        return ws.should_set_weights(
            current_block=self.block,
            last_set_block=last_update,
            subtensor=self.subtensor,
            netuid=self.config.netuid,
        )

    def resync_metagraph(self):
        """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
        bt.logging.info("resync_metagraph()")

        # Copies state of metagraph before syncing.
        previous_metagraph = copy.deepcopy(self.metagraph)

        # Sync the metagraph.
        self.metagraph.sync(subtensor=self.subtensor)

        # Check if the metagraph axon info has changed.
        if previous_metagraph.axons == self.metagraph.axons:
            return

        bt.logging.info(
            "Metagraph updated, re-syncing hotkeys, dendrite pool and moving averages"
        )
        # Zero out all hotkeys that have been replaced within overlapping range.
        overlap = min(len(self.hotkeys), len(self.metagraph.hotkeys))
        for uid in range(overlap):
            if self.hotkeys[uid] != self.metagraph.hotkeys[uid]:
                # Reset flat scores array
                self.scores[uid] = 0
                # Reset ScoreAggregator rolling window — new miner must start clean.
                # Without this, a re-registered UID inherits the old miner's full
                # 100-task history and gets immediate inflated weights.
                if hasattr(self, "score_aggregator"):
                    self.score_aggregator.score_windows[uid] = []
                    self.score_aggregator.tasks_seen[uid] = 0
                    bt.logging.debug(
                        f"UID {uid} hotkey changed — ScoreAggregator window cleared."
                    )

        # Resize scores to match current metagraph size (handle growth and shrink).
        if len(self.scores) != int(self.metagraph.n):
            new_scores = np.zeros((self.metagraph.n), dtype=self.scores.dtype)
            copy_len = min(len(self.scores), int(self.metagraph.n))
            new_scores[:copy_len] = self.scores[:copy_len]
            self.scores = new_scores

        # Update the hotkeys.
        self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)

    def update_scores(self, rewards: np.ndarray, uids: List[int]):
        """
        DEPRECATED: EMA contradicts readme §2.2 (equal-weight rolling window, no decay).
        Redirects to ScoreAggregator when available. Legacy EMA path kept for compat.
        """
        bt.logging.warning(
            "update_scores() uses EMA which contradicts readme §2.2. "
            "All callers should use score_aggregator.add_score() instead."
        )
        # Redirect to ScoreAggregator (spec-compliant path)
        if hasattr(self, "score_aggregator"):
            rewards = np.nan_to_num(np.asarray(rewards), nan=0.0)
            uids_arr = np.asarray(uids) if not isinstance(uids, np.ndarray) else uids.copy()
            for uid, reward in zip(uids_arr.tolist(), rewards.tolist()):
                self.score_aggregator.add_score(int(uid), float(reward))
            return

        # Legacy EMA fallback (only when score_aggregator not initialised)
        if np.isnan(rewards).any():
            bt.logging.warning(f"NaN values detected in rewards: {rewards}")
            rewards = np.nan_to_num(rewards, nan=0)
        rewards = np.asarray(rewards)
        if isinstance(uids, np.ndarray):
            uids_array = uids.copy()
        else:
            uids_array = np.array(uids)
        if rewards.size == 0 or uids_array.size == 0:
            return
        if rewards.size != uids_array.size:
            raise ValueError(f"Shape mismatch: rewards {rewards.shape} vs uids {uids_array.shape}")
        scattered_rewards: np.ndarray = np.zeros_like(self.scores)
        scattered_rewards[uids_array] = rewards
        alpha: float = self.config.neuron.moving_average_alpha
        self.scores = alpha * scattered_rewards + (1 - alpha) * self.scores

    def save_state(self):
        """Saves the state of the validator to a file."""
        import json, pathlib
        bt.logging.info("Saving validator state.")
        np.savez(
            self.config.neuron.full_path + "/state.npz",
            step=self.step,
            scores=self.scores,
            hotkeys=self.hotkeys,
        )
        # Persist ScoreAggregator rolling window + tasks_executed_this_tempo (fix 2.8)
        if hasattr(self, "score_aggregator"):
            agg_path = pathlib.Path(self.config.neuron.full_path) / "score_aggregator.json"
            agg_data = {
                "score_windows": {str(k): list(v) for k, v in self.score_aggregator.score_windows.items()},
                "tasks_seen":    {str(k): v for k, v in self.score_aggregator.tasks_seen.items()},
                "tasks_executed_this_tempo": getattr(
                    self.score_aggregator, "tasks_executed_this_tempo", 0
                ),
            }
            try:
                agg_path.write_text(json.dumps(agg_data))
            except IOError as e:
                bt.logging.warning(f"Could not save ScoreAggregator state: {e}")
                
        # Persist BenchmarkLifecycleTracker (fix 3)
        if hasattr(self, "lifecycle_tracker"):
            lc_path = pathlib.Path(self.config.neuron.full_path) / "lifecycle_tracker.json"
            try:
                self.lifecycle_tracker.save_state(str(lc_path))
            except Exception as e:
                bt.logging.warning(f"Could not save BenchmarkLifecycleTracker state: {e}")

    def load_state(self):
        """Loads the state of the validator from a file, including ScoreAggregator (fix 1.2, fix 2.8)."""
        import json, pathlib
        bt.logging.info("Loading validator state.")
        state_path = self.config.neuron.full_path + "/state.npz"
        if not os.path.exists(state_path):
            bt.logging.info("No saved state found — starting fresh.")
            return   # ← first-run guard (fix 1.2): prevents FileNotFoundError on new validators
        state = np.load(state_path)
        self.step = state["step"]
        self.scores = state["scores"]
        self.hotkeys = state["hotkeys"]
        # Restore ScoreAggregator rolling window + tasks_executed_this_tempo (fix 2.8)
        agg_path = pathlib.Path(self.config.neuron.full_path) / "score_aggregator.json"
        if hasattr(self, "score_aggregator") and agg_path.exists():
            try:
                agg_data = json.loads(agg_path.read_text())
                for k, v in agg_data.get("score_windows", {}).items():
                    self.score_aggregator.score_windows[int(k)] = list(v)
                for k, v in agg_data.get("tasks_seen", {}).items():
                    self.score_aggregator.tasks_seen[int(k)] = int(v)
                # Restore tempo counter so N_min eligibility survives restarts (fix 2.8)
                persisted_count = agg_data.get("tasks_executed_this_tempo", 0)
                self.score_aggregator.tasks_executed_this_tempo = persisted_count
                # Also sync the forward.py module-level counter
                import cswon.validator.forward as _fwd
                _fwd._tasks_executed_this_tempo = int(persisted_count)
                bt.logging.info(
                    f"ScoreAggregator state restored from disk "
                    f"(tasks_executed_this_tempo={persisted_count})."
                )
            except Exception as e:
                bt.logging.warning(f"Could not restore ScoreAggregator state: {e}")
                
        # Restore BenchmarkLifecycleTracker (fix 3)
        if hasattr(self, "lifecycle_tracker"):
            lc_path = pathlib.Path(self.config.neuron.full_path) / "lifecycle_tracker.json"
            try:
                self.lifecycle_tracker.load_state(str(lc_path))
                bt.logging.info("BenchmarkLifecycleTracker state restored from disk.")
            except Exception as e:
                bt.logging.warning(f"Could not load BenchmarkLifecycleTracker state: {e}")

#!/usr/bin/env python3
# C-SWON — Execution Support Pool Payout Script (fix 2.7)
# Implements readme §4.6 off-chain payout computation.
#
# Usage:
#   python scripts/exec_support_payout.py \
#       --log-dir ~/.bittensor/validators/ \
#       --alpha-pool 10.0 \
#       --tempo 1234 \
#       --wallet-name owner \
#       --output payout_manifest.json
#
# The script reads score_aggregator.json files from one or more validator
# log directories, verifies each validator UID met the EXEC_SUPPORT_N_MIN
# threshold, then computes proportional Alpha transfer amounts and writes
# a signed payout manifest for the subnet owner to execute.

"""
Execution Support Pool Payout Tool (readme §4.6).

Payouts are computed off-chain from validator execution logs and sent as
Alpha transfers at each tempo boundary by the subnet owner.

Eligibility: validators that evaluate >= EXEC_SUPPORT_N_MIN tasks in a tempo.
Payout: proportional to tasks_evaluated among all eligible validators.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Constants (must match cswon/validator/config.py) ──────────────────────────

EXEC_SUPPORT_N_MIN = 100     # Minimum tasks per tempo for eligibility (readme §4.6)


# ── Log Parsing ───────────────────────────────────────────────────────────────

def _read_validator_log(log_dir: Path) -> Optional[dict]:
    """
    Read a validator's score_aggregator.json from its state directory.

    Returns:
        Parsed JSON dict, or None if file not found or unreadable.
    """
    agg_path = log_dir / "score_aggregator.json"
    if not agg_path.exists():
        return None
    try:
        return json.loads(agg_path.read_text())
    except Exception as e:
        print(f"  WARNING: Could not read {agg_path}: {e}", file=sys.stderr)
        return None


def _find_validator_dirs(log_root: Path) -> List[Tuple[str, Path]]:
    """
    Discover validator UID → state directory mappings under log_root.

    Expects subdirectories named by UID (e.g. '0/', '1/', ...) or by
    validator hotkey. Returns a list of (uid_or_name, path) tuples.
    """
    found = []
    if not log_root.exists():
        print(f"ERROR: log-dir {log_root} does not exist.", file=sys.stderr)
        return found
    for child in sorted(log_root.iterdir()):
        if child.is_dir():
            found.append((child.name, child))
    return found


# ── Payout Computation ────────────────────────────────────────────────────────

def compute_payouts(
    validator_tasks: Dict[str, int],
    alpha_pool: float,
    n_min: int = EXEC_SUPPORT_N_MIN,
) -> Dict[str, float]:
    """
    Compute proportional Alpha payout amounts (readme §4.6).

    Args:
        validator_tasks: uid/name → tasks_evaluated_this_tempo count.
        alpha_pool: Total Alpha available for distribution this tempo.
        n_min: Minimum tasks to be eligible for payout.

    Returns:
        Dict of uid/name → Alpha amount to transfer. Only eligible
        validators are included. Sum ≈ alpha_pool.
    """
    eligible = {
        uid: count
        for uid, count in validator_tasks.items()
        if count >= n_min
    }

    if not eligible:
        print("  No eligible validators (none met EXEC_SUPPORT_N_MIN).", file=sys.stderr)
        return {}

    total_tasks = sum(eligible.values())
    payouts = {}
    for uid, count in eligible.items():
        proportion = count / total_tasks
        payouts[uid] = round(proportion * alpha_pool, 8)

    return payouts


# ── Manifest Output ───────────────────────────────────────────────────────────

def build_manifest(
    payouts: Dict[str, float],
    alpha_pool: float,
    tempo: int,
    wallet_name: str,
) -> dict:
    """
    Build the payout manifest dict for signing and execution.

    The owner executes this manifest by iterating over the transfers list
    and calling `btcli wallet transfer` or equivalent SDK call for each entry.
    """
    manifest = {
        "version": "1.0",
        "tempo": tempo,
        "alpha_pool_allocated": alpha_pool,
        "alpha_pool_distributed": round(sum(payouts.values()), 8),
        "exec_support_n_min": EXEC_SUPPORT_N_MIN,
        "eligible_count": len(payouts),
        "owner_wallet": wallet_name,
        "note": (
            "Execute each transfer by running:\n"
            "  btcli wallet transfer --wallet.name <owner_wallet>"
            " --dest <dest_address> --amount <alpha_amount> --network finney"
        ),
        "transfers": [
            {"uid_or_hotkey": uid, "alpha_amount": amount}
            for uid, amount in sorted(payouts.items())
        ],
    }
    return manifest


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compute C-SWON Execution Support Pool payouts (readme §4.6).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--log-dir", required=True,
        help="Root directory containing validator state subdirectories.",
    )
    parser.add_argument(
        "--alpha-pool", type=float, required=True,
        help="Total Alpha tokens available for distribution this tempo.",
    )
    parser.add_argument(
        "--tempo", type=int, required=True,
        help="Tempo number this payout covers (for manifest provenance).",
    )
    parser.add_argument(
        "--wallet-name", default="owner",
        help="Owner wallet name (for manifest note). Default: 'owner'.",
    )
    parser.add_argument(
        "--output", default="payout_manifest.json",
        help="Output path for the payout manifest JSON. Default: payout_manifest.json",
    )
    parser.add_argument(
        "--n-min", type=int, default=EXEC_SUPPORT_N_MIN,
        help=f"Override minimum tasks threshold. Default: {EXEC_SUPPORT_N_MIN}.",
    )
    args = parser.parse_args()

    log_root = Path(args.log_dir)
    print(f"[exec_support_payout] Scanning validator dirs under: {log_root}")

    validator_dirs = _find_validator_dirs(log_root)
    if not validator_dirs:
        print("ERROR: No validator directories found.", file=sys.stderr)
        sys.exit(1)

    # Collect tasks_evaluated counts from each validator's persisted state
    validator_tasks: Dict[str, int] = {}
    for uid_name, vdir in validator_dirs:
        data = _read_validator_log(vdir)
        if data is None:
            print(f"  SKIP {uid_name}: no score_aggregator.json found.")
            continue
        tasks_count = data.get("tasks_executed_this_tempo", 0)
        validator_tasks[uid_name] = int(tasks_count)
        status = "✓ ELIGIBLE" if tasks_count >= args.n_min else "✗ below n_min"
        print(f"  Validator {uid_name}: tasks_evaluated={tasks_count} → {status}")

    print(f"\n[exec_support_payout] Computing payouts (alpha_pool={args.alpha_pool} α)...")
    payouts = compute_payouts(validator_tasks, args.alpha_pool, args.n_min)

    if not payouts:
        print("No payouts to distribute — manifest will be empty.")

    manifest = build_manifest(payouts, args.alpha_pool, args.tempo, args.wallet_name)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n[exec_support_payout] Payout manifest written to: {output_path}")
    print(f"  Eligible validators: {manifest['eligible_count']}")
    print(f"  Alpha distributed:   {manifest['alpha_pool_distributed']} / {args.alpha_pool}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Dump the C-SWON metagraph (netuid 26) as JSON for the frontend API.

Usage:
    python scripts/dump-metagraph.py > public/chain-data/metagraph.json

Run periodically or before deploy to snapshot live chain state.
"""
import json
import bittensor as bt

NETUID = 26
NETWORK = "test"

sub = bt.Subtensor(network=NETWORK)
mg = sub.metagraph(netuid=NETUID)

# Identify true validators by dividends > 0
neurons = []
for i in range(int(mg.n)):
    dividends = float(mg.D[i])
    incentive = float(mg.I[i])
    is_validator = dividends > 0
    is_miner = incentive > 0

    neurons.append({
        "uid": i,
        "hotkey": mg.hotkeys[i],
        "coldkey": mg.coldkeys[i],
        "stake": round(float(mg.S[i]), 4),
        "validator_trust": round(float(mg.validator_trust[i]), 6),
        "consensus": round(float(mg.C[i]), 6),
        "incentive": round(incentive, 6),
        "dividends": round(dividends, 6),
        "emission": round(float(mg.E[i]), 6),
        "active": bool(mg.active[i]),
        "validator_permit": bool(mg.validator_permit[i]),
        "role": "validator" if is_validator else ("miner" if is_miner else "inactive"),
    })

hp = sub.get_subnet_hyperparameters(netuid=NETUID)

result = {
    "block": int(mg.block),
    "netuid": NETUID,
    "network": NETWORK,
    "n": int(mg.n),
    "tempo": hp.tempo,
    "immunity_period": hp.immunity_period,
    "neurons": neurons,
}

print(json.dumps(result, indent=2))

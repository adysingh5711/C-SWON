# Local Deployment Guide — C-SWON

Run a fully isolated C-SWON subnet on your local machine.
No testnet TAO required. No external APIs. No WandB.

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | ≥ 3.10 | `python3 --version` |
| Docker | any recent | `docker --version` |
| Git | any | `git --version` |

Install the Bittensor CLI if you do not have it:

```bash
pip install bittensor
```

---

## Step 1 — Clone and install C-SWON

```bash
git clone https://github.com/adysingh5711/C-SWON.git
cd C-SWON

# Create and activate a virtual environment (strongly recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -e .
```

Verify the package installed correctly:

```bash
python -c "import cswon; print(cswon.__version__)"
```

---

## Step 2 — Create the `.env` file

Run this **once**. It generates a persistent secret salt and sets mock mode.

```bash
python -c "
import secrets
lines = [
    'CSWON_MOCK_EXEC=true',
    'CSWON_SYNTHETIC_SALT=' + secrets.token_hex(32),
]
open('.env', 'w').write('\n'.join(lines) + '\n')
print('Generated .env:')
print(open('.env').read())
"
```

Lock it out of git immediately:

```bash
echo ".env" >> .gitignore
```

Verify the environment is correctly configured:

```bash
set -a && source .env && set +a

python - <<'PY'
import os
salt = os.environ.get("CSWON_SYNTHETIC_SALT", "")
mock = os.environ.get("CSWON_MOCK_EXEC", "")
exp  = os.environ.get("CSWON_ENABLE_EXPERIMENTAL_EXEC", "NOT SET")
assert mock == "true",   f"CSWON_MOCK_EXEC must be 'true', got: '{mock}'"
assert len(salt) == 64,  f"CSWON_SYNTHETIC_SALT must be 64 hex chars, got len={len(salt)}"
assert exp == "NOT SET", f"CSWON_ENABLE_EXPERIMENTAL_EXEC must be unset, got: '{exp}'"
print("OK: environment is correctly configured for local deployment")
PY
```

---

## Step 3 — Start the local Subtensor chain

Open **Terminal 1** and keep it running throughout.

```bash
docker pull ghcr.io/opentensor/subtensor:devnet-ready

docker run --rm \
  --name local_chain \
  -p 9944:9944 \
  -p 9945:9945 \
  ghcr.io/opentensor/subtensor:devnet-ready
```

Wait for this line in the Docker output before proceeding:

```
💤 Idle (0 peers), best: #0
```

Verify the chain is reachable:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

---

## Step 4 — Create wallets

Open **Terminal 2** for all remaining steps.

```bash
# Owner (creates and funds the subnet)
btcli wallet new_coldkey --wallet.name owner

# Validator
btcli wallet new_coldkey --wallet.name vali
btcli wallet new_hotkey  --wallet.name vali --wallet.hotkey default

# Miner
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey  --wallet.name miner --wallet.hotkey default
```

---

## Step 5 — Fund wallets with local TAO

```bash
btcli wallet faucet --wallet.name owner --network ws://127.0.0.1:9944
btcli wallet faucet --wallet.name vali  --network ws://127.0.0.1:9944
btcli wallet faucet --wallet.name miner --network ws://127.0.0.1:9944
```

Verify balances:

```bash
btcli wallet balance --wallet.name owner --network ws://127.0.0.1:9944
btcli wallet balance --wallet.name vali  --network ws://127.0.0.1:9944
```

---

## Step 6 — Create the subnet

```bash
btcli subnet create \
  --network ws://127.0.0.1:9944 \
  --wallet.name owner
```

Note the `netuid` printed in the output. On a fresh local chain this is
typically `1`. Use this value in every command from here onwards.

Verify:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

---

## Step 7 — Register validator and miner

Replace `<netuid>` with the value from Step 6.

```bash
btcli subnets register \
  --network ws://127.0.0.1:9944 \
  --netuid <netuid> \
  --wallet.name vali \
  --wallet.hotkey default

btcli subnets register \
  --network ws://127.0.0.1:9944 \
  --netuid <netuid> \
  --wallet.name miner \
  --wallet.hotkey default
```

Stake the validator so it can set weights:

```bash
btcli stake add \
  --network ws://127.0.0.1:9944 \
  --netuid <netuid> \
  --wallet.name vali \
  --wallet.hotkey default
```

Verify both are registered:

```bash
btcli subnets metagraph \
  --network ws://127.0.0.1:9944 \
  --netuid <netuid>
```

You should see two entries — one with `validator_permit=True` (vali) and one without (miner).

---

## Step 8 — Verify the benchmark file

```bash
python - <<'PY'
from cswon.validator.config import BENCHMARK_PATH
import os, json
assert os.path.exists(BENCHMARK_PATH), f"Missing: {BENCHMARK_PATH}"
tasks = json.load(open(BENCHMARK_PATH))
active = [t for t in tasks if t.get("status", "active") == "active"]
print(f"OK: {len(active)} active benchmark tasks at {BENCHMARK_PATH}")
for t in active:
    print(f"  - {t['task_id']} ({t['task_type']})")
PY
```

Expected output:

```
OK: 5 active benchmark tasks at .../benchmarks/v1.json
  - code_001 (code)
  - rag_001 (rag)
  - agent_001 (agent)
  - data_001 (data_transform)
  - synthetic_001 (code)
```

---

## Step 9 — Start the miner (Terminal 3)

**Always start the miner before the validator.**

```bash
cd C-SWON
source .venv/bin/activate
set -a && source .env && set +a

python neurons/miner.py \
  --netuid <netuid> \
  --subtensor.network local \
  --subtensor.chain_endpoint ws://127.0.0.1:9944 \
  --wallet.name miner \
  --wallet.hotkey default \
  --wandb.off
```

Wait until you see:

```
C-SWON Miner initialised
```

---

## Step 10 — Start the validator (Terminal 4)

```bash
cd C-SWON
source .venv/bin/activate
set -a && source .env && set +a

python neurons/validator.py \
  --netuid <netuid> \
  --subtensor.network local \
  --subtensor.chain_endpoint ws://127.0.0.1:9944 \
  --wallet.name vali \
  --wallet.hotkey default \
  --wandb.off
```

---

## What correct operation looks like

### Miner logs (every ~5s)

```
Received task: code_001 type=code
Returning workflow plan for code_001: 2 nodes, est_cost=0.0040τ
C-SWON Miner running... block=42
```

### Validator logs (every forward pass)

```
Selected task: rag_001 type=rag synthetic=False at block 45
Received 1 responses from 1 miners
Validated 1 responses
Miner 1: S=0.4200 (success=0.700, cost=0.300, latency=0.150, reliability=0.100)
```

### Weight set log (once per tempo, every 360 blocks ≈ ~90s on local fast chain)

```
set_weights on chain successfully!
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No benchmark tasks loaded` | `v1.json` not found or malformed | Run Step 8 verification |
| `No serving miners found` | Validator started before miner | Start miner first, restart validator |
| `CSWON_SYNTHETIC_SALT not set` | `.env` not sourced | Run `set -a && source .env && set +a` |
| `ModuleNotFoundError: cswon` | Package not installed | Run `pip install -e .` |
| `Connection refused ws://127.0.0.1:9944` | Docker chain not running | Check Terminal 1 |
| `wallet not found` | Wrong `--wallet.name` | Check `~/.bittensor/wallets/` |
| Validator exits with `RuntimeError` | No miner serving | Start miner, wait for axon to serve, restart validator |
| `set_weights failed` | Validator not staked enough | Re-run `btcli stake add` |

---

## Notes

- `CSWON_MOCK_EXEC=true` is correct and intentional for local. The mock
  executor provides deterministic outputs for all 4 benchmark task types
  so miners are meaningfully differentiated by plan quality, not by random
  network variance. Live cross-subnet execution is a mainnet concern.
- `CSWON_ENABLE_EXPERIMENTAL_EXEC` must remain **unset**. Setting it
  causes the executor to query back into the same local subnet's metagraph
  pretending it is SN1/SN4, which produces garbage scores.
- Block time on the local chain is ~250ms in fast-blocks mode, so a full
  tempo (360 blocks) completes in roughly 90 seconds locally.
- Do not set weights manually. The validator's `set_weights()` fires
  automatically at each tempo boundary once it has scored at least one miner.
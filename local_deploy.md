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

---

## Step 1 — Clone and install C-SWON

```bash
git clone https://github.com/adysingh5711/C-SWON.git
cd C-SWON

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -e .
```

Verify:

```bash
python -c "import cswon; print(cswon.__version__)"
# Expected: 1.0.0

btcli --version
# Expected: BTCLI version: 9.x.x

python -c "import bittensor; print(bittensor.__version__)"
# Expected: 10.x.x
```

> If `btcli` is not found after activating the venv, run:
> `pip install bittensor` — this installs both the SDK and btcli together.

---

## Step 2 — Create the `.env` file

Run this **once** from inside the project directory.
It generates a persistent secret salt and locks mock mode on.

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

Open **Terminal 1** and keep it running throughout the entire session.

```bash
docker pull ghcr.io/opentensor/subtensor-localnet:devnet-ready

# No --rm flag: preserves chain state if Docker is accidentally stopped
docker run \
  --name local_chain \
  -p 9944:9944 \
  -p 9945:9945 \
  ghcr.io/opentensor/subtensor-localnet:devnet-ready
```

Wait for this line in Docker output before doing anything else:

```
💤 Idle (0 peers), best: #0
```

If the container already exists from a previous run, resume it instead of creating a new one:

```bash
docker start local_chain
```

Verify the chain is reachable:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

---

## Step 4 — Create wallets

Open **Terminal 2**. Start every new terminal session in this project with:

```bash
cd C-SWON
source .venv/bin/activate
set -a && source .env && set +a
```

Create coldkeys and hotkeys:

```bash
# Owner (creates the subnet)
btcli wallet new_coldkey --wallet.name owner
btcli wallet new_hotkey --wallet.name owner --wallet.hotkey default

# Validator
btcli wallet new_coldkey --wallet.name vali
btcli wallet new_hotkey  --wallet.name vali --wallet.hotkey default

# Miner
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey  --wallet.name miner --wallet.hotkey default
```

> Wallets are stored at `~/.bittensor/wallets/` and persist across sessions.
> Skip this step entirely if you have already created these wallets.

---

## Step 5 — Fund wallets with local TAO

The localnet image ships with a pre-funded Alice account (~1,000,000 TAO).
Use Alice to fund your coldkeys.

> **Port note:** Use `ws://127.0.0.1:9945` for all wallet operations in this step.
> Port `9944` is used everywhere else.

**5a — Import Alice's key:**

```bash
btcli wallet regen_coldkey \
  --wallet.name alice \
  --uri //Alice \
  --network ws://127.0.0.1:9945
```

Press Enter when prompted for a password (no password needed for dev keys).

**5b — Verify Alice has funds:**

```bash
btcli wallet balance \
  --wallet.name alice \
  --network ws://127.0.0.1:9945
# Expected: ~1,000,000 TAO
```

**5c — Get your wallet addresses:**

```bash
python - <<'PY'
import bittensor as bt
for name in ["owner", "vali", "miner"]:
    w = bt.Wallet(name=name)
    print(f"{name}: {w.coldkeypub.ss58_address}")
PY
```

**5d — Transfer TAO from Alice to each wallet:**

```bash
btcli wallet transfer \
  --wallet.name alice \
  --destination <owner_address_from_5c> \
  --network ws://127.0.0.1:9945

btcli wallet transfer \
  --wallet.name alice \
  --destination <vali_address_from_5c> \
  --network ws://127.0.0.1:9945

btcli wallet transfer \
  --wallet.name alice \
  --destination <miner_address_from_5c> \
  --network ws://127.0.0.1:9945
```

Enter `1000` when prompted for amount on each transfer.

**5e — Verify balances:**

```bash
btcli wallet balance --wallet.name owner  --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name vali  --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name miner --network ws://127.0.0.1:9945
```

---

## Step 6 — Create the subnet

```bash
btcli subnet create \
  --network ws://127.0.0.1:9944 \
  --wallet.name owner
```

Note the `netuid` printed in the output — typically `1` on a fresh local chain.
**Write this value down. You will use it in every command from here onwards.**

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
  --wallet.name vali \
  --wallet.hotkey default \
  --amount 100
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

### Weight set log (once per tempo, ~90s on local fast chain)

```
set_weights on chain successfully!
```

---

## Restart survival tests (required before going to testnet)

**Test 1 — Validator state survives restart:**

```bash
# Ctrl+C the validator, restart it with the same command.
# First line in logs must be:
ScoreAggregator state restored from disk
```

**Test 2 — Miner reconnection:**

```bash
# Ctrl+C the miner, restart it.
# Validator logs must show:
Metagraph updated, re-syncing hotkeys
```

Both must pass before proceeding to testnet.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `docker: No such image` | Wrong image name | Use `ghcr.io/opentensor/subtensor-localnet:devnet-ready` |
| `docker: container name already in use` | Container exists from prior run | Run `docker start local_chain` instead |
| `btcli wallet faucet` not found | Removed in btcli 9.x | Use Step 5 Alice transfer method |
| `btcli subnet start` not found | Removed in btcli 9.x | Not needed — skip it |
| `No benchmark tasks loaded` | `v1.json` missing or malformed | Run Step 8 verification |
| `No serving miners found` | Validator started before miner | Start miner first, restart validator |
| `CSWON_SYNTHETIC_SALT not set` | `.env` not sourced | Run `set -a && source .env && set +a` |
| `ModuleNotFoundError: cswon` | Package not installed | Run `pip install -e .` |
| `Connection refused ws://127.0.0.1:9944` | Chain not running | Check Terminal 1, run `docker start local_chain` |
| `wallet not found` | Wrong wallet name | Check `~/.bittensor/wallets/` |
| Validator exits with `RuntimeError` | No miner serving | Start miner first, restart validator |
| `set_weights failed` | Validator not staked enough | Re-run `btcli stake add --amount 100` |
| Alice balance shows 0 | Wrong port | Use `ws://127.0.0.1:9945` for wallet operations |

---

## Notes

- **Port 9944** — chain RPC. Used for subnet creation, registration,
  metagraph queries, and running neurons.
- **Port 9945** — node RPC. Used for wallet balance and transfer only.
- `CSWON_MOCK_EXEC=true` is correct and intentional for local and testnet.
  The mock executor gives deterministic outputs for all benchmark task types
  so miners are meaningfully differentiated by plan quality.
  Live cross-subnet execution is a mainnet concern.
- `CSWON_ENABLE_EXPERIMENTAL_EXEC` must remain **unset**. Setting it causes
  the executor to query back into the same subnet's metagraph, producing
  garbage scores.
- Block time on the local chain is ~250ms, so a full tempo (360 blocks)
  completes in roughly 90 seconds locally.
- Do not set weights manually. The validator fires `set_weights()`
  automatically at each tempo boundary once it has scored at least one miner.
# Local Deployment Guide — C-SWON

Run a fully isolated C-SWON subnet on your local machine.
No testnet TAO required. No external APIs. No WandB.

This guide is generic: it avoids workstation-specific paths, IPs, wallet
addresses, and fixed subnet IDs.

---

## Prerequisites

| Requirement | Version | Check |
| --- | --- | --- |
| Python | 3.10+ | `python3 --version` |
| Docker | recent | `docker --version` |
| Git | any recent | `git --version` |

---

## Step 1 — Clone and install C-SWON

```bash
git clone https://github.com/adysingh5711/C-SWON.git
cd C-SWON

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

Verify the install:

```bash
python -c "import cswon; print(cswon.__version__)"
btcli --version
python -c "import bittensor; print(bittensor.__version__)"
```

If `btcli` is missing after activation:

```bash
pip install bittensor
```

---

## Step 2 — Create the `.env` file

Generate a local-safe `.env` once from the repo root:

```bash
python -c "
import secrets
lines = [
    'CSWON_MOCK_EXEC=true',
    'CSWON_SYNTHETIC_SALT=' + secrets.token_hex(32),
]
open('.env', 'w').write('\n'.join(lines) + '\n')
print(open('.env').read())
"
```

Keep it out of git:

```bash
echo ".env" >> .gitignore
```

Verify the environment:

```bash
set -a && source .env && set +a

python - <<'PY'
import os
salt = os.environ.get("CSWON_SYNTHETIC_SALT", "")
mock = os.environ.get("CSWON_MOCK_EXEC", "")
exp = os.environ.get("CSWON_ENABLE_EXPERIMENTAL_EXEC", "NOT SET")
assert mock == "true", f"CSWON_MOCK_EXEC must be 'true', got: '{mock}'"
assert len(salt) == 64, f"CSWON_SYNTHETIC_SALT must be 64 hex chars, got len={len(salt)}"
assert exp == "NOT SET", f"CSWON_ENABLE_EXPERIMENTAL_EXEC must be unset, got: '{exp}'"
print("OK: environment is correctly configured for local deployment")
PY
```

---

## Step 3 — Start the local Subtensor chain

Create the container on first run:

```bash
docker pull ghcr.io/opentensor/subtensor-localnet:devnet-ready

docker run -d \
  --name local_chain \
  -p 9944:9944 \
  -p 9945:9945 \
  ghcr.io/opentensor/subtensor-localnet:devnet-ready
```

If the container already exists:

```bash
docker start local_chain
```

Wait for the node to become ready:

```bash
docker logs -f local_chain
```

You want to see normal block production before proceeding.

Verify the chain is reachable:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

Notes:

- Do not use `--rm` when creating `local_chain`.
- Use `ws://127.0.0.1:9944` for subnet queries and neuron traffic.
- Use `ws://127.0.0.1:9945` for wallet operations.

---

## Step 4 — Create or inspect wallets

Start every new terminal session like this:

```bash
cd C-SWON
source .venv/bin/activate
set -a && source .env && set +a
```

If the wallets do not exist yet, create them:

```bash
btcli wallet new_coldkey --wallet.name owner
btcli wallet new_hotkey  --wallet.name owner --wallet.hotkey default

btcli wallet new_coldkey --wallet.name vali
btcli wallet new_hotkey  --wallet.name vali --wallet.hotkey default

btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey  --wallet.name miner --wallet.hotkey default
```

Wallets live under `~/.bittensor/wallets` and persist across sessions.

Inspect addresses:

```bash
python - <<'PY'
import bittensor as bt
for name in ["owner", "vali", "miner"]:
    w = bt.Wallet(name=name)
    print(f"{name}: coldkey={w.coldkeypub.ss58_address} hotkey={w.hotkey.ss58_address}")
PY
```

---

## Step 5 — Fund wallets with local TAO

Import Alice on localnet:

```bash
btcli wallet regen_coldkey \
  --wallet.name alice \
  --uri //Alice \
  --network ws://127.0.0.1:9945
```

Check Alice's balance:

```bash
btcli wallet balance --wallet.name alice --network ws://127.0.0.1:9945
```

Transfer funds from Alice to your wallets:

```bash
btcli wallet transfer \
  --wallet.name alice \
  --destination <owner-coldkey> \
  --network ws://127.0.0.1:9945

btcli wallet transfer \
  --wallet.name alice \
  --destination <vali-coldkey> \
  --network ws://127.0.0.1:9945

btcli wallet transfer \
  --wallet.name alice \
  --destination <miner-coldkey> \
  --network ws://127.0.0.1:9945
```

Use a reasonable local amount such as `1000` when prompted.

Verify balances:

```bash
btcli wallet balance --wallet.name alice --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name owner --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name vali  --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name miner --network ws://127.0.0.1:9945
```

---

## Step 6 — Create or reuse a subnet

Inspect current subnets:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

If you already own a local subnet, reuse its `netuid` and export it:

```bash
export NETUID=<netuid>
```

If you need a fresh one:

```bash
btcli subnet create \
  --network ws://127.0.0.1:9945 \
  --wallet.name owner \
  --wallet.hotkey default \
  --no-mev-protection
```

Then export the created subnet ID:

```bash
export NETUID=<netuid>
```

If needed, start emissions:

```bash
btcli subnet start \
  --network ws://127.0.0.1:9945 \
  --wallet.name owner \
  --netuid "$NETUID"
```

Verify the subnet exists:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

---

## Step 7 — Register validator and miner

Register both wallets on the subnet:

```bash
btcli subnets register \
  --network ws://127.0.0.1:9945 \
  --netuid "$NETUID" \
  --wallet.name vali \
  --wallet.hotkey default

btcli subnets register \
  --network ws://127.0.0.1:9945 \
  --netuid "$NETUID" \
  --wallet.name miner \
  --wallet.hotkey default
```

Stake the validator so it can set weights:

```bash
btcli stake add \
  --network ws://127.0.0.1:9945 \
  --wallet.name vali \
  --wallet.hotkey default \
  --amount 100 \
  --no-mev-protection \
  --tolerance 1.0
```

Verify registration state:

```bash
btcli subnets metagraph \
  --network ws://127.0.0.1:9944 \
  --netuid "$NETUID"
```

You should see the validator and miner on the chosen subnet.

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

Expected active tasks:

```text
code_001
rag_001
agent_001
data_001
synthetic_001
```

---

## Step 9 — Prepare for launch

Resolve a non-loopback axon IP for this machine:

```bash
export LOCAL_AXON_IP="$(python - <<'PY'
from cswon.utils.hotkey_extrinsics import get_preferred_local_axon_ip
ip = get_preferred_local_axon_ip()
if ip is None:
    raise SystemExit("Could not detect a non-loopback local IP. Set LOCAL_AXON_IP manually.")
print(ip)
PY
)"
echo "$LOCAL_AXON_IP"
```

Stop stale neuron processes before a clean restart:

```bash
ps -ax -o pid=,command= | rg 'neurons/(miner|validator)\.py'
kill <pid_1> <pid_2> ...
```

---

## Step 10 — Start the miner

Always start the miner before the validator.

```bash
python neurons/miner.py \
  --netuid "$NETUID" \
  --subtensor.network local \
  --subtensor.chain_endpoint ws://127.0.0.1:9944 \
  --wallet.name miner \
  --wallet.hotkey default \
  --axon.port 8091 \
  --axon.external_port 8091 \
  --axon.external_ip "$LOCAL_AXON_IP" \
  --blacklist.force_validator_permit \
  --wandb.off
```

Healthy startup indicators:

- The process stays alive.
- The miner registers an axon on-chain.
- The main process exits if the worker thread crashes instead of hanging.

---

## Step 11 — Start the validator

```bash
python neurons/validator.py \
  --netuid "$NETUID" \
  --subtensor.network local \
  --subtensor.chain_endpoint ws://127.0.0.1:9944 \
  --wallet.name vali \
  --wallet.hotkey default \
  --axon.port 8092 \
  --axon.external_port 8092 \
  --axon.external_ip "$LOCAL_AXON_IP" \
  --wandb.off
```

Healthy startup indicators:

- The process stays alive.
- It starts receiving valid miner responses.
- It keeps updating local scoring state over time.

---

## Step 12 — Post-launch verification

Check live subnet hyperparameters:

```bash
python - <<'PY'
import bittensor as bt
import os
subtensor = bt.Subtensor(network='ws://127.0.0.1:9944')
params = subtensor.get_subnet_hyperparameters(int(os.environ["NETUID"]))
for attr in ["tempo", "weights_rate_limit", "max_validators", "immunity_period"]:
    print(attr, getattr(params, attr, None))
PY
```

Inspect current axon registrations:

```bash
python - <<'PY'
import bittensor as bt
import os
subtensor = bt.Subtensor(network='ws://127.0.0.1:9944')
metagraph = subtensor.metagraph(int(os.environ["NETUID"]))
for name in ["vali", "miner"]:
    wallet = bt.Wallet(name=name)
    uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
    axon = metagraph.axons[uid]
    print(name, axon.ip, axon.port, bool(axon.is_serving))
PY
```

Inspect validator scoring state:

```bash
sed -n '1,200p' ~/.bittensor/neurons/vali/default/netuid${NETUID}/validator/score_aggregator.json
```

---

## What correct operation looks like

Typical miner logs:

```text
Received task: code_001 type=code
Returning workflow plan for code_001: 1 nodes, est_cost=0.0010τ
```

Typical validator logs:

```text
Selected task: rag_001 type=rag synthetic=False at block 45
Received 1 responses from 1 miners
Validated 1 responses
```

Typical weight-setting log:

```text
set_weights on chain successfully!
```

---

## Restart survival tests

Validator restart check:

```bash
# Stop and restart the validator.
# Confirm it restores local state and continues scoring.
```

Miner restart check:

```bash
# Stop and restart the miner.
# Confirm the validator resumes getting valid responses.
```

Run both before promoting the flow to testnet.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `docker: No such image` | Wrong image name | Use `ghcr.io/opentensor/subtensor-localnet:devnet-ready` |
| `docker: container name already in use` | Container already exists | Use `docker start local_chain` |
| `Connection refused ws://127.0.0.1:9944` | Chain not running | Start or restart `local_chain` |
| `wallet not found` | Wallet files missing | Create or import the wallet first |
| `No benchmark tasks loaded` | Benchmark file missing or malformed | Re-run Step 8 |
| `No serving miners found` | Validator started before miner | Start miner first, then validator |
| `set_weights failed` | Validator not staked enough | Re-run the validator stake command |
| Validator sees `503 Service unavailable` | Miner axon IP is unreachable | Recompute `LOCAL_AXON_IP` and restart with explicit `--axon.external_ip "$LOCAL_AXON_IP"` |
| `CSWON_SYNTHETIC_SALT not set` | `.env` not sourced | Re-run `set -a && source .env && set +a` |
| `ModuleNotFoundError: cswon` | Package not installed | Run `pip install -e .` |

---

## Notes

- `CSWON_MOCK_EXEC=true` is the correct local and staged-testnet setting.
- `CSWON_ENABLE_EXPERIMENTAL_EXEC` should remain unset.
- Local fast blocks are short, so tempo boundaries arrive quickly compared with public networks.
- Do not disable validator-permit enforcement unless you are doing isolated debugging.

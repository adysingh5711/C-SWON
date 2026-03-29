# Local Deployment Guide — C-SWON

This guide is intended to work for any machine running a local Subtensor node.
It keeps the flow generic and uses discovery commands instead of workstation-
specific wallet names, IPs, or subnet IDs.

The important defaults for local development are:

- Keep `CSWON_MOCK_EXEC=true`.
- Keep `CSWON_ENABLE_EXPERIMENTAL_EXEC` unset.
- Use `ws://127.0.0.1:9945` for wallet transfers and balances.
- Use `ws://127.0.0.1:9944` for subnet queries and neuron traffic.
- On local chains, advertise axons on a non-loopback IP from the machine running the neurons.
- Keep validator-permit enforcement enabled for the miner.

---

## 1. Prepare the environment

Activate your Python environment, enter the repo, and source `.env`:

```bash
source <path-to-venv>/bin/activate
cd <path-to-repo>
set -a && source .env && set +a
```

Verify the local-safe flags:

```bash
python - <<'PY'
import os
assert os.environ["CSWON_MOCK_EXEC"].lower() == "true"
assert len(os.environ["CSWON_SYNTHETIC_SALT"]) == 64
assert "CSWON_ENABLE_EXPERIMENTAL_EXEC" not in os.environ
print("OK: local-safe execution flags are set")
PY
```

Resolve a non-loopback IP for local axon advertisement:

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

---

## 2. Start or reuse the local chain

Create the container if this is the first run:

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

Wait for block production:

```bash
docker logs -f local_chain
```

Check chain reachability:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

Notes:

- Do not use `--rm` when creating `local_chain`.
- Reuse the same container if you want the chain state to persist.

---

## 3. Prepare wallets and balances

List existing wallets:

```bash
ls ~/.bittensor/wallets
```

Inspect wallet addresses:

```bash
python - <<'PY'
import bittensor as bt
for name in ["owner", "vali", "miner"]:
    try:
        w = bt.Wallet(name=name)
        print(f"{name}: coldkey={w.coldkeypub.ss58_address} hotkey={w.hotkey.ss58_address}")
    except Exception as e:
        print(f"{name}: missing ({e})")
PY
```

Check balances:

```bash
btcli wallet balance --wallet.name alice --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name owner --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name vali  --network ws://127.0.0.1:9945
btcli wallet balance --wallet.name miner --network ws://127.0.0.1:9945
```

If needed, fund your wallets from Alice using the coldkeys shown above:

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

---

## 4. Create or reuse a subnet

Inspect available subnets:

```bash
btcli subnet list --network ws://127.0.0.1:9944
```

If you already own a subnet on the local chain, reuse its `netuid`.

Export it for the remaining steps:

```bash
export NETUID=<netuid>
```

If you need a fresh subnet:

```bash
btcli subnet create \
  --network ws://127.0.0.1:9945 \
  --wallet.name owner \
  --wallet.hotkey default \
  --no-mev-protection
```

If needed, start emissions:

```bash
btcli subnet start \
  --network ws://127.0.0.1:9945 \
  --wallet.name owner \
  --netuid "$NETUID"
```

Check registration and permits on your chosen subnet:

```bash
python - <<'PY'
import bittensor as bt
import os
subtensor = bt.Subtensor(network='ws://127.0.0.1:9944')
netuid = int(os.environ["NETUID"])
metagraph = subtensor.metagraph(netuid)
for name in ["owner", "vali", "miner"]:
    wallet = bt.Wallet(name=name)
    hotkey = wallet.hotkey.ss58_address
    if hotkey in metagraph.hotkeys:
        uid = metagraph.hotkeys.index(hotkey)
        print(
            f"{name}: uid={uid} permit={bool(metagraph.validator_permit[uid])} "
            f"stake={float(metagraph.S[uid])}"
        )
    else:
        print(f"{name}: not registered")
PY
```

---

## 5. Register and stake if needed

Register the validator and miner if they are not already on the subnet:

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

Stake the validator if it needs enough stake to set weights:

```bash
btcli stake add \
  --network ws://127.0.0.1:9945 \
  --wallet.name vali \
  --wallet.hotkey default \
  --amount 100 \
  --no-mev-protection \
  --tolerance 1.0
```

---

## 6. Verify benchmark tasks

```bash
python - <<'PY'
from cswon.validator.config import BENCHMARK_PATH
import json
with open(BENCHMARK_PATH) as f:
    tasks = json.load(f)
active = [t for t in tasks if t.get("status", "active") == "active"]
print(BENCHMARK_PATH)
print(f"active_tasks={len(active)}")
print([t["task_id"] for t in active])
PY
```

---

## 7. Stop stale neuron processes

Before a clean restart:

```bash
ps -ax -o pid=,command= | rg 'neurons/(miner|validator)\.py'
kill <pid_1> <pid_2> ...
```

---

## 8. Start the miner

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
- The miner registers an axon on the chosen subnet.
- The main process exits if the worker thread crashes.

---

## 9. Start the validator

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
- It continues updating local scoring state over time.

---

## 10. Post-launch verification

Inspect the live subnet hyperparameters:

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

Inspect the current axon registrations:

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

Check the validator state files if you want to confirm scoring is moving:

```bash
sed -n '1,200p' ~/.bittensor/neurons/vali/default/netuid${NETUID}/validator/score_aggregator.json
```

---

## 11. Security notes for later testnet deployment

- Leave `CSWON_MOCK_EXEC=true` for local and staged testnet deployment unless you are explicitly testing another execution path.
- Leave `CSWON_ENABLE_EXPERIMENTAL_EXEC` unset.
- Keep validator-permit enforcement enabled.
- Do not use `--blacklist.allow_non_registered` outside isolated debugging.
- If a neuron background worker crashes, the top-level process should exit instead of idling forever.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `docker start local_chain` fails | Container does not exist yet | Run the first-time `docker run -d --name local_chain ...` command |
| `docker: container name already in use` | The container already exists | Use `docker start local_chain` instead of `docker run` |
| `No serving miners found on subnet` | Validator started before miner | Start the miner first, then restart the validator |
| Neuron process stays alive but chain state does not advance | Stale old process or dead worker thread | Kill the stale process and restart from Steps 7-9 |
| `wallet not found` | Missing local wallet files | Recreate the wallet or point the commands at the correct wallet names |
| Transfers or balances fail on `9944` | Wrong RPC port | Use `ws://127.0.0.1:9945` for wallet operations |
| Validator sees `503 Service unavailable` when querying the miner | The chain advertises an unreachable IP for the miner | Recompute `LOCAL_AXON_IP` and restart with explicit `--axon.external_ip "$LOCAL_AXON_IP"` flags |
| Miner rejects requests | Caller lacks validator permit | Ensure the validator is registered and has validator permit on the target subnet |
| `CSWON_SYNTHETIC_SALT` missing | `.env` not sourced | Re-run `set -a && source .env && set +a` |

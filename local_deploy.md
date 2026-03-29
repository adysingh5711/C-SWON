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
| pip packages | bittensor 10.x, bittensor-cli, bittensor-wallet | `pip list \| grep bittensor` |

---

## Step 1 — Clone and install C-SWON

```bash
git clone https://github.com/adysingh5711/C-SWON.git
cd C-SWON

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
pip install pexpect   # needed for automated btcli password handling
```

Verify the install:

```bash
python -c "import cswon; print(cswon.__version__)"
btcli --version
python -c "import bittensor; print(bittensor.__version__)"
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

Load it in every terminal session:

```bash
set -a && source .env && set +a
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

> **Warning:** `docker restart local_chain` resets all chain state (wallets, subnets, registrations, stake). You will need to redo Steps 5-8.

Wait for block production:

```bash
docker logs -f local_chain   # Ctrl-C once you see blocks
```

**Two endpoints:**

| Port | Use for |
| --- | --- |
| `ws://127.0.0.1:9944` | Subnet queries, neuron traffic, metagraph |
| `ws://127.0.0.1:9945` | Wallet operations (transfer, stake, register, subnet create) |

---

## Step 4 — Create wallets

```bash
btcli wallet new_coldkey --wallet.name owner
btcli wallet new_hotkey  --wallet.name owner --wallet.hotkey default

btcli wallet new_coldkey --wallet.name vali
btcli wallet new_hotkey  --wallet.name vali --wallet.hotkey default

btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey  --wallet.name miner --wallet.hotkey default
```

Also import Alice (the dev faucet with 1M TAO):

```bash
btcli wallet regen_coldkey \
  --wallet.name alice \
  --uri //Alice \
  --network ws://127.0.0.1:9945
```

---

## Step 5 — Fund wallets

Use btcli to transfer from Alice to each wallet:

```bash
btcli wallet transfer \
  --wallet.name alice \
  --destination <owner-coldkey> \
  --network ws://127.0.0.1:9945
# Enter amount: 100000

btcli wallet transfer \
  --wallet.name alice \
  --destination <vali-coldkey> \
  --network ws://127.0.0.1:9945
# Enter amount: 100000

btcli wallet transfer \
  --wallet.name alice \
  --destination <miner-coldkey> \
  --network ws://127.0.0.1:9945
# Enter amount: 100000
```

**Alternative (SDK):** If btcli prompts are problematic, use a Python script with `AsyncSubstrateInterface` and Alice's unencrypted keypair:

```python
from bittensor_wallet import Wallet
from async_substrate_interface import AsyncSubstrateInterface
import asyncio

async def fund():
    alice = Wallet(name='alice', path='~/.bittensor/wallets')
    sub = AsyncSubstrateInterface(url='ws://127.0.0.1:9945')
    await sub.initialize()
    for addr in ["<owner-coldkey>", "<vali-coldkey>", "<miner-coldkey>"]:
        call = await sub.compose_call(
            call_module='Balances',
            call_function='transfer_keep_alive',
            call_params={'dest': addr, 'value': 100_000 * 10**9},
        )
        ext = await sub.create_signed_extrinsic(call=call, keypair=alice.coldkey)
        receipt = await sub.submit_extrinsic(ext, wait_for_inclusion=True)
        print(f'{addr}: {await receipt.is_success}')
    await sub.close()

asyncio.run(fund())
```

---

## Step 6 — Create subnet

```bash
btcli subnet create \
  --network ws://127.0.0.1:9945 \
  --wallet-name owner \
  --hotkey default \
  --no-mev-protection
```

> The `--no-mev-protection` flag is required on local chains; MEV Shield fails on devnet.

Note the netuid from the output (usually 2) and export it:

```bash
export NETUID=2
```

**Start emissions** (required before staking works):

```bash
btcli subnet start \
  --network ws://127.0.0.1:9945 \
  --wallet-name owner \
  --netuid "$NETUID"
```

---

## Step 7 — Configure chain hyperparameters

The devnet chain ships with defaults that break local testing. Fix them using Alice's sudo key via the SDK:

```python
import asyncio
from bittensor_wallet import Wallet
from async_substrate_interface import AsyncSubstrateInterface

async def configure():
    alice = Wallet(name='alice', path='~/.bittensor/wallets')
    owner = Wallet(name='owner', path='~/.bittensor/wallets')
    owner_kp = owner.get_coldkey(password='<your-password>')

    sub = AsyncSubstrateInterface(url='ws://127.0.0.1:9945')
    await sub.initialize()

    # 1. Disable commit-reveal (causes bad-signature on devnet)
    for attempt in range(5):
        call = await sub.compose_call(
            call_module='AdminUtils',
            call_function='sudo_set_commit_reveal_weights_enabled',
            call_params={'netuid': 2, 'enabled': False},
        )
        ext = await sub.create_signed_extrinsic(call=call, keypair=owner_kp)
        receipt = await sub.submit_extrinsic(ext, wait_for_inclusion=True)
        ok = await receipt.is_success
        if ok:
            print('commit_reveal disabled')
            break
        err = await receipt.error_message
        if 'WeightsWindow' in str(err):
            await asyncio.sleep(12)  # wait for window to close
        else:
            print(f'Failed: {err}')
            break

    # 2. Set weights_rate_limit = tempo (requires Alice sudo)
    for fname, params in [
        ('sudo_set_weights_set_rate_limit', {'netuid': 2, 'weights_set_rate_limit': 10}),
    ]:
        inner = await sub.compose_call(call_module='AdminUtils', call_function=fname, call_params=params)
        sudo = await sub.compose_call(call_module='Sudo', call_function='sudo', call_params={'call': inner})
        ext = await sub.create_signed_extrinsic(call=sudo, keypair=alice.coldkey)
        receipt = await sub.submit_extrinsic(ext, wait_for_inclusion=True)
        print(f'{fname}: {await receipt.is_success}')

    await sub.close()

asyncio.run(configure())
```

**Why these changes are needed:**

| Parameter | Default | Required | Reason |
| --- | --- | --- | --- |
| `commit_reveal_weights_enabled` | `true` | `false` | Commit-reveal timelocked weights produce "bad signature" on devnet |
| `weights_rate_limit` | `100` | `10` (= tempo) | Default is 10x the tempo; validator can only set weights every 100 blocks instead of every tempo |

**Verify:**

```bash
python -c "
import bittensor as bt
hp = bt.Subtensor(network='ws://127.0.0.1:9944').get_subnet_hyperparameters(netuid=2)
print(f'commit_reveal={hp.commit_reveal_weights_enabled}')
print(f'weights_rate_limit={hp.weights_rate_limit}')
print(f'tempo={hp.tempo}')
"
```

Expected: `commit_reveal=False`, `weights_rate_limit=10`, `tempo=10`.

---

## Step 8 — Register and stake

```bash
# Register validator
btcli subnets register \
  --network ws://127.0.0.1:9945 \
  --netuid "$NETUID" \
  --wallet-name vali \
  --hotkey default \
  --no-prompt

# Register miner
btcli subnets register \
  --network ws://127.0.0.1:9945 \
  --netuid "$NETUID" \
  --wallet-name miner \
  --hotkey default \
  --no-prompt

# Stake validator (use port 9945, small amount to avoid slippage)
btcli stake add \
  --network ws://127.0.0.1:9945 \
  --wallet-name vali \
  --hotkey default \
  --amount 100 \
  --no-mev-protection \
  --tolerance 1.0
# When prompted for netuid, enter your NETUID (e.g. 2)
```

> **Slippage:** On a fresh chain the AMM pool is small. Stake 100 TAO first; larger amounts fail with `SlippageTooHigh`. The pool grows over time.

> **`subnet start` must be done first** (Step 6). Without it, staking fails with `SubtokenDisabled`.

Verify:

```bash
btcli subnet metagraph --netuid "$NETUID" --network ws://127.0.0.1:9944
```

You should see the validator with non-zero stake and `vpermit=True`.

---

## Step 9 — Resolve axon IP

```bash
export LOCAL_AXON_IP="$(python -c "
from cswon.utils.hotkey_extrinsics import get_preferred_local_axon_ip
ip = get_preferred_local_axon_ip()
if ip is None:
    raise SystemExit('Could not detect a non-loopback local IP. Set LOCAL_AXON_IP manually.')
print(ip)
")"
echo "$LOCAL_AXON_IP"
```

---

## Step 10 — Start the miner (first)

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

---

## Step 11 — Start the validator (separate terminal)

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

---

## Step 12 — Verify operation

**Check scoring in validator logs:**

```text
Selected task: data_001 type=data_transform synthetic=False at block 1234
Received 1 responses from 1 miners
Validated 1 responses
Scored 1 miners: mean=0.9500
Miner 2: S=0.9500 (success=1.000, cost=0.800, latency=1.000, reliability=1.000)
```

**Check weight submission:**

```text
set_weights on chain successfully!
```

**Check emissions:**

```python
import bittensor as bt
s = bt.Subtensor(network='ws://127.0.0.1:9944')
mg = s.metagraph(netuid=2)
for i in range(int(mg.n)):
    print(f'UID {i}: stake={mg.S[i]:.2f} incentive={mg.I[i]:.4f} dividend={mg.D[i]:.4f} vtrust={mg.validator_trust[i]:.4f}')
```

Expected: validator has `dividend=1.0, vtrust=1.0`; miner has `incentive=1.0`.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Transaction has a bad signature` on set_weights | `commit_reveal_weights_enabled=true` | Run Step 7 to disable it |
| `SubtokenDisabled` on staking | Subnet emissions not started | Run `btcli subnet start` (Step 6) |
| `SlippageTooHigh` on staking | Amount too large for AMM pool | Stake smaller amount (50-100 TAO) |
| `NeuronNoValidatorPermit` on set_weights | Validator has no stake / no vpermit | Complete Step 8 staking |
| `No serving miners found` at validator start | Miner not started or not yet registered axon | Start miner first, wait 10s |
| `No miners available to query` | All UIDs have vpermit + stake > 1024 | Code handles this on local chains automatically |
| `ConcurrencyError: cannot call recv` | Websocket thread conflict | Fixed in code; don't call `self.block` from main thread |
| `No valid responses received` | Miner forward() returning None fields | Verify miner process is alive and axon is serving |
| `docker restart` lost all state | Devnet chain is ephemeral | Redo Steps 5-8 after any restart |
| Scores all show `success=0.000` | Miner capability inference misses task keywords | Check `_infer_required_capabilities()` in `neurons/miner.py` |
| `AdminActionProhibitedDuringWeightsWindow` | Admin call during protected window | Retry after 12 seconds |
| `BadOrigin` on admin calls | Some params need root (Alice) sudo | Use `Sudo::sudo` wrapper with Alice keypair |

---

## Notes

- `CSWON_MOCK_EXEC=true` is the correct local setting. No real subnet calls are made.
- `CSWON_ENABLE_EXPERIMENTAL_EXEC` should remain unset.
- The devnet chain has `tempo=10` (fast blocks). Tempo boundaries arrive every ~2 minutes.
- On local chains, all UIDs may get `validator_permit=True` due to AMM staking. The code handles this automatically by treating all serving non-self UIDs as miners.
- **SDK vs CLI usage:** Use btcli for wallet operations (create, transfer, register, stake). Use the Python SDK (`AsyncSubstrateInterface`) for chain config changes that btcli doesn't expose cleanly (commit-reveal, rate limits). Use `bittensor.Subtensor` for verification queries.
- Wallet passwords: btcli prompts interactively. For automation, use `bittensor_wallet.Wallet.get_coldkey(password=...)` in Python scripts.

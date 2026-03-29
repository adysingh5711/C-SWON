# Testnet Deployment Guide for C-SWON

This guide provides step-by-step instructions to deploy the C-SWON subnet on the Bittensor Testnet for staging your subnet and testing interactions before moving to the main chain (`finney`).

## 1. Prerequisites

Before you start, ensure you have the following:
- **Bittensor SDK and CLI**: Install the official `bittensor` Python package (`pip install bittensor`).
- **A provisioned Wallet**: You must have a wallet (coldkey + hotkey) created.
- **Test TAO**: To create a subnet or register on the testnet, your wallet must hold Test TAO.
  - *Note: Test TAO can be requested from the OpenTensor Discord (`#testnet-faucet` or related threads).*

## 2. Setting Up Your Wallets

1. **Create the owner wallet (coldkey)**:
   ```bash
   btcli wallet new_coldkey --wallet.name owner
   ```

2. **Create validator and miner wallets**:
   ```bash
   btcli wallet new_coldkey --wallet.name vali
   btcli wallet new_hotkey --wallet.name vali --wallet.hotkey default

   btcli wallet new_coldkey --wallet.name miner
   btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default
   ```

*Make sure your `owner` wallet has received Test TAO before proceeding to the next step.*

## 3. Create the Subnet on Testnet

Use the `owner` wallet to create a new subnet on the testnet.

1. **Run the create command**:
   ```bash
   btcli subnet create --network test --wallet.name owner
   ```
   *Follow the prompts and accept the registration. You'll be given a `netuid`. Note this down as you'll need it when running the miner, validator, and for registrations.*

2. **Check your Testnet Subnet**:
   ```bash
   btcli subnet list --network test
   ```
   *Verify your newly created `netuid` is on the list.*

## 4. Register Validator and Miner

Once your subnet is live, you must register your hotkeys onto the testnet subnet.

1. **Register Validator**:
   ```bash
   btcli subnets register --network test --netuid <netuid> --wallet.name vali --wallet.hotkey default
   ```

2. **Register Miner**:
   ```bash
   btcli subnets register --network test --netuid <netuid> --wallet.name miner --wallet.hotkey default
   ```

3. **Stake the Validator**:
   ```bash
   btcli stake add --network test --wallet.name vali --wallet.hotkey default
   ```
   *Note: Ensure `vali` coldkey has sufficient Test TAO to stake and hit the minimum required stake for setting weights (usually determined by the network protocol).*

## 5. Start the Subnet (Testnet)

By default, subnets don't emit until activated. If testing emissions, start the subnet:
```bash
btcli subnet start --netuid <netuid> --network test
```

## 5.1 Disable Commit-Reveal Weights

Testnet defaults to `commit_reveal_weights_enabled=true`, which causes `Transaction has a bad signature` errors on weight submission. Disable it:

```bash
btcli sudo set --netuid <netuid> --param commit_reveal_weights_enabled --value false --network test --wallet.name owner
```

Verify:
```bash
btcli sudo get --netuid <netuid> --network test | grep commit_reveal
```

Expected: `commit_reveal_weights_enabled: False`

## 5.2 Configure Subnet Hyperparameters (Recommended)

For faster iteration on testnet, adjust these hyperparameters:

```bash
# Lower tempo for faster weight updates (default 360 → 60)
btcli sudo set --netuid <netuid> --param tempo --value 60 --network test --wallet.name owner

# Match weights_rate_limit to tempo
btcli sudo set --netuid <netuid> --param weights_set_rate_limit --value 60 --network test --wallet.name owner

# Lower immunity period for faster miner turnover
btcli sudo set --netuid <netuid> --param immunity_period --value 500 --network test --wallet.name owner

# If only 1-2 miners, lower min_allowed_weights
btcli sudo set --netuid <netuid> --param min_allowed_weights --value 1 --network test --wallet.name owner
```

> **Weight submission cadence:** The validator submits weights every `max(tempo, weights_rate_limit)` blocks. With defaults (tempo=360, rate_limit=100), weights submit every 360 blocks (~72 min). With the recommended settings above, every 60 blocks (~12 min).

## 5.3 Enable Emissions (Root Subnet Registration)

For emissions to flow to your subnet, register on the root network and set root weights:

```bash
btcli root register --subtensor.network test --wallet.name owner
btcli root weights --subtensor.network test --wallet.name owner
```

Without this step, your subnet will have zero emissions even after staking.

## 6. Run the C-SWON Subnet

> **CLI flag conventions:**
> - `btcli` commands use `--network test` (chain-level flag)
> - Neuron scripts (`neurons/validator.py`, `neurons/miner.py`) use `--subtensor.network test` (SDK-level flag)
> - These are different CLI frameworks and are NOT interchangeable

Navigate to your C-SWON local repository, ensure dependencies are installed (`pip install -r requirements.txt` and `pip install -e .`), and launch the nodes:

1. **Run the Miner**:
   ```bash
   python neurons/miner.py \
     --netuid <netuid> \
     --subtensor.network test \
     --wallet.name miner \
     --wallet.hotkey default \
     --wandb.off
   ```

2. **Run the Validator**:
   ```bash
   python neurons/validator.py \
     --netuid <netuid> \
     --subtensor.network test \
     --wallet.name vali \
     --wallet.hotkey default \
      --wandb.off
   ```

## 6.1 Required environment variables

> **CRITICAL:** Both variables below are **required**. The validator will refuse to start on testnet without `CSWON_SYNTHETIC_SALT`. Generate a persistent salt once and reuse it across restarts for scoring consistency.

```bash
export CSWON_MOCK_EXEC=true
export CSWON_SYNTHETIC_SALT=$(python -c "import secrets; print(secrets.token_hex(32))")
```

Save the salt value somewhere safe — reuse the same salt if you restart the validator.

---

## Codebase Checks & Potential Testnet Deployment Issues

When running C-SWON on the testnet, be aware of the following potential codebase configurations that need override:

1. **Wandb Configuration**:
   WandB logging defaults are empty (no entity or project configured). If you want to enable WandB, pass your own entity and project strings: `--wandb.entity your-org --wandb.project_name your-project`. Otherwise, use `--wandb.off` to disable logging entirely (recommended for testnet).

2. **`--netuid` is required**:
   There is no default `netuid` — you must always pass `--netuid <netuid>` matching the one returned when your subnet was created. The CLI will error if you forget this flag.

3. **Environment and Secrets Management**:
   If your C-SWON application relies on local environmental keys (API endpoints, specific db credentials, OpenAI keys for generation, etc.), these must be available to the processes running `neurons/miner.py` and `neurons/validator.py`. Missing local configuration could cause exceptions when workflows trigger.

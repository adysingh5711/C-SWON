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

## 6. Run the C-SWON Subnet

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

---

## Codebase Checks & Potential Testnet Deployment Issues

When running C-SWON on the testnet, be aware of the following potential codebase configurations that need override:

1. **Wandb Configuration Conflicts**: 
   The default setup in `cswon/utils/config.py` uses `--wandb.project_name` set to `template-miners` / `template-validators` under the `opentensor-dev` `--wandb.entity`. If you try to log here on testnet without access, the API call will bounce, and your neuron will crash.
   **Solution**: Either run with `--wandb.off` to disable logging entirely, or pass your own W&B project entity strings (`--wandb.entity your-org --wandb.project_name your-project`).

2. **Default netuid=1**:
   The default `netuid` argument across C-SWON is `1`. Netuid `1` on the testnet might already be claimed (or it might be an entirely different subnet). 
   **Solution**: Always pass `--netuid <netuid>` matching the one returned when your subnet was created.

3. **Environment and Secrets Management**:
   If your C-SWON application relies on local environmental keys (API endpoints, specific db credentials, OpenAI keys for generation, etc.), these must be available to the processes running `neurons/miner.py` and `neurons/validator.py`. Missing local configuration could cause exceptions when workflows trigger.

# Local Deployment Guide for C-SWON

This guide provides step-by-step instructions to run a local instance of Subtensor and deploy the C-SWON subnet for testing and development in a safe, isolated environment.

## 1. Prerequisites

Before you begin, ensure you have the following installed:
- **Docker**: Needed to run the local Subtensor instance easily.
- **Bittensor SDK and CLI**: Install the official `bittensor` Python package (`pip install bittensor`).

## 2. Run a Local Subtensor Instance (using Docker)

Using Docker is the recommended approach to run a local chain.

1. **Pull the Docker image**:
   ```bash
   docker pull ghcr.io/opentensor/subtensor-localnet:devnet-ready
   ```

2. **Run the container (Fast Blocks Mode)**:
   Fast block mode reduces block processing to 250ms, ideal for rapid testing.
   ```bash
   docker run --rm --name local_chain -p 9944:9944 -p 9945:9945 ghcr.io/opentensor/subtensor-localnet:devnet-ready
   ```
   *(Keep this terminal running. The local chain is accessible at `ws://127.0.0.1:9944`)*

3. **Verify the setup**:
   In a new terminal, check the subnets on your local chain:
   ```bash
   btcli subnet list --network ws://127.0.0.1:9944
   ```

## 3. Provision Wallets for Local Testing

You will need an owner wallet, a validator wallet, and a miner wallet.

1. **Create the owner wallet (coldkey only)**:
   ```bash
   btcli wallet new_coldkey --wallet.name owner --network ws://127.0.0.1:9944
   ```

2. **Create validator and miner wallets (coldkey + hotkey)**:
   ```bash
   btcli wallet new_coldkey --wallet.name vali --network ws://127.0.0.1:9944
   btcli wallet new_hotkey --wallet.name vali --wallet.hotkey default --network ws://127.0.0.1:9944

   btcli wallet new_coldkey --wallet.name miner --network ws://127.0.0.1:9944
   btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default --network ws://127.0.0.1:9944
   ```

3. **Fund the wallets**:
   Localnet wallets require test TAO. You can mint test TAO using the `btcli wallet faucet` command or by using the pre-funded default accounts in the localnet image (often `Alice` or `Bob`).
   ```bash
   btcli wallet faucet --wallet.name owner --network ws://127.0.0.1:9944
   btcli wallet faucet --wallet.name vali --network ws://127.0.0.1:9944
   ```

## 4. Create and Register the Subnet

1. **Create the subnet**:
   Use your owner wallet to create a new subnet on the local chain.
   ```bash
   btcli subnet create --network ws://127.0.0.1:9944 --wallet.name owner
   ```
   *Note the `netuid` returned in the output (e.g., typically `1` or `2` on a fresh chain).*

2. **Register the Validator and Miner**:
   Register the hotkeys on the newly created subnet (replace `<netuid>` with the actual netuid):
   ```bash
   btcli subnets register --network ws://127.0.0.1:9944 --netuid <netuid> --wallet.name vali --wallet.hotkey default
   btcli subnets register --network ws://127.0.0.1:9944 --netuid <netuid> --wallet.name miner --wallet.hotkey default
   ```

3. **Add Stake to the Validator**:
   ```bash
   btcli stake add --network ws://127.0.0.1:9944 --wallet.name vali --wallet.hotkey default
   ```

## 5. Run the C-SWON Validator and Miner

With the local chain running and wallets provisioned, you can now run the actual C-SWON code. Ensure your Python environment has all requirements installed (`pip install -r requirements.txt` and `pip install -e .`).

1. **Run the Miner**:
   ```bash
   python neurons/miner.py \
     --netuid <netuid> \
     --subtensor.network local \
     --subtensor.chain_endpoint ws://127.0.0.1:9944 \
     --wallet.name miner \
     --wallet.hotkey default \
     --wandb.off
   ```

2. **Run the Validator**:
   ```bash
   python neurons/validator.py \
     --netuid <netuid> \
     --subtensor.network local \
     --subtensor.chain_endpoint ws://127.0.0.1:9944 \
     --wallet.name vali \
     --wallet.hotkey default \
     --wandb.off
   ```

---

## Codebase Checks & Potential Local Deployment Issues

During a review of the C-SWON codebase, a few items were identified that you should be aware of when deploying locally:

1. **Wandb Configurations**: 
   The default arguments in `cswon/utils/config.py` point to `template-miners` / `template-validators` under the `opentensor-dev` entity. Attempting to log there without correct permissions will cause the script to crash. **Recommendation**: Either pass `--wandb.off` (as shown above) or supply your own valid `--wandb.project_name` and `--wandb.entity`.
   
2. **Default netuid**:
   The `netuid` defaults to `1` in `config.py`. Subnets added on local chains could take `netuid=2` if `1` is already taken by the apex subnet. **Recommendation**: Always explicitly pass `--netuid <netuid>` as returned by the `btcli subnet create` command.

3. **Dependency on external services/APIs**:
   Ensure any environment variables (`.env`) for local APIs or DBs are properly set up before launching the validator or miner, as missing endpoints might result in early crashes during the startup phases.

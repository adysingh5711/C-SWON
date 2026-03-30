# Running Subnet on Testnet

This guide describes how to create and run your Bittensor subnet on the **test network**. Creating a subnet is a major undertaking, so we recommend you first try [Running Subnet Locally](running_on_staging.md).

:::danger Alert: Security
- Do not expose your private keys.
- Only use your testnet wallet for testing.
- Do not reuse the password of your mainnet wallet.
- Make sure your incentive mechanism is resistant to abuse.
:::

## Considerations

### Research existing subnets
Prospective subnet creators should familiarize themselves with the space of existing subnets.
- Real-time subnet info on [tao.app](https://www.tao.app/explorer)
- LearnBittensor's [Subnet listings](https://learnbittensor.org/subnets)

### Burn cost
The required amount of TAO to be recycled when creating a new subnet is called the "burn cost." This cost is dynamic: it reflects current registration demand, lowers gradually over time, and doubles every time a new subnet is created.

### Validating in your own subnet
You must meet the same [requirements for validation](../validators#requirements-for-validation) as other validators in order to set weights in your own subnet.
One option for subnet owners is to ask one of the root network (subnet 0) validators to parent your validator hotkey as a childkey of theirs. This will lend their stake to your validator, and can help you ensure that your validator maintains a sufficient stake to effectively participate in consensus as well as resist deregistration.

### Subnet creation rate limits
Subnet creations are limited to **one subnet creation per 28800 blocks** (approximately one every four days). Picking the right time to create your subnet requires planning.

## Prerequisites

1. **Python 3.9–3.12** installed on your system.
2. **Install BTCLI**: Install the [most recent version of BTCLI](https://github.com/opentensor/btcli):
   ```bash
   pip install bittensor-cli
   ```
   Or via Homebrew:
   ```bash
   brew install btcli
   ```
   Verify with `btcli --version`.
3. **Install Repository**:
   ```bash
   git clone https://github.com/adysingh5711/C-SWON.git
   cd C-SWON
   python -m pip install -e .
   ```
4. **Create Wallets**: Create wallets for the subnet owner, validator, and miner.
   ```bash
   btcli wallet create --wallet.name owner --wallet.hotkey default
   btcli wallet create --wallet.name miner --wallet.hotkey default
   btcli wallet create --wallet.name validator --wallet.hotkey default
   ```
5. **Get Testnet TAO**: Your owner wallet must have sufficient testnet TAO (check burn cost below). You can inquire in the [Bittensor Discord](https://discord.com/channels/799672011265015819/1107738550373454028/threads/1331693251589312553) to obtain TAO on the test network.

## 1. Check the burn cost

Check the current burn cost to create a subnet on the test network:

```shell
btcli subnet burn-cost --network test
```

Expected output:
```bash
>> Subnet burn cost: τ100.000000000
```

## 2. Create the subnet

Create your new subnet on the testchain using the test TAO. This will give you owner permissions.

```bash
btcli subnet create --network test
```

Follow the prompts:
```bash
>> Enter wallet name (default): owner   # Enter your owner wallet name
>> Enter password to unlock key:        # Enter your wallet password.
>> Register subnet? [y/n]: <y/n>        # Select yes (y)
>> ⠇ 📡 Registering subnet...
✅ Registered subnetwork with netuid: 1 # Your subnet netuid will show here, save this for later.
```

## 3. (Optional) Configure or wait
Newly created subnets are inactive by default and do not begin emitting until they have been started. This allows you to configure hyperparameters, register validators, and onboard miners.

## 4. Start the subnet

Use the following command to start the subnet and begin emission:

```bash
btcli subnet start --netuid <your-netuid> --network test
```

## 5. Register keys

Register your miner and validator keys to the subnet to secure your initial slots.

**Register Miner:**
```bash
btcli subnet register --netuid <your-netuid> --network test --wallet.name miner --wallet.hotkey default
```

**Register Validator:**
```bash
btcli subnet register --netuid <your-netuid> --network test --wallet.name validator --wallet.hotkey default
```

## 6. Verify registration

Check the status of your keys using the wallet overview:

```bash
btcli wallet overview --wallet.name validator --network test
btcli wallet overview --wallet.name miner --network test
```

In the output, look for the `UID` assigned to each key. The `ACTIVE` column should show `True`.

## 7. Run miner and validator

**Run Miner:**
```bash
python neurons/miner.py --netuid <your-netuid> --subtensor.network test --wallet.name miner --wallet.hotkey default --logging.debug
```

**Run Validator:**
```bash
python neurons/validator.py --netuid <your-netuid> --subtensor.network test --wallet.name validator --wallet.hotkey default --logging.debug
```

## 8. Get emissions flowing (Root Registration)

To receive emissions, you must register to the root network and set your weights:

1. **Register to Root:**
   ```bash
   btcli root register --network test --wallet.name owner
   ```
2. **Set Weights:**
   ```bash
   btcli root weights --network test --wallet.name owner --netuid <your-netuid> --weights 1
   ```

## 9. Stopping your nodes

To stop your nodes, press **CTRL + C** in the terminals where they are running.

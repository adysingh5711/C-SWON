# Execution Support Pool — Operator Runbook
# Addresses issue 3.8 (readme §4.6)

# Execution Support Pool — Operator Runbook

**Purpose**: The Execution Support Pool provides supplemental Alpha token payouts to validators that
exceed the `EXEC_SUPPORT_N_MIN` (30 tasks/tempo) threshold, subsidising execution costs during the
period before organic user flow generates sufficient revenue (readme §4.6).

---

## Who manages this?

The pool is owner-managed. The subnet owner wallet holds the Alpha token reserve created at launch.
There is no on-chain escrow; payouts are discretionary transfers triggered by this runbook.

---

## Eligibility criteria

A validator qualifies for the support payout in a given tempo if:
1. `tasks_evaluated >= EXEC_SUPPORT_N_MIN` (30) in that tempo (logged by `forward.py`)
2. The validator's `axon.info.description` contains `cswon-bench:v1`
3. The validator is **not** the subnet owner

---

## Step 1 — Collect validator execution logs

Run this on each validator node (or aggregate via a log collector):

```bash
grep "EXEC_SUPPORT_ELIGIBLE: True" /var/log/cswon/validator.log | \
  grep "TEMPO_BOUNDARY" | \
  awk '{print $3, $4}' > /tmp/eligible_validators.txt
```

Or query the monitoring endpoint:

```bash
curl http://<validator-ip>:9090/audit-flags | python3 -m json.tool
```

---

## Step 2 — Calculate payout amounts

Payout formula (example — adjust based on pool balance and active validators):

```
payout_per_validator = pool_balance_alpha × 0.02   # 2% of pool per tempo max
```

Check pool balance:

```bash
btcli wallet balance --wallet.name owner --subtensor.network finney
```

---

## Step 3 — Send Alpha transfers

For each eligible validator hotkey, send from the owner wallet:

```bash
btcli wallet transfer \
  --wallet.name owner \
  --wallet.hotkey default \
  --dest <validator_hotkey_ss58> \
  --amount <payout_alpha> \
  --subtensor.network finney
```

**Confirm before sending**: verify the validator hotkey from metagraph:

```bash
btcli subnet metagraph --netuid <netuid> --subtensor.network finney | grep <validator_hotkey>
```

---

## Step 4 — Record payments

Keep a CSV ledger at `docs/exec_support_payments.csv`:

```csv
tempo,validator_hotkey,tasks_evaluated,payout_alpha,tx_hash,timestamp
```

---

## Pool replenishment

If pool balance drops below 10,000 Alpha, transfer from the owner cold wallet:

```bash
btcli wallet transfer \
  --wallet.name owner \
  --wallet.hotkey owner_hotkey \
  --dest <owner_hotkey_ss58> \
  --amount <topup_amount> \
  --subtensor.network finney
```

---

## Contact

For governance decisions about payout rates, file an issue on the C-SWON GitHub repository.

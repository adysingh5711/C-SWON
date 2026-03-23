# C-SWON: Cross-Subnet Workflow Orchestration Network

**Bittensor Subnet Proposal**
*"Zapier for Subnets" - The Intelligence Layer for Multi-Subnet Composition*

> **GitHub:** https://github.com/adysingh5711/C-SWON · **Whitepaper:** Upcoming

---

## 1. Introduction: The Vision for a Composable AI Operating System

Bittensor hosts over 100 specialized subnets, covering text generation, code review, inference, agents, data processing, and fact-checking, yet there is no native way to compose them into reliable, end-to-end workflows. Developers today manually wire calls to 5–10 subnets per application, guess at optimal routing, and rebuild orchestration logic from scratch every time. This is the core bottleneck preventing Bittensor from evolving from a collection of isolated AI services into a true composable AI operating system.

**C-SWON (Cross-Subnet Workflow Orchestration Network)** directly addresses this gap. It is a Bittensor subnet where **the mined commodity is optimal workflow policy**-miners propose multi-subnet execution plans (DAGs), validators score them on task success, cost, and latency, and the network continuously learns the best orchestration strategies through competitive pressure.

The result is an intelligent routing layer that turns any complex AI task into a single, optimized workflow. Just as Zapier abstracted away manual automation for Web2, C-SWON abstracts away manual orchestration for Bittensor's AI ecosystem, making optimal multi-subnet composition first-class intelligence on the network.

---

## 2. Incentive & Mechanism Design

The incentive mechanism of C-SWON is engineered to reward genuine orchestration intelligence - not raw output quality, but the quality of the *coordination strategy* used to produce it.

### 2.1 Emission Structure (dTAO Standard)

C-SWON operates under Bittensor's Dynamic TAO (dTAO) model. All participant rewards are paid in **CSWON Alpha tokens**, not TAO directly. TAO is injected into the subnet's AMM liquidity pool each block, and Alpha is distributed to participants via Yuma Consensus at the end of each **tempo** (default: 360 blocks / ~72 minutes).

**Alpha emission split per tempo:**

```mermaid
flowchart TD
    E(["Total Alpha Emissions per Tempo: Δα"]):::emission

    E -->|18%| O["Subnet Owner<br/>Protocol dev + treasury"]:::owner
    E -->|41%| M["Miners<br/>Workflow policy scores via Yuma"]:::miner
    E -->|41%| VS["Validators + Stakers<br/>Scoring quality + stake delegation"]:::validator

    M --> RF["Miner Reward Formula<br/>R_i = (Δα × 0.41) × (W_i / Σ_j W_j)"]:::formula
    RF --> WF["W_i = Yuma stake-weighted score<br/>S = 0.50·success + 0.25·cost + 0.15·latency + 0.10·reliability"]:::formula

    classDef emission fill:#1e3a5f,stroke:#3b82f6,color:#fff
    classDef owner   fill:#4c1d95,stroke:#a78bfa,color:#fff
    classDef miner   fill:#b45309,stroke:#fcd34d,color:#fff
    classDef validator fill:#1d4ed8,stroke:#93c5fd,color:#fff
    classDef formula fill:#065f46,stroke:#6ee7b7,color:#fff
```

| Variable | Unit        | Definition                                      |
| -------- | ----------- | ----------------------------------------------- |
| Δα     | Alpha/tempo | Total Alpha allocated to participants per tempo |
| R_i      | Alpha       | Reward to miner i per tempo                     |
| W_i      | float [0,1] | Yuma stake-weighted composite score for miner i |
| W_j      | float [0,1] | Score for miner j — normalisation denominator  |

**TAO liquidity:** TAO is injected into the C-SWON AMM pool at each block proportionally to Alpha injection, stabilising the Alpha price. Stakers who hold TAO on the root subnet receive a portion of validator dividends converted to TAO via this AMM swap, gradually deepening the liquidity pool through real usage.

**Halving:** Alpha participant rewards follow the Alpha supply schedule. TAO halving events affect TAO injection into the AMM pool, but Alpha distribution per tempo is governed by net TAO inflows and dTAO allocation — not by the TAO halving directly.

---

### 2.2 Scoring Formula (v1.0.0)

> **Scoring version:** All validators must run `SCORING_VERSION = "1.0.0"`. </br>
> [See Section 4.5 for the upgrade protocol]. </br>

Every workflow a miner submits is executed by validators. A composite score
**S ∈ [0, 1]** is computed across four dimensions:

```
S = 0.50 × S_success + 0.25 × S_cost + 0.15 × S_latency + 0.10 × S_reliability
```

**Sub-dimension formulas:**

```
S_success   = output_quality_score × completion_ratio
              where completion_ratio = steps_completed / total_steps_in_dag

S_cost      = max(0, 1 − actual_tao / max_budget_tao)
              only scored when S_success > 0.7; else S_cost = 0

S_latency   = max(0, 1 − actual_seconds / max_latency_seconds)
              only scored when S_success > 0.7; else S_latency = 0

S_reliability = min(1.0, max(0, 1 − (unplanned_retries × 0.10
                                    + timeouts          × 0.20
                                    + hard_failures     × 0.50)))
              applied regardless of success gate

where:
  unplanned_retries    = max(0, actual_retries − declared_retry_budget)
                         — must be a non-negative integer; clamp to 0 if counting
                           produces a negative value (guards against off-by-one bugs)
  declared_retry_budget = sum of retry_count values in error_handling (0 if absent)
  timeouts             = step execution events that exceeded declared timeout_seconds
  hard_failures        = steps that terminated after exhausting the declared retry budget
  min(1.0, ...) guard  = prevents S > 1.0 if a counting bug produces negative penalties
```

**Reliability scoring rationale (fix: declared retries are not penalised):**
A miner who writes `"retry_count": 2` in `error_handling` is declaring defensive intent. Charging `retries × 0.10` per declared retry previously penalised correct
error handling more than a hard failure (0.10×2 + 0.50 = 0.70 vs 0.50 for no retries). The corrected formula only penalises *unplanned* retries — attempts beyond the declared budget — and failures that exhaust that budget. Retries that stay within budget and ultimately succeed incur **zero** reliability penalty.

**Partial DAG completion:** If a 4-step workflow completes 3 steps before a hard failure, `completion_ratio = 0.75`. This prevents miners from submitting single-step workflows for multi-step tasks to inflate their success score.

**Success-first gating** enforces the correct priority: a workflow that fails the task cannot be considered "good" regardless of how cheap or fast it is. Reliability is always scored because error-handling quality is independent of task success.

**Score aggregation (fixed rolling window):** Scores are aggregated over a **rolling 100-task window with equal weight** per task. There is no exponential decay applied — a fixed equal-weight window is simpler to audit, harder to time-exploit, and produces the same recency effect for all miners without introducing a tunable λ parameter that could be gamed. The window is capped at **15% max weight per miner** before submission.

---

### 2.3 Output Quality Scoring by Task Type (No LLM Judge in v1)

To avoid circular dependencies — C-SWON calling a model subnet to judge C-SWON workflows — all quality scoring in v1 uses **deterministic, reference-based methods**.

| Task Type                | `output_quality_score` Method                                        | Ground Truth Source                        |
| ------------------------ | ---------------------------------------------------------------------- | ------------------------------------------ |
| **Code**           | Automated test pass rate + PEP8 linting score                          | Unit tests embedded in benchmark task JSON |
| **RAG**            | ROUGE-L F1 against reference answer                                    | Reference answers in benchmark dataset     |
| **Agent**          | Binary goal checklist: pass/fail per criterion; score = passed / total | Goal checklist in benchmark task JSON      |
| **Data transform** | Schema validation + exact-match against expected output                | Expected output in benchmark task JSON     |

**Why ROUGE-L for RAG (not an LLM judge):** ROUGE-L measures longest common subsequence overlap against a known reference answer. It is fast, deterministic, and reproducible — every validator produces the identical score for the same output. LLM judges require calling a model subnet (creating a recursive dependency) and produce non-deterministic results, making cross-validator consensus impossible in v1.

**Acknowledged limitation:** ROUGE-L penalises valid paraphrasing. This is acceptable for testnet MVP benchmarks where reference answers are tightly scoped. A semantic scoring upgrade (local BERTScore or embedding-based similarity, run by validators without external calls) is planned for v2.

---

### 2.4 Incentive Alignment and Penalties (No On-Chain Slashing)

C-SWON does **not** introduce on-chain slashing — Bittensor does not support automatic stake slashing at the protocol level. Instead, dishonest or low-quality validators are penalised through economic and governance mechanisms:

- **Yuma Consensus bonds:** validators whose scores deviate from stake-weighted consensus earn progressively less of the 41% validator emissions over time.
- **Delegation flow:** delegators move stake away from misbehaving validators, reducing their future emissions.
- **Governance control:** the subnet owner can adjust validator limits and prune permits for consistently misaligned validators under Bittensor's permit rules.

> **Explicit note:** There is no automatic cryptographic stake slashing in Bittensor today. Any future reference to "slashing" in this project means the above economic and governance actions only.

---

### 2.5 Anti-Gaming Mechanisms

- **Synthetic Ground Truth Tasks (15–20%):** Validators inject tasks with known optimal
  workflows. Miners cannot distinguish these from real tasks.
- **VRF-keyed per-validator task schedule (pre-caching and collusion resistant):**
  Each validator derives its task assignment from its own hotkey and the current block, making the per-validator stream pseudorandom but fully deterministic:

  ```python
  import hashlib
  seed       = f"{validator_hotkey}:{current_block}".encode()
  h          = hashlib.sha256(seed).digest()
  task_index = int.from_bytes(h, 'big') % len(benchmark_tasks)
  task       = benchmark_tasks[task_index]
  ```

  Different validators query different tasks at the same block height. Miners cannot pre-compute a per-validator cache without knowing every validator's hotkey and the current block simultaneously. Cross-validator score comparison uses distributional statistics over the rolling window, not identical-task point comparisons. Yuma's bond mechanism automatically reduces rewards for persistent outlier validators.
- **Scoring version enforcement:** Validators encode `SCORING_VERSION` as an integer in `__spec_version__` and as a human-readable string in `axon.info.description` (e.g. `"cswon-scoring:1.0.0"`). `axon.info.version` is an SDK-managed integer and must not be written manually. Mismatches are detected by reading `metagraph.axons[uid].version` (int) and `.description` (string) from the live metagraph. See Section 4.5 for the full upgrade protocol.
- **Dynamic Benchmark Rotation:** Tasks are deprecated when >70% of miners score above 0.90 consistently for 3 consecutive tempos, triggering mandatory dataset rotation.
- **Execution Sandboxing:** Validators execute all workflows in isolated Docker containers, tracking actual TAO costs, latency, retries, and step completions.
- **Temporal Consistency Checks:** Sudden unexplained performance jumps trigger a manual audit flag in the validator dashboard.
- **Completion Ratio Enforcement:** Submitting a single-step workflow for a multi-step task always results in a proportionally penalised `S_success`.

---

## 3. Miner Design

### 3.1 Registration and Stake Requirements

**Registration vs stake — these are different things:**

- **Registration** burns TAO to obtain a UID. This is separate from staking.
- **Staking** is adding TAO to the neuron's hotkey to influence Yuma weight.
- A miner can register with minimal burn and add stake separately.

**Active stake requirement:**

| Requirement        | Minimum  | Recommended |
| ------------------ | -------- | ----------- |
| TAO stake (active) | 1 TAO    | 10 TAO      |
| CPU                | 4 cores  | 8 cores     |
| RAM                | 16 GB    | 32 GB       |
| Network            | 100 Mbps | 1 Gbps      |
| Uptime target      | 90%      | 99%         |

Miners must maintain ≥1 TAO active stake on their hotkey after the immunity period expires. Miners below this threshold become candidates for deregistration under standard Yuma pruning when all UID slots are full. They cannot be deregistered during their `immunity_period` regardless of stake.

**Immunity period:** New miners receive a default `immunity_period` of 5,000 blocks (~16.7 hours). During this window they cannot be deregistered. See Section 4.4 for how validators handle scoring during immunity.

---

### 3.2 Data Model and `DataRef` Semantics

All workflow DAG nodes follow a strict I/O contract, executed by the validator runtime:

**Node output schema:**

```json
{
  "text": "primary textual output (max 16 KB)",
  "artifacts": {
    "code":     "optional code string (max 64 KB)",
    "metadata": {}
  }
}
```

**DataRef syntax — referencing earlier outputs in node params:**

```
"${<step_id>.output.<field_path>}"
```

Examples:

- `"${step_1.output.text}"`
- `"${step_2.output.artifacts.code}"`

**Execution contract (validator executor is the sole resolver):**

1. Derive the execution plan by topological sort of `edges`. Nodes with **no dependency on each other** (no shared path in the DAG) are placed in the same *execution tier* and run **concurrently**.
2. After each node completes (success or failure), store its output in `context[node_id]`.
3. Before executing node `K`, resolve only the `"${...}"` patterns that reference *completed* upstream nodes. If a referenced node is still executing, wait for it.
4. **Before dispatching** each node to its partner subnet, the executor checks the cumulative TAO cost so far:

   ```python
   budget_ceiling = min(constraints["max_budget_tao"],
                        1.5 * workflow_plan["total_estimated_cost"])
   if cumulative_tao >= budget_ceiling:
       # Mark all remaining unexecuted nodes as "budget_abort"
       for node in remaining_nodes:
           context[node.id] = {"status": "budget_abort", "output": None}
       break   # exit execution loop; S_cost forced to 0 at scoring time
   ```

   This check runs **before** each node dispatch, so the validator is never billed for a node that exceeds the ceiling. Aborted nodes are counted in `total_steps_in_dag` but not in `steps_completed`, reducing `completion_ratio`. `S_cost` is forced to 0 for any workflow that triggered a budget abort.
5. If a referenced field does not exist, exceeds size limits, or the upstream node **that this specific DataRef points to** failed, the current step is marked a hard failure and contributes to `S_reliability`. A parallel sibling's failure does NOT propagate to unrelated nodes.

**Parallel DAG rules (fix: undefined behaviour removed):**

| Metric                      | Sequential DAG                       | Parallel DAG                                                             |
| --------------------------- | ------------------------------------ | ------------------------------------------------------------------------ |
| `completion_ratio`        | `steps_completed / total_nodes`    | `steps_completed / total_nodes` (same; counts nodes, not paths)        |
| `S_latency`               | wall-clock end-to-end time           | wall-clock end-to-end time (correct; parallel branches compress it)      |
| `S_cost`                  | sum of all step costs                | sum of all step costs (parallel steps both charged)                      |
| DataRef failure propagation | upstream failure → downstream fails | only if the specific referenced node failed; unrelated branches continue |

**Example:** A→C and B→C (A and B independent). A completes, B fails. C only needs `${A.output.text}`. C **proceeds**; B's failure reduces `completion_ratio` by 1/3 but does not block C. If C needed `${B.output.text}`, C hard-fails.

Miners must not implement their own DataRef resolvers. All resolution is performed by the validator executor as written above.

---

### 3.2b WorkflowSynapse Protocol Definition

`WorkflowSynapse` is the Bittensor synapse that carries task packages from validators to miners and workflow plans back. It must be defined in `cswon/protocol.py` before any miner or validator code can interoperate.

```python
# cswon/protocol.py

import bittensor as bt
from typing import Optional

class WorkflowSynapse(bt.Synapse):
    """
    Validator → Miner: carries the task package.
    Miner → Validator: carries the workflow plan (populated by miner).
    """

    # ── Validator-populated fields (sent to miner) ──────────────────
    task_id:          str                    = ""
    task_type:        str                    = ""
    description:      str                    = ""
    quality_criteria: dict                   = {}
    constraints:      dict                   = {}   # max_budget_tao, max_latency_seconds, allowed_subnets
    available_tools:  dict                   = {}   # per-subnet cost/latency hints
    send_block:       int                    = 0    # stamped by query_loop before dispatch

    # ── Miner-populated fields (returned to validator) ───────────────
    miner_uid:              Optional[int]    = None
    scoring_version:        Optional[str]    = None
    workflow_plan:          Optional[dict]   = None  # nodes, edges, error_handling
    total_estimated_cost:   Optional[float]  = None
    total_estimated_latency:Optional[float]  = None
    confidence:             Optional[float]  = None
    reasoning:              Optional[str]    = None

    def deserialize(self) -> "WorkflowSynapse":
        return self
```

**Validator reads** `response.miner_uid`, `response.workflow_plan`, etc. </br>
**Validator writes** `task_id`, `task_type`, `description`, `constraints`, `available_tools`, `send_block` before calling `dendrite.forward()`. </br>
The miner populates all `Optional` fields in its `forward()` handler and returns the synapse. Any `Optional` field left as `None` by the miner is treated as an invalid response and discarded.

---

### 3.3 Miner Tasks

**Input (Task Package from Validator):**

```json
{
  "task_id": "uuid-v4",
  "task_type": "code_generation_pipeline",
  "description": "Generate a Python FastAPI endpoint for user authentication with JWT tokens, including unit tests",
  "quality_criteria": {
    "functional_correctness": true,
    "test_coverage": ">80%",
    "code_style": "PEP8"
  },
  "constraints": {
    "max_budget_tao": 0.05,
    "max_latency_seconds": 10.0,
    "allowed_subnets": ["SN1", "SN62", "SN64", "SN45", "SN70"]
  },
  "available_tools": {
    "SN1":  { "type": "text_generation", "avg_cost": 0.001,  "avg_latency": 0.5 },
    "SN62": { "type": "code_review",     "avg_cost": 0.003,  "avg_latency": 1.2 },
    "SN64": { "type": "inference",       "avg_cost": 0.0005, "avg_latency": 0.3 },
    "SN45": { "type": "code_testing",    "avg_cost": 0.002,  "avg_latency": 2.0 },
    "SN70": { "type": "fact_checking",   "avg_cost": 0.0015, "avg_latency": 0.8 }
  },
  "routing_policy": {
    "default": {
      "miner_selection": "top_k_stake_weighted",
      "top_k": 3,
      "aggregation": "majority_vote"
    },
    "SN1":  { "miner_selection": "top_k_stake_weighted", "top_k": 3, "aggregation": "median_logit" },
    "SN62": { "miner_selection": "top_k_stake_weighted", "top_k": 3, "aggregation": "majority_vote" },
    "SN45": { "miner_selection": "top_k_stake_weighted", "top_k": 3, "aggregation": "majority_vote" }
  }
}
```

**Output (Workflow Plan from Miner):**

```json
{
  "task_id":    "uuid-v4",
  "miner_uid":  42,
  "scoring_version": "1.0.0",
  "workflow_plan": {
    "nodes": [
      {
        "id": "step_1", "subnet": "SN1", "action": "generate_code",
        "params": { "prompt": "Generate FastAPI endpoint with JWT auth...", "max_tokens": 2000 },
        "estimated_cost": 0.0012, "estimated_latency": 0.6
      },
      {
        "id": "step_2", "subnet": "SN62", "action": "review_code",
        "params": {
          "code_input":      "${step_1.output.text}",
          "review_criteria": ["security", "style"]
        },
        "estimated_cost": 0.0035, "estimated_latency": 1.5
      },
      {
        "id": "step_3", "subnet": "SN45", "action": "generate_tests",
        "params": {
          "code_input":      "${step_2.output.artifacts.code}",
          "coverage_target": 0.85
        },
        "estimated_cost": 0.0025, "estimated_latency": 2.2
      }
    ],
    "edges": [
      { "from": "step_1", "to": "step_2" },
      { "from": "step_2", "to": "step_3" }
    ],
    "error_handling": {
      "step_1": { "retry_count": 2 },
      "step_2": { "retry_count": 1, "timeout_seconds": 3.0 }
    }
  },
  "total_estimated_cost":    0.0072,
  "total_estimated_latency": 4.3,
  "confidence": 0.88,
  "reasoning":  "Sequential pipeline: generate → review → test."
}
```

> **`routing_policy` field (fix: partner subnet non-determinism):**
> Validators use the `routing_policy` field embedded in every benchmark task JSON to
> select which miners on a partner subnet to call and how to aggregate their outputs.
> All validators reading the same benchmark task JSON will route identically, making
> cross-validator score comparison valid. The `aggregation` values are:
>
> - `"median_logit"` — take the median of numeric outputs (e.g. token logits)
> - `"majority_vote"` — take the modal text output across the top-k miners
>
> Validators must not override this policy with their own routing logic.

### 3.4 Performance Dimensions

| Dimension       | Weight | Formula                                                                                                     |
| --------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| Task Success    | 50%    | `output_quality × completion_ratio`                                                                      |
| Cost Efficiency | 25%    | `max(0, 1 − actual/budget)` — gated at S_success > 0.7                                                  |
| Latency         | 15%    | `max(0, 1 − actual_s/max_s)` — gated at S_success > 0.7                                                 |
| Reliability     | 10%    | `min(1.0, max(0, 1 − unplanned_retries×0.1 − timeouts×0.2 − failures×0.5))` — planned retries free |

Tracked but not yet weighted (signals for v2):

- **Creativity:** Novel subnet combinations not seen in baseline workflows
- **Robustness:** Score consistency across semantically similar tasks
- **Explainability:** Quality and coherence of the `reasoning` field

### 3.5 Early Participation Programme (Protocol-Compliant)

The "1.5× emission multiplier" is not achievable at the Yuma protocol level. C-SWON incentivises early miners through protocol-safe alternatives instead:

| Incentive                                                                    | Mechanism                                                                                                       | Protocol-Safe? |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------- |
| **3× query frequency** for first 50 registered miners, first 6 months | Validators triple selection probability for early miners in the task lottery (`validator/miner_selection.py`) | ✅             |
| **Faster score window fill**                                           | More queries → rolling window fills faster → emissions begin sooner                                           | ✅             |
| **GPU credits ($500–$1,000)**                                         | Off-chain grants from owner treasury                                                                            | ✅             |
| **$50K grants pool**                                                   | Off-chain, milestone-gated                                                                                      | ✅             |

For validators (first 10): the owner manually stakes up to 1,000 TAO equivalent in Alpha on behalf of qualifying validators. This is a manual on-chain action per transfer, publicly auditable, and not a protocol feature.

### 3.6 Miner Development Lifecycle

1. **Profile subnets:** Gather historical cost, latency, and reliability data for available subnets via the metagraph. Refresh every 100 blocks.
2. **Build workflow templates:** Develop reusable DAG patterns for code pipelines, RAG queries, agent tasks, and data transforms.
3. **Optimise for constraints:** Implement cost and latency passes — substitute cheaper subnets when over budget, parallelise independent steps when under latency budget.
4. **Deploy and monitor:** Serve the planner via a Bittensor axon. Track scores on the public dashboard and iterate based on benchmark performance.

---

## 4. Validator Design

Validators define challenging tasks, execute submitted workflow plans in a sandboxed environment, measure real outcomes, and translate those measurements into honest on-chain weights.

### 4.1 Weight Submission Cadence (Tempo-Aligned)

Validators submit weights exactly **once per tempo**:

```python
# validator/weight_setter.py

TEMPO              = subtensor.get_subnet_hyperparameters(netuid).tempo          # default 360
WEIGHTS_RATE_LIMIT = subtensor.get_subnet_hyperparameters(netuid).weights_rate_limit

if (current_block - last_set_block >= TEMPO
        and current_block - last_set_block >= WEIGHTS_RATE_LIMIT):
    subtensor.set_weights(
        netuid=netuid,
        uids=miner_uids,
        weights=normalised_weights,
        wait_for_inclusion=False,  # True blocks the event loop for up to 12 s; use False + check return value
    )
    last_set_block = current_block
```

This ensures:

- Weights are always submitted within the same Yuma epoch they were earned.
- `CommittingWeightsTooFast` is never triggered (guarded by the dual-condition check above).
- No reward signal drift from skipped epochs.

> **Testnet note:** C-SWON registers with `tempo = 360` blocks in
> `SubnetHyperparameters`. Do not change this without also updating
> `EXEC_SUPPORT_N_MIN` in `validator/config.py`.

**Async query loop (fix: timeout must be < 1 block):**

A 30-second blocking wait per query means the validator misses 2+ block heights
and attributes stale responses to the wrong block, breaking per-validator VRF task
selection. The query loop must be fully asynchronous:

```python
# validator/query_loop.py

import asyncio
import bittensor as bt

QUERY_TIMEOUT_S = 9   # hard ceiling: must be < 12 s (1 block)

async def query_miners(
    dendrite: bt.dendrite,
    axons: list[bt.AxonInfo],
    synapse: WorkflowSynapse,
    send_block: int,
) -> list[WorkflowSynapse]:
    responses = await dendrite.forward(
        axons   = axons,
        synapse = synapse,
        timeout = QUERY_TIMEOUT_S,
    )
    # Attribute ALL responses to send_block, not receipt block
    for r in responses:
        r.send_block = send_block
    return responses
```

`send_block` is stamped onto each response at dispatch time. The score aggregation
pipeline reads `response.send_block`, not `current_block`, so a reply arriving 11 s
after send is still scored against the correct task regardless of how many blocks have
elapsed since the query was sent.

---

### 4.2 Validator Hardware Requirements

Validators run sandboxed Docker containers, automated test runners, and ROUGE-L
scoring — they need substantially more resources than miners.

| Requirement   | Minimum | Recommended |
| ------------- | ------- | ----------- |
| CPU           | 8 cores | 16 cores    |
| RAM           | 32 GB   | 64 GB       |
| SSD storage   | 500 GB  | 1 TB NVMe   |
| Network       | 1 Gbps  | 10 Gbps     |
| Docker        | 24.x+   | 26.x+       |
| Python        | 3.10+   | 3.11+       |
| Uptime target | 95%     | 99.5%       |

Validators running below minimum spec will be bottlenecked during sandboxed execution, fail to meet `N_min`, and lose execution support payouts — functioning as natural self-exclusion.

---

### 4.3 Subnet Call Authentication

All calls to partner subnets are **off-chain HTTP** — C-SWON makes no claim of on-chain receipts, as Bittensor's Subtensor records no trace of inter-subnet calls.

| Stage             | Authentication Model                                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Testnet           | Mock execution (`CSWON_MOCK_EXEC=true`). No real calls, no TAO burned.                                                                    |
| Mainnet bootstrap | Validator registers a C-SWON dedicated hotkey on each partner subnet. Calls at standard rates, subsidised by the Execution Support Pool.    |
| Mainnet at scale  | Negotiated API-tier access with high-traffic partner subnets. Revenue-share (5% of gateway fees → partner subnet) replaces per-call costs. |

**Security model for MVP:** Off-chain execution logs + VRF-keyed per-validator task
schedule (validators test different tasks per block; collusion requires knowing all
validator hotkeys AND block heights in advance) + Yuma's stake-weighted bond clipping
for outlier detection. No on-chain receipts exist today; they are a v4 R&D item.

---

### 4.4 Immunity Period Scoring (Warm-Up Scale)

New miners have a default `immunity_period` of 5,000 blocks (~16.7 hours). Validators apply a warm-up scale to prevent both zero-emission periods and premature reward pool distortion:

```python
# validator/scoring.py

WARMUP_TASK_THRESHOLD = 20   # set in validator/config.py

def get_miner_weight(
    miner_uid:  int,
    tasks_seen: int,
    raw_score:  float,
    subtensor:  "bt.subtensor",
    netuid:     int,
    current_block: int,
) -> float:
    # immunity_period must be fetched from chain — it is NOT available as a bare variable
    immunity_period  = subtensor.get_subnet_hyperparameters(netuid).immunity_period
    # registration block is in neuron.block, not metagraph.block_at_registration
    reg_block        = subtensor.neuron_for_uid(uid=miner_uid, netuid=netuid).block
    blocks_since_reg = current_block - reg_block
    is_immune        = blocks_since_reg < immunity_period

    if is_immune:
        warmup_scale = min(1.0, tasks_seen / WARMUP_TASK_THRESHOLD)
        return raw_score * warmup_scale
    return raw_score
```

Once a miner has seen 20 evaluated tasks, their weight influence matches a fully-warmed miner with the same score. The 3× query frequency for early miners (Section 3.5) means most new miners reach this threshold within 1–2 tempos.

---

### 4.5 Scoring Formula Version Control and Upgrade Protocol

All validators must run the **same scoring version** to produce consistent weights. A mismatch creates divergent weight vectors that Yuma interprets as honest disagreement, distorting rewards during any upgrade transition.

```python
# validator/scoring.py

SCORING_VERSION = "1.0.0"   # bumped only via governance vote
```

**Version signal (fix: correct Subtensor field):**
`axon.info.version` in Bittensor's `NeuronInfo` struct is an **integer** populated automatically from `__spec_version__` (e.g. `60400` for v6.4.0). Writing a string like `"1.0.0"` into this field will be silently cast or rejected by the SDK.

Instead, `SCORING_VERSION` is stored as an integer in `__spec_version__` using a decimal encoding, and the validator exposes the full semantic string in `axon.info.description`:

```python
# validator/config.py
SCORING_VERSION     = "1.0.0"
# Encode as integer: major*10000 + minor*100 + patch
__spec_version__    = 10000        # "1.0.0"  →  1*10000 + 0*100 + 0
```

```python
# validator/base.py  (passed to bt.axon())
axon = bt.axon(
    wallet=wallet,
    config=config,
    port=port,
    external_ip=bt.utils.networking.get_external_ip(),
    info=bt.AxonInfo(
        version     = __spec_version__,        # int, SDK-compatible
        description = f"cswon-scoring:{SCORING_VERSION}",  # human-readable
    ),
)
```

Any validator on a different `__spec_version__` is detectable by parsing `metagraph.axons[uid].version` (integer) and `metagraph.axons[uid].description` (string). Both fields are available in the live metagraph.

**Upgrade protocol (requires ≥67% validator stake-weighted consensus):**

1. A new version PR is merged to the C-SWON repo with at least 3 validator sign-offs.
2. The owner announces an upgrade block height (minimum 2 tempos notice).
3. All validators upgrade before the announced block.
4. At the upgrade block, `SCORING_VERSION` is bumped in `validator/config.py`.
5. Validators still on the old version after the upgrade block are flagged as outliers by Yuma's bond mechanism and earn progressively less until they upgrade.

> There is no forced upgrade mechanism in Bittensor — this is a social coordination protocol enforced through economic pressure, not cryptographic enforcement.

---

### 4.6 Execution Support Pool (Owner-Managed)

Validators may incur TAO costs from sandboxed calls to partner subnets. C-SWON manages this with an owner-managed policy (not a protocol escrow):

- The owner publicly commits to allocate ~5% of their 18% Alpha per tempo to an **Execution Support Pool**.
- **Eligibility threshold (`N_min`):** validators must complete ≥ **30 benchmark tasks per tempo** (≈ 1 per block at 360-block tempo) to qualify. Set in `validator/config.py:EXEC_SUPPORT_N_MIN = 30`.
- Payouts are computed off-chain from validator execution logs and sent as Alpha transfers from the owner wallet — fully visible on-chain per transfer.
- **Testnet / early mainnet:** validators run in mock mode (`CSWON_MOCK_EXEC=true`), so no TAO is burned and no pool payout is required during bootstrapping.

> The Execution Support Pool is an economic commitment by the owner, not a protocol escrow. Every payout is an auditable on-chain Alpha transfer.

---

### 4.7 Benchmark Governance

Benchmark tasks are stored **off-chain** in a versioned JSON dataset (`benchmarks/v{N}.json`) in the C-SWON GitHub repo. Validators signal their active benchmark version via `axon.info.description` (e.g. `"cswon-bench:v1"`) alongside the `__spec_version__` integer — a lightweight mechanism requiring no new Subtensor extrinsics. `axon.info.version` is an SDK-managed integer and must not be used for freeform string signals.

- **Auditability:** Anyone can verify which benchmark version a validator is running.
- **Controlled updates:** New versions require ≥3 validator sign-offs via GitHub PR.
- **Tamper detection:** Score outliers from validators on an unrecognised benchmark version are detectable in the on-chain weights matrix.

Benchmark composition: 15–20% synthetic ground truth, 80–85% real-world tasks across code pipelines, RAG, agent tasks, and data transforms. Minimum 50 tasks per version.

**Lifecycle rules per task (fix: buggy tasks now detectable):**

| Trigger                                             | Action                                           | Rationale                                                               |
| --------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------- |
| >70% of miners score >0.90 for 3 consecutive tempos | Deprecate task                                   | Overfitted; no longer discriminating                                    |
| >70% of miners score <0.10 for 3 consecutive tempos | **Quarantine** task; flag for human review | Likely broken test, bad reference answer, or unreachable partner subnet |
| Quarantined task unresolved after 5 tempos          | Remove from active pool automatically            | Prevents dead weight permanently distorting scores                      |

A `"status"` field is added to each task entry in `benchmarks/v{N}.json`:

```json
{
  "task_id": "t-0042",
  "status": "active",
  "quarantine_since_tempo": null,
  "deprecation_reason": null,
  ...
}
```

Valid values: `"active"` | `"quarantined"` | `"deprecated"`. Validators skip tasks whose `status != "active"`. Quarantine transitions are written via PR with ≥2 validator sign-offs (lower bar than full version upgrades).

---

### 4.8 Evaluation Methodology (Six-Stage Pipeline)

1. **Deterministic task selection:**

   ```python
   import hashlib
   seed = f"{validator_hotkey}:{current_block}".encode()
   h    = hashlib.sha256(seed).digest()
   task_index = int.from_bytes(h, 'big') % len(benchmark_tasks)
   task       = benchmark_tasks[task_index]
   ```

   Different validators derive different tasks from the same block via their hotkey-keyed VRF. Cross-validator consensus uses distributional statistics over the rolling window, not identical-task point comparisons — eliminating the need for a gossip layer.
2. **Miner workflow collection:** Send task to 5–10 randomly selected miners with a sub-block timeout (≤ 10 seconds). For each response, validate that the signed `dendrite.hotkey` matches the queried UID in the metagraph before accepting a workflow plan. Discard any response whose hotkey does not match, even if the JSON is well-formed.
3. **Sandboxed execution:** Spin up an isolated Docker container per workflow. Execute each DAG step, resolve DataRefs, and track:

   - Actual TAO consumed per step
   - Wall-clock latency per step
   - Retry counts, timeouts, hard failures
   - `steps_completed` for `completion_ratio`
4. **Output quality evaluation (deterministic, no LLM judge):**

   - **Code:** Automated test pass rate + linting — test suite in task JSON.
   - **RAG:** ROUGE-L F1 against reference answer in benchmark dataset.
   - **Agent:** Binary goal checklist pass rate — checklist in task JSON.
   - **Data transform:** Schema validation + exact-match against expected output.
5. **Composite scoring:** Apply the four-dimensional formula. Compute `S_success = output_quality × completion_ratio`. Add to the rolling 100-task equal-weight window.
6. **Weight submission:** Once per tempo. Normalise scores, cap at 15% per miner, call `set_weights()`.

---

### 4.9 Evaluation Cadence

| Parameter                | Value                                                       | Configurable via          |
| ------------------------ | ----------------------------------------------------------- | ------------------------- |
| Query frequency          | Async, 1 send per block; ≤ 10 s recv timeout               | Not configurable          |
| Score window             | Rolling 100 tasks, equal weight                             | `validator/config.py`   |
| Weight submission        | Once per tempo (360 blocks)                                 | `tempo` hyperparameter  |
| N_min for exec support   | 30 tasks per tempo                                          | `EXEC_SUPPORT_N_MIN`    |
| Benchmark version signal | `axon.info.description` string + `__spec_version__` int | PR + ≥3 sign-offs        |
| Warmup threshold         | 20 tasks                                                    | `WARMUP_TASK_THRESHOLD` |
| Scoring version          | `__spec_version__ = 10000` (int) + description string     | ≥67% validator vote      |

---

### 4.10 Validator Incentive Alignment

- **Stake at risk:** Poor benchmark quality → weaker miners → lower Alpha demand → lower validator returns. The feedback loop runs through market economics.
- **Deterministic consensus:** Outlier validators detectable from the weights matrix. Yuma's bond mechanism progressively reduces rewards for persistent outliers.
- **Exec support access:** Only validators meeting N_min per tempo receive subsidy. Lazy validators self-exclude.
- **Delegation signal:** Stakers monitor validator history via the public dashboard and move stake to higher-quality validators.

> **vtrust bootstrap period (fix: expected behaviour, not a bug):**
> New validators start with `vtrust = 0.0` at registration. Bittensor's Yuma Consensus only grants vtrust as a validator's submitted weights converge with the stake-weighted consensus over multiple tempos. During the **first 5–10 tempos** (~6–12 hours at 360-block tempos), a new validator earns minimal emissions even if their hardware is perfect and their scoring is accurate. This is **expected Bittensor behaviour**, not a broken setup.
>
> New validators should:
>
> 1. Confirm their axon is reachable and UID is registered: `btcli subnet metagraph --netuid <netuid>` — look for your hotkey in the output.
> 2. Monitor `vtrust` in the metagraph — it should begin climbing after tempo 3–5 as bonds accumulate.
> 3. Expect near-zero Alpha earnings for the first 12–24 hours. If vtrust is still 0.0 after tempo 10, check weight submission logs for `CommittingWeightsTooFast` or signature errors.

---

## 5. Alpha Token Economy

### 5.1 CSWON Alpha Role

| Actor      | Earns           | Stakes                 | Can Swap to TAO via AMM?   |
| ---------- | --------------- | ---------------------- | -------------------------- |
| Miners     | Alpha (41% cut) | Not required           | Yes                        |
| Validators | Alpha (41% cut) | Alpha (voluntary bond) | Yes                        |
| Stakers    | Alpha dividends | Alpha or TAO           | Yes (auto for TAO stakers) |
| Owner      | Alpha (18% cut) | —                     | Yes                        |

### 5.2 Liquidity Maintenance

The dTAO AMM pool maintains TAO/CSWON Alpha liquidity automatically:

1. Each block, TAO is injected proportionally to Alpha injection, stabilising price.
2. TAO-staked delegators receive Alpha dividends auto-converted to TAO via the pool.
3. Phase 3 gateway fees (paid in Alpha) increase buy pressure, strengthening pool depth.
4. The subnet's emission rate is governed by **net TAO inflows** under Taoflow. Subnets with net outflows receive zero emissions — attracting genuine stakers is a first-class operational priority from day one.

### 5.3 Phase 3 Fee Flow (Gateway-Level, Month 12+)

Phase 3 fees are **gateway-collected**, not protocol-enforced. Bittensor's Subtensor has no native fee interception mechanism. This is an explicit design choice for MVP.

```
Workflow fee = 5% of actual TAO spent in a workflow
(collected at the C-SWON API Gateway for requests routed through it)

Example: a workflow costing 0.0072τ generates a fee of 0.00036τ

Distribution per tempo:
  Miners:     70% of collected fees (Alpha transfer, owner → miners)
  Validators: 20% of collected fees (Alpha transfer, owner → validators)
  Treasury:   10% of collected fees (dev fund, grants, marketing)

Illustrative projection (Month 12):
  100K workflows/day × 30 days × 0.00036τ fee × $500/TAO ≈ $540K/month
    Miners:    ~$378K
    Validators: ~$108K
    Treasury:   ~$54K
```

> **Note on earlier projections:** The figure of $2.25M/month cited in some earlier drafts assumed an average fee of 0.0015τ per workflow. This is not consistent with the example workflow cost of 0.0072τ shown in Section 3.3 (5% × 0.0072τ = 0.00036τ). The corrected figure above uses the actual example cost. Higher workflow complexity in production (longer DAGs, more subnets) may increase the average cost and thus the fee — but this cannot be stated as a ground-up projection without real usage data.

Users integrating directly at the protocol level (not via Gateway) pay no fee in v1. A trustless fee mechanism is a Phase 4 R&D item.

---

## 6. System Architecture

### 6.1 High-Level Architecture

```mermaid
flowchart TD
    subgraph APP["Application Layer"]
        A["AI Agents (Targon, Nous) · Web3 Apps · Enterprise SDK/API"]
    end

    subgraph GW["C-SWON API Gateway (fee collection point)"]
        G["get_optimal_workflow(task, constraints)
execute_workflow(plan) · monitor_execution(workflow_id)"]
    end

    subgraph SL["C-SWON Subnet Layer"]
        V["Validators (5–20)
· VRF task: hash(hotkey+block) % len(benchmarks)
· Docker sandbox execution
· ROUGE-L · test runner · checklist quality scoring
· Immunity warm-up scale for new miners
· set_weights() once per tempo (360 blocks)
· Exec support claims if tasks_executed >= N_min (30)"]
        M["Miners (30–100)
· Receive task package
· Design DataRef-compliant workflow DAG
· Return executable plan with scoring_version
· Serve via Bittensor axon"]
        S["Subtensor — Blockchain Layer
· Neuron registry · Weights · Alpha emissions · AMM pool"]

        V -->|Task queries — 1 per block, deterministic| M
        M -->|Workflow plans| V
        V -->|set_weights() once per tempo| S
    end

    subgraph ECO["Bittensor Subnet Ecosystem"]
        E["SN1 (Text) · SN62 (Code Review) · SN64 (Inference)
SN45 (Testing) · SN70 (Fact Check) · 100+ subnets"]
    end

    APP --> GW
    GW --> SL
    SL -->|Off-chain authenticated calls via registered hotkey| ECO

    style APP fill:#4c1d95,stroke:#7c3aed,color:#fff
    style GW  fill:#0c4a6e,stroke:#0ea5e9,color:#fff
    style SL  fill:#1e3a5f,stroke:#3b82f6,color:#fff
    style ECO fill:#14532d,stroke:#22c55e,color:#fff
    style A   fill:#6d28d9,stroke:#a78bfa,color:#fff
    style G   fill:#075985,stroke:#38bdf8,color:#fff
    style V   fill:#1d4ed8,stroke:#93c5fd,color:#fff
    style M   fill:#b45309,stroke:#fcd34d,color:#fff
    style S   fill:#0f172a,stroke:#64748b,color:#fff
    style E   fill:#166534,stroke:#4ade80,color:#fff
```

### 6.2 Validation Cycle Detail

```mermaid
sequenceDiagram
    participant V as Validator
    participant M as Miner Pool
    participant P as Partner Subnets (off-chain)

    Note over V: seed = hash(validator_hotkey + block)
    Note over V: task = benchmarks[seed % len]

    V->>M: Task Package (validator-specific pseudorandom task)
    M-->>V: Workflow Plans (DataRef-compliant, scoring_version included)

    Note over V: Sandboxed Docker execution

    V->>P: Off-chain calls via registered hotkey
    P-->>V: Outputs (logged locally, no on-chain receipt)

    Note over V: Quality scoring (no LLM judge)
    Note over V: Code -> test runner
    Note over V: RAG -> ROUGE-L
    Note over V: Agent -> checklist

    Note over V: S = 0.50 * success * completion_ratio
    Note over V: + 0.25 * cost + 0.15 * latency + 0.10 * reliability

    Note over V: Apply immunity warm-up scale if miner is new (< 20 tasks)

    Note over V: Rolling 100-task equal-weight window update

    Note over V: Once per tempo -> set_weights() with 15% cap per miner

    Note over M: Alpha rewards via Yuma Consensus
    Note over V: Alpha rewards (validator take + staker dividends)
```

### 6.3 Risk Register

| Risk                                           | Impact                                                               | Mitigation                                                                                                      |
| ---------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Low miner participation                        | Network fails to bootstrap                                           | 3× query frequency for early miners; GPU credits ($500–$1K); $50K grants pool                                 |
| Validator centralization                       | Collusion risk                                                       | Deterministic task schedule makes outliers visible in weights matrix; Yuma bond mechanism                       |
| Benchmark staleness                            | Miners overfit                                                       | Deprecation at >70% scoring 0.90+ for 3 tempos; quarterly forced rotation                                       |
| Competing orchestration layer                  | Market fragmentation                                                 | First-mover; network effects; deep Bittensor API integration                                                    |
| Insufficient subnet diversity                  | Limited workflow variety                                             | Revenue-share (5% gateway fees) with partner subnets                                                            |
| High execution costs                           | Developers avoid C-SWON                                              | Cost dimension baked into scoring; gateway subsidises early usage                                               |
| Validator TAO solvency                         | Validators exit                                                      | Owner-managed Execution Support Pool; mock mode on testnet; Phase 3 fees long-term                              |
| Negative net TAO inflows                       | Zero emissions (Taoflow)                                             | Active staker acquisition; public Alpha staking ROI dashboard                                                   |
| Alpha halving impact                           | Sudden reward reduction                                              | Pre-announced milestone tracking; treasury buffer                                                               |
| Immunity period scoring noise                  | New miners earn zero initially                                       | Warm-up scale `min(1.0, tasks_seen / 20)` applied in weight calculation                                       |
| Scoring formula version split                  | Divergent weights during upgrades                                    | `SCORING_VERSION` in axon metadata; ≥67% stake vote; 2-tempo notice before upgrade                           |
| LLM judge dependency (v2)                      | Recursive call / non-determinism                                     | v1 uses ROUGE-L + test runners only; LLM judge is a named v2 upgrade path                                       |
| Gateway fee centralization                     | Fee model requires centralized gateway                               | Explicitly acknowledged; trustless fee module is Phase 4 R&D                                                    |
| Pre-caching attack (miners memorise all tasks) | Miners serve cached plans; no real orchestration intelligence tested | VRF-style task schedule keyed to `(validator_hotkey, block)`; miners cannot predict per-validator task stream |
| Score reassignment by dishonest validator      | Validator attributes good miner A plan to miner B                    | Mandatory `dendrite.hotkey == metagraph.hotkeys[uid]` check before accepting any response                     |
| Partner subnet non-determinism                 | Different validators call different partner miners; scores diverge   | Canonical routing policy (top-3 stake-weighted miners, median/majority aggregation) encoded in benchmark JSON   |
| Validator budget bleed via fake estimates      | Malicious miners force expensive sandbox executions                  | Abort at min(max_budget_tao, 1.5× estimated_cost); remaining nodes unexecuted; S_cost = 0                      |
| Buggy benchmark task (always scores 0)         | Broken task becomes permanent dead weight                            | Quarantine trigger: >70% miners <0.10 for 3 tempos → quarantine → remove after 5 tempos                       |
| New validator vtrust confusion                 | Validators quit after day 1 seeing zero earnings                     | vtrust bootstrap note in Section 4.10; expected 0 for first 5–10 tempos                                        |
| No runnable code at launch                     | No one can actually participate                                      | Quickstart guide (Section 10) + required repo layout defined                                                    |

---

## 7. Business Logic & Market Rationale

### The Problem and Why It Matters

Bittensor has become a rich ecosystem of 100+ specialised subnets, but no native layer exists to compose them into reliable, optimised workflows. Today, developers face:

- **Manual orchestration:** Every team hand-wires calls to 5–10 subnets per app.
- **No objective benchmarks:** No standard for measuring which subnet combinations work best for a given task.
- **Brittle integrations:** No standardised error handling, retry logic, or failover.
- **Wasted TAO:** Suboptimal routing burns budget on expensive or slow paths.
- **Innovation bottleneck:** Engineering effort consumed by plumbing, not product.

Each new subnet that joins Bittensor *increases* the orchestration surface area — making the problem worse over time without a dedicated solution layer.

**Market signal:** Zapier grew to $140M ARR solving Web2 workflow orchestration. LangChain and LlamaIndex raised $100M+ building agent frameworks. Bittensor needs its native equivalent — decentralised, incentive-aligned, and continuously improving.

### Competing Solutions

**Within Bittensor:**

| Solution                      | What It Does                     | Why C-SWON Is Different                                  |
| ----------------------------- | -------------------------------- | -------------------------------------------------------- |
| Manual Integration            | Developers call subnets directly | C-SWON automates optimal routing through competition     |
| Bittensor API Layer*(in dev)* | Unified API access               | Solves interop infrastructure, not routing intelligence  |
| Agent Subnets (SN6, etc.)     | Build agents that use tools      | Agents*consume* C-SWON; C-SWON provides the strategies |
| Individual Subnet Routers     | Internal load balancing          | C-SWON operates*across* subnets, not within one        |

**Outside Bittensor:**

| Solution               | Limitations vs. C-SWON                                     |
| ---------------------- | ---------------------------------------------------------- |
| LangChain / LlamaIndex | Centralised; no incentivised optimisation; manual routing  |
| OpenAI Assistants API  | Locked to OpenAI; no external AI composability             |
| Zapier / Make.com      | Not AI-native; no ML model orchestration                   |
| AWS Step Functions     | Generic infrastructure; no AI intelligence; vendor lock-in |

### Why Bittensor Is Ideal

1. **Native composability:** Bittensor treats subnets as modular services. C-SWON extends this to intelligent composition.
2. **Incentive-driven optimisation:** Miners compete to find genuinely optimal workflows, aligned with users — not platform margin.
3. **Network effects:** Every new subnet makes C-SWON more valuable. Every C-SWON workflow makes participating subnets more valuable. Value scales super-linearly.
4. **Decentralised resilience:** Orchestration logic is distributed across competing miners — no single point of failure.

### Development Phases

| Phase                   | Timeline      | Target                                                                          |
| ----------------------- | ------------- | ------------------------------------------------------------------------------- |
| 1 — Bootstrap          | Months 1–6   | 30–50 miners, 5–10 validators, 1K+ workflows/day; testnet, mock execution     |
| 2 — Developer Adoption | Months 6–12  | 10+ apps, 10K+ workflows/day; mainnet, live sandbox                             |
| 3 — Revenue Model      | Months 12–24 | Gateway fee launch; ~$540K/month at 100K workflows/day                          |
| 4 — Ecosystem Standard | 24+ months    | Trustless fee R&D; BERTScore quality upgrade; Bittensor API gateway integration |

---

## 8. Go-To-Market Strategy

### Target Users and Anchor Use Cases

C-SWON's primary users are **agent platform builders** — teams building on Targon (SN4), Nous (SN6), or LangChain-based Bittensor integrations — who spend 70%+ of engineering effort on manual orchestration.

**Anchor use cases:**

1. **Code Pipeline as a Service:** `SN1 (generate) → SN62 (review) → SN45 (test)`. Result: 10× faster than manual, ~30% lower cost.
2. **RAG + Fact-Check Stack:** `Document subnet → Text subnet → SN70 (verify)`. Result: Trustworthy AI responses for regulated industries.
3. **Multi-Model Consensus:** `3× text subnets → SN70 → confidence aggregation`. Result: High-reliability outputs for legal, medical, and financial tasks.

**Secondary users:** Bittensor subnet operators who benefit from increased traffic from being included in popular C-SWON workflows — making them natural ecosystem promoters.

### Distribution Channels

- `bittensor-cswon` Python/TypeScript SDK: `cswon.execute("task", constraints)`
- Pre-built integrations for Targon, Nous, LangChain Bittensor connectors
- Developer tutorials: "Build a production AI pipeline in 10 minutes with C-SWON"
- Hackathon bounties: $50K across three events in Months 3, 6, 9
- Research publications: benchmark studies vs. manual orchestration

### Early Participation Incentives

| Stakeholder           | Incentive                                                              | Mechanism                                    |
| --------------------- | ---------------------------------------------------------------------- | -------------------------------------------- |
| Miners (first 50)     | 3× query frequency for 6 months + $500–$1K GPU credits + $50K grants | Validator selection logic + off-chain grants |
| Validators (first 10) | Owner stakes up to 1K TAO Alpha equivalent + $20K benchmark grants     | Manual on-chain Alpha transfer (auditable)   |
| Developers            | First 10K workflows free per project + $500–$2K migration bounty      | Gateway policy + off-chain grants            |
| Subnet Partners       | 5% traffic revenue share from gateway fees + $10K co-marketing         | Gateway distribution + agreements            |

---

## 9. Known Limitations and Upgrade Path

The following items are intentionally deferred from v1 to keep the MVP honest and buildable on testnet. They are not design failures — they are explicit decisions.

| Limitation                       | v1 Approach                                | Upgrade Path                                                           |
| -------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| No on-chain execution receipts   | Off-chain logs + Yuma consensus            | Sub-subnet with execution receipts (Phase 4)                           |
| No protocol-level fee collection | Gateway-level fee collection (centralised) | Trustless billing module if Subtensor adds EVM (Phase 4)               |
| ROUGE-L only for RAG quality     | Deterministic, reproducible                | Local BERTScore or embedding similarity (v2, no external calls)        |
| Manual Execution Support Pool    | Owner transfers each tempo                 | Multi-sig governance contract (Phase 4)                                |
| No on-chain slashing             | Economic + governance penalties only       | Slashing if added to Bittensor protocol                                |
| Social scoring upgrade protocol  | ≥67% stake vote + 2-tempo notice          | Automated via governance module (Phase 3+)                             |
| Parallel DAG semantics undefined | Sequential-only spec in v1                 | Fixed in Section 3.2: parallel tiers, per-node DataRef failure scoping |
| Planned retries penalised        | Error handling disincentivised             | Fixed in Section 2.2: only unplanned_retries scored                    |
| axon.info.version type mismatch  | SCORING_VERSION silently broken            | Fixed in Section 4.5:__spec_version__ int + description string   |
| Buggy benchmark task stuck at 0  | Dead weight in scoring pool                | Fixed in Section 4.7: quarantine + auto-remove lifecycle               |

---

## 10. Quickstart Guide

> Referenced code paths (`neurons/miner.py`, `neurons/validator.py`, `validator/`)
> must exist in the repository before mainnet launch. This section defines the
> **required file layout** and the exact commands participants will run.

### Repository Layout (Required)

```
C-SWON/
├── .circleci/
│   └── config.yml                   ← CI pipeline: lint, test, docker-build jobs
├── benchmarks/
│   └── v1.json
├── contrib/
│   ├── CODE_REVIEW_DOCS.md
│   ├── CONTRIBUTING.md              ← includes CircleCI documentation
│   ├── DEVELOPMENT_WORKFLOW.md
│   └── STYLE.md
├── cswon/
│   ├── api/
│   │   ├── __init__.py
│   │   └── get_query_axons.py
│   ├── base/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── weight_utils.py
│   │   ├── __init__.py
│   │   ├── miner.py
│   │   ├── neuron.py
│   │   └── validator.py
│   ├── miner/
│   │   ├── __init__.py
│   │   └── subnet_profiler.py       ← subnet cost/latency profiler (§3.6)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── misc.py
│   │   └── uids.py
│   ├── validator/
│   │   ├── __init__.py
│   │   ├── base.py                  ← re-exports BaseValidatorNeuron
│   │   ├── benchmark_lifecycle.py   ← quarantine/deprecation + quarterly rotation (§4.7)
│   │   ├── config.py
│   │   ├── docker_sandbox.py        ← Docker sandbox runner (§4.8 stage 3)
│   │   ├── executor.py              ← parallel-tier DAG execution (§4.8)
│   │   ├── executor_entrypoint.py   ← Docker container entry module (§4.8)
│   │   ├── forward.py               ← six-stage validator pipeline
│   │   ├── miner_selection.py       ← immunity-aware miner selection
│   │   ├── query_loop.py            ← async sub-block query loop (§4.1)
│   │   ├── reward.py                ← composite scoring + warm-up scale (§4.4)
│   │   ├── scoring.py               ← re-exports scoring symbols
│   │   └── weight_setter.py         ← tempo-aligned weight submission (§4.1)
│   ├── __init__.py
│   ├── mock.py
│   ├── protocol.py                  ← WorkflowSynapse only (Dummy removed)
│   └── subnet_links.py
├── docs/
│   ├── stream_tutorial/
│   │   ├── client.py
│   │   ├── config.py
│   │   ├── miner.py
│   │   ├── protocol.py
│   │   └── README.md
│   ├── ops_runbook.md               ← Execution Support Pool operator runbook (§4.6)
│   ├── running_on_mainnet.md
│   ├── running_on_staging.md
│   └── running_on_testnet.md
├── neurons/
│   ├── __init__.py
│   ├── miner.py
│   └── validator.py
├── scripts/
│   ├── check_compatibility.sh
│   ├── check_requirements_changes.sh
│   ├── exec_support_payout.py       ← Exec Support Pool payout tool (§4.6)
│   └── install_staging.sh
├── tests/
│   ├── __init__.py
│   ├── helpers.py
│   ├── test_executor.py
│   ├── test_mock.py
│   ├── test_protocol.py
│   ├── test_scoring.py
│   └── test_template_validator.py
├── verify/
│   ├── generate.py                  ← signs coldkey messages for identity verification
│   └── verify.py                    ← verifies coldkey signatures
├── Dockerfile                       ← builds cswon-executor:latest sandbox image (§4.8)
├── LICENSE
├── min_compute.yml
├── README.md
├── requirements.txt
└── setup.py
```

---

### Miner Quickstart

**Step 1 — Clone and install**

```bash
git clone https://github.com/adysingh5711/C-SWON.git
cd C-SWON
pip install -r requirements.txt
```

**Step 2 — Create wallet**

```bash
btcli wallet new_coldkey --wallet.name my_miner
btcli wallet new_hotkey  --wallet.name my_miner --wallet.hotkey default
```

**Step 3 — Register on the subnet**

```bash
# Testnet — find current netuid with:
#   btcli subnet list --subtensor.network test
# Then register:
btcli subnet register \
  --netuid <testnet_netuid> \
  --wallet.name my_miner \
  --wallet.hotkey default \
  --subtensor.network test

# Mainnet (once subnet is live)
btcli subnet register   --netuid <mainnet_netuid>   --wallet.name my_miner   --wallet.hotkey default
```

**Step 4 — Run the miner**

```bash
python neurons/miner.py   --netuid <netuid>   --wallet.name my_miner   --wallet.hotkey default   --axon.port 8091   --subtensor.network <test|finney>
```

**Step 5 — Check you are reachable**

```bash
btcli subnet metagraph --netuid <netuid>
# Confirm your UID appears and axon IP:port is visible
```

**Expected behaviour:**

- Immediately after registration: `trust = 0`, `emission = 0`. This is normal.
- After first few tempos: `incentive` and `emission` will begin to appear once
  validators query and score your workflows.

---

### Validator Quickstart

**Step 1–2:** Same as miner (clone, install, create wallet).

**Step 3 — Register on the subnet** *(same command as miner, different wallet name)*

**Step 4 — Ensure Docker is running**

```bash
docker info   # must succeed; Docker 24.x+ required
```

**Step 5 — Configure execution mode**

```bash
# Testnet / early mainnet: mock mode (no real TAO burned)
export CSWON_MOCK_EXEC=true

# Mainnet with live execution (NOT needed for testnet demo):
export CSWON_MOCK_EXEC=false
export CSWON_PARTNER_HOTKEY=<your_registered_hotkey_on_partner_subnets>
# NOTE: Partner subnets (SN1, SN62 etc.) are not available on testnet.
# For the testnet demo, always use CSWON_MOCK_EXEC=true.
```

**Step 6 — Run the validator**

```bash
python neurons/validator.py   --netuid <netuid>   --wallet.name my_validator   --wallet.hotkey default   --axon.port 8092   --subtensor.network <test|finney>
```

**Step 7 — Verify weight submission**

```bash
btcli subnet metagraph --netuid <netuid>
# After first tempo (~72 min), your UID should show vtrust > 0
# and weights column should be non-zero
```

**Expected behaviour:**

- `vtrust = 0.0` for first 5–10 tempos. This is expected (see Section 4.10).
- If vtrust is still 0 after tempo 10: check logs for `CommittingWeightsTooFast`
  or run `btcli subnet metagraph --netuid <netuid>` and inspect your UID row.

---

### Common Errors

| Error                            | Cause                                       | Fix                                                                            |
| -------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------ |
| `CommittingWeightsTooFast`     | Submitting weights more than once per tempo | Check `last_set_block` logic in `weight_setter.py`                         |
| `Axon not reachable`           | Port not open externally                    | Open port 8091/8092 in firewall; confirm with `curl http://<your_ip>:8091/`  |
| `vtrust = 0.0` after 10 tempos | Weights not being accepted                  | Check `set_weights()` return value; ensure UID is not in `immunity_period` |
| `CSWON_MOCK_EXEC missing`      | Env var not set                             | `export CSWON_MOCK_EXEC=true` before running validator                       |
| Docker permission denied         | Docker daemon not accessible                | Run `sudo usermod -aG docker $USER && newgrp docker`                         |

## Conclusion

> *"Bittensor has 100+ specialised AI services, but no brain to wire them together.
> C-SWON is that brain — a subnet where the commodity is optimal orchestration policy.
> We turn 'which subnets to call and how' into a competitive intelligence market,
> making Bittensor the world's first truly composable AI operating system."*

> **GitHub:** [https://github.com/adysingh5711/C-SWON](https://github.com/adysingh5711/C-SWON) </br>
> **Demo:** [https://youtu.be/X2RZts7AXX0](https://youtu.be/X2RZts7AXX0) </br>
> **Hackathon Link:** [https://www.hackquest.io/hackathons/Bittensor-Subnet-Ideathon](https://www.hackquest.io/hackathons/Bittensor-Subnet-Ideathon) </br>
> **Results:** [https://x.com/singhaditya5711/status/2030662024922071367?s=20](https://x.com/singhaditya5711/status/2030662024922071367?s=20) </br>
> **Whitepaper:** Upcoming

*C-SWON: Cross-Subnet Workflow Orchestration Network - Making Bittensor Composable*
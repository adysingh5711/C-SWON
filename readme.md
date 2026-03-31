![Testnet](https://img.shields.io/badge/testnet-live-brightgreen)
![Scoring Version](https://img.shields.io/badge/scoring-v1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-teal)

# C-SWON: Cross-Subnet Workflow Orchestration Network

**C-SWON is a decentralised AI workflow router built on Bittensor.** You give it a task; it competes to find which combination of AI services produces the best result at the lowest cost, learns from that competition, and improves over time.

> *"Zapier for Subnets"* — The Intelligence Layer for Multi-Subnet Composition

---

## The Digital Commodity

The mined commodity is **optimal workflow policy** — which subnets to call, in what order, with what parameters, to complete a given task at the lowest cost and highest quality. Miners propose multi-subnet execution plans (DAGs), validators score them on task success, cost, and latency, and the network continuously learns the best orchestration strategies through competitive pressure.

---

## Quick Navigation

| I am a... | My starting point |
|---|---|
| **Miner** | [Quickstart Miner](docs/1.2-quickstart-miner.md) |
| **Validator** | [Quickstart Validator](docs/1.3-quickstart-validator.md) |
| **Developer integrating C-SWON** | [WorkflowSynapse Protocol](docs/2.2-protocol.md) |
| **Hackathon Judge** | [Testnet Evidence](docs/7.1-testnet-evidence.md) → [Incentive Verification](docs/7.3-incentive-verification.md) |
| **Exploring the design** | [What is C-SWON?](docs/1.1-what-is-cswon.md) |

---

## Testnet Status

> **Verify live:**
> ```bash
> btcli subnet metagraph --netuid 26 --subtensor.network test
> ```

- 10 miner hotkeys registered
- 3 validator hotkeys registered
- Scoring version: `1.0.0`
- Execution mode: `CSWON_MOCK_EXEC=true`

---

## How It Works

```
Validator                          Miner                         Partner Subnets
    │                                │                                │
    │─── Task Package ──────────────►│                                │
    │    (task_id, constraints,      │                                │
    │     available_tools)           │                                │
    │                                │── Design DAG ──►               │
    │◄── WorkflowSynapse ───────────│   (nodes, edges,               │
    │    (workflow_plan,             │    error_handling)              │
    │     estimated_cost)            │                                │
    │                                │                                │
    │── Execute DAG in Docker ──────────────────────────────────────►│
    │                                │                    SN1, SN62,  │
    │◄── Collect outputs ───────────────────────────────── SN45 ────│
    │                                │                                │
    │── Score: S = 0.50×success + 0.25×cost + 0.15×latency + 0.10×reliability
    │── set_weights() per tempo ──► Subtensor
```

---

## Scoring Formula (v1.0.0)

```
S = 0.50 × S_success + 0.25 × S_cost + 0.15 × S_latency + 0.10 × S_reliability
```

- **S_success** = output_quality × completion_ratio (deterministic: ROUGE-L, test pass rate — no LLM judge)
- **S_cost** = max(0, 1 − actual/budget) — gated at S_success > 0.7
- **S_latency** = max(0, 1 − actual_s/max_s) — gated at S_success > 0.7
- **S_reliability** = 1 − penalties for unplanned retries, timeouts, failures

[Full formula details →](docs/3.2-scoring-formula.md)

---

## Anti-Gaming Mechanisms

| Mechanism | Purpose |
|---|---|
| VRF-keyed task schedule | Each validator derives tasks from `hash(hotkey + block)` — miners cannot pre-cache |
| Synthetic ground truth (15-20%) | Hidden known-answer tasks mixed into real workload |
| Benchmark rotation | Tasks deprecated when >70% miners score >0.90 for 3 tempos |
| Execution sandboxing | Docker containers track actual cost, latency, retries |
| 15% weight cap per miner | Prevents single-miner dominance |

[Full anti-gaming details →](docs/3.4-anti-gaming.md)

---

## SDK Integration (Preview)

```python
from cswon import WorkflowGateway

gw = WorkflowGateway(wallet=my_wallet, netuid=26)
result = gw.execute(
    "Generate a FastAPI endpoint with JWT auth and unit tests",
    constraints={"max_budget_tao": 0.05, "max_latency_seconds": 10}
)
```

---

## Documentation

Full documentation is available in the [`docs/`](docs/) directory and on the [documentation website](https://adysingh5711.github.io/C-SWON/).

### Getting Started
- [1.1 What is C-SWON?](docs/1.1-what-is-cswon.md)
- [1.2 Quickstart: Miner](docs/1.2-quickstart-miner.md)
- [1.3 Quickstart: Validator](docs/1.3-quickstart-validator.md)

### Architecture
- [2.1 System Architecture](docs/2.1-architecture.md)
- [2.2 WorkflowSynapse Protocol](docs/2.2-protocol.md)
- [2.3 DAG Execution Model](docs/2.3-dag-execution.md)

### Incentive Design
- [3.1 Emission Structure (dTAO)](docs/3.1-emission-structure.md)
- [3.2 Scoring Formula v1.0.0](docs/3.2-scoring-formula.md)
- [3.3 Output Quality Scoring](docs/3.3-quality-scoring.md)
- [3.4 Anti-Gaming Mechanisms](docs/3.4-anti-gaming.md)
- [3.5 Scoring Version Control](docs/3.5-scoring-versioning.md)

### Guides
- [4.1 Miner Registration](docs/4.1-miner-registration.md) · [4.2 Workflow Plan](docs/4.2-workflow-plan.md) · [4.3 Lifecycle](docs/4.3-miner-lifecycle.md) · [4.4 Early Participation](docs/4.4-early-participation.md)
- [5.1 Validator Hardware](docs/5.1-validator-hardware.md) · [5.2 Evaluation Pipeline](docs/5.2-evaluation-pipeline.md) · [5.3 Weight Submission](docs/5.3-weight-submission.md) · [5.4 Benchmark Governance](docs/5.4-benchmark-governance.md) · [5.5 Exec Support Pool](docs/5.5-exec-support-pool.md) · [5.6 Immunity & Warm-Up](docs/5.6-immunity-warmup.md)

### Deployment
- [6.1 Testnet](docs/6.1-running-on-testnet.md) · [6.2 Mainnet](docs/6.2-running-on-mainnet.md) · [6.3 Local Staging](docs/6.3-running-on-staging.md) · [6.4 Local Deploy](docs/6.4-local-deploy.md) · [6.5 Testnet Deploy](docs/6.5-testnet-deploy.md)

### Proof of Execution (Hackathon Evidence)
- [7.1 Testnet Evidence](docs/7.1-testnet-evidence.md) — Transaction hashes, metagraph snapshots
- [7.2 Validator Logs](docs/7.2-validator-logs.md) — Stage-by-stage pipeline output
- [7.3 Incentive Verification](docs/7.3-incentive-verification.md) — Proof of functional miner, validator, and incentive mechanisms

### Economics & Roadmap
- [8.1 Token Economy](docs/8.1-token-economy.md) · [8.2 Go-to-Market](docs/8.2-go-to-market.md) · [8.3 Roadmap](docs/8.3-roadmap.md)

### Contributing
- [9.1 Contributing Guide](docs/9.1-contributing.md)

---

## Repository Structure

```
C-SWON/
├── cswon/                   # Core subnet package
│   ├── protocol.py          # WorkflowSynapse — single source of truth
│   ├── base/                # BaseValidator / BaseMiner abstract classes
│   ├── validator/           # Scoring, execution, weight submission (3,035 LOC)
│   ├── miner/               # Subnet profiler, workflow planning
│   ├── api/                 # External-facing HTTP endpoints
│   └── utils/               # Shared helpers
├── neurons/                 # Entry points: validator.py, miner.py
├── tests/                   # Unit + integration tests (9 test files)
├── benchmarks/              # Versioned benchmark task datasets (v1.json)
├── docs/                    # Full numbered documentation (32 files)
├── frontend/                # Next.js dashboard (metagraph, DAG viewer, scores)
├── documentation_website/   # Docusaurus documentation site
├── contrib/                 # Contributing guidelines, style guide
└── scripts/                 # Benchmark generation, deployment helpers
```

---

## Links

| Resource | URL |
|---|---|
| GitHub | [github.com/adysingh5711/C-SWON](https://github.com/adysingh5711/C-SWON) |
| Demo Video | [youtu.be/X2RZts7AXX0](https://youtu.be/X2RZts7AXX0) |
| Documentation Site | [adysingh5711.github.io/C-SWON](https://adysingh5711.github.io/C-SWON/) |
| Hackathon | [HackQuest Submission](https://www.hackquest.io/hackathons/Bittensor-Subnet-Hackathon) |
| Bittensor Docs | [docs.learnbittensor.org](https://docs.learnbittensor.org) |

---

## Contact

| | |
|---|---|
| **Email** | [singhaditya5711@gmail.com](mailto:singhaditya5711@gmail.com) |
| **Twitter / X** | [@singhaditya5711](https://x.com/singhaditya5711) |
| **Telegram** | [@singhaditya5711](https://t.me/singhaditya5711) |
| **LinkedIn** | [singhaditya5711](https://www.linkedin.com/in/singhaditya5711/) |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*C-SWON: Cross-Subnet Workflow Orchestration Network — Making Bittensor Composable*

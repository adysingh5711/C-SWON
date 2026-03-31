---
id: index
title: "C-SWON Documentation"
sidebar_position: 1
---

# C-SWON Documentation

> *"The kernel of C-SWON is two things: a benchmark that measures optimal workflow policy, and a submission format (WorkflowSynapse). Everything else in these docs explains those two things."*

---

## 1. Getting Started

- [1.1 What is C-SWON?](1.1-what-is-cswon.md) — Problem statement, vision, digital commodity
- [1.2 Quickstart: Miner](1.2-quickstart-miner.md) — Register and run a miner in under 10 minutes
- [1.3 Quickstart: Validator](1.3-quickstart-validator.md) — Set up the full evaluation pipeline

## 2. Architecture

- [2.1 System Architecture](2.1-architecture.md) — High-level diagrams, validation cycle, risk register
- [2.2 WorkflowSynapse Protocol](2.2-protocol.md) — The wire format, field contract, submission format
- [2.3 DAG Execution Model](2.3-dag-execution.md) — DataRef syntax, execution contract, parallel rules

## 3. Incentive Design

- [3.1 Emission Structure (dTAO)](3.1-emission-structure.md) — Alpha split, AMM liquidity, halving
- [3.2 Scoring Formula v1.0.0](3.2-scoring-formula.md) — S = 0.50 success + 0.25 cost + 0.15 latency + 0.10 reliability
- [3.3 Output Quality Scoring](3.3-quality-scoring.md) — ROUGE-L, test runners, goal checklists — no LLM judge
- [3.4 Anti-Gaming Mechanisms](3.4-anti-gaming.md) — VRF tasks, synthetic ground truth, benchmark rotation
- [3.5 Scoring Version Control](3.5-scoring-versioning.md) — __spec_version__, upgrade protocol

## 4. Miner Guide

- [4.1 Registration & Requirements](4.1-miner-registration.md) — Hardware, stake, immunity period
- [4.2 Workflow Plan Design](4.2-workflow-plan.md) — Input/output JSON, routing policy
- [4.3 Miner Development Lifecycle](4.3-miner-lifecycle.md) — Profile, build, optimise, deploy
- [4.4 Early Participation Programme](4.4-early-participation.md) — 3x query frequency, grants

## 5. Validator Guide

- [5.1 Hardware Requirements](5.1-validator-hardware.md) — Compute specs, authentication model
- [5.2 Evaluation Pipeline](5.2-evaluation-pipeline.md) — Six-stage pipeline, cadence table
- [5.3 Weight Submission](5.3-weight-submission.md) — Tempo-aligned submission, async query loop
- [5.4 Benchmark Governance](5.4-benchmark-governance.md) — Lifecycle rules, quarantine, versioning
- [5.5 Execution Support Pool](5.5-exec-support-pool.md) — Operator runbook, eligibility, payouts
- [5.6 Immunity & Warm-Up](5.6-immunity-warmup.md) — Warm-up scale, vtrust bootstrap

## 6. Deployment & Operations

- [6.1 Running on Testnet](6.1-running-on-testnet.md) — Create subnet, register, run on test network
- [6.2 Running on Mainnet](6.2-running-on-mainnet.md) — Production deployment guide
- [6.3 Running Locally (Staging)](6.3-running-on-staging.md) — Local blockchain setup
- [6.4 Local Deploy Guide](6.4-local-deploy.md) — Docker-based local development
- [6.5 Testnet Deploy Guide](6.5-testnet-deploy.md) — Detailed testnet deployment steps

## 7. Proof of Execution (Hackathon Evidence)

- [7.1 Testnet Evidence](7.1-testnet-evidence.md) — Transaction hashes, metagraph snapshots
- [7.2 Validator Logs](7.2-validator-logs.md) — Stage-by-stage pipeline output
- [7.3 Incentive Verification](7.3-incentive-verification.md) — Three explicit proofs for judges

## 8. Economics & Roadmap

- [8.1 Token Economy](8.1-token-economy.md) — Alpha role, liquidity, Phase 3 fees
- [8.2 Go-to-Market Strategy](8.2-go-to-market.md) — Target users, use cases, distribution
- [8.3 Roadmap & Known Limitations](8.3-roadmap.md) — Four phases, upgrade paths

## 9. Contributing

- [9.1 Contributing Guide](9.1-contributing.md) — PR guidelines, CI pipeline, style guide

---

## Links

| Resource | URL |
|---|---|
| GitHub | [github.com/adysingh5711/C-SWON](https://github.com/adysingh5711/C-SWON) |
| Demo Video | [youtu.be/X2RZts7AXX0](https://youtu.be/X2RZts7AXX0) |
| Hackathon | [HackQuest Submission](https://www.hackquest.io/hackathons/Bittensor-Subnet-Hackathon) |

## Contact

| | |
|---|---|
| **Email** | [singhaditya5711@gmail.com](mailto:singhaditya5711@gmail.com) |
| **Twitter** | [@singhaditya5711](https://x.com/singhaditya5711) |
| **Telegram** | [@singhaditya5711](https://t.me/singhaditya5711) |
| **LinkedIn** | [singhaditya5711](https://www.linkedin.com/in/singhaditya5711/) |

---

## Navigation

| | |
|---|---|
| → Next | [1.1 What is C-SWON?](1.1-what-is-cswon.md) |
| Repository | [github.com/adysingh5711/C-SWON](https://github.com/adysingh5711/C-SWON) |

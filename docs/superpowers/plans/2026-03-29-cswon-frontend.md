# C-SWON Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete C-SWON frontend — a dark network-operations-style interface with 5 pages, interactive DAG visualization, mock data mirroring the real backend, and Vercel-ready deployment from `frontend/`.

**Architecture:** Next.js 15 App Router with TypeScript and Tailwind CSS v4. All data sourced from `lib/mock-data.ts` — a single file mirroring `WorkflowSynapse`, `ScoreAggregator`, and `benchmarks/v1.json` shapes. Shared components (`DAGViewer`, `ScoreBreakdown`, etc.) live in `components/`. No external state management — React state + context only. ReactFlow for DAG visualization.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS v4, ReactFlow (DAG), Recharts (charts), Framer Motion (animation)

**Design Direction:**
- Dark canvas (`#0a0e17`) with teal accent (`#00d4aa`) and gold for TAO values (`#f0b429`)
- Monospace (JetBrains Mono / Geist Mono) for data, Inter/Geist Sans for prose
- Borders-only depth (no shadows) — rgba borders at low opacity
- Surface elevation via lightness shifts on same navy hue
- Signature: DAG-as-living-organism — nodes pulse, edges animate data flow

---

## File Structure

```
frontend/
  package.json
  tsconfig.json
  next.config.ts
  tailwind.config.ts
  postcss.config.mjs
  app/
    layout.tsx              — Root layout: dark theme, fonts, nav
    page.tsx                — Landing page
    globals.css             — CSS variables, base styles
    dashboard/
      page.tsx              — Network dashboard
    submit/
      page.tsx              — Task submission flow
    task/
      [id]/
        page.tsx            — Single task detail
    explorer/
      page.tsx              — Miner/validator explorer
  components/
    nav.tsx                 — Top navigation bar
    dag-viewer.tsx          — Interactive DAG visualization (ReactFlow)
    score-breakdown.tsx     — Four-bar horizontal score breakdown
    score-gauge.tsx         — Semi-circular gauge for single dimension
    lifecycle-badge.tsx     — Colored pill: active/quarantined/deprecated
    miner-card.tsx          — Miner response card (competition view)
    step-animator.tsx        — Tier-by-tier DAG execution animation
    block-counter.tsx       — Auto-incrementing block counter
    weight-bar.tsx          — Horizontal bar with 15% cap line
    emission-sankey.tsx     — Emission flow diagram
    task-type-icon.tsx      — Icon for code/rag/agent/data_transform
    stat-card.tsx           — Metric display card
    data-table.tsx          — Sortable data table
    subnet-chip.tsx         — Subnet selector chip
  lib/
    mock-data.ts            — All mock data (single source of truth)
    types.ts                — TypeScript interfaces mirroring backend
    utils.ts                — Formatting helpers (truncate hotkey, format TAO, etc.)
    constants.ts            — Design tokens, scoring weights, config values
```

---

## Task 1: Project Scaffolding & Design Tokens

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/lib/constants.ts`

- [ ] **Step 1: Initialize Next.js project**

```bash
cd /Users/aditya/Dev/Web3/Bittensor/Cross-Subnet-Workflow-Orchestration-Network-SWON-
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false --import-alias="@/*" --use-npm --eslint
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install @xyflow/react recharts framer-motion
npm install -D @types/node
```

- [ ] **Step 3: Create `lib/constants.ts` with design tokens**

```typescript
// Design tokens for C-SWON dark network operations interface
export const colors = {
  // Surfaces (navy hue, elevation via lightness)
  canvas: "#0a0e17",
  surface0: "#0f1420",
  surface1: "#141a2a",
  surface2: "#1a2235",
  surface3: "#212b40",

  // Foreground (text hierarchy)
  ink: "#e8edf5",
  inkSecondary: "#8a94a8",
  inkTertiary: "#5a6478",
  inkMuted: "#3d4658",

  // Borders (rgba for blending)
  border: "rgba(138, 148, 168, 0.12)",
  borderEmphasis: "rgba(138, 148, 168, 0.25)",
  borderFocus: "rgba(0, 212, 170, 0.5)",

  // Accent
  teal: "#00d4aa",
  tealMuted: "rgba(0, 212, 170, 0.15)",
  tealDim: "#00a885",

  // Value / TAO
  gold: "#f0b429",
  goldMuted: "rgba(240, 180, 41, 0.15)",

  // Semantic
  success: "#22c55e",
  successMuted: "rgba(34, 197, 94, 0.15)",
  warning: "#eab308",
  warningMuted: "rgba(234, 179, 8, 0.15)",
  error: "#ef4444",
  errorMuted: "rgba(239, 68, 68, 0.15)",
} as const;

export const scoring = {
  weights: { success: 0.50, cost: 0.25, latency: 0.15, reliability: 0.10 },
  successGate: 0.70,
  windowSize: 100,
  maxMinerWeight: 0.15,
  warmupThreshold: 20,
} as const;

export const network = {
  tempo: 360,
  execSupportMin: 30,
  queryTimeout: 9,
  immunityPeriod: 5000,
} as const;
```

- [ ] **Step 4: Write `app/globals.css` with CSS custom properties**

```css
@import "tailwindcss";

@theme {
  --color-canvas: #0a0e17;
  --color-surface-0: #0f1420;
  --color-surface-1: #141a2a;
  --color-surface-2: #1a2235;
  --color-surface-3: #212b40;

  --color-ink: #e8edf5;
  --color-ink-secondary: #8a94a8;
  --color-ink-tertiary: #5a6478;
  --color-ink-muted: #3d4658;

  --color-teal: #00d4aa;
  --color-teal-dim: #00a885;
  --color-gold: #f0b429;

  --color-border: rgba(138, 148, 168, 0.12);
  --color-border-emphasis: rgba(138, 148, 168, 0.25);

  --font-mono: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;
  --font-sans: "Geist", "Inter", ui-sans-serif, sans-serif;
}

body {
  background-color: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-sans);
}

/* Scrollbar styling for dark theme */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: var(--color-surface-0);
}
::-webkit-scrollbar-thumb {
  background: var(--color-ink-muted);
  border-radius: 3px;
}
```

- [ ] **Step 5: Write root `app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ subsets: ["latin"], variable: "--font-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "C-SWON — Cross-Subnet Workflow Orchestration",
  description: "Zapier for Subnets — The Intelligence Layer for Multi-Subnet Composition",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 6: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): scaffold Next.js project with design tokens and dark theme"
```

---

## Task 2: TypeScript Types & Mock Data

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/mock-data.ts`
- Create: `frontend/lib/utils.ts`

- [ ] **Step 1: Create `lib/types.ts` — all interfaces mirroring backend**

```typescript
// Mirrors cswon/protocol.py WorkflowSynapse and supporting structures

export type TaskType = "code" | "rag" | "agent" | "data_transform";
export type LifecycleStatus = "active" | "quarantined" | "deprecated";
export type StepStatus = "pending" | "running" | "completed" | "failed";

export interface SubnetTool {
  type: string;
  avg_cost: number;
  avg_latency: number;
}

export interface TaskConstraints {
  max_budget_tao: number;
  max_latency_seconds: number;
  allowed_subnets: string[];
}

export interface RoutingPolicy {
  default: {
    miner_selection: string;
    top_k: number;
    aggregation: string;
  };
}

export interface BenchmarkTask {
  task_id: string;
  task_type: TaskType;
  status: LifecycleStatus;
  description: string;
  quality_criteria: Record<string, number>;
  constraints: TaskConstraints;
  available_tools: Record<string, SubnetTool>;
  routing_policy: RoutingPolicy;
  reference: Record<string, unknown>;
  deprecation_reason?: string;
}

export interface WorkflowNode {
  id: string;
  subnet: string;
  action: string;
  estimated_cost: number;
  estimated_latency: number;
  error_handling?: {
    retry_count: number;
    timeout: number;
  };
  tier: number; // execution tier (parallel grouping)
  status?: StepStatus;
}

export interface WorkflowEdge {
  from: string;
  to: string;
  data_ref?: string;
}

export interface WorkflowPlan {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface MinerResponse {
  miner_uid: number;
  hotkey: string;
  scoring_version: string;
  workflow_plan: WorkflowPlan;
  total_estimated_cost: number;
  total_estimated_latency: number;
  confidence: number;
  reasoning: string;
  composite_score?: number;
}

export interface ScoreBreakdownData {
  composite: number;
  success: number;
  cost: number;
  latency: number;
  reliability: number;
}

export interface MinerProfile {
  uid: number;
  hotkey: string;
  coldkey: string;
  role: "miner";
  stake: number;
  registration_block: number;
  blocks_since_registration: number;
  immunity_active: boolean;
  immunity_blocks_remaining: number;
  tasks_seen: number;
  scores: ScoreBreakdownData;
  score_history: number[]; // last 100 composite scores
  weight: number;
  weight_capped: boolean;
  subnet_stats: Record<string, {
    avg_cost: number;
    avg_latency: number;
    reliability: number;
    observations: number;
  }>;
  recent_workflows: MinerResponse[];
}

export interface ValidatorProfile {
  uid: number;
  hotkey: string;
  coldkey: string;
  role: "validator";
  stake: number;
  vtrust: number;
  last_weight_set_block: number;
  scoring_version: string;
  benchmark_version: string;
}

export interface AuditFlag {
  uid: number;
  block: number;
  score: number;
  previous_avg: number;
  jump_percent: number;
  message: string;
}

export interface NetworkStats {
  current_block: number;
  current_tempo: number;
  tasks_this_tempo: number;
  active_miners: number;
  active_validators: number;
  tasks_evaluated: number;
}

export interface ExecutionStep {
  node_id: string;
  status: StepStatus;
  output?: string;
  cost: number;
  latency: number;
  started_at?: number;
  completed_at?: number;
}

export interface ExecutionResult {
  steps: ExecutionStep[];
  final_output: string;
  total_cost: number;
  total_latency: number;
  scores: ScoreBreakdownData;
}
```

- [ ] **Step 2: Create `lib/utils.ts` — formatting helpers**

```typescript
export function truncateKey(key: string, chars = 6): string {
  if (key.length <= chars * 2 + 3) return key;
  return `${key.slice(0, chars)}...${key.slice(-chars)}`;
}

export function formatTao(amount: number): string {
  if (amount < 0.001) return `${(amount * 1000).toFixed(2)}m\u03C4`;
  return `${amount.toFixed(4)} \u03C4`;
}

export function formatLatency(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
  return `${seconds.toFixed(1)}s`;
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatScore(value: number): string {
  return value.toFixed(3);
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
```

- [ ] **Step 3: Create `lib/mock-data.ts` — single source of all mock data**

This is a large file. It must mirror the backend structures exactly. Key data:

- `mockTasks`: 5 benchmark tasks from `benchmarks/v1.json`
- `mockMiners`: 8 miner profiles with realistic score distributions
- `mockValidators`: 3 validator profiles
- `mockNetworkStats`: current block/tempo/counts
- `mockAuditFlags`: 3 sample audit alerts
- `mockWorkflowResponses`: pre-built per-task miner DAG responses (3-5 per task)
- `mockExecutionResults`: step-by-step execution traces per task

```typescript
import type {
  BenchmarkTask, MinerProfile, ValidatorProfile, MinerResponse,
  ExecutionResult, AuditFlag, NetworkStats, WorkflowPlan, ScoreBreakdownData,
} from "./types";

// ── Benchmark Tasks (mirrors benchmarks/v1.json) ──────────────────

export const mockTasks: BenchmarkTask[] = [
  {
    task_id: "code_001",
    task_type: "code",
    status: "active",
    description: "Implement a Python function that merges two sorted lists into one sorted list without using built-in sort.",
    quality_criteria: { min_test_pass_rate: 0.8 },
    constraints: { max_budget_tao: 0.02, max_latency_seconds: 15, allowed_subnets: ["sn1", "sn4"] },
    available_tools: {
      sn1: { type: "text_generation", avg_cost: 0.001, avg_latency: 0.5 },
      sn4: { type: "code_generation", avg_cost: 0.003, avg_latency: 1.2 },
    },
    routing_policy: { default: { miner_selection: "top_k_stake_weighted", top_k: 3, aggregation: "majority_vote" } },
    reference: {
      test_suite: 'def test_merge():\n    from solution import merge_sorted\n    assert merge_sorted([1,3,5],[2,4,6]) == [1,2,3,4,5,6]',
    },
  },
  {
    task_id: "rag_001",
    task_type: "rag",
    status: "active",
    description: "What is Bittensor's consensus mechanism and how does Yuma Consensus differ from standard PoW?",
    quality_criteria: { min_rouge_l: 0.3 },
    constraints: { max_budget_tao: 0.01, max_latency_seconds: 10, allowed_subnets: ["sn1"] },
    available_tools: { sn1: { type: "text_generation", avg_cost: 0.001, avg_latency: 0.5 } },
    routing_policy: { default: { miner_selection: "top_k_stake_weighted", top_k: 3, aggregation: "majority_vote" } },
    reference: { reference_answer: "Bittensor uses Yuma Consensus which is a stake-weighted agreement mechanism..." },
  },
  {
    task_id: "agent_001",
    task_type: "agent",
    status: "deprecated",
    description: "Calculate compound interest for principal 1000, rate 5%, 3 years compounded annually. Return only the final amount.",
    quality_criteria: {},
    constraints: { max_budget_tao: 0.01, max_latency_seconds: 10, allowed_subnets: ["sn1"] },
    available_tools: { sn1: { type: "text_generation", avg_cost: 0.001, avg_latency: 0.5 } },
    routing_policy: { default: { miner_selection: "top_k_stake_weighted", top_k: 3, aggregation: "majority_vote" } },
    reference: { goal_checklist: [{ type: "regex", pattern: "1157\\.625" }] },
    deprecation_reason: "auto-lifecycle",
  },
  {
    task_id: "data_001",
    task_type: "data_transform",
    status: "deprecated",
    description: "Convert this CSV row to JSON: name,age,city\\nAlice,30,Delhi",
    quality_criteria: {},
    constraints: { max_budget_tao: 0.005, max_latency_seconds: 8, allowed_subnets: ["sn1"] },
    available_tools: { sn1: { type: "text_generation", avg_cost: 0.001, avg_latency: 0.5 } },
    routing_policy: { default: { miner_selection: "top_k_stake_weighted", top_k: 3, aggregation: "majority_vote" } },
    reference: { expected_output: '{"name":"Alice","age":"30","city":"Delhi"}' },
    deprecation_reason: "auto-lifecycle",
  },
  {
    task_id: "synthetic_001",
    task_type: "code",
    status: "active",
    description: "Implement a function that returns the nth Fibonacci number using memoization.",
    quality_criteria: {},
    constraints: { max_budget_tao: 0.02, max_latency_seconds: 15, allowed_subnets: ["sn1", "sn4"] },
    available_tools: {
      sn1: { type: "text_generation", avg_cost: 0.001, avg_latency: 0.5 },
      sn4: { type: "code_generation", avg_cost: 0.003, avg_latency: 1.2 },
    },
    routing_policy: { default: { miner_selection: "top_k_stake_weighted", top_k: 3, aggregation: "majority_vote" } },
    reference: { test_suite: "def test_fib():\n    from solution import fib\n    assert fib(10)==55" },
  },
];

// ── Helper: generate score history ────────────────────────────────

function generateScoreHistory(base: number, variance: number, count: number): number[] {
  return Array.from({ length: count }, () =>
    Math.max(0, Math.min(1, base + (Math.random() - 0.5) * variance))
  );
}

// ── Miner Profiles ────────────────────────────────────────────────

export const mockMiners: MinerProfile[] = [
  {
    uid: 1, hotkey: "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty", coldkey: "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
    role: "miner", stake: 1024.5, registration_block: 3_200_000, blocks_since_registration: 48_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 87,
    scores: { composite: 0.847, success: 0.92, cost: 0.78, latency: 0.81, reliability: 0.95 },
    score_history: generateScoreHistory(0.847, 0.08, 100), weight: 0.148, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0009, avg_latency: 0.45, reliability: 0.97, observations: 52 },
      sn4: { avg_cost: 0.0028, avg_latency: 1.1, reliability: 0.93, observations: 35 },
    },
    recent_workflows: [],
  },
  {
    uid: 2, hotkey: "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y", coldkey: "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
    role: "miner", stake: 890.2, registration_block: 3_210_000, blocks_since_registration: 38_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 72,
    scores: { composite: 0.812, success: 0.88, cost: 0.82, latency: 0.72, reliability: 0.90 },
    score_history: generateScoreHistory(0.812, 0.10, 100), weight: 0.139, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0010, avg_latency: 0.52, reliability: 0.94, observations: 45 },
      sn4: { avg_cost: 0.0031, avg_latency: 1.3, reliability: 0.89, observations: 27 },
    },
    recent_workflows: [],
  },
  {
    uid: 3, hotkey: "5DAAnrj7VHTznn2AWBemMuyBwZWs6FNFjdyVXUeYum3PTXFy", coldkey: "5HGjWAeFDfFCWPsjFQdVV2Msvz2XtMktvgocEZcCj68kUMaw",
    role: "miner", stake: 756.8, registration_block: 3_220_000, blocks_since_registration: 28_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 65,
    scores: { composite: 0.793, success: 0.85, cost: 0.75, latency: 0.78, reliability: 0.88 },
    score_history: generateScoreHistory(0.793, 0.09, 100), weight: 0.128, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0011, avg_latency: 0.48, reliability: 0.92, observations: 40 },
    },
    recent_workflows: [],
  },
  {
    uid: 4, hotkey: "5HpG9w8EBLe5XCrbczpwq5TSXvedjrBGCwqxK1iQ7qUsSWFc", coldkey: "5GNJqTPyNqANBkUVMN1LPPrxXnFouWA2MRQg3gKrUYgw6J9o",
    role: "miner", stake: 620.1, registration_block: 3_240_000, blocks_since_registration: 8_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 48,
    scores: { composite: 0.756, success: 0.80, cost: 0.71, latency: 0.74, reliability: 0.85 },
    score_history: generateScoreHistory(0.756, 0.12, 100), weight: 0.112, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0012, avg_latency: 0.55, reliability: 0.90, observations: 30 },
      sn4: { avg_cost: 0.0035, avg_latency: 1.4, reliability: 0.85, observations: 18 },
    },
    recent_workflows: [],
  },
  {
    uid: 5, hotkey: "5CiPPseXPECbkjWCa6MnjNokrgYjMqmKndv2rSneWj6VRnhk", coldkey: "5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y",
    role: "miner", stake: 510.3, registration_block: 3_243_000, blocks_since_registration: 5_000,
    immunity_active: true, immunity_blocks_remaining: 0, tasks_seen: 12,
    scores: { composite: 0.634, success: 0.72, cost: 0.65, latency: 0.58, reliability: 0.70 },
    score_history: generateScoreHistory(0.634, 0.15, 12), weight: 0.062, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0013, avg_latency: 0.60, reliability: 0.85, observations: 12 },
    },
    recent_workflows: [],
  },
  {
    uid: 6, hotkey: "5Ew3MyB15VprZrjQVkpDGq7BFYB3TsRXyoYuKSAdBGJe3me6", coldkey: "5DAAnrj7VHTznn2AWBemMuyBwZWs6FNFjdyVXUeYum3PTXFy",
    role: "miner", stake: 445.0, registration_block: 3_230_000, blocks_since_registration: 18_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 55,
    scores: { composite: 0.721, success: 0.78, cost: 0.68, latency: 0.69, reliability: 0.82 },
    score_history: generateScoreHistory(0.721, 0.11, 100), weight: 0.105, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0011, avg_latency: 0.51, reliability: 0.88, observations: 35 },
      sn4: { avg_cost: 0.0033, avg_latency: 1.35, reliability: 0.80, observations: 20 },
    },
    recent_workflows: [],
  },
  {
    uid: 7, hotkey: "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", coldkey: "5CiPPseXPECbkjWCa6MnjNokrgYjMqmKndv2rSneWj6VRnhk",
    role: "miner", stake: 380.7, registration_block: 3_235_000, blocks_since_registration: 13_000,
    immunity_active: false, immunity_blocks_remaining: 0, tasks_seen: 41,
    scores: { composite: 0.689, success: 0.75, cost: 0.62, latency: 0.66, reliability: 0.78 },
    score_history: generateScoreHistory(0.689, 0.13, 100), weight: 0.095, weight_capped: false,
    subnet_stats: {
      sn4: { avg_cost: 0.0034, avg_latency: 1.25, reliability: 0.82, observations: 41 },
    },
    recent_workflows: [],
  },
  {
    uid: 8, hotkey: "5HGjWAeFDfFCWPsjFQdVV2Msvz2XtMktvgocEZcCj68kUMaw", coldkey: "5Ew3MyB15VprZrjQVkpDGq7BFYB3TsRXyoYuKSAdBGJe3me6",
    role: "miner", stake: 290.4, registration_block: 3_244_000, blocks_since_registration: 4_000,
    immunity_active: true, immunity_blocks_remaining: 1_000, tasks_seen: 8,
    scores: { composite: 0.542, success: 0.60, cost: 0.55, latency: 0.48, reliability: 0.65 },
    score_history: generateScoreHistory(0.542, 0.18, 8), weight: 0.038, weight_capped: false,
    subnet_stats: {
      sn1: { avg_cost: 0.0014, avg_latency: 0.65, reliability: 0.78, observations: 8 },
    },
    recent_workflows: [],
  },
];

// ── Validator Profiles ────────────────────────────────────────────

export const mockValidators: ValidatorProfile[] = [
  { uid: 100, hotkey: "5GNJqTPyNqANBkUVMN1LPPrxXnFouWA2MRQg3gKrUYgw6J9o", coldkey: "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", role: "validator", stake: 15_200, vtrust: 0.95, last_weight_set_block: 3_247_500, scoring_version: "1.0.0", benchmark_version: "v1" },
  { uid: 101, hotkey: "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty", coldkey: "5HpG9w8EBLe5XCrbczpwq5TSXvedjrBGCwqxK1iQ7qUsSWFc", role: "validator", stake: 12_800, vtrust: 0.91, last_weight_set_block: 3_247_480, scoring_version: "1.0.0", benchmark_version: "v1" },
  { uid: 102, hotkey: "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", coldkey: "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM", role: "validator", stake: 9_500, vtrust: 0.87, last_weight_set_block: 3_247_450, scoring_version: "1.0.0", benchmark_version: "v1" },
];

// ── Network Stats ─────────────────────────────────────────────────

export const mockNetworkStats: NetworkStats = {
  current_block: 3_248_000,
  current_tempo: 9022,
  tasks_this_tempo: 24,
  active_miners: 8,
  active_validators: 3,
  tasks_evaluated: 1_847,
};

// ── Audit Flags ───────────────────────────────────────────────────

export const mockAuditFlags: AuditFlag[] = [
  { uid: 7, block: 3_247_800, score: 0.89, previous_avg: 0.52, jump_percent: 71.2, message: "Score jump >50% from rolling average" },
  { uid: 5, block: 3_247_600, score: 0.78, previous_avg: 0.45, jump_percent: 73.3, message: "Score jump >50% — new miner in warmup" },
  { uid: 4, block: 3_247_200, score: 0.91, previous_avg: 0.58, jump_percent: 56.9, message: "Score jump >50% from rolling average" },
];

// ── Workflow Responses (per task, 3-5 miner bids) ─────────────────

const codePlan: WorkflowPlan = {
  nodes: [
    { id: "step_1", subnet: "sn1", action: "analyze_requirements", estimated_cost: 0.001, estimated_latency: 0.5, tier: 0 },
    { id: "step_2", subnet: "sn4", action: "generate_code", estimated_cost: 0.003, estimated_latency: 1.2, error_handling: { retry_count: 2, timeout: 5 }, tier: 1 },
    { id: "step_3", subnet: "sn4", action: "generate_tests", estimated_cost: 0.002, estimated_latency: 1.0, tier: 1 },
    { id: "step_4", subnet: "sn1", action: "validate_output", estimated_cost: 0.001, estimated_latency: 0.5, tier: 2 },
  ],
  edges: [
    { from: "step_1", to: "step_2", data_ref: "${step_1.output.requirements}" },
    { from: "step_1", to: "step_3", data_ref: "${step_1.output.requirements}" },
    { from: "step_2", to: "step_4", data_ref: "${step_2.output.code}" },
    { from: "step_3", to: "step_4", data_ref: "${step_3.output.tests}" },
  ],
};

const ragPlan: WorkflowPlan = {
  nodes: [
    { id: "step_1", subnet: "sn1", action: "retrieve_context", estimated_cost: 0.001, estimated_latency: 0.5, tier: 0 },
    { id: "step_2", subnet: "sn1", action: "generate_answer", estimated_cost: 0.002, estimated_latency: 0.8, error_handling: { retry_count: 1, timeout: 4 }, tier: 1 },
    { id: "step_3", subnet: "sn1", action: "fact_check", estimated_cost: 0.001, estimated_latency: 0.5, tier: 2 },
  ],
  edges: [
    { from: "step_1", to: "step_2", data_ref: "${step_1.output.context}" },
    { from: "step_2", to: "step_3", data_ref: "${step_2.output.answer}" },
  ],
};

export const mockWorkflowResponses: Record<string, MinerResponse[]> = {
  code_001: [
    { miner_uid: 1, hotkey: "5FHneW46...694ty", scoring_version: "1.0.0", workflow_plan: codePlan, total_estimated_cost: 0.007, total_estimated_latency: 3.2, confidence: 0.92, reasoning: "Two-phase approach: parallel code gen + test gen on SN4, then validate on SN1. Retry on code gen for reliability.", composite_score: 0.847 },
    { miner_uid: 2, hotkey: "5FLSigC9...cS59Y", scoring_version: "1.0.0", workflow_plan: { ...codePlan, nodes: codePlan.nodes.map(n => ({ ...n, estimated_cost: n.estimated_cost * 1.2 })) }, total_estimated_cost: 0.0084, total_estimated_latency: 3.8, confidence: 0.87, reasoning: "Sequential pipeline: requirements → code → tests → validation. Higher cost but more thorough.", composite_score: 0.812 },
    { miner_uid: 3, hotkey: "5DAAnrj7...TXFy", scoring_version: "1.0.0", workflow_plan: { nodes: codePlan.nodes.slice(0, 2), edges: [codePlan.edges[0]] }, total_estimated_cost: 0.004, total_estimated_latency: 1.7, confidence: 0.78, reasoning: "Minimal approach: analyze then generate. Fast and cheap.", composite_score: 0.793 },
    { miner_uid: 6, hotkey: "5Ew3MyB1...3me6", scoring_version: "1.0.0", workflow_plan: codePlan, total_estimated_cost: 0.009, total_estimated_latency: 4.1, confidence: 0.71, reasoning: "Full pipeline with validation. Conservative cost estimates.", composite_score: 0.721 },
  ],
  rag_001: [
    { miner_uid: 1, hotkey: "5FHneW46...694ty", scoring_version: "1.0.0", workflow_plan: ragPlan, total_estimated_cost: 0.004, total_estimated_latency: 1.8, confidence: 0.94, reasoning: "Retrieve context → generate → fact-check pipeline.", composite_score: 0.860 },
    { miner_uid: 2, hotkey: "5FLSigC9...cS59Y", scoring_version: "1.0.0", workflow_plan: ragPlan, total_estimated_cost: 0.005, total_estimated_latency: 2.1, confidence: 0.88, reasoning: "RAG pipeline with extended context retrieval.", composite_score: 0.825 },
    { miner_uid: 4, hotkey: "5HpG9w8E...SWFc", scoring_version: "1.0.0", workflow_plan: { nodes: ragPlan.nodes.slice(0, 2), edges: [ragPlan.edges[0]] }, total_estimated_cost: 0.003, total_estimated_latency: 1.3, confidence: 0.80, reasoning: "Direct retrieval and generation, skip fact-check for speed.", composite_score: 0.756 },
  ],
  agent_001: [
    { miner_uid: 1, hotkey: "5FHneW46...694ty", scoring_version: "1.0.0", workflow_plan: { nodes: [{ id: "step_1", subnet: "sn1", action: "compute", estimated_cost: 0.001, estimated_latency: 0.5, tier: 0 }, { id: "step_2", subnet: "sn1", action: "verify", estimated_cost: 0.001, estimated_latency: 0.3, tier: 1 }], edges: [{ from: "step_1", to: "step_2", data_ref: "${step_1.output.result}" }] }, total_estimated_cost: 0.002, total_estimated_latency: 0.8, confidence: 0.96, reasoning: "Simple compute + verify for arithmetic.", composite_score: 0.890 },
  ],
  data_001: [
    { miner_uid: 2, hotkey: "5FLSigC9...cS59Y", scoring_version: "1.0.0", workflow_plan: { nodes: [{ id: "step_1", subnet: "sn1", action: "parse_csv", estimated_cost: 0.001, estimated_latency: 0.3, tier: 0 }, { id: "step_2", subnet: "sn1", action: "transform_to_json", estimated_cost: 0.001, estimated_latency: 0.3, tier: 1 }], edges: [{ from: "step_1", to: "step_2", data_ref: "${step_1.output.parsed}" }] }, total_estimated_cost: 0.002, total_estimated_latency: 0.6, confidence: 0.95, reasoning: "Parse then transform pipeline.", composite_score: 0.870 },
  ],
  synthetic_001: [
    { miner_uid: 1, hotkey: "5FHneW46...694ty", scoring_version: "1.0.0", workflow_plan: codePlan, total_estimated_cost: 0.007, total_estimated_latency: 3.2, confidence: 0.91, reasoning: "Full code generation pipeline with tests.", composite_score: 0.840 },
  ],
};

// ── Execution Results ─────────────────────────────────────────────

export const mockExecutionResults: Record<string, ExecutionResult> = {
  code_001: {
    steps: [
      { node_id: "step_1", status: "completed", output: "Requirements: merge two sorted lists, O(n) time, no built-in sort", cost: 0.0009, latency: 0.45 },
      { node_id: "step_2", status: "completed", output: "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result", cost: 0.0028, latency: 1.1 },
      { node_id: "step_3", status: "completed", output: "3 tests generated: empty, single, multiple elements", cost: 0.0019, latency: 0.95 },
      { node_id: "step_4", status: "completed", output: "All tests passed. Output validated.", cost: 0.0008, latency: 0.42 },
    ],
    final_output: "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result",
    total_cost: 0.0064,
    total_latency: 2.92,
    scores: { composite: 0.847, success: 0.92, cost: 0.78, latency: 0.81, reliability: 0.95 },
  },
  rag_001: {
    steps: [
      { node_id: "step_1", status: "completed", output: "Retrieved: Yuma Consensus documentation, validator scoring mechanism, PoW comparison", cost: 0.0009, latency: 0.48 },
      { node_id: "step_2", status: "completed", output: "Bittensor uses Yuma Consensus, a stake-weighted agreement mechanism where validators assign scores to miners based on the quality of their work...", cost: 0.0018, latency: 0.75 },
      { node_id: "step_3", status: "completed", output: "Fact-check passed: key claims verified against documentation", cost: 0.0008, latency: 0.40 },
    ],
    final_output: "Bittensor uses Yuma Consensus, a stake-weighted agreement mechanism where validators assign scores to miners based on the quality of their work. Unlike Proof of Work (PoW) which requires miners to expend computational energy solving cryptographic puzzles, Yuma Consensus rewards useful machine learning work evaluated by validator peers.",
    total_cost: 0.0035,
    total_latency: 1.63,
    scores: { composite: 0.860, success: 0.94, cost: 0.65, latency: 0.84, reliability: 0.98 },
  },
};

// ── Task Performance History (mock per-tempo averages) ────────────

export const mockTaskPerformance: Record<string, number[]> = {
  code_001: [0.72, 0.74, 0.76, 0.78, 0.80, 0.81, 0.82, 0.83, 0.84, 0.84, 0.85, 0.85],
  rag_001: [0.68, 0.71, 0.73, 0.75, 0.77, 0.79, 0.80, 0.82, 0.83, 0.84, 0.85, 0.86],
  agent_001: [0.88, 0.89, 0.90, 0.91, 0.91, 0.92, 0.92, 0.92, 0.93, 0.93, 0.93, 0.93],
  data_001: [0.04, 0.05, 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.08, 0.09, 0.09, 0.09],
  synthetic_001: [0.70, 0.73, 0.75, 0.77, 0.79, 0.80, 0.81, 0.82, 0.83, 0.83, 0.84, 0.84],
};
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/
git commit -m "feat(frontend): add TypeScript types, mock data, and utility helpers"
```

---

## Task 3: Navigation & Shared UI Components

**Files:**
- Create: `frontend/components/nav.tsx`
- Create: `frontend/components/task-type-icon.tsx`
- Create: `frontend/components/lifecycle-badge.tsx`
- Create: `frontend/components/block-counter.tsx`
- Create: `frontend/components/stat-card.tsx`
- Create: `frontend/components/subnet-chip.tsx`

- [ ] **Step 1: Create `components/nav.tsx` — top navigation bar**

Minimal top nav with logo, page links, and block counter. Full-bleed on dark canvas, no sidebar. Active link indicated with teal underline.

```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BlockCounter } from "./block-counter";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Network" },
  { href: "/submit", label: "Submit Task" },
  { href: "/explorer", label: "Explorer" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-[--color-border] bg-[--color-canvas]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-mono text-sm font-bold tracking-tight text-[--color-teal]">
            C-SWON
          </Link>
          <div className="flex items-center gap-1">
            {links.map(({ href, label }) => {
              const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-[--color-teal]/10 text-[--color-teal]"
                      : "text-[--color-ink-secondary] hover:text-[--color-ink]"
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
        <BlockCounter />
      </div>
    </nav>
  );
}
```

- [ ] **Step 2: Create `components/block-counter.tsx`**

Auto-incrementing block number that ticks every ~12s (1 block time). Monospace, teal accent.

```tsx
"use client";
import { useState, useEffect } from "react";
import { mockNetworkStats } from "@/lib/mock-data";

export function BlockCounter() {
  const [block, setBlock] = useState(mockNetworkStats.current_block);

  useEffect(() => {
    const interval = setInterval(() => setBlock((b) => b + 1), 12_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span className="h-1.5 w-1.5 rounded-full bg-[--color-teal] animate-pulse" />
      <span className="text-[--color-ink-tertiary]">Block</span>
      <span className="text-[--color-ink-secondary] tabular-nums">{block.toLocaleString()}</span>
    </div>
  );
}
```

- [ ] **Step 3: Create `components/task-type-icon.tsx`**

Monospace badge with colored background per task type.

```tsx
import type { TaskType } from "@/lib/types";
import { cn } from "@/lib/utils";

const config: Record<TaskType, { label: string; className: string }> = {
  code: { label: "</>", className: "bg-[--color-teal]/15 text-[--color-teal]" },
  rag: { label: "RAG", className: "bg-purple-500/15 text-purple-400" },
  agent: { label: "AGT", className: "bg-[--color-gold]/15 text-[--color-gold]" },
  data_transform: { label: "DTX", className: "bg-blue-500/15 text-blue-400" },
};

export function TaskTypeIcon({ type, size = "sm" }: { type: TaskType; size?: "sm" | "md" }) {
  const { label, className } = config[type];
  return (
    <span className={cn(
      "inline-flex items-center justify-center rounded font-mono font-bold",
      size === "sm" ? "h-6 px-1.5 text-[10px]" : "h-8 px-2 text-xs",
      className
    )}>
      {label}
    </span>
  );
}
```

- [ ] **Step 4: Create `components/lifecycle-badge.tsx`**

```tsx
import type { LifecycleStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<LifecycleStatus, string> = {
  active: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  quarantined: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  deprecated: "bg-[--color-ink-muted]/15 text-[--color-ink-tertiary] border-[--color-ink-muted]/20",
};

export function LifecycleBadge({ status }: { status: LifecycleStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider", styles[status])}>
      {status}
    </span>
  );
}
```

- [ ] **Step 5: Create `components/stat-card.tsx`**

```tsx
import { cn } from "@/lib/utils";

export function StatCard({
  label, value, sublabel, accent = false,
}: {
  label: string; value: string | number; sublabel?: string; accent?: boolean;
}) {
  return (
    <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4">
      <p className="text-[11px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]">{label}</p>
      <p className={cn(
        "mt-1 font-mono text-2xl font-bold tabular-nums",
        accent ? "text-[--color-teal]" : "text-[--color-ink]"
      )}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {sublabel && <p className="mt-1 text-xs text-[--color-ink-tertiary]">{sublabel}</p>}
    </div>
  );
}
```

- [ ] **Step 6: Create `components/subnet-chip.tsx`**

```tsx
import { cn } from "@/lib/utils";

export function SubnetChip({ subnet, selected, onClick }: { subnet: string; selected?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 font-mono text-xs transition-colors",
        selected
          ? "border-[--color-teal]/40 bg-[--color-teal]/15 text-[--color-teal]"
          : "border-[--color-border] bg-[--color-surface-1] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
      )}
    >
      {subnet}
    </button>
  );
}
```

- [ ] **Step 7: Update `app/layout.tsx` to include Nav**

```tsx
import { Nav } from "@/components/nav";
// ... existing imports ...

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Nav />
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 8: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/ frontend/app/layout.tsx
git commit -m "feat(frontend): add navigation, shared UI components, and design tokens"
```

---

## Task 4: Score Components (ScoreBreakdown, ScoreGauge, WeightBar)

**Files:**
- Create: `frontend/components/score-breakdown.tsx`
- Create: `frontend/components/score-gauge.tsx`
- Create: `frontend/components/weight-bar.tsx`

- [ ] **Step 1: Create `components/score-breakdown.tsx`**

Four horizontal bars showing composite score breakdown. Each bar fills to its value with the dimension's weight shown.

```tsx
import { scoring } from "@/lib/constants";
import type { ScoreBreakdownData } from "@/lib/types";
import { formatScore } from "@/lib/utils";

const dimensions: { key: keyof Omit<ScoreBreakdownData, "composite">; label: string; color: string }[] = [
  { key: "success", label: "Success", color: "bg-emerald-400" },
  { key: "cost", label: "Cost", color: "bg-[--color-gold]" },
  { key: "latency", label: "Latency", color: "bg-[--color-teal]" },
  { key: "reliability", label: "Reliability", color: "bg-purple-400" },
];

export function ScoreBreakdown({ scores, showComposite = true }: { scores: ScoreBreakdownData; showComposite?: boolean }) {
  return (
    <div className="space-y-3">
      {showComposite && (
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-3xl font-bold text-[--color-ink]">{formatScore(scores.composite)}</span>
          <span className="text-xs text-[--color-ink-tertiary]">composite</span>
        </div>
      )}
      <div className="space-y-2">
        {dimensions.map(({ key, label, color }) => {
          const value = scores[key];
          const weight = scoring.weights[key];
          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[--color-ink-secondary]">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[--color-ink-tertiary]">{(weight * 100).toFixed(0)}%</span>
                  <span className="font-mono text-[--color-ink] tabular-nums">{formatScore(value)}</span>
                </div>
              </div>
              <div className="h-1.5 rounded-full bg-[--color-surface-3]">
                <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${value * 100}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `components/score-gauge.tsx`**

Semi-circular gauge with SVG arc for a single score dimension.

```tsx
"use client";
import { formatScore } from "@/lib/utils";

const colorMap: Record<string, string> = {
  success: "#22c55e",
  cost: "#f0b429",
  latency: "#00d4aa",
  reliability: "#a78bfa",
};

export function ScoreGauge({ value, dimension, size = 80 }: { value: number; dimension: string; size?: number }) {
  const color = colorMap[dimension] ?? "#00d4aa";
  const radius = (size - 8) / 2;
  const circumference = Math.PI * radius; // semicircle
  const offset = circumference * (1 - value);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
        {/* Background arc */}
        <path
          d={`M 4 ${center} A ${radius} ${radius} 0 0 1 ${size - 4} ${center}`}
          fill="none" stroke="var(--color-surface-3)" strokeWidth={4} strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M 4 ${center} A ${radius} ${radius} 0 0 1 ${size - 4} ${center}`}
          fill="none" stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <span className="font-mono text-sm font-bold tabular-nums text-[--color-ink]">{formatScore(value)}</span>
      <span className="text-[10px] uppercase tracking-wider text-[--color-ink-tertiary]">{dimension}</span>
    </div>
  );
}
```

- [ ] **Step 3: Create `components/weight-bar.tsx`**

Horizontal bar with a 15% cap indicator line.

```tsx
import { scoring } from "@/lib/constants";
import { formatPercent } from "@/lib/utils";

export function WeightBar({ weight, capped }: { weight: number; capped: boolean }) {
  const capPercent = scoring.maxMinerWeight * 100;
  return (
    <div className="space-y-1">
      <div className="relative h-2 rounded-full bg-[--color-surface-3]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${capped ? "bg-[--color-gold]" : "bg-[--color-teal]"}`}
          style={{ width: `${Math.min(weight * 100 / 0.20, 100)}%` }}
        />
        {/* 15% cap line */}
        <div
          className="absolute top-[-2px] h-[calc(100%+4px)] w-px bg-[--color-ink-tertiary]"
          style={{ left: `${capPercent / 0.20 * 100}%` }}
          title="15% cap"
        />
      </div>
      <div className="flex items-center justify-between text-[10px]">
        <span className="font-mono tabular-nums text-[--color-ink-secondary]">{formatPercent(weight)}</span>
        {capped && <span className="text-[--color-gold]">capped</span>}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/score-breakdown.tsx frontend/components/score-gauge.tsx frontend/components/weight-bar.tsx
git commit -m "feat(frontend): add score breakdown, gauge, and weight bar components"
```

---

## Task 5: DAG Viewer Component

**Files:**
- Create: `frontend/components/dag-viewer.tsx`

- [ ] **Step 1: Create `components/dag-viewer.tsx` using ReactFlow**

The centerpiece — interactive DAG with colored nodes per subnet, animated edges, step status overlays. Nodes show step ID, action, subnet, cost, and latency. Edges labeled with DataRef strings.

```tsx
"use client";
import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  type Node,
  type Edge,
  Position,
  Handle,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { WorkflowPlan, StepStatus } from "@/lib/types";
import { formatTao, formatLatency, cn } from "@/lib/utils";

const subnetColors: Record<string, string> = {
  sn1: "#00d4aa",
  sn4: "#a78bfa",
  sn8: "#f0b429",
};

const statusStyles: Record<StepStatus, string> = {
  pending: "border-[--color-border-emphasis]",
  running: "border-[--color-teal] ring-1 ring-[--color-teal]/30",
  completed: "border-emerald-500/50",
  failed: "border-red-500/50",
};

function DagNode({ data }: NodeProps) {
  const node = data as { label: string; subnet: string; action: string; cost: number; latency: number; status: StepStatus; retries?: number; timeout?: number };
  const color = subnetColors[node.subnet] ?? "#8a94a8";

  return (
    <div className={cn(
      "rounded-lg border bg-[--color-surface-1] p-3 min-w-[160px] transition-all duration-300",
      statusStyles[node.status ?? "pending"]
    )}>
      <Handle type="target" position={Position.Top} className="!bg-[--color-ink-muted] !border-none !w-2 !h-2" />
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] text-[--color-ink-tertiary]">{node.label}</span>
        <span className="rounded px-1.5 py-0.5 font-mono text-[10px] font-medium" style={{ backgroundColor: `${color}20`, color }}>
          {node.subnet}
        </span>
      </div>
      <p className="mt-1 text-xs font-medium text-[--color-ink]">{node.action}</p>
      <div className="mt-2 flex items-center gap-3 text-[10px] text-[--color-ink-tertiary]">
        <span className="font-mono tabular-nums">{formatTao(node.cost)}</span>
        <span className="font-mono tabular-nums">{formatLatency(node.latency)}</span>
      </div>
      {node.retries && (
        <div className="mt-1 flex items-center gap-1 text-[10px] text-[--color-ink-muted]">
          <span>retry:{node.retries}</span>
          {node.timeout && <span>timeout:{node.timeout}s</span>}
        </div>
      )}
      {node.status === "running" && (
        <div className="mt-2 h-0.5 rounded-full bg-[--color-surface-3] overflow-hidden">
          <div className="h-full w-1/2 rounded-full bg-[--color-teal] animate-pulse" />
        </div>
      )}
      {node.status === "completed" && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-400">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
          done
        </div>
      )}
      {node.status === "failed" && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-red-400">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          failed
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-[--color-ink-muted] !border-none !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = { dag: DagNode };

interface DagViewerProps {
  plan: WorkflowPlan;
  stepStatuses?: Record<string, StepStatus>;
  className?: string;
}

export function DagViewer({ plan, stepStatuses = {}, className }: DagViewerProps) {
  // Layout: position nodes by tier (y-axis) and index within tier (x-axis)
  const { nodes, edges } = useMemo(() => {
    const tiers: Record<number, typeof plan.nodes> = {};
    for (const node of plan.nodes) {
      (tiers[node.tier] ??= []).push(node);
    }

    const layoutNodes: Node[] = [];
    const xSpacing = 220;
    const ySpacing = 140;

    for (const [tierStr, tierNodes] of Object.entries(tiers)) {
      const tier = Number(tierStr);
      const totalWidth = (tierNodes.length - 1) * xSpacing;
      const startX = -totalWidth / 2;

      tierNodes.forEach((node, idx) => {
        layoutNodes.push({
          id: node.id,
          type: "dag",
          position: { x: startX + idx * xSpacing, y: tier * ySpacing },
          data: {
            label: node.id,
            subnet: node.subnet,
            action: node.action,
            cost: node.estimated_cost,
            latency: node.estimated_latency,
            status: stepStatuses[node.id] ?? "pending",
            retries: node.error_handling?.retry_count,
            timeout: node.error_handling?.timeout,
          },
        });
      });
    }

    const layoutEdges: Edge[] = plan.edges.map((edge, i) => ({
      id: `e-${i}`,
      source: edge.from,
      target: edge.to,
      label: edge.data_ref,
      animated: stepStatuses[edge.from] === "running" || stepStatuses[edge.from] === "completed",
      style: { stroke: "var(--color-ink-muted)", strokeWidth: 1.5 },
      labelStyle: { fill: "var(--color-ink-tertiary)", fontSize: 9, fontFamily: "var(--font-mono)" },
      labelBgStyle: { fill: "var(--color-surface-0)", fillOpacity: 0.8 },
    }));

    return { nodes: layoutNodes, edges: layoutEdges };
  }, [plan, stepStatuses]);

  return (
    <div className={cn("h-[400px] rounded-lg border border-[--color-border] bg-[--color-surface-0]", className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="var(--color-ink-muted)" gap={24} size={1} style={{ opacity: 0.3 }} />
      </ReactFlow>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/dag-viewer.tsx
git commit -m "feat(frontend): add interactive DAG viewer with ReactFlow"
```

---

## Task 6: Miner Card & Step Animator Components

**Files:**
- Create: `frontend/components/miner-card.tsx`
- Create: `frontend/components/step-animator.tsx`

- [ ] **Step 1: Create `components/miner-card.tsx`**

Card showing miner response during competition view. Highlighted state for "best plan".

```tsx
import type { MinerResponse } from "@/lib/types";
import { truncateKey, formatTao, formatLatency, formatScore, cn } from "@/lib/utils";

export function MinerCard({ response, isBest = false }: { response: MinerResponse; isBest?: boolean }) {
  return (
    <div className={cn(
      "rounded-lg border p-4 transition-all",
      isBest
        ? "border-[--color-teal]/40 bg-[--color-teal]/5"
        : "border-[--color-border] bg-[--color-surface-1]"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-[--color-ink]">UID {response.miner_uid}</span>
          <span className="font-mono text-[10px] text-[--color-ink-tertiary]">{truncateKey(response.hotkey)}</span>
        </div>
        {isBest && (
          <span className="rounded-full bg-[--color-teal]/15 px-2 py-0.5 text-[10px] font-medium text-[--color-teal]">
            Best Plan
          </span>
        )}
      </div>
      <div className="mt-3 grid grid-cols-4 gap-3">
        <div>
          <p className="text-[10px] text-[--color-ink-tertiary]">Confidence</p>
          <p className="font-mono text-sm font-bold tabular-nums text-[--color-ink]">{formatScore(response.confidence)}</p>
        </div>
        <div>
          <p className="text-[10px] text-[--color-ink-tertiary]">Est. Cost</p>
          <p className="font-mono text-sm tabular-nums text-[--color-gold]">{formatTao(response.total_estimated_cost)}</p>
        </div>
        <div>
          <p className="text-[10px] text-[--color-ink-tertiary]">Est. Latency</p>
          <p className="font-mono text-sm tabular-nums text-[--color-ink-secondary]">{formatLatency(response.total_estimated_latency)}</p>
        </div>
        <div>
          <p className="text-[10px] text-[--color-ink-tertiary]">DAG Nodes</p>
          <p className="font-mono text-sm tabular-nums text-[--color-ink-secondary]">{response.workflow_plan.nodes.length}</p>
        </div>
      </div>
      <p className="mt-3 text-xs leading-relaxed text-[--color-ink-secondary]">{response.reasoning}</p>
    </div>
  );
}
```

- [ ] **Step 2: Create `components/step-animator.tsx`**

Manages execution animation state. Takes a plan, triggers tier-by-tier progression with realistic delays, and reports status changes.

```tsx
"use client";
import { useState, useCallback } from "react";
import type { WorkflowPlan, StepStatus } from "@/lib/types";

interface StepAnimatorState {
  statuses: Record<string, StepStatus>;
  isRunning: boolean;
  isComplete: boolean;
  currentCost: number;
  currentLatency: number;
}

export function useStepAnimator(plan: WorkflowPlan) {
  const [state, setState] = useState<StepAnimatorState>({
    statuses: {},
    isRunning: false,
    isComplete: false,
    currentCost: 0,
    currentLatency: 0,
  });

  const execute = useCallback(async () => {
    setState((s) => ({ ...s, isRunning: true, isComplete: false, statuses: {}, currentCost: 0, currentLatency: 0 }));

    // Group nodes by tier
    const tiers: Record<number, typeof plan.nodes> = {};
    for (const node of plan.nodes) {
      (tiers[node.tier] ??= []).push(node);
    }

    const sortedTiers = Object.keys(tiers).map(Number).sort((a, b) => a - b);
    let totalCost = 0;
    let totalLatency = 0;

    for (const tier of sortedTiers) {
      const tierNodes = tiers[tier];

      // Set all nodes in tier to "running"
      setState((s) => {
        const newStatuses = { ...s.statuses };
        for (const node of tierNodes) newStatuses[node.id] = "running";
        return { ...s, statuses: newStatuses };
      });

      // Simulate execution (max latency of parallel nodes)
      const maxLatency = Math.max(...tierNodes.map((n) => n.estimated_latency));
      await new Promise((r) => setTimeout(r, maxLatency * 1000 + 500));

      // Complete all nodes in tier
      const tierCost = tierNodes.reduce((sum, n) => sum + n.estimated_cost, 0);
      totalCost += tierCost;
      totalLatency += maxLatency;

      setState((s) => {
        const newStatuses = { ...s.statuses };
        for (const node of tierNodes) newStatuses[node.id] = "completed";
        return { ...s, statuses: newStatuses, currentCost: totalCost, currentLatency: totalLatency };
      });

      // Brief pause between tiers
      await new Promise((r) => setTimeout(r, 300));
    }

    setState((s) => ({ ...s, isRunning: false, isComplete: true }));
  }, [plan]);

  return { ...state, execute };
}
```

- [ ] **Step 3: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/miner-card.tsx frontend/components/step-animator.tsx
git commit -m "feat(frontend): add miner card and step animator components"
```

---

## Task 7: Sortable Data Table Component

**Files:**
- Create: `frontend/components/data-table.tsx`

- [ ] **Step 1: Create `components/data-table.tsx`**

Generic sortable table with monospace data cells, hover states, and optional click handler.

```tsx
"use client";
import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";

interface Column<T> {
  key: string;
  label: string;
  render: (row: T) => React.ReactNode;
  sortValue?: (row: T) => number | string;
  align?: "left" | "right" | "center";
  mono?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  keyField: keyof T;
}

export function DataTable<T>({ columns, data, onRowClick, keyField }: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return data;
    return [...data].sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      const cmp = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir, columns]);

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-[--color-border]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[--color-border] bg-[--color-surface-1]">
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => col.sortValue && handleSort(col.key)}
                className={cn(
                  "px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]",
                  col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                  col.sortValue && "cursor-pointer hover:text-[--color-ink-secondary]"
                )}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {sortKey === col.key && (
                    <span className="text-[--color-teal]">{sortDir === "asc" ? "\u2191" : "\u2193"}</span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={String(row[keyField])}
              onClick={() => onRowClick?.(row)}
              className={cn(
                "border-b border-[--color-border] bg-[--color-surface-0] transition-colors",
                onRowClick && "cursor-pointer hover:bg-[--color-surface-1]"
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-4 py-3",
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                    col.mono && "font-mono tabular-nums"
                  )}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/data-table.tsx
git commit -m "feat(frontend): add generic sortable data table component"
```

---

## Task 8: Emission Sankey Diagram

**Files:**
- Create: `frontend/components/emission-sankey.tsx`

- [ ] **Step 1: Create `components/emission-sankey.tsx`**

Custom SVG flow diagram showing emission split (18% owner, 41% miners, 41% validators). Uses animated paths with gradient fills. Not a library Sankey — hand-drawn SVG for precise control.

```tsx
"use client";
import { motion } from "framer-motion";

const flows = [
  { label: "Owner", percent: 18, color: "#a78bfa", y: 0 },
  { label: "Miners", percent: 41, color: "#00d4aa", y: 1 },
  { label: "Validators + Stakers", percent: 41, color: "#f0b429", y: 2 },
];

export function EmissionSankey() {
  const height = 200;
  const width = 500;
  const barWidth = 24;
  const sourceX = 60;
  const targetX = width - 120;
  const sourceHeight = height - 40;
  const sourceY = 20;

  return (
    <div className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
      <h3 className="mb-4 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Emission Flow</h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxWidth: 500 }}>
        {/* Source bar */}
        <rect x={sourceX} y={sourceY} width={barWidth} height={sourceHeight} rx={4} fill="var(--color-surface-2)" />
        <text x={sourceX + barWidth / 2} y={sourceY - 6} textAnchor="middle" className="fill-[--color-ink-secondary] text-[10px]" style={{ font: "10px var(--font-mono)" }}>
          \u0394\u03B1
        </text>

        {/* Flow paths */}
        {flows.map((flow, i) => {
          const flowHeight = (sourceHeight * flow.percent) / 100;
          const flowSourceY = sourceY + flows.slice(0, i).reduce((sum, f) => sum + (sourceHeight * f.percent) / 100, 0);
          const targetY = 20 + i * 60;
          const targetHeight = 36;

          const path = `M ${sourceX + barWidth} ${flowSourceY + flowHeight / 2}
            C ${sourceX + barWidth + 80} ${flowSourceY + flowHeight / 2},
              ${targetX - 80} ${targetY + targetHeight / 2},
              ${targetX} ${targetY + targetHeight / 2}`;

          return (
            <g key={flow.label}>
              <motion.path
                d={path}
                fill="none"
                stroke={flow.color}
                strokeWidth={flowHeight * 0.6}
                strokeOpacity={0.15}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.2 }}
              />
              <motion.path
                d={path}
                fill="none"
                stroke={flow.color}
                strokeWidth={2}
                strokeOpacity={0.5}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.2 }}
              />
              {/* Target bar */}
              <rect x={targetX} y={targetY} width={barWidth} height={targetHeight} rx={4} fill={flow.color} fillOpacity={0.2} />
              <text x={targetX + barWidth + 8} y={targetY + 14} className="fill-[--color-ink]" style={{ font: "12px var(--font-sans)" }}>
                {flow.label}
              </text>
              <text x={targetX + barWidth + 8} y={targetY + 28} className="fill-[--color-ink-tertiary]" style={{ font: "11px var(--font-mono)" }}>
                {flow.percent}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/components/emission-sankey.tsx
git commit -m "feat(frontend): add animated emission sankey flow diagram"
```

---

## Task 9: Landing Page (`/`)

**Files:**
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Build landing page with all 6 sections**

Hero, How It Works, Scoring Formula, Emission Structure, Network Stats, Footer. Full implementation with animations, mock data counters.

```tsx
"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { mockNetworkStats } from "@/lib/mock-data";
import { StatCard } from "@/components/stat-card";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { EmissionSankey } from "@/components/emission-sankey";
import { BlockCounter } from "@/components/block-counter";
import { scoring } from "@/lib/constants";

const steps = [
  { num: "01", title: "Describe a Task", desc: "User submits a complex AI task — code generation, RAG, agent workflow, or data transformation.", color: "text-[--color-teal]" },
  { num: "02", title: "Miners Compete", desc: "Miners design optimized multi-subnet workflow DAGs. Each plan routes work across specialized subnets.", color: "text-[--color-gold]" },
  { num: "03", title: "Validate & Reward", desc: "Validators execute, score on success/cost/latency/reliability, and reward the best orchestration strategies.", color: "text-purple-400" },
];

const scoreDimensions = [
  { label: "Success", weight: "50%", desc: "Output quality x completion ratio — did the workflow produce correct results?", color: "bg-emerald-400" },
  { label: "Cost", weight: "25%", desc: "Budget efficiency — how much TAO was spent vs. the maximum allowed?", color: "bg-[--color-gold]" },
  { label: "Latency", weight: "15%", desc: "Speed — how quickly did the workflow complete vs. the deadline?", color: "bg-[--color-teal]" },
  { label: "Reliability", weight: "10%", desc: "Fault tolerance — how few retries, timeouts, or failures occurred?", color: "bg-purple-400" },
];

export default function LandingPage() {
  return (
    <div className="space-y-24 pb-24">
      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="pt-16 text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <p className="font-mono text-sm text-[--color-teal]">Bittensor Subnet</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-[--color-ink] sm:text-5xl">
            Zapier for Subnets
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-[--color-ink-secondary]">
            The Intelligence Layer for Multi-Subnet Composition. Turn any complex AI task into an optimized multi-subnet workflow.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link href="/submit" className="rounded-lg bg-[--color-teal] px-6 py-2.5 text-sm font-medium text-[--color-canvas] transition-opacity hover:opacity-90">
              Try a Task
            </Link>
            <Link href="/dashboard" className="rounded-lg border border-[--color-border-emphasis] px-6 py-2.5 text-sm font-medium text-[--color-ink-secondary] transition-colors hover:text-[--color-ink]">
              View Network
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── How It Works ───────────────────────────────────── */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">How It Works</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6"
            >
              <span className={`font-mono text-2xl font-bold ${step.color}`}>{step.num}</span>
              <h3 className="mt-3 text-lg font-semibold text-[--color-ink]">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[--color-ink-secondary]">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Scoring Formula ────────────────────────────────── */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Scoring Formula</h2>
        <div className="mx-auto mt-4 max-w-2xl rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <p className="text-center font-mono text-sm text-[--color-ink-secondary]">
            S = 0.50 x Success + 0.25 x Cost + 0.15 x Latency + 0.10 x Reliability
          </p>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {scoreDimensions.map((dim) => (
            <div key={dim.label} className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4">
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${dim.color}`} />
                <span className="text-sm font-medium text-[--color-ink]">{dim.label}</span>
                <span className="ml-auto font-mono text-xs text-[--color-ink-tertiary]">{dim.weight}</span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-[--color-ink-secondary]">{dim.desc}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-[--color-ink-tertiary]">
          Success gate: Cost & latency only count if success &gt; 70%
        </p>
      </section>

      {/* ── Emission Structure ─────────────────────────────── */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Emission Structure</h2>
        <div className="mx-auto mt-6 max-w-lg">
          <EmissionSankey />
        </div>
        <p className="mt-4 text-center text-xs text-[--color-ink-secondary]">
          dTAO Alpha token model — TAO injected into AMM pool, Alpha distributed via Yuma Consensus
        </p>
      </section>

      {/* ── Network Stats ──────────────────────────────────── */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Network Stats</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard label="Active Miners" value={mockNetworkStats.active_miners} accent />
          <StatCard label="Active Validators" value={mockNetworkStats.active_validators} />
          <StatCard label="Tasks Evaluated" value={mockNetworkStats.tasks_evaluated} accent />
          <StatCard label="Current Tempo" value={mockNetworkStats.current_tempo} sublabel={`${mockNetworkStats.current_tempo} x 360 blocks`} />
          <StatCard label="Current Block" value={mockNetworkStats.current_block} />
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="border-t border-[--color-border] pt-8 text-center text-xs text-[--color-ink-tertiary]">
        <div className="flex items-center justify-center gap-6">
          <a href="https://github.com/adysingh5711/C-SWON" target="_blank" rel="noopener noreferrer" className="hover:text-[--color-ink-secondary]">GitHub</a>
          <a href="https://docs.learnbittensor.org" target="_blank" rel="noopener noreferrer" className="hover:text-[--color-ink-secondary]">Bittensor Docs</a>
          <span className="text-[--color-ink-muted]">Whitepaper (upcoming)</span>
        </div>
        <p className="mt-4">C-SWON — Cross-Subnet Workflow Orchestration Network</p>
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/app/page.tsx
git commit -m "feat(frontend): implement landing page with hero, scoring, emissions, and stats"
```

---

## Task 10: Task Submission Page (`/submit`)

**Files:**
- Create: `frontend/app/submit/page.tsx`

- [ ] **Step 1: Build the full task submission flow**

Five-phase page: input form, miner competition view, DAG visualization, simulated execution, results panel. All connected with state transitions and mock timing.

```tsx
"use client";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { TaskType, MinerResponse, StepStatus } from "@/lib/types";
import { mockTasks, mockWorkflowResponses, mockExecutionResults } from "@/lib/mock-data";
import { MinerCard } from "@/components/miner-card";
import { DagViewer } from "@/components/dag-viewer";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { useStepAnimator } from "@/components/step-animator";
import { SubnetChip } from "@/components/subnet-chip";
import { formatTao, formatLatency } from "@/lib/utils";

type Phase = "input" | "competing" | "dag" | "executing" | "results";

const exampleTasks = [
  { label: "Merge two sorted lists (code)", taskId: "code_001" },
  { label: "Bittensor consensus (RAG)", taskId: "rag_001" },
  { label: "Compound interest (agent)", taskId: "agent_001" },
  { label: "CSV to JSON (data)", taskId: "data_001" },
];

const allSubnets = ["sn1", "sn4", "sn8", "sn13", "sn21"];

export default function SubmitPage() {
  const [phase, setPhase] = useState<Phase>("input");
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("code");
  const [budget, setBudget] = useState(0.02);
  const [maxLatency, setMaxLatency] = useState(15);
  const [selectedSubnets, setSelectedSubnets] = useState<string[]>(["sn1", "sn4"]);
  const [minerResponses, setMinerResponses] = useState<MinerResponse[]>([]);
  const [visibleMiners, setVisibleMiners] = useState<number>(0);
  const [selectedTaskId, setSelectedTaskId] = useState("code_001");

  const bestResponse = minerResponses.length > 0
    ? minerResponses.reduce((best, r) => (r.composite_score ?? 0) > (best.composite_score ?? 0) ? r : best)
    : null;

  const animator = bestResponse ? useStepAnimator(bestResponse.workflow_plan) : null;

  function pickExample(taskId: string) {
    const task = mockTasks.find((t) => t.task_id === taskId);
    if (!task) return;
    setDescription(task.description);
    setTaskType(task.task_type);
    setBudget(task.constraints.max_budget_tao);
    setMaxLatency(task.constraints.max_latency_seconds);
    setSelectedSubnets(task.constraints.allowed_subnets);
    setSelectedTaskId(taskId);
  }

  async function handleSubmit() {
    setPhase("competing");
    const responses = mockWorkflowResponses[selectedTaskId] ?? mockWorkflowResponses.code_001;
    setMinerResponses(responses);

    // Stagger miner arrivals
    for (let i = 0; i < responses.length; i++) {
      await new Promise((r) => setTimeout(r, 800 + Math.random() * 1500));
      setVisibleMiners(i + 1);
    }

    // Brief pause then show DAG
    await new Promise((r) => setTimeout(r, 1000));
    setPhase("dag");
  }

  async function handleExecute() {
    setPhase("executing");
    if (animator) {
      await animator.execute();
    }
    await new Promise((r) => setTimeout(r, 500));
    setPhase("results");
  }

  function toggleSubnet(subnet: string) {
    setSelectedSubnets((prev) =>
      prev.includes(subnet) ? prev.filter((s) => s !== subnet) : [...prev, subnet]
    );
  }

  const executionResult = mockExecutionResults[selectedTaskId] ?? mockExecutionResults.code_001;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[--color-ink]">Submit a Task</h1>
        <p className="mt-1 text-sm text-[--color-ink-secondary]">Describe a task and watch C-SWON orchestrate an optimized workflow.</p>
      </div>

      {/* ── Phase 1: Input Form ──────────────────────────── */}
      {phase === "input" && (
        <div className="space-y-6">
          {/* Example tasks */}
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Quick Examples</p>
            <div className="flex flex-wrap gap-2">
              {exampleTasks.map((ex) => (
                <button
                  key={ex.taskId}
                  onClick={() => pickExample(ex.taskId)}
                  className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                    selectedTaskId === ex.taskId
                      ? "border-[--color-teal]/40 bg-[--color-teal]/10 text-[--color-teal]"
                      : "border-[--color-border] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
                  }`}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Task Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-[--color-border] bg-[--color-surface-1] px-4 py-3 text-sm text-[--color-ink] placeholder-[--color-ink-muted] focus:border-[--color-teal]/50 focus:outline-none focus:ring-1 focus:ring-[--color-teal]/30"
              placeholder="Describe your task..."
            />
          </div>

          {/* Task type */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Task Type</label>
            <div className="flex gap-2">
              {(["code", "rag", "agent", "data_transform"] as TaskType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setTaskType(type)}
                  className={`rounded-lg border px-3 py-1.5 font-mono text-xs transition-colors ${
                    taskType === type
                      ? "border-[--color-teal]/40 bg-[--color-teal]/10 text-[--color-teal]"
                      : "border-[--color-border] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Constraints */}
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">
                Max Budget: <span className="font-mono text-[--color-gold]">{formatTao(budget)}</span>
              </label>
              <input
                type="range" min={0.005} max={0.1} step={0.001} value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-[--color-teal]"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">
                Max Latency: <span className="font-mono text-[--color-ink]">{maxLatency}s</span>
              </label>
              <input
                type="range" min={5} max={30} step={1} value={maxLatency}
                onChange={(e) => setMaxLatency(Number(e.target.value))}
                className="w-full accent-[--color-teal]"
              />
            </div>
          </div>

          {/* Subnets */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Allowed Subnets</label>
            <div className="flex flex-wrap gap-2">
              {allSubnets.map((sn) => (
                <SubnetChip key={sn} subnet={sn} selected={selectedSubnets.includes(sn)} onClick={() => toggleSubnet(sn)} />
              ))}
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={!description}
            className="rounded-lg bg-[--color-teal] px-6 py-2.5 text-sm font-medium text-[--color-canvas] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Design Workflow
          </button>
        </div>
      )}

      {/* ── Phase 2: Miner Competition ───────────────────── */}
      {phase === "competing" && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-[--color-teal] animate-pulse" />
            <span className="text-sm text-[--color-ink-secondary]">Querying miners...</span>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {minerResponses.slice(0, visibleMiners).map((r) => (
                <motion.div
                  key={r.miner_uid}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <MinerCard response={r} isBest={bestResponse?.miner_uid === r.miner_uid && visibleMiners === minerResponses.length} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* ── Phase 3: DAG Visualization ───────────────────── */}
      {(phase === "dag" || phase === "executing") && bestResponse && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-[--color-ink]">Winning Workflow Plan</h2>
            <p className="text-sm text-[--color-ink-secondary]">
              UID {bestResponse.miner_uid} — {bestResponse.workflow_plan.nodes.length} steps across{" "}
              {[...new Set(bestResponse.workflow_plan.nodes.map((n) => n.subnet))].join(", ")}
            </p>
          </div>

          <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator?.statuses ?? {}} />

          {phase === "dag" && (
            <button
              onClick={handleExecute}
              className="rounded-lg bg-[--color-teal] px-6 py-2.5 text-sm font-medium text-[--color-canvas] transition-opacity hover:opacity-90"
            >
              Execute Workflow
            </button>
          )}

          {phase === "executing" && animator && (
            <div className="flex items-center gap-6 rounded-lg border border-[--color-border] bg-[--color-surface-1] px-6 py-4">
              <div>
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Running Cost</p>
                <p className="font-mono text-lg font-bold tabular-nums text-[--color-gold]">{formatTao(animator.currentCost)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Running Latency</p>
                <p className="font-mono text-lg font-bold tabular-nums text-[--color-ink]">{formatLatency(animator.currentLatency)}</p>
              </div>
              <div className="flex-1">
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Budget Used</p>
                <div className="mt-1 h-2 rounded-full bg-[--color-surface-3]">
                  <div
                    className="h-full rounded-full bg-[--color-gold] transition-all duration-300"
                    style={{ width: `${Math.min((animator.currentCost / budget) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Phase 5: Results ─────────────────────────────── */}
      {phase === "results" && executionResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Keep DAG visible */}
          {bestResponse && <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator?.statuses ?? {}} />}

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Output */}
            <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Final Output</h3>
              <pre className="overflow-x-auto rounded-lg bg-[--color-surface-0] p-4 font-mono text-xs leading-relaxed text-[--color-ink-secondary]">
                {executionResult.final_output}
              </pre>
            </div>

            {/* Scores */}
            <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Score Breakdown</h3>
              <ScoreBreakdown scores={executionResult.scores} />
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Cost vs Budget</p>
                  <p className="font-mono text-sm tabular-nums text-[--color-gold]">
                    {formatTao(executionResult.total_cost)} / {formatTao(budget)}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Latency vs Limit</p>
                  <p className="font-mono text-sm tabular-nums text-[--color-ink]">
                    {formatLatency(executionResult.total_latency)} / {formatLatency(maxLatency)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Reset */}
          <button
            onClick={() => { setPhase("input"); setVisibleMiners(0); setMinerResponses([]); }}
            className="rounded-lg border border-[--color-border-emphasis] px-6 py-2.5 text-sm font-medium text-[--color-ink-secondary] transition-colors hover:text-[--color-ink]"
          >
            Submit Another Task
          </button>
        </motion.div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/app/submit/
git commit -m "feat(frontend): implement task submission page with competition, DAG, and execution"
```

---

## Task 11: Network Dashboard (`/dashboard`)

**Files:**
- Create: `frontend/app/dashboard/page.tsx`

- [ ] **Step 1: Build dashboard with all 8 panels**

Network overview, miner leaderboard, scoring formula, benchmark status, weight distribution, emission flow, audit flags, validator status.

```tsx
"use client";
import { useRouter } from "next/navigation";
import { mockMiners, mockValidators, mockTasks, mockNetworkStats, mockAuditFlags } from "@/lib/mock-data";
import { scoring, network } from "@/lib/constants";
import { StatCard } from "@/components/stat-card";
import { DataTable } from "@/components/data-table";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { WeightBar } from "@/components/weight-bar";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { EmissionSankey } from "@/components/emission-sankey";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import type { MinerProfile, ValidatorProfile, BenchmarkTask, AuditFlag } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const execProgress = mockNetworkStats.tasks_this_tempo / network.execSupportMin;

  const minerColumns = [
    { key: "rank", label: "#", render: (_: MinerProfile, i?: number) => <span className="text-[--color-ink-tertiary]">{(i ?? 0) + 1}</span>, align: "center" as const },
    { key: "uid", label: "UID", render: (m: MinerProfile) => <span className="font-mono text-[--color-ink]">{m.uid}</span>, sortValue: (m: MinerProfile) => m.uid, mono: true },
    { key: "hotkey", label: "Hotkey", render: (m: MinerProfile) => <span className="text-[--color-ink-tertiary]">{truncateKey(m.hotkey)}</span>, mono: true },
    { key: "composite", label: "Score", render: (m: MinerProfile) => <span className="font-bold text-[--color-ink]">{formatScore(m.scores.composite)}</span>, sortValue: (m: MinerProfile) => m.scores.composite, mono: true, align: "right" as const },
    { key: "success", label: "Success", render: (m: MinerProfile) => formatScore(m.scores.success), sortValue: (m: MinerProfile) => m.scores.success, mono: true, align: "right" as const },
    { key: "cost", label: "Cost", render: (m: MinerProfile) => formatScore(m.scores.cost), sortValue: (m: MinerProfile) => m.scores.cost, mono: true, align: "right" as const },
    { key: "latency", label: "Latency", render: (m: MinerProfile) => formatScore(m.scores.latency), sortValue: (m: MinerProfile) => m.scores.latency, mono: true, align: "right" as const },
    { key: "reliability", label: "Reliability", render: (m: MinerProfile) => formatScore(m.scores.reliability), sortValue: (m: MinerProfile) => m.scores.reliability, mono: true, align: "right" as const },
    { key: "tasks", label: "Tasks", render: (m: MinerProfile) => (
      <div className="flex items-center gap-2">
        <span>{m.tasks_seen}</span>
        {m.tasks_seen < scoring.warmupThreshold && <span className="rounded bg-[--color-gold]/15 px-1.5 py-0.5 text-[9px] text-[--color-gold]">warmup</span>}
      </div>
    ), sortValue: (m: MinerProfile) => m.tasks_seen, mono: true, align: "right" as const },
    { key: "weight", label: "Weight", render: (m: MinerProfile) => <div className="w-24"><WeightBar weight={m.weight} capped={m.weight_capped} /></div>, sortValue: (m: MinerProfile) => m.weight, align: "right" as const },
  ];

  // Sort miners by composite score for initial render
  const sortedMiners = [...mockMiners].sort((a, b) => b.scores.composite - a.scores.composite);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-[--color-ink]">Network Dashboard</h1>

      {/* ── Network Overview ──────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Current Block" value={mockNetworkStats.current_block} accent />
        <StatCard label="Current Tempo" value={mockNetworkStats.current_tempo} sublabel={`Block / ${network.tempo}`} />
        <StatCard label="Tasks This Tempo" value={mockNetworkStats.tasks_this_tempo} />
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4">
          <p className="text-[11px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Exec Support Eligibility</p>
          <p className="mt-1 font-mono text-sm tabular-nums text-[--color-ink-secondary]">{mockNetworkStats.tasks_this_tempo} / {network.execSupportMin}</p>
          <div className="mt-2 h-2 rounded-full bg-[--color-surface-3]">
            <div className={`h-full rounded-full transition-all ${execProgress >= 1 ? "bg-emerald-400" : "bg-[--color-teal]"}`} style={{ width: `${Math.min(execProgress * 100, 100)}%` }} />
          </div>
        </div>
      </div>

      {/* ── Miner Leaderboard ─────────────────────────────── */}
      <section>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Miner Leaderboard</h2>
        <DataTable
          columns={minerColumns}
          data={sortedMiners}
          keyField="uid"
          onRowClick={(m) => router.push(`/explorer?uid=${m.uid}`)}
        />
      </section>

      {/* ── Two-column: Scoring Formula + Benchmark Tasks ── */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Scoring Formula */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Scoring Formula</h2>
          <p className="mb-4 font-mono text-xs text-[--color-ink-secondary]">
            S = {Object.entries(scoring.weights).map(([k, v]) => `${v.toFixed(2)}x${k}`).join(" + ")}
          </p>
          <div className="space-y-2">
            {Object.entries(scoring.weights).map(([key, weight]) => (
              <div key={key} className="flex items-center gap-3">
                <span className="w-20 text-xs text-[--color-ink-secondary] capitalize">{key}</span>
                <div className="flex-1 h-2 rounded-full bg-[--color-surface-3]">
                  <div className="h-full rounded-full bg-[--color-teal]" style={{ width: `${weight * 100}%` }} />
                </div>
                <span className="font-mono text-xs tabular-nums text-[--color-ink-tertiary]">{(weight * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded border border-[--color-gold]/20 bg-[--color-gold]/5 px-3 py-2 text-xs text-[--color-gold]">
            Success gate: {scoring.successGate} — cost & latency only scored above this threshold
          </div>
        </section>

        {/* Benchmark Task Status */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Benchmark Tasks</h2>
          <div className="space-y-3">
            {mockTasks.map((task) => (
              <div
                key={task.task_id}
                onClick={() => router.push(`/task/${task.task_id}`)}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-[--color-border] bg-[--color-surface-0] px-4 py-3 transition-colors hover:bg-[--color-surface-2]"
              >
                <TaskTypeIcon type={task.task_type} />
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-xs text-[--color-ink-secondary]">{task.task_id}</p>
                  <p className="truncate text-sm text-[--color-ink]">{task.description}</p>
                </div>
                <LifecycleBadge status={task.status} />
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* ── Weight Distribution (bar chart) ───────────────── */}
      <section>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Weight Distribution</h2>
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <div className="space-y-2">
            {sortedMiners.map((m) => (
              <div key={m.uid} className="flex items-center gap-3">
                <span className="w-16 font-mono text-xs text-[--color-ink-secondary]">UID {m.uid}</span>
                <div className="flex-1 h-4 rounded bg-[--color-surface-2] relative">
                  <div
                    className={`h-full rounded transition-all ${m.weight_capped ? "bg-[--color-gold]" : "bg-[--color-teal]"}`}
                    style={{ width: `${(m.weight / 0.20) * 100}%` }}
                  />
                  {/* 15% cap line */}
                  <div className="absolute top-0 h-full w-px bg-red-400/60" style={{ left: `${(0.15 / 0.20) * 100}%` }} />
                </div>
                <span className="w-14 text-right font-mono text-xs tabular-nums text-[--color-ink-tertiary]">{formatPercent(m.weight)}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[10px] text-[--color-ink-muted]">Red line = 15% cap. Excess redistributed to uncapped miners.</p>
        </div>
      </section>

      {/* ── Emission Flow ─────────────────────────────────── */}
      <section>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Emission Flow</h2>
        <EmissionSankey />
      </section>

      {/* ── Two-column: Audit Flags + Validator Status ───── */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Audit Flags */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Audit Flags</h2>
          <div className="space-y-2">
            {mockAuditFlags.map((flag, i) => (
              <div key={i} className="rounded border border-[--color-gold]/20 bg-[--color-gold]/5 px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-[--color-ink]">UID {flag.uid}</span>
                  <span className="font-mono text-[10px] text-[--color-ink-tertiary]">Block {flag.block.toLocaleString()}</span>
                </div>
                <div className="mt-1 flex items-center gap-4 font-mono text-xs">
                  <span className="text-[--color-ink-secondary]">Score: {formatScore(flag.score)}</span>
                  <span className="text-[--color-ink-tertiary]">Avg: {formatScore(flag.previous_avg)}</span>
                  <span className="text-[--color-gold]">+{flag.jump_percent.toFixed(1)}%</span>
                </div>
                <p className="mt-1 text-[10px] text-[--color-ink-tertiary]">{flag.message}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Validator Status */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Validator Status</h2>
          <div className="space-y-3">
            {mockValidators.map((v) => (
              <div key={v.uid} className="rounded-lg border border-[--color-border] bg-[--color-surface-0] px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-[--color-ink]">UID {v.uid}</span>
                    <span className="font-mono text-[10px] text-[--color-ink-tertiary]">{truncateKey(v.hotkey)}</span>
                  </div>
                  <span className="rounded bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-medium text-purple-400">validator</span>
                </div>
                <div className="mt-2 grid grid-cols-4 gap-2 text-xs">
                  <div>
                    <p className="text-[10px] text-[--color-ink-tertiary]">Stake</p>
                    <p className="font-mono tabular-nums text-[--color-gold]">{v.stake.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[--color-ink-tertiary]">VTrust</p>
                    <p className="font-mono tabular-nums text-[--color-ink]">{formatScore(v.vtrust)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[--color-ink-tertiary]">Scoring</p>
                    <p className="font-mono text-[--color-ink-secondary]">{v.scoring_version}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[--color-ink-tertiary]">Benchmark</p>
                    <p className="font-mono text-[--color-ink-secondary]">{v.benchmark_version}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/app/dashboard/
git commit -m "feat(frontend): implement network dashboard with leaderboard, weights, and audit"
```

---

## Task 12: Task Detail Page (`/task/[id]`)

**Files:**
- Create: `frontend/app/task/[id]/page.tsx`

- [ ] **Step 1: Build task detail page**

```tsx
"use client";
import { use } from "react";
import { notFound } from "next/navigation";
import { mockTasks, mockTaskPerformance, mockWorkflowResponses } from "@/lib/mock-data";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { DagViewer } from "@/components/dag-viewer";
import { formatTao, formatLatency } from "@/lib/utils";
import { scoring } from "@/lib/constants";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine, Tooltip } from "recharts";

export default function TaskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const task = mockTasks.find((t) => t.task_id === id);
  if (!task) return notFound();

  const perfHistory = mockTaskPerformance[id] ?? [];
  const chartData = perfHistory.map((score, i) => ({ tempo: i + 1, score }));
  const responses = mockWorkflowResponses[id];
  const bestResponse = responses?.[0];

  return (
    <div className="space-y-8">
      {/* ── Header ────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <TaskTypeIcon type={task.task_type} size="md" />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-mono text-lg font-bold text-[--color-ink]">{task.task_id}</h1>
              <LifecycleBadge status={task.status} />
            </div>
            <p className="mt-1 text-sm text-[--color-ink-secondary]">{task.description}</p>
          </div>
        </div>
      </div>

      {/* ── Config + Routing ──────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Configuration</h2>
          {Object.keys(task.quality_criteria).length > 0 && (
            <div className="mb-4">
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Quality Criteria</p>
              <div className="mt-1 space-y-1">
                {Object.entries(task.quality_criteria).map(([k, v]) => (
                  <p key={k} className="font-mono text-xs text-[--color-ink-secondary]">{k}: {v}</p>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Budget</p>
              <p className="font-mono text-sm text-[--color-gold]">{formatTao(task.constraints.max_budget_tao)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Latency</p>
              <p className="font-mono text-sm text-[--color-ink]">{formatLatency(task.constraints.max_latency_seconds)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Subnets</p>
              <p className="font-mono text-sm text-[--color-teal]">{task.constraints.allowed_subnets.join(", ")}</p>
            </div>
          </div>

          {/* Available tools */}
          <div className="mt-4">
            <p className="mb-2 text-[10px] uppercase text-[--color-ink-muted]">Available Tools</p>
            <div className="space-y-1">
              {Object.entries(task.available_tools).map(([subnet, tool]) => (
                <div key={subnet} className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-[--color-teal]">{subnet}</span>
                  <span className="text-[--color-ink-tertiary]">{tool.type}</span>
                  <span className="text-[--color-gold]">{formatTao(tool.avg_cost)}</span>
                  <span className="text-[--color-ink-muted]">{formatLatency(tool.avg_latency)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Routing Policy</h2>
          <div className="space-y-3 font-mono text-sm">
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Miner Selection</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.miner_selection}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Top K</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.top_k}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Aggregation</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.aggregation}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Performance History ────────────────────────────── */}
      {perfHistory.length > 0 && (
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Performance History</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="tempo" stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <YAxis domain={[0, 1]} stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "var(--color-surface-2)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12, fontFamily: "var(--font-mono)" }}
                  labelStyle={{ color: "var(--color-ink-tertiary)" }}
                />
                <ReferenceLine y={0.90} stroke="#f0b429" strokeDasharray="4 4" label={{ value: "deprecation", position: "right", fill: "#f0b429", fontSize: 10 }} />
                <ReferenceLine y={0.10} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "quarantine", position: "right", fill: "#ef4444", fontSize: 10 }} />
                <Line type="monotone" dataKey="score" stroke="#00d4aa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ── Reference Data (collapsed) ────────────────────── */}
      <details className="rounded-lg border border-[--color-border] bg-[--color-surface-1]">
        <summary className="cursor-pointer px-6 py-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]">
          Reference Data
        </summary>
        <div className="border-t border-[--color-border] px-6 py-4">
          <pre className="overflow-x-auto rounded-lg bg-[--color-surface-0] p-4 font-mono text-xs leading-relaxed text-[--color-ink-secondary]">
            {JSON.stringify(task.reference, null, 2)}
          </pre>
        </div>
      </details>

      {/* ── Example Workflow (if available) ────────────────── */}
      {bestResponse && (
        <section>
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Example Workflow</h2>
          <DagViewer plan={bestResponse.workflow_plan} />
        </section>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/app/task/
git commit -m "feat(frontend): implement task detail page with config, performance chart, and reference data"
```

---

## Task 13: Miner/Validator Explorer (`/explorer`)

**Files:**
- Create: `frontend/app/explorer/page.tsx`

- [ ] **Step 1: Build explorer page**

```tsx
"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import { mockMiners, mockValidators } from "@/lib/mock-data";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { ScoreGauge } from "@/components/score-gauge";
import { WeightBar } from "@/components/weight-bar";
import { DagViewer } from "@/components/dag-viewer";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import { scoring } from "@/lib/constants";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts";

function ExplorerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const uidParam = searchParams.get("uid");

  // If no UID, show miner list
  if (!uidParam) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold text-[--color-ink]">Network Explorer</h1>

        {/* Miners */}
        <section>
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Miners</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {mockMiners.map((m) => (
              <div
                key={m.uid}
                onClick={() => router.push(`/explorer?uid=${m.uid}`)}
                className="cursor-pointer rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4 transition-colors hover:bg-[--color-surface-2]"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-[--color-ink]">UID {m.uid}</span>
                  <span className="rounded bg-[--color-teal]/15 px-1.5 py-0.5 text-[9px] font-medium text-[--color-teal]">miner</span>
                </div>
                <p className="mt-1 font-mono text-[10px] text-[--color-ink-tertiary]">{truncateKey(m.hotkey)}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="font-mono text-lg font-bold text-[--color-ink]">{formatScore(m.scores.composite)}</span>
                  <span className="font-mono text-xs text-[--color-ink-tertiary]">{m.tasks_seen} tasks</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Validators */}
        <section>
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Validators</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {mockValidators.map((v) => (
              <div key={v.uid} className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-[--color-ink]">UID {v.uid}</span>
                  <span className="rounded bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-medium text-purple-400">validator</span>
                </div>
                <p className="mt-1 font-mono text-[10px] text-[--color-ink-tertiary]">{truncateKey(v.hotkey)}</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-[10px] text-[--color-ink-muted]">Stake</p>
                    <p className="font-mono tabular-nums text-[--color-gold]">{v.stake.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[--color-ink-muted]">VTrust</p>
                    <p className="font-mono tabular-nums text-[--color-ink]">{formatScore(v.vtrust)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  const uid = Number(uidParam);
  const miner = mockMiners.find((m) => m.uid === uid);
  const validator = mockValidators.find((v) => v.uid === uid);

  if (!miner && !validator) {
    return <p className="text-[--color-ink-secondary]">Participant UID {uid} not found.</p>;
  }

  // ── Miner Profile View ──────────────────────────────
  if (miner) {
    const historyData = miner.score_history.map((score, i) => ({ task: i + 1, score }));
    const warmupScale = miner.tasks_seen < scoring.warmupThreshold
      ? miner.tasks_seen / scoring.warmupThreshold
      : 1;

    return (
      <div className="space-y-8">
        {/* Identity Card */}
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="font-mono text-2xl font-bold text-[--color-ink]">UID {miner.uid}</h1>
                <span className="rounded bg-[--color-teal]/15 px-2 py-0.5 text-[10px] font-medium text-[--color-teal]">miner</span>
                {miner.immunity_active && (
                  <span className="rounded bg-[--color-gold]/15 px-2 py-0.5 text-[10px] font-medium text-[--color-gold]">
                    immunity {miner.immunity_blocks_remaining > 0 && `(${miner.immunity_blocks_remaining.toLocaleString()} blocks)`}
                  </span>
                )}
              </div>
              <div className="mt-2 space-y-0.5 font-mono text-xs text-[--color-ink-tertiary]">
                <p>Hotkey: {truncateKey(miner.hotkey, 10)}</p>
                <p>Coldkey: {truncateKey(miner.coldkey, 10)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Stake</p>
              <p className="font-mono text-lg font-bold tabular-nums text-[--color-gold]">{miner.stake.toLocaleString()}</p>
              <p className="mt-1 text-[10px] text-[--color-ink-tertiary]">Registered at block {miner.registration_block.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Scoring Profile */}
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
            <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Scoring Profile</h2>
            <ScoreBreakdown scores={miner.scores} />
            {warmupScale < 1 && (
              <div className="mt-4 rounded border border-[--color-gold]/20 bg-[--color-gold]/5 px-3 py-2 text-xs text-[--color-gold]">
                Warmup: {miner.tasks_seen}/{scoring.warmupThreshold} tasks — scale factor {warmupScale.toFixed(2)}
              </div>
            )}
            <div className="mt-4">
              <p className="mb-1 text-[10px] uppercase text-[--color-ink-muted]">Weight</p>
              <WeightBar weight={miner.weight} capped={miner.weight_capped} />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
            <ScoreGauge value={miner.scores.success} dimension="success" size={100} />
            <ScoreGauge value={miner.scores.cost} dimension="cost" size={100} />
            <ScoreGauge value={miner.scores.latency} dimension="latency" size={100} />
            <ScoreGauge value={miner.scores.reliability} dimension="reliability" size={100} />
          </div>
        </div>

        {/* Score History Chart */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Score History (Last {miner.score_history.length} Tasks)</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="task" stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <YAxis domain={[0, 1]} stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "var(--color-surface-2)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12, fontFamily: "var(--font-mono)" }}
                />
                <Line type="monotone" dataKey="score" stroke="#00d4aa" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Subnet Profiler */}
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Subnet Profiler</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[--color-border] text-left text-[10px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]">
                  <th className="pb-2 pr-6">Subnet</th>
                  <th className="pb-2 pr-6 text-right">Avg Cost</th>
                  <th className="pb-2 pr-6 text-right">Avg Latency</th>
                  <th className="pb-2 pr-6 text-right">Reliability</th>
                  <th className="pb-2 text-right">Observations</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(miner.subnet_stats).map(([subnet, stats]) => (
                  <tr key={subnet} className="border-b border-[--color-border]/50">
                    <td className="py-2 pr-6 font-mono text-[--color-teal]">{subnet}</td>
                    <td className="py-2 pr-6 text-right font-mono tabular-nums text-[--color-gold]">{stats.avg_cost.toFixed(4)}</td>
                    <td className="py-2 pr-6 text-right font-mono tabular-nums text-[--color-ink-secondary]">{stats.avg_latency.toFixed(2)}s</td>
                    <td className="py-2 pr-6 text-right font-mono tabular-nums text-[--color-ink]">{formatPercent(stats.reliability)}</td>
                    <td className="py-2 text-right font-mono tabular-nums text-[--color-ink-tertiary]">{stats.observations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    );
  }

  // ── Validator view (minimal) ─────────────────────────
  if (validator) {
    return (
      <div className="space-y-8">
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-2xl font-bold text-[--color-ink]">UID {validator.uid}</h1>
            <span className="rounded bg-purple-500/15 px-2 py-0.5 text-[10px] font-medium text-purple-400">validator</span>
          </div>
          <div className="mt-2 space-y-0.5 font-mono text-xs text-[--color-ink-tertiary]">
            <p>Hotkey: {truncateKey(validator.hotkey, 10)}</p>
            <p>Coldkey: {truncateKey(validator.coldkey, 10)}</p>
          </div>
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Stake</p>
              <p className="font-mono text-lg font-bold tabular-nums text-[--color-gold]">{validator.stake.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">VTrust</p>
              <p className="font-mono text-lg font-bold tabular-nums text-[--color-ink]">{formatScore(validator.vtrust)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Scoring Version</p>
              <p className="font-mono text-sm text-[--color-ink-secondary]">{validator.scoring_version}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Last Weight Set</p>
              <p className="font-mono text-sm tabular-nums text-[--color-ink-secondary]">{validator.last_weight_set_block.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default function ExplorerPage() {
  return (
    <Suspense fallback={<div className="text-[--color-ink-secondary]">Loading...</div>}>
      <ExplorerContent />
    </Suspense>
  );
}
```

- [ ] **Step 2: Verify build and commit**

```bash
cd frontend && npm run build
git add frontend/app/explorer/
git commit -m "feat(frontend): implement miner/validator explorer with profiles, gauges, and charts"
```

---

## Task 14: Final Polish & Build Verification

**Files:**
- Modify: Various files for build fixes

- [ ] **Step 1: Run full build and fix any TypeScript/lint errors**

```bash
cd frontend && npm run build 2>&1
```

Fix any errors that surface — common issues:
- Missing imports
- Type mismatches in DataTable generic
- CSS custom property references in Tailwind classes

- [ ] **Step 2: Run dev server and visual smoke test**

```bash
cd frontend && npm run dev
```

Check each page loads: `/`, `/dashboard`, `/submit`, `/task/code_001`, `/explorer`, `/explorer?uid=1`

- [ ] **Step 3: Final commit**

```bash
git add frontend/
git commit -m "feat(frontend): polish and fix build for all pages"
```

---

Plan complete and saved to `docs/superpowers/plans/2026-03-29-cswon-frontend.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
import type {
  BenchmarkTask, MinerProfile, ValidatorProfile, MinerResponse,
  ExecutionResult, AuditFlag, NetworkStats, WorkflowPlan,
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
      test_suite: 'def test_merge():\\n    from solution import merge_sorted\\n    assert merge_sorted([1,3,5],[2,4,6]) == [1,2,3,4,5,6]',
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
    reference: { test_suite: "def test_fib():\\n    from solution import fib\\n    assert fib(10)==55" },
  },
];

// ── Helper ────────────────────────────────────────────────────────

function generateScoreHistory(base: number, variance: number, count: number): number[] {
  const seed = base * 1000;
  return Array.from({ length: count }, (_, i) => {
    const pseudo = Math.sin(seed + i) * 0.5 + 0.5;
    return Math.max(0, Math.min(1, base + (pseudo - 0.5) * variance));
  });
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

// ── Workflow Plans ────────────────────────────────────────────────

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
    { miner_uid: 2, hotkey: "5FLSigC9...cS59Y", scoring_version: "1.0.0", workflow_plan: { ...codePlan, nodes: codePlan.nodes.map(n => ({ ...n, estimated_cost: n.estimated_cost * 1.2 })) }, total_estimated_cost: 0.0084, total_estimated_latency: 3.8, confidence: 0.87, reasoning: "Sequential pipeline with higher cost estimates for safety margin.", composite_score: 0.812 },
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
      { node_id: "step_2", status: "completed", output: "Bittensor uses Yuma Consensus, a stake-weighted agreement mechanism where validators assign scores to miners...", cost: 0.0018, latency: 0.75 },
      { node_id: "step_3", status: "completed", output: "Fact-check passed: key claims verified against documentation", cost: 0.0008, latency: 0.40 },
    ],
    final_output: "Bittensor uses Yuma Consensus, a stake-weighted agreement mechanism where validators assign scores to miners based on the quality of their work. Unlike Proof of Work (PoW) which requires miners to expend computational energy solving cryptographic puzzles, Yuma Consensus rewards useful machine learning work evaluated by validator peers.",
    total_cost: 0.0035,
    total_latency: 1.63,
    scores: { composite: 0.860, success: 0.94, cost: 0.65, latency: 0.84, reliability: 0.98 },
  },
};

// ── Task Performance History ──────────────────────────────────────

export const mockTaskPerformance: Record<string, number[]> = {
  code_001: [0.72, 0.74, 0.76, 0.78, 0.80, 0.81, 0.82, 0.83, 0.84, 0.84, 0.85, 0.85],
  rag_001: [0.68, 0.71, 0.73, 0.75, 0.77, 0.79, 0.80, 0.82, 0.83, 0.84, 0.85, 0.86],
  agent_001: [0.88, 0.89, 0.90, 0.91, 0.91, 0.92, 0.92, 0.92, 0.93, 0.93, 0.93, 0.93],
  data_001: [0.04, 0.05, 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.08, 0.09, 0.09, 0.09],
  synthetic_001: [0.70, 0.73, 0.75, 0.77, 0.79, 0.80, 0.81, 0.82, 0.83, 0.83, 0.84, 0.84],
};

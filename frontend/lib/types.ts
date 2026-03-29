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
  tier: number;
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
  score_history: number[];
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
}

export interface ExecutionResult {
  steps: ExecutionStep[];
  final_output: string;
  total_cost: number;
  total_latency: number;
  scores: ScoreBreakdownData;
}

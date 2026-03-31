import type { MinerProfile, ValidatorProfile, NetworkStats, ScoreBreakdownData } from "./types";

// ── Chain snapshot types (from scripts/dump-metagraph.py) ───────

interface ChainNeuron {
  uid: number;
  hotkey: string;
  coldkey: string;
  stake: number;
  validator_trust: number;
  consensus: number;
  incentive: number;
  dividends: number;
  emission: number;
  active: boolean;
  validator_permit: boolean;
  role: "validator" | "miner" | "inactive";
}

interface ChainSnapshot {
  block: number;
  netuid: number;
  network: string;
  n: number;
  tempo: number;
  immunity_period: number;
  neurons: ChainNeuron[];
}

// ── Fetch (reads static snapshot from /chain-data/metagraph.json) ─

let snapshotCache: { data: ChainSnapshot; ts: number } | null = null;
const CACHE_TTL = 60_000;

export async function fetchChainSnapshot(): Promise<ChainSnapshot> {
  if (snapshotCache && Date.now() - snapshotCache.ts < CACHE_TTL) {
    return snapshotCache.data;
  }

  const res = await fetch("/chain-data/metagraph.json");
  if (!res.ok) {
    throw new Error(`Chain snapshot fetch failed (${res.status})`);
  }

  const data: ChainSnapshot = await res.json();
  if (!data.neurons || data.neurons.length === 0) {
    throw new Error("Chain snapshot is empty");
  }

  snapshotCache = { data, ts: Date.now() };
  return data;
}

// ── Mappers ──────────────────────────────────────────────────────

const CHAIN_ONLY_SCORES: ScoreBreakdownData = {
  composite: 0,
  success: 0,
  cost: 0,
  latency: 0,
  reliability: 0,
};

export function mapNeuronToMiner(n: ChainNeuron, block: number, immunityPeriod: number): MinerProfile {
  return {
    uid: n.uid,
    hotkey: n.hotkey,
    coldkey: n.coldkey,
    role: "miner",
    stake: n.stake,
    registration_block: 0,
    blocks_since_registration: 0,
    immunity_active: false,
    immunity_blocks_remaining: 0,
    tasks_seen: 0,
    scores: { ...CHAIN_ONLY_SCORES, composite: n.incentive },
    score_history: [],
    weight: n.incentive,
    weight_capped: false,
    subnet_stats: {},
    recent_workflows: [],
  };
}

export function mapNeuronToValidator(n: ChainNeuron): ValidatorProfile {
  return {
    uid: n.uid,
    hotkey: n.hotkey,
    coldkey: n.coldkey,
    role: "validator",
    stake: n.stake,
    vtrust: n.validator_trust,
    last_weight_set_block: 0,
    scoring_version: "chain",
    benchmark_version: "chain",
  };
}

export function mapSnapshotToNetworkStats(snapshot: ChainSnapshot): NetworkStats {
  const miners = snapshot.neurons.filter((n) => n.role === "miner");
  const validators = snapshot.neurons.filter((n) => n.role === "validator");
  return {
    current_block: snapshot.block,
    current_tempo: snapshot.tempo,
    tasks_this_tempo: 0,
    active_miners: miners.filter((n) => n.active).length || miners.length,
    active_validators: validators.filter((n) => n.active).length || validators.length,
    tasks_evaluated: 0,
  };
}

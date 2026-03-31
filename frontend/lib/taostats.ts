import type { MinerProfile, ValidatorProfile, NetworkStats, ScoreBreakdownData } from "./types";

// ── Raw Taostats response types ──────────────────────────────────

interface TaostatsAddress {
  ss58: string;
  hex: string;
}

interface TaostatsNeuron {
  hotkey: TaostatsAddress;
  coldkey: TaostatsAddress;
  netuid: number;
  uid: number;
  block_number: number;
  timestamp: string;
  stake: string;
  trust: string;
  validator_trust: string;
  consensus: string;
  incentive: string;
  dividends: string;
  emission: string;
  active: boolean;
  validator_permit: boolean;
  updated: number;
  daily_reward: string;
  registered_at_block: number;
  is_immunity_period: boolean;
  rank: number;
  axon: {
    block: number;
    ip: string;
    port: number;
    protocol: number;
    version: number;
  };
}

interface TaostatsSubnet {
  block_number: number;
  timestamp: string;
  netuid: number;
  owner: TaostatsAddress;
  active_keys: number;
  active_validators: number;
  active_miners: number;
  emission: string;
  tempo: number;
  immunity_period: number;
  blocks_since_last_step: number;
  blocks_until_next_epoch: number;
}

// ── Fetch functions (hit our proxy routes) ───────────────────────

let metagraphCache: { data: TaostatsNeuron[]; ts: number } | null = null;
let subnetCache: { data: TaostatsSubnet; ts: number } | null = null;
const CACHE_TTL = 60_000;

export async function fetchMetagraph(): Promise<TaostatsNeuron[]> {
  if (metagraphCache && Date.now() - metagraphCache.ts < CACHE_TTL) {
    return metagraphCache.data;
  }

  const res = await fetch("/api/taostats/metagraph");
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Metagraph fetch failed (${res.status})`);
  }

  const json = await res.json();
  const neurons: TaostatsNeuron[] = Array.isArray(json) ? json : json.data ?? [];
  metagraphCache = { data: neurons, ts: Date.now() };
  return neurons;
}

export async function fetchSubnetInfo(): Promise<TaostatsSubnet> {
  if (subnetCache && Date.now() - subnetCache.ts < CACHE_TTL) {
    return subnetCache.data;
  }

  const res = await fetch("/api/taostats/subnet");
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Subnet fetch failed (${res.status})`);
  }

  const json = await res.json();
  const subnets = Array.isArray(json) ? json : json.data ?? [];
  const subnet = subnets.find((s: TaostatsSubnet) => s.netuid === 26) ?? subnets[0];
  if (!subnet) throw new Error("Subnet 26 not found in Taostats response");
  subnetCache = { data: subnet, ts: Date.now() };
  return subnet;
}

// ── Mappers ──────────────────────────────────────────────────────

const CHAIN_ONLY_SCORES: ScoreBreakdownData = {
  composite: 0,
  success: 0,
  cost: 0,
  latency: 0,
  reliability: 0,
};

export function mapNeuronToMiner(n: TaostatsNeuron): MinerProfile {
  const incentive = parseFloat(n.incentive) || 0;
  return {
    uid: n.uid,
    hotkey: n.hotkey.ss58,
    coldkey: n.coldkey.ss58,
    role: "miner",
    stake: parseFloat(n.stake) / 1e9,
    registration_block: n.registered_at_block,
    blocks_since_registration: n.block_number - n.registered_at_block,
    immunity_active: n.is_immunity_period,
    immunity_blocks_remaining: n.is_immunity_period ? Math.max(0, 5000 - (n.block_number - n.registered_at_block)) : 0,
    tasks_seen: 0,
    scores: { ...CHAIN_ONLY_SCORES, composite: incentive },
    score_history: [],
    weight: incentive,
    weight_capped: false,
    subnet_stats: {},
    recent_workflows: [],
  };
}

export function mapNeuronToValidator(n: TaostatsNeuron): ValidatorProfile {
  return {
    uid: n.uid,
    hotkey: n.hotkey.ss58,
    coldkey: n.coldkey.ss58,
    role: "validator",
    stake: parseFloat(n.stake) / 1e9,
    vtrust: parseFloat(n.validator_trust) || 0,
    last_weight_set_block: n.updated,
    scoring_version: "chain",
    benchmark_version: "chain",
  };
}

export function mapSubnetToNetworkStats(
  subnet: TaostatsSubnet,
  neurons: TaostatsNeuron[]
): NetworkStats {
  const activeMiners = neurons.filter((n) => !n.validator_permit && n.active).length;
  const activeValidators = neurons.filter((n) => n.validator_permit && n.active).length;
  return {
    current_block: subnet.block_number,
    current_tempo: Math.floor(subnet.blocks_since_last_step),
    tasks_this_tempo: 0,
    active_miners: activeMiners || subnet.active_miners,
    active_validators: activeValidators || subnet.active_validators,
    tasks_evaluated: 0,
  };
}

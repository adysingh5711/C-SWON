# Testnet/Mock Data Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-page toggle that switches between mock demo data and live Bittensor testnet data from the Taostats API on the Dashboard and Explorer pages.

**Architecture:** React Context persists the toggle state in localStorage. A Taostats API client (proxied through a Next.js API route to protect the API key) fetches metagraph and subnet data. A mapper converts API responses to existing frontend types. Pages use a `useNetworkData()` hook that returns mock or live data based on context.

**Tech Stack:** Next.js 16, React 19, TypeScript, Taostats REST API, existing design tokens

---

### Task 1: Data Source Context

**Files:**
- Create: `frontend/lib/data-source-context.tsx`

- [ ] **Step 1: Create the context provider**

```tsx
// frontend/lib/data-source-context.tsx
"use client";
import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type DataSource = "mock" | "testnet";

interface DataSourceContextValue {
  source: DataSource;
  setSource: (s: DataSource) => void;
}

const DataSourceContext = createContext<DataSourceContextValue>({
  source: "mock",
  setSource: () => {},
});

const STORAGE_KEY = "cswon-data-source";

export function DataSourceProvider({ children }: { children: ReactNode }) {
  const [source, setSourceState] = useState<DataSource>("mock");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "mock" || stored === "testnet") {
      setSourceState(stored);
    }
    setMounted(true);
  }, []);

  function setSource(s: DataSource) {
    setSourceState(s);
    localStorage.setItem(STORAGE_KEY, s);
  }

  // Avoid hydration mismatch — render children only after mount
  if (!mounted) {
    return <DataSourceContext.Provider value={{ source: "mock", setSource }}>{children}</DataSourceContext.Provider>;
  }

  return (
    <DataSourceContext.Provider value={{ source, setSource }}>
      {children}
    </DataSourceContext.Provider>
  );
}

export function useDataSource() {
  return useContext(DataSourceContext);
}
```

- [ ] **Step 2: Wrap layout with provider**

Modify `frontend/app/layout.tsx`. Add import and wrap `<body>` children:

```tsx
// Add import at top:
import { DataSourceProvider } from "@/lib/data-source-context";

// Change the body content from:
//   <Nav />
//   <main ...>{children}</main>
// To:
//   <DataSourceProvider>
//     <Nav />
//     <main ...>{children}</main>
//   </DataSourceProvider>
```

The `<Analytics />` and `<SpeedInsights />` stay outside the provider (they don't need it).

- [ ] **Step 3: Commit**

```bash
cd frontend && git add lib/data-source-context.tsx app/layout.tsx
git commit -m "feat(frontend): add DataSource context with localStorage persistence"
```

---

### Task 2: Taostats API Proxy Route

The Taostats API requires an API key in the `Authorization` header. We proxy through a Next.js API route so the key stays server-side.

**Files:**
- Create: `frontend/.env.local` (git-ignored, holds API key)
- Create: `frontend/app/api/taostats/metagraph/route.ts`
- Create: `frontend/app/api/taostats/subnet/route.ts`

- [ ] **Step 1: Add environment variable**

Create `frontend/.env.local`:

```
TAOSTATS_API_KEY=your-api-key-here
```

Verify `.gitignore` includes `.env.local` (Next.js default does).

- [ ] **Step 2: Create metagraph proxy route**

```ts
// frontend/app/api/taostats/metagraph/route.ts
import { NextResponse } from "next/server";

const TAOSTATS_BASE = "https://api.taostats.io";
const NETUID = 26;

export async function GET() {
  const apiKey = process.env.TAOSTATS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "TAOSTATS_API_KEY not configured" },
      { status: 500 }
    );
  }

  try {
    const res = await fetch(
      `${TAOSTATS_BASE}/api/metagraph/latest/v1?netuid=${NETUID}&network=test`,
      {
        headers: {
          Authorization: apiKey,
          Accept: "application/json",
        },
        next: { revalidate: 60 },
      }
    );

    if (!res.ok) {
      return NextResponse.json(
        { error: `Taostats API returned ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: "Failed to reach Taostats API" },
      { status: 502 }
    );
  }
}
```

- [ ] **Step 3: Create subnet proxy route**

```ts
// frontend/app/api/taostats/subnet/route.ts
import { NextResponse } from "next/server";

const TAOSTATS_BASE = "https://api.taostats.io";
const NETUID = 26;

export async function GET() {
  const apiKey = process.env.TAOSTATS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "TAOSTATS_API_KEY not configured" },
      { status: 500 }
    );
  }

  try {
    const res = await fetch(
      `${TAOSTATS_BASE}/api/subnet/latest/v1?netuid=${NETUID}&network=test`,
      {
        headers: {
          Authorization: apiKey,
          Accept: "application/json",
        },
        next: { revalidate: 60 },
      }
    );

    if (!res.ok) {
      return NextResponse.json(
        { error: `Taostats API returned ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: "Failed to reach Taostats API" },
      { status: 502 }
    );
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add app/api/taostats/metagraph/route.ts app/api/taostats/subnet/route.ts
git commit -m "feat(frontend): add Taostats API proxy routes for metagraph and subnet"
```

---

### Task 3: Taostats Client & Mapper

**Files:**
- Create: `frontend/lib/taostats.ts`

- [ ] **Step 1: Create the API client with response mapper**

```ts
// frontend/lib/taostats.ts
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

interface TaostatsPaginatedResponse<T> {
  pagination: {
    current_page: number;
    per_page: number;
    total_items: number;
    total_pages: number;
  };
  data: T[];
}

// ── Fetch functions (hit our proxy routes) ───────────────────────

let metagraphCache: { data: TaostatsNeuron[]; ts: number } | null = null;
let subnetCache: { data: TaostatsSubnet; ts: number } | null = null;
const CACHE_TTL = 60_000; // 60 seconds

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
  // API may return { pagination, data: [...] } or just [...]
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
    stake: parseFloat(n.stake) / 1e9, // RAO to TAO
    registration_block: n.registered_at_block,
    blocks_since_registration: n.block_number - n.registered_at_block,
    immunity_active: n.is_immunity_period,
    immunity_blocks_remaining: n.is_immunity_period ? 15000 - (n.block_number - n.registered_at_block) : 0,
    tasks_seen: 0, // not available from chain
    scores: { ...CHAIN_ONLY_SCORES, composite: incentive },
    score_history: [],
    weight: incentive, // best proxy from chain
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
    tasks_this_tempo: 0, // not available from chain
    active_miners: activeMiners || subnet.active_miners,
    active_validators: activeValidators || subnet.active_validators,
    tasks_evaluated: 0, // not available from chain
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/taostats.ts
git commit -m "feat(frontend): add Taostats API client with response mappers"
```

---

### Task 4: useNetworkData Hook

**Files:**
- Create: `frontend/lib/use-network-data.ts`

- [ ] **Step 1: Create the hook**

```ts
// frontend/lib/use-network-data.ts
"use client";
import { useState, useEffect, useCallback } from "react";
import { useDataSource } from "./data-source-context";
import { mockMiners, mockValidators, mockNetworkStats } from "./mock-data";
import {
  fetchMetagraph,
  fetchSubnetInfo,
  mapNeuronToMiner,
  mapNeuronToValidator,
  mapSubnetToNetworkStats,
} from "./taostats";
import type { MinerProfile, ValidatorProfile, NetworkStats } from "./types";

interface NetworkData {
  miners: MinerProfile[];
  validators: ValidatorProfile[];
  networkStats: NetworkStats;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useNetworkData(): NetworkData {
  const { source } = useDataSource();
  const [miners, setMiners] = useState<MinerProfile[]>(mockMiners);
  const [validators, setValidators] = useState<ValidatorProfile[]>(mockValidators);
  const [networkStats, setNetworkStats] = useState<NetworkStats>(mockNetworkStats);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchCount, setFetchCount] = useState(0);

  const retry = useCallback(() => setFetchCount((c) => c + 1), []);

  useEffect(() => {
    if (source === "mock") {
      setMiners(mockMiners);
      setValidators(mockValidators);
      setNetworkStats(mockNetworkStats);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const [neurons, subnet] = await Promise.all([
          fetchMetagraph(),
          fetchSubnetInfo(),
        ]);

        if (cancelled) return;

        const chainMiners = neurons
          .filter((n) => !n.validator_permit)
          .map(mapNeuronToMiner);
        const chainValidators = neurons
          .filter((n) => n.validator_permit)
          .map(mapNeuronToValidator);
        const chainStats = mapSubnetToNetworkStats(subnet, neurons);

        setMiners(chainMiners.length > 0 ? chainMiners : []);
        setValidators(chainValidators.length > 0 ? chainValidators : []);
        setNetworkStats(chainStats);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to fetch testnet data");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [source, fetchCount]);

  return { miners, validators, networkStats, loading, error, retry };
}
```

- [ ] **Step 2: Commit**

```bash
git add lib/use-network-data.ts
git commit -m "feat(frontend): add useNetworkData hook for mock/testnet switching"
```

---

### Task 5: Toggle Component

**Files:**
- Create: `frontend/components/data-source-toggle.tsx`

- [ ] **Step 1: Create the toggle**

```tsx
// frontend/components/data-source-toggle.tsx
"use client";
import { useDataSource, type DataSource } from "@/lib/data-source-context";

interface DataSourceToggleProps {
  mode: "enabled" | "coming-soon";
}

export function DataSourceToggle({ mode }: DataSourceToggleProps) {
  const { source, setSource } = useDataSource();

  function handleSelect(target: DataSource) {
    if (mode === "coming-soon" && target === "testnet") return;
    setSource(target);
  }

  return (
    <div className="inline-flex items-center rounded-full border border-[--color-border] bg-[--color-surface-1] p-0.5 text-xs">
      <button
        onClick={() => handleSelect("mock")}
        className={`rounded-full px-3 py-1 transition-colors ${
          source === "mock"
            ? "bg-[--color-surface-3] text-[--color-ink]"
            : "text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]"
        }`}
      >
        Mock
      </button>
      <button
        onClick={() => handleSelect("testnet")}
        className={`group relative rounded-full px-3 py-1 transition-colors ${
          mode === "coming-soon"
            ? "cursor-not-allowed text-[--color-ink-muted]"
            : source === "testnet"
              ? "bg-[--color-teal]/15 text-[--color-teal]"
              : "text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]"
        }`}
        disabled={mode === "coming-soon"}
        title={mode === "coming-soon" ? "Live testnet data coming soon" : undefined}
      >
        Testnet
        {mode === "coming-soon" && (
          <span className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-[--color-surface-3] px-2 py-0.5 text-[10px] text-[--color-ink-tertiary] opacity-0 transition-opacity group-hover:opacity-100">
            Coming Soon
          </span>
        )}
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add components/data-source-toggle.tsx
git commit -m "feat(frontend): add DataSourceToggle component with coming-soon mode"
```

---

### Task 6: Dashboard Page Integration

**Files:**
- Modify: `frontend/app/dashboard/page.tsx`

- [ ] **Step 1: Replace mock imports with hook and add toggle**

Replace the top of `dashboard/page.tsx`. Key changes:

1. Replace direct mock imports with `useNetworkData()` hook
2. Add `DataSourceToggle` in the header
3. Add loading and error states
4. In testnet mode, hide C-SWON-internal columns (success, cost, latency, reliability, tasks, weight)

```tsx
// frontend/app/dashboard/page.tsx
"use client";
import { useRouter } from "next/navigation";
import { useNetworkData } from "@/lib/use-network-data";
import { useDataSource } from "@/lib/data-source-context";
import { mockTasks, mockAuditFlags } from "@/lib/mock-data";
import { scoring, network } from "@/lib/constants";
import { StatCard } from "@/components/stat-card";
import { DataTable } from "@/components/data-table";
import { WeightBar } from "@/components/weight-bar";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { EmissionSankey } from "@/components/emission-sankey";
import { DataSourceToggle } from "@/components/data-source-toggle";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import type { MinerProfile } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const { source } = useDataSource();
  const { miners, validators, networkStats, loading, error, retry } = useNetworkData();
  const isTestnet = source === "testnet";

  const execProgress = networkStats.tasks_this_tempo / network.execSupportMin;
  const sortedMiners = [...miners].sort((a, b) => b.scores.composite - a.scores.composite);

  // Full columns for mock, reduced for testnet
  const minerColumns = [
    { key: "uid", label: "UID", render: (m: MinerProfile) => <span className="font-mono text-[--color-ink]">{m.uid}</span>, sortValue: (m: MinerProfile) => m.uid, mono: true },
    { key: "hotkey", label: "Hotkey", render: (m: MinerProfile) => <span className="text-[--color-ink-tertiary]">{truncateKey(m.hotkey)}</span>, mono: true },
    { key: "stake", label: "Stake", render: (m: MinerProfile) => <span className="font-mono text-[--color-ink-secondary]">{m.stake.toFixed(4)}</span>, sortValue: (m: MinerProfile) => m.stake, mono: true, align: "right" as const },
    { key: "composite", label: isTestnet ? "Incentive" : "Score", render: (m: MinerProfile) => <span className="font-bold text-[--color-ink]">{formatScore(m.scores.composite)}</span>, sortValue: (m: MinerProfile) => m.scores.composite, mono: true, align: "right" as const },
    // C-SWON-internal columns — only in mock mode
    ...(!isTestnet ? [
      { key: "success", label: "Success", render: (m: MinerProfile) => <span className="text-[--color-ink-secondary]">{formatScore(m.scores.success)}</span>, sortValue: (m: MinerProfile) => m.scores.success, mono: true, align: "right" as const },
      { key: "cost", label: "Cost", render: (m: MinerProfile) => <span className="text-[--color-ink-secondary]">{formatScore(m.scores.cost)}</span>, sortValue: (m: MinerProfile) => m.scores.cost, mono: true, align: "right" as const },
      { key: "latency", label: "Latency", render: (m: MinerProfile) => <span className="text-[--color-ink-secondary]">{formatScore(m.scores.latency)}</span>, sortValue: (m: MinerProfile) => m.scores.latency, mono: true, align: "right" as const },
      { key: "reliability", label: "Rel.", render: (m: MinerProfile) => <span className="text-[--color-ink-secondary]">{formatScore(m.scores.reliability)}</span>, sortValue: (m: MinerProfile) => m.scores.reliability, mono: true, align: "right" as const },
      { key: "tasks", label: "Tasks", render: (m: MinerProfile) => (
        <div className="flex items-center gap-2">
          <span className="text-[--color-ink-secondary]">{m.tasks_seen}</span>
          {m.tasks_seen < scoring.warmupThreshold && <span className="rounded bg-[--color-gold]/15 px-1.5 py-0.5 text-[9px] text-[--color-gold]">warmup</span>}
        </div>
      ), sortValue: (m: MinerProfile) => m.tasks_seen, mono: true, align: "right" as const },
      { key: "weight", label: "Weight", render: (m: MinerProfile) => <div className="w-24"><WeightBar weight={m.weight} capped={m.weight_capped} /></div>, sortValue: (m: MinerProfile) => m.weight, align: "right" as const },
    ] : [
      { key: "emission", label: "Emission", render: (m: MinerProfile) => <span className="font-mono text-[--color-ink-secondary]">{m.weight.toFixed(6)}</span>, sortValue: (m: MinerProfile) => m.weight, mono: true, align: "right" as const },
      { key: "immunity", label: "Immunity", render: (m: MinerProfile) => <span className={`text-xs ${m.immunity_active ? "text-[--color-gold]" : "text-[--color-ink-muted]"}`}>{m.immunity_active ? "Active" : "Expired"}</span>, sortValue: (m: MinerProfile) => (m.immunity_active ? 1 : 0), align: "right" as const },
    ]),
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-ink]">Network Dashboard</h1>
        <DataSourceToggle mode="enabled" />
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-[--color-error]/30 bg-[--color-error]/10 px-4 py-3">
          <span className="text-sm text-[--color-error]">{error}</span>
          <button onClick={retry} className="rounded bg-[--color-error]/20 px-3 py-1 text-xs text-[--color-error] hover:bg-[--color-error]/30">
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-[--color-surface-2]" />
            ))}
          </div>
          <div className="h-64 animate-pulse rounded-lg bg-[--color-surface-2]" />
        </div>
      ) : (
        <>
          {/* Testnet banner */}
          {isTestnet && (
            <div className="rounded-lg border border-[--color-teal]/30 bg-[--color-teal]/5 px-4 py-2 text-xs text-[--color-teal]">
              Showing live data from Bittensor testnet (netuid 26). Score breakdown columns are only available in mock mode.
            </div>
          )}

          {/* Network Overview */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Current Block" value={networkStats.current_block} accent />
            <StatCard label={isTestnet ? "Blocks Into Tempo" : "Current Tempo"} value={networkStats.current_tempo} sublabel={`/ ${network.tempo}`} />
            <StatCard label="Active Miners" value={networkStats.active_miners} />
            <StatCard label="Active Validators" value={networkStats.active_validators} />
          </div>

          {/* Miner Leaderboard */}
          <section>
            <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">
              {isTestnet ? "Metagraph — Miners" : "Miner Leaderboard"}
            </h2>
            {sortedMiners.length > 0 ? (
              <DataTable
                columns={minerColumns}
                data={sortedMiners}
                keyField="uid"
                onRowClick={(m: MinerProfile) => router.push(`/explorer?uid=${m.uid}`)}
                defaultSort="composite"
                defaultOrder="desc"
              />
            ) : (
              <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-8 text-center text-sm text-[--color-ink-tertiary]">
                No miners found on testnet subnet 26
              </div>
            )}
          </section>

          {/* Mock-only sections */}
          {!isTestnet && (
            <>
              {/* Scoring Formula section — keep existing code */}
              {/* Benchmark Tasks section — keep existing code */}
              {/* Weight Distribution section — keep existing code */}
              {/* Emission Sankey section — keep existing code */}
              {/* Audit Flags section — keep existing code */}
            </>
          )}

          {/* Validator Status — always shown */}
          <section>
            <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Validator Status</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {validators.map((v) => (
                <div key={v.uid} className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm text-[--color-ink]">UID {v.uid}</span>
                    <span className="text-xs text-[--color-ink-tertiary]">{truncateKey(v.hotkey)}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-[--color-ink-tertiary]">Stake</span><p className="font-mono text-[--color-ink-secondary]">{v.stake.toFixed(4)} {isTestnet ? "ב" : "τ"}</p></div>
                    <div><span className="text-[--color-ink-tertiary]">VTrust</span><p className="font-mono text-[--color-ink-secondary]">{v.vtrust.toFixed(4)}</p></div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
```

Note: The existing mock-only sections (Scoring Formula, Benchmark Tasks, Weight Distribution, Emission Sankey, Audit Flags) should be kept as-is inside the `{!isTestnet && (...)}` block. Copy them from the current file — they remain unchanged.

- [ ] **Step 2: Verify the page renders in mock mode**

Run: `cd frontend && npm run dev`
Open: `http://localhost:3000/dashboard`
Expected: Dashboard renders with mock data, toggle shows "Mock" active.

- [ ] **Step 3: Commit**

```bash
git add app/dashboard/page.tsx
git commit -m "feat(frontend): wire dashboard to useNetworkData with testnet toggle"
```

---

### Task 7: Explorer Page Integration

**Files:**
- Modify: `frontend/app/explorer/page.tsx`

- [ ] **Step 1: Add toggle and hook to explorer**

The explorer has two views: grid (no UID) and detail (with UID). Both need the hook.

Key changes:
1. Replace mock imports with `useNetworkData()`
2. Add toggle in header
3. In testnet detail view, show chain-available fields only, grey out score breakdown

The explorer page uses `useSearchParams()` for the `uid` query param. Replace mock data lookups:

```tsx
// At the top of the file, replace:
//   import { mockMiners, mockValidators } from "@/lib/mock-data";
// With:
import { useNetworkData } from "@/lib/use-network-data";
import { useDataSource } from "@/lib/data-source-context";
import { DataSourceToggle } from "@/components/data-source-toggle";
```

```tsx
// Inside the component, replace:
//   const miners = mockMiners;
//   const validators = mockValidators;
// With:
const { source } = useDataSource();
const { miners, validators, loading, error, retry } = useNetworkData();
const isTestnet = source === "testnet";
```

Add the toggle next to the page heading:

```tsx
<div className="flex items-center justify-between">
  <h1 className="text-2xl font-bold text-[--color-ink]">Explorer</h1>
  <DataSourceToggle mode="enabled" />
</div>
```

Add loading/error states similar to dashboard.

In the miner detail view, when `isTestnet` is true:
- Show UID, hotkey, coldkey, stake, registration_block, immunity status, incentive (composite)
- Replace score breakdown gauges with a note: "Detailed score breakdown available in mock mode"
- Hide score_history chart and subnet_stats table (empty in testnet mode)

- [ ] **Step 2: Verify explorer renders in both modes**

Run: `cd frontend && npm run dev`
Open: `http://localhost:3000/explorer`
Expected: Grid view shows miners/validators. Clicking one shows detail. Toggle switches data source.

- [ ] **Step 3: Commit**

```bash
git add app/explorer/page.tsx
git commit -m "feat(frontend): wire explorer to useNetworkData with testnet toggle"
```

---

### Task 8: Submit Page Coming-Soon Toggle

**Files:**
- Modify: `frontend/app/submit/page.tsx`

- [ ] **Step 1: Add disabled toggle to submit page**

Add the import and toggle to the submit page header. No data changes needed.

```tsx
// Add import:
import { DataSourceToggle } from "@/components/data-source-toggle";

// Add toggle next to the page heading (inside the input phase or always visible):
<div className="flex items-center justify-between">
  <h1 className="text-2xl font-bold text-[--color-ink]">Submit Task</h1>
  <DataSourceToggle mode="coming-soon" />
</div>
```

- [ ] **Step 2: Verify tooltip appears**

Run: `cd frontend && npm run dev`
Open: `http://localhost:3000/submit`
Expected: Toggle visible, "Testnet" side greyed out, hovering shows "Coming Soon" tooltip.

- [ ] **Step 3: Commit**

```bash
git add app/submit/page.tsx
git commit -m "feat(frontend): add coming-soon toggle to submit page"
```

---

### Task 9: End-to-End Verification

- [ ] **Step 1: Get a Taostats API key**

Sign up at https://taostats.io and get a free API key. Add it to `frontend/.env.local`:

```
TAOSTATS_API_KEY=your-actual-key
```

- [ ] **Step 2: Test mock mode on all pages**

Run: `cd frontend && npm run dev`

Verify:
- Dashboard: mock data, full columns, all sections visible
- Explorer: mock miners/validators grid and detail views
- Submit: mock simulation works, toggle shows "Coming Soon" for testnet

- [ ] **Step 3: Test testnet mode on dashboard and explorer**

Click toggle to "Testnet" on dashboard:
- Should show loading skeleton
- Then real metagraph data (UIDs 0, 1, 2 from your subnet)
- Reduced columns (no success/cost/latency/reliability)
- Testnet info banner visible

Navigate to explorer — should still be in testnet mode (persisted):
- Grid shows real UIDs
- Click a UID — detail shows chain data

- [ ] **Step 4: Test error handling**

Temporarily remove `TAOSTATS_API_KEY` from `.env.local`. Restart dev server.
Toggle to testnet — should show error banner with retry button.
Restore the key and click retry — should load data.

- [ ] **Step 5: Test persistence**

Toggle to testnet, refresh page — should still be testnet.
Toggle to mock, navigate between pages — should stay mock.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(frontend): complete testnet/mock toggle with Taostats integration"
```

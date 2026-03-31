"use client";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { mockTasks, mockAuditFlags } from "@/lib/mock-data";
import { scoring, network } from "@/lib/constants";
import { StatCard } from "@/components/stat-card";
import { DataTable } from "@/components/data-table";
import { WeightBar } from "@/components/weight-bar";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { EmissionSankey } from "@/components/emission-sankey";
import { formatScore, formatPercent } from "@/lib/utils";
import { CopyableAddress } from "@/components/copyable-address";
import { useNetworkData } from "@/lib/use-network-data";
import { useDataSource } from "@/lib/data-source-context";
import { DataSourceToggle } from "@/components/data-source-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MinerProfile } from "@/lib/types";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

export default function DashboardPage() {
  const router = useRouter();
  const { source } = useDataSource();
  const { miners, validators, networkStats, loading, error, retry } = useNetworkData();
  const isTestnet = source === "testnet";
  const execProgress = networkStats.tasks_this_tempo / network.execSupportMin;
  const sortedMiners = [...miners].sort((a, b) => b.scores.composite - a.scores.composite);

  const sharedColumns = [
    { key: "uid", label: "UID", render: (m: MinerProfile) => <span className="font-mono text-ink font-semibold">{m.uid}</span>, sortValue: (m: MinerProfile) => m.uid, mono: true },
    { key: "hotkey", label: "Hotkey", render: (m: MinerProfile) => <CopyableAddress address={m.hotkey} className="text-ink-tertiary text-xs" />, mono: true },
    { key: "stake", label: "Stake", render: (m: MinerProfile) => <span className="font-mono text-ink-secondary">{m.stake.toLocaleString()} {isTestnet ? "\u05D1" : "\u03C4"}</span>, sortValue: (m: MinerProfile) => m.stake, mono: true, align: "right" as const },
    { key: "composite", label: isTestnet ? "Incentive" : "Score", render: (m: MinerProfile) => <span className="font-bold text-ink">{formatScore(m.scores.composite)}</span>, sortValue: (m: MinerProfile) => m.scores.composite, mono: true, align: "right" as const },
  ];

  const mockColumns = [
    { key: "success", label: "Success", render: (m: MinerProfile) => <span className="text-ink-secondary">{formatScore(m.scores.success)}</span>, sortValue: (m: MinerProfile) => m.scores.success, mono: true, align: "right" as const },
    { key: "cost", label: "Cost", render: (m: MinerProfile) => <span className="text-ink-secondary">{formatScore(m.scores.cost)}</span>, sortValue: (m: MinerProfile) => m.scores.cost, mono: true, align: "right" as const },
    { key: "latency", label: "Latency", render: (m: MinerProfile) => <span className="text-ink-secondary">{formatScore(m.scores.latency)}</span>, sortValue: (m: MinerProfile) => m.scores.latency, mono: true, align: "right" as const },
    { key: "reliability", label: "Rel.", render: (m: MinerProfile) => <span className="text-ink-secondary">{formatScore(m.scores.reliability)}</span>, sortValue: (m: MinerProfile) => m.scores.reliability, mono: true, align: "right" as const },
    { key: "tasks", label: "Tasks", render: (m: MinerProfile) => (
      <div className="flex items-center gap-2 justify-end">
        <span className="text-ink-secondary">{m.tasks_seen}</span>
        {m.tasks_seen < scoring.warmupThreshold && <Badge variant="outline" className="border-gold/30 text-gold bg-gold/5 px-1.5 py-0 text-[10px]">warmup</Badge>}
      </div>
    ), sortValue: (m: MinerProfile) => m.tasks_seen, mono: true, align: "right" as const },
    { key: "weight", label: "Weight", render: (m: MinerProfile) => <div className="w-24 ml-auto"><WeightBar weight={m.weight} capped={m.weight_capped} /></div>, sortValue: (m: MinerProfile) => m.weight, align: "right" as const },
  ];

  const testnetColumns = [
    { key: "emission", label: "Emission", render: (m: MinerProfile) => <span className="font-mono text-teal font-semibold">{formatScore(m.weight)}</span>, sortValue: (m: MinerProfile) => m.weight, mono: true, align: "right" as const },
    { key: "immunity", label: "Immunity", render: (m: MinerProfile) => (
      <span className={`rounded-md px-2 py-1 text-[10px] font-medium ${m.immunity_active ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" : "bg-surface-2 text-ink-tertiary"}`}>
        {m.immunity_active ? `${m.immunity_blocks_remaining} blocks` : "none"}
      </span>
    ), mono: true, align: "right" as const },
  ];

  const minerColumns = [
    ...sharedColumns,
    ...(!isTestnet ? mockColumns : testnetColumns),
  ];

  return (
    <div className="space-y-10 pb-12">
      <div className="flex items-center justify-between mt-4">
        <h1 className="text-3xl font-extrabold tracking-tight text-ink">Network Dashboard</h1>
        <DataSourceToggle mode="enabled" />
      </div>

      {error && (
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="flex items-center justify-between rounded-xl border border-error/30 bg-error/10 px-5 py-4 backdrop-blur-sm">
          <span className="text-sm font-medium text-error">{error}</span>
          <Button variant="outline" size="sm" onClick={retry} className="border-error/20 text-error hover:bg-error/20">Retry</Button>
        </motion.div>
      )}

      {isTestnet && !loading && (
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="rounded-xl border border-teal/30 bg-teal/5 px-5 py-3 text-sm font-medium text-teal backdrop-blur-sm">
          Showing live data from Bittensor testnet (netuid 26). Score breakdown columns are only available in mock mode.
        </motion.div>
      )}

      {loading ? (
        <div className="space-y-10">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl border border-border bg-surface-1" />
            ))}
          </div>
          <div className="h-80 animate-pulse rounded-2xl border border-border bg-surface-1" />
        </div>
      ) : (
      <>
      {/* Network Overview */}
      <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Current Block" value={networkStats.current_block} accent />
        <StatCard label="Current Tempo" value={networkStats.current_tempo} sublabel={`Block / ${network.tempo}`} />
        {isTestnet ? (
          <>
            <StatCard label="Active Miners" value={networkStats.active_miners} />
            <StatCard label="Active Validators" value={networkStats.active_validators} />
          </>
        ) : (
          <>
            <StatCard label="Tasks This Tempo" value={networkStats.tasks_this_tempo} />
            <div className="rounded-2xl border border-border bg-surface-0/60 p-5 shadow-sm backdrop-blur-md transition-colors hover:bg-surface-0">
              <p className="text-xs font-semibold uppercase tracking-widest text-ink-tertiary">Exec Support Eligibility</p>
              <p className="mt-2 font-mono text-base font-bold text-ink-secondary tabular-nums">{networkStats.tasks_this_tempo} / {network.execSupportMin}</p>
              <div className="mt-3 h-2.5 rounded-full bg-surface-2 overflow-hidden shadow-inner">
                <div className={`h-full rounded-full transition-all duration-500 ${execProgress >= 1 ? "bg-success" : "bg-teal"}`} style={{ width: `${Math.min(execProgress * 100, 100)}%` }} />
              </div>
            </div>
          </>
        )}
      </motion.div>

      {/* Miner Leaderboard */}
      <motion.section initial="hidden" animate="visible" variants={fadeInUp}>
        <h2 className="mb-5 text-sm font-semibold uppercase tracking-widest text-teal">Miner Leaderboard</h2>
        {sortedMiners.length === 0 ? (
          <div className="rounded-2xl border border-border bg-surface-0/50 p-10 text-center text-sm font-medium text-ink-tertiary backdrop-blur-md">
            No miners found{isTestnet ? " on testnet" : ""}. {isTestnet && "The subnet may not have active miners yet."}
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-border bg-surface-0/80 shadow-sm backdrop-blur-md">
            <DataTable
              columns={minerColumns}
              data={sortedMiners}
              keyField="uid"
              onRowClick={(m) => router.push(`/explorer?uid=${m.uid}`)}
            />
          </div>
        )}
      </motion.section>

      {/* Scoring Formula + Benchmark Tasks */}
      {!isTestnet && (
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className="grid gap-8 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md transition-all hover:bg-surface-0">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Scoring Formula</h2>
          <div className="mb-6 rounded-xl border border-border bg-surface-1 p-4 shadow-inner">
            <p className="font-mono text-sm text-ink-secondary text-center font-medium">
              S = {Object.entries(scoring.weights).map(([k, v]) => `${v.toFixed(2)}x${k}`).join(" + ")}
            </p>
          </div>
          <div className="space-y-4">
            {Object.entries(scoring.weights).map(([key, weight]) => (
              <div key={key} className="flex items-center gap-4">
                <span className="w-24 text-sm font-semibold text-ink-secondary capitalize">{key}</span>
                <div className="flex-1 h-2 rounded-full bg-surface-2 overflow-hidden shadow-inner">
                  <div className="h-full rounded-full bg-teal" style={{ width: `${weight * 100}%` }} />
                </div>
                <span className="w-12 text-right font-mono text-xs font-bold tabular-nums text-ink-tertiary">{(weight * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-lg border border-gold/30 bg-gold/10 px-4 py-3 text-xs font-medium text-gold">
            Success gate: {scoring.successGate} — cost &amp; latency only scored above this threshold
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md hover:bg-surface-0 transition-all">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Benchmark Tasks</h2>
          <div className="space-y-4">
            {mockTasks.map((task) => (
              <div
                key={task.task_id}
                onClick={() => router.push(`/task/${task.task_id}`)}
                className="group flex cursor-pointer items-center gap-4 rounded-xl border border-border bg-surface-1 px-5 py-4 transition-all hover:border-teal/30 hover:bg-surface-1/50 hover:shadow-md hover:-translate-y-0.5"
              >
                <div className="rounded-full bg-surface-0 p-2 shadow-sm text-teal group-hover:bg-teal/10">
                  <TaskTypeIcon type={task.task_type} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-xs font-semibold text-ink-secondary group-hover:text-teal transition-colors">{task.task_id}</p>
                  <p className="truncate text-sm font-medium text-ink mt-0.5">{task.description}</p>
                </div>
                <LifecycleBadge status={task.status} />
              </div>
            ))}
          </div>
        </section>
      </motion.div>
      )}

      {/* Weight Distribution */}
      {!isTestnet && (
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="mb-5 text-sm font-semibold uppercase tracking-widest text-teal">Weight Distribution</h2>
        <div className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
          <div className="space-y-4">
            {sortedMiners.map((m) => (
              <div key={m.uid} className="flex items-center gap-4">
                <span className="w-16 font-mono text-sm font-semibold text-ink-secondary">UID {m.uid}</span>
                <div className="flex-1 h-5 rounded-md bg-surface-2 relative shadow-inner overflow-hidden">
                  <div
                    className={`h-full transition-all ${m.weight_capped ? "bg-gold" : "bg-teal"}`}
                    style={{ width: `${(m.weight / 0.20) * 100}%` }}
                  />
                  <div className="absolute top-0 h-full w-0.5 bg-error opacity-70" style={{ left: `${(0.15 / 0.20) * 100}%` }} />
                </div>
                <span className="w-16 text-right font-mono text-sm font-bold tabular-nums text-ink-tertiary">{formatPercent(m.weight)}</span>
              </div>
            ))}
          </div>
          <p className="mt-5 text-xs font-medium text-ink-muted flex items-center gap-2">
            <span className="inline-block w-3 h-3 bg-error rounded-full opacity-70"></span>
            Red line = 15% cap. Excess redistributed to uncapped miners.
          </p>
        </div>
      </motion.section>
      )}

      {/* Emission Flow */}
      {!isTestnet && (
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="mb-5 text-sm font-semibold uppercase tracking-widest text-teal">Emission Flow</h2>
        <div className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
           <EmissionSankey />
        </div>
      </motion.section>
      )}

      {/* Audit Flags + Validator Status */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className={`grid gap-8 ${!isTestnet ? "lg:grid-cols-2" : ""}`}>
        {!isTestnet && (
        <section className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Audit Flags</h2>
          <div className="space-y-4">
            {mockAuditFlags.map((flag, i) => (
              <div key={i} className="rounded-xl border border-gold/30 bg-gold/5 px-5 py-4 transition-all hover:bg-gold/10 hover:shadow-sm">
                <div className="flex items-center justify-between border-b border-gold/20 pb-2 mb-2">
                  <span className="font-mono text-sm font-bold text-ink">UID {flag.uid}</span>
                  <span className="font-mono text-xs font-medium text-ink-tertiary">Block {flag.block.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-4 font-mono text-xs font-medium mb-2">
                  <span className="text-ink-secondary">Score: {formatScore(flag.score)}</span>
                  <span className="text-ink-tertiary">Avg: {formatScore(flag.previous_avg)}</span>
                  <Badge variant="outline" className="border-gold text-gold bg-gold/10 px-1 py-0 shadow-none">+{flag.jump_percent.toFixed(1)}%</Badge>
                </div>
                <p className="text-xs font-medium text-ink-tertiary">{flag.message}</p>
              </div>
            ))}
          </div>
        </section>
        )}

        <section className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Validator Status</h2>
          <div className="space-y-4">
            {validators.map((v) => (
              <div key={v.uid} className="rounded-xl border border-border bg-surface-1 px-5 py-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-base font-bold text-ink">UID {v.uid}</span>
                    <CopyableAddress address={v.hotkey} className="text-xs text-ink-tertiary" />
                  </div>
                  <Badge variant="secondary" className="bg-purple/15 text-purple hover:bg-purple/25 shadow-none border-none">validator</Badge>
                </div>
                <div className="grid grid-cols-4 gap-4 text-xs">
                  <div>
                    <p className="text-[10px] uppercase font-medium text-ink-muted">Stake</p>
                    <p className="font-mono text-sm font-bold tabular-nums text-gold mt-1">{v.stake.toLocaleString()} {isTestnet ? "\u05D1" : "\u03C4"}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-medium text-ink-muted">VTrust</p>
                    <p className="font-mono text-sm font-bold tabular-nums text-ink mt-1">{formatScore(v.vtrust)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-medium text-ink-muted">Scoring</p>
                    <p className="font-mono text-sm font-bold text-ink-secondary mt-1">{v.scoring_version}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-medium text-ink-muted">Benchmark</p>
                    <p className="font-mono text-sm font-bold text-ink-secondary mt-1">{v.benchmark_version}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </motion.div>
      </>
      )}
    </div>
  );
}

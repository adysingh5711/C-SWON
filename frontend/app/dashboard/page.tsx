"use client";
import { useRouter } from "next/navigation";
import { mockMiners, mockValidators, mockTasks, mockNetworkStats, mockAuditFlags } from "@/lib/mock-data";
import { scoring, network } from "@/lib/constants";
import { StatCard } from "@/components/stat-card";
import { DataTable } from "@/components/data-table";
import { WeightBar } from "@/components/weight-bar";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { EmissionSankey } from "@/components/emission-sankey";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import type { MinerProfile } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const execProgress = mockNetworkStats.tasks_this_tempo / network.execSupportMin;
  const sortedMiners = [...mockMiners].sort((a, b) => b.scores.composite - a.scores.composite);

  const minerColumns = [
    { key: "uid", label: "UID", render: (m: MinerProfile) => <span className="font-mono text-[--color-ink]">{m.uid}</span>, sortValue: (m: MinerProfile) => m.uid, mono: true },
    { key: "hotkey", label: "Hotkey", render: (m: MinerProfile) => <span className="text-[--color-ink-tertiary]">{truncateKey(m.hotkey)}</span>, mono: true },
    { key: "composite", label: "Score", render: (m: MinerProfile) => <span className="font-bold text-[--color-ink]">{formatScore(m.scores.composite)}</span>, sortValue: (m: MinerProfile) => m.scores.composite, mono: true, align: "right" as const },
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
  ];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-[--color-ink]">Network Dashboard</h1>

      {/* Network Overview */}
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

      {/* Miner Leaderboard */}
      <section>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Miner Leaderboard</h2>
        <DataTable
          columns={minerColumns}
          data={sortedMiners}
          keyField="uid"
          onRowClick={(m) => router.push(`/explorer?uid=${m.uid}`)}
        />
      </section>

      {/* Scoring Formula + Benchmark Tasks (two-column) */}
      <div className="grid gap-8 lg:grid-cols-2">
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
            Success gate: {scoring.successGate} — cost &amp; latency only scored above this threshold
          </div>
        </section>

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

      {/* Weight Distribution */}
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
                  <div className="absolute top-0 h-full w-px bg-red-400/60" style={{ left: `${(0.15 / 0.20) * 100}%` }} />
                </div>
                <span className="w-14 text-right font-mono text-xs tabular-nums text-[--color-ink-tertiary]">{formatPercent(m.weight)}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[10px] text-[--color-ink-muted]">Red line = 15% cap. Excess redistributed to uncapped miners.</p>
        </div>
      </section>

      {/* Emission Flow */}
      <section>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Emission Flow</h2>
        <EmissionSankey />
      </section>

      {/* Audit Flags + Validator Status (two-column) */}
      <div className="grid gap-8 lg:grid-cols-2">
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

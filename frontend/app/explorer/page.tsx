"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import { mockMiners, mockValidators } from "@/lib/mock-data";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { ScoreGauge } from "@/components/score-gauge";
import { WeightBar } from "@/components/weight-bar";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import { scoring } from "@/lib/constants";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts";

function ExplorerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const uidParam = searchParams.get("uid");

  if (!uidParam) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold text-[--color-ink]">Network Explorer</h1>

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

        {/* Scoring Profile + Gauges */}
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
                <Tooltip contentStyle={{ backgroundColor: "var(--color-surface-2)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12, fontFamily: "var(--font-mono)" }} />
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

  return null;
}

export default function ExplorerPage() {
  return (
    <Suspense fallback={<div className="text-[--color-ink-secondary]">Loading...</div>}>
      <ExplorerContent />
    </Suspense>
  );
}

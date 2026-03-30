"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import { motion } from "framer-motion";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { ScoreGauge } from "@/components/score-gauge";
import { WeightBar } from "@/components/weight-bar";
import { truncateKey, formatScore, formatPercent } from "@/lib/utils";
import { scoring } from "@/lib/constants";
import { useNetworkData } from "@/lib/use-network-data";
import { useDataSource } from "@/lib/data-source-context";
import { DataSourceToggle } from "@/components/data-source-toggle";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

function ExplorerContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const uidParam = searchParams.get("uid");
  const { source } = useDataSource();
  const { miners, validators, loading, error, retry } = useNetworkData();
  const isTestnet = source === "testnet";

  if (loading) {
    return (
      <div className="space-y-10 pb-12">
        <div className="flex items-center justify-between mt-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink">Network Explorer</h1>
          <DataSourceToggle mode="enabled" />
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-2xl border border-border bg-surface-1" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-10 pb-12">
        <div className="flex items-center justify-between mt-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink">Network Explorer</h1>
          <DataSourceToggle mode="enabled" />
        </div>
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="flex items-center justify-between rounded-xl border border-error/30 bg-error/10 px-5 py-4 backdrop-blur-sm">
          <span className="text-sm font-medium text-error">{error}</span>
          <Button variant="outline" size="sm" onClick={retry} className="border-error/20 text-error hover:bg-error/20">Retry</Button>
        </motion.div>
      </div>
    );
  }

  if (!uidParam) {
    return (
      <div className="space-y-10 pb-12">
        <div className="flex items-center justify-between mt-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink">Network Explorer</h1>
          <DataSourceToggle mode="enabled" />
        </div>

        <motion.section initial="hidden" animate="visible" variants={fadeInUp}>
          <h2 className="mb-5 text-sm font-semibold uppercase tracking-widest text-teal">Miners</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {miners.map((m) => (
              <div
                key={m.uid}
                onClick={() => router.push(`/explorer?uid=${m.uid}`)}
                className="group cursor-pointer rounded-2xl border border-border bg-surface-0/50 p-6 shadow-sm backdrop-blur-md transition-all hover:-translate-y-1 hover:bg-surface-0"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-base font-bold text-ink">UID {m.uid}</span>
                  <Badge variant="outline" className="border-teal/30 text-teal bg-teal/5">miner</Badge>
                </div>
                <p className="mt-2 font-mono text-xs text-ink-tertiary group-hover:text-ink-secondary transition-colors">{truncateKey(m.hotkey)}</p>
                <div className="mt-5 flex items-end justify-between">
                  <div>
                    <p className="text-[10px] uppercase font-medium text-ink-muted mb-1">Composite Score</p>
                    <span className="font-mono text-xl font-bold text-ink">{formatScore(m.scores.composite)}</span>
                  </div>
                  <span className="font-mono text-sm font-medium text-ink-tertiary">{m.tasks_seen} tasks</span>
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
          <h2 className="mb-5 text-sm font-semibold uppercase tracking-widest text-teal">Validators</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {validators.map((v) => (
              <div key={v.uid} className="rounded-2xl border border-border bg-surface-0/50 p-6 shadow-sm backdrop-blur-md">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-base font-bold text-ink">UID {v.uid}</span>
                  <Badge variant="secondary" className="bg-purple/15 text-purple shadow-none border-none">validator</Badge>
                </div>
                <p className="mt-2 font-mono text-xs text-ink-tertiary">{truncateKey(v.hotkey)}</p>
                <div className="mt-5 grid grid-cols-2 gap-4 text-xs font-medium">
                  <div>
                    <p className="text-[10px] uppercase text-ink-muted mb-1">Stake</p>
                    <p className="font-mono text-sm font-bold tabular-nums text-gold">{v.stake.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase text-ink-muted mb-1">VTrust</p>
                    <p className="font-mono text-sm font-bold tabular-nums text-ink">{formatScore(v.vtrust)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.section>
      </div>
    );
  }

  const uid = Number(uidParam);
  const miner = miners.find((m) => m.uid === uid);
  const validator = validators.find((v) => v.uid === uid);

  if (!miner && !validator) {
    return <p className="text-ink-secondary mt-12 text-center">Participant UID {uid} not found.</p>;
  }

  if (miner) {
    const historyData = miner.score_history.map((score, i) => ({ task: i + 1, score }));
    const warmupScale = miner.tasks_seen < scoring.warmupThreshold
      ? miner.tasks_seen / scoring.warmupThreshold
      : 1;

    return (
      <div className="space-y-10 pb-12">
        {/* Identity Card */}
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="rounded-2xl border border-border bg-surface-0 p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="font-mono text-3xl font-extrabold text-ink">UID {miner.uid}</h1>
                <Badge variant="outline" className="border-teal/30 text-teal bg-teal/5">miner</Badge>
                {miner.immunity_active && (
                  <Badge variant="outline" className="border-gold/30 text-gold bg-gold/5">
                    immunity {miner.immunity_blocks_remaining > 0 && `(${miner.immunity_blocks_remaining.toLocaleString()} blocks)`}
                  </Badge>
                )}
              </div>
              <div className="space-y-1 font-mono text-sm text-ink-tertiary">
                <p>Hotkey: <span className="text-ink-secondary font-medium">{truncateKey(miner.hotkey, 10)}</span></p>
                <p>Coldkey: <span className="text-ink-secondary font-medium">{truncateKey(miner.coldkey, 10)}</span></p>
              </div>
            </div>
            <div className="sm:text-right rounded-xl border border-border bg-surface-1 p-5 self-start">
              <p className="text-[10px] sm:text-xs uppercase font-medium text-ink-muted">Stake</p>
              <p className="font-mono text-2xl font-bold tabular-nums text-gold mt-1">{miner.stake.toLocaleString()}</p>
              <p className="mt-2 text-[10px] text-ink-tertiary">Registered at block {miner.registration_block.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>

        {/* Scoring Profile + Gauges */}
        {isTestnet ? (
          <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="rounded-2xl border border-border bg-surface-0/50 p-8 text-center text-sm font-medium text-ink-tertiary">
            Detailed score breakdown available in mock mode
          </motion.div>
        ) : (
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
              <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Scoring Profile</h2>
              <ScoreBreakdown scores={miner.scores} />
              {warmupScale < 1 && (
                <div className="mt-6 rounded-xl border border-gold/30 bg-gold/10 px-5 py-4 text-xs font-medium text-gold">
                  Warmup: {miner.tasks_seen}/{scoring.warmupThreshold} tasks — scale factor {warmupScale.toFixed(2)}
                </div>
              )}
              <div className="mt-6 rounded-xl border border-border bg-surface-1 p-5 shadow-inner">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">Weight</p>
                <WeightBar weight={miner.weight} capped={miner.weight_capped} />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-8 rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
              <ScoreGauge value={miner.scores.success} dimension="success" size={120} />
              <ScoreGauge value={miner.scores.cost} dimension="cost" size={120} />
              <ScoreGauge value={miner.scores.latency} dimension="latency" size={120} />
              <ScoreGauge value={miner.scores.reliability} dimension="reliability" size={120} />
            </div>
          </motion.div>
        )}

        {/* Score History Chart */}
        {!isTestnet && miner.score_history.length > 0 && (
          <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className="rounded-2xl border border-border bg-surface-0 p-8 shadow-sm">
            <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Score History (Last {miner.score_history.length} Tasks)</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                  <XAxis dataKey="task" stroke="var(--ink-tertiary)" tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={false} dy={10} />
                  <YAxis domain={[0, 1]} stroke="var(--ink-tertiary)" tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={false} dx={-10} />
                  <Tooltip contentStyle={{ backgroundColor: "var(--surface-0)", border: "1px solid var(--border-color)", borderRadius: 12, fontSize: 13, fontFamily: "var(--font-mono)", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }} />
                  <Line type="monotone" dataKey="score" stroke="var(--teal)" strokeWidth={2.5} dot={false} activeDot={{ r: 6, fill: "var(--teal)", stroke: "var(--surface-0)" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.section>
        )}

        {/* Subnet Profiler */}
        {!isTestnet && Object.keys(miner.subnet_stats).length > 0 && (
          <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp} className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
            <h2 className="mb-6 text-sm font-semibold uppercase tracking-widest text-teal">Subnet Profiler</h2>
            <div className="overflow-hidden rounded-xl border border-border bg-surface-1">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-surface-2 text-left text-xs font-semibold uppercase tracking-wider text-ink-tertiary">
                      <th className="py-3 px-5">Subnet</th>
                      <th className="py-3 px-5 text-right">Avg Cost</th>
                      <th className="py-3 px-5 text-right">Avg Latency</th>
                      <th className="py-3 px-5 text-right">Reliability</th>
                      <th className="py-3 px-5 text-right">Observations</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {Object.entries(miner.subnet_stats).map(([subnet, stats]) => (
                      <tr key={subnet} className="transition-colors hover:bg-surface-2/50">
                        <td className="py-4 px-5 font-mono text-teal font-medium">{subnet}</td>
                        <td className="py-4 px-5 text-right font-mono tabular-nums text-gold">{stats.avg_cost.toFixed(4)}</td>
                        <td className="py-4 px-5 text-right font-mono tabular-nums text-ink-secondary">{stats.avg_latency.toFixed(2)}s</td>
                        <td className="py-4 px-5 text-right font-mono tabular-nums text-ink font-medium">{formatPercent(stats.reliability)}</td>
                        <td className="py-4 px-5 text-right font-mono tabular-nums text-ink-tertiary">{stats.observations}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.section>
        )}
      </div>
    );
  }

  if (validator) {
    return (
      <div className="space-y-10 pb-12">
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="rounded-2xl border border-border bg-surface-0 p-8 shadow-sm">
          <div className="flex items-center gap-4 mb-4">
            <h1 className="font-mono text-3xl font-extrabold text-ink">UID {validator.uid}</h1>
            <Badge variant="secondary" className="bg-purple/15 text-purple shadow-none border-none">validator</Badge>
          </div>
          <div className="space-y-1 font-mono text-sm text-ink-tertiary">
            <p>Hotkey: <span className="text-ink-secondary">{truncateKey(validator.hotkey, 10)}</span></p>
            <p>Coldkey: <span className="text-ink-secondary">{truncateKey(validator.coldkey, 10)}</span></p>
          </div>
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-6 rounded-xl border border-border bg-surface-1 p-6">
            <div>
              <p className="text-[10px] uppercase font-medium text-ink-muted">Stake</p>
              <p className="font-mono text-2xl font-bold tabular-nums text-gold mt-1">{validator.stake.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-medium text-ink-muted">VTrust</p>
              <p className="font-mono text-xl font-bold tabular-nums text-ink mt-2">{formatScore(validator.vtrust)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-medium text-ink-muted">Scoring Version</p>
              <p className="font-mono text-base font-bold text-ink-secondary mt-2">{validator.scoring_version}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-medium text-ink-muted">Last Weight Set</p>
              <p className="font-mono text-base font-medium tabular-nums text-ink-secondary mt-2">{validator.last_weight_set_block.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  return null;
}

export default function ExplorerPage() {
  return (
    <Suspense fallback={<div className="mt-12 text-center text-ink-secondary animate-pulse">Loading explorer...</div>}>
      <ExplorerContent />
    </Suspense>
  );
}

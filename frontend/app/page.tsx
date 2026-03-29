"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { mockNetworkStats } from "@/lib/mock-data";
import { StatCard } from "@/components/stat-card";
import { EmissionSankey } from "@/components/emission-sankey";

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
    <div className="space-y-24">
      {/* Hero */}
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

      {/* How It Works */}
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

      {/* Scoring Formula */}
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
          Success gate: Cost &amp; latency only count if success &gt; 70%
        </p>
      </section>

      {/* Emission Structure */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Emission Structure</h2>
        <div className="mx-auto mt-6 max-w-lg">
          <EmissionSankey />
        </div>
        <p className="mt-4 text-center text-xs text-[--color-ink-secondary]">
          dTAO Alpha token model — TAO injected into AMM pool, Alpha distributed via Yuma Consensus
        </p>
      </section>

      {/* Network Stats */}
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

      {/* Footer */}
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

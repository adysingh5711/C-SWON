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

const workflows = [
  { name: "Content Multi-Gen", trigger: "Raw Transcript", path: "Subnet 1 (STT) → Subnet 11 (LLM) → Subnet 19 (Image)", result: "Video script + Blog + Thumbnails" },
  { name: "RAG Engine", trigger: "PDF Query", path: "Subnet 13 (Retrieval) → Subnet 11 (LLM Summarization)", result: "Verified Answer" },
  { name: "Autonomous Agent", trigger: "Code Request", path: "Subnet 11 (Planner) → Subnet 18 (Execution) → Subnet 3 (Search)", result: "Debugged Code Repo" },
];

const faqs = [
  { q: "What is C-SWON?", a: "C-SWON stands for Cross-Subnet Workflow Orchestration Network. It's a Bittensor subnet that allows users to execute complex tasks by chaining multiple specialized subnets together automatically." },
  { q: "How do miners earn rewards?", a: "Miners earn rewards by designing the most efficient and successful execution plans (DAGs) for user tasks. They are scored based on success rate, cost efficiency, latency, and reliability." },
  { q: "Is it fully decentralized?", a: "Yes, C-SWON leverages Bittensor's decentralized infrastructure, where validators ensure the integrity of workflow execution and miners compete in an open marketplace." },
];

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": faqs.map(f => ({
    "@type": "Question",
    "name": f.q,
    "acceptedAnswer": {
      "@type": "Answer",
      "text": f.a
    }
  }))
};

const techArticleSchema = {
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "C-SWON: The Intelligence Layer for Multi-Subnet Composition",
  "description": "Learn how C-SWON orchestrates complex workflows across the Bittensor network using specialized subnets.",
  "author": {
    "@type": "Organization",
    "name": "C-SWON Network"
  },
  "image": "https://c-swon.vercel.app/images/og-image.png"
};

export default function LandingPage() {
  return (
    <div className="space-y-24">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(techArticleSchema) }}
      />
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

      {/* Workflow Examples */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Orchestration Examples</h2>
        <div className="mt-8 overflow-x-auto rounded-lg border border-[--color-border] bg-[--color-surface-0]">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[--color-border] bg-[--color-surface-1]">
              <tr>
                <th className="px-6 py-4 font-semibold text-[--color-ink]">Workflow</th>
                <th className="px-6 py-4 font-semibold text-[--color-ink]">Trigger</th>
                <th className="px-6 py-4 font-semibold text-[--color-ink]">Subnet Path</th>
                <th className="px-6 py-4 font-semibold text-[--color-ink]">Final Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[--color-border]">
              {workflows.map((wf) => (
                <tr key={wf.name} className="transition-colors hover:bg-[--color-surface-1]">
                  <td className="px-6 py-4 font-medium text-[--color-teal]">{wf.name}</td>
                  <td className="px-6 py-4 text-[--color-ink-secondary]">{wf.trigger}</td>
                  <td className="px-6 py-4 font-mono text-xs text-[--color-ink-tertiary]">{wf.path}</td>
                  <td className="px-6 py-4 text-[--color-ink-secondary]">{wf.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
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

      {/* Python Interaction Snippet */}
      {/* <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Developer Integration</h2>
        <div className="mx-auto mt-8 max-w-3xl rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <div className="flex items-center justify-between border-b border-[--color-border] pb-4">
            <span className="font-mono text-xs text-[--color-ink-tertiary]">pip install bittensor</span>
            <span className="rounded bg-[--color-teal]/10 px-2 py-1 text-[10px] uppercase text-[--color-teal]">Python 3.10+</span>
          </div>
          <pre className="mt-6 overflow-x-auto font-mono text-sm leading-relaxed text-[--color-ink-secondary]">
{`import bittensor as bt
from cswon.protocol import WorkflowSynapse

wallet = bt.wallet(name="my_wallet")
dendrite = bt.dendrite(wallet=wallet)
metagraph = bt.metagraph(netuid=NETUID)

# Query the top-performing miner for a workflow plan
miner_axon = metagraph.axons[top_miner_uid]
synapse = WorkflowSynapse(
    description="Analyze 2024 AI trends and generate a summary report.",
    constraints={"max_budget_tao": 0.1, "max_latency_seconds": 30}
)

response = await dendrite.forward(axons=[miner_axon], synapse=synapse)
print("Workflow Plan:", response.workflow_plan)`}
          </pre>
        </div>
      </section> */}

      {/* FAQ Section */}
      <section>
        <h2 className="text-center text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Frequently Asked Questions</h2>
        <div className="mx-auto mt-8 max-w-2xl divide-y divide-[--color-border]">
          {faqs.map((faq) => (
            <div key={faq.q} className="py-6">
              <h3 className="text-lg font-semibold text-[--color-ink]">{faq.q}</h3>
              <p className="mt-2 text-[--color-ink-secondary]">{faq.a}</p>
            </div>
          ))}
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

"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { mockNetworkStats } from "@/lib/mock-data";
import { StatCard } from "@/components/stat-card";
import { EmissionSankey } from "@/components/emission-sankey";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const steps = [
  { num: "01", title: "Describe a Task", desc: "User submits a complex AI task — code generation, RAG, agent workflow, or data transformation.", color: "text-teal" },
  { num: "02", title: "Miners Compete", desc: "Miners design optimized multi-subnet workflow DAGs. Each plan routes work across specialized subnets.", color: "text-gold" },
  { num: "03", title: "Validate & Reward", desc: "Validators execute, score on success/cost/latency/reliability, and reward the best orchestration strategies.", color: "text-purple" },
];

const scoreDimensions = [
  { label: "Success", weight: "50%", desc: "Output quality x completion ratio — did the workflow produce correct results?", color: "bg-success" },
  { label: "Cost", weight: "25%", desc: "Budget efficiency — how much TAO was spent vs. the maximum allowed?", color: "bg-gold" },
  { label: "Latency", weight: "15%", desc: "Speed — how quickly did the workflow complete vs. the deadline?", color: "bg-teal" },
  { label: "Reliability", weight: "10%", desc: "Fault tolerance — how few retries, timeouts, or failures occurred?", color: "bg-purple" },
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

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

export default function LandingPage() {
  return (
    <div className="relative space-y-32 pb-0">
      {/* Background Decor */}
      <div className="absolute inset-x-0 top-0 -z-10 transform-gpu overflow-hidden blur-3xl" aria-hidden="true">
        <div
          className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-teal to-purple opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
          style={{
            clipPath: 'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)'
          }}
        />
      </div>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(techArticleSchema) }} />

      {/* Hero Section */}
      <section className="relative pt-20 pb-16 text-center">
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="mx-auto max-w-3xl">
          <Badge variant="secondary" className="mb-6 font-mono text-xs uppercase tracking-widest text-teal bg-teal/10 hover:bg-teal/20">
            Bittensor Subnet
          </Badge>
          <h1 className="mt-4 text-5xl font-extrabold tracking-tight text-ink sm:text-7xl">
            Zapier for Subnets
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-secondary sm:text-xl">
            The Intelligence Layer for Multi-Subnet Composition. Turn any complex AI task into an optimized multi-subnet workflow effortlessly.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Button size="lg" asChild className="rounded-full px-8 text-base shadow-lg shadow-teal/20">
              <Link href="/submit">Try a Task</Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="rounded-full px-8 text-base bg-surface-0/50 backdrop-blur-md">
              <Link href="/dashboard">View Network</Link>
            </Button>
          </div>
        </motion.div>
      </section>

      {/* How It Works */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <div className="text-center">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-teal">How It Works</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-ink sm:text-4xl">Decentralized Orchestration</p>
        </div>
        <div className="mx-auto mt-12 grid max-w-6xl gap-6 md:grid-cols-3">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2, duration: 0.6 }}
              className="group relative rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-lg transition-all hover:shadow-xl hover:border-teal/30 hover:-translate-y-1"
            >
              <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-teal/30 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
              <span className={`inline-block font-mono text-3xl font-black ${step.color}`}>{step.num}</span>
              <h3 className="mt-4 text-xl font-bold text-ink">{step.title}</h3>
              <p className="mt-3 leading-relaxed text-ink-secondary">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Workflow Examples */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <div className="text-center">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-teal">Orchestration Examples</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-ink sm:text-4xl">Real-world AI Workflows</p>
        </div>
        <div className="mx-auto mt-12 max-w-6xl overflow-hidden rounded-2xl border border-border bg-surface-0/80 shadow-sm backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-1 font-medium text-ink">
                <tr>
                  <th className="px-6 py-4">Workflow</th>
                  <th className="px-6 py-4">Trigger</th>
                  <th className="px-6 py-4">Subnet Path</th>
                  <th className="px-6 py-4">Final Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {workflows.map((wf) => (
                  <tr key={wf.name} className="transition-colors hover:bg-surface-1/50">
                    <td className="px-6 py-5 font-semibold text-teal">{wf.name}</td>
                    <td className="px-6 py-5 text-ink-secondary">{wf.trigger}</td>
                    <td className="px-6 py-5 font-mono text-xs text-ink-tertiary">
                      <Badge variant="outline" className="font-mono">{wf.path}</Badge>
                    </td>
                    <td className="px-6 py-5 font-medium text-ink-secondary">{wf.result}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.section>

      {/* Scoring Formula */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-teal">Scoring Formula</h2>
        <div className="mx-auto mt-8 max-w-3xl rounded-2xl border border-border bg-surface-0/80 p-6 shadow-sm backdrop-blur-md">
          <p className="text-center font-mono text-base font-semibold text-ink">
            Score <span className="text-ink-secondary font-normal">=</span> 0.50<span className="text-ink-secondary font-normal">x</span>Success + 0.25<span className="text-ink-secondary font-normal">x</span>Cost + 0.15<span className="text-ink-secondary font-normal">x</span>Latency + 0.10<span className="text-ink-secondary font-normal">x</span>Reliability
          </p>
        </div>
        <div className="mx-auto mt-6 grid max-w-6xl gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {scoreDimensions.map((dim, i) => (
            <motion.div 
              key={dim.label} 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-xl border border-border bg-surface-0/50 p-5 shadow-sm transition-colors hover:bg-surface-1/50"
            >
              <div className="flex items-center gap-3">
                <div className={`h-2.5 w-2.5 rounded-full ${dim.color} shadow-sm`} />
                <span className="font-bold text-ink">{dim.label}</span>
                <span className="ml-auto font-mono text-sm font-medium text-ink-secondary">{dim.weight}</span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-tertiary">{dim.desc}</p>
            </motion.div>
          ))}
        </div>
        <p className="mt-6 text-center text-xs font-medium text-ink-tertiary">
          * Success gate: Cost &amp; latency only count if success &gt; 70%
        </p>
      </motion.section>

      {/* Emission Structure */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-teal">Emission Structure</h2>
        <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
          <EmissionSankey />
        </div>
        <p className="mt-6 text-center text-sm text-ink-secondary">
          dTAO Alpha token model — TAO injected into AMM pool, Alpha distributed via Yuma Consensus
        </p>
      </motion.section>

      {/* Network Stats */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-teal">Network Stats</h2>
        <div className="mx-auto mt-8 grid max-w-6xl gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard label="Active Miners" value={mockNetworkStats.active_miners} accent />
          <StatCard label="Active Validators" value={mockNetworkStats.active_validators} />
          <StatCard label="Tasks Evaluated" value={mockNetworkStats.tasks_evaluated} accent />
          <StatCard label="Current Tempo" value={mockNetworkStats.current_tempo} sublabel={`${mockNetworkStats.current_tempo} x 360 blocks`} />
          <StatCard label="Current Block" value={mockNetworkStats.current_block} />
        </div>
      </motion.section>

      {/* FAQ Section */}
      <motion.section initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={fadeInUp}>
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-teal">FAQ</h2>
        <div className="mx-auto mt-10 max-w-3xl divide-y divide-border">
          {faqs.map((faq) => (
            <div key={faq.q} className="py-6">
              <h3 className="text-xl font-bold text-ink">{faq.q}</h3>
              <p className="mt-3 text-lg text-ink-secondary">{faq.a}</p>
            </div>
          ))}
        </div>
      </motion.section>

    </div>
  );
}

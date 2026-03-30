"use client";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { TaskType, MinerResponse } from "@/lib/types";
import { mockTasks, mockWorkflowResponses, mockExecutionResults } from "@/lib/mock-data";
import { MinerCard } from "@/components/miner-card";
import { DagViewer } from "@/components/dag-viewer";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { useStepAnimator } from "@/components/step-animator";
import { SubnetChip } from "@/components/subnet-chip";
import { formatTao, formatLatency } from "@/lib/utils";
import { DataSourceToggle } from "@/components/data-source-toggle";
import { Button } from "@/components/ui/button";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

type Phase = "input" | "competing" | "dag" | "executing" | "results";

const exampleTasks = [
  { label: "Merge two sorted lists (code)", taskId: "code_001" },
  { label: "Bittensor consensus (RAG)", taskId: "rag_001" },
  { label: "Compound interest (agent)", taskId: "agent_001" },
  { label: "CSV to JSON (data)", taskId: "data_001" },
];

const allSubnets = ["sn1", "sn4", "sn8", "sn13", "sn21"];

// Default plan for hook initialization
const defaultPlan = mockWorkflowResponses.code_001[0].workflow_plan;

export default function SubmitPage() {
  const [phase, setPhase] = useState<Phase>("input");
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("code");
  const [budget, setBudget] = useState(0.02);
  const [maxLatency, setMaxLatency] = useState(15);
  const [selectedSubnets, setSelectedSubnets] = useState<string[]>(["sn1", "sn4"]);
  const [minerResponses, setMinerResponses] = useState<MinerResponse[]>([]);
  const [visibleMiners, setVisibleMiners] = useState<number>(0);
  const [selectedTaskId, setSelectedTaskId] = useState("code_001");

  const bestResponse = minerResponses.length > 0
    ? minerResponses.reduce((best, r) => (r.composite_score ?? 0) > (best.composite_score ?? 0) ? r : best)
    : null;

  // Always call hook unconditionally with best plan or default
  const animator = useStepAnimator(bestResponse?.workflow_plan ?? defaultPlan);

  function pickExample(taskId: string) {
    const task = mockTasks.find((t) => t.task_id === taskId);
    if (!task) return;
    setDescription(task.description);
    setTaskType(task.task_type);
    setBudget(task.constraints.max_budget_tao);
    setMaxLatency(task.constraints.max_latency_seconds);
    setSelectedSubnets(task.constraints.allowed_subnets);
    setSelectedTaskId(taskId);
  }

  async function handleSubmit() {
    setPhase("competing");
    const responses = mockWorkflowResponses[selectedTaskId] ?? mockWorkflowResponses.code_001;
    setMinerResponses(responses);

    for (let i = 0; i < responses.length; i++) {
      await new Promise((r) => setTimeout(r, 800 + Math.random() * 1500));
      setVisibleMiners(i + 1);
    }

    await new Promise((r) => setTimeout(r, 1000));
    setPhase("dag");
  }

  async function handleExecute() {
    setPhase("executing");
    await animator.execute();
    await new Promise((r) => setTimeout(r, 500));
    setPhase("results");
  }

  function toggleSubnet(subnet: string) {
    setSelectedSubnets((prev) =>
      prev.includes(subnet) ? prev.filter((s) => s !== subnet) : [...prev, subnet]
    );
  }

  function handleReset() {
    setPhase("input");
    setVisibleMiners(0);
    setMinerResponses([]);
  }

  const executionResult = mockExecutionResults[selectedTaskId] ?? mockExecutionResults.code_001;

  return (
    <div className="space-y-10 pb-12">
      <div className="mt-4">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink">Submit Task</h1>
          <DataSourceToggle mode="coming-soon" />
        </div>
        <p className="mt-2 text-sm font-medium text-ink-secondary">Describe a task and watch C-SWON orchestrate an optimized workflow.</p>
      </div>

      {/* Phase 1: Input Form */}
      {phase === "input" && (
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="space-y-8 rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-teal">Quick Examples</p>
            <div className="flex flex-wrap gap-3">
              {exampleTasks.map((ex) => (
                <button
                  key={ex.taskId}
                  onClick={() => pickExample(ex.taskId)}
                  className={`rounded-xl border px-4 py-2 text-xs font-medium transition-all hover:-translate-y-0.5 ${
                    selectedTaskId === ex.taskId
                      ? "border-teal/40 bg-teal/10 text-teal shadow-sm"
                      : "border-border bg-surface-1 text-ink-secondary hover:border-teal/30 hover:bg-surface-2"
                  }`}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-ink-tertiary">Task Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-xl border border-border bg-surface-1 px-5 py-4 text-sm text-ink placeholder-ink-muted transition-colors focus:border-teal/50 focus:bg-surface-0 focus:outline-none focus:ring-1 focus:ring-teal/30"
              placeholder="Describe your task..."
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-ink-tertiary">Task Type</label>
            <div className="flex gap-3">
              {(["code", "rag", "agent", "data_transform"] as TaskType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setTaskType(type)}
                  className={`rounded-xl border px-4 py-2 font-mono text-xs font-medium transition-colors ${
                    taskType === type
                      ? "border-teal/40 bg-teal/10 text-teal shadow-sm"
                      : "border-border bg-surface-1 text-ink-secondary hover:border-teal/30 hover:bg-surface-2"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-8 sm:grid-cols-2">
            <div>
              <label className="mb-3 flex justify-between items-center text-xs font-semibold uppercase tracking-widest text-ink-tertiary">
                <span>Max Budget</span>
                <span className="font-mono font-bold text-gold bg-gold/10 px-2 py-1 rounded-md">{formatTao(budget)}</span>
              </label>
              <input
                type="range" min={0.005} max={0.1} step={0.001} value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-teal h-1.5 bg-surface-2 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="mb-3 flex justify-between items-center text-xs font-semibold uppercase tracking-widest text-ink-tertiary">
                <span>Max Latency</span>
                <span className="font-mono font-bold text-ink bg-surface-2 px-2 py-1 rounded-md">{maxLatency}s</span>
              </label>
              <input
                type="range" min={5} max={30} step={1} value={maxLatency}
                onChange={(e) => setMaxLatency(Number(e.target.value))}
                className="w-full accent-teal h-1.5 bg-surface-2 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-ink-tertiary">Allowed Subnets</label>
            <div className="flex flex-wrap gap-2 rounded-xl border border-border bg-surface-1 p-4">
              {allSubnets.map((sn) => (
                <SubnetChip key={sn} subnet={sn} selected={selectedSubnets.includes(sn)} onClick={() => toggleSubnet(sn)} />
              ))}
            </div>
          </div>

          <div className="pt-2">
            <Button
              onClick={handleSubmit}
              disabled={!description}
              className="w-full sm:w-auto px-8"
              size="lg"
            >
              Design Workflow
            </Button>
          </div>
        </motion.div>
      )}

      {/* Phase 2: Miner Competition */}
      {phase === "competing" && (
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="space-y-6">
          <div className="flex items-center gap-4 rounded-xl border border-teal/20 bg-teal/5 p-5 backdrop-blur-sm">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-teal"></span>
            </span>
            <span className="text-sm font-medium text-teal">Querying miners for execution plans...</span>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <AnimatePresence>
              {minerResponses.slice(0, visibleMiners).map((r) => (
                <motion.div
                  key={r.miner_uid}
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
                >
                  <MinerCard response={r} isBest={bestResponse?.miner_uid === r.miner_uid && visibleMiners === minerResponses.length} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}

      {/* Phase 3 & 4: DAG + Execution */}
      {(phase === "dag" || phase === "executing") && bestResponse && (
        <motion.div initial="hidden" animate="visible" variants={fadeInUp} className="space-y-8">
          <div className="rounded-2xl border border-border bg-surface-0/50 p-6 shadow-sm backdrop-blur-md">
            <h2 className="text-xl font-bold text-ink mb-1">Winning Workflow Plan</h2>
            <p className="text-sm font-medium text-ink-secondary">
              UID {bestResponse.miner_uid} — {bestResponse.workflow_plan.nodes.length} steps across{" "}
              <span className="font-mono text-teal">
                {[...new Set(bestResponse.workflow_plan.nodes.map((n) => n.subnet))].join(", ")}
              </span>
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface-0 shadow-sm overflow-hidden">
            <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator.statuses} />
          </div>

          {phase === "dag" && (
            <div className="flex justify-center pt-4">
              <Button onClick={handleExecute} size="lg" className="w-full max-w-sm">
                Execute Workflow
              </Button>
            </div>
          )}

          {phase === "executing" && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col sm:flex-row items-center gap-6 rounded-2xl border border-teal/20 bg-surface-1 px-8 py-6 shadow-sm">
              <div className="flex gap-8 w-full sm:w-auto border-b sm:border-b-0 sm:border-r border-border pb-4 sm:pb-0 sm:pr-8">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-tertiary mb-1">Running Cost</p>
                  <p className="font-mono text-xl font-bold tabular-nums text-gold">{formatTao(animator.currentCost)}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-tertiary mb-1">Running Latency</p>
                  <p className="font-mono text-xl font-bold tabular-nums text-ink">{formatLatency(animator.currentLatency)}</p>
                </div>
              </div>
              <div className="flex-1 w-full">
                <div className="flex justify-between items-end mb-2">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-tertiary">Budget Usage</p>
                  <span className="font-mono text-xs font-medium text-ink-secondary">{Math.min(Math.round((animator.currentCost / budget) * 100), 100)}%</span>
                </div>
                <div className="h-3 rounded-full bg-surface-2 overflow-hidden shadow-inner w-full">
                  <div
                    className="h-full rounded-full bg-gold transition-all duration-300 ease-out"
                    style={{ width: `${Math.min((animator.currentCost / budget) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Phase 5: Results */}
      {phase === "results" && executionResult && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-8"
        >
          {bestResponse && (
            <div className="rounded-2xl border border-border bg-surface-0 shadow-sm overflow-hidden mb-8">
              <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator.statuses} />
            </div>
          )}

          <div className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-teal">
                <div className="bg-success rounded-full w-2 h-2" />
                Final Output
              </h3>
              <pre className="overflow-x-auto rounded-xl border border-border bg-surface-1 p-5 font-mono text-xs leading-relaxed text-ink-secondary shadow-inner max-h-64">
                {executionResult.final_output}
              </pre>
            </div>

            <div className="rounded-2xl border border-border bg-surface-0/50 p-8 shadow-sm backdrop-blur-md">
              <h3 className="mb-4 text-sm font-semibold uppercase tracking-widest text-teal">Score Breakdown</h3>
              <ScoreBreakdown scores={executionResult.scores} />
              
              <div className="mt-8 grid grid-cols-2 gap-6 rounded-xl border border-border bg-surface-1 p-5 shadow-inner">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-muted mb-1">Cost vs Budget</p>
                  <p className="font-mono text-sm font-bold tabular-nums text-gold">
                    {formatTao(executionResult.total_cost)} <span className="text-ink-tertiary text-xs font-normal">/ {formatTao(budget)}</span>
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-muted mb-1">Latency vs Limit</p>
                  <p className="font-mono text-sm font-bold tabular-nums text-ink">
                    {formatLatency(executionResult.total_latency)} <span className="text-ink-tertiary text-xs font-normal">/ {formatLatency(maxLatency)}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center pt-4">
            <Button
              variant="outline"
              size="lg"
              onClick={handleReset}
              className="w-full max-w-sm border-border-emphasis text-ink-secondary hover:text-ink hover:bg-surface-1"
            >
              Submit Another Task
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

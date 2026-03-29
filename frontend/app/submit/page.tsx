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
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[--color-ink]">Submit a Task</h1>
        <p className="mt-1 text-sm text-[--color-ink-secondary]">Describe a task and watch C-SWON orchestrate an optimized workflow.</p>
      </div>

      {/* Phase 1: Input Form */}
      {phase === "input" && (
        <div className="space-y-6">
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Quick Examples</p>
            <div className="flex flex-wrap gap-2">
              {exampleTasks.map((ex) => (
                <button
                  key={ex.taskId}
                  onClick={() => pickExample(ex.taskId)}
                  className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                    selectedTaskId === ex.taskId
                      ? "border-[--color-teal]/40 bg-[--color-teal]/10 text-[--color-teal]"
                      : "border-[--color-border] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
                  }`}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Task Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-[--color-border] bg-[--color-surface-1] px-4 py-3 text-sm text-[--color-ink] placeholder-[--color-ink-muted] focus:border-[--color-teal]/50 focus:outline-none focus:ring-1 focus:ring-[--color-teal]/30"
              placeholder="Describe your task..."
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Task Type</label>
            <div className="flex gap-2">
              {(["code", "rag", "agent", "data_transform"] as TaskType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setTaskType(type)}
                  className={`rounded-lg border px-3 py-1.5 font-mono text-xs transition-colors ${
                    taskType === type
                      ? "border-[--color-teal]/40 bg-[--color-teal]/10 text-[--color-teal]"
                      : "border-[--color-border] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">
                Max Budget: <span className="font-mono text-[--color-gold]">{formatTao(budget)}</span>
              </label>
              <input
                type="range" min={0.005} max={0.1} step={0.001} value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full accent-[--color-teal]"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">
                Max Latency: <span className="font-mono text-[--color-ink]">{maxLatency}s</span>
              </label>
              <input
                type="range" min={5} max={30} step={1} value={maxLatency}
                onChange={(e) => setMaxLatency(Number(e.target.value))}
                className="w-full accent-[--color-teal]"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[--color-ink-secondary]">Allowed Subnets</label>
            <div className="flex flex-wrap gap-2">
              {allSubnets.map((sn) => (
                <SubnetChip key={sn} subnet={sn} selected={selectedSubnets.includes(sn)} onClick={() => toggleSubnet(sn)} />
              ))}
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={!description}
            className="rounded-lg bg-[--color-teal] px-6 py-2.5 text-sm font-medium text-[--color-canvas] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Design Workflow
          </button>
        </div>
      )}

      {/* Phase 2: Miner Competition */}
      {phase === "competing" && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-[--color-teal] animate-pulse" />
            <span className="text-sm text-[--color-ink-secondary]">Querying miners...</span>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {minerResponses.slice(0, visibleMiners).map((r) => (
                <motion.div
                  key={r.miner_uid}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <MinerCard response={r} isBest={bestResponse?.miner_uid === r.miner_uid && visibleMiners === minerResponses.length} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Phase 3 & 4: DAG + Execution */}
      {(phase === "dag" || phase === "executing") && bestResponse && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-[--color-ink]">Winning Workflow Plan</h2>
            <p className="text-sm text-[--color-ink-secondary]">
              UID {bestResponse.miner_uid} — {bestResponse.workflow_plan.nodes.length} steps across{" "}
              {[...new Set(bestResponse.workflow_plan.nodes.map((n) => n.subnet))].join(", ")}
            </p>
          </div>

          <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator.statuses} />

          {phase === "dag" && (
            <button
              onClick={handleExecute}
              className="rounded-lg bg-[--color-teal] px-6 py-2.5 text-sm font-medium text-[--color-canvas] transition-opacity hover:opacity-90"
            >
              Execute Workflow
            </button>
          )}

          {phase === "executing" && (
            <div className="flex items-center gap-6 rounded-lg border border-[--color-border] bg-[--color-surface-1] px-6 py-4">
              <div>
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Running Cost</p>
                <p className="font-mono text-lg font-bold tabular-nums text-[--color-gold]">{formatTao(animator.currentCost)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Running Latency</p>
                <p className="font-mono text-lg font-bold tabular-nums text-[--color-ink]">{formatLatency(animator.currentLatency)}</p>
              </div>
              <div className="flex-1">
                <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Budget Used</p>
                <div className="mt-1 h-2 rounded-full bg-[--color-surface-3]">
                  <div
                    className="h-full rounded-full bg-[--color-gold] transition-all duration-300"
                    style={{ width: `${Math.min((animator.currentCost / budget) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Phase 5: Results */}
      {phase === "results" && executionResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {bestResponse && <DagViewer plan={bestResponse.workflow_plan} stepStatuses={animator.statuses} />}

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Final Output</h3>
              <pre className="overflow-x-auto rounded-lg bg-[--color-surface-0] p-4 font-mono text-xs leading-relaxed text-[--color-ink-secondary]">
                {executionResult.final_output}
              </pre>
            </div>

            <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Score Breakdown</h3>
              <ScoreBreakdown scores={executionResult.scores} />
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Cost vs Budget</p>
                  <p className="font-mono text-sm tabular-nums text-[--color-gold]">
                    {formatTao(executionResult.total_cost)} / {formatTao(budget)}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-[--color-ink-tertiary]">Latency vs Limit</p>
                  <p className="font-mono text-sm tabular-nums text-[--color-ink]">
                    {formatLatency(executionResult.total_latency)} / {formatLatency(maxLatency)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="rounded-lg border border-[--color-border-emphasis] px-6 py-2.5 text-sm font-medium text-[--color-ink-secondary] transition-colors hover:text-[--color-ink]"
          >
            Submit Another Task
          </button>
        </motion.div>
      )}
    </div>
  );
}

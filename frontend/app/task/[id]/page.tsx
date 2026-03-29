"use client";
import { use } from "react";
import { notFound } from "next/navigation";
import { mockTasks, mockTaskPerformance, mockWorkflowResponses } from "@/lib/mock-data";
import { LifecycleBadge } from "@/components/lifecycle-badge";
import { TaskTypeIcon } from "@/components/task-type-icon";
import { DagViewer } from "@/components/dag-viewer";
import { formatTao, formatLatency } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine, Tooltip } from "recharts";

export default function TaskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const task = mockTasks.find((t) => t.task_id === id);
  if (!task) return notFound();

  const perfHistory = mockTaskPerformance[id] ?? [];
  const chartData = perfHistory.map((score, i) => ({ tempo: i + 1, score }));
  const responses = mockWorkflowResponses[id];
  const bestResponse = responses?.[0];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start gap-3">
        <TaskTypeIcon type={task.task_type} size="md" />
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-lg font-bold text-[--color-ink]">{task.task_id}</h1>
            <LifecycleBadge status={task.status} />
          </div>
          <p className="mt-1 text-sm text-[--color-ink-secondary]">{task.description}</p>
        </div>
      </div>

      {/* Config + Routing */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Configuration</h2>
          {Object.keys(task.quality_criteria).length > 0 && (
            <div className="mb-4">
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Quality Criteria</p>
              <div className="mt-1 space-y-1">
                {Object.entries(task.quality_criteria).map(([k, v]) => (
                  <p key={k} className="font-mono text-xs text-[--color-ink-secondary]">{k}: {v}</p>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Budget</p>
              <p className="font-mono text-sm text-[--color-gold]">{formatTao(task.constraints.max_budget_tao)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Latency</p>
              <p className="font-mono text-sm text-[--color-ink]">{formatLatency(task.constraints.max_latency_seconds)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Subnets</p>
              <p className="font-mono text-sm text-[--color-teal]">{task.constraints.allowed_subnets.join(", ")}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="mb-2 text-[10px] uppercase text-[--color-ink-muted]">Available Tools</p>
            <div className="space-y-1">
              {Object.entries(task.available_tools).map(([subnet, tool]) => (
                <div key={subnet} className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-[--color-teal]">{subnet}</span>
                  <span className="text-[--color-ink-tertiary]">{tool.type}</span>
                  <span className="text-[--color-gold]">{formatTao(tool.avg_cost)}</span>
                  <span className="text-[--color-ink-muted]">{formatLatency(tool.avg_latency)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Routing Policy</h2>
          <div className="space-y-3 font-mono text-sm">
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Miner Selection</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.miner_selection}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Top K</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.top_k}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[--color-ink-muted]">Aggregation</p>
              <p className="text-[--color-ink-secondary]">{task.routing_policy.default.aggregation}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance History */}
      {perfHistory.length > 0 && (
        <section className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Performance History</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="tempo" stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <YAxis domain={[0, 1]} stroke="var(--color-ink-tertiary)" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "var(--color-surface-2)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12, fontFamily: "var(--font-mono)" }}
                  labelStyle={{ color: "var(--color-ink-tertiary)" }}
                />
                <ReferenceLine y={0.90} stroke="#f0b429" strokeDasharray="4 4" label={{ value: "deprecation", position: "right", fill: "#f0b429", fontSize: 10 }} />
                <ReferenceLine y={0.10} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "quarantine", position: "right", fill: "#ef4444", fontSize: 10 }} />
                <Line type="monotone" dataKey="score" stroke="#00d4aa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Reference Data */}
      <details className="rounded-lg border border-[--color-border] bg-[--color-surface-1]">
        <summary className="cursor-pointer px-6 py-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]">
          Reference Data
        </summary>
        <div className="border-t border-[--color-border] px-6 py-4">
          <pre className="overflow-x-auto rounded-lg bg-[--color-surface-0] p-4 font-mono text-xs leading-relaxed text-[--color-ink-secondary]">
            {JSON.stringify(task.reference, null, 2)}
          </pre>
        </div>
      </details>

      {/* Example Workflow */}
      {bestResponse && (
        <section>
          <h2 className="mb-4 text-xs font-medium uppercase tracking-widest text-[--color-ink-tertiary]">Example Workflow</h2>
          <DagViewer plan={bestResponse.workflow_plan} />
        </section>
      )}
    </div>
  );
}

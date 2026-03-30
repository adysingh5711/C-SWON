"use client";
import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  type Node,
  type Edge,
  Position,
  Handle,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { WorkflowPlan, StepStatus } from "@/lib/types";
import { formatTao, formatLatency, cn } from "@/lib/utils";

const subnetColors: Record<string, string> = {
  sn1: "#00d4aa",
  sn4: "#a78bfa",
  sn8: "#f0b429",
};

const statusStyles: Record<StepStatus, string> = {
  pending: "border-border-emphasis",
  running: "border-teal ring-1 ring-teal/30",
  completed: "border-emerald-500/50",
  failed: "border-red-500/50",
};

interface DagNodeData {
  label: string;
  subnet: string;
  action: string;
  cost: number;
  latency: number;
  status: StepStatus;
  retries?: number;
  timeout?: number;
  [key: string]: unknown;
}

function DagNode({ data }: NodeProps<Node<DagNodeData>>) {
  const color = subnetColors[data.subnet] ?? "#8a94a8";

  return (
    <div className={cn(
      "rounded-lg border bg-surface-1 p-3 min-w-[160px] transition-all duration-300",
      statusStyles[data.status ?? "pending"]
    )}>
      <Handle type="target" position={Position.Top} className="!bg-ink-muted !border-none !w-2 !h-2" />
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] text-ink-tertiary">{data.label}</span>
        <span className="rounded px-1.5 py-0.5 font-mono text-[10px] font-medium" style={{ backgroundColor: `${color}20`, color }}>
          {data.subnet}
        </span>
      </div>
      <p className="mt-1 text-xs font-medium text-ink">{data.action}</p>
      <div className="mt-2 flex items-center gap-3 text-[10px] text-ink-tertiary">
        <span className="font-mono tabular-nums">{formatTao(data.cost)}</span>
        <span className="font-mono tabular-nums">{formatLatency(data.latency)}</span>
      </div>
      {data.retries && (
        <div className="mt-1 flex items-center gap-1 text-[10px] text-ink-muted">
          <span>retry:{data.retries}</span>
          {data.timeout && <span>timeout:{data.timeout}s</span>}
        </div>
      )}
      {data.status === "running" && (
        <div className="mt-2 h-0.5 rounded-full bg-surface-3 overflow-hidden">
          <div className="h-full w-1/2 rounded-full bg-teal animate-pulse" />
        </div>
      )}
      {data.status === "completed" && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-400">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
          done
        </div>
      )}
      {data.status === "failed" && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-red-400">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          failed
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-ink-muted !border-none !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = { dag: DagNode };

interface DagViewerProps {
  plan: WorkflowPlan;
  stepStatuses?: Record<string, StepStatus>;
  className?: string;
}

export function DagViewer({ plan, stepStatuses = {}, className }: DagViewerProps) {
  const { nodes, edges } = useMemo(() => {
    const tiers: Record<number, typeof plan.nodes> = {};
    for (const node of plan.nodes) {
      (tiers[node.tier] ??= []).push(node);
    }

    const layoutNodes: Node[] = [];
    const xSpacing = 220;
    const ySpacing = 140;

    for (const [tierStr, tierNodes] of Object.entries(tiers)) {
      const tier = Number(tierStr);
      const totalWidth = (tierNodes.length - 1) * xSpacing;
      const startX = -totalWidth / 2;

      tierNodes.forEach((node, idx) => {
        layoutNodes.push({
          id: node.id,
          type: "dag",
          position: { x: startX + idx * xSpacing, y: tier * ySpacing },
          data: {
            label: node.id,
            subnet: node.subnet,
            action: node.action,
            cost: node.estimated_cost,
            latency: node.estimated_latency,
            status: stepStatuses[node.id] ?? "pending",
            retries: node.error_handling?.retry_count,
            timeout: node.error_handling?.timeout,
          },
        });
      });
    }

    const layoutEdges: Edge[] = plan.edges.map((edge, i) => ({
      id: `e-${i}`,
      source: edge.from,
      target: edge.to,
      label: edge.data_ref,
      animated: stepStatuses[edge.from] === "running" || stepStatuses[edge.from] === "completed",
      style: { stroke: "var(--ink-muted)", strokeWidth: 1.5 },
      labelStyle: { fill: "var(--ink-tertiary)", fontSize: 9, fontFamily: "var(--font-mono)" },
      labelBgStyle: { fill: "var(--surface-0)", fillOpacity: 0.8 },
    }));

    return { nodes: layoutNodes, edges: layoutEdges };
  }, [plan, stepStatuses]);

  return (
    <div className={cn("h-[400px] rounded-lg border border-border bg-surface-0", className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="var(--ink-muted)" gap={24} size={1} style={{ opacity: 0.3 }} />
      </ReactFlow>
    </div>
  );
}

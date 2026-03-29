"use client";
import { useState, useCallback } from "react";
import type { WorkflowPlan, StepStatus } from "@/lib/types";

interface StepAnimatorState {
  statuses: Record<string, StepStatus>;
  isRunning: boolean;
  isComplete: boolean;
  currentCost: number;
  currentLatency: number;
}

export function useStepAnimator(plan: WorkflowPlan) {
  const [state, setState] = useState<StepAnimatorState>({
    statuses: {},
    isRunning: false,
    isComplete: false,
    currentCost: 0,
    currentLatency: 0,
  });

  const execute = useCallback(async () => {
    setState({ statuses: {}, isRunning: true, isComplete: false, currentCost: 0, currentLatency: 0 });

    const tiers: Record<number, typeof plan.nodes> = {};
    for (const node of plan.nodes) {
      (tiers[node.tier] ??= []).push(node);
    }

    const sortedTiers = Object.keys(tiers).map(Number).sort((a, b) => a - b);
    let totalCost = 0;
    let totalLatency = 0;

    for (const tier of sortedTiers) {
      const tierNodes = tiers[tier];

      setState((s) => {
        const newStatuses = { ...s.statuses };
        for (const node of tierNodes) newStatuses[node.id] = "running";
        return { ...s, statuses: newStatuses };
      });

      const maxLatency = Math.max(...tierNodes.map((n) => n.estimated_latency));
      await new Promise((r) => setTimeout(r, maxLatency * 1000 + 500));

      const tierCost = tierNodes.reduce((sum, n) => sum + n.estimated_cost, 0);
      totalCost += tierCost;
      totalLatency += maxLatency;

      setState((s) => {
        const newStatuses = { ...s.statuses };
        for (const node of tierNodes) newStatuses[node.id] = "completed";
        return { ...s, statuses: newStatuses, currentCost: totalCost, currentLatency: totalLatency };
      });

      await new Promise((r) => setTimeout(r, 300));
    }

    setState((s) => ({ ...s, isRunning: false, isComplete: true }));
  }, [plan]);

  return { ...state, execute };
}

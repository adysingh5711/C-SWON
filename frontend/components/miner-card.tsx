import type { MinerResponse } from "@/lib/types";
import { truncateKey, formatTao, formatLatency, formatScore, cn } from "@/lib/utils";

export function MinerCard({ response, isBest = false }: { response: MinerResponse; isBest?: boolean }) {
  return (
    <div className={cn(
      "rounded-lg border p-4 transition-all",
      isBest
        ? "border-teal/40 bg-teal/5"
        : "border-border bg-surface-1"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-ink">UID {response.miner_uid}</span>
          <span className="font-mono text-[10px] text-ink-tertiary">{truncateKey(response.hotkey)}</span>
        </div>
        {isBest && (
          <span className="rounded-full bg-teal/15 px-2 py-0.5 text-[10px] font-medium text-teal">
            Best Plan
          </span>
        )}
      </div>
      <div className="mt-3 grid grid-cols-4 gap-3">
        <div>
          <p className="text-[10px] text-ink-tertiary">Confidence</p>
          <p className="font-mono text-sm font-bold tabular-nums text-ink">{formatScore(response.confidence)}</p>
        </div>
        <div>
          <p className="text-[10px] text-ink-tertiary">Est. Cost</p>
          <p className="font-mono text-sm tabular-nums text-gold">{formatTao(response.total_estimated_cost)}</p>
        </div>
        <div>
          <p className="text-[10px] text-ink-tertiary">Est. Latency</p>
          <p className="font-mono text-sm tabular-nums text-ink-secondary">{formatLatency(response.total_estimated_latency)}</p>
        </div>
        <div>
          <p className="text-[10px] text-ink-tertiary">DAG Nodes</p>
          <p className="font-mono text-sm tabular-nums text-ink-secondary">{response.workflow_plan.nodes.length}</p>
        </div>
      </div>
      <p className="mt-3 text-xs leading-relaxed text-ink-secondary">{response.reasoning}</p>
    </div>
  );
}

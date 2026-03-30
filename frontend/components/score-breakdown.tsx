import { scoring } from "@/lib/constants";
import type { ScoreBreakdownData } from "@/lib/types";
import { formatScore } from "@/lib/utils";

const dimensions: { key: keyof Omit<ScoreBreakdownData, "composite">; label: string; color: string }[] = [
  { key: "success", label: "Success", color: "bg-emerald-400" },
  { key: "cost", label: "Cost", color: "bg-gold" },
  { key: "latency", label: "Latency", color: "bg-teal" },
  { key: "reliability", label: "Reliability", color: "bg-purple-400" },
];

export function ScoreBreakdown({ scores, showComposite = true }: { scores: ScoreBreakdownData; showComposite?: boolean }) {
  return (
    <div className="space-y-3">
      {showComposite && (
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-3xl font-bold text-ink">{formatScore(scores.composite)}</span>
          <span className="text-xs text-ink-tertiary">composite</span>
        </div>
      )}
      <div className="space-y-2">
        {dimensions.map(({ key, label, color }) => {
          const value = scores[key];
          const weight = scoring.weights[key];
          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-ink-secondary">{label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-ink-tertiary">{(weight * 100).toFixed(0)}%</span>
                  <span className="font-mono text-ink tabular-nums">{formatScore(value)}</span>
                </div>
              </div>
              <div className="h-1.5 rounded-full bg-surface-3">
                <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${value * 100}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

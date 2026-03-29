import { scoring } from "@/lib/constants";
import { formatPercent } from "@/lib/utils";

export function WeightBar({ weight, capped }: { weight: number; capped: boolean }) {
  const capPercent = scoring.maxMinerWeight * 100;
  return (
    <div className="space-y-1">
      <div className="relative h-2 rounded-full bg-[--color-surface-3]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${capped ? "bg-[--color-gold]" : "bg-[--color-teal]"}`}
          style={{ width: `${Math.min(weight * 100 / 0.20, 100)}%` }}
        />
        <div
          className="absolute top-[-2px] h-[calc(100%+4px)] w-px bg-[--color-ink-tertiary]"
          style={{ left: `${capPercent / 0.20 * 100}%` }}
          title="15% cap"
        />
      </div>
      <div className="flex items-center justify-between text-[10px]">
        <span className="font-mono tabular-nums text-[--color-ink-secondary]">{formatPercent(weight)}</span>
        {capped && <span className="text-[--color-gold]">capped</span>}
      </div>
    </div>
  );
}

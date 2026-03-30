"use client";
import { formatScore } from "@/lib/utils";

const colorMap: Record<string, string> = {
  success: "#22c55e",
  cost: "#f0b429",
  latency: "#00d4aa",
  reliability: "#a78bfa",
};

export function ScoreGauge({ value, dimension, size = 80 }: { value: number; dimension: string; size?: number }) {
  const color = colorMap[dimension] ?? "#00d4aa";
  const radius = (size - 8) / 2;
  const circumference = Math.PI * radius;
  const offset = circumference * (1 - value);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
        <path
          d={`M 4 ${center} A ${radius} ${radius} 0 0 1 ${size - 4} ${center}`}
          fill="none" stroke="var(--surface-3)" strokeWidth={4} strokeLinecap="round"
        />
        <path
          d={`M 4 ${center} A ${radius} ${radius} 0 0 1 ${size - 4} ${center}`}
          fill="none" stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <span className="font-mono text-sm font-bold tabular-nums text-ink">{formatScore(value)}</span>
      <span className="text-[10px] uppercase tracking-wider text-ink-tertiary">{dimension}</span>
    </div>
  );
}

"use client";
import { motion } from "framer-motion";

const flows = [
  { label: "Owner", percent: 18, color: "#a78bfa", y: 0 },
  { label: "Miners", percent: 41, color: "#00d4aa", y: 1 },
  { label: "Validators + Stakers", percent: 41, color: "#f0b429", y: 2 },
];

export function EmissionSankey() {
  const height = 200;
  const width = 500;
  const barWidth = 24;
  const sourceX = 60;
  const targetX = width - 120;
  const sourceHeight = height - 40;
  const sourceY = 20;

  return (
    <div className="rounded-lg border border-[--color-border] bg-[--color-surface-0] p-6">
      <h3 className="mb-4 text-xs font-medium uppercase tracking-wider text-[--color-ink-tertiary]">Emission Flow</h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxWidth: 500 }}>
        {/* Source bar */}
        <rect x={sourceX} y={sourceY} width={barWidth} height={sourceHeight} rx={4} fill="var(--color-surface-2)" />
        <text x={sourceX + barWidth / 2} y={sourceY - 6} textAnchor="middle" className="fill-[--color-ink-secondary]" style={{ font: "10px var(--font-mono)" }}>
          {"\u0394\u03B1"}
        </text>

        {/* Flow paths */}
        {flows.map((flow, i) => {
          const flowHeight = (sourceHeight * flow.percent) / 100;
          const flowSourceY = sourceY + flows.slice(0, i).reduce((sum, f) => sum + (sourceHeight * f.percent) / 100, 0);
          const targetY = 20 + i * 60;
          const targetHeight = 36;

          const path = `M ${sourceX + barWidth} ${flowSourceY + flowHeight / 2}
            C ${sourceX + barWidth + 80} ${flowSourceY + flowHeight / 2},
              ${targetX - 80} ${targetY + targetHeight / 2},
              ${targetX} ${targetY + targetHeight / 2}`;

          return (
            <g key={flow.label}>
              <motion.path
                d={path}
                fill="none"
                stroke={flow.color}
                strokeWidth={flowHeight * 0.6}
                strokeOpacity={0.15}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.2 }}
              />
              <motion.path
                d={path}
                fill="none"
                stroke={flow.color}
                strokeWidth={2}
                strokeOpacity={0.5}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.2 }}
              />
              <rect x={targetX} y={targetY} width={barWidth} height={targetHeight} rx={4} fill={flow.color} fillOpacity={0.2} />
              <text x={targetX + barWidth + 8} y={targetY + 14} className="fill-[--color-ink]" style={{ font: "12px var(--font-sans)" }}>
                {flow.label}
              </text>
              <text x={targetX + barWidth + 8} y={targetY + 28} className="fill-[--color-ink-tertiary]" style={{ font: "11px var(--font-mono)" }}>
                {flow.percent}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

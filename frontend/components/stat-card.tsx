import { cn } from "@/lib/utils";

export function StatCard({
  label, value, sublabel, accent = false,
}: {
  label: string; value: string | number; sublabel?: string; accent?: boolean;
}) {
  return (
    <div className="rounded-lg border border-[--color-border] bg-[--color-surface-1] p-4">
      <p className="text-[11px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]">{label}</p>
      <p className={cn(
        "mt-1 font-mono text-2xl font-bold tabular-nums",
        accent ? "text-[--color-teal]" : "text-[--color-ink]"
      )}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {sublabel && <p className="mt-1 text-xs text-[--color-ink-tertiary]">{sublabel}</p>}
    </div>
  );
}

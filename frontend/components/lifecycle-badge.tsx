import type { LifecycleStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<LifecycleStatus, string> = {
  active: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  quarantined: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  deprecated: "bg-ink-muted/15 text-ink-tertiary border-ink-muted/20",
};

export function LifecycleBadge({ status }: { status: LifecycleStatus }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider", styles[status])}>
      {status}
    </span>
  );
}

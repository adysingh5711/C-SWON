import { cn } from "@/lib/utils";

export function SubnetChip({ subnet, selected, onClick }: { subnet: string; selected?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 font-mono text-xs transition-colors",
        selected
          ? "border-teal/40 bg-teal/15 text-teal"
          : "border-border bg-surface-1 text-ink-secondary hover:border-border-emphasis"
      )}
    >
      {subnet}
    </button>
  );
}

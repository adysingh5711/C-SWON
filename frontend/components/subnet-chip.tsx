import { cn } from "@/lib/utils";

export function SubnetChip({ subnet, selected, onClick }: { subnet: string; selected?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 font-mono text-xs transition-colors",
        selected
          ? "border-[--color-teal]/40 bg-[--color-teal]/15 text-[--color-teal]"
          : "border-[--color-border] bg-[--color-surface-1] text-[--color-ink-secondary] hover:border-[--color-border-emphasis]"
      )}
    >
      {subnet}
    </button>
  );
}

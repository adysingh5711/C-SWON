"use client";
import { useDataSource, type DataSource } from "@/lib/data-source-context";

interface DataSourceToggleProps {
  mode: "enabled" | "coming-soon";
}

export function DataSourceToggle({ mode }: DataSourceToggleProps) {
  const { source, setSource } = useDataSource();

  function handleSelect(target: DataSource) {
    if (mode === "coming-soon" && target === "testnet") return;
    setSource(target);
  }

  return (
    <div className="inline-flex items-center rounded-full border border-[--color-border] bg-[--color-surface-1] p-0.5 text-xs">
      <button
        onClick={() => handleSelect("mock")}
        className={`rounded-full px-3 py-1 transition-colors ${
          source === "mock"
            ? "bg-[--color-surface-3] text-[--color-ink]"
            : "text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]"
        }`}
      >
        Mock
      </button>
      <button
        onClick={() => handleSelect("testnet")}
        className={`group relative rounded-full px-3 py-1 transition-colors ${
          mode === "coming-soon"
            ? "cursor-not-allowed text-[--color-ink-muted]"
            : source === "testnet"
              ? "bg-[--color-teal]/15 text-[--color-teal]"
              : "text-[--color-ink-tertiary] hover:text-[--color-ink-secondary]"
        }`}
        disabled={mode === "coming-soon"}
        title={mode === "coming-soon" ? "Live testnet data coming soon" : undefined}
      >
        Testnet
        {mode === "coming-soon" && (
          <span className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-[--color-surface-3] px-2 py-0.5 text-[10px] text-[--color-ink-tertiary] opacity-0 transition-opacity group-hover:opacity-100">
            Coming Soon
          </span>
        )}
      </button>
    </div>
  );
}

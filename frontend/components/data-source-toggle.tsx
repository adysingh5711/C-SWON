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
    <div className="inline-flex items-center rounded-full border border-border bg-surface-1 p-0.5 text-xs">
      <button
        onClick={() => handleSelect("mock")}
        className={`rounded-full px-3 py-1 transition-colors ${
          source === "mock"
            ? "bg-surface-3 text-ink"
            : "text-ink-tertiary hover:text-ink-secondary"
        }`}
      >
        Mock
      </button>
      <button
        onClick={() => handleSelect("testnet")}
        className={`group relative rounded-full px-3 py-1 transition-colors ${
          mode === "coming-soon"
            ? "cursor-not-allowed text-ink-muted"
            : source === "testnet"
              ? "bg-teal/15 text-teal"
              : "text-ink-tertiary hover:text-ink-secondary"
        }`}
        disabled={mode === "coming-soon"}
        title={mode === "coming-soon" ? "Live testnet data coming soon" : undefined}
      >
        Testnet
        {mode === "coming-soon" && (
          <span className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-surface-3 px-2 py-0.5 text-[10px] text-ink-tertiary opacity-0 transition-opacity group-hover:opacity-100">
            Coming Soon
          </span>
        )}
      </button>
    </div>
  );
}

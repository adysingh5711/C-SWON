"use client";
import { useState, useEffect } from "react";
import { mockNetworkStats } from "@/lib/mock-data";

export function BlockCounter() {
  const [block, setBlock] = useState(mockNetworkStats.current_block);

  useEffect(() => {
    const interval = setInterval(() => setBlock((b) => b + 1), 12_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <span className="h-1.5 w-1.5 rounded-full bg-teal animate-pulse" />
      <span className="text-ink-tertiary">Block</span>
      <span className="text-ink-secondary tabular-nums">{block.toLocaleString()}</span>
    </div>
  );
}

import type { TaskType } from "@/lib/types";
import { cn } from "@/lib/utils";

const config: Record<TaskType, { label: string; className: string }> = {
  code: { label: "</>", className: "bg-teal/15 text-teal" },
  rag: { label: "RAG", className: "bg-purple-500/15 text-purple-400" },
  agent: { label: "AGT", className: "bg-gold/15 text-gold" },
  data_transform: { label: "DTX", className: "bg-blue-500/15 text-blue-400" },
};

export function TaskTypeIcon({ type, size = "sm" }: { type: TaskType; size?: "sm" | "md" }) {
  const { label, className } = config[type];
  return (
    <span className={cn(
      "inline-flex items-center justify-center rounded font-mono font-bold",
      size === "sm" ? "h-6 px-1.5 text-[10px]" : "h-8 px-2 text-xs",
      className
    )}>
      {label}
    </span>
  );
}

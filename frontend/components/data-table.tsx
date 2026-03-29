"use client";
import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";

interface Column<T> {
  key: string;
  label: string;
  render: (row: T) => React.ReactNode;
  sortValue?: (row: T) => number | string;
  align?: "left" | "right" | "center";
  mono?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  keyField: keyof T;
}

export function DataTable<T>({ columns, data, onRowClick, keyField }: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return data;
    return [...data].sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      const cmp = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir, columns]);

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-[--color-border]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[--color-border] bg-[--color-surface-1]">
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => col.sortValue && handleSort(col.key)}
                className={cn(
                  "px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-[--color-ink-tertiary]",
                  col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                  col.sortValue && "cursor-pointer hover:text-[--color-ink-secondary]"
                )}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {sortKey === col.key && (
                    <span className="text-[--color-teal]">{sortDir === "asc" ? "\u2191" : "\u2193"}</span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={String(row[keyField])}
              onClick={() => onRowClick?.(row)}
              className={cn(
                "border-b border-[--color-border] bg-[--color-surface-0] transition-colors",
                onRowClick && "cursor-pointer hover:bg-[--color-surface-1]"
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-4 py-3",
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                    col.mono && "font-mono tabular-nums"
                  )}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

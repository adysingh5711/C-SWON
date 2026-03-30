"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BlockCounter } from "./block-counter";
import { ThemeToggle } from "./theme-toggle";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Network" },
  { href: "/submit", label: "Submit Task" },
  { href: "/explorer", label: "Explorer" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--canvas)]/70 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-mono text-sm font-bold tracking-tight text-[var(--teal)] transition-colors hover:text-[var(--teal-dim)]">
            C-SWON
          </Link>
          <div className="flex items-center gap-1">
            {links.map(({ href, label }) => {
              const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
                    active
                      ? "bg-[initial] text-[var(--teal)] drop-shadow-sm"
                      : "text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)]"
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <BlockCounter />
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}

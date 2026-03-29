"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BlockCounter } from "./block-counter";

const links = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Network" },
  { href: "/submit", label: "Submit Task" },
  { href: "/explorer", label: "Explorer" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-[--color-border] bg-[--color-canvas]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-mono text-sm font-bold tracking-tight text-[--color-teal]">
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
                    "rounded-md px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-[--color-teal]/10 text-[--color-teal]"
                      : "text-[--color-ink-secondary] hover:text-[--color-ink]"
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
        <BlockCounter />
      </div>
    </nav>
  );
}

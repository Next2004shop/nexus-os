"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  BotMessageSquare,
  Crosshair,
  ShieldAlert,
  ScrollText,
  Settings,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/markets", label: "Markets", icon: BarChart3 },
  { href: "/ai-console", label: "AI Console", icon: BotMessageSquare },
  { href: "/positions", label: "Positions", icon: Crosshair },
  { href: "/risk", label: "Risk Control", icon: ShieldAlert },
  { href: "/logs", label: "System Logs", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[var(--sidebar-width)] bg-[var(--nexus-card-solid)] border-r border-[var(--nexus-border)] flex flex-col z-40">
      {/* Logo */}
      <div className="h-[var(--topbar-height)] flex items-center gap-2 px-5 border-b border-[var(--nexus-border)]">
        <Zap className="w-5 h-5 text-[var(--nexus-green)]" />
        <span className="font-mono font-bold text-sm tracking-wider">
          NEXUS<span className="text-[var(--nexus-green)]">_OS</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-3 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium transition-all",
                isActive
                  ? "bg-[var(--nexus-green-glow)] text-[var(--nexus-green)] border border-[var(--nexus-border-active)]"
                  : "text-[var(--nexus-subtext)] hover:text-[var(--foreground)] hover:bg-white/[0.03]"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[var(--nexus-border)]">
        <p className="text-[10px] text-[var(--nexus-muted)] font-mono">
          SOVEREIGN v3.0
        </p>
        <p className="text-[10px] text-[var(--nexus-muted)] font-mono">
          COUNCIL_PROTOCOL ACTIVE
        </p>
      </div>
    </aside>
  );
}

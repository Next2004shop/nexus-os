"use client";

import { useEffect, useState } from "react";
import { Activity, Wifi, WifiOff, Shield } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface SystemState {
  connected: boolean;
  equity: number;
  riskLevel: string;
  aiStatus: string;
}

export function TopBar() {
  const [state, setState] = useState<SystemState>({
    connected: false,
    equity: 0,
    riskLevel: "UNKNOWN",
    aiStatus: "OFFLINE",
  });

  useEffect(() => {
    let mounted = true;

    const poll = async () => {
      try {
        const [health, status] = await Promise.allSettled([
          api.getHealth(),
          api.getStatus(),
        ]);

        if (!mounted) return;

        const connected = health.status === "fulfilled";
        const statusData =
          status.status === "fulfilled" ? status.value : null;

        setState({
          connected,
          equity:
            (statusData?.risk as Record<string, unknown>)?.current_equity as number ?? 0,
          riskLevel:
            ((statusData?.risk as Record<string, unknown>)?.risk_level as string) ?? "UNKNOWN",
          aiStatus: connected ? "RUNNING" : "OFFLINE",
        });
      } catch {
        if (mounted) setState((s) => ({ ...s, connected: false, aiStatus: "OFFLINE" }));
      }
    };

    poll();
    const interval = setInterval(poll, 15_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const riskColor =
    state.riskLevel === "NORMAL"
      ? "text-[var(--nexus-green)]"
      : state.riskLevel === "WARNING"
        ? "text-[var(--nexus-yellow)]"
        : state.riskLevel === "CRITICAL"
          ? "text-[var(--nexus-red)]"
          : "text-[var(--nexus-subtext)]";

  return (
    <header className="fixed top-0 left-[var(--sidebar-width)] right-0 h-[var(--topbar-height)] bg-[var(--nexus-card-solid)] border-b border-[var(--nexus-border)] flex items-center justify-between px-6 z-30">
      {/* Left: Connection */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-mono">
          {state.connected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-[var(--nexus-green)]" />
              <span className="text-[var(--nexus-green)]">CONNECTED</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-[var(--nexus-red)]" />
              <span className="text-[var(--nexus-red)]">DISCONNECTED</span>
            </>
          )}
        </div>
        <div className="w-px h-5 bg-[var(--nexus-border)]" />
        <div className="flex items-center gap-2 text-xs font-mono">
          <Activity
            className={`w-3.5 h-3.5 ${state.aiStatus === "RUNNING" ? "text-[var(--nexus-green)] animate-pulse" : "text-[var(--nexus-subtext)]"}`}
          />
          <span className="text-[var(--nexus-subtext)]">AI:</span>
          <span
            className={
              state.aiStatus === "RUNNING"
                ? "text-[var(--nexus-green)]"
                : "text-[var(--nexus-subtext)]"
            }
          >
            {state.aiStatus}
          </span>
        </div>
      </div>

      {/* Right: Equity + Risk */}
      <div className="flex items-center gap-5">
        <div className="text-right">
          <p className="text-[10px] text-[var(--nexus-subtext)] font-mono uppercase">
            Account Equity
          </p>
          <p className="text-sm font-mono font-semibold">
            {state.equity > 0 ? formatCurrency(state.equity) : "—"}
          </p>
        </div>
        <div className="w-px h-5 bg-[var(--nexus-border)]" />
        <div className="flex items-center gap-2">
          <Shield className={`w-4 h-4 ${riskColor}`} />
          <div>
            <p className="text-[10px] text-[var(--nexus-subtext)] font-mono uppercase">
              Risk Level
            </p>
            <p className={`text-xs font-mono font-semibold ${riskColor}`}>
              {state.riskLevel}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

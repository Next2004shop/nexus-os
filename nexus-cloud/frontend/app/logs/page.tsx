"use client";

import { useState } from "react";
import { ScrollText, Filter, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/Card";

type LogLevel = "INFO" | "WARNING" | "ERROR" | "CRITICAL" | "DEBUG";

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
}

// Placeholder logs — in production, these come from the backend or Cloud Logging
const PLACEHOLDER_LOGS: LogEntry[] = [
  { timestamp: "2026-02-13T10:45:12Z", level: "INFO", module: "nexus.heartbeat", message: "HEARTBEAT_INITIATED: 2026-02-13T10:45:12Z" },
  { timestamp: "2026-02-13T10:45:12Z", level: "INFO", module: "nexus.heartbeat", message: "STRATEGY_SIGNAL: BTCUSD BUY confidence=0.642" },
  { timestamp: "2026-02-13T10:45:13Z", level: "INFO", module: "nexus.heartbeat", message: "SOVEREIGN_DISPATCH: BTCUSD BUY qty=0.005100" },
  { timestamp: "2026-02-13T10:45:13Z", level: "INFO", module: "nexus.pipeline", message: "PIPELINE_STAGE: STEALTH_CHECK passed" },
  { timestamp: "2026-02-13T10:45:14Z", level: "INFO", module: "nexus.council", message: "COUNCIL_DELIBERATION: BTCUSD BUY — 4/5 agents approved" },
  { timestamp: "2026-02-13T10:45:14Z", level: "INFO", module: "nexus.ensemble", message: "ENSEMBLE_PREDICT: agreement=0.78 — PROCEED" },
  { timestamp: "2026-02-13T10:45:15Z", level: "WARNING", module: "nexus.ancient_logic", message: "CYCLE_RESTRICTION: BUY REJECTED IN ACCUMULATION." },
  { timestamp: "2026-02-13T10:45:15Z", level: "INFO", module: "nexus.heartbeat", message: "HEARTBEAT_RESULT: BTCUSD BUY -> REJECTED_BY_GOVERNOR" },
  { timestamp: "2026-02-13T10:45:15Z", level: "INFO", module: "nexus.heartbeat", message: "HEARTBEAT_COMPLETE" },
  { timestamp: "2026-02-13T10:30:00Z", level: "INFO", module: "nexus.risk", message: "EQUITY_UPDATED: 10000.00 -> 10000.00" },
  { timestamp: "2026-02-13T10:15:00Z", level: "INFO", module: "nexus.heartbeat", message: "HEARTBEAT_INITIATED: 2026-02-13T10:15:00Z" },
  { timestamp: "2026-02-13T10:15:01Z", level: "INFO", module: "nexus.heartbeat", message: "STRATEGY_NO_SIGNAL: BTCUSD (confidence=0.182)" },
  { timestamp: "2026-02-13T10:00:00Z", level: "INFO", module: "nexus.scheduler", message: "HEARTBEAT_SCHEDULER_ACTIVE. INTERVAL: 15M." },
  { timestamp: "2026-02-13T10:00:00Z", level: "INFO", module: "nexus.nervous_system", message: "NEXUS_SOVEREIGN_SYSTEM_ONLINE" },
];

const LEVEL_COLORS: Record<LogLevel, string> = {
  INFO: "text-[var(--nexus-green)]",
  WARNING: "text-[var(--nexus-yellow)]",
  ERROR: "text-[var(--nexus-red)]",
  CRITICAL: "text-[var(--nexus-red)] font-bold",
  DEBUG: "text-[var(--nexus-subtext)]",
};

const LEVEL_FILTERS: LogLevel[] = ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"];

export default function LogsPage() {
  const [logs] = useState<LogEntry[]>(PLACEHOLDER_LOGS);
  const [levelFilter, setLevelFilter] = useState<LogLevel | "ALL">("ALL");

  const filtered = levelFilter === "ALL" ? logs : logs.filter((l) => l.level === levelFilter);

  return (
    <div className="space-y-6 animate-fade-in h-[calc(100vh-var(--topbar-height)-48px)] flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-mono font-bold tracking-wide">System Logs</h1>
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[var(--nexus-subtext)]" />
          <div className="flex items-center gap-1">
            <button
              onClick={() => setLevelFilter("ALL")}
              className={`px-2 py-1 text-[10px] font-mono uppercase rounded transition-colors ${
                levelFilter === "ALL"
                  ? "bg-white/[0.08] text-[var(--foreground)]"
                  : "text-[var(--nexus-subtext)] hover:text-[var(--foreground)]"
              }`}
            >
              ALL
            </button>
            {LEVEL_FILTERS.map((level) => (
              <button
                key={level}
                onClick={() => setLevelFilter(level)}
                className={`px-2 py-1 text-[10px] font-mono rounded transition-colors ${
                  levelFilter === level
                    ? `bg-white/[0.08] ${LEVEL_COLORS[level]}`
                    : "text-[var(--nexus-subtext)] hover:text-[var(--foreground)]"
                }`}
              >
                {level}
              </button>
            ))}
          </div>
          <button className="ml-2 p-1.5 text-[var(--nexus-subtext)] hover:text-[var(--foreground)] transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <Card className="flex-1 min-h-0 flex flex-col">
        <div className="flex-1 overflow-y-auto font-mono text-xs space-y-0.5">
          {filtered.map((log, i) => (
            <div key={i} className="flex gap-3 py-1 px-2 hover:bg-white/[0.02] rounded">
              <span className="text-[var(--nexus-muted)] shrink-0 w-[140px]">
                {new Date(log.timestamp).toLocaleString("en-US", {
                  month: "short",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                  hour12: false,
                })}
              </span>
              <span className={`shrink-0 w-[60px] ${LEVEL_COLORS[log.level]}`}>
                {log.level}
              </span>
              <span className="shrink-0 w-[160px] text-[var(--nexus-blue)]">
                {log.module}
              </span>
              <span className="text-[var(--foreground)]">{log.message}</span>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-8 text-[var(--nexus-subtext)]">
              No logs matching filter
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Power,
  Play,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { SkeletonCard } from "@/components/ui/Skeleton";

interface RiskData {
  current_equity: number;
  peak_equity: number;
  initial_equity: number;
  max_drawdown_limit: number;
  warning_drawdown: number;
  max_position_size_pct: number;
  max_total_exposure_pct: number;
  max_correlation: number;
  trading_enabled: boolean;
  circuit_breaker_active: boolean;
  risk_level: string;
  consecutive_losses: number;
  max_consecutive_losses: number;
  current_drawdown: number;
}

const DEFAULT_RISK: RiskData = {
  current_equity: 10000,
  peak_equity: 10000,
  initial_equity: 10000,
  max_drawdown_limit: 0.02,
  warning_drawdown: 0.01,
  max_position_size_pct: 0.05,
  max_total_exposure_pct: 0.20,
  max_correlation: 0.70,
  trading_enabled: true,
  circuit_breaker_active: false,
  risk_level: "NORMAL",
  consecutive_losses: 0,
  max_consecutive_losses: 5,
  current_drawdown: 0,
};

export default function RiskControlPage() {
  const [risk, setRisk] = useState<RiskData>(DEFAULT_RISK);
  const [loading, setLoading] = useState(true);
  const [killModalOpen, setKillModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchRisk = async () => {
      try {
        const data = await api.getRiskStatus();
        if (mounted) setRisk(data as unknown as RiskData);
      } catch {
        // keep defaults
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchRisk();
    const interval = setInterval(fetchRisk, 5_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleKill = async () => {
    setActionLoading(true);
    try {
      await api.killSwitch();
      setKillModalOpen(false);
    } catch {
      // error handled in UI
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await api.resume();
    } catch {
      // error handled
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-lg font-mono font-bold tracking-wide">Risk Control</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} lines={4} />
          ))}
        </div>
      </div>
    );
  }

  const drawdownPct = risk.current_drawdown * 100;
  const drawdownRatio = risk.max_drawdown_limit > 0 ? risk.current_drawdown / risk.max_drawdown_limit : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-mono font-bold tracking-wide">Risk Control</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleResume}
            disabled={actionLoading || risk.trading_enabled}
            className="flex items-center gap-2 px-4 py-2 text-xs font-mono nexus-card text-[var(--nexus-green)] hover:bg-[var(--nexus-green-glow)] transition-colors disabled:opacity-30"
          >
            <Play className="w-3.5 h-3.5" /> RESUME
          </button>
          <button
            onClick={() => setKillModalOpen(true)}
            disabled={actionLoading}
            className="flex items-center gap-2 px-4 py-2 text-xs font-mono border border-[var(--nexus-red)]/30 rounded-lg bg-[var(--nexus-red-glow)] text-[var(--nexus-red)] hover:border-[var(--nexus-red)]/60 transition-colors"
          >
            <Power className="w-3.5 h-3.5" /> KILL SWITCH
          </button>
        </div>
      </div>

      {/* Risk Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Drawdown Gauge */}
        <Card title="Drawdown Gauge" icon={<ShieldAlert className="w-3.5 h-3.5" />}>
          <div className="space-y-4">
            <div className="relative pt-8 pb-2">
              <svg viewBox="0 0 200 100" className="w-full">
                {/* Background arc */}
                <path
                  d="M 20 90 A 80 80 0 0 1 180 90"
                  fill="none"
                  stroke="var(--nexus-muted)"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
                {/* Value arc */}
                <path
                  d="M 20 90 A 80 80 0 0 1 180 90"
                  fill="none"
                  stroke={drawdownRatio < 0.5 ? "var(--nexus-green)" : drawdownRatio < 0.8 ? "var(--nexus-yellow)" : "var(--nexus-red)"}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${drawdownRatio * 251} 251`}
                />
                <text x="100" y="80" textAnchor="middle" fill="var(--foreground)" fontSize="18" fontFamily="monospace" fontWeight="bold">
                  {drawdownPct.toFixed(2)}%
                </text>
                <text x="100" y="95" textAnchor="middle" fill="var(--nexus-subtext)" fontSize="9" fontFamily="monospace">
                  of {(risk.max_drawdown_limit * 100).toFixed(1)}% limit
                </text>
              </svg>
            </div>
          </div>
        </Card>

        {/* Risk Level */}
        <Card title="Risk Level" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
          <div className="space-y-3">
            <p
              className={`text-3xl font-mono font-bold ${
                risk.risk_level === "NORMAL" ? "text-[var(--nexus-green)]" :
                risk.risk_level === "WARNING" ? "text-[var(--nexus-yellow)]" :
                "text-[var(--nexus-red)]"
              }`}
            >
              {risk.risk_level}
            </p>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[var(--nexus-subtext)]">Trading</span>
                <span className={risk.trading_enabled ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}>
                  {risk.trading_enabled ? "ENABLED" : "HALTED"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--nexus-subtext)]">Circuit Breaker</span>
                <span className={risk.circuit_breaker_active ? "text-[var(--nexus-red)]" : "text-[var(--nexus-green)]"}>
                  {risk.circuit_breaker_active ? "TRIPPED" : "CLOSED"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--nexus-subtext)]">Consecutive Losses</span>
                <span className="font-mono">{risk.consecutive_losses} / {risk.max_consecutive_losses}</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Risk Limits */}
        <Card title="Governor Limits" icon={<AlertTriangle className="w-3.5 h-3.5" />}>
          <div className="space-y-2.5 text-xs">
            {[
              { label: "Max Drawdown", value: formatPercent(risk.max_drawdown_limit * 100, 1) },
              { label: "Warning Threshold", value: formatPercent(risk.warning_drawdown * 100, 1) },
              { label: "Max Position Size", value: formatPercent(risk.max_position_size_pct * 100, 0) },
              { label: "Max Exposure", value: formatPercent(risk.max_total_exposure_pct * 100, 0) },
              { label: "Max Correlation", value: `${(risk.max_correlation * 100).toFixed(0)}%` },
            ].map((item) => (
              <div key={item.label} className="flex justify-between py-1 border-b border-[var(--nexus-border)]">
                <span className="text-[var(--nexus-subtext)]">{item.label}</span>
                <span className="font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Equity Summary */}
      <Card title="Equity Summary" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-[10px] text-[var(--nexus-subtext)] uppercase">Current</p>
            <p className="text-lg font-mono font-bold">{formatCurrency(risk.current_equity)}</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--nexus-subtext)] uppercase">Peak</p>
            <p className="text-lg font-mono font-bold text-[var(--nexus-blue)]">{formatCurrency(risk.peak_equity)}</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--nexus-subtext)] uppercase">Initial</p>
            <p className="text-lg font-mono font-bold text-[var(--nexus-subtext)]">{formatCurrency(risk.initial_equity)}</p>
          </div>
        </div>
      </Card>

      {/* Kill Switch Modal */}
      <Modal
        open={killModalOpen}
        onClose={() => setKillModalOpen(false)}
        title="EMERGENCY KILL SWITCH"
        variant="danger"
      >
        <div className="space-y-4">
          <p className="text-xs text-[var(--nexus-subtext)]">
            This will immediately halt all trading, close open orders, and trigger the circuit breaker.
            Are you sure?
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setKillModalOpen(false)}
              className="px-4 py-2 text-xs font-mono nexus-card hover:bg-white/[0.04] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleKill}
              disabled={actionLoading}
              className="px-4 py-2 text-xs font-mono bg-[var(--nexus-red)] text-white rounded-lg hover:bg-[var(--nexus-red)]/80 transition-colors disabled:opacity-50"
            >
              {actionLoading ? "EXECUTING..." : "CONFIRM KILL"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

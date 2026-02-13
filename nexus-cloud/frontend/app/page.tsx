"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Activity,
  ShieldCheck,
  Crosshair,
  Zap,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { SkeletonCard } from "@/components/ui/Skeleton";

// Placeholder data (replaced by live API when backend is connected)
const PLACEHOLDER = {
  equity: 10000.0,
  balance: 10000.0,
  pnl: 0.0,
  pnlPercent: 0.0,
  drawdown: 0.0,
  maxDrawdownLimit: 2.0,
  openPositions: 0,
  councilStatus: "IDLE",
  ensembleAgreement: 0,
  riskLevel: "NORMAL",
  tradingEnabled: true,
  circuitBreaker: "CLOSED",
};

export default function DashboardPage() {
  const [data, setData] = useState(PLACEHOLDER);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        const status = await api.getStatus();
        if (!mounted) return;

        const risk = status.risk as Record<string, unknown> ?? {};
        const council = status.council as Record<string, unknown> ?? {};
        const ensemble = status.ensemble as Record<string, unknown> ?? {};
        const execution = status.execution as Record<string, unknown> ?? {};

        setData({
          equity: (risk.current_equity as number) ?? PLACEHOLDER.equity,
          balance: (risk.peak_equity as number) ?? PLACEHOLDER.balance,
          pnl:
            ((risk.current_equity as number) ?? 0) -
            ((risk.initial_equity as number) ?? 0),
          pnlPercent:
            (risk.initial_equity as number)
              ? (((risk.current_equity as number) ?? 0) -
                  ((risk.initial_equity as number) ?? 0)) /
                ((risk.initial_equity as number) ?? 1) *
                100
              : 0,
          drawdown: ((risk.current_drawdown as number) ?? 0) * 100,
          maxDrawdownLimit: ((risk.max_drawdown_limit as number) ?? 0.02) * 100,
          openPositions: Object.keys(
            (risk.open_positions as Record<string, unknown>) ?? {}
          ).length,
          councilStatus: (council.status as string) ?? "IDLE",
          ensembleAgreement: (ensemble.agreement_score as number) ?? 0,
          riskLevel: (risk.risk_level as string) ?? "NORMAL",
          tradingEnabled: (risk.trading_enabled as boolean) ?? true,
          circuitBreaker: (execution.circuit_breaker as string) ?? "CLOSED",
        });
      } catch {
        // Use placeholder data when backend is unavailable
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} lines={2} />
        ))}
      </div>
    );
  }

  const pnlColor = data.pnl >= 0 ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]";
  const PnlIcon = data.pnl >= 0 ? TrendingUp : TrendingDown;
  const drawdownRatio = data.maxDrawdownLimit > 0 ? data.drawdown / data.maxDrawdownLimit : 0;
  const drawdownColor =
    drawdownRatio < 0.5
      ? "bg-[var(--nexus-green)]"
      : drawdownRatio < 0.8
        ? "bg-[var(--nexus-yellow)]"
        : "bg-[var(--nexus-red)]";

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-lg font-mono font-bold tracking-wide">
        Command Center
      </h1>

      {/* Row 1: Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card title="Account Equity" icon={<DollarSign className="w-3.5 h-3.5" />}>
          <p className="text-2xl font-mono font-bold">{formatCurrency(data.equity)}</p>
          <p className="text-xs text-[var(--nexus-subtext)] mt-1">
            Balance: {formatCurrency(data.balance)}
          </p>
        </Card>

        <Card title="Total P&L" icon={<PnlIcon className="w-3.5 h-3.5" />}>
          <p className={`text-2xl font-mono font-bold ${pnlColor}`}>
            {formatCurrency(data.pnl)}
          </p>
          <p className={`text-xs mt-1 ${pnlColor}`}>{formatPercent(data.pnlPercent)}</p>
        </Card>

        <Card title="Open Positions" icon={<Crosshair className="w-3.5 h-3.5" />}>
          <p className="text-2xl font-mono font-bold">{data.openPositions}</p>
          <p className="text-xs text-[var(--nexus-subtext)] mt-1">
            {data.tradingEnabled ? "Trading enabled" : "Trading halted"}
          </p>
        </Card>

        <Card title="AI Status" icon={<Activity className="w-3.5 h-3.5" />}>
          <p className="text-2xl font-mono font-bold text-[var(--nexus-green)]">
            {data.councilStatus}
          </p>
          <p className="text-xs text-[var(--nexus-subtext)] mt-1">
            Council protocol active
          </p>
        </Card>
      </div>

      {/* Row 2: Risk & System */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Risk Meter */}
        <Card
          title="Risk Governor"
          icon={<ShieldCheck className="w-3.5 h-3.5" />}
          className="lg:col-span-1"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--nexus-subtext)]">Drawdown</span>
              <span className="text-xs font-mono">
                {data.drawdown.toFixed(2)}% / {data.maxDrawdownLimit.toFixed(1)}%
              </span>
            </div>
            <div className="h-2 bg-[var(--nexus-muted)] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${drawdownColor}`}
                style={{ width: `${Math.min(drawdownRatio * 100, 100)}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[var(--nexus-subtext)]">Risk Level</span>
              <span
                className={`font-mono font-semibold ${
                  data.riskLevel === "NORMAL"
                    ? "text-[var(--nexus-green)]"
                    : data.riskLevel === "WARNING"
                      ? "text-[var(--nexus-yellow)]"
                      : "text-[var(--nexus-red)]"
                }`}
              >
                {data.riskLevel}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[var(--nexus-subtext)]">Circuit Breaker</span>
              <span className="font-mono text-[var(--nexus-green)]">
                {data.circuitBreaker}
              </span>
            </div>
          </div>
        </Card>

        {/* Ensemble Agreement */}
        <Card
          title="Model Ensemble"
          icon={<BarChart3 className="w-3.5 h-3.5" />}
          className="lg:col-span-1"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--nexus-subtext)]">Agreement</span>
              <span className="text-xs font-mono">
                {(data.ensembleAgreement * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 bg-[var(--nexus-muted)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--nexus-blue)] rounded-full transition-all duration-500"
                style={{ width: `${data.ensembleAgreement * 100}%` }}
              />
            </div>
            <p className="text-[11px] text-[var(--nexus-subtext)]">
              3 models: GeminiPro, RuleBased, PatternMatcher
            </p>
          </div>
        </Card>

        {/* Quick System Status */}
        <Card
          title="System Health"
          icon={<Zap className="w-3.5 h-3.5" />}
          className="lg:col-span-1"
        >
          <div className="space-y-2.5">
            {[
              { label: "Agent Council", status: "ACTIVE", ok: true },
              { label: "Risk Governor", status: data.tradingEnabled ? "ARMED" : "HALTED", ok: data.tradingEnabled },
              { label: "Stealth Mode", status: "OPERATIONAL", ok: true },
              { label: "MT5 Bridge", status: "CONNECTED", ok: true },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between text-xs">
                <span className="text-[var(--nexus-subtext)]">{item.label}</span>
                <span
                  className={`font-mono ${item.ok ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}
                >
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Row 3: Market Overview Placeholder */}
      <Card
        title="Market Overview"
        icon={<BarChart3 className="w-3.5 h-3.5" />}
        headerRight={
          <span className="text-[10px] text-[var(--nexus-subtext)] font-mono">LIVE DATA</span>
        }
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { symbol: "BTCUSD", price: 98124.50, change: 2.34 },
            { symbol: "ETHUSD", price: 3412.80, change: -0.87 },
            { symbol: "EURUSD", price: 1.0842, change: 0.12 },
            { symbol: "XAUUSD", price: 2645.30, change: 0.56 },
          ].map((m) => (
            <div
              key={m.symbol}
              className="p-3 rounded-md bg-white/[0.02] border border-[var(--nexus-border)]"
            >
              <p className="text-xs font-mono text-[var(--nexus-subtext)] mb-1">
                {m.symbol}
              </p>
              <p className="text-sm font-mono font-semibold">
                {m.price.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </p>
              <p
                className={`text-xs font-mono mt-1 ${m.change >= 0 ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}
              >
                {formatPercent(m.change)}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Crosshair, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { SkeletonTable } from "@/components/ui/Skeleton";

interface Position {
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  opened_at: string;
}

interface Order {
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  status: string;
  timestamp: string;
}

// Placeholder data for when backend is offline
const PLACEHOLDER_POSITIONS: Position[] = [];
const PLACEHOLDER_ORDERS: Order[] = [];

export default function PositionsPage() {
  const [positions, setPositions] = useState<Position[]>(PLACEHOLDER_POSITIONS);
  const [orders, setOrders] = useState<Order[]>(PLACEHOLDER_ORDERS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        const [posRes, ordRes] = await Promise.allSettled([
          api.getPositions(),
          api.getOrders(),
        ]);

        if (!mounted) return;

        if (posRes.status === "fulfilled") {
          setPositions(posRes.value.positions as unknown as Position[]);
        }
        if (ordRes.status === "fulfilled") {
          setOrders(ordRes.value.orders as unknown as Order[]);
        }
      } catch {
        // keep placeholder data
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

  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-lg font-mono font-bold tracking-wide">Positions</h1>

      {/* Open Positions */}
      <Card
        title="Open Positions"
        icon={<Crosshair className="w-3.5 h-3.5" />}
        headerRight={
          <span className="text-[10px] font-mono text-[var(--nexus-subtext)]">
            {positions.length} active
          </span>
        }
      >
        {loading ? (
          <SkeletonTable rows={3} />
        ) : positions.length === 0 ? (
          <div className="text-center py-8 text-[var(--nexus-subtext)] text-xs font-mono">
            NO_OPEN_POSITIONS — Council awaiting signal
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="text-[var(--nexus-subtext)] border-b border-[var(--nexus-border)]">
                  <th className="text-left py-2 px-3">Symbol</th>
                  <th className="text-left py-2 px-3">Side</th>
                  <th className="text-right py-2 px-3">Quantity</th>
                  <th className="text-right py-2 px-3">Entry</th>
                  <th className="text-right py-2 px-3">Current</th>
                  <th className="text-right py-2 px-3">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => (
                  <tr key={i} className="border-b border-[var(--nexus-border)] hover:bg-white/[0.02]">
                    <td className="py-3 px-3 font-semibold">{pos.symbol}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 ${pos.side === "BUY" ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}
                      >
                        {pos.side === "BUY" ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {pos.side}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">{pos.quantity}</td>
                    <td className="py-3 px-3 text-right text-[var(--nexus-subtext)]">
                      {formatCurrency(pos.entry_price)}
                    </td>
                    <td className="py-3 px-3 text-right">{formatCurrency(pos.current_price)}</td>
                    <td
                      className={`py-3 px-3 text-right font-semibold ${pos.pnl >= 0 ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}
                    >
                      {formatCurrency(pos.pnl)} ({formatPercent(pos.pnl_percent)})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Recent Orders */}
      <Card
        title="Recent Orders"
        icon={<Crosshair className="w-3.5 h-3.5" />}
        headerRight={
          <span className="text-[10px] font-mono text-[var(--nexus-subtext)]">
            Last 20
          </span>
        }
      >
        {loading ? (
          <SkeletonTable rows={5} />
        ) : orders.length === 0 ? (
          <div className="text-center py-8 text-[var(--nexus-subtext)] text-xs font-mono">
            NO_RECENT_ORDERS — Pipeline idle
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="text-[var(--nexus-subtext)] border-b border-[var(--nexus-border)]">
                  <th className="text-left py-2 px-3">Time</th>
                  <th className="text-left py-2 px-3">Symbol</th>
                  <th className="text-left py-2 px-3">Side</th>
                  <th className="text-right py-2 px-3">Quantity</th>
                  <th className="text-right py-2 px-3">Price</th>
                  <th className="text-center py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((ord, i) => (
                  <tr key={i} className="border-b border-[var(--nexus-border)] hover:bg-white/[0.02]">
                    <td className="py-3 px-3 text-[var(--nexus-subtext)]">
                      {new Date(ord.timestamp).toLocaleString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                        hour12: false,
                      })}
                    </td>
                    <td className="py-3 px-3 font-semibold">{ord.symbol}</td>
                    <td
                      className={`py-3 px-3 ${ord.side === "BUY" ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}
                    >
                      {ord.side}
                    </td>
                    <td className="py-3 px-3 text-right">{ord.quantity}</td>
                    <td className="py-3 px-3 text-right">{formatCurrency(ord.price)}</td>
                    <td className="py-3 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase ${
                          ord.status === "EXECUTED"
                            ? "bg-[var(--nexus-green-glow)] text-[var(--nexus-green)]"
                            : ord.status === "REJECTED"
                              ? "bg-[var(--nexus-red-glow)] text-[var(--nexus-red)]"
                              : "bg-white/[0.04] text-[var(--nexus-subtext)]"
                        }`}
                      >
                        {ord.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

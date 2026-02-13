"use client";

import { useState } from "react";
import { BarChart3, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { formatPercent } from "@/lib/utils";

const MARKET_DATA = [
  { symbol: "BTCUSD", name: "Bitcoin", price: 98124.5, change: 2.34, volume: "42.3B", high: 99200.0, low: 96500.0, class: "crypto" },
  { symbol: "ETHUSD", name: "Ethereum", price: 3412.8, change: -0.87, volume: "18.1B", high: 3490.0, low: 3380.0, class: "crypto" },
  { symbol: "EURUSD", name: "EUR/USD", price: 1.0842, change: 0.12, volume: "6.2T", high: 1.0868, low: 1.0812, class: "forex" },
  { symbol: "GBPUSD", name: "GBP/USD", price: 1.2654, change: -0.24, volume: "3.1T", high: 1.2690, low: 1.2618, class: "forex" },
  { symbol: "XAUUSD", name: "Gold", price: 2645.3, change: 0.56, volume: "182B", high: 2660.0, low: 2630.0, class: "commodity" },
  { symbol: "AAPL", name: "Apple Inc.", price: 234.56, change: 1.12, volume: "54.2M", high: 236.10, low: 232.80, class: "stock" },
  { symbol: "NVDA", name: "NVIDIA Corp.", price: 892.30, change: 3.45, volume: "48.9M", high: 905.00, low: 878.00, class: "stock" },
  { symbol: "TSLA", name: "Tesla Inc.", price: 248.90, change: -1.82, volume: "62.1M", high: 255.00, low: 245.30, class: "stock" },
];

const FILTERS = ["all", "crypto", "forex", "stock", "commodity"] as const;

export default function MarketsPage() {
  const [filter, setFilter] = useState<string>("all");

  const filtered = filter === "all" ? MARKET_DATA : MARKET_DATA.filter((m) => m.class === filter);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-mono font-bold tracking-wide">Markets</h1>
        <div className="flex items-center gap-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-[11px] font-mono uppercase rounded transition-colors ${
                filter === f
                  ? "bg-[var(--nexus-green-glow)] text-[var(--nexus-green)] border border-[var(--nexus-border-active)]"
                  : "text-[var(--nexus-subtext)] hover:text-[var(--foreground)] border border-transparent"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Market table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-[var(--nexus-subtext)] border-b border-[var(--nexus-border)]">
                <th className="text-left py-2 px-3 font-medium">Symbol</th>
                <th className="text-left py-2 px-3 font-medium">Name</th>
                <th className="text-right py-2 px-3 font-medium">Price</th>
                <th className="text-right py-2 px-3 font-medium">24h Change</th>
                <th className="text-right py-2 px-3 font-medium">Volume</th>
                <th className="text-right py-2 px-3 font-medium">High</th>
                <th className="text-right py-2 px-3 font-medium">Low</th>
                <th className="text-center py-2 px-3 font-medium">Class</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m) => (
                <tr
                  key={m.symbol}
                  className="border-b border-[var(--nexus-border)] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-3 px-3 font-semibold">{m.symbol}</td>
                  <td className="py-3 px-3 text-[var(--nexus-subtext)]">{m.name}</td>
                  <td className="py-3 px-3 text-right font-semibold">
                    {m.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                  </td>
                  <td className={`py-3 px-3 text-right ${m.change >= 0 ? "text-[var(--nexus-green)]" : "text-[var(--nexus-red)]"}`}>
                    <span className="inline-flex items-center gap-1">
                      {m.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {formatPercent(m.change)}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right text-[var(--nexus-subtext)]">{m.volume}</td>
                  <td className="py-3 px-3 text-right text-[var(--nexus-subtext)]">
                    {m.high.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                  </td>
                  <td className="py-3 px-3 text-right text-[var(--nexus-subtext)]">
                    {m.low.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase bg-white/[0.04] text-[var(--nexus-subtext)]">
                      {m.class}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Market hours indicator */}
      <Card title="Session Status" icon={<Clock className="w-3.5 h-3.5" />}>
        <div className="grid grid-cols-3 gap-4">
          {[
            { name: "London", status: "OPEN", time: "08:00 - 16:00 GMT" },
            { name: "New York", status: "OPEN", time: "13:00 - 21:00 GMT" },
            { name: "Tokyo", status: "CLOSED", time: "00:00 - 09:00 GMT" },
          ].map((s) => (
            <div key={s.name} className="flex items-center justify-between p-3 rounded-md bg-white/[0.02]">
              <div>
                <p className="text-xs font-mono font-semibold">{s.name}</p>
                <p className="text-[10px] text-[var(--nexus-subtext)]">{s.time}</p>
              </div>
              <span
                className={`text-[10px] font-mono ${s.status === "OPEN" ? "text-[var(--nexus-green)]" : "text-[var(--nexus-subtext)]"}`}
              >
                {s.status}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

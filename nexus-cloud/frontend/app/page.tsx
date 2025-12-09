"use client";

import { Card } from "@/components/ui/Card";
import { Chart } from "@/components/trade/Chart";
import { Bitcoin, Zap, TrendingUp, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { nexusApi } from "@/lib/api";

export default function TradePage() {
  const [mode, setMode] = useState<"BUY" | "SELL">("BUY");
  const [status, setStatus] = useState("CONNECTING...");
  const [price, setPrice] = useState(98124.50);
  const [loading, setLoading] = useState(false);
  const [lots, setLots] = useState(0.01);

  // Poll for Status & Price
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const s = await nexusApi.getStatus();
        if (s.status === 'online') setStatus("CONNECTED");
        else setStatus("OFFLINE");

        const p = await nexusApi.getPrices();
        if (p.BTCUSD) setPrice(p.BTCUSD);
      } catch (e) {
        setStatus("ERROR");
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleTrade = async () => {
    setLoading(true);
    try {
      const res = await nexusApi.placeTrade('BTCUSD', mode, lots);
      if (res.status === 'Trade Executed') {
        alert(`✅ Order Executed\nTicket: ${res.ticket}`);
      } else {
        alert(`❌ Error: ${res.error || 'Unknown'}`);
      }
    } catch (e) {
      alert("❌ Execution Failed");
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen p-6 gap-6">
      {/* Chart Section - Takes available space */}
      <div className="flex-1 flex flex-col gap-6 h-full">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
              <Bitcoin className="text-orange-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">BTC/USD</h1>
              <div className="text-nexus-subtext text-xs font-mono">BITCOIN SPOT MARKET</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold font-mono text-nexus-green text-glow-green">
              ${price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="flex items-center justify-end gap-2 text-xs text-nexus-subtext">
              <span className="w-2 h-2 rounded-full bg-nexus-green animate-pulse" />
              MARKET OPEN
            </div>
          </div>
        </div>

        {/* Chart */}
        <Card className="flex-1 relative">
          <Chart />
        </Card>
      </div>

      {/* Sidebar Panel - Fixed Width */}
      <aside className="w-[360px] flex flex-col gap-6 overflow-y-auto">

        {/* Connection Status */}
        <Card className="p-4 bg-nexus-blue/5 border-nexus-blue/20">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-nexus-blue uppercase">Connection Status</span>
            <span className={cn("text-xs font-mono", status === "CONNECTED" ? "text-nexus-green" : "text-nexus-red")}>
              {status}
            </span>
          </div>
          <div className="h-1 bg-black/50 rounded-full overflow-hidden">
            <div className={cn("h-full w-full animate-pulse", status === "CONNECTED" ? "bg-nexus-green" : "bg-nexus-red")} />
          </div>
        </Card>

        {/* AI Intelligence */}
        <Card className="p-4 relative min-h-[200px]">
          <div className="absolute top-4 right-4 text-nexus-subtext"><Zap size={16} /></div>
          <h3 className="text-xs font-bold text-nexus-subtext uppercase mb-4">Nexus Intelligence</h3>

          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-full border-2 border-nexus-green flex items-center justify-center">
              <TrendingUp className="text-nexus-green" size={20} />
            </div>
            <div>
              <div className="text-xs text-nexus-subtext font-mono">DIRECTION</div>
              <div className="text-xl font-bold text-nexus-green">UPTREND</div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-nexus-subtext">Confidence</span>
              <span className="font-bold text-nexus-blue">87%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-nexus-subtext">Risk Level</span>
              <span className="font-bold text-nexus-green">LOW</span>
            </div>
          </div>
        </Card>

        {/* Trade Controls */}
        <div className="flex-1 flex flex-col">
          <div className="flex gap-2 mb-6 p-1 bg-white/5 rounded-xl border border-white/5">
            <button
              onClick={() => setMode("BUY")}
              className={cn(
                "flex-1 py-3 rounded-lg font-bold text-sm transition-all",
                mode === "BUY" ? "bg-nexus-green text-black shadow-[0_0_15px_rgba(0,221,128,0.3)]" : "text-nexus-subtext hover:text-white"
              )}
            >
              BUY
            </button>
            <button
              onClick={() => setMode("SELL")}
              className={cn(
                "flex-1 py-3 rounded-lg font-bold text-sm transition-all",
                mode === "SELL" ? "bg-nexus-red text-white shadow-[0_0_15px_rgba(255,59,48,0.3)]" : "text-nexus-subtext hover:text-white"
              )}
            >
              SELL
            </button>
          </div>

          <div className="space-y-4 mb-6">
            <div>
              <label className="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Amount (Lots)</label>
              <input
                type="number"
                value={lots}
                onChange={(e) => setLots(parseFloat(e.target.value))}
                step={0.01}
                className="w-full bg-black/40 border border-nexus-border rounded-xl p-3 text-white font-mono focus:border-nexus-green outline-none transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Stop Loss</label>
                <input type="number" placeholder="0.00" className="w-full bg-black/40 border border-nexus-border rounded-xl p-3 text-white font-mono focus:border-nexus-red outline-none transition-colors" />
              </div>
              <div>
                <label className="text-xs text-nexus-subtext font-bold block mb-2 uppercase">Take Profit</label>
                <input type="number" placeholder="0.00" className="w-full bg-black/40 border border-nexus-border rounded-xl p-3 text-white font-mono focus:border-nexus-green outline-none transition-colors" />
              </div>
            </div>
          </div>

          <button
            onClick={handleTrade}
            disabled={loading}
            className={cn(
              "w-full py-4 text-lg font-bold rounded-xl transition-all shadow-lg active:scale-[0.98] flex items-center justify-center gap-2",
              loading ? "opacity-50 cursor-not-allowed" : "",
              mode === "BUY" ? "bg-nexus-green text-black hover:bg-green-400 shadow-[0_0_20px_rgba(0,221,128,0.2)]" : "bg-nexus-red text-white hover:bg-red-500 shadow-[0_0_20px_rgba(255,59,48,0.2)]"
            )}>
            {loading ? <Loader2 className="animate-spin" /> : `EXECUTE ${mode}`}
          </button>
        </div>

      </aside>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Sparkles, Radio } from 'lucide-react';
import { ChartContainer } from '../components/trading/ChartContainer';
import { OrderBook } from '../components/trading/OrderBook';
import { TradeForm } from '../components/trading/TradeForm';
import { PositionTable } from '../components/trading/PositionTable';
import { placeTrade, getPositions, checkStatus } from '../services/api';

export const TradePage = ({ ticker, setTicker, marketType, setMarketType }) => {
    // State
    const [price, setPrice] = useState(0);
    const [trend, setTrend] = useState(0);
    const [chartData, setChartData] = useState([]);
    const [asks, setAsks] = useState([]);
    const [bids, setBids] = useState([]);
    const [trades, setTrades] = useState([]);
    const [autoPilot, setAutoPilot] = useState(false);
    const [aiSentiment, setAiSentiment] = useState("NEUTRAL");
    const [winProb, setWinProb] = useState(0);
    const [balance, setBalance] = useState(24593.42);

    // Mock Data Generation (Simulated Market)
    useEffect(() => {
        const interval = setInterval(async () => {
            let newPrice = price;
            let newTrend = trend;

            if (marketType === 'CRYPTO') {
                try {
                    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
                    const data = await res.json();
                    newPrice = data.bitcoin.usd;
                    newTrend = data.bitcoin.usd_24h_change;
                } catch (e) {
                    // Fallback if API fails
                    newPrice = price > 0 ? price + (Math.random() - 0.5) * 50 : 50000;
                }
            } else {
                const base = ticker === 'NVDA' ? 890 : ticker === 'TSLA' ? 175 : 180;
                newPrice = price > 0 ? price + (Math.random() - 0.5) * 2 : base;
                newTrend = trend + (Math.random() - 0.5) * 0.1;
            }

            setPrice(newPrice);
            setTrend(newTrend);

            // Update Chart
            const now = Math.floor(Date.now() / 1000);
            setChartData(prev => {
                const newData = [...prev, { time: now, value: newPrice }];
                if (newData.length > 100) newData.shift();
                return newData;
            });

            // Update Order Book
            const spread = newPrice * 0.0005;
            setAsks(Array.from({ length: 8 }, (_, i) => ({ p: newPrice + spread + (i * spread), a: Math.random() * 2 })));
            setBids(Array.from({ length: 8 }, (_, i) => ({ p: newPrice - spread - (i * spread), a: Math.random() * 2 })));

        }, 1000);
        return () => clearInterval(interval);
    }, [marketType, price, ticker]);

    // Initial Chart Data
    useEffect(() => {
        const initialData = [];
        let baseTime = Math.floor(Date.now() / 1000) - 1000;
        let basePrice = 50000;
        for (let i = 0; i < 100; i++) {
            basePrice += (Math.random() - 0.5) * 100;
            initialData.push({ time: baseTime + (i * 10), value: basePrice });
        }
        setChartData(initialData);
    }, []);

    const handleTrade = async (type, volume) => {
        // Optimistic UI update
        const newTrade = {
            id: Date.now(),
            ticket: 'PENDING',
            ticker,
            type,
            entry: price,
            pnl: "0.00",
            status: 'OPEN'
        };
        setTrades(prev => [newTrade, ...prev]);

        // Real Backend Call
        const result = await placeTrade(ticker, type, volume);
        if (result.status === 'EXECUTED') {
            // Update ticket
            setTrades(prev => prev.map(t => t.id === newTrade.id ? { ...t, ticket: result.ticket } : t));
        } else if (result.status === 'FAILED') {
            // Remove if failed
            // alert(`Trade Failed: ${result.error}`); // Optional: show error
        }
    };

    return (
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 h-[calc(100vh-80px)] overflow-y-auto">
            {/* LEFT: CHART & ANALYSIS */}
            <div className="lg:col-span-8 flex flex-col gap-6">
                {/* MAIN CHART CARD */}
                <div className="h-[500px] glass-panel rounded-3xl p-6 relative overflow-hidden shadow-2xl flex flex-col">
                    <div className="flex justify-between items-start mb-4 z-10">
                        <div>
                            <div className="flex items-baseline gap-3">
                                <h1 className="text-4xl md:text-6xl font-black text-white tracking-tighter">{ticker}</h1>
                                <span className={`text-xl font-mono font-bold ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {trend >= 0 ? '+' : ''}{trend.toFixed(2)}%
                                </span>
                            </div>
                            <div className="text-2xl font-mono text-zinc-400 mt-1">${price.toLocaleString()}</div>
                        </div>
                        <div className="text-right hidden md:block">
                            <div className={`px-3 py-1 rounded-full text-xs font-bold mb-1 inline-block ${aiSentiment === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>
                                {aiSentiment}
                            </div>
                            <div className="text-[10px] text-zinc-500 font-mono">CONFIDENCE: {winProb}%</div>
                        </div>
                    </div>

                    {/* CHART VISUALIZATION */}
                    <div className="flex-1 w-full relative">
                        <ChartContainer
                            data={chartData}
                            colors={{
                                lineColor: trend >= 0 ? '#10b981' : '#f43f5e',
                                areaTopColor: trend >= 0 ? 'rgba(16, 185, 129, 0.5)' : 'rgba(244, 63, 94, 0.5)',
                                areaBottomColor: trend >= 0 ? 'rgba(16, 185, 129, 0.0)' : 'rgba(244, 63, 94, 0.0)',
                            }}
                        />
                    </div>

                    {/* TIMEFRAMES */}
                    <div className="flex gap-2 mt-4 border-t border-white/5 pt-4">
                        {['1H', '4H', '1D', '1W'].map(t => <button key={t} className="glass-button px-3 py-1 rounded-lg text-[10px] font-bold text-zinc-500 hover:text-white">{t}</button>)}
                        <button className="ml-auto flex items-center gap-2 px-4 py-1 rounded-lg text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500/20 transition-all">
                            <Sparkles size={12} /> AI ANALYSIS
                        </button>
                    </div>
                </div>

                {/* ORDER BOOK & NEWS */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[300px]">
                    <OrderBook asks={asks} bids={bids} currentPrice={price} trend={trend} />

                    <div className="glass-panel rounded-3xl p-5 flex flex-col justify-center items-center text-center">
                        <div className="w-16 h-16 rounded-full bg-zinc-900 border border-white/10 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(245,158,11,0.1)]">
                            <Radio className="text-amber-500 animate-pulse" />
                        </div>
                        <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-2">Live Intelligence</div>
                        <p className="text-sm font-mono text-white leading-relaxed mb-4">"Market volatility increasing due to global macro events."</p>
                    </div>
                </div>
            </div>

            {/* RIGHT: EXECUTION & POSITIONS */}
            <div className="lg:col-span-4 flex flex-col gap-6">
                <TradeForm
                    onTrade={handleTrade}
                    balance={balance}
                    autoPilot={autoPilot}
                    setAutoPilot={setAutoPilot}
                />
                <PositionTable trades={trades} />
            </div>
        </div>
    );
};

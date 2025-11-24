import React, { useState } from 'react';
import { ChevronDown, ArrowUp, ArrowDown, Settings, Maximize2 } from 'lucide-react';
import { useToast } from '../context/ToastContext';

export const TradePage = ({ ticker = "BTC/USDT" }) => {
    const [side, setSide] = useState('buy');
    const [price, setPrice] = useState('64230.10');
    const [amount, setAmount] = useState('');
    const { addToast } = useToast();

    const handleTrade = () => {
        if (!amount) {
            addToast("Please enter an amount", "error");
            return;
        }
        addToast(`${side === 'buy' ? 'Buy' : 'Sell'} Order Placed Successfully!`, "success");
        setAmount('');
    };

    return (
        <div className="flex flex-col lg:flex-row h-[calc(100vh-100px)] gap-4">
            {/* LEFT COLUMN: CHART & ORDERS */}
            <div className="flex-1 flex flex-col gap-4 min-h-[500px]">
                {/* CHART CONTAINER */}
                <div className="flex-1 bg-nexus-card/50 backdrop-blur-sm border border-white/5 rounded-2xl p-4 relative overflow-hidden group">
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-3">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                {ticker} <ChevronDown size={16} className="text-nexus-subtext" />
                            </h2>
                            <span className="text-nexus-green font-mono font-bold">$64,230.10</span>
                        </div>
                        <div className="flex gap-2">
                            {['15m', '1h', '4h', '1D'].map(tf => (
                                <button key={tf} className="px-2 py-1 text-xs font-bold text-nexus-subtext hover:text-white hover:bg-white/10 rounded transition-colors">{tf}</button>
                            ))}
                            <button className="p-1 hover:bg-white/10 rounded"><Settings size={16} className="text-nexus-subtext" /></button>
                        </div>
                    </div>

                    {/* MOCK CHART VISUAL */}
                    <div className="absolute inset-0 top-16 bottom-0 left-0 right-0 opacity-20 pointer-events-none">
                        <svg width="100%" height="100%" viewBox="0 0 1000 400" preserveAspectRatio="none">
                            <path d="M0,300 Q100,250 200,320 T400,280 T600,200 T800,250 T1000,150" fill="none" stroke="#00FF94" strokeWidth="2" />
                            <path d="M0,300 L1000,300" stroke="#333" strokeWidth="1" strokeDasharray="5,5" />
                        </svg>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center text-nexus-subtext/20 font-bold text-4xl pointer-events-none">
                        TRADINGVIEW CHART
                    </div>
                </div>

                {/* ORDER BOOK (Simplified for Pro Look) */}
                <div className="h-64 bg-nexus-card/50 backdrop-blur-sm border border-white/5 rounded-2xl p-4 flex gap-4">
                    <div className="flex-1">
                        <h3 className="text-xs font-bold text-nexus-subtext mb-2">Order Book</h3>
                        <div className="space-y-1 font-mono text-xs">
                            {[1, 2, 3, 4, 5].map(i => (
                                <div key={i} className="flex justify-between text-nexus-red hover:bg-nexus-red/5 px-1 rounded cursor-pointer">
                                    <span>64,23{i}.00</span>
                                    <span>0.4{i}2</span>
                                </div>
                            ))}
                            <div className="text-center py-2 font-bold text-white text-sm">64,230.10</div>
                            {[1, 2, 3, 4, 5].map(i => (
                                <div key={i} className="flex justify-between text-nexus-green hover:bg-nexus-green/5 px-1 rounded cursor-pointer">
                                    <span>64,22{9 - i}.00</span>
                                    <span>0.8{i}1</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="flex-1 border-l border-white/5 pl-4">
                        <h3 className="text-xs font-bold text-nexus-subtext mb-2">Recent Trades</h3>
                        <div className="space-y-1 font-mono text-xs opacity-70">
                            <div className="flex justify-between text-nexus-green"><span>64,230.10</span><span>0.002</span></div>
                            <div className="flex justify-between text-nexus-red"><span>64,230.05</span><span>0.150</span></div>
                            <div className="flex justify-between text-nexus-green"><span>64,230.10</span><span>0.050</span></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* RIGHT COLUMN: TRADE FORM */}
            <div className="w-full lg:w-80 bg-nexus-card/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex flex-col shadow-2xl">
                <div className="flex bg-black/40 rounded-xl p-1 mb-6">
                    <button
                        onClick={() => setSide('buy')}
                        className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${side === 'buy' ? 'bg-nexus-green text-black shadow-[0_0_10px_rgba(0,255,148,0.4)]' : 'text-nexus-subtext hover:text-white'}`}
                    >
                        Buy
                    </button>
                    <button
                        onClick={() => setSide('sell')}
                        className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${side === 'sell' ? 'bg-nexus-red text-white shadow-[0_0_10px_rgba(255,46,84,0.4)]' : 'text-nexus-subtext hover:text-white'}`}
                    >
                        Sell
                    </button>
                </div>

                <div className="space-y-4 flex-1">
                    <div>
                        <label className="text-xs text-nexus-subtext mb-1 block">Price (USDT)</label>
                        <div className="bg-black/40 border border-white/10 rounded-xl px-4 py-3 flex justify-between items-center focus-within:border-nexus-blue/50 transition-colors">
                            <input
                                type="text"
                                value={price}
                                onChange={(e) => setPrice(e.target.value)}
                                className="bg-transparent text-white font-mono font-bold w-full outline-none"
                            />
                            <span className="text-xs text-nexus-subtext">USDT</span>
                        </div>
                    </div>

                    <div>
                        <label className="text-xs text-nexus-subtext mb-1 block">Amount (BTC)</label>
                        <div className="bg-black/40 border border-white/10 rounded-xl px-4 py-3 flex justify-between items-center focus-within:border-nexus-blue/50 transition-colors">
                            <input
                                type="text"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder="0.00"
                                className="bg-transparent text-white font-mono font-bold w-full outline-none"
                            />
                            <span className="text-xs text-nexus-subtext">BTC</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2">
                        {[25, 50, 75, 100].map(pct => (
                            <button key={pct} onClick={() => setAmount((0.1542 * (pct / 100)).toFixed(4))} className="bg-white/5 hover:bg-white/10 text-xs text-nexus-subtext py-1 rounded-lg transition-colors">{pct}%</button>
                        ))}
                    </div>

                    <div className="pt-4 border-t border-white/5">
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-nexus-subtext">Total</span>
                            <span className="font-bold text-white">{(parseFloat(price) * (parseFloat(amount) || 0)).toFixed(2)} USDT</span>
                        </div>
                        <div className="flex justify-between text-xs text-nexus-subtext">
                            <span>Available</span>
                            <span>12,450.00 USDT</span>
                        </div>
                    </div>
                </div>

                <button
                    onClick={handleTrade}
                    className={`w-full py-4 rounded-xl font-bold text-lg mt-6 shadow-lg transition-transform active:scale-95 ${side === 'buy' ? 'bg-nexus-green text-black shadow-nexus-green/20' : 'bg-nexus-red text-white shadow-nexus-red/20'}`}
                >
                    {side === 'buy' ? 'Buy BTC' : 'Sell BTC'}
                </button>
            </div>
        </div>
    );
};

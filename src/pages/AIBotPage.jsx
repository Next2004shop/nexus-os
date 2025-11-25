import React, { useState } from 'react';
import { Bot, Zap, Link, Shield, Activity, TrendingUp, Server, CheckCircle, AlertCircle } from 'lucide-react';

export const AIBotPage = () => {
    const [connected, setConnected] = useState(false);
    const [broker, setBroker] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [isLearning, setIsLearning] = useState(true);

    const handleConnect = (e) => {
        e.preventDefault();
        // Mock connection
        setTimeout(() => {
            setConnected(true);
        }, 1500);
    };

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto animate-fadeIn pb-24">
            {/* HEADER */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-black text-white flex items-center gap-3">
                        <Bot className="text-nexus-blue" size={32} />
                        NEXUS <span className="text-nexus-blue">AI CORE</span>
                    </h1>
                    <p className="text-nexus-subtext text-sm mt-1">Autonomous Trading Neural Network</p>
                </div>
                <div className="flex items-center gap-2 bg-nexus-blue/10 px-4 py-2 rounded-full border border-nexus-blue/20">
                    <div className="w-2 h-2 bg-nexus-green rounded-full animate-pulse"></div>
                    <span className="text-nexus-blue text-xs font-bold">SYSTEM ONLINE</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* LEFT: CONNECTION PANEL */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Link size={20} className="text-nexus-yellow" />
                            Broker Connection
                        </h2>

                        {!connected ? (
                            <form onSubmit={handleConnect} className="space-y-4">
                                <div>
                                    <label className="text-xs text-nexus-subtext font-bold uppercase mb-1 block">Platform</label>
                                    <select
                                        className="w-full bg-nexus-black border border-nexus-border rounded-xl p-3 text-white focus:border-nexus-blue outline-none"
                                        value={broker}
                                        onChange={(e) => setBroker(e.target.value)}
                                    >
                                        <option value="">Select Platform</option>
                                        <option value="mt5">MetaTrader 5</option>
                                        <option value="mt4">MetaTrader 4</option>
                                        <option value="fxpesa">FXPesa</option>
                                        <option value="binance">Binance</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-nexus-subtext font-bold uppercase mb-1 block">API Key / Login ID</label>
                                    <input
                                        type="text"
                                        className="w-full bg-nexus-black border border-nexus-border rounded-xl p-3 text-white focus:border-nexus-blue outline-none"
                                        placeholder="Enter ID"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={!broker || !apiKey}
                                    className="w-full py-3 bg-nexus-blue text-black font-bold rounded-xl hover:bg-nexus-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    ESTABLISH LINK
                                </button>
                            </form>
                        ) : (
                            <div className="space-y-4">
                                <div className="bg-nexus-green/10 border border-nexus-green/20 p-4 rounded-xl flex items-center gap-3">
                                    <CheckCircle className="text-nexus-green" size={24} />
                                    <div>
                                        <div className="text-white font-bold">Connected to {broker.toUpperCase()}</div>
                                        <div className="text-xs text-nexus-green">Latency: 12ms</div>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Account Balance</span>
                                        <span className="text-white font-mono">$12,450.00</span>
                                    </div>
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Active Positions</span>
                                        <span className="text-white font-mono">3</span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setConnected(false)}
                                    className="w-full py-2 border border-nexus-red/50 text-nexus-red text-xs font-bold rounded-lg hover:bg-nexus-red/10 transition-colors"
                                >
                                    DISCONNECT
                                </button>
                            </div>
                        )}
                    </div>

                    {/* RISK SETTINGS */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Shield size={20} className="text-nexus-red" />
                            Risk Management
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-xs text-nexus-subtext mb-1">
                                    <span>Max Drawdown</span>
                                    <span className="text-white">15%</span>
                                </div>
                                <div className="h-2 bg-nexus-black rounded-full overflow-hidden">
                                    <div className="h-full bg-nexus-red w-[15%]"></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs text-nexus-subtext mb-1">
                                    <span>Lot Size Allocation</span>
                                    <span className="text-white">Dynamic (AI)</span>
                                </div>
                                <div className="h-2 bg-nexus-black rounded-full overflow-hidden">
                                    <div className="h-full bg-nexus-blue w-[75%]"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CENTER/RIGHT: AI DASHBOARD */}
                <div className="lg:col-span-2 space-y-6">
                    {/* LEARNING VISUALIZATION */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4">
                            <Activity className="text-nexus-blue opacity-20" size={100} />
                        </div>
                        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                            <Zap size={20} className="text-nexus-yellow" />
                            Neural Network Status
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Win Rate</div>
                                <div className="text-2xl font-mono font-bold text-nexus-green">78.4%</div>
                                <div className="text-[10px] text-nexus-subtext">Last 100 Trades</div>
                            </div>
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Learning Cycles</div>
                                <div className="text-2xl font-mono font-bold text-nexus-blue">14,205</div>
                                <div className="text-[10px] text-nexus-subtext">Adapting to Volatility</div>
                            </div>
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Profit Factor</div>
                                <div className="text-2xl font-mono font-bold text-nexus-yellow">2.45</div>
                                <div className="text-[10px] text-nexus-subtext">High Efficiency</div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-bold text-white">Pattern Recognition: Bullish Divergence</span>
                                <span className="text-xs text-nexus-green animate-pulse">Learning...</span>
                            </div>
                            <div className="h-1.5 bg-nexus-black rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-nexus-blue to-nexus-purple w-[85%] animate-pulse"></div>
                            </div>
                            <p className="text-xs text-nexus-subtext mt-2">
                                The AI is currently analyzing historical data from connected accounts to optimize entry points for the upcoming session.
                            </p>
                        </div>
                    </div>

                    {/* RECENT AI TRADES */}
                    <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                        <div className="p-4 border-b border-nexus-border flex justify-between items-center">
                            <h3 className="font-bold text-white">Recent AI Executions</h3>
                            <button className="text-xs text-nexus-blue font-bold">View All</button>
                        </div>
                        <div className="divide-y divide-white/5">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${i === 2 ? 'bg-nexus-red/10 text-nexus-red' : 'bg-nexus-green/10 text-nexus-green'}`}>
                                            {i === 2 ? <ArrowDownRight size={16} /> : <ArrowUpRight size={16} />}
                                        </div>
                                        <div>
                                            <div className="font-bold text-white text-sm">BTC/USDT</div>
                                            <div className="text-xs text-nexus-subtext">Scalp Strategy • 5m</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className={`font-mono font-bold ${i === 2 ? 'text-nexus-red' : 'text-nexus-green'}`}>
                                            {i === 2 ? '-$45.20' : '+$128.50'}
                                        </div>
                                        <div className="text-[10px] text-nexus-subtext">12:3{i} PM</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

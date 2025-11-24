import React from 'react';
import { TrendingUp, Activity, Globe, Zap, ArrowUpRight, ArrowDownRight, CreditCard, RefreshCw } from 'lucide-react';

const StatCard = ({ label, value, change, isPositive }) => (
    <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-4 rounded-2xl hover:bg-white/10 transition-all group">
        <div className="flex justify-between items-start mb-2">
            <span className="text-nexus-subtext text-xs font-medium uppercase tracking-wider">{label}</span>
            <div className={`p-1.5 rounded-lg ${isPositive ? 'bg-nexus-green/10 text-nexus-green' : 'bg-nexus-red/10 text-nexus-red'}`}>
                {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            </div>
        </div>
        <div className="text-2xl font-bold text-white mb-1 group-hover:text-nexus-blue transition-colors">{value}</div>
        <div className={`text-xs font-medium ${isPositive ? 'text-nexus-green' : 'text-nexus-red'}`}>
            {change} <span className="text-nexus-subtext ml-1">vs last 24h</span>
        </div>
    </div>
);

const MarketTicker = ({ symbol, price, change }) => {
    const isPositive = parseFloat(change) >= 0;
    return (
        <div className="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl transition-colors cursor-pointer border border-transparent hover:border-white/5">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-800 to-black border border-white/10 flex items-center justify-center font-bold text-xs">
                    {symbol[0]}
                </div>
                <div>
                    <div className="font-bold text-sm">{symbol}</div>
                    <div className="text-xs text-nexus-subtext">USDT</div>
                </div>
            </div>
            <div className="text-right">
                <div className="font-mono font-medium text-sm">{price}</div>
                <div className={`text-xs ${isPositive ? 'text-nexus-green' : 'text-nexus-red'}`}>
                    {isPositive ? '+' : ''}{change}%
                </div>
            </div>
        </div>
    );
};

export const HomePage = ({ onNavigate }) => {
    return (
        <div className="space-y-6">
            {/* WELCOME SECTION */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white via-nexus-blue to-purple-500 bg-clip-text text-transparent animate-fadeIn">
                        Command Center
                    </h1>
                    <p className="text-nexus-subtext mt-1">Welcome back, Commander. Market sentiment is <span className="text-nexus-green">Bullish</span>.</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={() => onNavigate('wallet')} className="px-4 py-2 bg-nexus-blue/10 text-nexus-blue border border-nexus-blue/50 rounded-xl font-bold text-sm hover:bg-nexus-blue/20 transition-all shadow-[0_0_10px_rgba(0,240,255,0.2)]">
                        Deposit Assets
                    </button>
                </div>
            </div>

            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Portfolio Value" value="$12,450.00" change="+2.5%" isPositive={true} />
                <StatCard label="24h Profit" value="+$320.50" change="+1.2%" isPositive={true} />
                <StatCard label="Active Trades" value="3" change="-1" isPositive={false} />
                <StatCard label="Global Volume" value="$42.5B" change="+5.4%" isPositive={true} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* MARKET OVERVIEW */}
                <div className="lg:col-span-2 bg-nexus-card/50 backdrop-blur-md border border-white/5 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-lg flex items-center gap-2">
                            <Activity className="text-nexus-blue" size={20} />
                            Live Markets
                        </h3>
                        <button className="text-xs text-nexus-blue hover:text-white transition-colors">View All</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <MarketTicker symbol="BTC" price="64,230.10" change="0.85" />
                        <MarketTicker symbol="ETH" price="3,450.55" change="-0.42" />
                        <MarketTicker symbol="SOL" price="145.20" change="5.60" />
                        <MarketTicker symbol="BNB" price="593.20" change="1.24" />
                        <MarketTicker symbol="XRP" price="0.62" change="0.15" />
                        <MarketTicker symbol="DOGE" price="0.16" change="2.30" />
                    </div>
                </div>

                {/* AI INSIGHTS */}
                <div className="bg-gradient-to-b from-nexus-blue/5 to-purple-500/5 border border-white/5 rounded-2xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-nexus-blue/10 rounded-full blur-3xl"></div>
                    <h3 className="font-bold text-lg flex items-center gap-2 mb-4 relative z-10">
                        <Zap className="text-nexus-yellow" size={20} />
                        AI Insights
                    </h3>
                    <div className="space-y-4 relative z-10">
                        <div className="bg-black/40 p-4 rounded-xl border-l-2 border-nexus-green">
                            <p className="text-xs text-nexus-subtext mb-1">Bitcoin (BTC)</p>
                            <p className="text-sm font-medium">Strong buy signal detected on 4H timeframe. RSI divergence suggests upward momentum.</p>
                        </div>
                        <div className="bg-black/40 p-4 rounded-xl border-l-2 border-nexus-red">
                            <p className="text-xs text-nexus-subtext mb-1">Ethereum (ETH)</p>
                            <p className="text-sm font-medium">Resistance at $3,500. Consider taking profits if volume decreases.</p>
                        </div>
                    </div>
                    <button className="w-full mt-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold transition-colors">
                        Ask Nexus AI
                    </button>
                </div>
            </div>
        </div>
    );
};

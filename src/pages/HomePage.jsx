import React, { useState, useEffect } from 'react';
import { TrendingUp, Activity, Globe, ArrowUpRight, ArrowDownRight, Newspaper, Zap } from 'lucide-react';
import { marketData } from '../services/marketData';

const StatCard = ({ title, value, change, isPositive }) => (
    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl hover:border-nexus-blue/50 transition-all group">
        <div className="flex justify-between items-start mb-4">
            <span className="text-nexus-subtext text-sm font-medium">{title}</span>
            <div className={`p-2 rounded-lg ${isPositive ? 'bg-nexus-green/10 text-nexus-green' : 'bg-nexus-red/10 text-nexus-red'}`}>
                {isPositive ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
            </div>
        </div>
        <div className="text-2xl font-bold text-white mb-1">{value}</div>
        <div className={`text-xs font-medium ${isPositive ? 'text-nexus-green' : 'text-nexus-red'}`}>
            {isPositive ? '+' : ''}{change}% <span className="text-nexus-subtext ml-1">vs last 24h</span>
        </div>
    </div>
);

const MarketRow = ({ coin }) => (
    <div className="flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-colors cursor-pointer group border-b border-white/5 last:border-0">
        <div className="flex items-center gap-4">
            <img src={coin.image} alt={coin.name} className="w-10 h-10 rounded-full" />
            <div>
                <div className="font-bold text-white group-hover:text-nexus-blue transition-colors">{coin.symbol.toUpperCase()}</div>
                <div className="text-xs text-nexus-subtext">{coin.name}</div>
            </div>
        </div>
        <div className="text-right">
            <div className="font-mono text-white">${coin.current_price?.toLocaleString() || '0.00'}</div>
            <div className={`text-xs font-medium ${coin.price_change_percentage_24h >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                {coin.price_change_percentage_24h ? coin.price_change_percentage_24h.toFixed(2) : '0.00'}%
            </div>
        </div>
    </div>
);

const NewsCard = ({ news }) => (
    <div className="bg-nexus-card border border-nexus-border p-4 rounded-xl hover:border-nexus-blue/30 transition-all">
        <div className="flex justify-between items-start mb-2">
            <span className="text-nexus-blue text-xs font-bold px-2 py-1 bg-nexus-blue/10 rounded-md">CRYPTO</span>
            <span className="text-nexus-subtext text-[10px]">{new Date(news.created_at * 1000).toLocaleDateString()}</span>
        </div>
        <p className="text-white text-sm font-medium line-clamp-2 mb-2">{news.description || news.user_title}</p>
        <div className="flex items-center gap-2 text-nexus-subtext text-xs">
            <Globe size={12} />
            <span>{news.project?.name || 'Market Update'}</span>
        </div>
    </div>
);

const HomePage = () => {
    const [coins, setCoins] = useState([]);
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [coinData, newsData] = await Promise.all([
                    marketData.getTopCryptos(),
                    marketData.getNews()
                ]);
                setCoins(coinData || []);
                setNews((newsData || []).slice(0, 6));
            } catch (err) {
                console.error("Failed to load home data", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="p-8 text-nexus-blue animate-pulse">Loading Command Center...</div>;

    return (
        <div className="p-6 space-y-8 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-1">Command Center</h1>
                    <p className="text-nexus-subtext text-sm">Global Market Overview</p>
                </div>
                <div className="flex gap-2">
                    <button className="bg-nexus-blue/10 text-nexus-blue px-4 py-2 rounded-lg text-sm font-bold hover:bg-nexus-blue/20 transition-colors">
                        + Deposit
                    </button>
                </div>
            </div>

            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard title="Total Balance" value="$124,592.00" change="2.4" isPositive={true} />
                <StatCard title="24h Profit" value="+$1,240.50" change="1.1" isPositive={true} />
                <StatCard title="Active Trades" value="8" change="-0.5" isPositive={false} />
            </div>

            {/* MAIN CONTENT SPLIT */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* LEFT: LIVE MARKETS */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center gap-2 text-white font-bold text-lg">
                        <Activity className="text-nexus-green" />
                        <h2>Live Markets</h2>
                    </div>
                    <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                        <div className="p-4 border-b border-white/5 flex justify-between text-xs text-nexus-subtext font-bold uppercase tracking-wider">
                            <span>Asset</span>
                            <span>Price / 24h</span>
                        </div>
                        <div className="divide-y divide-white/5">
                            {coins.map(coin => (
                                <MarketRow key={coin.id} coin={coin} />
                            ))}
                        </div>
                    </div>
                </div>

                {/* RIGHT: NEWS FEED */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 text-white font-bold text-lg">
                        <Newspaper className="text-nexus-yellow" />
                        <h2>Global Intel</h2>
                    </div>
                    <div className="space-y-4">
                        {news.map((item, idx) => (
                            <NewsCard key={idx} news={item} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HomePage;

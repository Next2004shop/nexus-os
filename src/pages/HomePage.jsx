import React, { useState, useEffect } from 'react';
import { TrendingUp, Activity, Globe, ArrowUpRight, ArrowDownRight, Newspaper, Zap, Search, Filter } from 'lucide-react';
import { marketData } from '../services/marketData';
import { NewsItem } from '../components/NewsItem';

const StatCard = ({ title, value, change, isPositive }) => (
    <div className="bg-nexus-card border border-nexus-border p-4 rounded-2xl hover:border-nexus-blue/50 transition-all group min-w-[160px]">
        <div className="flex justify-between items-start mb-2">
            <span className="text-nexus-subtext text-xs font-medium">{title}</span>
            <div className={`p-1.5 rounded-lg ${isPositive ? 'bg-nexus-green/10 text-nexus-green' : 'bg-nexus-red/10 text-nexus-red'}`}>
                {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            </div>
        </div>
        <div className="text-lg font-bold text-white mb-1">{value}</div>
        <div className={`text-[10px] font-medium ${isPositive ? 'text-nexus-green' : 'text-nexus-red'}`}>
            {isPositive ? '+' : ''}{change}%
        </div>
    </div>
);

const MarketTicker = ({ coins }) => (
    <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar">
        {coins.map(coin => (
            <div key={coin.id} className="flex items-center gap-3 bg-nexus-card border border-nexus-border px-4 py-2 rounded-xl shrink-0 hover:bg-white/5 transition-colors cursor-pointer">
                <img src={coin.image} alt={coin.name} className="w-6 h-6 rounded-full" />
                <div>
                    <div className="font-bold text-white text-sm">{coin.symbol.toUpperCase()}</div>
                    <div className={`text-xs ${coin.price_change_percentage_24h >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                        {coin.price_change_percentage_24h?.toFixed(2)}%
                    </div>
                </div>
                <div className="text-sm font-mono text-white/80">
                    ${coin.current_price?.toLocaleString()}
                </div>
            </div>
        ))}
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
                // Duplicate news to simulate infinite scroll feel for now
                const baseNews = newsData || [];
                setNews([...baseNews, ...baseNews, ...baseNews]);
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

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-nexus-black">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-nexus-blue"></div>
        </div>
    );

    return (
        <div className="min-h-screen bg-nexus-black pb-24">
            {/* HEADER STATS (Scrollable horizontally on mobile) */}
            <div className="p-4 space-y-4 bg-nexus-black/50 backdrop-blur-xl sticky top-0 z-20 border-b border-white/5">
                <div className="flex justify-between items-center">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <Globe className="text-nexus-blue" size={20} />
                        Global Intel
                    </h1>
                    <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <Search size={20} className="text-nexus-subtext" />
                    </button>
                </div>

                {/* Quick Stats Row */}
                <div className="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
                    <StatCard title="Portfolio" value="$124,592" change="2.4" isPositive={true} />
                    <StatCard title="24h PnL" value="+$1,240" change="1.1" isPositive={true} />
                    <StatCard title="AI Bot" value="+8.5%" change="0.5" isPositive={true} />
                </div>

                {/* Market Ticker */}
                <MarketTicker coins={coins} />
            </div>

            {/* MAIN NEWS FEED */}
            <div className="max-w-2xl mx-auto p-4 space-y-4">
                <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-bold text-nexus-subtext uppercase tracking-wider">Latest Updates</h2>
                    <button className="flex items-center gap-1 text-xs text-nexus-blue font-bold">
                        <Filter size={12} /> Filter
                    </button>
                </div>

                {news.map((item, idx) => (
                    <NewsItem
                        key={idx}
                        title={item.description || item.user_title || "Market Update"}
                        description={item.user_title ? item.description : ""}
                        source={item.project?.name || "System"}
                        time="Just now"
                        image={item.project?.image?.large || null}
                        category={item.category || "CRYPTO"}
                    />
                ))}

                <div className="py-8 text-center text-nexus-subtext text-xs animate-pulse">
                    Loading more insights...
                </div>
            </div>
        </div>
    );
};

export default HomePage;

import React, { useState, useEffect } from 'react';
import { TrendingUp, Activity, Globe, ArrowUpRight, ArrowDownRight, Newspaper, Zap, Search, Filter, Calendar, BarChart3, AlertTriangle } from 'lucide-react';
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

const SentimentGauge = () => (
    <div className="bg-nexus-card border border-nexus-border p-4 rounded-2xl relative overflow-hidden">
        <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Activity size={16} className="text-nexus-purple" />
                Market Sentiment
            </h3>
            <span className="text-xs font-bold text-nexus-green bg-nexus-green/10 px-2 py-0.5 rounded">GREED</span>
        </div>
        <div className="relative h-2 bg-white/10 rounded-full overflow-hidden mb-2">
            <div className="absolute top-0 left-0 h-full w-[75%] bg-gradient-to-r from-nexus-red via-nexus-yellow to-nexus-green"></div>
        </div>
        <div className="flex justify-between text-[10px] text-nexus-subtext font-bold uppercase">
            <span>Extreme Fear</span>
            <span>Neutral</span>
            <span className="text-white">Extreme Greed</span>
        </div>
    </div>
);

const TopMovers = ({ coins }) => (
    <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp size={16} className="text-nexus-green" />
                Top Movers (24h)
            </h3>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-4 no-scrollbar">
            {coins.slice(0, 5).map(coin => (
                <div key={coin.id} className="min-w-[140px] bg-nexus-card border border-nexus-border p-3 rounded-xl hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-2 mb-2">
                        <img src={coin.image} alt={coin.symbol} className="w-6 h-6 rounded-full" />
                        <span className="font-bold text-white text-xs">{coin.symbol.toUpperCase()}</span>
                    </div>
                    <div className="text-sm font-mono text-white font-bold">${coin.current_price?.toLocaleString()}</div>
                    <div className={`text-xs font-bold mt-1 ${coin.price_change_percentage_24h >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                        {coin.price_change_percentage_24h >= 0 ? '+' : ''}{coin.price_change_percentage_24h?.toFixed(2)}%
                    </div>
                </div>
            ))}
        </div>
    </div>
);

const EconomicEvent = () => (
    <div className="bg-gradient-to-br from-nexus-blue/20 to-nexus-purple/20 border border-nexus-blue/30 p-4 rounded-2xl flex items-center justify-between">
        <div>
            <div className="text-[10px] text-nexus-blue font-bold uppercase mb-1 flex items-center gap-1">
                <Calendar size={12} /> Upcoming Event
            </div>
            <div className="text-white font-bold text-sm">FOMC Meeting Minutes</div>
            <div className="text-nexus-subtext text-xs mt-1">High Volatility Expected</div>
        </div>
        <div className="text-center bg-nexus-black/50 p-2 rounded-lg border border-white/10">
            <div className="text-xs text-nexus-subtext uppercase">In</div>
            <div className="text-lg font-mono font-bold text-white">2d</div>
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

                // ROBUST MOCK DATA GENERATOR
                const mockNews = [
                    {
                        user_title: "Bitcoin Breaks $90k Resistance Level",
                        description: "BTC shows strong momentum as institutional inflows reach record highs. Analysts predict a run to $100k by month end.",
                        project: { name: "CryptoDaily", image: { large: "https://assets.coingecko.com/coins/images/1/large/bitcoin.png" } },
                        category: "MARKET ALERT"
                    },
                    {
                        user_title: "Ethereum 2.0 Staking Yields Increase",
                        description: "Validators are seeing higher returns as network activity surges. Gas fees remain stable despite high volume.",
                        project: { name: "DeFi Pulse", image: { large: "https://assets.coingecko.com/coins/images/279/large/ethereum.png" } },
                        category: "DEFI"
                    },
                    {
                        user_title: "Solana Ecosystem Expands with New DEX",
                        description: "A new decentralized exchange on Solana promises zero-slippage trading and instant settlement.",
                        project: { name: "SolanaNews", image: { large: "https://assets.coingecko.com/coins/images/4128/large/solana.png" } },
                        category: "ECOSYSTEM"
                    },
                    {
                        user_title: "Fed Chair Powell Signals Rate Cuts",
                        description: "Markets rally as the Federal Reserve hints at a dovish pivot in the upcoming quarter.",
                        project: { name: "MacroInsider", image: null },
                        category: "MACRO"
                    }
                ];

                // Use real news if available, otherwise fallback to mock
                const finalNews = (newsData && newsData.length > 0) ? newsData : mockNews;
                // Duplicate for feed length
                setNews([...finalNews, ...mockNews, ...finalNews]);

            } catch (err) {
                console.error("Failed to load home data", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-nexus-black">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-nexus-blue"></div>
        </div>
    );

    return (
        <div className="min-h-screen bg-nexus-black pb-32 overflow-y-auto">
            {/* HEADER STATS (Sticky) */}
            <div className="p-4 space-y-4 bg-nexus-black/80 backdrop-blur-xl sticky top-0 z-20 border-b border-white/5">
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
            </div>

            {/* MAIN CONTENT */}
            <div className="max-w-2xl mx-auto p-4 space-y-6">

                {/* MARKET SENTIMENT & EVENT */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <SentimentGauge />
                    <EconomicEvent />
                </div>

                {/* TOP MOVERS */}
                <TopMovers coins={coins} />

                {/* NEWS FEED */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-bold text-nexus-subtext uppercase tracking-wider flex items-center gap-2">
                            <Newspaper size={16} /> Latest Updates
                        </h2>
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
                </div>

                <div className="py-8 text-center">
                    <button className="text-xs font-bold text-nexus-subtext hover:text-white transition-colors uppercase tracking-widest">
                        End of Feed
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HomePage;

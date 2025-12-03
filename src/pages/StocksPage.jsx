import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, Globe, Zap, Activity, ArrowUpRight, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { marketData } from '../services/marketData';

const StockCard = ({ item, onClick }) => (
    <div
        onClick={() => onClick(item)}
        className="bg-white/5 border border-white/10 rounded-2xl p-4 relative overflow-hidden group cursor-pointer hover:border-nexus-blue/50 transition-all hover:shadow-[0_0_20px_rgba(0,240,255,0.1)]"
    >
        <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-100 transition-opacity">
            <ArrowUpRight className="text-nexus-blue" size={20} />
        </div>

        <div className="flex items-start justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-nexus-blue/20 to-purple-500/20 flex items-center justify-center text-white font-bold border border-white/10">
                {item.symbol[0]}
            </div>
            <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg ${item.change >= 0 ? 'bg-green-500/10 text-nexus-green' : 'bg-red-500/10 text-nexus-red'}`}>
                {item.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                {Math.abs(item.change)}%
            </div>
        </div>

        <div>
            <h3 className="text-lg font-bold text-white tracking-wide">{item.symbol}</h3>
            <p className="text-xs text-nexus-subtext mb-2">{item.name}</p>
            <div className="text-2xl font-mono font-medium text-white">
                ${item.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
        </div>
    </div>
);

const StockRow = ({ item, onClick }) => (
    <div
        onClick={() => onClick(item)}
        className="flex items-center justify-between p-4 hover:bg-white/5 border-b border-white/5 last:border-0 cursor-pointer transition-colors group"
    >
        <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-[#1e2026] flex items-center justify-center text-zinc-400 font-bold text-sm group-hover:text-white group-hover:bg-nexus-blue/20 transition-colors">
                {item.symbol[0]}
            </div>
            <div>
                <div className="font-bold text-white group-hover:text-nexus-blue transition-colors">{item.symbol}</div>
                <div className="text-xs text-nexus-subtext">{item.name}</div>
            </div>
        </div>

        <div className="flex items-center gap-8">
            <div className="hidden md:block w-24 h-8">
                {/* Simulated Sparkline */}
                <svg viewBox="0 0 100 30" className={`w-full h-full stroke-2 fill-none ${item.change >= 0 ? 'stroke-nexus-green' : 'stroke-nexus-red'}`}>
                    <path d={`M0,15 Q25,${item.change >= 0 ? 5 : 25} 50,15 T100,${item.change >= 0 ? 5 : 25}`} />
                </svg>
            </div>
            <div className="text-right min-w-[80px]">
                <div className="font-mono font-medium text-white">${item.price.toFixed(2)}</div>
                <div className={`text-xs font-bold ${item.change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                    {item.change > 0 ? '+' : ''}{item.change}%
                </div>
            </div>
        </div>
    </div>
);

export const StocksPage = () => {
    const [search, setSearch] = useState('');
    const [stocks, setStocks] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchStocks = async () => {
            try {
                const data = await marketData.getStocks();
                setStocks(data);
            } catch (error) {
                console.error("Failed to fetch stocks:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStocks();
        const interval = setInterval(fetchStocks, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const filteredData = stocks.filter(item =>
        item.symbol.toLowerCase().includes(search.toLowerCase()) ||
        item.name.toLowerCase().includes(search.toLowerCase())
    );

    const handleItemClick = (item) => {
        // Navigate to trade page with asset data
        navigate('/trade', { state: { asset: { ...item, type: 'stock' } } });
    };

    return (
        <div className="min-h-screen bg-nexus-black pb-24 animate-fadeIn">
            {/* HERO SECTION */}
            <div className="relative overflow-hidden bg-gradient-to-b from-[#0f1115] to-nexus-black border-b border-white/5 p-6 pt-8">
                <div className="absolute top-0 right-0 w-64 h-64 bg-nexus-blue/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2"></div>

                <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-nexus-blue/10 rounded-lg border border-nexus-blue/20">
                            <Globe className="text-nexus-blue" size={24} />
                        </div>
                        <h1 className="text-3xl font-black text-white tracking-tight">
                            Global <span className="text-transparent bg-clip-text bg-gradient-to-r from-nexus-blue to-cyan-400">Stocks</span>
                        </h1>
                    </div>
                    <p className="text-nexus-subtext max-w-md">
                        Trade shares of the world's leading companies with zero commission and instant execution.
                    </p>
                </div>

                {/* SEARCH */}
                <div className="mt-8 relative max-w-xl">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-nexus-subtext" size={20} />
                    <input
                        type="text"
                        placeholder="Search companies (e.g. Apple, Tesla)..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white placeholder-nexus-subtext focus:outline-none focus:border-nexus-blue/50 focus:bg-white/10 transition-all shadow-lg backdrop-blur-sm"
                    />
                </div>
            </div>

            {/* CONTENT */}
            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <Loader className="text-nexus-blue animate-spin" size={32} />
                </div>
            ) : (
                <>
                    {/* FEATURED GRID */}
                    {!search && stocks.length > 0 && (
                        <div className="p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Zap className="text-nexus-yellow" size={16} />
                                <h2 className="text-sm font-bold text-nexus-subtext uppercase tracking-wider">Trending Now</h2>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {stocks.slice(0, 4).map(item => (
                                    <StockCard key={item.id} item={item} onClick={handleItemClick} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* MARKET LIST */}
                    <div className="px-6">
                        <div className="flex items-center gap-2 mb-4 mt-2">
                            <Activity className="text-nexus-green" size={16} />
                            <h2 className="text-sm font-bold text-nexus-subtext uppercase tracking-wider">Market Movers</h2>
                        </div>
                        <div className="bg-[#13151a] border border-white/5 rounded-2xl overflow-hidden">
                            {filteredData.length > 0 ? (
                                filteredData.map(item => (
                                    <StockRow key={item.id} item={item} onClick={handleItemClick} />
                                ))
                            ) : (
                                <div className="p-8 text-center text-nexus-subtext">
                                    {stocks.length === 0 ? "No stocks available. Check connection." : `No stocks found matching "${search}"`}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

import React, { useState, useEffect } from 'react';
import { Coins, TrendingUp, TrendingDown, Droplets, ArrowRight, BarChart3, Search, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { marketData } from '../services/marketData';

const CommodityCard = ({ item, onClick }) => {
    // Determine colors based on symbol type
    let color = 'text-zinc-300';
    let bgColor = 'bg-zinc-500/10';
    let borderColor = 'border-zinc-500/20';

    if (item.symbol.includes('XAU') || item.symbol.includes('GOLD')) {
        color = 'text-nexus-gold';
        bgColor = 'bg-nexus-gold/10';
        borderColor = 'border-nexus-gold/20';
    } else if (item.symbol.includes('OIL') || item.symbol.includes('WTI') || item.symbol.includes('BRENT')) {
        color = 'text-orange-500';
        bgColor = 'bg-orange-500/10';
        borderColor = 'border-orange-500/20';
    } else if (item.symbol.includes('GAS')) {
        color = 'text-blue-400';
        bgColor = 'bg-blue-500/10';
        borderColor = 'border-blue-500/20';
    }

    return (
        <div
            onClick={() => onClick(item)}
            className="relative overflow-hidden bg-[#13151a] border border-white/5 rounded-2xl p-6 mb-4 cursor-pointer group hover:border-white/20 transition-all"
        >
            {/* Background Glow */}
            <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-[60px] opacity-10 ${bgColor.replace('/10', '')}`}></div>

            <div className="relative z-10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl ${bgColor} ${borderColor} border flex items-center justify-center`}>
                        {item.symbol.includes('OIL') || item.symbol.includes('GAS') ? (
                            <Droplets className={color} size={24} />
                        ) : (
                            <Coins className={color} size={24} />
                        )}
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white tracking-wide">{item.symbol}</h3>
                        <p className="text-sm text-nexus-subtext">{item.name}</p>
                    </div>
                </div>

                <div className="text-right">
                    <div className="text-2xl font-mono font-medium text-white">
                        ${item.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className={`flex items-center justify-end gap-1 text-sm font-bold ${item.change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                        {item.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {Math.abs(item.change)}%
                    </div>
                </div>
            </div>

            {/* Footer / Action */}
            <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4">
                <p className="text-xs text-zinc-500">{item.description || 'Global Market Asset'}</p>
                <div className="flex items-center gap-2 text-sm font-bold text-white group-hover:text-nexus-blue transition-colors">
                    Trade Now <ArrowRight size={16} />
                </div>
            </div>
        </div>
    );
};

export const CommoditiesPage = () => {
    const navigate = useNavigate();
    const [commodities, setCommodities] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCommodities = async () => {
            try {
                const data = await marketData.getCommodities();
                setCommodities(data);
            } catch (error) {
                console.error("Failed to fetch commodities:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchCommodities();
        const interval = setInterval(fetchCommodities, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleItemClick = (item) => {
        navigate('/trade', { state: { asset: { ...item, type: 'commodity' } } });
    };

    return (
        <div className="min-h-screen bg-nexus-black pb-24 animate-fadeIn">
            {/* HERO */}
            <div className="relative bg-[#0f1115] border-b border-white/5 p-8">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-nexus-gold via-orange-500 to-nexus-black"></div>

                <h1 className="text-3xl font-black text-white mb-2 flex items-center gap-3">
                    <Coins className="text-nexus-gold" size={32} />
                    Commodities <span className="text-nexus-gold">Exchange</span>
                </h1>
                <p className="text-nexus-subtext max-w-lg">
                    Direct access to global energy and precious metal markets.
                    Trade Gold, Silver, and Oil with leverage up to 1:500.
                </p>
            </div>

            {/* CONTENT */}
            <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <BarChart3 className="text-nexus-subtext" size={18} />
                        Live Markets
                    </h2>
                    <span className="text-xs font-mono text-nexus-green animate-pulse">● MARKET OPEN</span>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader className="text-nexus-gold animate-spin" size={32} />
                    </div>
                ) : (
                    <div className="space-y-2">
                        {commodities.length > 0 ? (
                            commodities.map(item => (
                                <CommodityCard key={item.id} item={item} onClick={handleItemClick} />
                            ))
                        ) : (
                            <div className="p-8 text-center text-nexus-subtext">
                                No commodities available. Check connection.
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

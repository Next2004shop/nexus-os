import React, { useState, useEffect } from 'react';
import { Flame, ArrowUp, ArrowDown, Layers, Globe, Database } from 'lucide-react';

export const MarketOverview = () => {
    const [coins, setCoins] = useState([]);
    const [activeTab, setActiveTab] = useState('CRYPTO');

    useEffect(() => {
        const fetchMarket = async () => {
            try {
                // Fetch Top 5 Coins by Market Cap + Price Change
                const res = await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1&sparkline=false&price_change_percentage=24h');
                const data = await res.json();
                setCoins(data);
            } catch (e) {
                console.error("Failed to fetch market data", e);
            }
        };
        fetchMarket();
        const interval = setInterval(fetchMarket, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const getDisplayData = () => {
        // Only return crypto data
        return coins.map(c => ({
            id: c.id,
            symbol: c.symbol.toUpperCase(),
            name: c.name,
            price: c.current_price,
            change: c.price_change_percentage_24h,
            image: c.image
        }));
    };

    return (
        <div className="glass-panel p-6 w-full">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Flame className="text-nexus-gold" fill="currentColor" />
                    <h2 className="font-bold text-lg">Market Overview</h2>
                </div>
            </div>

            {/* TABS - Removed Stocks/Commodities */}
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                <button
                    onClick={() => setActiveTab('CRYPTO')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${activeTab === 'CRYPTO' ? 'bg-nexus-gold text-black' : 'bg-[#2b3139] text-zinc-400 hover:text-white'}`}
                >
                    <Layers size={14} /> Crypto
                </button>
            </div>

            <div className="space-y-4">
                {getDisplayData().map(asset => (
                    <div key={asset.id} className="flex justify-between items-center group cursor-pointer hover:bg-white/5 p-2 rounded-lg transition-colors">
                        <div className="flex items-center gap-3">
                            <img src={asset.image} alt={asset.name} className="w-8 h-8 rounded-full bg-white p-0.5" />
                            <div>
                                <div className="font-bold text-sm group-hover:text-nexus-gold transition-colors">{asset.symbol}</div>
                                <div className="text-xs text-zinc-500">{asset.name}</div>
                            </div>
                        </div>

                        <div className="text-right">
                            <div className="font-mono font-bold text-sm">${asset.price.toLocaleString()}</div>
                            <div className={`text-xs font-bold flex items-center justify-end gap-1 ${asset.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {asset.change >= 0 ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                                {Math.abs(asset.change).toFixed(2)}%
                            </div>
                        </div>
                    </div>
                ))}
                {activeTab === 'CRYPTO' && coins.length === 0 && <div className="text-center text-zinc-500 text-xs py-4">Loading Market Data...</div>}
            </div>
        </div>
    );
};

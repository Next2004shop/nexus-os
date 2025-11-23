import React, { useState, useEffect } from 'react';
import { Flame, ArrowUp, ArrowDown } from 'lucide-react';

export const MarketOverview = () => {
    const [coins, setCoins] = useState([]);

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

    return (
        <div className="glass-panel p-6 w-full">
            <div className="flex items-center gap-2 mb-4">
                <Flame className="text-orange-500" fill="currentColor" />
                <h2 className="font-bold text-lg">Hot List</h2>
            </div>

            <div className="space-y-4">
                {coins.map(coin => (
                    <div key={coin.id} className="flex justify-between items-center group cursor-pointer hover:bg-white/5 p-2 rounded-lg transition-colors">
                        <div className="flex items-center gap-3">
                            <span className="text-zinc-500 font-mono text-xs w-4">{coin.market_cap_rank}</span>
                            <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full" />
                            <div>
                                <div className="font-bold text-sm group-hover:text-nexus-gold transition-colors">{coin.symbol.toUpperCase()}</div>
                                <div className="text-xs text-zinc-500">{coin.name}</div>
                            </div>
                        </div>

                        <div className="text-right">
                            <div className="font-mono font-bold text-sm">${coin.current_price.toLocaleString()}</div>
                            <div className={`text-xs font-bold flex items-center justify-end gap-1 ${coin.price_change_percentage_24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {coin.price_change_percentage_24h >= 0 ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                                {Math.abs(coin.price_change_percentage_24h).toFixed(2)}%
                            </div>
                        </div>
                    </div>
                ))}
                {coins.length === 0 && <div className="text-center text-zinc-500 text-xs py-4">Loading Market Data...</div>}
            </div>
        </div>
    );
};

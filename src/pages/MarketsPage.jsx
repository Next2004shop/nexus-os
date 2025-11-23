import React, { useState } from 'react';
import { Search, Star } from 'lucide-react';

const MarketItem = ({ symbol, price, change }) => (
    <div className="flex justify-between items-center py-4 border-b border-nexus-border last:border-0">
        <div className="flex items-center gap-3">
            <Star size={16} className="text-nexus-subtext" />
            <div>
                <div className="font-bold text-nexus-text text-sm">{symbol}<span className="text-nexus-subtext text-xs">/USDT</span></div>
                <div className="text-xs text-nexus-subtext">Vol $1.2B</div>
            </div>
        </div>
        <div className="text-right flex items-center gap-4">
            <div className="text-right">
                <div className="text-nexus-text font-medium text-sm font-mono-numbers">{price}</div>
                <div className="text-nexus-subtext text-xs">≈ ${price}</div>
            </div>
            <div className={`w-20 py-2 rounded text-center text-xs font-bold text-white ${parseFloat(change) >= 0 ? 'bg-nexus-green' : 'bg-nexus-red'}`}>
                {parseFloat(change) >= 0 ? '+' : ''}{change}%
            </div>
        </div>
    </div>
);

export const MarketsPage = () => {
    const [activeTab, setActiveTab] = useState('crypto');

    return (
        <div className="bg-nexus-black min-h-screen pb-24">
            {/* SEARCH */}
            <div className="sticky top-0 bg-nexus-black z-30 px-4 py-2">
                <div className="bg-nexus-border rounded-full flex items-center px-4 py-2 gap-2">
                    <Search size={16} className="text-nexus-subtext" />
                    <input
                        type="text"
                        placeholder="Search Coin Pairs"
                        className="bg-transparent text-sm text-nexus-text outline-none w-full placeholder-nexus-subtext"
                    />
                </div>
            </div>

            {/* TABS */}
            <div className="flex gap-6 px-4 border-b border-nexus-border mt-2 overflow-x-auto no-scrollbar">
                {['Favorites', 'Crypto', 'Spot', 'Futures', 'New'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab.toLowerCase())}
                        className={`text-sm font-bold pb-3 whitespace-nowrap relative ${activeTab === tab.toLowerCase() ? 'text-nexus-text' : 'text-nexus-subtext'}`}
                    >
                        {tab}
                        {activeTab === tab.toLowerCase() && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-nexus-yellow"></div>}
                    </button>
                ))}
            </div>

            {/* LIST */}
            <div className="px-4 mt-2">
                <div className="flex justify-between text-xs text-nexus-subtext py-2">
                    <span>Name / Vol</span>
                    <span className="pr-8">Last Price</span>
                    <span>24h Chg%</span>
                </div>

                <MarketItem symbol="BTC" price="64,230.10" change="0.85" />
                <MarketItem symbol="ETH" price="3,450.55" change="-0.42" />
                <MarketItem symbol="BNB" price="593.20" change="1.24" />
                <MarketItem symbol="SOL" price="145.20" change="5.60" />
                <MarketItem symbol="XRP" price="0.62" change="0.15" />
                <MarketItem symbol="ADA" price="0.45" change="-1.20" />
                <MarketItem symbol="DOGE" price="0.16" change="2.30" />
                <MarketItem symbol="AVAX" price="35.40" change="4.10" />
                <MarketItem symbol="DOT" price="7.20" change="-0.50" />
                <MarketItem symbol="LINK" price="14.50" change="1.80" />
            </div>
        </div>
    );
};

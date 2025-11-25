import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, Star, Globe, Zap, Layers } from 'lucide-react';
import { marketData } from '../../services/marketData';

const AssetRow = ({ asset, onSelect }) => (
    <div
        onClick={() => onSelect(asset)}
        className="flex items-center justify-between p-4 hover:bg-white/5 cursor-pointer border-b border-white/5 transition-colors group"
    >
        <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-nexus-card border border-white/10 flex items-center justify-center relative overflow-hidden group-hover:border-nexus-blue/50 transition-colors">
                {asset.image ? (
                    <img src={asset.image} alt={asset.name} className="w-6 h-6 object-contain" />
                ) : (
                    <span className="text-sm font-bold text-white">{asset.symbol[0]}</span>
                )}
            </div>
            <div>
                <div className="flex items-center gap-2">
                    <span className="text-white font-bold">{asset.symbol.toUpperCase()}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-nexus-subtext border border-white/5">
                        {asset.type === 'stock' ? 'EQ' : asset.type === 'commodity' ? 'COM' : 'PERP'}
                    </span>
                </div>
                <div className="text-xs text-nexus-subtext">{asset.name}</div>
            </div>
        </div>
        <div className="text-right">
            <div className="text-white font-mono font-medium">${asset.price?.toLocaleString()}</div>
            <div className={`text-xs font-bold flex items-center justify-end gap-1 ${asset.change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                {asset.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                {Math.abs(asset.change)}%
            </div>
        </div>
    </div>
);

export const MarketSelector = ({ onSelect }) => {
    const [activeTab, setActiveTab] = useState('crypto');
    const [search, setSearch] = useState('');
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadAssets = async () => {
            setLoading(true);
            let data = [];
            if (activeTab === 'crypto') {
                const cryptos = await marketData.getTopCryptos();
                data = cryptos.map(c => ({
                    id: c.id,
                    symbol: c.symbol,
                    name: c.name,
                    price: c.current_price,
                    change: c.price_change_percentage_24h,
                    image: c.image,
                    type: 'crypto'
                }));
            } else if (activeTab === 'stocks') {
                data = marketData.getStocks();
            } else if (activeTab === 'commodities') {
                data = marketData.getCommodities();
            }
            setAssets(data);
            setLoading(false);
        };
        loadAssets();
    }, [activeTab]);

    const filteredAssets = assets.filter(a =>
        a.symbol.toLowerCase().includes(search.toLowerCase()) ||
        a.name.toLowerCase().includes(search.toLowerCase())
    );

    const tabs = [
        { id: 'crypto', label: 'Crypto', icon: Zap },
        { id: 'stocks', label: 'Stocks', icon: Globe },
        { id: 'commodities', label: 'Gold/Oil', icon: Layers },
    ];

    return (
        <div className="flex flex-col h-full bg-nexus-black animate-fadeIn">
            {/* HEADER */}
            <div className="p-6 pb-2">
                <h1 className="text-2xl font-bold text-white mb-1">Markets</h1>
                <p className="text-nexus-subtext text-sm">Select an asset to trade</p>
            </div>

            {/* SEARCH */}
            <div className="px-6 py-4">
                <div className="relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-nexus-subtext group-focus-within:text-nexus-blue transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search markets..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-nexus-card border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white placeholder-nexus-subtext focus:outline-none focus:border-nexus-blue/50 transition-all shadow-lg"
                    />
                </div>
            </div>

            {/* TABS */}
            <div className="px-6 flex gap-4 border-b border-white/5 overflow-x-auto no-scrollbar">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 pb-3 px-1 text-sm font-bold transition-colors relative ${activeTab === tab.id ? 'text-white' : 'text-nexus-subtext hover:text-white'
                            }`}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                        {activeTab === tab.id && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-nexus-blue shadow-[0_0_10px_#00F0FF]"></div>
                        )}
                    </button>
                ))}
            </div>

            {/* LIST */}
            <div className="flex-1 overflow-y-auto">
                {loading ? (
                    <div className="p-8 flex justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-nexus-blue"></div>
                    </div>
                ) : (
                    <div className="pb-20">
                        {filteredAssets.map((asset, i) => (
                            <AssetRow key={asset.id || i} asset={asset} onSelect={onSelect} />
                        ))}
                        {filteredAssets.length === 0 && (
                            <div className="p-8 text-center text-nexus-subtext">
                                No assets found.
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

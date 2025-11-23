import React, { useState } from 'react';
import { Eye, EyeOff, Search, History } from 'lucide-react';

const AssetRow = ({ symbol, name, amount, value }) => (
    <div className="flex justify-between items-center py-4 border-b border-nexus-border last:border-0">
        <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-nexus-yellow flex items-center justify-center text-nexus-black font-bold text-xs">
                {symbol[0]}
            </div>
            <div>
                <div className="font-bold text-nexus-text">{symbol}</div>
                <div className="text-xs text-nexus-subtext">{name}</div>
            </div>
        </div>
        <div className="text-right">
            <div className="font-bold text-nexus-text">{amount}</div>
            <div className="text-xs text-nexus-subtext">≈ ${value}</div>
        </div>
    </div>
);

export const WalletPage = () => {
    const [hideBalance, setHideBalance] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    return (
        <div className="bg-nexus-black min-h-screen pb-24">
            {/* HEADER */}
            <div className="bg-nexus-card pt-4 pb-6 px-4 rounded-b-3xl shadow-lg">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex gap-4">
                        {['Overview', 'Spot', 'Funding', 'Futures'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab.toLowerCase())}
                                className={`text-sm font-bold transition-colors ${activeTab === tab.toLowerCase() ? 'text-nexus-text' : 'text-nexus-subtext'}`}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                    <History size={20} className="text-nexus-subtext" />
                </div>

                <div className="mb-6">
                    <div className="flex items-center gap-2 text-nexus-subtext text-sm mb-1">
                        <span>Total Balance (USD)</span>
                        <button onClick={() => setHideBalance(!hideBalance)}>
                            {hideBalance ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                    </div>
                    <Search size={18} className="text-nexus-subtext" />
                </div>

                <div className="space-y-1">
                    <AssetRow symbol="USDT" name="Tether" amount="12,450.00" value="12,450.00" />
                    <AssetRow symbol="BTC" name="Bitcoin" amount="0.1542" value="9,850.20" />
                    <AssetRow symbol="ETH" name="Ethereum" amount="0.54" value="1,863.54" />
                    <AssetRow symbol="BNB" name="BNB" amount="0.75" value="429.68" />
                </div>
            </div>
        </div>
    );
};

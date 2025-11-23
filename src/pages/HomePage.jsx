import React, { useState } from 'react';
import { CreditCard, Grid, Gift, Users, FileText, MoreHorizontal, ArrowUpRight, ArrowDownRight, Flame, Download, Zap, Repeat, PieChart } from 'lucide-react';

const QuickAction = ({ icon: Icon, label, action, color = "text-nexus-yellow" }) => (
    <button onClick={action} className="flex flex-col items-center gap-2 min-w-[70px]">
        <div className="w-10 h-10 rounded-full bg-nexus-border flex items-center justify-center text-nexus-yellow hover:bg-nexus-gray transition-colors">
            <Icon size={20} />
        </div>
        <span className="text-[11px] text-nexus-text text-center leading-tight">{label}</span>
    </button>
);

const MarketRow = ({ symbol, price, change, isHot }) => (
    <div className="flex justify-between items-center py-3 border-b border-nexus-border last:border-0 hover:bg-nexus-border/30 px-2 -mx-2 rounded transition-colors cursor-pointer">
        <div className="flex items-center gap-2">
            {isHot && <Flame size={12} className="text-nexus-yellow" />}
            <div className="font-bold text-nexus-text text-sm">{symbol}<span className="text-nexus-subtext text-xs">/USDT</span></div>
        </div>
        <div className="text-right">
            <div className="text-nexus-text font-medium text-sm font-mono-numbers">{price}</div>
            <div className="text-nexus-subtext text-xs">≈ ${price}</div>
        </div>
        <div className={`w-20 py-1.5 rounded text-center text-xs font-bold text-white flex items-center justify-center gap-1 ${parseFloat(change) >= 0 ? 'bg-nexus-green' : 'bg-nexus-red'}`}>
            {parseFloat(change) >= 0 ? '+' : ''}{change}%
        </div>
    </div>
);

export const HomePage = ({ onNavigate }) => {
    const [activeList, setActiveList] = useState('hot');

    return (
        <div className="pb-24 bg-nexus-black min-h-screen">
            {/* BANNERS */}
            <div className="mt-2 px-4 overflow-x-auto flex gap-3 pb-2 no-scrollbar">
                <div className="min-w-[300px] h-36 rounded-xl bg-gradient-to-r from-nexus-yellow to-[#f0b90b] flex items-center p-5 relative overflow-hidden shrink-0">
                    <div className="relative z-10">
                        <h3 className="font-bold text-nexus-black text-xl">Join the 500M+</h3>
                        <p className="text-nexus-black/80 text-xs mt-1 font-medium">Trading Competition Live!</p>
                        <button className="mt-3 bg-nexus-black text-nexus-yellow px-4 py-1.5 rounded-md text-xs font-bold hover:scale-105 transition-transform">Join Now</button>
                    </div>
                    <div className="absolute right-0 bottom-0 opacity-10">
                        <Grid size={120} color="black" />
                    </div>
                </div>
                <div className="min-w-[300px] h-36 rounded-xl bg-gradient-to-r from-nexus-green to-emerald-600 flex items-center p-5 relative overflow-hidden shrink-0">
                    <div className="relative z-10">
                        <h3 className="font-bold text-white text-xl">Zero Fees</h3>
                        <p className="text-white/90 text-xs mt-1 font-medium">On First Deposit</p>
                        <button className="mt-3 bg-white text-nexus-green px-4 py-1.5 rounded-md text-xs font-bold hover:scale-105 transition-transform">Deposit</button>
                    </div>
                </div>
            </div>

            {/* QUICK ACTIONS */}
            <div className="grid grid-cols-4 gap-y-6 mt-6 px-4">
                <QuickAction icon={Download} label="Deposit" action={() => onNavigate('wallet')} />
                <QuickAction icon={Users} label="Referral" action={() => alert('Referral Program: Share your link to earn 20% commission!')} />
                <QuickAction icon={Grid} label="Grid Trading" action={() => onNavigate('trade')} />
                <QuickAction icon={PieChart} label="Earn" action={() => alert('Nexus Earn: Staking APY up to 12%')} />
                <QuickAction icon={Zap} label="Futures" action={() => onNavigate('futures')} />
                <QuickAction icon={Repeat} label="P2P" action={() => onNavigate('trade')} />
                <QuickAction icon={CreditCard} label="Buy Crypto" action={() => onNavigate('markets')} />
                <QuickAction icon={MoreHorizontal} label="More" action={() => alert('More services coming soon!')} />
            </div>

            {/* HOT LIST */}
            <div className="mt-8">
                <div className="flex gap-6 px-4 border-b border-nexus-border pb-0">
                    {['Hot', 'Gainers', 'Losers', 'New'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveList(tab.toLowerCase())}
                            className={`text-sm font-bold pb-3 relative transition-colors ${activeList === tab.toLowerCase() ? 'text-nexus-text' : 'text-nexus-subtext'}`}
                        >
                            {tab}
                            {activeList === tab.toLowerCase() && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-nexus-yellow"></div>}
                        </button>
                    ))}
                </div>
                <div className="px-4 mt-2">
                    <MarketRow symbol="BNB" price="593.20" change="1.24" isHot />
                    <MarketRow symbol="BTC" price="64,230.10" change="0.85" isHot />
                    <MarketRow symbol="ETH" price="3,450.55" change="-0.42" isHot />
                    <MarketRow symbol="SOL" price="145.20" change="5.60" isHot />
                    <MarketRow symbol="XRP" price="0.62" change="0.15" />
                    <MarketRow symbol="DOGE" price="0.16" change="2.30" />
                    <MarketRow symbol="PEPE" price="0.0000078" change="-1.20" />
                    <MarketRow symbol="SHIB" price="0.000024" change="0.50" />
                </div>
            </div>
        </div>
    );
};

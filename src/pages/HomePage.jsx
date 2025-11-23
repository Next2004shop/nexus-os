import React from 'react';
import { NewsFeed } from '../components/home/NewsFeed';
import { MarketOverview } from '../components/home/MarketOverview';
import { Wallet, ArrowRightLeft, CreditCard, ShieldCheck } from 'lucide-react';

export const HomePage = ({ onNavigate }) => {
    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 animate-fade-in pb-24 md:pb-8">
            {/* HERO SECTION */}
            <div className="flex flex-col md:flex-row gap-8 items-center justify-between">
                <div className="space-y-2">
                    <h1 className="text-4xl md:text-5xl font-black tracking-tighter">
                        TRADE <span className="text-nexus-gold">FUTURE</span>
                    </h1>
                    <p className="text-zinc-400 max-w-md">
                        The world's most advanced AI-powered trading terminal.
                        Zero latency. Maximum security.
                    </p>
                </div>

                {/* QUICK ACTIONS */}
                <div className="grid grid-cols-4 gap-4 w-full md:w-auto">
                    <button onClick={() => onNavigate('wallet')} className="flex flex-col items-center gap-2 group">
                        <div className="w-14 h-14 rounded-2xl bg-nexus-gold flex items-center justify-center text-black shadow-lg group-hover:scale-110 transition-transform">
                            <Wallet size={24} />
                        </div>
                        <span className="text-xs font-bold text-zinc-400 group-hover:text-white">Deposit</span>
                    </button>
                    <button onClick={() => onNavigate('trade')} className="flex flex-col items-center gap-2 group">
                        <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform group-hover:bg-zinc-700">
                            <ArrowRightLeft size={24} />
                        </div>
                        <span className="text-xs font-bold text-zinc-400 group-hover:text-white">Trade</span>
                    </button>
                    <button onClick={() => onNavigate('hedge')} className="flex flex-col items-center gap-2 group">
                        <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform group-hover:bg-zinc-700">
                            <CreditCard size={24} />
                        </div>
                        <span className="text-xs font-bold text-zinc-400 group-hover:text-white">Buy Crypto</span>
                    </button>
                    <button onClick={() => onNavigate('security')} className="flex flex-col items-center gap-2 group">
                        <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform group-hover:bg-zinc-700">
                            <ShieldCheck size={24} />
                        </div>
                        <span className="text-xs font-bold text-zinc-400 group-hover:text-white">Security</span>
                    </button>
                </div>
            </div>

            {/* MAIN CONTENT GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT: MARKET OVERVIEW */}
                <div className="lg:col-span-1">
                    <MarketOverview />

                    {/* BANNER */}
                    <div className="mt-6 glass-panel p-6 bg-gradient-to-br from-purple-900/50 to-blue-900/50 border-purple-500/30 relative overflow-hidden">
                        <div className="relative z-10">
                            <h3 className="font-bold text-lg mb-1">Invite Friends</h3>
                            <p className="text-xs text-zinc-300 mb-4">Earn 20% commission on every trade they make.</p>
                            <button className="bg-white text-black px-4 py-2 rounded-lg text-xs font-bold hover:bg-zinc-200 transition-colors">
                                Get Referral Link
                            </button>
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-purple-500 rounded-full blur-3xl opacity-50"></div>
                    </div>
                </div>

                {/* RIGHT: NEWS FEED */}
                <div className="lg:col-span-2">
                    <NewsFeed />
                </div>
            </div>
        </div>
    );
};

import React, { useState } from 'react';
import { Eye, EyeOff, Send, Download, RefreshCw, History, CreditCard } from 'lucide-react';

const AssetRow = ({ symbol, name, amount, value, color }) => (
    <div className="flex justify-between items-center p-4 hover:bg-white/5 rounded-xl transition-colors cursor-pointer group border border-transparent hover:border-white/5">
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-full ${color} flex items-center justify-center text-black font-bold text-sm shadow-lg`}>
                {symbol[0]}
            </div>
            <div>
                <div className="font-bold text-white text-base">{symbol}</div>
                <div className="text-xs text-nexus-subtext">{name}</div>
            </div>
        </div>
        <div className="text-right">
            <div className="font-bold text-white text-base">{amount}</div>
            <div className="text-xs text-nexus-subtext group-hover:text-nexus-blue transition-colors">≈ ${value}</div>
        </div>
    </div>
);

export const WalletPage = () => {
    const [hideBalance, setHideBalance] = useState(false);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-3xl font-bold text-white">My Assets</h1>

            {/* DIGITAL CARD */}
            <div className="relative h-56 rounded-3xl overflow-hidden shadow-2xl group transition-transform hover:scale-[1.01]">
                <div className="absolute inset-0 bg-gradient-to-br from-nexus-blue via-purple-600 to-pink-600 opacity-90"></div>
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20"></div>
                <div className="absolute -right-20 -top-20 w-64 h-64 bg-white/20 rounded-full blur-3xl"></div>

                <div className="relative z-10 p-8 flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-white/70 text-sm font-medium mb-1">Total Balance</p>
                            <div className="flex items-center gap-3">
                                <h2 className="text-4xl font-bold text-white tracking-tight">
                                    {hideBalance ? '••••••••' : '$12,450.00'}
                                </h2>
                                <button onClick={() => setHideBalance(!hideBalance)} className="text-white/70 hover:text-white transition-colors">
                                    {hideBalance ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>
                        <div className="w-12 h-12 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center">
                            <CreditCard className="text-white" size={24} />
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <button className="flex-1 bg-black/30 hover:bg-black/40 backdrop-blur-md py-3 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2 transition-all">
                            <Download size={16} /> Deposit
                        </button>
                        <button className="flex-1 bg-white/20 hover:bg-white/30 backdrop-blur-md py-3 rounded-xl text-white font-bold text-sm flex items-center justify-center gap-2 transition-all">
                            <Send size={16} /> Withdraw
                        </button>
                    </div>

                    {/* FINANCE AGENT: SMART REINVEST */}
                    <div className="mt-4 bg-black/20 p-3 rounded-xl border border-white/10 flex items-center justify-between">
                    </div>
                </div>
            </div>

            {/* ASSET LIST */}
            <div className="bg-nexus-card/50 backdrop-blur-sm border border-white/5 rounded-3xl p-6">
                <div className="flex justify-between items-center mb-6 px-2">
                    <h3 className="font-bold text-lg text-white">Crypto Assets</h3>
                    <button className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                        <History size={20} className="text-nexus-subtext" />
                    </button>
                </div>
                <div className="space-y-2">
                    <AssetRow symbol="USDT" name="Tether" amount="12,450.00" value="12,450.00" color="bg-emerald-400" />
                    <AssetRow symbol="BTC" name="Bitcoin" amount="0.1542" value="9,850.20" color="bg-orange-400" />
                    <AssetRow symbol="ETH" name="Ethereum" amount="0.54" value="1,863.54" color="bg-indigo-400" />
                    <AssetRow symbol="BNB" name="BNB" amount="0.75" value="429.68" color="bg-yellow-400" />
                </div>
            </div>
        </div>
    );
};

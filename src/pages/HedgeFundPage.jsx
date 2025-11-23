import React, { useState } from 'react';
import { Users, TrendingUp, Shield, Globe, DollarSign, PieChart } from 'lucide-react';

export const HedgeFundPage = () => {
    const [aum, setAum] = useState(1250000.00); // 1.25M Initial AUM
    const [performanceFee, setPerformanceFee] = useState(20); // 20% Standard
    const [reinvest, setReinvest] = useState(true);

    const clients = [
        { id: 1, name: "Alpha Syndicate", invested: 500000, profit: 125000, status: "Active" },
        { id: 2, name: "Venture Group A", invested: 250000, profit: 45000, status: "Active" },
        { id: 3, name: "Private Equity X", invested: 500000, profit: 89000, status: "Active" },
    ];

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto animate-fade-in">
            {/* HEADER */}
            <div className="flex flex-col md:flex-row justify-between items-end md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-black tracking-tighter text-white flex items-center gap-3">
                        <Globe className="text-amber-500" size={32} />
                        NEXUS <span className="text-amber-500">CAPITAL</span>
                    </h1>
                    <p className="text-zinc-400 mt-1">Global Hedge Fund Management System</p>
                </div>
                <div className="glass-panel px-6 py-3 rounded-xl flex items-center gap-4">
                    <div className="text-right">
                        <div className="text-xs text-zinc-500 uppercase tracking-wider font-bold">Total AUM</div>
                        <div className="text-2xl font-mono font-bold text-green-400 text-glow-blue">
                            ${aum.toLocaleString()}
                        </div>
                    </div>
                </div>
            </div>

            {/* MAIN STATS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <TrendingUp size={100} />
                    </div>
                    <div className="text-zinc-400 text-sm font-bold uppercase tracking-wider mb-2">YTD Return</div>
                    <div className="text-4xl font-black text-green-500">+42.8%</div>
                    <div className="mt-4 text-xs text-zinc-500">Outperforming S&P 500 by 31.2%</div>
                </div>

                <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <DollarSign size={100} />
                    </div>
                    <div className="text-zinc-400 text-sm font-bold uppercase tracking-wider mb-2">Est. Performance Fee</div>
                    <div className="text-4xl font-black text-amber-500">${(aum * 0.428 * 0.20).toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                    <div className="mt-4 text-xs text-zinc-500">Based on 20% carry</div>
                </div>

                <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Shield size={100} />
                    </div>
                    <div className="text-zinc-400 text-sm font-bold uppercase tracking-wider mb-2">Risk Exposure</div>
                    <div className="text-4xl font-black text-blue-500">LOW</div>
                    <div className="mt-4 text-xs text-zinc-500">Hedging Protocols Active</div>
                </div>
            </div>

            {/* CLIENT LEDGER */}
            <div className="glass-panel rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-white/5 flex justify-between items-center">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                        <Users size={20} className="text-zinc-400" />
                        Client Ledger
                    </h3>
                    <button className="bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 px-4 py-2 rounded-lg text-sm font-bold transition-colors">
                        + Add Investor
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-white/5 text-zinc-400 text-xs uppercase tracking-wider">
                            <tr>
                                <th className="p-4">Investor Name</th>
                                <th className="p-4">Principal</th>
                                <th className="p-4">Net Profit</th>
                                <th className="p-4">Status</th>
                                <th className="p-4 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {clients.map(client => (
                                <tr key={client.id} className="hover:bg-white/5 transition-colors">
                                    <td className="p-4 font-bold">{client.name}</td>
                                    <td className="p-4 font-mono text-zinc-300">${client.invested.toLocaleString()}</td>
                                    <td className="p-4 font-mono text-green-400">+${client.profit.toLocaleString()}</td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-bold">
                                            {client.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-zinc-400 hover:text-white transition-colors">Manage</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* CONTROLS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <PieChart size={18} className="text-zinc-400" />
                        Allocation Strategy
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Crypto (High Growth)</span>
                            <span className="font-bold">60%</span>
                        </div>
                        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-amber-500 w-[60%]"></div>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Forex (Liquidity)</span>
                            <span className="font-bold">30%</span>
                        </div>
                        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 w-[30%]"></div>
                        </div>

                        <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Offshore Cash</span>
                            <span className="font-bold">10%</span>
                        </div>
                        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-zinc-500 w-[10%]"></div>
                        </div>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-2xl flex flex-col justify-center">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-lg font-bold">Auto-Reinvest</h3>
                            <p className="text-xs text-zinc-500">Compound profits daily</p>
                        </div>
                        <button
                            onClick={() => setReinvest(!reinvest)}
                            className={`w-14 h-8 rounded-full p-1 transition-colors ${reinvest ? 'bg-green-500' : 'bg-zinc-700'}`}
                        >
                            <div className={`w-6 h-6 bg-white rounded-full shadow-lg transform transition-transform ${reinvest ? 'translate-x-6' : 'translate-x-0'}`}></div>
                        </button>
                    </div>
                    <button className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 font-bold text-black hover:shadow-[0_0_20px_rgba(245,158,11,0.4)] transition-all">
                        GENERATE REPORT
                    </button>
                </div>
            </div>
        </div>
    );
};

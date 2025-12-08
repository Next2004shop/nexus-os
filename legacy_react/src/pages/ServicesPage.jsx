import React, { useState } from 'react';
import { Users, UserPlus, TrendingUp, Shield, FileText, Search, Briefcase } from 'lucide-react';

export const ServicesPage = () => {
    const [clients] = useState([
        { id: 1, name: 'Sarah Connor', plan: 'Platinum Growth', invested: 150000, profit: 45000, status: 'Active', nextPayout: 'Dec 15' },
        { id: 2, name: 'John Wick', plan: 'Gold Secure', invested: 500000, profit: 120000, status: 'Active', nextPayout: 'Dec 20' },
        { id: 3, name: 'Bruce Wayne', plan: 'Institutional', invested: 5000000, profit: 850000, status: 'Active', nextPayout: 'Jan 01' },
    ]);

    const [showAddForm, setShowAddForm] = useState(false);

    return (
        <div className="p-6 space-y-6 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Client Services</h1>
                    <p className="text-nexus-subtext">Manage Reinvestments & Service Delivery</p>
                </div>
                <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="btn-primary flex items-center gap-2"
                >
                    <UserPlus size={18} />
                    ADD NEW CLIENT
                </button>
            </div>

            {/* ADD CLIENT FORM */}
            {showAddForm && (
                <div className="bg-card border border-nexus-accent/30 p-6 rounded-xl animate-slide-up">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Briefcase size={20} className="text-nexus-accent" /> Onboard New Client
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-nexus-subtext mb-1">Full Name</label>
                            <input type="text" className="input-premium w-full" placeholder="e.g. Tony Stark" />
                        </div>
                        <div>
                            <label className="block text-xs text-nexus-subtext mb-1">Investment Plan</label>
                            <select className="input-premium w-full">
                                <option>Silver Starter ($10k - $50k)</option>
                                <option>Gold Secure ($50k - $250k)</option>
                                <option>Platinum Growth ($250k+)</option>
                                <option>Institutional (Custom)</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-nexus-subtext mb-1">Initial Capital</label>
                            <input type="number" className="input-premium w-full" placeholder="0.00" />
                        </div>
                        <div>
                            <label className="block text-xs text-nexus-subtext mb-1">Reinvestment Strategy</label>
                            <select className="input-premium w-full">
                                <option>100% Reinvest (Compound)</option>
                                <option>50% Payout / 50% Reinvest</option>
                                <option>Monthly Payout</option>
                            </select>
                        </div>
                    </div>
                    <div className="mt-6 flex justify-end gap-3">
                        <button onClick={() => setShowAddForm(false)} className="btn-secondary">CANCEL</button>
                        <button className="btn-primary">CONFIRM ONBOARDING</button>
                    </div>
                </div>
            )}

            {/* CLIENT LIST */}
            <div className="bg-card border border-white/5 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-white/5 flex justify-between items-center">
                    <h3 className="font-bold text-white flex items-center gap-2">
                        <Users size={18} className="text-nexus-subtext" /> Active Portfolios
                    </h3>
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-3 text-nexus-subtext" />
                        <input
                            type="text"
                            placeholder="Search clients..."
                            className="bg-nexus-black border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:border-nexus-accent outline-none"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-xs text-nexus-subtext border-b border-white/5">
                                <th className="p-4 font-medium">CLIENT NAME</th>
                                <th className="p-4 font-medium">PLAN</th>
                                <th className="p-4 font-medium text-right">INVESTED</th>
                                <th className="p-4 font-medium text-right">PROFIT (YTD)</th>
                                <th className="p-4 font-medium text-center">STATUS</th>
                                <th className="p-4 font-medium text-right">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {clients.map(client => (
                                <tr key={client.id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                                    <td className="p-4">
                                        <div className="font-bold text-white">{client.name}</div>
                                        <div className="text-xs text-nexus-subtext">Next Payout: {client.nextPayout}</div>
                                    </td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 bg-nexus-accent/10 text-nexus-accent rounded text-xs font-bold border border-nexus-accent/20">
                                            {client.plan}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right font-mono text-white">${client.invested.toLocaleString()}</td>
                                    <td className="p-4 text-right font-mono text-nexus-green">+${client.profit.toLocaleString()}</td>
                                    <td className="p-4 text-center">
                                        <span className="flex items-center justify-center gap-1 text-xs text-nexus-green font-bold">
                                            <Shield size={12} /> {client.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-nexus-subtext hover:text-white transition-colors p-2">
                                            <FileText size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

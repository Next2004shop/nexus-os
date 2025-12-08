import React, { useState } from 'react';
import { Landmark, Eye, EyeOff, FileText, Download, Lock, ShieldCheck, PieChart } from 'lucide-react';

export default function BankingPage() {
    const [bankMode, setBankMode] = useState(false);

    // Data that changes based on Bank Mode
    const financialData = {
        totalAssets: bankMode ? 1500000.00 : 12450000.00, // Hide crypto/offshore in Bank Mode
        liabilities: 25000.00,
        monthlyRevenue: bankMode ? 45000.00 : 185000.00, // Show only "clean" revenue
        netIncome: bankMode ? 32000.00 : 145000.00
    };

    return (
        <div className="p-6 space-y-6 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Landmark className="text-nexus-yellow" /> Corporate Banking
                    </h1>
                    <p className="text-nexus-subtext">Official Book of Accounts & Statements</p>
                </div>

                {/* BANK MODE TOGGLE */}
                <button
                    onClick={() => setBankMode(!bankMode)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all font-bold ${bankMode
                            ? 'bg-white text-black border-white hover:bg-gray-200'
                            : 'bg-nexus-black text-nexus-subtext border-white/10 hover:text-white'
                        }`}
                >
                    {bankMode ? <Eye size={18} /> : <EyeOff size={18} />}
                    {bankMode ? 'BANK MODE: ON' : 'BANK MODE: OFF'}
                </button>
            </div>

            {bankMode && (
                <div className="bg-white/10 border border-white/20 p-4 rounded-xl flex items-center gap-3 animate-fadeIn">
                    <ShieldCheck size={24} className="text-white" />
                    <div>
                        <h3 className="font-bold text-white">Sanitized View Active</h3>
                        <p className="text-xs text-white/70">
                            Displaying only verified, tax-compliant income sources. Crypto wallets and offshore assets are hidden.
                            Safe for loan applications and bank audits.
                        </p>
                    </div>
                </div>
            )}

            {/* FINANCIAL OVERVIEW */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold">Total Assets</h3>
                    <p className="text-2xl font-mono text-white mt-2">${financialData.totalAssets.toLocaleString()}</p>
                </div>
                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold">Liabilities</h3>
                    <p className="text-2xl font-mono text-nexus-red mt-2">${financialData.liabilities.toLocaleString()}</p>
                </div>
                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold">Monthly Revenue</h3>
                    <p className="text-2xl font-mono text-nexus-green mt-2">+${financialData.monthlyRevenue.toLocaleString()}</p>
                </div>
                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold">Net Income</h3>
                    <p className="text-2xl font-mono text-white mt-2">${financialData.netIncome.toLocaleString()}</p>
                </div>
            </div>

            {/* STATEMENTS VAULT */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card border border-white/5 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FileText size={20} className="text-nexus-accent" /> Financial Statements
                    </h3>
                    <div className="space-y-3">
                        {['Balance Sheet (Nov 2025)', 'Profit & Loss (Q3 2025)', 'Cash Flow Statement', 'Tax Returns (2024)'].map((doc, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors cursor-pointer group">
                                <div className="flex items-center gap-3">
                                    <FileText size={18} className="text-nexus-subtext group-hover:text-white" />
                                    <span className="text-sm text-nexus-subtext group-hover:text-white">{doc}</span>
                                </div>
                                <Download size={16} className="text-nexus-subtext group-hover:text-nexus-accent" />
                            </div>
                        ))}
                    </div>
                    <button className="w-full mt-6 btn-secondary flex items-center justify-center gap-2">
                        GENERATE NEW REPORT
                    </button>
                </div>

                <div className="bg-card border border-white/5 rounded-xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6 opacity-5">
                        <Lock size={120} />
                    </div>
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Lock size={20} className="text-nexus-yellow" /> Secure Vault
                    </h3>
                    <p className="text-sm text-nexus-subtext mb-6">
                        Encrypted storage for sensitive documents. Access requires biometric authentication (Level 10).
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-nexus-black border border-nexus-yellow/20 rounded-lg flex flex-col items-center justify-center gap-2 hover:border-nexus-yellow/50 transition-colors cursor-pointer">
                            <Lock size={24} className="text-nexus-yellow" />
                            <span className="text-xs font-bold text-nexus-yellow">PRIVATE KEYS</span>
                        </div>
                        <div className="p-4 bg-nexus-black border border-nexus-yellow/20 rounded-lg flex flex-col items-center justify-center gap-2 hover:border-nexus-yellow/50 transition-colors cursor-pointer">
                            <FileText size={24} className="text-nexus-yellow" />
                            <span className="text-xs font-bold text-nexus-yellow">DEEDS & TITLES</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

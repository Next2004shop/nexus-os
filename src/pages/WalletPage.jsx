import React, { useState } from 'react';
import { Wallet, ArrowUpRight, ArrowDownLeft, CreditCard, Building, Shield, PieChart, Activity } from 'lucide-react';

export const WalletPage = () => {
    const [activeTab, setActiveTab] = useState('deposit');
    const [balance, setBalance] = useState({
        total: 12450000.00,
        crypto: 8500000.00,
        stocks: 3200000.00,
        cash: 750000.00
    });

    return (
        <div className="p-6 space-y-6 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Hedge Fund Wallet</h1>
                    <p className="text-nexus-subtext">Global Asset Management & Transfers</p>
                </div>
                <div className="bg-nexus-green/10 px-4 py-2 rounded-lg border border-nexus-green/20">
                    <span className="text-nexus-green font-mono font-bold">STATUS: VERIFIED (LEVEL 10)</span>
                </div>
            </div>

            {/* MAIN DASHBOARD CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* TOTAL EQUITY */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <PieChart size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Total Equity (AUM)</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.total.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-green text-sm">
                        <Activity size={16} className="mr-1" />
                        <span>+12.5% this month</span>
                    </div>
                </div>

                {/* LIQUID CASH */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Building size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Liquid Capital</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.cash.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-subtext text-sm">
                        <Shield size={16} className="mr-1" />
                        <span>Insured & Protected</span>
                    </div>
                </div>

                {/* CRYPTO ASSETS */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Wallet size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Digital Assets</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.crypto.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-yellow text-sm">
                        <ArrowUpRight size={16} className="mr-1" />
                        <span>High Yield Staking Active</span>
                    </div>
                </div>
            </div>

            {/* ACTION AREA */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* DEPOSIT / WITHDRAW FORM */}
                <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
                    <div className="flex border-b border-white/5">
                        <button
                            onClick={() => setActiveTab('deposit')}
                            className={`flex-1 py-4 text-sm font-bold transition-colors ${activeTab === 'deposit'
                                    ? 'bg-nexus-green/10 text-nexus-green border-b-2 border-nexus-green'
                                    : 'text-nexus-subtext hover:text-white'
                                }`}
                        >
                            <div className="flex items-center justify-center gap-2">
                                <ArrowDownLeft size={18} />
                                DEPOSIT FUNDS
                            </div>
                        </button>
                        <button
                            onClick={() => setActiveTab('withdraw')}
                            className={`flex-1 py-4 text-sm font-bold transition-colors ${activeTab === 'withdraw'
                                    ? 'bg-nexus-red/10 text-nexus-red border-b-2 border-nexus-red'
                                    : 'text-nexus-subtext hover:text-white'
                                }`}
                        >
                            <div className="flex items-center justify-center gap-2">
                                <ArrowUpRight size={18} />
                                WITHDRAW FUNDS
                            </div>
                        </button>
                    </div>

                    <div className="p-6">
                        {activeTab === 'deposit' ? (
                            <div className="space-y-4 animate-fadeIn">
                                <div className="bg-nexus-green/5 border border-nexus-green/20 p-4 rounded-lg mb-6">
                                    <h4 className="text-nexus-green font-bold flex items-center gap-2">
                                        <Shield size={16} /> Secure Deposit Gateway
                                    </h4>
                                    <p className="text-xs text-nexus-subtext mt-1">
                                        Supports Wire Transfer, ACH, Crypto, and Institutional Transfers.
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Select Asset</label>
                                    <select className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-green">
                                        <option>USD - United States Dollar</option>
                                        <option>EUR - Euro</option>
                                        <option>BTC - Bitcoin</option>
                                        <option>USDT - Tether (TRC20)</option>
                                        <option>XAU - Gold Bullion</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Amount</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-3 text-nexus-subtext">$</span>
                                        <input
                                            type="number"
                                            placeholder="0.00"
                                            className="w-full bg-nexus-black border border-white/10 rounded p-3 pl-8 text-white outline-none focus:border-nexus-green font-mono text-lg"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Source / Method</label>
                                    <select className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-green">
                                        <option>Bank Wire (Chase JP Morgan)</option>
                                        <option>Crypto Wallet (Connect Web3)</option>
                                        <option>Credit Card (Visa Infinite)</option>
                                    </select>
                                </div>

                                <button className="w-full bg-nexus-green text-black font-bold py-4 rounded-lg hover:bg-green-400 transition-colors mt-4 flex items-center justify-center gap-2">
                                    <ArrowDownLeft size={20} />
                                    INITIATE DEPOSIT
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-4 animate-fadeIn">
                                <div className="bg-nexus-red/5 border border-nexus-red/20 p-4 rounded-lg mb-6">
                                    <h4 className="text-nexus-red font-bold flex items-center gap-2">
                                        <Activity size={16} /> High-Value Withdrawal
                                    </h4>
                                    <p className="text-xs text-nexus-subtext mt-1">
                                        Unlimited withdrawals enabled. Processing time: Instant - 24h.
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Withdraw From</label>
                                    <select className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-red">
                                        <option>Liquid Cash ($750,000.00)</option>
                                        <option>Crypto Vault ($8,500,000.00)</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Amount</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-3 text-nexus-subtext">$</span>
                                        <input
                                            type="number"
                                            placeholder="0.00"
                                            className="w-full bg-nexus-black border border-white/10 rounded p-3 pl-8 text-white outline-none focus:border-nexus-red font-mono text-lg"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Destination</label>
                                    <input
                                        type="text"
                                        placeholder="Bank Account / Wallet Address"
                                        className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-red"
                                    />
                                </div>

                                <button className="w-full bg-nexus-red text-white font-bold py-4 rounded-lg hover:bg-red-600 transition-colors mt-4 flex items-center justify-center gap-2">
                                    <ArrowUpRight size={20} />
                                    PROCESS WITHDRAWAL
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* RECENT TRANSACTIONS */}
                <div className="bg-card rounded-xl border border-white/5 p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Recent Institutional Transfers</h3>
                    <div className="space-y-4">
                        {[
                            { type: 'Deposit', asset: 'USDT', amount: '+50,000.00', status: 'Completed', date: 'Today, 10:42 AM' },
                            { type: 'Withdrawal', asset: 'USD', amount: '-12,500.00', status: 'Processing', date: 'Yesterday, 4:15 PM' },
                            { type: 'Deposit', asset: 'BTC', amount: '+2.5000', status: 'Completed', date: 'Dec 01, 09:30 AM' },
                            { type: 'Trade Profit', asset: 'XAUUSD', amount: '+8,240.50', status: 'Credited', date: 'Dec 01, 02:15 AM' },
                            { type: 'Dividend', asset: 'TSLA', amount: '+1,200.00', status: 'Credited', date: 'Nov 30, 11:00 PM' },
                        ].map((tx, i) => (
                            <div key={i} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors cursor-pointer group">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type.includes('Deposit') || tx.type.includes('Profit') || tx.type.includes('Dividend')
                                            ? 'bg-nexus-green/10 text-nexus-green'
                                            : 'bg-nexus-red/10 text-nexus-red'
                                        }`}>
                                        {tx.type.includes('Deposit') || tx.type.includes('Profit') || tx.type.includes('Dividend') ? <ArrowDownLeft size={18} /> : <ArrowUpRight size={18} />}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-white">{tx.type} ({tx.asset})</p>
                                        <p className="text-xs text-nexus-subtext">{tx.date}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className={`font-mono font-bold ${tx.type.includes('Deposit') || tx.type.includes('Profit') || tx.type.includes('Dividend')
                                            ? 'text-nexus-green'
                                            : 'text-white'
                                        }`}>
                                        {tx.amount}
                                    </p>
                                    <p className="text-xs text-nexus-subtext group-hover:text-nexus-yellow transition-colors">{tx.status}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button className="w-full mt-6 py-3 text-sm text-nexus-subtext hover:text-white border border-white/10 rounded hover:bg-white/5 transition-colors">
                        View All Transactions
                    </button>
                </div>
            </div>
        </div>
    );
};

import React, { useState } from 'react';
import { Building, CreditCard, Globe, Shield, ArrowRight, Plus } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { userRepository } from '../services/userRepository';
import { useAuth } from '../context/AuthContext';

const BankingPage = () => {
    const [showAddAccount, setShowAddAccount] = useState(false);
    const { showToast } = useToast();
    const { currentUser } = useAuth();

    const handleAddAccount = () => {
        showToast("Connecting to SWIFT network...", "info");
        setTimeout(() => {
            showToast("Offshore Account Linked Successfully", "success");
            setShowAddAccount(false);
        }, 2000);
    };

    return (
        <div className="p-6 animate-fadeIn pb-24 md:pb-6">
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-1">Offshore Banking</h1>
                    <p className="text-nexus-subtext text-sm">Manage international liquidity and assets.</p>
                </div>
                <button
                    onClick={() => setShowAddAccount(true)}
                    className="bg-nexus-blue/10 text-nexus-blue px-4 py-2 rounded-lg text-sm font-bold hover:bg-nexus-blue/20 transition-colors flex items-center gap-2"
                >
                    <Plus size={16} /> Link Account
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* MAIN ACCOUNT CARD */}
                <div className="bg-gradient-to-br from-[#0f172a] to-[#1e293b] border border-white/10 rounded-2xl p-8 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Globe size={120} />
                    </div>
                    <div className="relative z-10">
                        <div className="flex justify-between items-start mb-8">
                            <div className="flex items-center gap-2">
                                <Shield className="text-nexus-green" size={20} />
                                <span className="text-nexus-green font-bold text-xs tracking-wider">ENCRYPTED & INSURED</span>
                            </div>
                            <img src="/logo.jpg" className="w-8 h-8 rounded-full opacity-50" alt="Logo" />
                        </div>
                        <div className="mb-8">
                            <div className="text-nexus-subtext text-sm mb-1">Total Liquidity (USD)</div>
                            <div className="text-4xl font-bold text-white font-mono">$124,592.00</div>
                        </div>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <div className="text-[10px] text-nexus-subtext uppercase font-bold">Account Holder</div>
                                <div className="text-white font-medium">{currentUser?.displayName || 'Commander'}</div>
                            </div>
                            <div className="flex-1">
                                <div className="text-[10px] text-nexus-subtext uppercase font-bold">IBAN</div>
                                <div className="text-white font-mono text-sm">CH89 0076 2099 8812</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ACTIONS */}
                <div className="space-y-4">
                    {/* MPESA */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-xl hover:border-nexus-green/50 transition-all cursor-pointer group" onClick={() => showToast("MPESA Paybill: 247247 (Enter Account No)", "info")}>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-green-500/10 rounded-full flex items-center justify-center text-green-500 group-hover:scale-110 transition-transform">
                                <Building size={24} />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-white font-bold">MPESA Mobile Money</h3>
                                <p className="text-nexus-subtext text-xs">Instant Deposit via Paybill 247247</p>
                            </div>
                            <ArrowRight size={20} className="text-nexus-subtext group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                    </div>

                    {/* PAYPAL */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-xl hover:border-blue-500/50 transition-all cursor-pointer group" onClick={() => showToast("Redirecting to PayPal Secure Gateway...", "info")}>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center text-blue-500 group-hover:scale-110 transition-transform">
                                <Globe size={24} />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-white font-bold">PayPal</h3>
                                <p className="text-nexus-subtext text-xs">Link account for international transfers</p>
                            </div>
                            <ArrowRight size={20} className="text-nexus-subtext group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                    </div>

                    {/* BINANCE / CRYPTO */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-xl hover:border-yellow-500/50 transition-all cursor-pointer group" onClick={() => showToast("Binance Connect: Address Copied", "success")}>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center text-yellow-500 group-hover:scale-110 transition-transform">
                                <CreditCard size={24} />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-white font-bold">Binance / Crypto</h3>
                                <p className="text-nexus-subtext text-xs">Deposit USDT, BTC, ETH (TRC20/ERC20)</p>
                            </div>
                            <ArrowRight size={20} className="text-nexus-subtext group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BankingPage;

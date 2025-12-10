"use client";
import { Card } from "@/components/ui/Card";
import { TrendingUp, Plus, ArrowUpRight, ArrowDownLeft, ShoppingCart, DollarSign } from "lucide-react";

export default function WalletPage() {
    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Wallet</h1>
                <p className="text-nexus-subtext">Manage your assets and portfolio</p>
            </div>

            {/* Total Balance */}
            <Card className="p-8 mb-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-nexus-green/5 rounded-full blur-3xl" />
                <div className="relative z-10">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <div className="text-nexus-subtext uppercase text-xs font-bold mb-3">Total Balance</div>
                            <div className="font-mono text-white text-5xl font-bold mb-4">$124,592.40</div>
                            <div className="text-nexus-green flex items-center gap-2">
                                <TrendingUp size={20} />
                                +$2,490.10 (2.1%) Today
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button className="flex items-center gap-2 px-6 py-3 bg-nexus-green text-black font-bold rounded-xl hover:bg-green-400 transition-colors shadow-lg">
                                <Plus size={18} /> Deposit
                            </button>
                            <button className="flex items-center gap-2 px-6 py-3 bg-white/10 text-white font-bold rounded-xl hover:bg-white/20 transition-colors">
                                <ArrowUpRight size={18} /> Withdraw
                            </button>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 pt-6 border-t border-white/10">
                        <div>
                            <div className="text-nexus-subtext text-xs mb-1">Available</div>
                            <div className="text-xl font-bold font-mono">$98,234.50</div>
                        </div>
                        <div>
                            <div className="text-nexus-subtext text-xs mb-1">In Orders</div>
                            <div className="text-xl font-bold font-mono text-nexus-yellow">$26,357.90</div>
                        </div>
                        <div>
                            <div className="text-nexus-subtext text-xs mb-1">Total P&L</div>
                            <div className="text-xl font-bold font-mono text-nexus-green">+$12,450.20</div>
                        </div>
                    </div>
                </div>
            </Card>

            <h2 className="text-xl font-bold mb-4">Assets</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                {[
                    { sym: 'USDT', name: 'Tether', bal: '45,000.00', val: '$45,000.00', chg: '+0.01%', type: 'stable' },
                    { sym: 'BTC', name: 'Bitcoin', bal: '1.24', val: '$121,700.00', chg: '+2.5%', type: 'crypto' },
                    { sym: 'ETH', name: 'Ethereum', bal: '14.5', val: '$28,450.00', chg: '+1.8%', type: 'crypto' },
                    { sym: 'EUR', name: 'Euro', bal: '25,000.00', val: '$26,250.00', chg: '+0.5%', type: 'forex' },
                    { sym: 'AAPL', name: 'Apple Stock', bal: '120.00', val: '$26,460.00', chg: '+0.8%', type: 'stock' },
                    { sym: 'GOLD', name: 'Gold (oz)', bal: '10.5', val: '$24,780.00', chg: '+1.2%', type: 'commo' },
                ].map((asset, i) => (
                    <Card key={i} className="p-5 hover:scale-[1.02] transition-transform cursor-pointer group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center font-bold text-lg border border-white/20">
                                    {asset.sym[0]}
                                </div>
                                <div>
                                    <div className="font-bold text-lg">{asset.sym}</div>
                                    <div className="text-nexus-subtext text-xs">{asset.name}</div>
                                </div>
                            </div>
                            <span className="px-2 py-1 rounded-md text-xs font-bold uppercase bg-white/10 text-nexus-subtext">{asset.type}</span>
                        </div>
                        <div className="mb-3">
                            <div className="text-nexus-subtext text-xs mb-1">Holdings</div>
                            <div className="font-mono text-2xl font-bold">{asset.bal}</div>
                        </div>
                        <div className="flex justify-between items-center pt-3 border-t border-white/10">
                            <div>
                                <div className="text-nexus-subtext text-xs">Value</div>
                                <div className="font-mono font-bold">{asset.val}</div>
                            </div>
                            <div className="text-nexus-green flex items-center gap-1 text-sm font-bold">
                                <TrendingUp size={16} />
                                {asset.chg}
                            </div>
                        </div>
                    </Card>
                ))}
            </div>

            <h3 className="text-lg font-bold mb-4">Recent Transactions</h3>
            <div className="space-y-3">
                {[
                    { type: 'Deposit', asset: 'USDT', amt: '+5,000.00', time: '2 hours ago', icon: ArrowDownLeft, color: 'text-nexus-green' },
                    { type: 'Buy', asset: 'BTC', amt: '-0.05', time: '5 hours ago', icon: ShoppingCart, color: 'text-nexus-blue' },
                    { type: 'Sell', asset: 'ETH', amt: '+2.5', time: '1 day ago', icon: DollarSign, color: 'text-nexus-green' },
                    { type: 'Withdrawal', asset: 'USD', amt: '-10,000.00', time: '2 days ago', icon: ArrowUpRight, color: 'text-nexus-red' },
                ].map((tx, i) => (
                    <div key={i} className="flex justify-between items-center p-4 bg-black/20 rounded-xl border border-white/5 hover:bg-black/30 transition-all">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                                <tx.icon className={`w-5 h-5 ${tx.color}`} />
                            </div>
                            <div>
                                <div className="font-bold">{tx.type}</div>
                                <div className="text-nexus-subtext text-xs">{tx.time}</div>
                            </div>
                        </div>
                        <div className={`font-mono font-bold ${tx.color}`}>{tx.amt} {tx.asset}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

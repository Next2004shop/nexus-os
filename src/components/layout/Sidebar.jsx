import React from 'react';
import { Terminal, Wallet, Server, PieChart } from 'lucide-react';

export const Sidebar = ({ activeTab, onTabChange }) => {
    const navItems = [
        { id: 'trade', icon: Terminal },
        { id: 'wallet', icon: Wallet },
        { id: 'brokers', icon: Server },
        { id: 'tax', icon: PieChart }
    ];

    return (
        <div className="hidden md:flex w-20 border-r border-white/5 flex-col items-center py-8 bg-zinc-950/50 z-50 h-full">
            <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center text-black font-black mb-8 shadow-[0_0_15px_rgba(245,158,11,0.3)]">N</div>
            <div className="space-y-6 flex-1">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={`p-3 rounded-xl transition-all duration-300 relative group ${activeTab === item.id ? 'bg-white/10 text-amber-500' : 'text-zinc-600 hover:text-zinc-300'}`}
                    >
                        <item.icon size={24} />
                        {activeTab === item.id && (
                            <div className="absolute inset-0 rounded-xl ring-1 ring-amber-500/50 shadow-[0_0_10px_rgba(245,158,11,0.2)]"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

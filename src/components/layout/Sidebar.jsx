import React from 'react';
import { Terminal, Wallet, Server, PieChart, Globe, Shield, Home, Bot } from 'lucide-react';
import logo from '../../assets/logo.png';

export const Sidebar = ({ activeTab, onTabChange }) => {
    const navItems = [
        { id: 'home', icon: Home },
        { id: 'ai-bot', icon: Bot }, // AI Core
        { id: 'trade', icon: Terminal },
        { id: 'wallet', icon: Wallet },
        { id: 'hedge', icon: Globe },
        { id: 'security', icon: Shield },
        { id: 'brokers', icon: Server },
        { id: 'tax', icon: PieChart }
    ];

    return (
        <div className="hidden md:flex w-20 border-r border-[#2b3139] flex-col items-center py-6 bg-[#181a20] z-50 h-full">
            <div className="w-10 h-10 mb-8 rounded-full overflow-hidden border-2 border-nexus-gold shadow-[0_0_15px_rgba(252,213,53,0.3)]">
                <img src={logo} alt="Nexus" className="w-full h-full object-cover" />
            </div>
            <div className="space-y-6 flex-1">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={`p-3 rounded-xl transition-all duration-300 relative group ${activeTab === item.id ? 'bg-[#2b3139] text-nexus-gold' : 'text-zinc-500 hover:text-zinc-300'}`}
                    >
                        <item.icon size={24} />
                        {activeTab === item.id && (
                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-nexus-gold rounded-r-full"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

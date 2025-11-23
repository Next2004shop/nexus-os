import React from 'react';
import { Activity, Wallet, Server, PieChart, Globe, Shield, Home } from 'lucide-react';

export const MobileNav = ({ activeTab, onTabChange }) => {
    const navItems = [
        { id: 'home', icon: Home, label: 'Home' },
        { id: 'trade', icon: Activity, label: 'Trade' },
        { id: 'wallet', icon: Wallet, label: 'Wallet' },
        { id: 'hedge', icon: Globe, label: 'Hedge' },
        { id: 'security', icon: Shield, label: 'Security' },
        { id: 'brokers', icon: Server, label: 'Brokers' },
        { id: 'tax', icon: PieChart, label: 'Tax' }
    ];

    return (
        <div className="md:hidden fixed bottom-0 left-0 right-0 h-[80px] bg-[#181a20] border-t border-[#2b3139] flex justify-around items-center pb-4 z-50">
            {navItems.map(item => (
                <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    className={`flex flex-col items-center gap-1 p-2 transition-colors ${activeTab === item.id ? 'text-nexus-gold' : 'text-zinc-500'}`}
                >
                    <item.icon size={22} />
                    <span className="text-[10px] font-medium">{item.label}</span>
                </button>
            ))}
        </div>
    );
};

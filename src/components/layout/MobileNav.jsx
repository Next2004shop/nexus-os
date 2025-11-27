import React from 'react';
import { Home, Terminal, Wallet, Globe, Shield, Layers, Bot } from 'lucide-react';

export const MobileNav = ({ activeTab, onTabChange }) => {
    const navItems = [
        { id: 'home', icon: Home, label: 'Home' },
        { id: 'stocks', icon: Globe, label: 'Stocks' },
        { id: 'ai-bot', icon: Bot, label: 'AI Core' }, // New Central AI Button
        { id: 'trade', icon: Terminal, label: 'Trade' },
        { id: 'wallet', icon: Wallet, label: 'Wallet' }
    ];

    return (
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#181a20]/90 backdrop-blur-lg border-t border-[#2b3139] z-50 pb-safe">
            <div className="flex justify-around items-center px-2 py-3">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => onTabChange(item.id)}
                        className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-colors ${activeTab === item.id
                            ? 'text-nexus-gold'
                            : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                    >
                        <item.icon size={20} />
                        <span className="text-[10px] font-medium uppercase tracking-wide">
                            {item.label}
                        </span>
                        {activeTab === item.id && (
                            <div className="absolute bottom-0 w-8 h-0.5 bg-nexus-gold rounded-t-full shadow-[0_0_8px_rgba(252,213,53,0.5)]"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

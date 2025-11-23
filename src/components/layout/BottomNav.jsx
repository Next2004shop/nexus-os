import React from 'react';
import { Home, BarChart2, Repeat, Briefcase, Wallet, Newspaper } from 'lucide-react';

export function BottomNav({ activeTab, onTabChange }) {
    const navItems = [
        { id: 'home', label: 'Home', icon: Home },
        { id: 'markets', label: 'Markets', icon: BarChart2 },
        { id: 'trade', label: 'Trade', icon: Repeat },
        { id: 'futures', label: 'Futures', icon: Briefcase },
        { id: 'news', label: 'News', icon: Newspaper },
        { id: 'wallet', label: 'Wallets', icon: Wallet },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-nexus-black border-t border-nexus-border pb-safe z-50">
            <div className="flex justify-between items-center px-2 h-16">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;

                    return (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors duration-200 ${isActive ? 'text-nexus-text' : 'text-nexus-subtext'
                                }`}
                        >
                            <Icon
                                size={24}
                                className={isActive ? 'text-nexus-yellow fill-nexus-yellow' : ''}
                                strokeWidth={isActive ? 2.5 : 2}
                            />
                            <span className={`text-[10px] font-medium ${isActive ? 'text-nexus-text' : 'text-nexus-subtext'}`}>
                                {item.label}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

import React from 'react';
import { Home, Terminal, Wallet, Globe, Shield, Layers, Bot, Download } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

export const MobileNav = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const navItems = [
        { id: 'trade', path: '/trade', icon: Terminal, label: 'Trade' },
        { id: 'stocks', path: '/stocks', icon: Globe, label: 'Stocks' },
        { id: 'ai-bot', path: '/ai-bot', icon: Bot, label: 'AI Core' },
        { id: 'wallet', path: '/wallet', icon: Wallet, label: 'Wallet' },
        { id: 'downloads', path: '/downloads', icon: Download, label: 'Get App' },
        { id: 'profile', path: '/profile', icon: Layers, label: 'Menu' }
    ];

    return (
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#181a20]/90 backdrop-blur-lg border-t border-[#2b3139] z-50 pb-safe">
            <div className="flex justify-around items-center px-2 py-3">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => navigate(item.path)}
                        className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-colors ${location.pathname === item.path
                            ? 'text-nexus-gold'
                            : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                    >
                        <item.icon size={20} />
                        <span className="text-[10px] font-medium uppercase tracking-wide">
                            {item.label}
                        </span>
                        {location.pathname === item.path && (
                            <div className="absolute bottom-0 w-8 h-0.5 bg-nexus-gold rounded-t-full shadow-[0_0_8px_rgba(252,213,53,0.5)]"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

import React from 'react';
import { Terminal, Wallet, Server, PieChart, Globe, Shield, Home, Bot } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import logo from '../../assets/logo.png';

export const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const activeTab = location.pathname.substring(1) || 'home';

    const navItems = [
        { id: 'trade', path: '/trade', icon: Terminal },
        { id: 'stocks', path: '/stocks', icon: Globe },
        { id: 'ai-bot', path: '/ai-bot', icon: Bot },
        { id: 'wallet', path: '/wallet', icon: Wallet },
        { id: 'banking', path: '/banking', icon: Server }, // Using Server icon for Banking for now
        { id: 'security', path: '/security', icon: Shield },
        { id: 'investments', path: '/investments', icon: PieChart },
        { id: 'tax', path: '/tax', icon: Server } // Reuse icon or find better
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
                        onClick={() => navigate(item.path)}
                        className={`p-3 rounded-xl transition-all duration-300 relative group ${location.pathname === item.path ? 'bg-[#2b3139] text-nexus-gold' : 'text-zinc-500 hover:text-zinc-300'}`}
                    >
                        <item.icon size={24} />
                        {location.pathname === item.path && (
                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-nexus-gold rounded-r-full"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

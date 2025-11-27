import { Home, BarChart2, Wallet, User, Settings, Bell, Search, Menu, Building, TrendingUp, Bot } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

import { HelpCenterPage } from '../../pages/HelpCenterPage';

export const ModernLayout = ({ children, activeTab, onNavigate }) => {
    const { currentUser } = useAuth();

    const NavItem = ({ icon: Icon, label, id }) => (
        <button
            onClick={() => onNavigate(id)}
            className={`relative flex flex-col md:flex-row items-center md:gap-4 p-2 md:px-4 md:py-3 rounded-xl transition-all duration-300 group
            ${activeTab === id
                    ? 'text-nexus-blue bg-nexus-blue/10 shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'text-nexus-subtext hover:text-nexus-text hover:bg-white/5'}`}
        >
            <Icon size={24} className={`transition-transform duration-300 ${activeTab === id ? 'scale-110' : 'group-hover:scale-110'}`} />
            <span className="text-[10px] md:text-sm font-medium mt-1 md:mt-0">{label}</span>
            {activeTab === id && (
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-nexus-blue rounded-l-full hidden md:block shadow-[0_0_10px_#00F0FF]"></div>
            )}
        </button>
    );

    return (
        <div className="min-h-screen bg-nexus-black text-nexus-text font-sans selection:bg-nexus-blue/30">
            {/* DESKTOP SIDEBAR */}
            <aside className="hidden md:flex flex-col w-64 fixed left-0 top-0 bottom-0 bg-nexus-black/50 backdrop-blur-xl border-r border-white/5 z-50">
                <div className="p-6 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-nexus-blue to-purple-600 flex items-center justify-center shadow-lg shadow-nexus-blue/20">
                        <span className="font-bold text-xl text-white">N</span>
                    </div>
                    <h1 className="text-xl font-bold tracking-wider bg-gradient-to-r from-white to-nexus-subtext bg-clip-text text-transparent">
                        NXTradex
                    </h1>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <NavItem icon={Home} label="Dashboard" id="home" />
                    <NavItem icon={BarChart2} label="Trade" id="trade" />
                    <NavItem icon={Wallet} label="Wallet" id="wallet" />
                    <NavItem icon={Building} label="Banking" id="banking" />
                    <NavItem icon={TrendingUp} label="Investments" id="investments" />
                    <NavItem icon={Bot} label="AI Bot" id="aibot" />
                    <NavItem icon={User} label="Profile" id="profile" />
                </nav>

                <div className="p-4 border-t border-white/5">
                    <div className="bg-gradient-to-r from-nexus-blue/10 to-purple-500/10 rounded-xl p-4 border border-white/5">
                        <p className="text-xs text-nexus-subtext mb-1">Total Balance</p>
                        <p className="text-lg font-bold text-white">$12,450.00</p>
                    </div>
                </div>
            </aside>

            {/* MOBILE BOTTOM NAV */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-nexus-black/80 backdrop-blur-xl border-t border-white/10 z-50 px-6 py-2 pb-safe flex justify-between items-center">
                <NavItem icon={Home} label="Home" id="home" />
                <NavItem icon={BarChart2} label="Trade" id="trade" />
                <div className="w-12"></div> {/* Spacer for FAB */}
                <NavItem icon={Wallet} label="Wallet" id="wallet" />
                <NavItem icon={Bot} label="AI Bot" id="aibot" />
                <NavItem icon={User} label="Profile" id="profile" />

                {/* Floating Action Button (FAB) */}
                <button
                    onClick={() => onNavigate('trade')}
                    className="absolute left-1/2 -top-6 -translate-x-1/2 w-14 h-14 bg-gradient-to-br from-nexus-blue to-purple-600 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.4)] border-4 border-nexus-black animate-pulse"
                >
                    <BarChart2 size={24} className="text-white" />
                </button>
            </nav>

            {/* MAIN CONTENT AREA */}
            <main className="md:ml-64 min-h-screen pb-24 md:pb-0">
                {/* HEADER */}
                <header className="sticky top-0 z-40 bg-nexus-black/50 backdrop-blur-md border-b border-white/5 px-6 py-4 flex justify-between items-center">
                    <div className="md:hidden font-bold text-lg">NXTradex</div>

                    <div className="hidden md:flex items-center gap-4 flex-1 max-w-xl ml-4">
                        <div className="relative flex-1 group">
                            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-nexus-subtext group-focus-within:text-nexus-blue transition-colors" />
                            <input
                                type="text"
                                placeholder="Search markets, coins, or news..."
                                className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-nexus-blue/50 focus:bg-nexus-blue/5 transition-all"
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => onNavigate('notifications')}
                            className="relative p-2 hover:bg-white/5 rounded-lg transition-colors"
                        >
                            <Bell size={20} className="text-nexus-subtext hover:text-white" />
                            <span className="absolute top-2 right-2 w-2 h-2 bg-nexus-red rounded-full shadow-[0_0_5px_#FF2E54]"></span>
                        </button>
                        <button
                            onClick={() => onNavigate('profile')}
                            className="w-8 h-8 rounded-full bg-gradient-to-r from-nexus-blue to-purple-500 p-[1px] cursor-pointer hover:scale-105 transition-transform"
                        >
                            <div className="w-full h-full rounded-full bg-nexus-black flex items-center justify-center overflow-hidden">
                                {currentUser?.photoURL ? (
                                    <img src={currentUser.photoURL} alt="User" className="w-full h-full object-cover" />
                                ) : (
                                    <span className="font-bold text-xs text-white">{currentUser?.email?.[0].toUpperCase() || 'U'}</span>
                                )}
                            </div>
                        </button>
                    </div>
                </header>

                {/* CONTENT */}
                <div className="p-4 md:p-8 animate-fadeIn">
                    {activeTab === 'help' ? <HelpCenterPage /> : children}
                </div>
            </main>
        </div>
    );
};

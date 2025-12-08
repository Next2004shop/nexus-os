import { Terminal, Wallet, Landmark, PieChart, Globe, Shield, Users, Bot, Download, Scale, LogOut, Coins, Search } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import logo from '../../assets/logo.png';

export default function Sidebar() {
    const location = useLocation();
    const navigate = useNavigate();
    const { logout } = useAuth();

    const navItems = [
        { id: 'trade', path: '/trade', icon: Terminal },
        { id: 'stocks', path: '/stocks', icon: Globe },
        { id: 'commodities', path: '/commodities', icon: Coins },
        { id: 'ai-bot', path: '/ai-bot', icon: Bot },
        { id: 'opportunities', path: '/opportunities', icon: Search },
        { id: 'wallet', path: '/wallet', icon: Wallet },
        { id: 'downloads', path: '/downloads', icon: Download }
    ];

    const handleLogout = async () => {
        try {
            await logout();
            navigate('/');
        } catch (error) {
            console.error("Logout failed", error);
        }
    };

    return (
        <div className="hidden md:flex w-20 border-r border-[#2b3139] flex-col items-center py-6 bg-[#181a20] z-50 h-full">
            <div className="w-10 h-10 mb-8 rounded-full overflow-hidden border-2 border-nexus-gold shadow-[0_0_15px_rgba(252,213,53,0.3)]">
                <img src={logo} alt="Nexus" className="w-full h-full object-cover" />
            </div>
            <div className="space-y-6 flex-1 overflow-y-auto scrollbar-hide w-full flex flex-col items-center">
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

            <div className="mt-auto pt-4 border-t border-white/5 w-full flex flex-col items-center gap-4">
                <button
                    onClick={async () => {
                        if (confirm("💀 ACTIVATE KILL SWITCH? THIS WILL CLOSE ALL POSITIONS.")) {
                            try {
                                await fetch('/api/bridge/kill', { method: 'POST', headers: { 'Authorization': 'Basic ' + btoa('admin:securepassword') } });
                                alert("SYSTEM KILLED.");
                            } catch (e) {
                                alert("KILL FAILED: " + e.message);
                            }
                        }
                    }}
                    className="p-3 rounded-xl text-nexus-red bg-nexus-red/10 hover:bg-nexus-red hover:text-white transition-all duration-300 group animate-pulse"
                    title="KILL SWITCH"
                >
                    <Shield size={24} />
                </button>

                <button
                    onClick={handleLogout}
                    className="p-3 rounded-xl text-nexus-subtext hover:text-white hover:bg-white/5 transition-all duration-300 group"
                    title="Logout"
                >
                    <LogOut size={24} />
                </button>
            </div>
        </div>
    );
};

import React, { ReactNode, useState } from 'react';
import { Activity, BarChart3, Shield, Settings, Terminal, ChevronLeft, ChevronRight } from 'lucide-react';

interface LayoutProps {
    children: ReactNode;
}

const NAV_ITEMS = [
    { icon: Activity, label: 'Dashboard', id: 'dashboard', active: true },
    { icon: BarChart3, label: 'Markets', id: 'markets', active: false },
    { icon: Terminal, label: 'Console', id: 'console', active: false },
    { icon: Shield, label: 'Risk', id: 'risk', active: false },
    { icon: Settings, label: 'Config', id: 'config', active: false },
];

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const [collapsed, setCollapsed] = useState(true);

    return (
        <div className="flex h-screen bg-zinc-950 text-zinc-400 font-mono overflow-hidden">
            {/* Sidebar */}
            <aside
                className={`${collapsed ? 'w-14' : 'w-48'
                    } flex-shrink-0 border-r border-zinc-800/60 bg-zinc-950 flex flex-col transition-all duration-200`}
            >
                {/* Logo */}
                <div className="h-12 flex items-center justify-center border-b border-zinc-800/60 px-3">
                    <span className={`text-green-500 font-bold text-xs tracking-[0.2em] uppercase ${collapsed ? 'hidden' : 'block'}`}>
                        Nexus
                    </span>
                    <span className={`text-green-500 font-bold text-sm ${collapsed ? 'block' : 'hidden'}`}>
                        N
                    </span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-4 space-y-1 px-2">
                    {NAV_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            className={`w-full flex items-center gap-3 px-2 py-2.5 rounded-sm text-[11px] uppercase tracking-wider transition-colors ${item.active
                                    ? 'text-green-500 bg-green-500/5 border border-green-500/10'
                                    : 'text-zinc-600 hover:text-zinc-400 hover:bg-zinc-800/30 border border-transparent'
                                }`}
                            title={item.label}
                        >
                            <item.icon className="w-4 h-4 flex-shrink-0" />
                            <span className={collapsed ? 'hidden' : 'block'}>{item.label}</span>
                        </button>
                    ))}
                </nav>

                {/* Collapse toggle */}
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="h-10 flex items-center justify-center border-t border-zinc-800/60 text-zinc-700 hover:text-zinc-400 transition-colors"
                >
                    {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                </button>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-12 flex items-center justify-between px-4 border-b border-zinc-800/60 flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <h1 className="text-xs font-bold tracking-[0.3em] uppercase text-green-500">
                            Nexus Sovereign
                        </h1>
                        <span className="text-[10px] bg-green-500/10 text-green-700 px-2 py-0.5 rounded-full border border-green-500/20">
                            v1.0.5
                        </span>
                    </div>
                    <div className="text-[10px] text-zinc-600 flex gap-4 uppercase">
                        <span>Encrypted_Link: Active</span>
                        <span>Ghost_Mode: Enabled</span>
                    </div>
                </header>

                {/* Content */}
                <main className="flex-1 overflow-auto">
                    {children}
                </main>

                {/* Status Bar */}
                <footer className="h-7 flex items-center justify-between px-4 border-t border-zinc-800/60 text-[9px] text-zinc-700 uppercase flex-shrink-0">
                    <div className="flex gap-4">
                        <span>Secret_Manager: Verified</span>
                        <span>Auth: JWT+Firebase</span>
                    </div>
                    <span>© 2025 NEXUS_GENESIS</span>
                </footer>
            </div>
        </div>
    );
};

export default Layout;

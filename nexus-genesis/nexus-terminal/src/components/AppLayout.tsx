import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    LayoutDashboard,
    BarChart3,
    Shield,
    Brain,
    Terminal,
    ScrollText,
    Settings,
    LogOut,
    Activity,
} from 'lucide-react';

const NAV_ITEMS = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/positions', icon: BarChart3, label: 'Positions' },
    { to: '/risk', icon: Shield, label: 'Risk' },
    { to: '/intelligence', icon: Brain, label: 'Intelligence' },
    { to: '/execution', icon: Terminal, label: 'Execution' },
    { to: '/logs', icon: ScrollText, label: 'Logs' },
];

interface AppLayoutProps {
    children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
    const { user, logout } = useAuth();
    const location = useLocation();

    return (
        <div className="min-h-screen bg-nexus-bg flex">
            {/* Sidebar */}
            <aside className="w-56 bg-nexus-surface border-r border-nexus-border flex flex-col flex-shrink-0">
                {/* Logo */}
                <div className="h-14 flex items-center px-5 border-b border-nexus-border">
                    <Activity className="w-4 h-4 text-nexus-accent mr-2" />
                    <span className="text-sm font-semibold text-nexus-text tracking-wide">NEXUS</span>
                    <span className="text-[10px] text-nexus-muted ml-2 font-mono">v3.2</span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-3 px-3 space-y-0.5">
                    {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
                        <NavLink
                            key={to}
                            to={to}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${isActive
                                    ? 'bg-nexus-accent/10 text-nexus-accent'
                                    : 'text-nexus-muted hover:text-nexus-text hover:bg-nexus-hover'
                                }`
                            }
                        >
                            <Icon className="w-4 h-4" />
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* User section */}
                <div className="border-t border-nexus-border p-3">
                    <div className="flex items-center gap-2 px-3 py-2">
                        <div className="w-7 h-7 bg-nexus-accent/20 rounded-full flex items-center justify-center">
                            <span className="text-xs font-semibold text-nexus-accent">
                                {user?.username?.charAt(0).toUpperCase() || '?'}
                            </span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-sm text-nexus-text truncate">{user?.username}</div>
                            <div className="text-[10px] text-nexus-muted uppercase">{user?.role}</div>
                        </div>
                    </div>
                    <button
                        onClick={logout}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs text-nexus-muted hover:text-nexus-red transition-colors w-full mt-1"
                    >
                        <LogOut className="w-3 h-3" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top bar */}
                <header className="h-14 bg-nexus-surface border-b border-nexus-border flex items-center justify-between px-6 flex-shrink-0">
                    <div className="flex items-center gap-4">
                        <h1 className="text-sm font-medium text-nexus-text">
                            {NAV_ITEMS.find((item) => item.to === location.pathname)?.label || 'NEXUS'}
                        </h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-nexus-green rounded-full animate-pulse" />
                            <span className="text-xs text-nexus-muted font-mono">ONLINE</span>
                        </div>
                        <span className="text-xs text-nexus-muted font-mono">
                            {new Date().toLocaleTimeString('en-US', { hour12: false })}
                        </span>
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}

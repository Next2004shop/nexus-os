"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BarChart2, Bot, Wallet, Settings, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

const Sidebar = () => {
    const pathname = usePathname();

    const navItems = [
        { name: "Trade", href: "/", icon: LayoutDashboard },
        { name: "Stocks", href: "/stocks", icon: BarChart2 },
        { name: "AI Bot", href: "/ai-bot", icon: Bot },
        { name: "Wallet", href: "/wallet", icon: Wallet },
    ];

    return (
        <aside className="w-[80px] h-screen bg-nexus-bg/80 backdrop-blur-xl border-r border-nexus-border flex flex-col items-center py-8 z-50">
            {/* Logo */}
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 flex items-center justify-center mb-12 shadow-[0_0_20px_rgba(0,221,128,0.1)]">
                <div className="w-6 h-6 bg-nexus-green rounded transform rotate-45" />
            </div>

            {/* Nav Items */}
            <nav className="flex flex-col gap-6 w-full px-4">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "relative w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 group",
                                isActive
                                    ? "text-nexus-green bg-gradient-to-br from-white/10 to-white/5 border border-white/10 shadow-lg"
                                    : "text-nexus-subtext hover:text-white hover:bg-white/5 hover:-translate-y-0.5"
                            )}
                        >
                            <Icon size={24} />

                            {/* Active Indicator */}
                            {isActive && (
                                <div className="absolute -right-4 top-1/2 -translate-y-1/2 w-1 h-5 bg-nexus-green rounded-l shadow-[0_0_10px_var(--nexus-green)]" />
                            )}

                            {/* Tooltip */}
                            <div className="absolute left-14 px-2 py-1 bg-nexus-card border border-nexus-border rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                                {item.name}
                            </div>
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom Actions */}
            <div className="mt-auto flex flex-col gap-4">
                <button className="w-12 h-12 rounded-xl flex items-center justify-center text-nexus-subtext hover:text-white transition-colors">
                    <Settings size={24} />
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;

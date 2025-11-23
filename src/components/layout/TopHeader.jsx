import React from 'react';
import { User, Search, ScanLine, Headset, Bell } from 'lucide-react';

export function TopHeader({ onProfileClick }) {
    return (
        <div className="sticky top-0 z-40 bg-nexus-black px-4 py-3 flex items-center justify-between gap-4">
            {/* Profile */}
            <button
                onClick={onProfileClick}
                className="w-8 h-8 rounded-full bg-nexus-border flex items-center justify-center text-nexus-subtext hover:bg-nexus-gray transition-colors"
            >
                <User size={18} />
            </button>

            {/* Search Bar */}
            <div className="flex-1 relative">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                    <Search size={16} className="text-nexus-subtext" />
                </div>
                <input
                    type="text"
                    placeholder="BTC"
                    className="w-full bg-nexus-border text-nexus-text text-sm rounded-full py-2 pl-10 pr-4 placeholder-nexus-subtext focus:outline-none focus:ring-1 focus:ring-nexus-yellow"
                />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4 text-nexus-text">
                <button className="hover:text-nexus-yellow transition-colors">
                    <ScanLine size={20} />
                </button>
                <button className="hover:text-nexus-yellow transition-colors">
                    <Headset size={20} />
                </button>
                <button className="hover:text-nexus-yellow transition-colors relative">
                    <Bell size={20} />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-nexus-red rounded-full"></span>
                </button>
            </div>
        </div>
    );
}

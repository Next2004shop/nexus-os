import React from 'react';
import { User, Shield, Bell, HelpCircle, LogOut, ChevronRight, CreditCard } from 'lucide-react';

export const ProfilePage = () => {
    const menuItems = [
        { icon: User, label: 'Account Information', desc: 'Personal details & verification' },
        { icon: Shield, label: 'Security', desc: '2FA, Password, Devices' },
        { icon: CreditCard, label: 'Payment Methods', desc: 'Bank accounts & cards' },
        { icon: Bell, label: 'Notifications', desc: 'Alert preferences' },
        { icon: HelpCircle, label: 'Help & Support', desc: 'FAQ & Customer Service' },
    ];

    return (
        <div className="max-w-2xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in pb-24 md:pb-8">
            <h1 className="text-2xl font-bold mb-6">Profile & Settings</h1>

            {/* USER CARD */}
            <div className="glass-panel p-6 flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-nexus-gold to-orange-500 flex items-center justify-center text-black font-bold text-2xl shadow-lg">
                    D
                </div>
                <div className="flex-1">
                    <h2 className="text-lg font-bold text-white">Danteh</h2>
                    <p className="text-zinc-400 text-xs font-mono">ID: 88392019 • <span className="text-emerald-400">Verified</span></p>
                </div>
                <button className="px-3 py-1 bg-zinc-800 rounded-lg text-xs font-bold hover:bg-zinc-700 transition-colors">
                    Edit
                </button>
            </div>

            {/* MENU */}
            <div className="space-y-2">
                {menuItems.map((item, index) => (
                    <button key={index} className="w-full glass-panel p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group">
                        <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-nexus-gold transition-colors">
                            <item.icon size={20} />
                        </div>
                        <div className="flex-1 text-left">
                            <div className="font-bold text-sm text-zinc-200">{item.label}</div>
                            <div className="text-xs text-zinc-500">{item.desc}</div>
                        </div>
                        <ChevronRight size={16} className="text-zinc-600 group-hover:text-white transition-colors" />
                    </button>
                ))}
            </div>

            {/* LOGOUT */}
            <button className="w-full p-4 rounded-xl border border-rose-500/20 text-rose-500 flex items-center justify-center gap-2 hover:bg-rose-500/10 transition-colors font-bold text-sm">
                <LogOut size={18} />
                Log Out
            </button>
        </div>
    );
};

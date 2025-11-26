import React, { useState } from 'react';
import { User, Settings, Shield, LogOut, ChevronRight, Mail, Crown, Star, Share2, Bell, Globe, Moon, CreditCard, HelpCircle, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const ProfileItem = ({ icon: Icon, label, value, onClick, isDanger, hasToggle }) => (
    <button onClick={onClick} className="w-full flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-colors group border border-transparent hover:border-white/5">
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isDanger ? 'bg-nexus-red/10 text-nexus-red' : 'bg-nexus-blue/10 text-nexus-blue'}`}>
                <Icon size={20} />
            </div>
            <div className="text-left">
                <div className={`font-medium ${isDanger ? 'text-nexus-red' : 'text-white'}`}>{label}</div>
                {value && <div className="text-xs text-nexus-subtext">{value}</div>}
            </div>
        </div>
        {hasToggle ? (
            <div className="w-10 h-6 bg-nexus-blue/20 rounded-full relative">
                <div className="absolute right-1 top-1 w-4 h-4 bg-nexus-blue rounded-full shadow-sm"></div>
            </div>
        ) : (
            <ChevronRight size={16} className="text-nexus-subtext group-hover:translate-x-1 transition-transform" />
        )}
    </button>
);

const SecurityCard = () => (
    <div className="bg-nexus-card border border-nexus-border p-5 rounded-2xl relative overflow-hidden">
        <div className="flex justify-between items-start mb-4">
            <div>
                <h3 className="text-white font-bold flex items-center gap-2">
                    <Shield size={18} className="text-nexus-green" />
                    Security Status
                </h3>
                <p className="text-nexus-subtext text-xs mt-1">Your account is well protected.</p>
            </div>
            <div className="text-right">
                <div className="text-2xl font-bold text-nexus-green">92%</div>
                <div className="text-[10px] text-nexus-subtext uppercase font-bold">Secure</div>
            </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-4">
            <div className="h-full w-[92%] bg-gradient-to-r from-nexus-blue to-nexus-green"></div>
        </div>

        <div className="grid grid-cols-2 gap-2">
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">2FA Enabled</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">Email Verified</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">Phone Linked</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-yellow"></div>
                <span className="text-xs text-white/80">Anti-Phishing</span>
            </div>
        </div>
    </div>
);

const ReferralCard = () => (
    <div className="bg-gradient-to-br from-nexus-purple/20 to-nexus-blue/20 border border-nexus-purple/30 p-5 rounded-2xl relative overflow-hidden group cursor-pointer hover:border-nexus-purple/50 transition-all">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Crown size={80} />
        </div>
        <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
                <Crown size={18} className="text-nexus-yellow" />
                <span className="text-xs font-bold text-nexus-yellow uppercase tracking-wider">VIP Referral Hub</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Invite Friends, Earn Crypto</h3>
            <p className="text-nexus-subtext text-xs mb-4 max-w-[80%]">Get 20% of trading fees from every friend you invite to Nexus AI.</p>

            <div className="flex gap-3">
                <button className="flex-1 bg-white/10 hover:bg-white/20 text-white text-xs font-bold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2">
                    <Share2 size={14} /> Share Link
                </button>
                <div className="px-4 py-2 bg-black/30 rounded-xl border border-white/10 text-white font-mono text-xs flex items-center">
                    NEXUS-2024
                </div>
            </div>
        </div>
    </div>
);

export const ProfilePage = () => {
    const { currentUser, logout } = useAuth();

    return (
        <div className="min-h-screen bg-nexus-black pb-32 overflow-y-auto">
            <div className="max-w-2xl mx-auto p-4 space-y-6">

                {/* HEADER */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-white">Profile</h1>
                    <button className="p-2 hover:bg-white/10 rounded-full transition-colors text-nexus-subtext hover:text-white">
                        <Settings size={20} />
                    </button>
                </div>

                {/* USER CARD */}
                <div className="bg-nexus-card border border-nexus-border rounded-3xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6">
                        <div className="bg-nexus-yellow/10 text-nexus-yellow text-[10px] font-bold px-3 py-1 rounded-full border border-nexus-yellow/20 flex items-center gap-1">
                            <Crown size={12} /> PLATINUM TRADER
                        </div>
                    </div>

                    <div className="flex items-center gap-5 relative z-10">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-nexus-blue to-purple-600 p-[2px]">
                            <div className="w-full h-full rounded-full bg-nexus-black flex items-center justify-center overflow-hidden">
                                {currentUser?.photoURL ? (
                                    <img src={currentUser.photoURL} alt="Profile" className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-2xl font-bold text-white">{currentUser?.email?.[0].toUpperCase()}</span>
                                )}
                            </div>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{currentUser?.displayName || 'Nexus Trader'}</h2>
                            <p className="text-nexus-subtext text-sm flex items-center gap-1 mb-2">
                                <Mail size={12} /> {currentUser?.email}
                            </p>
                            <div className="flex items-center gap-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-nexus-green/10 text-nexus-green border border-nexus-green/20">
                                    Verified
                                </span>
                                <span className="text-nexus-subtext text-[10px]">ID: 8493021</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SECURITY CENTER */}
                <SecurityCard />

                {/* REFERRAL HUB */}
                <ReferralCard />

                {/* SETTINGS GROUPS */}
                <div className="space-y-6">
                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Account Settings</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={User} label="Personal Information" value="KYC Level 2" />
                            <ProfileItem icon={CreditCard} label="Payment Methods" value="2 Linked" />
                            <ProfileItem icon={Globe} label="Language" value="English (US)" />
                            <ProfileItem icon={Moon} label="Dark Mode" hasToggle />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Notifications</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={Bell} label="Push Notifications" hasToggle />
                            <ProfileItem icon={Mail} label="Email Alerts" hasToggle />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Support</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={HelpCircle} label="Help Center" />
                            <ProfileItem icon={MessageSquare} label="Live Chat" value="Online" />
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="w-full py-4 rounded-2xl bg-nexus-red/10 text-nexus-red font-bold text-sm hover:bg-nexus-red/20 transition-colors flex items-center justify-center gap-2"
                    >
                        <LogOut size={18} /> Log Out
                    </button>

                    <div className="text-center text-nexus-subtext text-[10px] pb-4">
                        Nexus AI v2.4.0 (Build 892)
                    </div>
                </div>
            </div>
        </div>
    );
};

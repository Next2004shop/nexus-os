import React from 'react';
import { User, Settings, Shield, LogOut, ChevronRight, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const ProfileItem = ({ icon: Icon, label, value, onClick, isDanger }) => (
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
        <ChevronRight size={16} className="text-nexus-subtext group-hover:translate-x-1 transition-transform" />
    </button>
);

export const ProfilePage = () => {
    const { currentUser, logout } = useAuth();

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <h1 className="text-3xl font-bold text-white">Profile & Settings</h1>

            {/* USER CARD */}
            <div className="bg-nexus-card/50 backdrop-blur-sm border border-white/5 rounded-3xl p-6 flex items-center gap-6">
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
                    <p className="text-nexus-subtext text-sm flex items-center gap-1">
                        <Mail size={12} /> {currentUser?.email}
                    </p>
                    <div className="mt-2 inline-flex items-center px-2 py-1 rounded-lg bg-nexus-green/10 text-nexus-green text-xs font-bold border border-nexus-green/20">
                        <Shield size={10} className="mr-1" /> Verified
                    </div>
                </div>
            </div>

            {/* SETTINGS LIST */}
            <div className="space-y-2">
                <ProfileItem icon={User} label="Account Details" value="Personal Information" />
                <ProfileItem icon={Shield} label="Security" value="2FA, Password" />
                <ProfileItem icon={Settings} label="Preferences" value="Theme, Language, Notifications" />
                <div className="h-4"></div>
                <ProfileItem icon={LogOut} label="Log Out" isDanger onClick={logout} />
            </div>
        </div>
    );
};

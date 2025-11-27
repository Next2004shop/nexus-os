import React, { useState } from 'react';
import { Shield, Lock, Smartphone, Key, History, AlertTriangle, CheckCircle } from 'lucide-react';

export const SecurityPage = () => {
    const [twoFactor, setTwoFactor] = useState(true);
    const [biometric, setBiometric] = useState(false);

    return (
        <div className="p-6 space-y-6 max-w-4xl mx-auto animate-fadeIn pb-24">
            <h1 className="text-3xl font-black text-white flex items-center gap-3">
                <Shield className="text-nexus-blue" size={32} />
                Security Center
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 2FA SETTINGS */}
                <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-nexus-blue/10 flex items-center justify-center text-nexus-blue">
                            <Smartphone size={20} />
                        </div>
                        <div>
                            <h3 className="font-bold text-white">Two-Factor Authentication</h3>
                            <p className="text-xs text-nexus-subtext">Protect your account with 2FA</p>
                        </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl mb-4">
                        <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${twoFactor ? 'bg-nexus-green' : 'bg-nexus-red'}`}></div>
                            <span className="text-sm font-bold text-white">Authenticator App</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={twoFactor} onChange={() => setTwoFactor(!twoFactor)} />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nexus-blue"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                        <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${biometric ? 'bg-nexus-green' : 'bg-nexus-subtext'}`}></div>
                            <span className="text-sm font-bold text-white">Biometric Login</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={biometric} onChange={() => setBiometric(!biometric)} />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nexus-blue"></div>
                        </label>
                    </div>
                </div>

                {/* PASSWORD & DEVICES */}
                <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-nexus-yellow/10 flex items-center justify-center text-nexus-yellow">
                            <Lock size={20} />
                        </div>
                        <div>
                            <h3 className="font-bold text-white">Password & Devices</h3>
                            <p className="text-xs text-nexus-subtext">Manage access</p>
                        </div>
                    </div>

                    <button className="w-full py-3 mb-4 border border-white/10 rounded-xl text-white font-bold hover:bg-white/5 transition-colors flex items-center justify-center gap-2">
                        <Key size={16} /> Change Password
                    </button>

                    <div className="space-y-3">
                        <h4 className="text-xs font-bold text-nexus-subtext uppercase">Active Sessions</h4>
                        <div className="flex items-center justify-between text-sm text-white p-3 bg-white/5 rounded-lg">
                            <div className="flex items-center gap-2">
                                <Smartphone size={14} className="text-nexus-subtext" />
                                <span>iPhone 14 Pro</span>
                            </div>
                            <span className="text-xs text-nexus-green">Current</span>
                        </div>
                        <div className="flex items-center justify-between text-sm text-white p-3 bg-white/5 rounded-lg">
                            <div className="flex items-center gap-2">
                                <History size={14} className="text-nexus-subtext" />
                                <span>Chrome / Windows</span>
                            </div>
                            <span className="text-xs text-nexus-subtext">2h ago</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

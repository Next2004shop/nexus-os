import React from 'react';
import { Download, Smartphone, Monitor, Shield, Zap, Terminal } from 'lucide-react';

export const DownloadPage = () => {
    return (
        <div className="p-6 animate-fadeIn pb-24 md:pb-6 max-w-5xl mx-auto">
            <div className="mb-10 text-center">
                <h1 className="text-4xl font-black text-white mb-2">Nexus OS <span className="text-nexus-blue">Deployment Center</span></h1>
                <p className="text-nexus-subtext">Select your combat platform. Secure. Fast. Autonomous.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* PC / DESKTOP */}
                <div className="bg-nexus-card border border-nexus-border p-8 rounded-3xl relative overflow-hidden group hover:border-nexus-blue/50 transition-all">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Monitor size={120} />
                    </div>

                    <div className="relative z-10">
                        <div className="w-16 h-16 bg-nexus-blue/10 rounded-2xl flex items-center justify-center mb-6 text-nexus-blue">
                            <Monitor size={32} />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Desktop Command Station</h2>
                        <p className="text-nexus-subtext text-sm mb-6">
                            Full-featured trading terminal for Windows, macOS, and Linux.
                            Optimized for multi-screen setups and high-frequency execution.
                        </p>

                        <div className="space-y-3 mb-8">
                            <div className="flex items-center gap-3 text-sm text-white">
                                <Zap size={16} className="text-nexus-yellow" />
                                <span>PWA Technology (Instant Updates)</span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-white">
                                <Shield size={16} className="text-nexus-green" />
                                <span>Encrypted Local Storage</span>
                            </div>
                        </div>

                        <button
                            onClick={() => alert("To install on PC: Click the 'Install' icon in your browser address bar.")}
                            className="w-full py-4 bg-nexus-blue text-black font-bold rounded-xl hover:bg-cyan-400 transition-colors flex items-center justify-center gap-2"
                        >
                            <Download size={20} />
                            INSTALL APP (PWA)
                        </button>
                        <p className="text-center text-xs text-nexus-subtext mt-3">
                            *Requires Chrome, Edge, or Brave Browser
                        </p>
                    </div>
                </div>

                {/* ANDROID / MOBILE */}
                <div className="bg-nexus-card border border-nexus-border p-8 rounded-3xl relative overflow-hidden group hover:border-nexus-green/50 transition-all">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Smartphone size={120} />
                    </div>

                    <div className="relative z-10">
                        <div className="w-16 h-16 bg-nexus-green/10 rounded-2xl flex items-center justify-center mb-6 text-nexus-green">
                            <Smartphone size={32} />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Mobile Field Unit</h2>
                        <p className="text-nexus-subtext text-sm mb-6">
                            Tactical mobile interface for Android. Monitor positions and execute trades on the go.
                            Includes biometric security.
                        </p>

                        <div className="space-y-3 mb-8">
                            <div className="flex items-center gap-3 text-sm text-white">
                                <Terminal size={16} className="text-nexus-purple" />
                                <span>Native APK Performance</span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-white">
                                <Shield size={16} className="text-nexus-green" />
                                <span>Fingerprint / FaceID Ready</span>
                            </div>
                        </div>

                        <button
                            onClick={() => alert("Build APK Command: npx cap build android")}
                            className="w-full py-4 bg-nexus-green text-black font-bold rounded-xl hover:bg-emerald-400 transition-colors flex items-center justify-center gap-2"
                        >
                            <Download size={20} />
                            DOWNLOAD APK
                        </button>
                        <p className="text-center text-xs text-nexus-subtext mt-3">
                            *Version 2.5.0 (Build 420)
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

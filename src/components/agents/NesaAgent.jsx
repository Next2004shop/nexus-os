import React, { useState, useEffect } from 'react';
import { Skull, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

export const NesaAgent = () => {
    const [activeError, setActiveError] = useState(null);
    const [fixing, setFixing] = useState(false);
    const [fixed, setFixed] = useState(false);

    useEffect(() => {
        // Global Error Listener
        const handleError = (event) => {
            console.log("NESA Detected Error:", event);
            triggerNesa(event.message || "Unknown System Error");
        };

        const handleRejection = (event) => {
            console.log("NESA Detected Promise Rejection:", event);
            triggerNesa(event.reason?.message || "Async Operation Failed");
        };

        window.addEventListener('error', handleError);
        window.addEventListener('unhandledrejection', handleRejection);

        return () => {
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleRejection);
        };
    }, []);

    const triggerNesa = (errorMessage) => {
        if (fixing) return; // Already working
        setActiveError(errorMessage);
        setFixing(true);

        // Simulate "Fixing" Process
        setTimeout(() => {
            setFixing(false);
            setFixed(true);

            // Auto-hide after success
            setTimeout(() => {
                setFixed(false);
                setActiveError(null);
            }, 3000);
        }, 2500);
    };

    if (!activeError && !fixing && !fixed) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 50 }}
                className="fixed bottom-20 right-4 md:bottom-8 md:right-8 z-[9999] flex items-end gap-4 pointer-events-none"
            >
                {/* DIALOG BUBBLE */}
                <div className="bg-black/90 border border-red-500/30 p-4 rounded-2xl rounded-br-none shadow-2xl backdrop-blur-md max-w-xs mb-4">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold text-red-500 uppercase tracking-widest">NESA Protocol</span>
                        <div className="h-1 flex-1 bg-red-900/30 rounded-full overflow-hidden">
                            <div className={`h-full bg-red-500 ${fixing ? 'animate-progress' : 'w-full'}`}></div>
                        </div>
                    </div>

                    {fixing ? (
                        <div>
                            <p className="text-white text-sm font-bold mb-1">Anomaly Detected!</p>
                            <p className="text-red-400 text-xs font-mono truncate">{activeError}</p>
                            <p className="text-nexus-subtext text-[10px] mt-2 animate-pulse">Injecting hotfix patch...</p>
                        </div>
                    ) : fixed ? (
                        <div>
                            <div className="flex items-center gap-2 text-green-400 font-bold text-sm mb-1">
                                <CheckCircle size={14} />
                                <span>System Restored</span>
                            </div>
                            <p className="text-nexus-subtext text-[10px]">Optimization complete. Resume operations.</p>
                        </div>
                    ) : null}
                </div>

                {/* SKULL AVATAR */}
                <div className="relative w-16 h-16">
                    {/* Flames Animation */}
                    <div className="absolute inset-0 bg-red-600 rounded-full blur-xl opacity-50 animate-pulse"></div>
                    <div className="absolute -top-2 -left-2 w-20 h-20 bg-orange-500 rounded-full blur-2xl opacity-30 animate-blob"></div>

                    {/* Skull Icon */}
                    <div className="relative z-10 w-16 h-16 bg-black rounded-full border-2 border-red-500/50 flex items-center justify-center shadow-[0_0_30px_rgba(220,38,38,0.5)]">
                        <Skull size={32} className={`text-red-500 ${fixing ? 'animate-shake' : ''}`} />

                        {/* Eyes Glow */}
                        <div className="absolute top-6 left-5 w-1.5 h-1.5 bg-red-100 rounded-full shadow-[0_0_10px_red] animate-ping"></div>
                        <div className="absolute top-6 right-5 w-1.5 h-1.5 bg-red-100 rounded-full shadow-[0_0_10px_red] animate-ping"></div>
                    </div>

                    {/* Status Badge */}
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-black rounded-full border border-red-500 flex items-center justify-center z-20">
                        <Zap size={10} className="text-red-500 fill-red-500" />
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

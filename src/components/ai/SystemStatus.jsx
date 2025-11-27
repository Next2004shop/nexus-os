import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle, Activity, Zap, ShieldCheck } from 'lucide-react';

export const SystemStatus = () => {
    const [status, setStatus] = useState('SCANNING');
    const [health, setHealth] = useState(98);
    const [activeAgents, setActiveAgents] = useState(3);

    useEffect(() => {
        const interval = setInterval(() => {
            setStatus(prev => prev === 'SCANNING' ? 'OPTIMIZING' : 'SECURE');
            setHealth(prev => Math.min(100, prev + Math.random()));
        }, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <Cpu size={100} className="text-nexus-blue" />
            </div>

            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <ShieldCheck size={20} className="text-nexus-green" />
                Engineering Agent
            </h2>

            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-nexus-black/50 p-3 rounded-xl border border-white/5">
                    <div className="text-xs text-nexus-subtext uppercase font-bold">System Health</div>
                    <div className="text-xl font-mono font-bold text-nexus-green">{health.toFixed(1)}%</div>
                </div>
                <div className="bg-nexus-black/50 p-3 rounded-xl border border-white/5">
                    <div className="text-xs text-nexus-subtext uppercase font-bold">Active Agents</div>
                    <div className="text-xl font-mono font-bold text-nexus-blue">{activeAgents}/4</div>
                </div>
            </div>

            <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                    <div className={`w-2 h-2 rounded-full ${status === 'SCANNING' ? 'bg-nexus-yellow animate-pulse' : 'bg-nexus-green'}`}></div>
                    <span className="text-white font-medium">
                        {status === 'SCANNING' ? 'Scanning Codebase...' :
                            status === 'OPTIMIZING' ? 'Optimizing React Render Cycles...' :
                                'All Systems Nominal'}
                    </span>
                </div>

                <div className="h-1.5 bg-nexus-black rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-1000 ${status === 'SECURE' ? 'bg-nexus-green w-full' : 'bg-nexus-blue w-[70%] animate-pulse'}`}></div>
                </div>

                <div className="text-[10px] text-nexus-subtext font-mono mt-2">
                    > ErrorBoundary: ACTIVE (Self-Healing)<br />
                    > Bridge Connection: STABLE<br />
                    > Memory Usage: 42MB (Optimized)
                </div>
            </div>
        </div>
    );
};

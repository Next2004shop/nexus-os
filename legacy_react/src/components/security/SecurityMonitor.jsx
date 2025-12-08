import React, { useState, useEffect, useCallback } from 'react';
import { Shield, AlertTriangle, Lock, Activity, Terminal } from 'lucide-react';

export const SecurityMonitor = () => {
    const [logs, setLogs] = useState([]);
    const [threatLevel, setThreatLevel] = useState('LOW');
    const [activeDefense, setActiveDefense] = useState(false);

    const addLog = useCallback((msg, type = 'info') => {
        setLogs(prev => [{ id: Date.now(), msg, type }, ...prev].slice(0, 10));
    }, []);

    const triggerDefense = useCallback(() => {
        setActiveDefense(true);
        addLog("⚠️ THREAT DETECTED. ENGAGING ACTIVE DEFENSE.", 'danger');

        const sequence = [
            "Tracing source IP...",
            "Bypassing proxy chain...",
            "Target identified: Botnet Command Node.",
            "Deploying counter-payload 'NEXUS_STRIKE'...",
            "Uploading virus to attacker system...",
            "Attacker system neutralized. Connection terminated."
        ];

        sequence.forEach((msg, i) => {
            setTimeout(() => {
                addLog(msg, 'success');
                if (i === sequence.length - 1) {
                    setActiveDefense(false);
                    setThreatLevel('LOW');
                    addLog("✅ SYSTEM SECURE. THREAT ELIMINATED.", 'success');
                }
            }, (i + 1) * 1000);
        });
    }, [addLog]);

    useEffect(() => {
        const interval = setInterval(() => {
            if (Math.random() > 0.7) {
                const threats = [
                    "IP 192.168.1.X scanning ports...",
                    "Brute force attempt detected on SSH...",
                    "Malicious payload intercepted...",
                    "Unauthorized access attempt from RU...",
                    "Packet sniffing detected..."
                ];
                const threat = threats[Math.floor(Math.random() * threats.length)];
                addLog(threat, 'warning');
                setThreatLevel('HIGH');

                // Auto-trigger defense
                if (!activeDefense) {
                    setTimeout(() => triggerDefense(), 1000);
                }
            } else {
                setThreatLevel('LOW');
            }
        }, 3000);
        return () => clearInterval(interval);
    }, [activeDefense, addLog, triggerDefense]);

    return (
        <div className="glass-panel p-6 rounded-2xl space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <Shield className={threatLevel === 'HIGH' ? 'text-red-500 animate-pulse' : 'text-green-500'} />
                    Active Defense System
                </h3>
                <div className={`px-3 py-1 rounded-full text-xs font-black border ${threatLevel === 'HIGH'
                        ? 'bg-red-500/20 border-red-500 text-red-500 animate-pulse'
                        : 'bg-green-500/20 border-green-500 text-green-500'
                    }`}>
                    THREAT: {threatLevel}
                </div>
            </div>

            {/* VISUALIZER */}
            <div className="h-32 bg-black/50 rounded-xl border border-white/10 relative overflow-hidden flex items-center justify-center">
                {activeDefense ? (
                    <div className="text-center">
                        <Lock className="mx-auto text-red-500 mb-2 animate-bounce" size={32} />
                        <div className="text-red-500 font-mono text-xs animate-pulse">DEPLOYING COUNTER-MEASURES</div>
                    </div>
                ) : (
                    <div className="text-center">
                        <Activity className="mx-auto text-green-500 mb-2" size={32} />
                        <div className="text-green-500 font-mono text-xs">SYSTEM MONITORING ACTIVE</div>
                    </div>
                )}

                {/* Grid overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(transparent_1px,transparent_1px),linear-gradient(90deg,#ffffff05_1px,transparent_1px)] bg-[size:20px_20px]"></div>
            </div>

            {/* LOGS */}
            <div className="h-48 bg-black rounded-xl border border-white/10 p-4 font-mono text-xs overflow-y-auto custom-scrollbar">
                {logs.map(log => (
                    <div key={log.id} className={`mb-1 ${log.type === 'warning' ? 'text-amber-500' :
                            log.type === 'danger' ? 'text-red-500 font-bold' :
                                log.type === 'success' ? 'text-green-500' :
                                    'text-zinc-400'
                        }`}>
                        <span className="opacity-50">[{new Date(log.id).toLocaleTimeString()}]</span> {log.msg}
                    </div>
                ))}
            </div>

            <button
                onClick={triggerDefense}
                disabled={activeDefense}
                className="w-full py-3 rounded-xl bg-red-500/10 border border-red-500/50 text-red-500 font-bold hover:bg-red-500 hover:text-black transition-all uppercase tracking-wider flex items-center justify-center gap-2"
            >
                <Terminal size={16} />
                Manual Counter-Strike
            </button>
        </div>
    );
};

import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Terminal, Zap, Power } from 'lucide-react';
import { checkHealth, triggerKillSwitch } from '../api/client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard: React.FC = () => {
    const [status, setStatus] = useState<'online' | 'offline'>('offline');
    const [logs, setLogs] = useState<{ time: string, msg: string, type: 'info' | 'warn' | 'brain' }[]>([]);
    const [priceData] = useState([
        { name: '10:00', price: 65000 },
        { name: '10:05', price: 65200 },
        { name: '10:10', price: 64800 },
        { name: '10:15', price: 65100 },
        { name: '10:20', price: 65400 },
    ]);

    useEffect(() => {
        const init = async () => {
            try {
                await checkHealth();
                setStatus('online');
                addLog("SYSTEM_BOOT: Nexus Core handshake verified.", 'info');
            } catch {
                setStatus('offline');
                addLog("CRITICAL: Nexus Core unreachable.", 'warn');
            }
        };
        init();
    }, []);

    const addLog = (msg: string, type: 'info' | 'warn' | 'brain') => {
        const time = new Date().toLocaleTimeString();
        setLogs((prev: any[]) => [{ time, msg, type }, ...prev].slice(0, 50));
    };

    const handleKillSwitch = async () => {
        addLog("MANUAL_OVERRIDE: Initiating Kill Switch...", 'warn');
        try {
            await triggerKillSwitch();
            addLog("KILL_SWITCH: All orders purged.", 'warn');
        } catch (e) {
            addLog("ERROR: Kill switch failed to propagate.", 'warn');
        }
    };

    return (
        <div className="min-h-screen p-6 grid grid-cols-12 gap-6 font-mono selection:bg-green-500 selection:text-black">
            {/* SECTION A: SYSTEM STATUS */}
            <div className="col-span-12 lg:col-span-3 border border-zinc-800 bg-zinc-900/50 p-4 rounded-sm flex flex-col justify-between">
                <div>
                    <h2 className="text-zinc-500 text-xs mb-4 uppercase tracking-widest flex items-center gap-2">
                        <Activity className="w-3 h-3" /> System Status
                    </h2>
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full animate-pulse ${status === 'online' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500'}`} />
                        <span className={status === 'online' ? 'text-green-500' : 'text-red-500'}>
                            {status === 'online' ? 'NEXUS_ONLINE' : 'NEXUS_DISCONNECTED'}
                        </span>
                    </div>
                </div>
                <div className="mt-8">
                    <p className="text-[10px] text-zinc-600 uppercase">Architecture: Sovereign Architecture 1.0</p>
                    <p className="text-[10px] text-zinc-600 uppercase">Security: Zero-Trust Logic Active</p>
                </div>
            </div>

            {/* SECTION B: THE EYE (CONSOLE) */}
            <div className="col-span-12 lg:col-span-6 border border-zinc-800 bg-zinc-950 p-4 rounded-sm h-[400px] flex flex-col">
                <h2 className="text-zinc-500 text-xs mb-4 uppercase tracking-widest flex items-center gap-2">
                    <Terminal className="w-3 h-3" /> The Eye [AI Analysis Console]
                </h2>
                <div className="flex-1 overflow-y-auto space-y-2 text-xs scrollbar-hide">
                    {logs.map((log: any, i: number) => (
                        <div key={i} className="flex gap-3">
                            <span className="text-zinc-700">[{log.time}]</span>
                            <span className={log.type === 'warn' ? 'text-red-500' : log.type === 'brain' ? 'text-blue-400' : 'text-green-600'}>
                                {log.msg}
                            </span>
                        </div>
                    ))}
                    {logs.length === 0 && <div className="text-zinc-800 animate-pulse">Waiting for signals...</div>}
                </div>
            </div>

            {/* SECTION C: MANUAL OVERRIDE */}
            <div className="col-span-12 lg:col-span-3 border border-red-900/30 bg-red-950/10 p-4 rounded-sm flex flex-col items-center justify-center gap-6">
                <h2 className="text-red-900 text-xs uppercase tracking-widest flex items-center gap-2 font-bold">
                    <ShieldAlert className="w-3 h-3" /> Manual Override
                </h2>
                <button
                    onClick={handleKillSwitch}
                    className="group relative w-32 h-32 rounded-full border-4 border-red-900 bg-red-950 flex flex-col items-center justify-center transition-all hover:scale-105 active:scale-95 hover:border-red-600 hover:shadow-[0_0_30px_rgba(220,38,38,0.5)]"
                >
                    <Power className="w-8 h-8 text-red-600 group-hover:text-red-500" />
                    <span className="text-xs font-bold text-red-900 group-hover:text-red-600 mt-2">KILL</span>
                </button>
                <p className="text-[10px] text-red-900 text-center uppercase leading-tight">
                    Warning: Activating the Kill Switch will purge all orders and stop the body execution logic.
                </p>
            </div>

            {/* SECTION D: MARKET FEED */}
            <div className="col-span-12 border border-zinc-800 bg-zinc-900/30 p-4 rounded-sm h-[200px]">
                <h2 className="text-zinc-500 text-xs mb-2 uppercase tracking-widest flex items-center gap-2">
                    <Zap className="w-3 h-3" /> Market Feed [BTC/USDT]
                </h2>
                <div className="w-full h-32">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={priceData}>
                            <Line type="monotone" dataKey="price" stroke="#22c55e" strokeWidth={1} dot={false} />
                            <XAxis dataKey="name" hide />
                            <YAxis domain={['auto', 'auto']} hide />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#09090b', border: '1px solid #27272a', fontSize: '10px' }}
                                itemStyle={{ color: '#22c55e' }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;

import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Cpu } from 'lucide-react';

export const TradeForm = ({ onTrade, balance, autoPilot, setAutoPilot }) => {
    const [volume, setVolume] = useState(0.01);

    return (
        <div className="glass-panel rounded-3xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
                <span className="text-xs font-bold text-white tracking-widest">ORDER ENTRY</span>
                <button
                    onClick={() => setAutoPilot(!autoPilot)}
                    className={`text-[10px] px-3 py-1 rounded-full border transition-all flex items-center gap-2 ${autoPilot ? 'bg-purple-500/20 border-purple-500 text-purple-400 shadow-[0_0_10px_rgba(168,85,247,0.3)]' : 'border-zinc-700 text-zinc-500'}`}
                >
                    <Cpu size={12} /> {autoPilot ? 'AI PILOT: ON' : 'AI PILOT: OFF'}
                </button>
            </div>

            <div className="mb-4">
                <label className="text-[10px] text-zinc-500 uppercase font-bold mb-2 block">Volume (Lots)</label>
                <div className="flex items-center bg-black/30 rounded-xl border border-white/10 p-1">
                    <button onClick={() => setVolume(Math.max(0.01, volume - 0.01))} className="w-10 h-10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/5 rounded-lg">-</button>
                    <input
                        type="number"
                        value={volume.toFixed(2)}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="flex-1 bg-transparent text-center font-mono text-white outline-none"
                    />
                    <button onClick={() => setVolume(volume + 0.01)} className="w-10 h-10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/5 rounded-lg">+</button>
                </div>
            </div>

            <div className="space-y-3">
                <button
                    onClick={() => onTrade('BUY', volume)}
                    className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-black rounded-xl shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                    <ArrowUpRight strokeWidth={3} /> BUY / LONG
                </button>
                <button
                    onClick={() => onTrade('SELL', volume)}
                    className="w-full py-4 bg-rose-500 hover:bg-rose-400 text-white font-black rounded-xl shadow-[0_0_20px_rgba(244,63,94,0.3)] transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                    <ArrowDownRight strokeWidth={3} /> SELL / SHORT
                </button>
            </div>

            <div className="mt-6 pt-6 border-t border-white/5 grid grid-cols-2 gap-4">
                <div className="text-center">
                    <div className="text-[10px] text-zinc-500 uppercase">Available</div>
                    <div className="font-mono text-white">${balance.toLocaleString()}</div>
                </div>
                <div className="text-center">
                    <div className="text-[10px] text-zinc-500 uppercase">Leverage</div>
                    <div className="font-mono text-amber-500">20x</div>
                </div>
            </div>
        </div>
    );
};

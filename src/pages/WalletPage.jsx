import React from 'react';
import { Download, Send, Repeat } from 'lucide-react';

const QuickAction = ({ icon: Icon, label, color, onClick }) => (
    <button onClick={onClick} className="flex flex-col items-center gap-2 group w-full">
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${color} shadow-lg group-hover:scale-105 transition-all border border-white/10`}>
            <Icon size={24} className="text-white" />
        </div>
        <span className="text-[10px] text-zinc-400 font-medium group-hover:text-white transition-colors">{label}</span>
    </button>
);

export const WalletPage = () => {
    const balance = 24593.42;

    return (
        <div className="max-w-2xl mx-auto space-y-8 animate-fadeIn p-6">
            <div className="bg-gradient-to-br from-zinc-900 to-black border border-white/10 rounded-[32px] p-8 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 blur-[80px] rounded-full pointer-events-none"></div>
                <div className="relative z-10 text-center">
                    <div className="text-zinc-500 text-xs font-bold uppercase tracking-[0.2em] mb-2">Total Balance</div>
                    <div className="text-6xl font-mono font-black text-white mb-8 tracking-tighter text-glow">${balance.toLocaleString()}</div>
                    <div className="flex justify-center gap-6">
                        <QuickAction icon={Download} label="Deposit" color="bg-emerald-600" onClick={() => { }} />
                        <QuickAction icon={Send} label="Send" color="bg-blue-600" onClick={() => { }} />
                        <QuickAction icon={Repeat} label="Swap" color="bg-purple-600" onClick={() => { }} />
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                <h3 className="text-xs font-bold text-zinc-500 uppercase ml-4 mb-2">Assets</h3>
                {[
                    { n: 'Bitcoin', s: 'BTC', b: '0.424', v: '$37,500', c: 'text-orange-500' },
                    { n: 'Tether', s: 'USDT', b: '12,450', v: '$12,450', c: 'text-emerald-500' },
                    { n: 'M-Pesa', s: 'KES', b: '45,200', v: '$350', c: 'text-green-600' }
                ].map((a, i) => (
                    <div key={i} className="flex items-center justify-between p-4 glass-panel rounded-2xl hover:bg-white/5 transition-colors cursor-pointer">
                        <div className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-full bg-white/5 flex items-center justify-center font-bold ${a.c}`}>{a.s[0]}</div>
                            <div>
                                <div className="font-bold text-white text-sm">{a.n}</div>
                                <div className="text-xs text-zinc-500 font-mono">{a.b} {a.s}</div>
                            </div>
                        </div>
                        <div className="text-right font-mono font-bold text-white text-sm">{a.v}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

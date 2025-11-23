import React from 'react';
import { Layers } from 'lucide-react';

export const PositionTable = ({ trades }) => {
    return (
        <div className="flex-1 glass-panel rounded-3xl p-0 overflow-hidden flex flex-col min-h-[300px]">
            <div className="p-5 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                <span className="text-xs font-bold text-white tracking-widest">OPEN POSITIONS</span>
                <span className="text-xs font-mono text-zinc-500">{trades.length}</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {trades.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-700 gap-3 opacity-50">
                        <Layers size={32} />
                        <span className="text-xs font-mono">NO ACTIVE PROTOCOLS</span>
                    </div>
                )}
                {trades.map((t) => (
                    <div key={t.id} className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors group">
                        <div className="flex justify-between items-center mb-1">
                            <div className="flex items-center gap-2">
                                <span className="font-bold text-white text-sm">{t.ticker}</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${t.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>{t.type}</span>
                            </div>
                            <span className={`font-mono text-sm font-bold ${parseFloat(t.pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {parseFloat(t.pnl) > 0 ? '+' : ''}{t.pnl}
                            </span>
                        </div>
                        <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                            <span>#{t.ticket || t.id}</span>
                            <span>Entry: {t.entry.toLocaleString()}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

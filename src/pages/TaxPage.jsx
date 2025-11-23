import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const TaxPage = () => {
    const taxLiability = 1250.40;
    const taxSaved = 450.20;

    return (
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 animate-fadeIn p-6">
            <div className="glass-panel p-8 rounded-3xl">
                <div className="text-xs text-zinc-500 font-bold uppercase tracking-widest mb-4">Tax Liability</div>
                <div className="text-5xl font-mono text-white font-light mb-2">${taxLiability.toFixed(2)}</div>
                <div className="text-xs text-rose-400 flex items-center gap-2"><AlertTriangle size={12} /> Estimate</div>
            </div>
            <div className="bg-gradient-to-br from-amber-900/20 to-black border border-amber-500/20 p-8 rounded-3xl">
                <div className="text-xs text-amber-500 font-bold uppercase tracking-widest mb-4">Optimized Savings</div>
                <div className="text-5xl font-mono text-emerald-400 font-light mb-2">-${taxSaved.toFixed(2)}</div>
                <div className="text-xs text-zinc-400 font-mono">Harvesting Protocol Active</div>
            </div>
        </div>
    );
};

import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const TaxPage = () => {
    const taxLiability = 1250.40;
    const taxSaved = 450.20;

    const [generating, setGenerating] = React.useState(false);

    const handleGenerateReport = () => {
        setGenerating(true);
        setTimeout(() => {
            setGenerating(false);
            alert("Tax Report (PDF) Downloaded Successfully!");
        }, 2000);
    };

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

            <div className="md:col-span-2 flex justify-center mt-8">
                <button 
                    onClick={handleGenerateReport}
                    disabled={generating}
                    className="bg-nexus-border hover:bg-white/10 text-white px-8 py-3 rounded-xl font-bold transition-colors flex items-center gap-2"
                >
                    {generating ? 'Compiling Data...' : 'Download Tax Report (PDF)'}
                </button>
            </div>
        </div>
    );
};

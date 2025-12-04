import React from 'react';
import { CheckCircle } from 'lucide-react';

export const BrokerSelector = ({ brokers, selected, onSelect }) => {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {brokers.map(broker => (
                <button
                    key={broker.id}
                    onClick={() => onSelect(broker)}
                    className={`relative p-4 rounded-xl border transition-all duration-300 flex flex-col items-center gap-3 group ${selected?.id === broker.id
                            ? 'bg-white/10 border-nexus-gold shadow-[0_0_15px_rgba(252,213,53,0.2)]'
                            : 'bg-black/40 border-white/5 hover:bg-white/5 hover:border-white/10'
                        }`}
                >
                    {selected?.id === broker.id && (
                        <div className="absolute top-2 right-2 text-nexus-gold">
                            <CheckCircle size={16} fill="currentColor" className="text-black" />
                        </div>
                    )}

                    <div className="w-12 h-12 rounded-full bg-white p-2 flex items-center justify-center overflow-hidden">
                        {/* Placeholder for actual logos if images fail */}
                        <span className="text-black font-bold text-xs">{broker.name.substring(0, 2).toUpperCase()}</span>
                    </div>

                    <div className="text-center">
                        <h4 className="text-white font-bold text-sm">{broker.name}</h4>
                        <span className="text-[10px] text-nexus-subtext block">Min Dep: ${broker.minDeposit}</span>
                    </div>
                </button>
            ))}
        </div>
    );
};

import React, { useState } from 'react';
import { Globe, Server } from 'lucide-react';

export const BrokersPage = () => {
    const [brokerStatus, setBrokerStatus] = useState({ fxpesa: false, mt5: false });

    const toggleBroker = (b) => {
        setBrokerStatus(p => ({ ...p, [b]: !p[b] }));
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn p-6">
            {['fxpesa', 'mt5'].map(b => (
                <div key={b} className="glass-panel p-6 rounded-3xl flex items-center justify-between group hover:border-white/10 transition-all">
                    <div className="flex items-center gap-5">
                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-xl ${b === 'fxpesa' ? 'bg-blue-500/10 text-blue-500' : 'bg-orange-500/10 text-orange-500'}`}>
                            {b === 'fxpesa' ? <Globe /> : <Server />}
                        </div>
                        <div>
                            <h3 className="font-bold text-white text-lg capitalize">{b === 'fxpesa' ? 'FxPesa Direct' : 'MetaTrader 5'}</h3>
                            <div className="flex items-center gap-2 mt-1">
                                <div className={`w-1.5 h-1.5 rounded-full ${brokerStatus[b] ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                                <span className="text-xs text-zinc-500 font-mono">{brokerStatus[b] ? 'CONNECTED' : 'DISCONNECTED'}</span>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={() => toggleBroker(b)}
                        className={`px-6 py-3 rounded-xl text-xs font-bold tracking-wider border transition-all ${brokerStatus[b] ? 'border-emerald-500 text-emerald-500 bg-emerald-500/10' : 'border-zinc-700 text-zinc-400 hover:bg-white/5'}`}
                    >
                        {brokerStatus[b] ? 'LINKED' : 'CONNECT'}
                    </button>
                </div>
            ))}
        </div>
    );
};

import React from 'react';

export const OrderBook = ({ asks, bids, currentPrice, trend }) => {
    return (
        <div className="glass-panel rounded-3xl p-5 h-full flex flex-col">
            <div className="flex justify-between text-[10px] text-zinc-500 font-mono mb-3 uppercase tracking-wider">
                <span>Price (USD)</span><span>Amount</span><span>Total</span>
            </div>
            <div className="flex-1 overflow-hidden space-y-1 font-mono text-xs">
                {/* ASKS (Sells) - Red */}
                <div className="flex flex-col-reverse">
                    {asks.slice(0, 8).map((a, i) => (
                        <div key={i} className="flex justify-between relative group cursor-pointer hover:bg-white/5">
                            <div className="absolute right-0 top-0 bottom-0 bg-rose-500/10 transition-all duration-300" style={{ width: `${Math.min(a.a * 20, 100)}%` }}></div>
                            <span className="text-rose-400 relative z-10 group-hover:text-rose-300">{a.p.toFixed(2)}</span>
                            <span className="text-zinc-400 relative z-10">{a.a.toFixed(4)}</span>
                            <span className="text-zinc-500 relative z-10">{(a.p * a.a).toFixed(0)}</span>
                        </div>
                    ))}
                </div>

                {/* Current Price */}
                <div className={`text-center py-3 font-bold text-lg border-y border-white/5 my-2 ${trend >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    ${currentPrice.toFixed(2)}
                    <span className="text-xs ml-2 opacity-70">{trend >= 0 ? '↑' : '↓'}</span>
                </div>

                {/* BIDS (Buys) - Green */}
                <div>
                    {bids.slice(0, 8).map((b, i) => (
                        <div key={i} className="flex justify-between relative group cursor-pointer hover:bg-white/5">
                            <div className="absolute right-0 top-0 bottom-0 bg-emerald-500/10 transition-all duration-300" style={{ width: `${Math.min(b.a * 20, 100)}%` }}></div>
                            <span className="text-emerald-400 relative z-10 group-hover:text-emerald-300">{b.p.toFixed(2)}</span>
                            <span className="text-zinc-400 relative z-10">{b.a.toFixed(4)}</span>
                            <span className="text-zinc-500 relative z-10">{(b.p * b.a).toFixed(0)}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

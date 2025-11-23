import React, { useState } from 'react';
import { ChevronDown, MoreHorizontal, ArrowUp, ArrowDown, Info } from 'lucide-react';

export const FuturesPage = () => {
    const [side, setSide] = useState('buy');
    const [leverage, setLeverage] = useState(20);
    const [price, setPrice] = useState('64230.10');
    const [amount, setAmount] = useState('');

    return (
        <div className="bg-nexus-black min-h-screen pb-20">
            {/* HEADER */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-nexus-border">
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-nexus-text flex items-center gap-1">
                        BTCUSDT <span className="text-xs bg-nexus-border px-1 rounded text-nexus-subtext">Perp</span> <ChevronDown size={16} className="text-nexus-subtext" />
                    </h2>
                    <span className="text-xs text-nexus-green bg-nexus-green/10 px-1.5 py-0.5 rounded">+0.85%</span>
                </div>
                <div className="flex gap-4 text-nexus-subtext">
                    <MoreHorizontal size={20} />
                </div>
            </div>

            <div className="flex p-2 gap-2">
                {/* ORDER BOOK (LEFT) */}
                <div className="w-[40%] text-xs">
                    <div className="flex justify-between text-nexus-subtext mb-1 px-1">
                        <span>Price</span>
                        <span>Amount</span>
                    </div>
                    {/* Asks (Sells) */}
                    <div className="flex flex-col gap-0.5 mb-2">
                        {[64235, 64234, 64233, 64232, 64231].map((p, i) => (
                            <div key={i} className="flex justify-between px-1 relative">
                                <span className="text-nexus-red relative z-10">{p}.00</span>
                                <span className="text-nexus-text relative z-10">0.{(i + 1) * 123}</span>
                                <div className="absolute right-0 top-0 bottom-0 bg-nexus-red/10" style={{ width: `${Math.random() * 100}%` }}></div>
                            </div>
                        ))}
                    </div>

                    <div className="text-lg font-bold text-nexus-green text-center my-2">64,230.10</div>

                    {/* Bids (Buys) */}
                    <div className="flex flex-col gap-0.5">
                        {[64229, 64228, 64227, 64226, 64225].map((p, i) => (
                            <div key={i} className="flex justify-between px-1 relative">
                                <span className="text-nexus-green relative z-10">{p}.00</span>
                                <span className="text-nexus-text relative z-10">0.{(i + 1) * 154}</span>
                                <div className="absolute right-0 top-0 bottom-0 bg-nexus-green/10" style={{ width: `${Math.random() * 100}%` }}></div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* TRADE FORM (RIGHT) */}
                <div className="flex-1 pl-2">
                    <div className="flex gap-2 mb-3">
                        <button className="bg-nexus-border text-nexus-text text-xs px-2 py-1 rounded flex-1">Cross</button>
                        <button className="bg-nexus-border text-nexus-text text-xs px-2 py-1 rounded flex-1">{leverage}x</button>
                    </div>

                    <div className="flex bg-nexus-border rounded-lg p-0.5 mb-4">
                        <button
                            onClick={() => setSide('buy')}
                            className={`flex-1 py-1.5 text-sm font-bold rounded-md transition-colors ${side === 'buy' ? 'bg-nexus-green text-white' : 'text-nexus-subtext'}`}
                        >
                            Buy
                        </button>
                        <button
                            onClick={() => setSide('sell')}
                            className={`flex-1 py-1.5 text-sm font-bold rounded-md transition-colors ${side === 'sell' ? 'bg-nexus-red text-white' : 'text-nexus-subtext'}`}
                        >
                            Sell
                        </button>
                    </div>

                    <div className="flex items-center justify-between mb-3">
                        <div className="bg-nexus-border/50 px-3 py-1 rounded text-xs text-nexus-subtext flex items-center gap-1">
                            Limit <ChevronDown size={12} />
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="bg-nexus-border rounded px-3 py-2 flex items-center justify-between">
                            <input
                                type="text"
                                value={price}
                                onChange={(e) => setPrice(e.target.value)}
                                className="bg-transparent text-nexus-text text-sm font-bold w-full outline-none text-right"
                            />
                            <span className="text-xs text-nexus-subtext ml-2">USDT</span>
                        </div>
                        <div className="bg-nexus-border rounded px-3 py-2 flex items-center justify-between">
                            <input
                                type="text"
                                placeholder="Size"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="bg-transparent text-nexus-text text-sm font-bold w-full outline-none text-right"
                            />
                            <span className="text-xs text-nexus-subtext ml-2">BTC</span>
                        </div>

                        {/* Leverage Slider */}
                        <div className="px-1">
                            <div className="flex justify-between text-[10px] text-nexus-subtext mb-1">
                                <span>1x</span>
                                <span>{leverage}x</span>
                                <span>125x</span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="125"
                                value={leverage}
                                onChange={(e) => setLeverage(e.target.value)}
                                className="w-full h-1 bg-nexus-border rounded-lg appearance-none cursor-pointer"
                            />
                        </div>

                        <div className="flex justify-between text-xs text-nexus-subtext mt-2">
                            <span>Max Buy</span>
                            <span className="text-nexus-text">0.42 BTC</span>
                        </div>

                        <button className={`w-full py-3 rounded-lg font-bold text-white mt-4 ${side === 'buy' ? 'bg-nexus-green' : 'bg-nexus-red'}`}>
                            {side === 'buy' ? 'Buy / Long' : 'Sell / Short'}
                        </button>
                    </div>
                </div>
            </div>

            {/* POSITIONS */}
            <div className="mt-4 px-4">
                <div className="flex items-center gap-4 mb-4 border-b border-nexus-border pb-2">
                    <h3 className="font-bold text-nexus-text text-sm border-b-2 border-nexus-yellow pb-2 -mb-2.5">Positions (1)</h3>
                    <h3 className="font-bold text-nexus-subtext text-sm">Orders (0)</h3>
                </div>

                <div className="bg-nexus-card p-4 rounded-lg border-l-4 border-nexus-green">
                    <div className="flex justify-between items-start mb-2">
                        <div>
                            <div className="font-bold text-nexus-text text-lg flex items-center gap-2">
                                BTCUSDT <span className="text-xs bg-nexus-border px-1.5 py-0.5 rounded text-nexus-green">Long</span> <span className="text-xs text-nexus-subtext">20x</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-nexus-green font-bold">+125.40</div>
                            <div className="text-nexus-green text-xs">+12.5%</div>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-y-2 text-xs">
                        <div className="text-nexus-subtext">Size (USDT)</div>
                        <div className="text-right text-nexus-text">12,450.00</div>
                        <div className="text-nexus-subtext">Entry Price</div>
                        <div className="text-right text-nexus-text">63,850.20</div>
                        <div className="text-nexus-subtext">Mark Price</div>
                        <div className="text-right text-nexus-text">64,230.10</div>
                        <div className="text-nexus-subtext">Liq. Price</div>
                        <div className="text-right text-nexus-yellow">61,200.00</div>
                    </div>
                    <button className="w-full mt-3 bg-nexus-border text-nexus-text py-2 rounded font-bold text-xs">Close Position</button>
                </div>
            </div>
        </div>
    );
};

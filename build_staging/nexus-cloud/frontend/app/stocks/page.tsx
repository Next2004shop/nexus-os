"use client";
import { Card } from "@/components/ui/Card";

const stocks = [
    { symbol: 'AAPL', name: 'Apple Inc.', price: '220.50', change: '+0.8%', isPositive: true, category: 'tech' },
    { symbol: 'TSLA', name: 'Tesla Inc.', price: '175.20', change: '-1.2%', isPositive: false, category: 'auto' },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', price: '120.00', change: '+3.4%', isPositive: true, category: 'tech' },
    { symbol: 'MSFT', name: 'Microsoft Corp.', price: '415.30', change: '+0.5%', isPositive: true, category: 'tech' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: '140.25', change: '-0.3%', isPositive: false, category: 'tech' },
    { symbol: 'AMZN', name: 'Amazon.com', price: '178.90', change: '+1.1%', isPositive: true, category: 'ecom' },
];

export default function StocksPage() {
    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Global Markets</h1>
                <p className="text-nexus-subtext">Real-time stock prices and market data</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {stocks.map((stock) => (
                    <Card key={stock.symbol} className="p-6 hover:scale-[1.02] transition-transform cursor-pointer group relative">
                        {/* Glow effect */}
                        <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity ${stock.isPositive ? 'bg-nexus-green/5' : 'bg-nexus-red/5'}`} />

                        <div className="relative z-10">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-2xl font-bold font-mono">{stock.symbol}</h3>
                                        <span className="px-2 py-0.5 rounded-md text-xs font-bold uppercase bg-white/10 text-nexus-subtext">{stock.category}</span>
                                    </div>
                                    <p className="text-sm text-nexus-subtext">{stock.name}</p>
                                </div>
                                <div className="text-right">
                                    <div className={`text-xl font-bold font-mono ${stock.isPositive ? 'text-nexus-green' : 'text-nexus-red'}`}>{stock.change}</div>
                                </div>
                            </div>

                            <div className="text-4xl font-bold font-mono mb-4">${stock.price}</div>

                            {/* Visual Chart Bars */}
                            <div className="h-16 flex items-end justify-between gap-1 opacity-50">
                                {[...Array(20)].map((_, i) => (
                                    <div
                                        key={i}
                                        className={`flex-1 rounded-t ${stock.isPositive ? 'bg-nexus-green' : 'bg-nexus-red'}`}
                                        style={{ height: `${Math.random() * 80 + 20}%` }}
                                    />
                                ))}
                            </div>

                            <div className="mt-4 flex gap-2">
                                <button className={`flex-1 py-3 rounded-lg text-sm font-bold transition-all bg-nexus-green/10 hover:bg-nexus-green/20 border border-nexus-green/30 text-nexus-green`}>BUY</button>
                                <button className={`flex-1 py-3 rounded-lg text-sm font-bold transition-all bg-nexus-red/10 hover:bg-nexus-red/20 border border-nexus-red/30 text-nexus-red`}>SELL</button>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
}

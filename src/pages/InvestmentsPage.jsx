import React from 'react';
import { TrendingUp, PieChart, Layers, ArrowUpRight } from 'lucide-react';

const StockCard = ({ symbol, name, price, change }) => (
    <div className="bg-nexus-card border border-nexus-border p-4 rounded-xl hover:border-nexus-blue/50 transition-all cursor-pointer">
        <div className="flex justify-between items-start mb-2">
            <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center font-bold text-white">
                {symbol[0]}
            </div>
            <div className={`text-sm font-bold ${change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                {change > 0 ? '+' : ''}{change}%
            </div>
        </div>
        <div className="text-white font-bold text-lg">{symbol}</div>
        <div className="text-nexus-subtext text-xs mb-2">{name}</div>
        <div className="text-white font-mono">${price}</div>
    </div>
);

const InvestmentsPage = () => {
    return (
        <div className="p-6 animate-fadeIn pb-24 md:pb-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-1">Asset Management</h1>
                <p className="text-nexus-subtext text-sm">Diversified portfolio tracking and staking.</p>
            </div>

            {/* STAKING SECTION */}
            <div className="mb-10">
                <div className="flex items-center gap-2 text-white font-bold text-lg mb-4">
                    <Layers className="text-nexus-blue" />
                    <h2>High Yield Staking</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-nexus-blue/20 to-transparent border border-nexus-blue/30 p-6 rounded-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 bg-nexus-blue text-black text-xs font-bold px-2 py-1 rounded-bl-lg">
                            12.5% APY
                        </div>
                        <div className="text-nexus-blue font-bold text-xl mb-1">USDT Vault</div>
                        <p className="text-nexus-subtext text-xs mb-4">Stablecoin Yield Farming</p>
                        <button className="w-full bg-nexus-blue text-black font-bold py-2 rounded-lg text-sm hover:bg-cyan-400 transition-colors">
                            Stake Now
                        </button>
                    </div>
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                        <div className="text-white font-bold text-xl mb-1">ETH 2.0</div>
                        <p className="text-nexus-subtext text-xs mb-4">Validator Staking (4.8% APY)</p>
                        <button className="w-full bg-white/5 text-white font-bold py-2 rounded-lg text-sm hover:bg-white/10 transition-colors">
                            Stake Now
                        </button>
                    </div>
                </div>
            </div>

            {/* STOCKS SECTION */}
            <div>
                <div className="flex items-center gap-2 text-white font-bold text-lg mb-4">
                    <TrendingUp className="text-nexus-green" />
                    <h2>Equity Portfolio</h2>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    <StockCard symbol="AAPL" name="Apple Inc." price="185.92" change={1.25} />
                    <StockCard symbol="TSLA" name="Tesla, Inc." price="242.50" change={-0.85} />
                    <StockCard symbol="NVDA" name="NVIDIA Corp." price="485.09" change={2.10} />
                    <StockCard symbol="MSFT" name="Microsoft" price="375.20" change={0.55} />
                    <StockCard symbol="GOOGL" name="Alphabet Inc." price="138.40" change={0.90} />
                </div>
            </div>
        </div>
    );
};

export default InvestmentsPage;

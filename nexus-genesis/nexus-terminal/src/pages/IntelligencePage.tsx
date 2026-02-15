import React from 'react';
import { Brain, TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react';

const MOCK_SIGNALS = [
    { symbol: 'XAUUSD', direction: 'BUY', confidence: 87, timeframe: 'H4', strategy: 'Momentum' },
    { symbol: 'EURUSD', direction: 'SELL', confidence: 72, timeframe: 'H1', strategy: 'Mean Reversion' },
    { symbol: 'NAS100', direction: 'BUY', confidence: 64, timeframe: 'D1', strategy: 'Trend Following' },
    { symbol: 'BTCUSD', direction: 'NEUTRAL', confidence: 45, timeframe: 'H4', strategy: 'Volatility' },
];

const MARKET_REGIME = {
    current: 'TRENDING',
    direction: 'BULLISH',
    strength: 72,
    volatility_index: 18.5,
    regime_duration: '3d 14h',
};

function ConfidenceBar({ value }: { value: number }) {
    const color = value >= 80 ? 'bg-nexus-green' : value >= 60 ? 'bg-nexus-accent' : value >= 40 ? 'bg-nexus-amber' : 'bg-nexus-red';
    return (
        <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 bg-nexus-bg rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
            </div>
            <span className="text-xs font-mono w-8">{value}%</span>
        </div>
    );
}

export default function IntelligencePage() {
    return (
        <div className="space-y-6">
            {/* Market Regime */}
            <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Brain className="w-4 h-4 text-nexus-accent" />
                        <h3 className="text-xs text-nexus-muted uppercase tracking-wider">Market Regime</h3>
                    </div>
                    <span className="text-xs text-nexus-muted font-mono">Duration: {MARKET_REGIME.regime_duration}</span>
                </div>

                <div className="grid grid-cols-3 gap-6">
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Regime</div>
                        <div className="text-lg font-semibold text-nexus-text font-mono">{MARKET_REGIME.current}</div>
                    </div>
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Direction</div>
                        <div className={`text-lg font-semibold font-mono ${MARKET_REGIME.direction === 'BULLISH' ? 'text-nexus-green' : 'text-nexus-red'}`}>
                            {MARKET_REGIME.direction}
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Strength</div>
                        <div className="text-lg font-semibold text-nexus-text font-mono">{MARKET_REGIME.strength}%</div>
                    </div>
                </div>
            </div>

            {/* Volatility Index */}
            <div className="stat-card">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Volatility Index</div>
                        <div className="text-2xl font-semibold text-nexus-text font-mono">{MARKET_REGIME.volatility_index}</div>
                    </div>
                    <Zap className={`w-5 h-5 ${MARKET_REGIME.volatility_index > 25 ? 'text-nexus-red' : MARKET_REGIME.volatility_index > 15 ? 'text-nexus-amber' : 'text-nexus-green'}`} />
                </div>
                <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden mt-3">
                    <div
                        className={`h-full rounded-full ${MARKET_REGIME.volatility_index > 25 ? 'bg-nexus-red' : MARKET_REGIME.volatility_index > 15 ? 'bg-nexus-amber' : 'bg-nexus-green'}`}
                        style={{ width: `${Math.min(MARKET_REGIME.volatility_index / 40 * 100, 100)}%` }}
                    />
                </div>
                <div className="flex justify-between text-[10px] text-nexus-muted mt-1">
                    <span>LOW</span>
                    <span>MEDIUM</span>
                    <span>HIGH</span>
                </div>
            </div>

            {/* Signal List */}
            <div>
                <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-3">Active Signals</h3>
                <div className="bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th className="pl-4">Symbol</th>
                                <th>Direction</th>
                                <th>Confidence</th>
                                <th>Timeframe</th>
                                <th className="pr-4">Strategy</th>
                            </tr>
                        </thead>
                        <tbody>
                            {MOCK_SIGNALS.map((sig, i) => (
                                <tr key={i}>
                                    <td className="pl-4 font-semibold text-nexus-text">{sig.symbol}</td>
                                    <td>
                                        <span className={`inline-flex items-center gap-1 ${sig.direction === 'BUY' ? 'text-nexus-green' :
                                                sig.direction === 'SELL' ? 'text-nexus-red' : 'text-nexus-muted'
                                            }`}>
                                            {sig.direction === 'BUY' ? <TrendingUp className="w-3 h-3" /> :
                                                sig.direction === 'SELL' ? <TrendingDown className="w-3 h-3" /> :
                                                    <Minus className="w-3 h-3" />}
                                            {sig.direction}
                                        </span>
                                    </td>
                                    <td><ConfidenceBar value={sig.confidence} /></td>
                                    <td className="text-nexus-muted">{sig.timeframe}</td>
                                    <td className="pr-4 text-nexus-muted">{sig.strategy}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

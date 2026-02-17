import React, { useEffect, useState } from 'react';
import { Brain, TrendingUp, TrendingDown, Minus, Zap, RefreshCw } from 'lucide-react';
import api from '../api/client';

interface Signal {
    symbol: string;
    side: string; // "BUY" | "SELL" | "WAIT"
    confidence: number;
    reasoning: string;
    timestamp: string;
}

interface IntelligenceData {
    timestamp: string | null;
    regime: string;
    volatility: string;
    signals: Signal[];
    ai_active: boolean;
}

function ConfidenceBar({ value }: { value: number }) {
    const color = value >= 80 ? 'bg-nexus-green' : value >= 60 ? 'bg-nexus-accent' : value >= 40 ? 'bg-nexus-amber' : 'bg-nexus-red';
    return (
        <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 bg-nexus-bg rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full ${color} w-[var(--prog-width)]`}
                    style={{ '--prog-width': `${value * 100}%` } as React.CSSProperties}
                />
            </div>
            <span className="text-xs font-mono w-8">{(value * 100).toFixed(0)}%</span>
        </div>
    );
}

export default function IntelligencePage() {
    const [data, setData] = useState<IntelligenceData | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const res = await api.get('/api/intelligence/latest');
            setData(res.data);
        } catch (err) {
            console.error("Failed to fetch intelligence", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // 10s poll
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) return <div className="p-8 text-nexus-muted font-mono animate-pulse">Connecting to Neural Engine...</div>;

    // Default safe values if data is null or initial state
    const regime = data?.regime || "OFFLINE";
    const volatility = data?.volatility || "UNKNOWN";
    const signals = data?.signals || [];
    const isAiActive = data?.ai_active || false;

    return (
        <div className="space-y-6">
            {/* Market Regime */}
            <div className="stat-card">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Brain className={`w-4 h-4 ${isAiActive ? 'text-nexus-accent' : 'text-nexus-muted'}`} />
                        <h3 className="text-xs text-nexus-muted uppercase tracking-wider">Market Regime</h3>
                    </div>
                    <span className="text-xs text-nexus-muted font-mono">
                        AI Status: {isAiActive ? <span className="text-nexus-green">ACTIVE</span> : <span className="text-nexus-red">OFFLINE</span>}
                    </span>
                </div>

                <div className="grid grid-cols-3 gap-6">
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Current State</div>
                        <div className="text-lg font-semibold text-nexus-text font-mono">{regime}</div>
                    </div>
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Bias</div>
                        <div className={`text-lg font-semibold font-mono ${regime.includes('UP') ? 'text-nexus-green' :
                            regime.includes('DOWN') ? 'text-nexus-red' : 'text-nexus-muted'
                            }`}>
                            {regime.includes('UP') ? 'BULLISH' : regime.includes('DOWN') ? 'BEARISH' : 'NEUTRAL'}
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-nexus-muted mb-1">Volatility</div>
                        <div className={`text-lg font-semibold text-nexus-text font-mono ${volatility === 'HIGH' ? 'text-nexus-red' : volatility === 'NORMAL' ? 'text-nexus-green' : 'text-nexus-muted'
                            }`}>{volatility}</div>
                    </div>
                </div>
            </div>

            {/* Volatility Index (Visual) */}
            <div className="stat-card">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Volatility Meter</div>
                        <div className="text-2xl font-semibold text-nexus-text font-mono">{volatility}</div>
                    </div>
                    <Zap className={`w-5 h-5 ${volatility === 'HIGH' ? 'text-nexus-red animate-pulse' : 'text-nexus-green'}`} />
                </div>
                <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden mt-3">
                    <div
                        className={`h-full rounded-full transition-all duration-500 ${volatility === 'HIGH' ? 'bg-nexus-red w-full' : volatility === 'NORMAL' ? 'bg-nexus-green w-1/3' : 'bg-nexus-muted w-0'}`}
                    />
                </div>
            </div>

            {/* Signal List */}
            <div>
                <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-3">Active Signals</h3>
                <div className="bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden">
                    {signals.length === 0 ? (
                        <div className="p-8 text-center text-nexus-muted font-mono text-sm">
                            No active signals projected. Market analysis pending.
                        </div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th className="pl-4">Symbol</th>
                                    <th>Direction</th>
                                    <th>Confidence</th>
                                    <th className="pr-4">Reasoning</th>
                                </tr>
                            </thead>
                            <tbody>
                                {signals.map((sig, i) => (
                                    <tr key={i}>
                                        <td className="pl-4 font-semibold text-nexus-text">{sig.symbol}</td>
                                        <td>
                                            <span className={`inline-flex items-center gap-1 ${sig.side === 'BUY' ? 'text-nexus-green' :
                                                sig.side === 'SELL' ? 'text-nexus-red' : 'text-nexus-muted'
                                                }`}>
                                                {sig.side === 'BUY' ? <TrendingUp className="w-3 h-3" /> :
                                                    sig.side === 'SELL' ? <TrendingDown className="w-3 h-3" /> :
                                                        <Minus className="w-3 h-3" />}
                                                {sig.side}
                                            </span>
                                        </td>
                                        <td><ConfidenceBar value={sig.confidence} /></td>
                                        <td className="pr-4 text-nexus-muted truncate max-w-xs">{sig.reasoning}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            <div className="flex justify-end">
                <span className="text-[10px] text-nexus-muted font-mono">
                    Last analysis: {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : 'Waiting for data...'}
                </span>
            </div>
        </div>
    );
}

import React, { useState, useEffect, useCallback } from 'react';
import { Brain, TrendingUp, Shield, Activity, AlertTriangle, BarChart3 } from 'lucide-react';
import api from '../api/client';

interface EvolutionData {
    current_regime: {
        regime: string;
        classified_at: string | null;
    };
    strategy_weights: Record<string, number>;
    baseline_weights: Record<string, number>;
    risk_modulation: {
        multiplier: number;
        mode: string;
        history_count: number;
    };
    adaptation_state: {
        mode: string;
        protective_mode: boolean;
        cooldown_remaining: number;
        total_trades_analyzed: number;
        last_analysis_at: number;
    };
    health: {
        healthy: boolean;
        activity_throttle: number;
        issues: string[];
    };
    performance_30_trade: {
        win_rate: number;
        avg_r_multiple: number;
        profit_factor: number;
        drawdown_depth: number;
        total_pnl: number;
        avg_slippage: number;
        avg_execution_score: number;
        trade_count: number;
    };
}

const REGIME_COLORS: Record<string, string> = {
    TRENDING: 'text-blue-400',
    RANGING: 'text-yellow-400',
    HIGH_VOLATILITY: 'text-red-400',
    LOW_VOLATILITY: 'text-green-400',
    NEWS_DRIVEN: 'text-purple-400',
    UNKNOWN: 'text-zinc-500',
};

const MODE_COLORS: Record<string, string> = {
    NORMAL: 'text-green-500',
    CAUTIOUS: 'text-yellow-500',
    AGGRESSIVE: 'text-blue-400',
    PROTECTIVE: 'text-red-500',
    REDUCED_ACTIVITY: 'text-orange-400',
};

const SystemEvolution: React.FC = () => {
    const [data, setData] = useState<EvolutionData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        try {
            const response = await api.get('/api/meta/evolution');
            setData(response.data);
            setError(null);
        } catch (err) {
            setError('Meta-Intelligence offline');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading) {
        return (
            <div className="col-span-12 border border-zinc-800 bg-zinc-900/50 p-4 rounded-sm">
                <h2 className="text-zinc-500 text-xs uppercase tracking-widest flex items-center gap-2">
                    <Brain className="w-3 h-3" /> System Evolution
                </h2>
                <div className="text-zinc-700 text-xs mt-4 animate-pulse">Loading meta-intelligence...</div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="col-span-12 border border-zinc-800 bg-zinc-900/50 p-4 rounded-sm">
                <h2 className="text-zinc-500 text-xs uppercase tracking-widest flex items-center gap-2">
                    <Brain className="w-3 h-3" /> System Evolution
                </h2>
                <div className="text-zinc-600 text-xs mt-4">{error || 'No data'}</div>
            </div>
        );
    }

    const perf = data.performance_30_trade;
    const regime = data.current_regime;
    const risk = data.risk_modulation;
    const adapt = data.adaptation_state;
    const health = data.health;

    return (
        <div className="col-span-12 border border-zinc-800 bg-zinc-900/50 p-4 rounded-sm">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-zinc-500 text-xs uppercase tracking-widest flex items-center gap-2">
                    <Brain className="w-3 h-3" /> System Evolution
                </h2>
                {adapt.protective_mode && (
                    <span className="text-[10px] font-bold text-red-500 border border-red-900 px-2 py-0.5 rounded animate-pulse">
                        PROTECTIVE MODE
                    </span>
                )}
            </div>

            <div className="grid grid-cols-12 gap-4">
                {/* Current Regime */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Regime</div>
                    <div className={`text-sm font-bold ${REGIME_COLORS[regime.regime] || 'text-zinc-400'}`}>
                        {regime.regime}
                    </div>
                </div>

                {/* Adaptation Mode */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Adaptation</div>
                    <div className={`text-sm font-bold ${MODE_COLORS[risk.mode] || 'text-zinc-400'}`}>
                        {risk.mode}
                    </div>
                </div>

                {/* Risk Multiplier */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Risk Level</div>
                    <div className={`text-sm font-bold ${risk.multiplier < 0.8 ? 'text-red-400' : risk.multiplier > 1.05 ? 'text-blue-400' : 'text-green-500'}`}>
                        {(risk.multiplier * 100).toFixed(0)}%
                    </div>
                </div>

                {/* Health */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Health</div>
                    <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${health.healthy ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className={`text-sm font-bold ${health.healthy ? 'text-green-500' : 'text-red-400'}`}>
                            {health.healthy ? 'NOMINAL' : 'DEGRADED'}
                        </span>
                    </div>
                </div>

                {/* Trades Analyzed */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Trades</div>
                    <div className="text-sm font-bold text-zinc-300">
                        {adapt.total_trades_analyzed}
                    </div>
                </div>

                {/* Throttle */}
                <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1">Throttle</div>
                    <div className={`text-sm font-bold ${health.activity_throttle < 0.8 ? 'text-yellow-400' : 'text-green-500'}`}>
                        {(health.activity_throttle * 100).toFixed(0)}%
                    </div>
                </div>
            </div>

            {/* Strategy Weight Distribution */}
            <div className="mt-4 pt-3 border-t border-zinc-800">
                <div className="text-[10px] text-zinc-600 uppercase mb-2 flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" /> Strategy Weights
                </div>
                <div className="grid grid-cols-5 gap-2">
                    {Object.entries(data.strategy_weights).map(([name, weight]) => {
                        const baseline = data.baseline_weights[name] || weight;
                        const pctChange = ((weight - baseline) / baseline) * 100;
                        const isUp = pctChange > 1;
                        const isDown = pctChange < -1;
                        return (
                            <div key={name} className="text-center">
                                <div className="text-[9px] text-zinc-600 truncate">{name}</div>
                                <div className={`text-xs font-mono font-bold ${isUp ? 'text-green-400' : isDown ? 'text-red-400' : 'text-zinc-400'}`}>
                                    {(weight * 100).toFixed(1)}%
                                </div>
                                {pctChange !== 0 && (
                                    <div className={`text-[8px] ${isUp ? 'text-green-600' : isDown ? 'text-red-600' : 'text-zinc-700'}`}>
                                        {pctChange > 0 ? '+' : ''}{pctChange.toFixed(1)}%
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* 30-Trade Performance Snapshot */}
            <div className="mt-3 pt-3 border-t border-zinc-800">
                <div className="text-[10px] text-zinc-600 uppercase mb-2 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" /> 30-Trade Snapshot
                </div>
                <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
                    <StatBlock label="Win Rate" value={`${(perf.win_rate * 100).toFixed(1)}%`} warn={perf.win_rate < 0.45} />
                    <StatBlock label="Avg R" value={perf.avg_r_multiple.toFixed(2)} warn={perf.avg_r_multiple < 0} />
                    <StatBlock label="PF" value={perf.profit_factor.toFixed(2)} warn={perf.profit_factor < 1.0} />
                    <StatBlock label="P&L" value={perf.total_pnl.toFixed(2)} warn={perf.total_pnl < 0} />
                    <StatBlock label="Drawdown" value={perf.drawdown_depth.toFixed(2)} warn={perf.drawdown_depth > 100} />
                    <StatBlock label="Slippage" value={perf.avg_slippage.toFixed(4)} warn={perf.avg_slippage > 0.005} />
                    <StatBlock label="Exec Score" value={perf.avg_execution_score.toFixed(2)} warn={perf.avg_execution_score < 0.7} />
                    <StatBlock label="Count" value={String(perf.trade_count)} />
                </div>
            </div>

            {/* Health Issues */}
            {health.issues.length > 0 && (
                <div className="mt-3 pt-3 border-t border-zinc-800">
                    <div className="text-[10px] text-zinc-600 uppercase mb-1 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-yellow-500" /> Issues
                    </div>
                    {health.issues.map((issue, i) => (
                        <div key={i} className="text-[10px] text-yellow-600">{issue}</div>
                    ))}
                </div>
            )}
        </div>
    );
};

const StatBlock: React.FC<{ label: string; value: string; warn?: boolean }> = ({ label, value, warn }) => (
    <div>
        <div className="text-[9px] text-zinc-600 uppercase">{label}</div>
        <div className={`text-xs font-mono font-bold ${warn ? 'text-red-400' : 'text-zinc-300'}`}>
            {value}
        </div>
    </div>
);

export default SystemEvolution;

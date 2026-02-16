import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, RefreshCw, Activity } from 'lucide-react';
import api from '../api/client';

interface RiskStatus {
    risk_level: string;
    trading_enabled: boolean;
    circuit_breaker_active: boolean;
    drawdown: {
        current: number;
        warning_threshold: number;
        max_limit: number;
    };
    exposure: {
        current_pct: number;
        max_pct: number;
        max_position_pct: number;
    };
    equity: {
        current: number;
        peak: number;
        initial: number;
    };
    total_pnl_pct: number;
    consecutive_losses: number;
    open_positions_count: number;
    last_updated: string;
}

function RiskGauge({ label, value, max, unit = '%', warn = false, inverse = false }: {
    label: string; value: number; max: number; unit?: string; warn?: boolean; inverse?: boolean;
}) {
    // For drawdown/loss, value is usually positive in this context (e.g. 1.2% drawdown)
    // Inverse means higher is bad
    const pct = Math.min(Math.abs(value / max) * 100, 100);

    let color = 'bg-nexus-green';
    if (inverse) {
        color = pct > 80 ? 'bg-nexus-red' : pct > 50 ? 'bg-nexus-amber' : 'bg-nexus-green';
    } else {
        color = pct > 80 ? 'bg-nexus-green' : pct > 50 ? 'bg-nexus-amber' : 'bg-nexus-red';
    }

    return (
        <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-nexus-muted uppercase tracking-wider">{label}</span>
                {warn && <AlertTriangle className="w-3.5 h-3.5 text-nexus-amber" />}
            </div>
            <div className={`text-xl font-semibold font-mono ${inverse && pct > 80 ? 'text-nexus-red' : 'text-nexus-text'}`}>
                {value.toFixed(2)}{unit}
            </div>
            <div className="text-xs text-nexus-muted mt-1 mb-2 font-mono">
                Limit: {max.toFixed(2)}{unit}
            </div>
            <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

export default function RiskPage() {
    const [data, setData] = useState<RiskStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchRiskStatus = async () => {
        try {
            const res = await api.get('/api/risk/status');
            setData(res.data);
            setError(null);
        } catch (err: any) {
            console.error(err);
            setError('Failed to fetch risk status');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRiskStatus();
        const interval = setInterval(fetchRiskStatus, 5000); // 5s poll
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) return <div className="p-8 text-nexus-muted font-mono animate-pulse">Initializing risk engine connection...</div>;
    if (error) return <div className="p-8 text-nexus-red font-mono border border-nexus-red/20 rounded bg-nexus-red/10">{error}</div>;
    if (!data) return null;

    const riskModeColor = {
        'NORMAL': 'bg-green-500/10 text-nexus-green',
        'ELEVATED': 'bg-amber-500/10 text-nexus-amber',
        'CRITICAL': 'bg-red-500/10 text-nexus-red',
        'SHUTDOWN': 'bg-nexus-red text-white',
    }[data.risk_level] || 'bg-nexus-hover text-nexus-muted';

    return (
        <div className="space-y-6">
            {/* Risk Mode Banner */}
            <div className="stat-card flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Shield className={`w-5 h-5 ${data.circuit_breaker_active ? 'text-nexus-red animate-pulse' : 'text-nexus-accent'}`} />
                    <div>
                        <div className="text-sm font-medium text-nexus-text">Risk Governor</div>
                        <div className="text-xs text-nexus-muted">
                            {data.circuit_breaker_active ? 'CIRCUIT BREAKER ACTIVE - TRADING HALTED' : 'Real-time portfolio risk monitoring'}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {!data.trading_enabled && <span className="text-xs font-mono text-nexus-red font-bold">TRADING DISABLED</span>}
                    <span className={`status-badge ${riskModeColor}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${data.risk_level === 'NORMAL' ? 'bg-nexus-green' : 'bg-red-500'}`} />
                        {data.risk_level}
                    </span>
                </div>
            </div>

            {/* Risk Gauges */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <RiskGauge
                    label="Current Drawdown"
                    value={data.drawdown.current}
                    max={data.drawdown.max_limit}
                    warn={data.drawdown.current > data.drawdown.warning_threshold}
                    inverse={true}
                />
                <RiskGauge
                    label="Total Exposure"
                    value={data.exposure.current_pct}
                    max={data.exposure.max_pct}
                    inverse={true}
                />
                <RiskGauge
                    label="Loss Streak"
                    value={data.consecutive_losses}
                    max={5}
                    unit=""
                    inverse={true}
                />
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-3">Total PnL</div>
                    <div className={`text-2xl font-mono font-semibold ${data.total_pnl_pct >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                        {data.total_pnl_pct > 0 ? '+' : ''}{data.total_pnl_pct}%
                    </div>
                    <div className="text-xs text-nexus-muted mt-2">
                        Initial: ${data.equity.initial.toLocaleString()}
                    </div>
                </div>
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-3 gap-4">
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Open Positions</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        {data.open_positions_count}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Current Equity</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        ${data.equity.current.toLocaleString()}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Peak Equity</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        ${data.equity.peak.toLocaleString()}
                    </div>
                </div>
            </div>

            <div className="flex justify-end">
                <span className="text-[10px] text-nexus-muted font-mono">
                    Last updated: {data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : 'Never'}
                </span>
            </div>
        </div>
    );
}

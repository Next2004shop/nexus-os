import React from 'react';
import { Shield, AlertTriangle, TrendingDown, Activity } from 'lucide-react';

const RISK_DATA = {
    daily_loss_pct: -0.42,
    max_daily_loss_pct: -2.0,
    max_exposure_pct: 15.8,
    max_allowed_exposure: 30.0,
    correlation_exposure: 0.35,
    max_correlation: 0.70,
    risk_mode: 'NORMAL',
    drawdown_pct: -1.2,
    trades_today: 5,
    max_trades_per_day: 20,
};

function RiskGauge({ label, value, max, unit = '%', warn = false }: {
    label: string; value: number; max: number; unit?: string; warn?: boolean;
}) {
    const pct = Math.min(Math.abs(value / max) * 100, 100);
    const color = pct > 80 ? 'bg-nexus-red' : pct > 50 ? 'bg-nexus-amber' : 'bg-nexus-green';

    return (
        <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-nexus-muted uppercase tracking-wider">{label}</span>
                {warn && <AlertTriangle className="w-3.5 h-3.5 text-nexus-amber" />}
            </div>
            <div className="text-xl font-semibold text-nexus-text font-mono">
                {value}{unit}
            </div>
            <div className="text-xs text-nexus-muted mt-1 mb-2">
                Limit: {max}{unit}
            </div>
            <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

export default function RiskPage() {
    const riskModeColor = {
        'NORMAL': 'bg-green-500/10 text-nexus-green',
        'CAUTIOUS': 'bg-amber-500/10 text-nexus-amber',
        'HALTED': 'bg-red-500/10 text-nexus-red',
    }[RISK_DATA.risk_mode] || 'bg-nexus-hover text-nexus-muted';

    return (
        <div className="space-y-6">
            {/* Risk Mode Banner */}
            <div className="stat-card flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-nexus-accent" />
                    <div>
                        <div className="text-sm font-medium text-nexus-text">Risk Engine</div>
                        <div className="text-xs text-nexus-muted">Real-time portfolio risk monitoring</div>
                    </div>
                </div>
                <span className={`status-badge ${riskModeColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${RISK_DATA.risk_mode === 'NORMAL' ? 'bg-nexus-green' : RISK_DATA.risk_mode === 'HALTED' ? 'bg-nexus-red' : 'bg-nexus-amber'}`} />
                    {RISK_DATA.risk_mode}
                </span>
            </div>

            {/* Risk Gauges */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <RiskGauge
                    label="Daily Loss"
                    value={RISK_DATA.daily_loss_pct}
                    max={RISK_DATA.max_daily_loss_pct}
                />
                <RiskGauge
                    label="Max Exposure"
                    value={RISK_DATA.max_exposure_pct}
                    max={RISK_DATA.max_allowed_exposure}
                />
                <RiskGauge
                    label="Correlation"
                    value={RISK_DATA.correlation_exposure}
                    max={RISK_DATA.max_correlation}
                    unit=""
                />
                <RiskGauge
                    label="Drawdown"
                    value={RISK_DATA.drawdown_pct}
                    max={-5.0}
                />
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-2 gap-4">
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Trades Today</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        {RISK_DATA.trades_today} / {RISK_DATA.max_trades_per_day}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Daily Loss Limit</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        {RISK_DATA.max_daily_loss_pct}%
                    </div>
                </div>
            </div>
        </div>
    );
}

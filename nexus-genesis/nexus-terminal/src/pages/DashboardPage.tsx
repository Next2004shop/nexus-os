import React, { useEffect, useState } from 'react';
import api from '../api/client';
import {
    DollarSign,
    TrendingUp,
    BarChart3,
    Activity,
    Zap,
    AlertTriangle,
    Shield,
    Lock
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';

interface TelemetryData {
    metrics: {
        equity: number;
        balance: number;
        floating_pl: number;
        daily_return: number;
        win_rate: number;
        drawdown: number;
        open_positions: number;
        margin_usage: number;
        system_mode: string;
        latency_ms: number;
        error_rate: number;
        runtime_status: string;
        capital_status: {
            mode: string;
            daily_start_equity: number;
            daily_pnl_pct: number;
            active_risk_pct: number;
        };
        strategic_status: {
            regime: string;
            volatility: string;
            bias: string;
        };
        execution_health: {
            execution_score: number;
            slippage_avg: number;
            broker_condition: string;
        };
    };
    history: {
        equity: { timestamp: string; value: number }[];
        pnl: { timestamp: string; value: number }[];
    };
    warnings: {
        drawdown: boolean;
        latency: boolean;
        errors: boolean;
    };
}

export default function DashboardPage() {
    const [data, setData] = useState<TelemetryData | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const res = await api.get('/api/system/telemetry');
            setData(res.data);
            setLastUpdate(new Date());
        } catch (err) {
            console.error("Telemetry fetch failed", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 2000); // Poll every 2s for "live" feel
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-nexus-muted text-sm font-mono animate-pulse">Initializing Telemetry Uplink...</div>
            </div>
        );
    }

    const metrics = data?.metrics;
    const isWarning = data?.warnings.drawdown || data?.warnings.latency || data?.warnings.errors;

    // Formatting helpers
    const fmtCurrency = (val: number) => `$${val?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    const fmtPct = (val: number) => `${val > 0 ? '+' : ''}${val?.toFixed(2)}%`;

    const stats = [
        {
            label: 'Total Equity',
            value: fmtCurrency(metrics?.equity || 0),
            icon: TrendingUp,
            change: fmtPct(metrics?.daily_return || 0),
            positive: (metrics?.daily_return || 0) >= 0,
        },
        {
            label: 'Floating P/L',
            value: fmtCurrency(metrics?.floating_pl || 0),
            icon: Activity,
            change: '', // Real-time floating
            positive: (metrics?.floating_pl || 0) >= 0,
        },
        {
            label: 'Margin Usage',
            value: `${(metrics?.margin_usage || 0).toFixed(1)}%`,
            icon: Zap,
            change: `Exp: ${(metrics?.open_positions || 0)} Pos`,
            positive: (metrics?.margin_usage || 0) < 50,
        },
        {
            label: 'Drawdown',
            value: `${(metrics?.drawdown || 0).toFixed(2)}%`,
            icon: Shield,
            change: 'Max 5.0%',
            positive: (metrics?.drawdown || 0) < 5.0,
        },
    ];

    // Prepare chart data
    const chartData = data?.history.equity.map(p => ({
        time: new Date(p.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        value: p.value,
        rawTime: p.timestamp
    })).slice(-50) || []; // Last 50 points

    return (
        <div className="space-y-6">
            {/* Warnings Banner */}
            {isWarning && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 flex items-center gap-3 animate-pulse">
                    <AlertTriangle className="w-5 h-5 text-nexus-red" />
                    <div className="text-sm font-mono text-nexus-red">
                        SYSTEM WARNING:
                        {data?.warnings.drawdown && " HIGH DRAWDOWN DETECTED "}
                        {data?.warnings.latency && " HIGH LATENCY "}
                        {data?.warnings.errors && " ELEVATED ERROR RATE "}
                    </div>
                </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="stat-card">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-xs text-nexus-muted uppercase tracking-wider">{stat.label}</span>
                            <stat.icon className={`w-4 h-4 ${stat.positive !== undefined ? (stat.positive ? 'text-nexus-green' : 'text-nexus-red') : 'text-nexus-muted'}`} />
                        </div>
                        <div className="text-2xl font-semibold text-nexus-text font-mono">{stat.value}</div>
                        {stat.change && (
                            <div className={`text-xs mt-1 font-mono ${stat.positive !== undefined ? (stat.positive ? 'text-nexus-green' : 'text-nexus-red') : 'text-nexus-muted'}`}>
                                {stat.change}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Equity Curve */}
                <div className="stat-card lg:col-span-2 h-[350px] flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xs text-nexus-muted uppercase tracking-wider">Live Equity Curve</h3>
                        <div className="text-[10px] text-nexus-muted font-mono">
                            Latency: <span className={metrics && metrics.latency_ms > 200 ? 'text-nexus-amber' : 'text-nexus-green'}>{metrics?.latency_ms}ms</span>
                        </div>
                    </div>

                    <div className="flex-1 w-full min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis
                                    dataKey="time"
                                    stroke="#666"
                                    tick={{ fontSize: 10 }}
                                    tickLine={false}
                                    axisLine={false}
                                    minTickGap={30}
                                />
                                <YAxis
                                    domain={['auto', 'auto']}
                                    stroke="#666"
                                    tick={{ fontSize: 10 }}
                                    tickLine={false}
                                    axisLine={false}
                                    width={60}
                                    tickFormatter={(val) => `$${val}`}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }}
                                    itemStyle={{ color: '#10b981' }}
                                    formatter={(val: number) => [`$${val.toFixed(2)}`, 'Equity']}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorEquity)"
                                    isAnimationActive={false} // Disable animation for smoother realtime updates
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* System Diagnostics */}
                {/* Modified to include Capital Status */}
                <div className="space-y-4">
                    {/* Capital Status Card */}
                    <div className="stat-card border-l-4 border-l-nexus-accent">
                        <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Lock className="w-3 h-3" /> Capital Discipline
                        </h3>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Allocation Mode</span>
                                <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${metrics?.capital_status?.mode === 'NORMAL' ? 'text-nexus-green bg-green-500/10' :
                                    metrics?.capital_status?.mode === 'REDUCED' ? 'text-nexus-amber bg-amber-500/10' :
                                        metrics?.capital_status?.mode === 'DEFENSIVE' ? 'text-nexus-red bg-red-500/10' : 'text-gray-500'
                                    }`}>
                                    {metrics?.capital_status?.mode || 'INIT'}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Daily P/L</span>
                                <span className={`text-sm font-mono ${(metrics?.capital_status?.daily_pnl_pct || 0) >= 0 ? 'text-nexus-green' : 'text-nexus-red'
                                    }`}>
                                    {fmtPct(metrics?.capital_status?.daily_pnl_pct || 0)}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Daily Start</span>
                                <span className="text-sm font-mono text-nexus-muted">
                                    {fmtCurrency(metrics?.capital_status?.daily_start_equity || 0)}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Strategic Intelligence Card */}
                    <div className="stat-card border-l-4 border-l-purple-500">
                        <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Activity className="w-3 h-3 text-purple-500" /> Strategic Intelligence
                        </h3>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Macro Regime</span>
                                <span className="text-sm font-mono text-purple-400 font-bold">
                                    {metrics?.strategic_status?.regime || 'WAITING'}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Volatility</span>
                                <span className={`text-sm font-mono ${metrics?.strategic_status?.volatility === 'HIGH' ? 'text-nexus-red' :
                                    metrics?.strategic_status?.volatility === 'LOW' ? 'text-nexus-amber' : 'text-nexus-green'
                                    }`}>
                                    {metrics?.strategic_status?.volatility || 'NORMAL'}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-nexus-muted">Risk Bias</span>
                                <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${metrics?.strategic_status?.bias === 'RISK_ON' ? 'text-nexus-green bg-green-500/10' :
                                    metrics?.strategic_status?.bias === 'RISK_OFF' ? 'text-nexus-red bg-red-500/10' : 'text-nexus-muted bg-gray-500/10'
                                    }`}>
                                    {metrics?.strategic_status?.bias || 'NEUTRAL'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Execution Health Card */}
            <div className="stat-card border-l-4 border-l-blue-500">
                <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Zap className="w-3 h-3 text-blue-500" /> Execution Health
                </h3>
                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Quality Score</span>
                        <span className="text-sm font-mono text-blue-400 font-bold">
                            {metrics?.execution_health?.execution_score || 100}/100
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Avg Slippage</span>
                        <span className={`text-sm font-mono ${(metrics?.execution_health?.slippage_avg || 0) > 0.1 ? 'text-nexus-red' : 'text-nexus-green'
                            }`}>
                            {metrics?.execution_health?.slippage_avg?.toFixed(3) || '0.000'}%
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Broker Condition</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${metrics?.execution_health?.broker_condition === 'OPTIMAL' ? 'text-nexus-green bg-green-500/10' : 'text-nexus-red bg-red-500/10'
                            }`}>
                            {metrics?.execution_health?.broker_condition || 'OPTIMAL'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="stat-card">
                <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4">Diagnostics</h3>
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Runtime Guard</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-mono border ${metrics?.runtime_status === 'RUNNING' ? 'bg-green-500/10 text-nexus-green border-green-500/20' :
                            metrics?.runtime_status === 'RECOVERING' ? 'bg-amber-500/10 text-nexus-amber border-amber-500/20 animate-pulse' :
                                'bg-red-500/10 text-nexus-red border-red-500/20'
                            }`}>
                            <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${metrics?.runtime_status === 'RUNNING' ? 'bg-nexus-green' :
                                metrics?.runtime_status === 'RECOVERING' ? 'bg-nexus-amber' : 'bg-nexus-red'
                                }`}></span>
                            {metrics?.runtime_status || 'UNKNOWN'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">System Mode</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-mono ${metrics?.system_mode === 'NORMAL' ? 'bg-green-500/10 text-nexus-green' :
                            metrics?.system_mode === 'SHUTDOWN' ? 'bg-red-500/10 text-nexus-red' : 'bg-nexus-accent/10 text-nexus-accent'
                            }`}>
                            {metrics?.system_mode || 'OFFLINE'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Error Rate</span>
                        <span className={`text-sm font-mono ${(metrics?.error_rate || 0) > 0 ? 'text-nexus-red' : 'text-nexus-green'
                            }`}>
                            {metrics?.error_rate.toFixed(1)} / min
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Win Rate (20)</span>
                        <span className="text-sm font-mono text-nexus-text">
                            {(metrics?.win_rate || 0).toFixed(0)}%
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-nexus-muted">Balance</span>
                        <span className="text-sm font-mono text-nexus-muted">
                            {fmtCurrency(metrics?.balance || 0)}
                        </span>
                    </div>
                </div>
            </div>

            <div className="stat-card bg-nexus-surface/50">
                <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-2">Last Update</h3>
                <div className="text-right font-mono text-xs text-nexus-muted">
                    {lastUpdate.toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
}

import React, { useEffect, useState } from 'react';
import { checkHealth } from '../api/client';
import {
    DollarSign,
    TrendingUp,
    BarChart3,
    Activity,
    Zap,
} from 'lucide-react';

interface HealthData {
    status: string;
    uptime: string;
    mt5_connected: boolean;
    version: string;
    risk_engine: string;
    execution_layer: string;
    mode: string;
    trading_enabled: boolean;
    trading_status: string;
}

export default function DashboardPage() {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        loadHealth();
        const interval = setInterval(loadHealth, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadHealth = async () => {
        try {
            const data = await checkHealth();
            setHealth(data);
            setError('');
        } catch (err: any) {
            setError('Failed to connect to backend');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-nexus-muted text-sm font-mono">Loading system status...</div>
            </div>
        );
    }

    const stats = [
        {
            label: 'Account Balance',
            value: '$50,000.00',
            icon: DollarSign,
            change: '+2.4%',
            positive: true,
        },
        {
            label: 'Equity',
            value: '$51,200.00',
            icon: TrendingUp,
            change: '+$1,200.00',
            positive: true,
        },
        {
            label: 'Open Positions',
            value: '3',
            icon: BarChart3,
            change: '',
            positive: true,
        },
        {
            label: "Today's P/L",
            value: '+$340.50',
            icon: Activity,
            change: '+0.68%',
            positive: true,
        },
    ];

    return (
        <div className="space-y-6">
            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="stat-card">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-xs text-nexus-muted uppercase tracking-wider">{stat.label}</span>
                            <stat.icon className="w-4 h-4 text-nexus-muted" />
                        </div>
                        <div className="text-2xl font-semibold text-nexus-text font-mono">{stat.value}</div>
                        {stat.change && (
                            <div className={`text-xs mt-1 ${stat.positive ? 'text-nexus-green' : 'text-nexus-red'}`}>
                                {stat.change}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* System Status */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* System Mode */}
                <div className="stat-card">
                    <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4">System Mode</h3>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Status</span>
                            <span className={`status-badge ${health?.trading_enabled ? 'bg-green-500/10 text-nexus-green' : 'bg-red-500/10 text-nexus-red'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${health?.trading_enabled ? 'bg-nexus-green' : 'bg-nexus-red'}`} />
                                {health?.trading_enabled ? 'RUNNING' : 'HALTED'}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Mode</span>
                            <span className="text-sm text-nexus-text font-mono uppercase">{health?.mode || '—'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Version</span>
                            <span className="text-sm text-nexus-text font-mono">{health?.version || '—'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Uptime</span>
                            <span className="text-sm text-nexus-text font-mono">{health?.uptime || '—'}</span>
                        </div>
                    </div>
                </div>

                {/* Connections */}
                <div className="stat-card">
                    <h3 className="text-xs text-nexus-muted uppercase tracking-wider mb-4">Connections</h3>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">MT5 Bridge</span>
                            <span className={`status-badge ${health?.mt5_connected ? 'bg-green-500/10 text-nexus-green' : 'bg-red-500/10 text-nexus-red'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${health?.mt5_connected ? 'bg-nexus-green' : 'bg-nexus-red'}`} />
                                {health?.mt5_connected ? 'CONNECTED' : 'DISCONNECTED'}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Risk Engine</span>
                            <span className={`status-badge ${health?.risk_engine === 'active' ? 'bg-green-500/10 text-nexus-green' : 'bg-amber-500/10 text-nexus-amber'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${health?.risk_engine === 'active' ? 'bg-nexus-green' : 'bg-nexus-amber'}`} />
                                {health?.risk_engine?.toUpperCase() || '—'}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Execution Layer</span>
                            <span className={`status-badge ${health?.execution_layer === 'ready' ? 'bg-green-500/10 text-nexus-green' : 'bg-red-500/10 text-nexus-red'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${health?.execution_layer === 'ready' ? 'bg-nexus-green' : 'bg-nexus-red'}`} />
                                {health?.execution_layer?.toUpperCase() || '—'}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-nexus-muted">Trading Status</span>
                            <span className="text-sm text-nexus-text font-mono text-right max-w-[200px] truncate">
                                {health?.trading_status || '—'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

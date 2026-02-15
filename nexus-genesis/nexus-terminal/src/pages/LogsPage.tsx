import React, { useState, useEffect, useRef } from 'react';
import { ScrollText, Filter } from 'lucide-react';

interface LogEntry {
    timestamp: string;
    level: 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';
    layer: string;
    message: string;
}

const MOCK_LOGS: LogEntry[] = [
    { timestamp: '14:23:01', level: 'INFO', layer: 'EXECUTION', message: 'Trade submitted: BUY XAUUSD 0.10 lots' },
    { timestamp: '14:23:01', level: 'INFO', layer: 'RISK', message: 'Risk check passed: lot_size=0.10, exposure=12.3%' },
    { timestamp: '14:23:02', level: 'INFO', layer: 'EXECUTION', message: 'Order filled: #12847291 BUY XAUUSD @ 2034.50' },
    { timestamp: '14:22:45', level: 'WARN', layer: 'RISK', message: 'Daily loss approaching limit: -1.8% / -2.0%' },
    { timestamp: '14:22:30', level: 'INFO', layer: 'INTENT', message: 'Command parsed: buy gold → BUY XAUUSD' },
    { timestamp: '14:22:00', level: 'SYSTEM', layer: 'SYSTEM', message: 'Heartbeat: MT5 connected, risk engine active' },
    { timestamp: '14:21:30', level: 'ERROR', layer: 'EXECUTION', message: 'Order rejected: insufficient margin for BTCUSD 0.5' },
    { timestamp: '14:21:00', level: 'INFO', layer: 'INTELLIGENCE', message: 'Signal generated: SELL EURUSD, confidence=72%' },
    { timestamp: '14:20:30', level: 'INFO', layer: 'SYSTEM', message: 'Model ensemble evaluation complete: 3 models converged' },
    { timestamp: '14:20:00', level: 'WARN', layer: 'RISK', message: 'Correlation alert: XAUUSD + EURUSD correlation=0.65' },
    { timestamp: '14:19:30', level: 'INFO', layer: 'EXECUTION', message: 'Position closed: SELL NAS100 #12847283 P/L: +$145.20' },
    { timestamp: '14:19:00', level: 'SYSTEM', layer: 'SYSTEM', message: 'Circuit breaker: all systems nominal' },
];

const LEVEL_COLORS: Record<string, string> = {
    INFO: 'text-nexus-accent',
    WARN: 'text-nexus-amber',
    ERROR: 'text-nexus-red',
    SYSTEM: 'text-nexus-muted',
};

const LAYER_COLORS: Record<string, string> = {
    EXECUTION: 'text-nexus-green',
    RISK: 'text-nexus-amber',
    INTENT: 'text-nexus-accent',
    INTELLIGENCE: 'text-purple-400',
    SYSTEM: 'text-nexus-muted',
};

export default function LogsPage() {
    const [filter, setFilter] = useState<string>('ALL');
    const scrollRef = useRef<HTMLDivElement>(null);

    const filteredLogs = filter === 'ALL'
        ? MOCK_LOGS
        : MOCK_LOGS.filter((log) => log.level === filter || log.layer === filter);

    return (
        <div className="space-y-4 h-full flex flex-col">
            {/* Filter bar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <ScrollText className="w-4 h-4 text-nexus-muted" />
                    <span className="text-xs text-nexus-muted uppercase tracking-wider">Event Log</span>
                </div>
                <div className="flex items-center gap-1">
                    {['ALL', 'INFO', 'WARN', 'ERROR', 'SYSTEM'].map((level) => (
                        <button
                            key={level}
                            onClick={() => setFilter(level)}
                            className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${filter === level
                                    ? 'bg-nexus-accent/10 text-nexus-accent'
                                    : 'text-nexus-muted hover:text-nexus-text hover:bg-nexus-hover'
                                }`}
                        >
                            {level}
                        </button>
                    ))}
                </div>
            </div>

            {/* Log Feed */}
            <div
                ref={scrollRef}
                className="flex-1 bg-nexus-surface border border-nexus-border rounded-lg overflow-auto min-h-[400px]"
            >
                <div className="p-3 space-y-0.5 font-mono text-xs">
                    {filteredLogs.map((log, i) => (
                        <div key={i} className="flex gap-3 py-1 px-2 rounded hover:bg-nexus-hover group">
                            <span className="text-nexus-muted flex-shrink-0 w-16">{log.timestamp}</span>
                            <span className={`flex-shrink-0 w-12 font-semibold ${LEVEL_COLORS[log.level]}`}>
                                {log.level}
                            </span>
                            <span className={`flex-shrink-0 w-24 ${LAYER_COLORS[log.layer] || 'text-nexus-muted'}`}>
                                [{log.layer}]
                            </span>
                            <span className="text-nexus-text">{log.message}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Log summary */}
            <div className="flex items-center gap-4 text-xs text-nexus-muted">
                <span>{filteredLogs.length} entries</span>
                <span>•</span>
                <span className="text-nexus-red">{MOCK_LOGS.filter((l) => l.level === 'ERROR').length} errors</span>
                <span>•</span>
                <span className="text-nexus-amber">{MOCK_LOGS.filter((l) => l.level === 'WARN').length} warnings</span>
            </div>
        </div>
    );
}

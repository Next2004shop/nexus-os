import React from 'react';

const MOCK_POSITIONS = [
    { symbol: 'XAUUSD', direction: 'BUY', volume: 0.10, entry: 2034.50, sl: 2028.00, tp: 2050.00, profit: 85.30 },
    { symbol: 'EURUSD', direction: 'SELL', volume: 0.20, entry: 1.0862, sl: 1.0900, tp: 1.0800, profit: -12.40 },
    { symbol: 'NAS100', direction: 'BUY', volume: 0.05, entry: 17820.00, sl: 17750.00, tp: 17950.00, profit: 267.60 },
];

export default function PositionsPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xs text-nexus-muted uppercase tracking-wider">Open Positions</h2>
                <span className="text-xs text-nexus-muted font-mono">{MOCK_POSITIONS.length} active</span>
            </div>

            <div className="bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th className="pl-4">Symbol</th>
                            <th>Direction</th>
                            <th>Volume</th>
                            <th>Entry</th>
                            <th>SL</th>
                            <th>TP</th>
                            <th className="pr-4 text-right">P/L</th>
                        </tr>
                    </thead>
                    <tbody>
                        {MOCK_POSITIONS.map((pos, i) => (
                            <tr key={i}>
                                <td className="pl-4 font-semibold text-nexus-text">{pos.symbol}</td>
                                <td>
                                    <span className={`status-badge ${pos.direction === 'BUY' ? 'bg-green-500/10 text-nexus-green' : 'bg-red-500/10 text-nexus-red'}`}>
                                        {pos.direction}
                                    </span>
                                </td>
                                <td>{pos.volume.toFixed(2)}</td>
                                <td>{pos.entry.toFixed(pos.symbol === 'EURUSD' ? 4 : 2)}</td>
                                <td className="text-nexus-red">{pos.sl.toFixed(pos.symbol === 'EURUSD' ? 4 : 2)}</td>
                                <td className="text-nexus-green">{pos.tp.toFixed(pos.symbol === 'EURUSD' ? 4 : 2)}</td>
                                <td className={`pr-4 text-right font-semibold ${pos.profit >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                                    {pos.profit >= 0 ? '+' : ''}{pos.profit.toFixed(2)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Total Positions</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">{MOCK_POSITIONS.length}</div>
                </div>
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Total Volume</div>
                    <div className="text-xl font-semibold text-nexus-text font-mono">
                        {MOCK_POSITIONS.reduce((sum, p) => sum + p.volume, 0).toFixed(2)}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="text-xs text-nexus-muted uppercase tracking-wider mb-1">Total P/L</div>
                    <div className={`text-xl font-semibold font-mono ${MOCK_POSITIONS.reduce((sum, p) => sum + p.profit, 0) >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                        ${MOCK_POSITIONS.reduce((sum, p) => sum + p.profit, 0).toFixed(2)}
                    </div>
                </div>
            </div>
        </div>
    );
}

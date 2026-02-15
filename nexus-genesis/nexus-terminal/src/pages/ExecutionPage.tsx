import React, { useState } from 'react';
import { Terminal, Send, X, AlertTriangle } from 'lucide-react';

interface TradePreview {
    symbol: string;
    direction: string;
    volume: number;
    sl?: number;
    tp?: number;
}

export default function ExecutionPage() {
    const [command, setCommand] = useState('');
    const [preview, setPreview] = useState<TradePreview | null>(null);
    const [output, setOutput] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    const handleCommand = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim()) return;

        setLoading(true);
        setOutput((prev) => [...prev, `> ${command}`]);

        // Simulate command processing
        setTimeout(() => {
            // Parse basic commands for preview
            const lower = command.toLowerCase();
            if (lower.includes('buy') || lower.includes('sell')) {
                const direction = lower.includes('buy') ? 'BUY' : 'SELL';
                const symbols = ['XAUUSD', 'EURUSD', 'NAS100', 'BTCUSD'];
                const symbol = symbols.find((s) => lower.includes(s.toLowerCase())) || 'XAUUSD';
                setPreview({
                    symbol,
                    direction,
                    volume: 0.10,
                    sl: undefined,
                    tp: undefined,
                });
                setOutput((prev) => [...prev, `[SYSTEM] Trade preview generated — awaiting confirmation`]);
            } else {
                setOutput((prev) => [...prev, `[SYSTEM] Command received: ${command}`]);
            }
            setLoading(false);
        }, 500);

        setCommand('');
    };

    const handleConfirm = () => {
        if (!preview) return;
        setOutput((prev) => [
            ...prev,
            `[EXEC] ${preview.direction} ${preview.symbol} @ ${preview.volume} lots — SENT TO RISK GOVERNOR`,
        ]);
        setPreview(null);
    };

    const handleCancel = () => {
        setOutput((prev) => [...prev, `[SYSTEM] Trade cancelled`]);
        setPreview(null);
    };

    return (
        <div className="space-y-4 h-full flex flex-col">
            {/* Trade Preview Card */}
            {preview && (
                <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-nexus-amber" />
                            <span className="text-xs text-nexus-muted uppercase tracking-wider">Trade Preview</span>
                        </div>
                    </div>
                    <div className="grid grid-cols-4 gap-4 mb-4">
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Symbol</div>
                            <div className="text-sm font-semibold text-nexus-text font-mono">{preview.symbol}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Direction</div>
                            <div className={`text-sm font-semibold font-mono ${preview.direction === 'BUY' ? 'text-nexus-green' : 'text-nexus-red'}`}>
                                {preview.direction}
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Volume</div>
                            <div className="text-sm font-semibold text-nexus-text font-mono">{preview.volume}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Status</div>
                            <div className="text-sm font-semibold text-nexus-amber font-mono">PENDING</div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={handleConfirm} className="btn-primary text-sm">
                            Confirm Trade
                        </button>
                        <button onClick={handleCancel} className="btn-ghost text-sm">
                            <X className="w-3.5 h-3.5 mr-1 inline" />
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Terminal Output */}
            <div className="flex-1 bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden flex flex-col min-h-[300px]">
                <div className="flex items-center gap-2 px-4 py-2 border-b border-nexus-border">
                    <Terminal className="w-3.5 h-3.5 text-nexus-muted" />
                    <span className="text-xs text-nexus-muted font-mono">NEXUS COMMAND TERMINAL</span>
                </div>
                <div className="flex-1 overflow-auto p-4 font-mono text-xs space-y-1">
                    {output.length === 0 ? (
                        <div className="text-nexus-muted">Waiting for commands...</div>
                    ) : (
                        output.map((line, i) => (
                            <div
                                key={i}
                                className={
                                    line.startsWith('>')
                                        ? 'text-nexus-accent'
                                        : line.includes('[EXEC]')
                                            ? 'text-nexus-green'
                                            : line.includes('cancelled')
                                                ? 'text-nexus-red'
                                                : 'text-nexus-muted'
                                }
                            >
                                {line}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Command Input */}
            <form onSubmit={handleCommand} className="flex gap-2">
                <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="Enter command (e.g., buy XAUUSD 0.1)"
                    className="input-field font-mono text-sm flex-1"
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !command.trim()} className="btn-primary" aria-label="Send command">
                    <Send className="w-4 h-4" />
                </button>
            </form>
        </div>
    );
}

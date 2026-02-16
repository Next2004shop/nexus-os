import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Send, X, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import api from '../api/client';

interface ParsedIntent {
    intent: string;
    asset: string | null;
    direction: string | null;
    volume: number | null;
    sl: number | null;
    tp: number | null;
    confidence: number;
    reasoning: string;
    requires_confirmation: boolean;
    error: string | null;
}

interface LogEntry {
    time: string;
    type: 'cmd' | 'sys' | 'ok' | 'err';
    text: string;
}

export default function ExecutionPage() {
    const [command, setCommand] = useState('');
    const [preview, setPreview] = useState<ParsedIntent | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [parsing, setParsing] = useState(false);
    const [executing, setExecuting] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);

    const ts = () => new Date().toLocaleTimeString('en-US', { hour12: false });

    const addLog = (type: LogEntry['type'], text: string) => {
        setLogs((prev) => [...prev, { time: ts(), type, text }]);
    };

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    // ── Step 1: Parse (Analyze) ─────────────────────────────────────────
    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim() || parsing) return;

        addLog('cmd', command);
        setParsing(true);
        setPreview(null);

        try {
            const { data } = await api.post('/api/command/parse', { text: command });
            setPreview(data);
            addLog('sys', `Intent parsed: ${data.direction?.toUpperCase() || '?'} ${data.asset || '?'} — confidence ${data.confidence}%`);
        } catch (err: any) {
            const msg = err.response?.data?.error || 'Failed to parse command';
            addLog('err', msg);
        } finally {
            setParsing(false);
            setCommand('');
        }
    };

    // ── Step 2: Confirm Execution ───────────────────────────────────────
    const handleConfirm = async () => {
        if (!preview || executing) return;

        setExecuting(true);
        addLog('sys', 'Sending to execution pipeline...');

        try {
            const { data } = await api.post('/api/command/execute', {
                asset: preview.asset,
                direction: preview.direction,
                volume: preview.volume,
                sl: preview.sl,
                tp: preview.tp,
                source: 'manual',
            });

            if (data.status === 'APPROVED') {
                addLog('ok', `APPROVED: ${data.execution?.message || 'Command routed to execution engine'}`);
            } else if (data.status === 'REJECTED') {
                addLog('err', `REJECTED: ${data.errors?.join(', ') || 'Validation failed'}`);
            } else {
                addLog('sys', `Status: ${data.status}`);
            }
        } catch (err: any) {
            const msg = err.response?.data?.error || 'Execution failed';
            addLog('err', msg);
        } finally {
            setExecuting(false);
            setPreview(null);
        }
    };

    const handleCancel = () => {
        addLog('sys', 'Trade cancelled by operator');
        setPreview(null);
    };

    // ── Render ──────────────────────────────────────────────────────────
    return (
        <div className="space-y-4 h-full flex flex-col">
            {/* Trade Preview Card */}
            {preview && !preview.error && (
                <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="w-4 h-4 text-nexus-amber" />
                        <span className="text-xs text-nexus-muted uppercase tracking-wider">Trade Preview — Confirmation Required</span>
                    </div>

                    <div className="grid grid-cols-5 gap-4 mb-4">
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Asset</div>
                            <div className="text-sm font-semibold text-nexus-text font-mono">{preview.asset || '—'}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Direction</div>
                            <div className={`text-sm font-semibold font-mono ${preview.direction === 'buy' ? 'text-nexus-green' : 'text-nexus-red'}`}>
                                {preview.direction?.toUpperCase() || '—'}
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">Volume</div>
                            <div className="text-sm font-semibold text-nexus-text font-mono">{preview.volume ?? '—'}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">SL</div>
                            <div className="text-sm font-mono text-nexus-red">{preview.sl ?? '—'}</div>
                        </div>
                        <div>
                            <div className="text-[10px] text-nexus-muted uppercase">TP</div>
                            <div className="text-sm font-mono text-nexus-green">{preview.tp ?? '—'}</div>
                        </div>
                    </div>

                    {preview.reasoning && (
                        <div className="text-xs text-nexus-muted mb-3 font-mono bg-nexus-bg rounded px-2 py-1">
                            {preview.reasoning}
                        </div>
                    )}

                    <div className="flex items-center gap-3">
                        <button onClick={handleConfirm} disabled={executing} className="btn-primary text-sm flex items-center gap-1.5">
                            {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                            {executing ? 'Executing...' : 'Confirm Trade'}
                        </button>
                        <button onClick={handleCancel} disabled={executing} className="btn-ghost text-sm flex items-center gap-1.5">
                            <X className="w-3.5 h-3.5" />
                            Cancel
                        </button>
                        <span className="ml-auto text-xs text-nexus-muted font-mono">
                            Confidence: {preview.confidence}%
                        </span>
                    </div>
                </div>
            )}

            {/* Terminal Output */}
            <div className="flex-1 bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden flex flex-col min-h-[300px]">
                <div className="flex items-center gap-2 px-4 py-2 border-b border-nexus-border">
                    <Terminal className="w-3.5 h-3.5 text-nexus-muted" />
                    <span className="text-xs text-nexus-muted font-mono">NEXUS COMMAND TERMINAL</span>
                </div>
                <div className="flex-1 overflow-auto p-4 font-mono text-xs space-y-0.5">
                    {logs.length === 0 ? (
                        <div className="text-nexus-muted">Waiting for commands...</div>
                    ) : (
                        logs.map((entry, i) => (
                            <div key={i} className="flex gap-2">
                                <span className="text-nexus-muted flex-shrink-0">{entry.time}</span>
                                <span className={
                                    entry.type === 'cmd' ? 'text-nexus-accent' :
                                        entry.type === 'ok' ? 'text-nexus-green' :
                                            entry.type === 'err' ? 'text-nexus-red' :
                                                'text-nexus-muted'
                                }>
                                    {entry.type === 'cmd' ? '>' : entry.type === 'ok' ? '✓' : entry.type === 'err' ? '✗' : '•'}{' '}
                                    {entry.text}
                                </span>
                            </div>
                        ))
                    )}
                    <div ref={logEndRef} />
                </div>
            </div>

            {/* Command Input */}
            <form onSubmit={handleAnalyze} className="flex gap-2">
                <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder='Enter command (e.g., "Buy gold 0.01 lot SL 20 TP 40")'
                    className="input-field font-mono text-sm flex-1"
                    disabled={parsing || executing}
                />
                <button
                    type="submit"
                    disabled={parsing || executing || !command.trim()}
                    className="btn-primary flex items-center gap-1.5"
                    aria-label="Analyze command"
                >
                    {parsing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    <span className="text-sm">Analyze</span>
                </button>
            </form>
        </div>
    );
}

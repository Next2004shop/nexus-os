"use client";

import { useState, useRef, useEffect } from "react";
import { BotMessageSquare, Send, Terminal } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface LogEntry {
  timestamp: string;
  type: "command" | "response" | "error" | "system";
  message: string;
}

export default function AIConsolePage() {
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([
    { timestamp: new Date().toISOString(), type: "system", message: "NEXUS AI Console initialized. Type a command or ask a question." },
    { timestamp: new Date().toISOString(), type: "system", message: "Available commands: status, pause, resume, explain trade, risk, stealth, kill" },
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [logs]);

  const addLog = (type: LogEntry["type"], message: string) => {
    setLogs((prev) => [...prev, { timestamp: new Date().toISOString(), type, message }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const command = input.trim();
    setInput("");
    addLog("command", command);
    setLoading(true);

    try {
      const result = await api.aiCommand(command);
      addLog("response", JSON.stringify(result, null, 2));
    } catch (err) {
      addLog("error", `Failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  const typeColor = {
    command: "text-[var(--nexus-blue)]",
    response: "text-[var(--nexus-green)]",
    error: "text-[var(--nexus-red)]",
    system: "text-[var(--nexus-yellow)]",
  };

  const typePrefix = {
    command: ">>> ",
    response: "<<< ",
    error: "ERR ",
    system: "SYS ",
  };

  return (
    <div className="space-y-6 animate-fade-in h-[calc(100vh-var(--topbar-height)-48px)] flex flex-col">
      <h1 className="text-lg font-mono font-bold tracking-wide">AI Console</h1>

      {/* Console Output */}
      <Card
        title="Master AI Terminal"
        icon={<Terminal className="w-3.5 h-3.5" />}
        className="flex-1 flex flex-col min-h-0"
      >
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1 font-mono text-xs min-h-0">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-2 py-0.5">
              <span className="text-[var(--nexus-muted)] shrink-0 w-[72px]">
                {new Date(log.timestamp).toLocaleTimeString("en-US", { hour12: false })}
              </span>
              <span className={`shrink-0 w-8 ${typeColor[log.type]}`}>
                {typePrefix[log.type]}
              </span>
              <span className={typeColor[log.type]} style={{ whiteSpace: "pre-wrap" }}>
                {log.message}
              </span>
            </div>
          ))}
          {loading && (
            <div className="flex gap-2 py-0.5">
              <span className="text-[var(--nexus-muted)] w-[72px]" />
              <span className="text-[var(--nexus-subtext)] animate-pulse">Processing...</span>
            </div>
          )}
        </div>
      </Card>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 flex items-center gap-3 nexus-card px-4 py-3">
          <BotMessageSquare className="w-4 h-4 text-[var(--nexus-subtext)] shrink-0" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter command (e.g., status, risk, explain trade)..."
            className="flex-1 bg-transparent text-sm font-mono outline-none placeholder:text-[var(--nexus-muted)]"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-3 nexus-card text-[var(--nexus-green)] hover:bg-[var(--nexus-green-glow)] transition-colors disabled:opacity-30"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}

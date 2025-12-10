"use client";
import { Card } from "@/components/ui/Card";
import { Bot, Send, Trash2, Loader2 } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { nexusApi } from "@/lib/api";

export default function AIBotPage() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<{ role: string, content: string }[]>([
        { role: 'ai', content: 'Hello. I am Nexus AI. I can analyze markets, fix code, and execute trades. How can I assist?' }
    ]);
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput("");
        setLoading(true);

        try {
            const res = await nexusApi.aiChat(userMsg);
            setMessages(prev => [...prev, { role: 'ai', content: res.response || "No response received." }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'ai', content: "Error communicating with Nexus Brain." }]);
        }
        setLoading(false);
    };

    return (
        <div className="flex h-screen p-6 gap-6">
            <Card className="flex-1 flex flex-col p-6">
                <div className="flex justify-between items-center mb-6 pb-4 border-b border-nexus-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-nexus-blue/20 flex items-center justify-center border border-nexus-blue/30">
                            <Bot className="text-nexus-blue" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">Nexus Brain</h2>
                            <div className="text-xs text-nexus-green font-mono flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-nexus-green animate-pulse" />
                                ONLINE - GPT-4o
                            </div>
                        </div>
                    </div>
                    <button onClick={() => setMessages([])} className="p-2 hover:bg-white/10 rounded-lg text-nexus-subtext hover:text-white transition-colors">
                        <Trash2 size={20} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-6 scrollbar-thin scrollbar-thumb-white/10">
                    {messages.map((msg, i) => (
                        <div key={i} className={cn("flex flex-col gap-1 items-start", msg.role === 'user' ? "items-end" : "items-start")}>
                            <span className="text-xs text-nexus-subtext mx-2">{msg.role === 'user' ? 'You' : 'Nexus AI'}</span>
                            <div className={cn(
                                "p-4 rounded-2xl max-w-[80%] text-sm leading-relaxed",
                                msg.role === 'user' ? "bg-nexus-blue/20 rounded-tr-none border border-nexus-blue/30" : "bg-white/5 rounded-tl-none border border-white/5"
                            )}>
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex flex-col gap-1 items-start">
                            <span className="text-xs text-nexus-subtext mx-2">Nexus AI</span>
                            <div className="bg-white/5 p-4 rounded-2xl rounded-tl-none border border-white/5 flex items-center gap-2">
                                <Loader2 className="animate-spin" size={16} />
                                <span className="text-xs text-nexus-subtext">Thinking...</span>
                            </div>
                        </div>
                    )}
                </div>

                <div className="relative">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        type="text"
                        placeholder="Ask me to buy BTC or analyze EURUSD..."
                        className="w-full bg-black/40 border border-nexus-border rounded-xl pl-4 pr-14 py-4 text-white placeholder:text-nexus-subtext focus:border-nexus-blue outline-none transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        className="absolute right-2 top-2 p-2 bg-nexus-blue hover:bg-blue-600 rounded-lg text-white transition-colors"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </Card>

            <Card className="w-80 p-6 flex flex-col">
                <h3 className="text-sm font-bold text-nexus-subtext uppercase mb-4">System Logs</h3>
                <div className="flex-1 font-mono text-xs text-nexus-subtext opacity-70 space-y-2">
                    <div className="text-nexus-green">&gt; System Initialized</div>
                    <div className="text-nexus-blue">&gt; Connected to Brain</div>
                    <div className="text-white/50">&gt; Waiting for input...</div>
                </div>
            </Card>
        </div>
    );
}

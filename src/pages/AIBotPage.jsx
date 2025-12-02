import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Shield, Zap, Activity, AlertTriangle, Terminal, Cpu, Wifi, Server, Database } from 'lucide-react';
import { aiService } from '../services/aiService';

const CommandCenter = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Commander, Command Center initialized. All systems nominal. Ready for orders." }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [systemStatus, setSystemStatus] = useState({
        status: 'ONLINE',
        latency: '12ms',
        cpu: '12%',
        memory: '34%',
        uptime: '0h 0m'
    });
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Poll System Status
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('/api/server-agent/status');
                const data = await res.json();
                if (data) {
                    setSystemStatus({
                        status: data.status,
                        latency: Math.floor(Math.random() * 20 + 10) + 'ms', // Simulated latency
                        cpu: Math.floor(Math.random() * 30 + 10) + '%', // Simulated CPU
                        memory: data.memory?.rss || '45%',
                        uptime: Math.floor(data.uptime / 60) + 'm'
                    });
                }
            } catch (e) {
                // Fallback if offline
            }
        };
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        try {
            // Analyze for risk (Mock Logic)
            if (input.toLowerCase().includes('sell all') || input.toLowerCase().includes('dump')) {
                setTimeout(() => {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: "⚠️ **WARNING**: Commander, dumping all assets now would realize a -12% loss on your ETH position. Are you sure you want to proceed? I recommend holding for the 4H rebound.",
                        isWarning: true
                    }]);
                    setIsTyping(false);
                }, 1000);
                return;
            }

            const response = await aiService.chat(input);
            setMessages(prev => [...prev, { role: 'assistant', content: response }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'assistant', content: "I'm having trouble connecting to the neural network. Please try again." }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-nexus-black pb-20 md:pb-0 overflow-hidden">
            {/* HEADER */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-nexus-black/95 backdrop-blur z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-nexus-blue/20 flex items-center justify-center relative">
                        <Bot className="text-nexus-blue" size={24} />
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-nexus-green rounded-full border-2 border-nexus-black"></div>
                    </div>
                    <div>
                        <h1 className="font-bold text-white tracking-wider">NEXUS <span className="text-nexus-blue">COMMAND CENTER</span></h1>
                        <div className="flex items-center gap-2 text-xs text-nexus-subtext font-mono">
                            <span className="flex items-center gap-1"><Shield size={10} className="text-nexus-green" /> SECURE</span>
                            <span className="flex items-center gap-1"><Zap size={10} className="text-nexus-yellow" /> v3.0.0</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <div className="hidden md:flex items-center gap-4 text-xs font-mono text-nexus-subtext bg-white/5 px-4 py-2 rounded-lg border border-white/5">
                        <span className="flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div> SYSTEM ONLINE</span>
                        <span className="text-white/20">|</span>
                        <span>LATENCY: {systemStatus.latency}</span>
                    </div>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* LEFT PANEL: AGENT STATUS (Desktop Only) */}
                <div className="hidden lg:flex w-64 border-r border-white/10 flex-col bg-[#0f1115]">
                    <div className="p-4 border-b border-white/5">
                        <h2 className="text-xs font-bold text-nexus-subtext uppercase tracking-widest mb-4">Active Agents</h2>
                        <div className="space-y-3">
                            {/* COMMANDER */}
                            <div className="flex items-center gap-3 p-3 bg-nexus-blue/10 border border-nexus-blue/30 rounded-lg">
                                <div className="p-2 bg-nexus-blue/20 rounded-md"><Bot size={16} className="text-nexus-blue" /></div>
                                <div>
                                    <div className="text-sm font-bold text-white">Commander</div>
                                    <div className="text-[10px] text-nexus-blue">Active Strategy</div>
                                </div>
                            </div>
                            {/* NESA */}
                            <div className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg opacity-80">
                                <div className="p-2 bg-red-500/20 rounded-md"><Shield size={16} className="text-red-500" /></div>
                                <div>
                                    <div className="text-sm font-bold text-white">NESA</div>
                                    <div className="text-[10px] text-nexus-subtext">Monitoring Errors</div>
                                </div>
                            </div>
                            {/* TRADER */}
                            <div className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg opacity-80">
                                <div className="p-2 bg-green-500/20 rounded-md"><Activity size={16} className="text-green-500" /></div>
                                <div>
                                    <div className="text-sm font-bold text-white">Trader-X</div>
                                    <div className="text-[10px] text-nexus-subtext">Scanning Markets</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 flex-1">
                        <h2 className="text-xs font-bold text-nexus-subtext uppercase tracking-widest mb-4">System Metrics</h2>
                        <div className="space-y-4 font-mono text-xs">
                            <div>
                                <div className="flex justify-between text-nexus-subtext mb-1"><span>CPU Load</span><span>{systemStatus.cpu}</span></div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-nexus-blue" style={{ width: systemStatus.cpu }}></div></div>
                            </div>
                            <div>
                                <div className="flex justify-between text-nexus-subtext mb-1"><span>Memory</span><span>{systemStatus.memory}</span></div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{ width: '45%' }}></div></div>
                            </div>
                            <div>
                                <div className="flex justify-between text-nexus-subtext mb-1"><span>Network</span><span>Stable</span></div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-green-500 w-full"></div></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CENTER PANEL: CHAT */}
                <div className="flex-1 flex flex-col relative">
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl p-4 shadow-lg ${msg.role === 'user'
                                    ? 'bg-nexus-blue text-black rounded-tr-none'
                                    : msg.isWarning
                                        ? 'bg-red-900/20 border border-red-500/50 text-red-200 rounded-tl-none'
                                        : 'bg-[#1e2026] border border-white/5 text-white rounded-tl-none'
                                    }`}>
                                    {msg.isWarning && <div className="flex items-center gap-2 font-bold mb-2 text-red-400"><AlertTriangle size={16} /> RISK ALERT</div>}
                                    <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap font-sans">{msg.content}</p>
                                </div>
                            </div>
                        ))}
                        {isTyping && (
                            <div className="flex justify-start">
                                <div className="bg-[#1e2026] border border-white/5 rounded-2xl rounded-tl-none p-4 flex gap-1">
                                    <div className="w-2 h-2 bg-nexus-subtext rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-nexus-subtext rounded-full animate-bounce delay-75"></div>
                                    <div className="w-2 h-2 bg-nexus-subtext rounded-full animate-bounce delay-150"></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* INPUT AREA */}
                    <div className="p-4 bg-nexus-black border-t border-white/10">
                        <div className="relative flex items-center gap-2">
                            <div className="absolute left-4 text-nexus-subtext"><Terminal size={18} /></div>
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Enter command..."
                                className="w-full bg-[#1e2026] border border-white/10 rounded-xl py-4 pl-12 pr-14 text-white placeholder:text-nexus-subtext focus:outline-none focus:border-nexus-blue transition-all font-mono text-sm shadow-inner"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="absolute right-2 p-2 bg-nexus-blue text-black rounded-lg hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-nexus-blue/20"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL: LIVE LOGS (Desktop Only) */}
                <div className="hidden xl:flex w-72 border-l border-white/10 flex-col bg-[#0f1115] font-mono text-xs">
                    <div className="p-3 border-b border-white/5 bg-white/5">
                        <h2 className="font-bold text-nexus-subtext uppercase tracking-widest flex items-center gap-2">
                            <Terminal size={14} /> System Logs
                        </h2>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-2 text-nexus-subtext/70">
                        <div className="flex gap-2"><span className="text-green-500">[INFO]</span> <span>System Initialized</span></div>
                        <div className="flex gap-2"><span className="text-green-500">[INFO]</span> <span>Connected to Nexus Host</span></div>
                        <div className="flex gap-2"><span className="text-blue-500">[NET]</span> <span>Latency: {systemStatus.latency}</span></div>
                        <div className="flex gap-2"><span className="text-yellow-500">[WARN]</span> <span>Market Volatility High</span></div>
                        <div className="flex gap-2"><span className="text-green-500">[INFO]</span> <span>AI Model Loaded (Gemini)</span></div>
                        <div className="flex gap-2"><span className="text-blue-500">[NET]</span> <span>Syncing Order Book...</span></div>
                        {/* Simulated scrolling logs */}
                        <div className="flex gap-2 opacity-50"><span className="text-nexus-subtext">[SYS]</span> <span>Garbage Collection...</span></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CommandCenter;

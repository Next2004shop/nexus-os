import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, Shield, Zap, Activity, AlertTriangle, Terminal, Cpu, Network } from 'lucide-react';
import { aiService } from '../services/aiService';

// TYPEWRITER COMPONENT
const Typewriter = ({ text, onComplete }) => {
    const [displayedText, setDisplayedText] = useState('');
    const indexRef = useRef(0);

    useEffect(() => {
        indexRef.current = 0;
        setDisplayedText('');

        const interval = setInterval(() => {
            setDisplayedText((prev) => prev + text.charAt(indexRef.current));
            indexRef.current++;
            if (indexRef.current >= text.length) {
                clearInterval(interval);
                if (onComplete) onComplete();
            }
        }, 20); // Typing speed

        return () => clearInterval(interval);
    }, [text]);

    return <span>{displayedText}</span>;
};

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
    }, [messages, isTyping]);

    // Poll System Status
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('/api/server-agent/status');
                const data = await res.json();
                if (data) {
                    setSystemStatus({
                        status: data.status,
                        latency: Math.floor(Math.random() * 20 + 10) + 'ms',
                        cpu: Math.floor(Math.random() * 30 + 10) + '%',
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
            // Mock Risk Analysis
            if (input.toLowerCase().includes('sell all') || input.toLowerCase().includes('dump')) {
                setTimeout(() => {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: "⚠️ **WARNING**: Commander, dumping all assets now would realize a -12% loss on your ETH position. Are you sure you want to proceed? I recommend holding for the 4H rebound.",
                        isWarning: true
                    }]);
                    setIsTyping(false);
                }, 1500);
                return;
            }

            const response = await aiService.chat(input);
            setMessages(prev => [...prev, { role: 'assistant', content: response, isStreaming: true }]);
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
        <div className="flex flex-col h-screen bg-nexus-black pb-20 md:pb-0 overflow-hidden animate-fadeIn">
            {/* HEADER */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-nexus-black/95 backdrop-blur z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-nexus-accent/20 flex items-center justify-center relative animate-pulse-glow">
                        <Bot className="text-nexus-accent" size={24} />
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-nexus-green rounded-full border-2 border-nexus-black"></div>
                    </div>
                    <div>
                        <h1 className="font-bold text-white tracking-wider">NEXUS <span className="text-nexus-accent">COMMAND CENTER</span></h1>
                        <div className="flex items-center gap-2 text-xs text-nexus-subtext font-mono">
                            <span className="flex items-center gap-1"><Shield size={10} className="text-nexus-green" /> SECURE</span>
                            <span className="flex items-center gap-1"><Zap size={10} className="text-nexus-yellow" /> v3.0.0</span>
                        </div>
                    </div>
                </div>
                <div className="hidden md:flex items-center gap-4 text-xs font-mono text-nexus-subtext bg-white/5 px-4 py-2 rounded-lg border border-white/5">
                    <span className="flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div> SYSTEM ONLINE</span>
                    <span className="text-white/20">|</span>
                    <span>LATENCY: {systemStatus.latency}</span>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* LEFT PANEL: AGENT STATUS (Desktop Only) */}
                <div className="hidden lg:flex w-64 border-r border-white/10 flex-col bg-[#0f1115]">
                    <div className="p-4 border-b border-white/5">
                        <h2 className="text-xs font-bold text-nexus-subtext uppercase tracking-widest mb-4">Active Agents</h2>
                        <div className="space-y-3">
                            <div className="flex items-center gap-3 p-3 bg-nexus-accent/10 border border-nexus-accent/30 rounded-lg">
                                <div className="p-2 bg-nexus-accent/20 rounded-md"><Bot size={16} className="text-nexus-accent" /></div>
                                <div>
                                    <div className="text-sm font-bold text-white">Commander</div>
                                    <div className="text-[10px] text-nexus-accent">Active Strategy</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg opacity-80">
                                <div className="p-2 bg-red-500/20 rounded-md"><Shield size={16} className="text-red-500" /></div>
                                <div>
                                    <div className="text-sm font-bold text-white">NESA</div>
                                    <div className="text-[10px] text-nexus-subtext">Monitoring Errors</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 flex-1">
                        <h2 className="text-xs font-bold text-nexus-subtext uppercase tracking-widest mb-4">System Metrics</h2>
                        <div className="space-y-4 font-mono text-xs">
                            <div>
                                <div className="flex justify-between text-nexus-subtext mb-1"><span>CPU Load</span><span>{systemStatus.cpu}</span></div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-nexus-accent transition-all duration-500" style={{ width: systemStatus.cpu }}></div></div>
                            </div>
                            <div>
                                <div className="flex justify-between text-nexus-subtext mb-1"><span>Memory</span><span>{systemStatus.memory}</span></div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{ width: '45%' }}></div></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CENTER PANEL: CHAT */}
                <div className="flex-1 flex flex-col relative bg-gradient-to-b from-nexus-black to-[#0f1115]">
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                                <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl p-4 shadow-lg ${msg.role === 'user'
                                    ? 'bg-nexus-accent text-black rounded-tr-none font-bold'
                                    : msg.isWarning
                                        ? 'bg-red-900/20 border border-red-500/50 text-red-200 rounded-tl-none'
                                        : 'bg-[#1e2026] border border-white/5 text-white rounded-tl-none'
                                    }`}>
                                    {msg.isWarning && <div className="flex items-center gap-2 font-bold mb-2 text-red-400"><AlertTriangle size={16} /> RISK ALERT</div>}
                                    <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap font-sans">
                                        {msg.role === 'assistant' && msg.isStreaming ? (
                                            <Typewriter text={msg.content} />
                                        ) : (
                                            msg.content
                                        )}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {isTyping && (
                            <div className="flex justify-start animate-fadeIn">
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
                                className="w-full bg-[#1e2026] border border-white/10 rounded-xl py-4 pl-12 pr-14 text-white placeholder:text-nexus-subtext focus:outline-none focus:border-nexus-accent transition-all font-mono text-sm shadow-inner"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="absolute right-2 p-2 bg-nexus-accent text-black rounded-lg hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-nexus-accent/20"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL: NEURAL VISUALIZER (Desktop Only) */}
                <div className="hidden xl:flex w-72 border-l border-white/10 flex-col bg-[#0f1115] font-mono text-xs">
                    <div className="p-3 border-b border-white/5 bg-white/5">
                        <h2 className="font-bold text-nexus-subtext uppercase tracking-widest flex items-center gap-2">
                            <Network size={14} /> Neural Activity
                        </h2>
                    </div>
                    <div className="flex-1 p-4 flex flex-col gap-4">
                        {/* SIMULATED NEURAL NODES */}
                        <div className="h-32 border border-white/5 rounded-lg bg-black/40 relative overflow-hidden">
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-16 h-16 border-2 border-nexus-accent rounded-full animate-ping opacity-20"></div>
                                <div className="absolute w-8 h-8 bg-nexus-accent/20 rounded-full animate-pulse"></div>
                            </div>
                            <div className="absolute bottom-2 left-2 text-[10px] text-nexus-accent">PROCESSING...</div>
                        </div>

                        <div className="space-y-2 text-nexus-subtext/70">
                            <div className="flex gap-2"><span className="text-green-500">[INFO]</span> <span>Gemini Pro: CONNECTED</span></div>
                            <div className="flex gap-2"><span className="text-blue-500">[NET]</span> <span>Latency: {systemStatus.latency}</span></div>
                            <div className="flex gap-2"><span className="text-nexus-yellow">[AI]</span> <span>Pattern Recognition: ACTIVE</span></div>
                            <div className="flex gap-2"><span className="text-nexus-accent">[MEM]</span> <span>Context Window: 8k Tokens</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CommandCenter;

import React, { useState, useEffect, useRef } from 'react';
import { Bot, Zap, Link, Shield, Activity, TrendingUp, Server, CheckCircle, AlertCircle, ArrowUpRight, ArrowDownRight, MessageSquare, User, Send, Loader } from 'lucide-react';
import { aiService } from '../services/aiService';

export const AIBotPage = () => {
    const [connected, setConnected] = useState(false);
    const [server, setServer] = useState('');
    const [login, setLogin] = useState('');
    const [password, setPassword] = useState('');
    const [connectionLog, setConnectionLog] = useState([]);

    // AI Chat State
    const [messages, setMessages] = useState([
        { role: 'model', text: "Hello! I am Nexus AI. I'm analyzing the market 24/7. You can give me instructions or ask about market conditions." }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleConnect = (e) => {
        e.preventDefault();
        setConnectionLog(prev => [...prev, "> Initializing handshake with MT5 Gateway..."]);

        setTimeout(() => {
            setConnectionLog(prev => [...prev, `> Connecting to ${server}...`]);
        }, 500);

        setTimeout(() => {
            setConnectionLog(prev => [...prev, "> Authenticating user credentials..."]);
        }, 1000);

        setTimeout(() => {
            setConnectionLog(prev => [...prev, "> Connection Established."]);
            setConnected(true);
        }, 2000);
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || isTyping) return;

        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
        setIsTyping(true);

        try {
            // Convert internal message format to history format expected by service if needed
            // For now, we pass the raw text and let the service handle context if implemented
            const response = await aiService.sendMessage(userMessage, messages);
            setMessages(prev => [...prev, { role: 'model', text: response }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'model', text: "Error: Unable to reach neural network." }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto animate-fadeIn pb-24">
            {/* HEADER */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-black text-white flex items-center gap-3">
                        <Bot className="text-nexus-blue" size={32} />
                        NEXUS <span className="text-nexus-blue">AI CORE</span>
                    </h1>
                    <p className="text-nexus-subtext text-sm mt-1">Autonomous Trading Neural Network</p>
                </div>
                <div className="flex items-center gap-2 bg-nexus-blue/10 px-4 py-2 rounded-full border border-nexus-blue/20">
                    <div className="w-2 h-2 bg-nexus-green rounded-full animate-pulse"></div>
                    <span className="text-nexus-blue text-xs font-bold">SYSTEM ONLINE</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* LEFT: CONNECTION PANEL */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Link size={20} className="text-nexus-yellow" />
                            MetaTrader 5 Bridge
                        </h2>

                        {!connected ? (
                            <form onSubmit={handleConnect} className="space-y-4">
                                <div>
                                    <label className="text-xs text-nexus-subtext font-bold uppercase mb-1 block">Broker Server</label>
                                    <input
                                        type="text"
                                        className="w-full bg-nexus-black border border-nexus-border rounded-xl p-3 text-white focus:border-nexus-blue outline-none font-mono text-sm"
                                        placeholder="e.g. Exness-Real5"
                                        value={server}
                                        onChange={(e) => setServer(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-nexus-subtext font-bold uppercase mb-1 block">Login ID</label>
                                    <input
                                        type="number"
                                        className="w-full bg-nexus-black border border-nexus-border rounded-xl p-3 text-white focus:border-nexus-blue outline-none font-mono text-sm"
                                        placeholder="Account Number"
                                        value={login}
                                        onChange={(e) => setLogin(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-nexus-subtext font-bold uppercase mb-1 block">Password</label>
                                    <input
                                        type="password"
                                        className="w-full bg-nexus-black border border-nexus-border rounded-xl p-3 text-white focus:border-nexus-blue outline-none font-mono text-sm"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                    />
                                </div>

                                {connectionLog.length > 0 && (
                                    <div className="bg-black/50 p-3 rounded-lg border border-white/5 font-mono text-[10px] text-green-400 h-24 overflow-y-auto">
                                        {connectionLog.map((log, i) => (
                                            <div key={i}>{log}</div>
                                        ))}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={!server || !login || !password}
                                    className="w-full py-3 bg-nexus-blue text-black font-bold rounded-xl hover:bg-nexus-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    CONNECT TERMINAL
                                </button>
                            </form>
                        ) : (
                            <div className="space-y-4">
                                <div className="bg-nexus-green/10 border border-nexus-green/20 p-4 rounded-xl flex items-center gap-3">
                                    <CheckCircle className="text-nexus-green" size={24} />
                                    <div>
                                        <div className="text-white font-bold">MT5 Connected</div>
                                        <div className="text-xs text-nexus-green">{server} • {login}</div>
                                    </div>
                                </div>
                                <div className="space-y-2 bg-white/5 p-4 rounded-xl border border-white/5">
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Equity</span>
                                        <span className="text-white font-mono font-bold">$12,450.00</span>
                                    </div>
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Margin</span>
                                        <span className="text-white font-mono">$1,240.00</span>
                                    </div>
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Free Margin</span>
                                        <span className="text-nexus-green font-mono font-bold">$11,210.00</span>
                                    </div>
                                    <div className="h-px bg-white/10 my-2"></div>
                                    <div className="flex justify-between text-xs text-nexus-subtext">
                                        <span>Margin Level</span>
                                        <span className="text-nexus-blue font-mono">1004%</span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => { setConnected(false); setConnectionLog([]); }}
                                    className="w-full py-2 border border-nexus-red/50 text-nexus-red text-xs font-bold rounded-lg hover:bg-nexus-red/10 transition-colors"
                                >
                                    DISCONNECT
                                </button>
                            </div>
                        )}
                    </div>

                    {/* RISK SETTINGS */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl">
                        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Shield size={20} className="text-nexus-red" />
                            Risk Management
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-xs text-nexus-subtext mb-1">
                                    <span>Max Drawdown</span>
                                    <span className="text-white">15%</span>
                                </div>
                                <div className="h-2 bg-nexus-black rounded-full overflow-hidden">
                                    <div className="h-full bg-nexus-red w-[15%]"></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs text-nexus-subtext mb-1">
                                    <span>Lot Size Allocation</span>
                                    <span className="text-white">Dynamic (AI)</span>
                                </div>
                                <div className="h-2 bg-nexus-black rounded-full overflow-hidden">
                                    <div className="h-full bg-nexus-blue w-[75%]"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CENTER/RIGHT: AI DASHBOARD */}
                <div className="lg:col-span-2 space-y-6">
                    {/* LEARNING VISUALIZATION */}
                    <div className="bg-nexus-card border border-nexus-border p-6 rounded-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4">
                            <Activity className="text-nexus-blue opacity-20" size={100} />
                        </div>
                        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                            <Zap size={20} className="text-nexus-yellow" />
                            Neural Network Status
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Win Rate</div>
                                <div className="text-2xl font-mono font-bold text-nexus-green">78.4%</div>
                                <div className="text-[10px] text-nexus-subtext">Last 100 Trades</div>
                            </div>
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Learning Cycles</div>
                                <div className="text-2xl font-mono font-bold text-nexus-blue">14,205</div>
                                <div className="text-[10px] text-nexus-subtext">Adapting to Volatility</div>
                            </div>
                            <div className="bg-nexus-black/50 p-4 rounded-xl border border-white/5">
                                <div className="text-xs text-nexus-subtext uppercase font-bold">Profit Factor</div>
                                <div className="text-2xl font-mono font-bold text-nexus-yellow">2.45</div>
                                <div className="text-[10px] text-nexus-subtext">High Efficiency</div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-bold text-white">Pattern Recognition: Bullish Divergence</span>
                                <span className="text-xs text-nexus-green animate-pulse">Learning...</span>
                            </div>
                            <div className="h-1.5 bg-nexus-black rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-nexus-blue to-nexus-purple w-[85%] animate-pulse"></div>
                            </div>
                            <p className="text-xs text-nexus-subtext mt-2">
                                The AI is currently analyzing historical data from connected accounts to optimize entry points for the upcoming session.
                            </p>
                        </div>
                    </div>

                    {/* AI CHAT INTERFACE */}
                    <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden flex flex-col h-[500px]">
                        <div className="p-4 border-b border-nexus-border flex justify-between items-center bg-nexus-black/50">
                            <h3 className="font-bold text-white flex items-center gap-2">
                                <MessageSquare size={18} className="text-nexus-blue" />
                                Command Center
                            </h3>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-nexus-green rounded-full animate-pulse"></span>
                                <span className="text-xs text-nexus-subtext">Online</span>
                            </div>
                        </div>

                        {/* Chat Messages */}
                        <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-black/20">
                            {messages.map((msg, index) => (
                                <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-white/10' : 'bg-nexus-blue/10'}`}>
                                        {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-nexus-blue" />}
                                    </div>
                                    <div className={`border rounded-2xl p-3 max-w-[80%] ${msg.role === 'user'
                                            ? 'bg-white/10 border-white/20 rounded-tr-none'
                                            : 'bg-nexus-blue/10 border-nexus-blue/20 rounded-tl-none'
                                        }`}>
                                        <p className="text-sm text-white whitespace-pre-wrap">{msg.text}</p>
                                    </div>
                                </div>
                            ))}
                            {isTyping && (
                                <div className="flex gap-3">
                                    <div className="w-8 h-8 rounded-full bg-nexus-blue/10 flex items-center justify-center shrink-0">
                                        <Bot size={16} className="text-nexus-blue" />
                                    </div>
                                    <div className="bg-nexus-blue/10 border border-nexus-blue/20 rounded-2xl rounded-tl-none p-3">
                                        <Loader size={16} className="text-nexus-blue animate-spin" />
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-4 border-t border-nexus-border bg-nexus-black/50">
                            <form onSubmit={handleSendMessage} className="relative">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Type your instruction..."
                                    className="w-full bg-nexus-black border border-nexus-border rounded-xl py-3 pl-4 pr-12 text-sm text-white focus:border-nexus-blue outline-none transition-colors"
                                    disabled={isTyping}
                                />
                                <button
                                    type="submit"
                                    disabled={!input.trim() || isTyping}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-nexus-blue text-black rounded-lg hover:bg-nexus-blue/90 transition-colors disabled:opacity-50"
                                >
                                    <Send size={16} />
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

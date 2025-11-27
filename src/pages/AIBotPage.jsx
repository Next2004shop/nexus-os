import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Shield, Zap, Activity, AlertTriangle } from 'lucide-react';
import { aiService } from '../services/aiService';

const AIBotPage = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Commander, I am online. Systems are nominal. How can I assist you with your trading operations today?" }
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
        <div className="flex flex-col h-screen bg-nexus-black pb-20 md:pb-0">
            {/* HEADER */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-nexus-black/95 backdrop-blur z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-nexus-blue/20 flex items-center justify-center relative">
                        <Bot className="text-nexus-blue" size={24} />
                        <div className="absolute bottom-0 right-0 w-3 h-3 bg-nexus-green rounded-full border-2 border-nexus-black"></div>
                    </div>
                    <div>
                        <h1 className="font-bold text-white">Nexus Co-Pilot</h1>
                        <div className="flex items-center gap-2 text-xs text-nexus-subtext">
                            <span className="flex items-center gap-1"><Shield size={10} className="text-nexus-green" /> Secure</span>
                            <span className="flex items-center gap-1"><Zap size={10} className="text-nexus-yellow" /> v2.5.0</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button className="p-2 hover:bg-white/5 rounded-lg text-nexus-subtext transition-colors">
                        <Activity size={20} />
                    </button>
                </div>
            </div>

            {/* CHAT AREA */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl p-4 ${msg.role === 'user'
                                ? 'bg-nexus-blue text-black rounded-tr-none'
                                : msg.isWarning
                                    ? 'bg-nexus-red/10 border border-nexus-red text-nexus-red rounded-tl-none'
                                    : 'bg-white/5 border border-white/10 text-white rounded-tl-none'
                            }`}>
                            {msg.isWarning && <div className="flex items-center gap-2 font-bold mb-2"><AlertTriangle size={16} /> RISK ALERT</div>}
                            <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex justify-start">
                        <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-4 flex gap-1">
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
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Give orders or ask for analysis..."
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-4 pr-12 text-white placeholder:text-nexus-subtext focus:outline-none focus:border-nexus-blue transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="absolute right-2 p-2 bg-nexus-blue text-black rounded-lg hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <div className="text-center mt-2">
                    <p className="text-[10px] text-nexus-subtext">Nexus AI can make mistakes. Verify important trade executions.</p>
                </div>
            </div>
        </div>
    );
};

export default AIBotPage;

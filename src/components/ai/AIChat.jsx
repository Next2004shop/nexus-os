import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Cpu, X } from 'lucide-react';

export const AIChat = ({ isOpen, onClose }) => {
    const [messages, setMessages] = useState([
        { id: 1, sender: 'ai', text: 'Nexus Brain Online. Awaiting command.' }
    ]);
    const [input, setInput] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;

        const userMsg = { id: Date.now(), sender: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsThinking(true);

        // Simulate AI processing
        setTimeout(() => {
            const aiResponses = [
                "Analyzing market structure... Bullish divergence detected.",
                "Executing risk protocol. Position size adjusted.",
                "Offshore routing confirmed. Tax liability: 0%.",
                "Scanning for arbitrage opportunities...",
                "Hedge fund allocation updated. Clients notified.",
                "Security alert: Intrusion attempt blocked. Counter-measures deployed."
            ];
            const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];

            setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'ai', text: randomResponse }]);
            setIsThinking(false);
        }, 1500);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] glass-panel rounded-2xl flex flex-col overflow-hidden shadow-2xl z-50 animate-slide-up border border-amber-500/30">
            {/* HEADER */}
            <div className="p-4 border-b border-white/10 bg-black/40 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-500">
                        <Cpu size={18} />
                    </div>
                    <div>
                        <h3 className="font-bold text-sm">NEXUS BRAIN</h3>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            <span className="text-[10px] text-zinc-400 uppercase tracking-wider">Online</span>
                        </div>
                    </div>
                </div>
                <button onClick={onClose} className="text-zinc-400 hover:text-white">
                    <X size={18} />
                </button>
            </div>

            {/* MESSAGES */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map(msg => (
                    <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-xl text-sm ${msg.sender === 'user'
                                ? 'bg-amber-600 text-white rounded-tr-none'
                                : 'bg-white/10 text-zinc-200 rounded-tl-none'
                            }`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                {isThinking && (
                    <div className="flex justify-start">
                        <div className="bg-white/5 p-3 rounded-xl rounded-tl-none flex gap-1">
                            <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"></span>
                            <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-75"></span>
                            <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-150"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* INPUT */}
            <div className="p-4 bg-black/20 border-t border-white/10 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Command Nexus..."
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500/50 transition-colors"
                />
                <button onClick={handleSend} className="p-2 bg-amber-500 rounded-lg text-black hover:bg-amber-400 transition-colors">
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

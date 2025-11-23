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
                    <div className="fixed inset-0 md:inset-auto md:bottom-24 md:right-6 md:w-96 md:h-[500px] bg-[#181a20] md:glass-panel md:rounded-2xl flex flex-col overflow-hidden shadow-2xl z-[100] animate-slide-up border-t md:border border-nexus-gold/30">
                        {/* HEADER */}
                        <div className="p-4 border-b border-[#2b3139] bg-[#0b0e11] flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-nexus-gold/20 flex items-center justify-center text-nexus-gold">
                                    <Cpu size={18} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-sm text-white">NEXUS BRAIN</h3>
                                    <div className="flex items-center gap-1">
                                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                        <span className="text-[10px] text-zinc-400 uppercase tracking-wider">Online</span>
                                    </div>
                                </div>
                            </div>
                            <button onClick={onClose} className="text-zinc-400 hover:text-white p-2">
                                <X size={20} />
                            </button>
                        </div>

                        {/* MESSAGES */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0b0e11]/50">
                            {messages.map(msg => (
                                <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] p-3 rounded-xl text-sm ${msg.sender === 'user'
                                            ? 'bg-nexus-gold text-black font-medium rounded-tr-none'
                                            : 'bg-[#2b3139] text-zinc-200 rounded-tl-none'
                                        }`}>
                                        {msg.text}
                                    </div>
                                </div>
                            ))}
                            {isThinking && (
                                <div className="flex justify-start">
                                    <div className="bg-[#2b3139] p-3 rounded-xl rounded-tl-none flex gap-1">
                                        <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"></span>
                                        <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-75"></span>
                                        <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-150"></span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* INPUT */}
                        <div className="p-4 bg-[#181a20] border-t border-[#2b3139] flex gap-2 pb-8 md:pb-4">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                                placeholder="Ask Nexus..."
                                className="flex-1 bg-[#0b0e11] border border-[#2b3139] rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-nexus-gold/50 transition-colors text-white"
                            />
                            <button onClick={handleSend} className="p-3 bg-nexus-gold rounded-lg text-black hover:bg-[#ffe252] transition-colors shadow-lg">
                                <Send size={20} />
                            </button>
                        </div>
                    </div>
                );
            };

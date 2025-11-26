import React, { useState } from 'react';
import { HelpCircle, MessageSquare, Mail, ChevronDown, ChevronUp, Search, FileText, Shield } from 'lucide-react';

const FAQItem = ({ question, answer }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="border-b border-white/5 last:border-0">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full py-4 flex items-center justify-between text-left hover:bg-white/5 px-2 rounded-lg transition-colors"
            >
                <span className="font-medium text-white text-sm">{question}</span>
                {isOpen ? <ChevronUp size={16} className="text-nexus-blue" /> : <ChevronDown size={16} className="text-nexus-subtext" />}
            </button>
            {isOpen && (
                <div className="pb-4 px-2 text-xs text-nexus-subtext leading-relaxed animate-fadeIn">
                    {answer}
                </div>
            )}
        </div>
    );
};

export const HelpCenterPage = () => {
    const [searchQuery, setSearchQuery] = useState('');

    const faqs = [
        {
            question: "How do I deposit funds?",
            answer: "Go to the Wallet tab, select 'Deposit', and choose your preferred method (Crypto or Bank Transfer). Follow the on-screen instructions to complete the transaction."
        },
        {
            question: "Is my account secure?",
            answer: "Yes, Nexus AI uses military-grade encryption and cold storage for the majority of user funds. We also support 2FA and anti-phishing codes for enhanced security."
        },
        {
            question: "How does the AI Bot work?",
            answer: "The Nexus AI Bot analyzes market data in real-time using advanced neural networks. You can activate it in the 'AI Bot' tab to receive trading signals or automate your strategy."
        },
        {
            question: "What are the trading fees?",
            answer: "We offer competitive fees starting at 0.1% for spot trading. VIP users enjoy discounted rates based on their 30-day trading volume."
        },
        {
            question: "How do I verify my identity (KYC)?",
            answer: "Navigate to Profile > Personal Information to start the verification process. You'll need to upload a valid government ID and a selfie."
        }
    ];

    const filteredFaqs = faqs.filter(faq =>
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-nexus-black pb-24 animate-fadeIn">
            {/* HEADER */}
            <div className="bg-nexus-card border-b border-nexus-border p-6">
                <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                    <HelpCircle className="text-nexus-blue" /> Help Center
                </h1>
                <p className="text-nexus-subtext text-sm mb-6">Find answers or contact our support team.</p>

                <div className="relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-nexus-subtext" />
                    <input
                        type="text"
                        placeholder="Search for help..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-nexus-black border border-nexus-border rounded-xl py-3 pl-10 pr-4 text-sm text-white focus:border-nexus-blue outline-none transition-colors"
                    />
                </div>
            </div>

            <div className="p-4 max-w-2xl mx-auto space-y-6">
                {/* QUICK ACTIONS */}
                <div className="grid grid-cols-2 gap-4">
                    <button className="bg-nexus-card border border-nexus-border p-4 rounded-xl flex flex-col items-center gap-2 hover:border-nexus-blue/50 transition-colors group">
                        <div className="w-10 h-10 rounded-full bg-nexus-blue/10 flex items-center justify-center group-hover:bg-nexus-blue/20 transition-colors">
                            <MessageSquare size={20} className="text-nexus-blue" />
                        </div>
                        <span className="text-sm font-bold text-white">Live Chat</span>
                        <span className="text-[10px] text-nexus-green">Online Now</span>
                    </button>
                    <button className="bg-nexus-card border border-nexus-border p-4 rounded-xl flex flex-col items-center gap-2 hover:border-nexus-blue/50 transition-colors group">
                        <div className="w-10 h-10 rounded-full bg-nexus-purple/10 flex items-center justify-center group-hover:bg-nexus-purple/20 transition-colors">
                            <Mail size={20} className="text-nexus-purple" />
                        </div>
                        <span className="text-sm font-bold text-white">Email Support</span>
                        <span className="text-[10px] text-nexus-subtext">Response in 24h</span>
                    </button>
                </div>

                {/* FAQ SECTION */}
                <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden p-4">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FileText size={18} className="text-nexus-yellow" />
                        Frequently Asked Questions
                    </h2>
                    <div className="space-y-1">
                        {filteredFaqs.length > 0 ? (
                            filteredFaqs.map((faq, index) => (
                                <FAQItem key={index} {...faq} />
                            ))
                        ) : (
                            <div className="text-center py-8 text-nexus-subtext text-sm">
                                No results found for "{searchQuery}"
                            </div>
                        )}
                    </div>
                </div>

                {/* SECURITY TIP */}
                <div className="bg-nexus-green/10 border border-nexus-green/20 rounded-xl p-4 flex items-start gap-3">
                    <Shield size={20} className="text-nexus-green shrink-0 mt-0.5" />
                    <div>
                        <h3 className="text-sm font-bold text-white">Security Tip</h3>
                        <p className="text-xs text-nexus-subtext mt-1">
                            Nexus AI support will NEVER ask for your password or 2FA codes. Keep your account credentials safe.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

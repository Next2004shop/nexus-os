import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { MobileNav } from './components/layout/MobileNav';
import { HomePage } from './pages/HomePage';
import { TradePage } from './pages/TradePage';
import { WalletPage } from './pages/WalletPage';
import { BrokersPage } from './pages/BrokersPage';
import { TaxPage } from './pages/TaxPage';
import { HedgeFundPage } from './pages/HedgeFundPage';
import { SecurityMonitor } from './components/security/SecurityMonitor';
import { AIChat } from './components/ai/AIChat';
import { checkStatus } from './services/api';
import { MessageSquare } from 'lucide-react';

export default function NexusAI() {
   const [activeTab, setActiveTab] = useState('home'); // Default to Home
   const [marketType, setMarketType] = useState('CRYPTO');
   const [ticker, setTicker] = useState('BTC/USD');
   const [connectionStatus, setConnectionStatus] = useState('OFFLINE');
   const [isListening, setIsListening] = useState(false);
   const [isChatOpen, setIsChatOpen] = useState(false);

   // Check Bridge Status
   useEffect(() => {
      const check = async () => {
         const status = await checkStatus();
         if (status.status === 'ONLINE') setConnectionStatus('ONLINE');
         else if (status.status === 'DEMO') setConnectionStatus('DEMO');
         else setConnectionStatus('OFFLINE');
      };
      check();
      const interval = setInterval(check, 10000);
      return () => clearInterval(interval);
   }, []);

   const startListening = () => {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
         const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
         const recognition = new SpeechRecognition();
         recognition.continuous = false;
         recognition.lang = 'en-US';
         setIsListening(true);
         recognition.start();
         recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase();
            setIsListening(false);
            // Simple voice command routing
            if (transcript.includes('home')) setActiveTab('home');
            else if (transcript.includes('wallet')) setActiveTab('wallet');
            else if (transcript.includes('trade')) setActiveTab('trade');
            else if (transcript.includes('hedge')) setActiveTab('hedge');
            else if (transcript.includes('security')) setActiveTab('security');
         };
         recognition.onerror = () => setIsListening(false);
      } else {
         alert("Voice control not supported.");
      }
   };

   return (
      <div className="h-screen w-screen bg-[#0b0e11] text-[#eaecef] font-sans overflow-hidden selection:bg-nexus-gold/30 flex flex-col md:flex-row">

         {/* DESKTOP SIDEBAR - Hidden on mobile */}
         <div className="hidden md:block shrink-0">
            <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
         </div>

         {/* MAIN CONTENT AREA */}
         <div className="flex-1 flex flex-col h-full relative min-w-0">
            {/* BACKGROUND GRID */}
            <div className="absolute inset-0 bg-[radial-gradient(#ffffff05_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>

            {/* HEADER */}
            <Header
               balance={24593.42}
               isListening={isListening}
               onMicClick={startListening}
               connectionStatus={connectionStatus}
            />

            {/* SCROLLABLE PAGE CONTENT */}
            <main className="flex-1 overflow-y-auto overflow-x-hidden relative z-10 pb-[80px] md:pb-0 custom-scrollbar">
               {activeTab === 'home' && <HomePage onNavigate={setActiveTab} />}
               {activeTab === 'trade' && (
                  <TradePage
                     ticker={ticker}
                     setTicker={setTicker}
                     marketType={marketType}
                     setMarketType={setMarketType}
                  />
               )}
               {activeTab === 'wallet' && <WalletPage />}
               {activeTab === 'hedge' && <HedgeFundPage />}
               {activeTab === 'security' && (
                  <div className="p-6 max-w-4xl mx-auto">
                     <h1 className="text-3xl font-black mb-6 text-white">SECURITY <span className="text-red-500">COMMAND</span></h1>
                     <SecurityMonitor />
                  </div>
               )}
               {activeTab === 'brokers' && <BrokersPage />}
               {activeTab === 'tax' && <TaxPage />}
            </main>

            {/* AI CHAT BUTTON */}
            <button
               onClick={() => setIsChatOpen(!isChatOpen)}
               className="fixed bottom-24 right-6 w-14 h-14 bg-nexus-gold rounded-full flex items-center justify-center text-black shadow-[0_0_20px_rgba(252,213,53,0.4)] hover:scale-110 transition-transform z-50 md:bottom-8"
            >
               <MessageSquare size={24} fill="black" />
            </button>

            {/* AI CHAT WINDOW */}
            <AIChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
         </div>

         {/* MOBILE NAV - Fixed bottom */}
         <MobileNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
   );
}
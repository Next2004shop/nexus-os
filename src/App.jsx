import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { MobileNav } from './components/layout/MobileNav';
import { TradePage } from './pages/TradePage';
import { WalletPage } from './pages/WalletPage';
import { BrokersPage } from './pages/BrokersPage';
import { TaxPage } from './pages/TaxPage';
import { checkStatus } from './services/api';

export default function NexusAI() {
   const [activeTab, setActiveTab] = useState('trade');
   const [marketType, setMarketType] = useState('CRYPTO');
   const [ticker, setTicker] = useState('BTC/USD');
   const [connectionStatus, setConnectionStatus] = useState('OFFLINE');
   const [isListening, setIsListening] = useState(false);

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
            if (transcript.includes('wallet')) setActiveTab('wallet');
            else if (transcript.includes('trade')) setActiveTab('trade');
         };
         recognition.onerror = () => setIsListening(false);
      } else {
         alert("Voice control not supported.");
      }
   };

   return (
      <div className="flex h-screen bg-[#000000] text-white font-sans overflow-hidden selection:bg-amber-500/30">

         {/* SIDEBAR */}
         <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

         {/* MAIN AREA */}
         <div className="flex-1 flex flex-col relative pb-[80px] md:pb-0 overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(#ffffff05_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>

            {/* HEADER */}
            <Header
               balance={24593.42}
               isListening={isListening}
               onMicClick={startListening}
               connectionStatus={connectionStatus}
            />

            {/* CONTENT */}
            <div className="flex-1 overflow-hidden relative z-10">
               {activeTab === 'trade' && (
                  <TradePage
                     ticker={ticker}
                     setTicker={setTicker}
                     marketType={marketType}
                     setMarketType={setMarketType}
                  />
               )}
               {activeTab === 'wallet' && <WalletPage />}
               {activeTab === 'brokers' && <BrokersPage />}
               {activeTab === 'tax' && <TaxPage />}
            </div>
         </div>

         {/* MOBILE NAV */}
         <MobileNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
   );
}
import React, { useState, useEffect } from 'react';
import { BottomNav } from './components/layout/BottomNav';
import { TopHeader } from './components/layout/TopHeader';
import { HomePage } from './pages/HomePage';
import { TradePage } from './pages/TradePage';
import { WalletPage } from './pages/WalletPage';
import { checkStatus } from './services/api';
import { MarketsPage } from './pages/MarketsPage';
import { AuthPage } from './pages/AuthPage';
import { FuturesPage } from './pages/FuturesPage';
import { NewsFeed } from './pages/NewsFeed';

export default function NexusAI() {
   const [activeTab, setActiveTab] = useState('home');
   const [showAuth, setShowAuth] = useState(false);
   const [connectionStatus, setConnectionStatus] = useState('OFFLINE');

   useEffect(() => {
      const check = async () => {
         try {
            const status = await checkStatus();
            if (status.status === 'ONLINE') setConnectionStatus('ONLINE');
            else if (status.status === 'DEMO') setConnectionStatus('DEMO');
            else setConnectionStatus('OFFLINE');
         } catch (e) {
            setConnectionStatus('OFFLINE');
         }
      };
      check();
      const interval = setInterval(check, 10000);
      return () => clearInterval(interval);
   }, []);

   return (
      <div className="min-h-screen bg-nexus-black text-nexus-text font-sans pb-20">
         {/* AUTH MODAL */}
         {showAuth && <AuthPage onClose={() => setShowAuth(false)} />}

         {/* Top Header */}
         {(activeTab === 'home' || activeTab === 'markets' || activeTab === 'news') && (
            <TopHeader onProfileClick={() => setShowAuth(true)} />
         )}

         {/* Main Content Area */}
         <main className="flex-1 overflow-y-auto custom-scrollbar">
            {activeTab === 'home' && <HomePage onNavigate={setActiveTab} />}
            {activeTab === 'markets' && <MarketsPage />}
            {activeTab === 'trade' && <TradePage />}
            {activeTab === 'futures' && <FuturesPage />}
            {activeTab === 'wallet' && <WalletPage />}
            {activeTab === 'news' && <NewsFeed />}
         </main>

         {/* Bottom Navigation */}
         <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
   );
}
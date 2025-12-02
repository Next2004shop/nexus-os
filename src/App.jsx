import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Zap } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { Sidebar } from './components/layout/Sidebar';
import { MobileNav } from './components/layout/MobileNav';
import { AuthPage } from './pages/AuthPage';
import TradePage from './pages/TradePage';
import { StocksPage } from './pages/StocksPage';
import { CommoditiesPage } from './pages/CommoditiesPage';
import AIBotPage from './pages/AIBotPage';
import { ServicesPage } from './pages/ServicesPage';
import BankingPage from './pages/BankingPage';
import { TaxPage } from './pages/TaxPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SecurityPage } from './pages/SecurityPage';
import { InvestmentsPage } from './pages/InvestmentsPage';
import { DownloadPage } from './pages/DownloadPage';
import { NesaAgent } from './components/agents/NesaAgent';

// MAINTENANCE SCREEN COMPONENT
const MaintenanceScreen = () => (
   <div className="fixed inset-0 z-[9999] bg-nexus-black flex flex-col items-center justify-center p-6 text-center animate-fadeIn">
      <div className="w-24 h-24 bg-nexus-yellow/10 rounded-full flex items-center justify-center mb-6 animate-pulse">
         <Zap size={48} className="text-nexus-yellow" />
      </div>
      <h1 className="text-3xl font-bold text-white mb-2">System Upgrade in Progress</h1>
      <p className="text-nexus-subtext max-w-md mb-8">
         Nexus AI is currently undergoing a critical infrastructure upgrade.
         We are installing new trading algorithms and security patches.
      </p>
      <div className="w-full max-w-xs bg-white/5 rounded-full h-1.5 overflow-hidden">
         <div className="h-full bg-nexus-yellow animate-progress w-full origin-left"></div>
      </div>
      <p className="text-xs text-nexus-subtext mt-4 font-mono">EST. TIME REMAINING: 5 SECONDS</p>
   </div>
);

export default function App() {
   const [maintenance, setMaintenance] = useState(false);

   // POLL SERVER STATUS (5s Updates)
   useEffect(() => {
      const checkStatus = async () => {
         try {
            const res = await fetch('/api/status');
            const data = await res.json();
            if (data.maintenance) {
               setMaintenance(true);
            } else {
               setMaintenance(false);
            }
         } catch (e) {
            // If server is down/restarting, assume maintenance or offline
            console.log("Server unreachable, potential update...");
         }
      };

      const interval = setInterval(checkStatus, 5000);
      return () => clearInterval(interval);
   }, []);

   if (maintenance) {
      return <MaintenanceScreen />;
   }

   return (
      <ToastProvider>
         <NesaAgent />
         <div className="flex h-screen bg-nexus-black text-white overflow-hidden font-sans selection:bg-nexus-green/30">
            {/* DESKTOP SIDEBAR (Hidden on Mobile) */}
            <div className="hidden md:block w-64 flex-shrink-0 border-r border-white/5">
               <Sidebar />
            </div>

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 flex flex-col h-full relative overflow-hidden">
               <div className="flex-1 overflow-y-auto scrollbar-hide pb-20 md:pb-0">
                  <Routes>
                     <Route path="/" element={<Navigate to="/trade" replace />} />
                     <Route path="/trade" element={<TradePage />} />
                     <Route path="/stocks" element={<StocksPage />} />
                     <Route path="/commodities" element={<CommoditiesPage />} />
                     <Route path="/ai-bot" element={<AIBotPage />} />
                     <Route path="/wallet" element={<WalletPage />} />
                     <Route path="/services" element={<ServicesPage />} />
                     <Route path="/banking" element={<BankingPage />} />
                     <Route path="/tax" element={<TaxPage />} />
                     <Route path="/notifications" element={<NotificationsPage />} />
                     <Route path="/profile" element={<ProfilePage />} />
                     <Route path="/security" element={<SecurityPage />} />
                     <Route path="/investments" element={<InvestmentsPage />} />
                     <Route path="/downloads" element={<DownloadPage />} />
                  </Routes>
               </div>

               {/* MOBILE NAVIGATION (Hidden on Desktop) */}
               <div className="md:hidden absolute bottom-0 left-0 right-0 z-50">
                  <MobileNav />
               </div>
            </div>
         </div>
      </ToastProvider>
   );
}
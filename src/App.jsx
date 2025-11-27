
import React, { useState } from 'react';
import { ModernLayout } from './components/layout/ModernLayout';
import HomePage from './pages/HomePage';
import TradePage from './pages/TradePage';
import { WalletPage } from './pages/WalletPage';
import { ProfilePage } from './pages/ProfilePage';
import { AuthPage } from './pages/AuthPage';
import BankingPage from './pages/BankingPage';
import { HedgeFundPage } from './pages/HedgeFundPage';
import { AIBotPage } from './pages/AIBotPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { StocksPage } from './pages/StocksPage';
import { CommoditiesPage } from './pages/CommoditiesPage';
import { NewsFeed } from './components/home/NewsFeed';
import { SecurityPage } from './pages/SecurityPage';
import { BrokersPage } from './pages/BrokersPage';
import { HelpCenterPage } from './pages/HelpCenterPage';
import ErrorBoundary from './components/ErrorBoundary';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'; // Added for routing
import { Zap } from 'lucide-react'; // Assuming lucide-react for Zap icon
import Sidebar from './components/layout/Sidebar'; // Assuming these components exist
import MobileNav from './components/layout/MobileNav'; // Assuming these components exist
import { InvestmentsPage } from './pages/InvestmentsPage'; // Assuming these pages exist
import { TaxPage } from './pages/TaxPage'; // Assuming these pages exist


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

export default function App() { // Renamed NexusAI to App
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
      }
import React, { useState } from 'react';
import { ModernLayout } from './components/layout/ModernLayout';
import HomePage from './pages/HomePage';
import TradePage from './pages/TradePage';
import { WalletPage } from './pages/WalletPage';
import { ProfilePage } from './pages/ProfilePage';
import { AuthPage } from './pages/AuthPage';
import BankingPage from './pages/BankingPage';
import InvestmentsPage from './pages/InvestmentsPage';
import { useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import ErrorBoundary from './components/ErrorBoundary';


export default function NexusAI() {
   const [activeTab, setActiveTab] = useState('home');
   const { currentUser, loading } = useAuth();

   if (loading) {
      return (
         <div className="min-h-screen bg-nexus-black flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-nexus-blue shadow-[0_0_15px_#00F0FF]"></div>
         </div>
      );
   }

   const renderContent = () => {
      switch (activeTab) {
         case 'home': return <HomePage onNavigate={setActiveTab} />;
         case 'trade': return <TradePage />;
         case 'wallet': return <WalletPage />;
         case 'banking': return <BankingPage />;
         case 'investments': return <InvestmentsPage />;
         case 'profile': return <ProfilePage />;
         default: return <HomePage onNavigate={setActiveTab} />;
      }
   };

   return (
      <ErrorBoundary>
         <ToastProvider>
            {!currentUser ? (
               <AuthPage onClose={() => { }} />
            ) : (
               <ModernLayout activeTab={activeTab} onNavigate={setActiveTab}>
                  {renderContent()}
               </ModernLayout>
            )}
         </ToastProvider>
      </ErrorBoundary>
   );
}
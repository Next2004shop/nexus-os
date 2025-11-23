import React from 'react';
import { Mic, Bell, Settings, Wifi, WifiOff } from 'lucide-react';

export const Header = ({ balance, isListening, onMicClick, connectionStatus, onSettingsClick, onNotificationsClick }) => {
    return (
        <header className="h-16 flex items-center justify-between px-6 bg-black/40 backdrop-blur-md border-b border-white/5 z-20 shrink-0">
            <div className="flex items-center gap-4">
                <div className="md:hidden w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center text-black font-bold">N</div>
                <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/5">
                    {connectionStatus === 'ONLINE' ? <Wifi size={14} className="text-emerald-500" /> :
                        connectionStatus === 'DEMO' ? <Wifi size={14} className="text-amber-500" /> :
                            <WifiOff size={14} className="text-rose-500" />}
                    <span className={`text-[10px] font-mono ${connectionStatus === 'DEMO' ? 'text-amber-500' : 'text-zinc-400'}`}>{connectionStatus}</span>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className="text-right hidden sm:block">
                    <div className="text-[9px] text-zinc-500 uppercase font-mono">Total Balance</div>
                    <div className="text-sm font-mono font-bold text-white">${balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                </div>

                <button onClick={onNotificationsClick} className="p-2 hover:bg-white/5 rounded-full text-zinc-400 hover:text-white transition-colors">
                    <Bell size={18} />
                </button>

                <button onClick={onMicClick} className={`p-2 rounded-full transition-all ${isListening ? 'bg-rose-600 animate-pulse text-white' : 'bg-white/5 hover:bg-white/10 text-zinc-400'}`}>
                    <Mic size={18} />
                </button>

                <button onClick={onSettingsClick} className="p-2 hover:bg-white/5 rounded-full text-zinc-400 hover:text-white transition-colors">
                    <Settings size={18} />
                </button>
            </div>
        </header>
    );
};

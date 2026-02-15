import React from 'react';
import { WifiOff, Loader2 } from 'lucide-react';

interface ConnectionStatusProps {
    status: 'connecting' | 'offline';
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ status }) => {
    if (status === 'connecting') {
        return (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
                <Loader2 className="w-8 h-8 text-green-500 animate-spin" />
                <p className="text-zinc-500 text-xs font-mono uppercase tracking-wider">
                    Establishing connection to Nexus Core...
                </p>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
            <div className="w-16 h-16 rounded-full border-2 border-zinc-800 flex items-center justify-center">
                <WifiOff className="w-6 h-6 text-zinc-600" />
            </div>
            <div>
                <p className="text-zinc-400 text-xs font-mono uppercase tracking-wider mb-1">
                    Nexus Core Unreachable
                </p>
                <p className="text-zinc-700 text-[10px] font-mono max-w-xs">
                    Backend is offline or unavailable. The dashboard will auto-reconnect when the core comes back online.
                </p>
            </div>
            <div className="mt-2 px-3 py-1.5 border border-zinc-800 rounded-sm">
                <p className="text-zinc-600 text-[10px] font-mono">
                    Expected: <span className="text-zinc-400">{getApiUrl()}</span>
                </p>
            </div>
        </div>
    );
};

function getApiUrl(): string {
    if (typeof window !== 'undefined' && (window as any).NEXUS_CONFIG?.VITE_API_URL) {
        return (window as any).NEXUS_CONFIG.VITE_API_URL;
    }
    return import.meta.env.VITE_API_URL || 'http://localhost:8080';
}

export default ConnectionStatus;

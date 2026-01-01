import React from 'react';
import Dashboard from './components/Dashboard';

function App() {
    return (
        <div className="bg-zinc-950 text-green-500 min-h-screen selection:bg-green-500 selection:text-black">
            {/* Header Overlay */}
            <header className="p-4 border-b border-zinc-900 flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <h1 className="text-sm font-bold tracking-[0.3em] uppercase">Nexus Sovereign</h1>
                    <span className="text-[10px] bg-green-500/10 text-green-700 px-2 py-0.5 rounded-full border border-green-500/20">Term_v1.0.4</span>
                </div>
                <div className="text-[10px] text-zinc-600 flex gap-4 uppercase">
                    <span>Encrypted_Link: Active</span>
                    <span>Ghost_Mode: Enabled</span>
                </div>
            </header>

            {/* Control Deck */}
            <main>
                <Dashboard />
            </main>

            {/* Footer Status Bar */}
            <footer className="fixed bottom-0 w-full p-2 border-t border-zinc-900 flex justify-between items-center text-[9px] text-zinc-700 uppercase bg-zinc-950">
                <div className="flex gap-4">
                    <span>Pos: 40.7128° N, 74.0060° W</span>
                    <span>Secret_Manager: Verified</span>
                </div>
                <div>
                    <span>© 2025 NEXUS_GENESIS // Ancient_Market_Law</span>
                </div>
            </footer>
        </div>
    );
}

export default App;

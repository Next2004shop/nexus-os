import React from 'react';
import { Bot, RefreshCw, ShieldAlert } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, recoveryAttempts: 0 };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ error });
        console.error("System Agent Detected Error:", error, errorInfo);

        // Auto-Recovery Logic (Self-Healing)
        if (this.state.recoveryAttempts < 2) {
            console.log(`Agent: Attempting auto-recovery (${this.state.recoveryAttempts + 1}/2)...`);
            setTimeout(() => {
                this.setState(prevState => ({
                    hasError: false,
                    recoveryAttempts: prevState.recoveryAttempts + 1
                }));
            }, 2000); // Wait 2s then retry rendering
        }
    }

    handleManualReboot = () => {
        localStorage.clear(); // Clear potential bad state
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            const isRecovering = this.state.recoveryAttempts < 2;

            return (
                <div className="h-screen w-screen bg-black text-white flex flex-col items-center justify-center p-8 text-center animate-fadeIn">
                    <div className={`w-24 h-24 rounded-full bg-nexus-blue/10 flex items-center justify-center mb-6 ${isRecovering ? 'animate-pulse' : ''}`}>
                        <Bot size={48} className="text-nexus-blue" />
                    </div>

                    <h1 className="text-2xl font-bold mb-2">
                        {isRecovering ? 'Agent Analyzing Issue...' : 'System Malfunction Detected'}
                    </h1>

                    <p className="text-nexus-subtext mb-8 max-w-md">
                        {isRecovering
                            ? "I've detected an anomaly. Attempting to stabilize the neural link..."
                            : "I could not auto-recover this sector. A manual reboot is required to flush the cache."}
                    </p>

                    {!isRecovering && (
                        <div className="bg-nexus-card p-6 rounded-xl border border-nexus-red/30 max-w-lg w-full text-left mb-8">
                            <div className="flex items-center gap-2 text-nexus-red mb-2 font-bold text-xs uppercase tracking-wider">
                                <ShieldAlert size={14} /> Critical Error Log
                            </div>
                            <pre className="text-[10px] font-mono text-nexus-subtext whitespace-pre-wrap break-all">
                                {this.state.error && this.state.error.toString()}
                            </pre>
                        </div>
                    )}

                    {!isRecovering && (
                        <button
                            onClick={this.handleManualReboot}
                            className="px-8 py-3 bg-nexus-blue hover:bg-nexus-blue/90 text-black rounded-xl font-bold transition-all flex items-center gap-2"
                        >
                            <RefreshCw size={18} /> REBOOT SYSTEM
                        </button>
                    )}
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

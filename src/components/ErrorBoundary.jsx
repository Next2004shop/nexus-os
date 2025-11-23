import React from 'react';
import { AlertTriangle } from 'lucide-react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ error, errorInfo });
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="h-screen w-screen bg-black text-white flex flex-col items-center justify-center p-8 text-center">
                    <AlertTriangle size={64} className="text-red-500 mb-6" />
                    <h1 className="text-3xl font-bold mb-4">System Malfunction</h1>
                    <p className="text-zinc-400 mb-8 max-w-md">
                        The Nexus interface encountered a critical error.
                        Our automated recovery systems are analyzing the crash.
                    </p>

                    <div className="bg-zinc-900 p-6 rounded-xl border border-red-500/20 max-w-2xl w-full overflow-auto text-left">
                        <h3 className="text-red-500 font-mono font-bold mb-2">ERROR LOG:</h3>
                        <pre className="text-xs font-mono text-zinc-300 whitespace-pre-wrap">
                            {this.state.error && this.state.error.toString()}
                        </pre>
                        <div className="mt-4 pt-4 border-t border-white/10">
                            <h3 className="text-zinc-500 font-mono font-bold mb-2">STACK TRACE:</h3>
                            <pre className="text-xs font-mono text-zinc-500 whitespace-pre-wrap">
                                {this.state.errorInfo && this.state.errorInfo.componentStack}
                            </pre>
                        </div>
                    </div>

                    <button
                        onClick={() => window.location.reload()}
                        className="mt-8 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-bold transition-colors"
                    >
                        REBOOT SYSTEM
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

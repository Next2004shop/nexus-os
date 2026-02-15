import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error('[NEXUS] UI Error:', error, info.componentStack);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-8">
                    <div className="border border-red-900/50 bg-red-950/20 rounded-sm p-8 max-w-lg w-full text-center">
                        <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-4" />
                        <h2 className="text-red-500 text-sm uppercase tracking-widest mb-2 font-mono">
                            System Fault Detected
                        </h2>
                        <p className="text-zinc-500 text-xs font-mono mb-1">
                            {this.state.error?.message || 'Unknown error'}
                        </p>
                        <p className="text-zinc-700 text-[10px] font-mono mb-6">
                            The UI encountered an unrecoverable error. Core systems are unaffected.
                        </p>
                        <button
                            onClick={this.handleReset}
                            className="inline-flex items-center gap-2 px-4 py-2 border border-zinc-700 text-zinc-400 text-xs font-mono uppercase tracking-wider hover:border-green-700 hover:text-green-500 transition-colors rounded-sm"
                        >
                            <RefreshCw className="w-3 h-3" />
                            Reinitialize
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

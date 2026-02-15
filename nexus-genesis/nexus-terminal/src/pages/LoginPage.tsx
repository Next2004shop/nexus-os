import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock } from 'lucide-react';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(username, password);

        if (result.success) {
            navigate('/', { replace: true });
        } else {
            setError(result.error || 'Authentication failed');
        }

        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-nexus-bg flex items-center justify-center p-4">
            <div className="w-full max-w-sm">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-nexus-surface border border-nexus-border rounded-lg mb-4">
                        <Lock className="w-5 h-5 text-nexus-accent" />
                    </div>
                    <h1 className="text-xl font-semibold text-nexus-text">NEXUS</h1>
                    <p className="text-xs text-nexus-muted mt-1 font-mono tracking-wider">SOVEREIGN TRADING SYSTEM</p>
                </div>

                {/* Login Form */}
                <form onSubmit={handleSubmit} className="bg-nexus-surface border border-nexus-border rounded-lg p-6 space-y-4">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-xs text-nexus-muted font-medium mb-1.5 uppercase tracking-wider">
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="input-field font-mono"
                            placeholder="Enter username"
                            required
                            autoFocus
                            autoComplete="username"
                        />
                    </div>

                    <div>
                        <label className="block text-xs text-nexus-muted font-medium mb-1.5 uppercase tracking-wider">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="input-field font-mono"
                            placeholder="Enter password"
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !username || !password}
                        className="btn-primary w-full mt-2"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Authenticating...
                            </span>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>

                {/* Footer */}
                <p className="text-center text-xs text-nexus-muted mt-6 font-mono">
                    Unauthorized access is prohibited
                </p>
            </div>
        </div>
    );
}

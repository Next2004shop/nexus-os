import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, AlertTriangle, ExternalLink, RefreshCw, Zap } from 'lucide-react';

export const OpportunitiesPage = () => {
    const [opportunities, setOpportunities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchOpportunities = async (isMock = false) => {
        setLoading(true);
        setError(null);
        try {
            const url = isMock
                ? 'http://127.0.0.1:5001/api/ma-opportunities?mock=true'
                : 'http://127.0.0.1:5001/api/ma-opportunities';

            const res = await fetch(url, {
                headers: {
                    'Authorization': 'Basic ' + btoa('admin:securepassword') // Using default auth for now
                }
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || 'Failed to fetch opportunities');
            }

            const data = await res.json();
            setOpportunities(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOpportunities();
    }, []);

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        <Search className="text-nexus-green" />
                        M&A Opportunity Scanner
                    </h1>
                    <p className="text-nexus-subtext">
                        AI-powered analysis of market news to identify potential acquisition targets.
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => fetchOpportunities(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-nexus-gold/10 hover:bg-nexus-gold/20 text-nexus-gold rounded-lg transition-colors border border-nexus-gold/30"
                    >
                        <Zap size={18} />
                        Demo Mode
                    </button>
                    <button
                        onClick={() => fetchOpportunities(false)}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-white transition-colors disabled:opacity-50"
                    >
                        <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
                        Scan Market
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 flex items-start gap-3">
                    <AlertTriangle className="text-red-400 flex-shrink-0" />
                    <div>
                        <h3 className="text-red-400 font-medium">Scan Failed</h3>
                        <p className="text-red-400/80 text-sm">{error}</p>
                        {error.includes("API key") && (
                            <p className="text-red-400/60 text-xs mt-2">
                                Please check your Vertex AI API key in .env.local
                            </p>
                        )}
                    </div>
                </div>
            )}

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="bg-white/5 rounded-xl p-6 h-64 animate-pulse" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {opportunities.length === 0 && !error ? (
                        <div className="col-span-full text-center py-20 text-nexus-subtext">
                            No high-confidence opportunities found in recent news.
                        </div>
                    ) : (
                        opportunities.map((opp, idx) => (
                            <div key={idx} className="bg-white/5 border border-white/10 rounded-xl p-6 hover:border-nexus-green/30 transition-colors group">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-xl font-bold text-white">{opp.target_company}</h3>
                                        <p className="text-sm text-nexus-subtext">Target</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="flex items-center gap-1 text-nexus-green font-mono font-bold">
                                            <TrendingUp size={16} />
                                            {opp.likelihood_score}%
                                        </div>
                                        <p className="text-xs text-nexus-subtext">Confidence</p>
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <p className="text-sm text-white/60 mb-1">Potential Acquirer</p>
                                    <p className="text-white font-medium">{opp.acquirer}</p>
                                </div>

                                <div className="bg-black/20 rounded-lg p-3 mb-4">
                                    <p className="text-sm text-white/80 leading-relaxed">
                                        {opp.reasoning}
                                    </p>
                                </div>

                                <a
                                    href={opp.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-xs text-nexus-green hover:underline"
                                >
                                    Source: {opp.source_title}
                                    <ExternalLink size={12} />
                                </a>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

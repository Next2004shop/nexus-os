import React, { useState, useEffect } from 'react';
import { ExternalLink, Clock, TrendingUp } from 'lucide-react';

export const NewsFeed = () => {
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchNews = async () => {
            try {
                // Fetching from CryptoCompare Public API
                const res = await fetch('https://min-api.cryptocompare.com/data/v2/news/?lang=EN');
                const data = await res.json();
                setNews(data.Data.slice(0, 10)); // Top 10 stories
                setLoading(false);
            } catch (e) {
                console.error("Failed to fetch news", e);
                setLoading(false);
            }
        };
        fetchNews();
    }, []);

    if (loading) return <div className="p-4 text-center text-zinc-500 animate-pulse">Loading Global Market News...</div>;

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-4 px-2">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <TrendingUp className="text-nexus-gold" />
                    Market Pulse
                </h2>
                <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-1 rounded-full flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> LIVE
                </span>
            </div>

            {/* Vertical Stack for Mobile, Grid for Desktop */}
            <div className="flex flex-col space-y-4 md:space-y-0 md:grid md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
                {news.map(item => (
                    <a
                        key={item.id}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full glass-panel overflow-hidden group hover:border-nexus-gold transition-all duration-300 flex flex-col"
                    >
                        <div className="h-40 overflow-hidden relative">
                            <img
                                src={item.imageurl}
                                alt={item.title}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                            />
                            <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-bold text-white">
                                {item.source_info.name}
                            </div>
                        </div>
                        <div className="p-4 flex-1 flex flex-col justify-between">
                            <div>
                                <h3 className="font-bold text-sm mb-2 line-clamp-2 leading-tight group-hover:text-nexus-gold transition-colors">
                                    {item.title}
                                </h3>
                                <p className="text-xs text-zinc-400 line-clamp-3 mb-3">
                                    {item.body}
                                </p>
                            </div>
                            <div className="flex justify-between items-center text-[10px] text-zinc-500 border-t border-zinc-800 pt-3">
                                <span className="flex items-center gap-1">
                                    <Clock size={10} />
                                    {new Date(item.published_on * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                                <span className="flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                                    Read <ExternalLink size={10} />
                                </span>
                            </div>
                        </div>
                    </a>
                ))}
            </div>
        </div>
    );
};

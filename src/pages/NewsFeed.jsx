import React from 'react';
import { Clock, ExternalLink } from 'lucide-react';

const NewsItem = ({ title, source, time, image }) => (
    <div className="flex gap-4 py-4 border-b border-nexus-border last:border-0">
        <div className="flex-1">
            <h3 className="font-bold text-nexus-text text-sm leading-snug mb-2 line-clamp-2">{title}</h3>
            <div className="flex items-center gap-2 text-xs text-nexus-subtext">
                <span>{source}</span>
                <span>•</span>
                <span className="flex items-center gap-1"><Clock size={10} /> {time}</span>
            </div>
        </div>
        {image && (
            <div className="w-20 h-20 rounded-lg bg-nexus-border overflow-hidden shrink-0">
                <img src={image} alt="News" className="w-full h-full object-cover" />
            </div>
        )}
    </div>
);

export const NewsFeed = () => {
    return (
        <div className="bg-nexus-black min-h-screen pb-20">
            <div className="sticky top-0 bg-nexus-black z-30 px-4 py-3 border-b border-nexus-border">
                <h1 className="text-xl font-bold text-nexus-text">News</h1>
            </div>

            <div className="px-4">
                <NewsItem
                    title="Bitcoin Surges Past $64k as ETF Inflows Reach Record Highs"
                    source="CoinDesk"
                    time="2h ago"
                    image="https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=200&h=200&fit=crop"
                />
                <NewsItem
                    title="Ethereum Foundation Announces New Upgrade Roadmap for 2025"
                    source="The Block"
                    time="4h ago"
                    image="https://images.unsplash.com/photo-1622790698141-94e30457ef12?w=200&h=200&fit=crop"
                />
                <NewsItem
                    title="Solana Network Activity Spikes Amidst New Meme Coin Frenzy"
                    source="Decrypt"
                    time="5h ago"
                    image="https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=200&h=200&fit=crop"
                />
                <NewsItem
                    title="Regulatory Clarity: New Bill Proposed to Define Digital Assets"
                    source="Bloomberg"
                    time="8h ago"
                />
                <NewsItem
                    title="Top 5 Altcoins to Watch This Week: Analysis and Predictions"
                    source="CryptoSlate"
                    time="12h ago"
                    image="https://images.unsplash.com/photo-1620321023374-d1a68fddadb3?w=200&h=200&fit=crop"
                />
            </div>
        </div>
    );
};

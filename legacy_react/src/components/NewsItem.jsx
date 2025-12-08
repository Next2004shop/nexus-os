import React from 'react';
import { Clock, ExternalLink, Share2, MessageCircle, Heart } from 'lucide-react';

export const NewsItem = ({ title, source, time, image, description, category = "CRYPTO" }) => (
    <div className="bg-nexus-card border border-nexus-border p-4 rounded-xl hover:border-nexus-blue/30 transition-all group animate-fadeIn">
        <div className="flex gap-4">
            <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-nexus-blue text-[10px] font-bold px-2 py-0.5 bg-nexus-blue/10 rounded-md">{category}</span>
                    <span className="text-nexus-subtext text-[10px] flex items-center gap-1">
                        <Clock size={10} /> {time}
                    </span>
                </div>
                <h3 className="font-bold text-white text-base leading-snug mb-2 group-hover:text-nexus-blue transition-colors">{title}</h3>
                {description && (
                    <p className="text-nexus-subtext text-xs line-clamp-2 mb-3">{description}</p>
                )}
                <div className="flex items-center justify-between mt-2">
                    <span className="text-xs font-medium text-white/70">{source}</span>
                    <div className="flex gap-3 text-nexus-subtext">
                        <button className="hover:text-nexus-blue transition-colors"><Heart size={14} /></button>
                        <button className="hover:text-nexus-blue transition-colors"><MessageCircle size={14} /></button>
                        <button className="hover:text-nexus-blue transition-colors"><Share2 size={14} /></button>
                    </div>
                </div>
            </div>
            {image && (
                <div className="w-24 h-24 rounded-lg bg-nexus-border overflow-hidden shrink-0">
                    <img src={image} alt="News" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                </div>
            )}
        </div>
    </div>
);

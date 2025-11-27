import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, Loader, Globe } from 'lucide-react';
import { marketData } from '../services/marketData';
import { useNavigate } from 'react-router-dom';

const StockItem = ({ item, onClick }) => {
    if (!item || typeof item.price !== 'number') return null;

    return (
        <div onClick={() => onClick(item)} className="flex justify-between items-center py-4 border-b border-nexus-border last:border-0 cursor-pointer hover:bg-white/5 transition-colors px-4">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-nexus-blue/10 flex items-center justify-center text-nexus-blue font-bold text-xs">
                    {item.symbol[0]}
                </div>
                <div>
                    <div className="font-bold text-nexus-text text-sm">{item.symbol}</div>
                    <div className="text-xs text-nexus-subtext">{item.name}</div>
                </div>
            </div>
            <div className="text-right">
                <div className="text-nexus-text font-medium text-sm font-mono-numbers">
                    ${item.price.toFixed(2)}
                </div>
                <div className={`text-xs font-bold ${item.change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                    {item.change >= 0 ? '+' : ''}{item.change?.toFixed(2)}%
                </div>
            </div>
        </div>
    );
};

export const StocksPage = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await marketData.getStocks();
                // Defensive check
                setData(Array.isArray(result) ? result : []);
            } catch (error) {
                console.error("Failed to fetch stocks", error);
                setData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 15000); // Refresh every 15s
        return () => clearInterval(interval);
    }, []);

    const filteredData = data.filter(item =>
        (item.symbol?.toLowerCase() || '').includes(search.toLowerCase()) ||
        (item.name?.toLowerCase() || '').includes(search.toLowerCase())
    );

    const handleItemClick = (item) => {
        navigate('/trade', { state: { asset: item } });
    };

    return (
        <div className="bg-nexus-black min-h-screen pb-24 animate-fadeIn">
            {/* HEADER */}
            <div className="p-4 pt-6">
                <h1 className="text-2xl font-black text-white flex items-center gap-2 mb-1">
                    <Globe className="text-nexus-blue" /> Global Stocks
                </h1>
                <p className="text-nexus-subtext text-sm">Trade top companies worldwide</p>
            </div>

            {/* SEARCH */}
            <div className="px-4 mb-4">
                <div className="bg-nexus-card border border-nexus-border rounded-xl flex items-center px-4 py-3 gap-2">
                    <Search size={18} className="text-nexus-subtext" />
                    <input
                        type="text"
                        placeholder="Search Apple, Tesla, Safaricom..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="bg-transparent text-sm text-white outline-none w-full placeholder-nexus-subtext"
                    />
                </div>
            </div>

            {/* LIST */}
            <div className="bg-nexus-card border-y border-nexus-border">
                {loading ? (
                    <div className="flex justify-center py-10">
                        <Loader className="animate-spin text-nexus-blue" />
                    </div>
                ) : filteredData.length > 0 ? (
                    filteredData.map((item, index) => (
                        <StockItem key={index} item={item} onClick={handleItemClick} />
                    ))
                ) : (
                    <div className="text-center py-10 text-nexus-subtext">
                        No stocks found.
                    </div>
                )}
            </div>
        </div>
    );
};

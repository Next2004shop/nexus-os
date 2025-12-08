import { useState, useEffect } from 'react';
import { Search, Star, Loader } from 'lucide-react';
import { marketData } from '../services/marketData';
import { useNavigate } from 'react-router-dom';

const MarketItem = ({ item, onClick }) => {
    if (!item || typeof item.price !== 'number') return null;

    return (
        <div onClick={() => onClick(item)} className="flex justify-between items-center py-4 border-b border-nexus-border last:border-0 cursor-pointer hover:bg-white/5 transition-colors px-2">
            <div className="flex items-center gap-3">
                <Star size={16} className="text-nexus-subtext hover:text-nexus-yellow transition-colors" />
                <div>
                    <div className="font-bold text-nexus-text text-sm">{item.symbol}<span className="text-nexus-subtext text-xs">/{item.type === 'crypto' ? 'USDT' : 'USD'}</span></div>
                    <div className="text-xs text-nexus-subtext">{item.name}</div>
                </div>
            </div>
            <div className="text-right flex items-center gap-4">
                <div className="text-right">
                    <div className="text-nexus-text font-medium text-sm font-mono-numbers">
                        {item.price < 1 ? item.price.toFixed(4) : item.price.toFixed(2)}
                    </div>
                    <div className="text-nexus-subtext text-xs">≈ ${item.price.toFixed(2)}</div>
                </div>
                <div className={`w-20 py-2 rounded text-center text-xs font-bold text-white ${item.change >= 0 ? 'bg-nexus-green' : 'bg-nexus-red'}`}>
                    {item.change >= 0 ? '+' : ''}{item.change?.toFixed(2)}%
                </div>
            </div>
        </div>
    );
};

export const MarketsPage = () => {
    const [activeTab, setActiveTab] = useState('crypto');
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            let result = [];

            try {
                if (activeTab === 'crypto') {
                    const cryptos = await marketData.getTopCryptos();
                    result = cryptos.map(c => ({
                        id: c.id,
                        symbol: c.symbol.toUpperCase(),
                        name: c.name,
                        price: c.current_price,
                        change: c.price_change_percentage_24h,
                        type: 'crypto'
                    }));
                } else if (activeTab === 'stocks') {
                    result = await marketData.getStocks();
                } else if (activeTab === 'commodities') {
                    result = await marketData.getCommodities();
                }
            } catch (error) {
                console.error("Failed to fetch market data", error);
                result = [];
            }

            // Safety check: Ensure result is an array
            if (!Array.isArray(result)) {
                console.error("Market data is not an array:", result);
                result = [];
            }

            setData(result);
            setLoading(false);
        };

        fetchData();
        const interval = setInterval(fetchData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, [activeTab]);

    const safeData = Array.isArray(data) ? data : [];
    const filteredData = safeData.filter(item =>
        (item.symbol?.toLowerCase() || '').includes(search.toLowerCase()) ||
        (item.name?.toLowerCase() || '').includes(search.toLowerCase())
    );

    const handleItemClick = (item) => {
        // Navigate to trade page with selected asset
        navigate('/trade', { state: { asset: item } });
    };

    return (
        <div className="bg-nexus-black min-h-screen pb-24">
            {/* SEARCH */}
            <div className="sticky top-0 bg-nexus-black z-30 px-4 py-2">
                <div className="bg-nexus-border rounded-full flex items-center px-4 py-2 gap-2">
                    <Search size={16} className="text-nexus-subtext" />
                    <input
                        type="text"
                        placeholder="Search Markets"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="bg-transparent text-sm text-nexus-text outline-none w-full placeholder-nexus-subtext"
                    />
                </div>
            </div>

            {/* TABS */}
            <div className="flex gap-6 px-4 border-b border-nexus-border mt-2 overflow-x-auto no-scrollbar">
                {['Crypto', 'Stocks', 'Commodities'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab.toLowerCase())}
                        className={`text-sm font-bold pb-3 whitespace-nowrap relative ${activeTab === tab.toLowerCase() ? 'text-nexus-text' : 'text-nexus-subtext'}`}
                    >
                        {tab}
                        {activeTab === tab.toLowerCase() && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-nexus-yellow"></div>}
                    </button>
                ))}
            </div>

            {/* LIST */}
            <div className="px-4 mt-2">
                <div className="flex justify-between text-xs text-nexus-subtext py-2">
                    <span>Name / Vol</span>
                    <span className="pr-8">Last Price</span>
                    <span>24h Chg%</span>
                </div>

                {loading ? (
                    <div className="flex justify-center py-10">
                        <Loader className="animate-spin text-nexus-yellow" />
                    </div>
                ) : filteredData.length > 0 ? (
                    filteredData.map((item, index) => (
                        <MarketItem key={index} item={item} onClick={handleItemClick} />
                    ))
                ) : (
                    <div className="text-center py-10 text-nexus-red font-bold">
                        Market data unavailable. Please check connection.
                    </div>
                )}
            </div>
        </div>
    );
};

import React, { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Activity, Wallet, History, ChevronLeft, Search, Bot, Zap } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { marketData } from '../services/marketData';
import { userRepository } from '../services/userRepository';
import { useAuth } from '../context/AuthContext';
import { MarketSelector } from '../components/trading/MarketSelector';
import { ChartContainer } from '../components/trading/ChartContainer';

const OrderBookRow = ({ price, amount, total, type }) => (
    <div className="grid grid-cols-3 text-xs py-1 hover:bg-white/5 cursor-pointer font-mono">
        <span className={type === 'buy' ? 'text-nexus-green' : 'text-nexus-red'}>{price}</span>
        <span className="text-right text-nexus-subtext">{amount}</span>
        <span className="text-right text-white">{total}</span>
    </div>
);

const TradePage = () => {
    // STATE
    const [selectedAsset, setSelectedAsset] = useState(null); // If null, show MarketSelector
    const [side, setSide] = useState('buy');
    const [orderType, setOrderType] = useState('market'); // market, limit
    const [amount, setAmount] = useState('');
    const [limitPrice, setLimitPrice] = useState('');
    const [price, setPrice] = useState(null); // Real price
    const [loading, setLoading] = useState(false);
    const [wallet, setWallet] = useState(null);

    // AI STRATEGY STATE
    const [strategyMode, setStrategyMode] = useState('manual'); // manual, ai
    const [analyzing, setAnalyzing] = useState(false);
    const [aiSignal, setAiSignal] = useState(null);

    const { showToast } = useToast();
    const { currentUser } = useAuth();

    // Fetch Wallet on Mount
    useEffect(() => {
        const initWallet = async () => {
            if (currentUser) {
                const userWallet = await userRepository.getWallet(currentUser.uid);
                setWallet(userWallet);
            }
        };
        initWallet();
    }, [currentUser]);

    // Update Price when Asset Changes
    useEffect(() => {
        if (selectedAsset) {
            setPrice(selectedAsset.price);
        }

        // Live Polling
        const interval = setInterval(async () => {
            if (!selectedAsset) return;

            const newPrice = await marketData.getLatestPrice(selectedAsset);
            if (newPrice && newPrice !== price) {
                setPrice(newPrice);

                // Update Chart
                setChartData(prev => {
                    const newPoint = { time: Math.floor(Date.now() / 1000), value: newPrice };
                    const newData = [...prev, newPoint];
                    if (newData.length > 100) newData.shift(); // Keep last 100 points
                    return newData;
                });
            }
        }, 3000); // 3s Interval

        return () => clearInterval(interval);
    }, [selectedAsset]);

    const handleAnalyze = () => {
        setAnalyzing(true);
        setAiSignal(null);

        // Mock AI Analysis
        setTimeout(() => {
            const isBullish = Math.random() > 0.4; // Slightly bullish bias
            const currentPrice = price || selectedAsset.price;

            setAiSignal({
                direction: isBullish ? 'LONG' : 'SHORT',
                confidence: Math.floor(Math.random() * (98 - 75) + 75),
                reasoning: isBullish
                    ? "Bullish divergence on RSI (14) coupled with strong support bounce at key fib level."
                    : "Bearish engulfing candle on 4H timeframe indicating potential reversal.",
                entry: currentPrice,
                tp: isBullish ? currentPrice * 1.04 : currentPrice * 0.96,
                sl: isBullish ? currentPrice * 0.98 : currentPrice * 1.02
            });
            setAnalyzing(false);
        }, 2000);
    };

    const applyStrategy = () => {
        if (!aiSignal) return;
        setSide(aiSignal.direction === 'LONG' ? 'buy' : 'sell');
        setOrderType('limit');
        setLimitPrice(aiSignal.entry.toFixed(2));
        // Auto-allocate 10% of wallet for safety
        const safeAmount = wallet?.usdt ? (wallet.usdt * 0.10) / aiSignal.entry : 0;
        setAmount(safeAmount.toFixed(4));
        showToast("AI Strategy Applied to Order Form", "success");
    };

    const handleTrade = async () => {
        if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
            showToast('Please enter a valid amount', 'error');
            return;
        }
        if (!price) {
            showToast('Waiting for market data...', 'info');
            return;
        }

        try {
            setLoading(true);

            if (orderType === 'limit') {
                if (!limitPrice || parseFloat(limitPrice) <= 0) {
                    throw new Error("Invalid Limit Price");
                }
                await userRepository.placeLimitOrder(
                    currentUser.uid,
                    side,
                    selectedAsset.symbol.toLowerCase(),
                    parseFloat(amount),
                    parseFloat(limitPrice)
                );
                showToast(`Limit ${side === 'buy' ? 'Buy' : 'Sell'} Order Placed at $${limitPrice}`, 'success');
            } else {
                // Market Order
                await userRepository.executeTrade(
                    currentUser.uid,
                    side,
                    selectedAsset.symbol.toLowerCase(),
                    parseFloat(amount),
                    price
                );
                showToast(`${side === 'buy' ? 'Buy' : 'Sell'} Order Placed Successfully!`, 'success');

                // Refresh Wallet only on Market Order execution
                const updatedWallet = await userRepository.getWallet(currentUser.uid);
                setWallet(updatedWallet);
            }

            setAmount('');
            setLimitPrice('');

        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    // Generate Mock Order Book based on Real Price
    const generateOrderBook = (basePrice) => {
        const rows = [];
        for (let i = 1; i <= 5; i++) {
            rows.push({ price: (basePrice + i * (basePrice * 0.001)).toFixed(2), amount: (Math.random() * 2).toFixed(4), total: ((basePrice + i * 50) * 0.5).toFixed(2) });
        }
        return rows.reverse();
    };
    const asks = generateOrderBook(price || 40000);
    const bids = generateOrderBook(price ? price * 0.999 : 39750);

    // Generate Chart Data
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        if (!selectedAsset) return;

        const loadData = async () => {
            // Fetch Real Candles
            const candles = await marketData.getCandles(selectedAsset.id, '1'); // 1 Day (approx 30m candles)
            if (candles && candles.length > 0) {
                setChartData(candles);
                setPrice(candles[candles.length - 1].close);
            }
        };
        loadData();

        // Live Polling (Update Current Candle)
        const interval = setInterval(async () => {
            if (!selectedAsset) return;

            const newPrice = await marketData.getLatestPrice(selectedAsset);
            if (newPrice) {
                setPrice(newPrice);

                setChartData(prev => {
                    if (prev.length === 0) return prev;

                    const lastCandle = prev[prev.length - 1];
                    const now = Math.floor(Date.now() / 1000);

                    // If last candle is "stale" (> 30 mins), start a new one (simplified logic)
                    // For now, we just update the Close/High/Low of the current candle to simulate live movement
                    const updatedCandle = {
                        ...lastCandle,
                        close: newPrice,
                        high: Math.max(lastCandle.high, newPrice),
                        low: Math.min(lastCandle.low, newPrice)
                    };

                    return [...prev.slice(0, -1), updatedCandle];
                });
            }
        }, 3000); // 3s Interval

        return () => clearInterval(interval);
    }, [selectedAsset]);

    // RENDER: MARKET SELECTOR (If no asset selected)
    if (!selectedAsset) {
        return <MarketSelector onSelect={setSelectedAsset} />;
    }

    // RENDER: TRADING VIEW
    return (
        <div className="min-h-screen lg:h-[calc(100vh-80px)] flex flex-col lg:flex-row overflow-y-auto lg:overflow-hidden animate-fadeIn pb-20 lg:pb-0">

            {/* LEFT: CHART */}
            <div className="w-full lg:flex-1 bg-[#050505] border-r border-nexus-border flex flex-col h-[50vh] lg:h-auto shrink-0">
                {/* HEADER */}
                <div className="h-16 border-b border-nexus-border flex items-center px-4 justify-between bg-nexus-card/50 backdrop-blur-sm shrink-0">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setSelectedAsset(null)}
                            className="p-2 hover:bg-white/10 rounded-lg text-nexus-subtext hover:text-white transition-colors"
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <div className="flex items-center gap-3">
                            {selectedAsset.image ? (
                                <img src={selectedAsset.image} className="w-8 h-8" alt={selectedAsset.symbol} />
                            ) : (
                                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-white text-xs">
                                    {selectedAsset.symbol[0]}
                                </div>
                            )}
                            <div>
                                <h2 className="text-white font-bold text-lg leading-none">{selectedAsset.symbol.toUpperCase()}</h2>
                                <span className="text-nexus-subtext text-xs">{selectedAsset.name}</span>
                            </div>
                        </div>
                        <div className="h-8 w-[1px] bg-white/10 mx-2"></div>
                        <div>
                            <div className={`text-lg font-mono font-bold ${selectedAsset.change >= 0 ? 'text-nexus-green' : 'text-nexus-red'}`}>
                                ${price?.toLocaleString() || '---'}
                            </div>
                            <span className="text-xs text-nexus-subtext">Mark Price (v2)</span>
                        </div>
                    </div>

                    <button onClick={() => setSelectedAsset(null)} className="hidden md:flex items-center gap-2 text-xs font-bold bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg text-nexus-subtext transition-colors">
                        <Search size={14} /> Change Asset
                    </button>
                </div>

                {/* Chart Area */}
                <div className="flex-1 relative group overflow-hidden bg-[#050505]">
                    <ChartContainer
                        data={chartData}
                        colors={{
                            lineColor: selectedAsset.change >= 0 ? '#00DD80' : '#FF3B30',
                            areaTopColor: selectedAsset.change >= 0 ? 'rgba(0, 221, 128, 0.5)' : 'rgba(255, 59, 48, 0.5)',
                            areaBottomColor: selectedAsset.change >= 0 ? 'rgba(0, 221, 128, 0.0)' : 'rgba(255, 59, 48, 0.0)',
                        }}
                    />
                </div>
            </div>

            {/* RIGHT: ORDER BOOK & TRADE FORM */}
            <div className="w-full lg:w-[350px] bg-nexus-card flex flex-col border-l border-nexus-border shrink-0">

                {/* ORDER BOOK (Hidden on small mobile to save space, or reduced) */}
                <div className="p-4 overflow-y-auto border-b border-nexus-border max-h-64 lg:max-h-none lg:flex-1">
                    <div className="flex justify-between text-xs text-nexus-subtext font-bold mb-2 uppercase">
                        <span>Price (USD)</span>
                        <span>Amount</span>
                        <span>Total</span>
                    </div>
                    <div className="space-y-0.5">
                        {asks.map((row, i) => <OrderBookRow key={`ask-${i}`} {...row} type="sell" />)}
                    </div>
                    <div className="py-3 text-center font-mono text-lg font-bold text-white border-y border-white/5 my-2 bg-white/5">
                        ${price?.toLocaleString()}
                    </div>
                    <div className="space-y-0.5">
                        {bids.map((row, i) => <OrderBookRow key={`bid-${i}`} {...row} type="buy" />)}
                    </div>
                </div>

                {/* TRADE FORM */}
                <div className="p-4 bg-[#0A0A0A]">
                    {/* MODE TOGGLE */}
                    <div className="flex bg-white/5 p-1 rounded-xl mb-4 border border-white/5">
                        <button
                            onClick={() => setStrategyMode('manual')}
                            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${strategyMode === 'manual' ? 'bg-nexus-card text-white shadow-sm' : 'text-nexus-subtext'}`}
                        >
                            Manual
                        </button>
                        <button
                            onClick={() => setStrategyMode('ai')}
                            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1 ${strategyMode === 'ai' ? 'bg-nexus-blue/20 text-nexus-blue shadow-sm' : 'text-nexus-subtext'}`}
                        >
                            <Bot size={12} /> AI Auto
                        </button>
                    </div>

                    {strategyMode === 'ai' && (
                        <div className="mb-4 bg-nexus-blue/5 border border-nexus-blue/20 rounded-xl p-3">
                            {!aiSignal ? (
                                <div className="text-center py-2">
                                    <p className="text-xs text-nexus-subtext mb-3">Let Nexus AI analyze market structure and suggest the best entry.</p>
                                    <button
                                        onClick={handleAnalyze}
                                        disabled={analyzing}
                                        className="w-full py-2 bg-nexus-blue text-black font-bold text-xs rounded-lg hover:bg-nexus-blue/90 transition-colors flex items-center justify-center gap-2"
                                    >
                                        {analyzing ? <Activity size={14} className="animate-spin" /> : <Zap size={14} />}
                                        {analyzing ? 'SCANNING MARKET...' : 'SCAN MARKET STRUCTURE'}
                                    </button>
                                </div>
                            ) : (
                                <div className="space-y-2 animate-fadeIn">
                                    <div className="flex justify-between items-center">
                                        <span className={`text-sm font-black ${aiSignal.direction === 'LONG' ? 'text-nexus-green' : 'text-nexus-red'}`}>{aiSignal.direction} SIGNAL</span>
                                        <span className="text-xs font-bold text-nexus-blue">{aiSignal.confidence}% Conf.</span>
                                    </div>
                                    <p className="text-[10px] text-nexus-subtext leading-tight">{aiSignal.reasoning}</p>
                                    <div className="grid grid-cols-2 gap-2 mt-2">
                                        <div className="bg-black/40 p-1.5 rounded border border-white/5">
                                            <div className="text-[8px] text-nexus-subtext uppercase">Entry</div>
                                            <div className="text-xs font-mono text-white">${aiSignal.entry.toFixed(2)}</div>
                                        </div>
                                        <div className="bg-black/40 p-1.5 rounded border border-white/5">
                                            <div className="text-[8px] text-nexus-subtext uppercase">Take Profit</div>
                                            <div className="text-xs font-mono text-nexus-green">${aiSignal.tp.toFixed(2)}</div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={applyStrategy}
                                        className="w-full mt-2 py-2 bg-white/10 text-white font-bold text-xs rounded-lg hover:bg-white/20 transition-colors border border-white/10"
                                    >
                                        APPLY STRATEGY
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="flex bg-nexus-black p-1 rounded-xl mb-4 border border-white/5">
                        <button
                            onClick={() => setSide('buy')}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${side === 'buy' ? 'bg-nexus-green text-black shadow-lg' : 'text-nexus-subtext hover:text-white'}`}
                        >
                            Buy
                        </button>
                        <button
                            onClick={() => setSide('sell')}
                            className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${side === 'sell' ? 'bg-nexus-red text-white shadow-lg' : 'text-nexus-subtext hover:text-white'}`}
                        >
                            Sell
                        </button>
                    </div>

                    {/* ORDER TYPE TOGGLE */}
                    <div className="flex bg-white/5 p-0.5 rounded-lg mb-4">
                        <button
                            onClick={() => setOrderType('market')}
                            className={`flex-1 py-1.5 rounded-md text-[10px] font-bold transition-all ${orderType === 'market' ? 'bg-nexus-card text-white shadow-sm' : 'text-nexus-subtext'}`}
                        >
                            Market
                        </button>
                        <button
                            onClick={() => setOrderType('limit')}
                            className={`flex-1 py-1.5 rounded-md text-[10px] font-bold transition-all ${orderType === 'limit' ? 'bg-nexus-card text-white shadow-sm' : 'text-nexus-subtext'}`}
                        >
                            Limit
                        </button>
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between text-xs text-nexus-subtext">
                            <span>Avail:</span>
                            <span className="text-white font-mono">
                                {side === 'buy'
                                    ? `${wallet?.usdt?.toLocaleString() || '0'} USDT`
                                    : `${wallet?.btc ? wallet.btc.toFixed(6) : '0.000000'} ${selectedAsset.symbol}`}
                            </span>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-lg p-3 focus-within:border-nexus-blue/50 transition-colors">
                            <label className="text-[10px] text-nexus-subtext uppercase font-bold block mb-1">Amount</label>
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="w-full bg-transparent text-white font-mono outline-none"
                                placeholder="0.00"
                            />
                        </div>

                        {orderType === 'limit' && (
                            <div className="bg-white/5 border border-white/10 rounded-lg p-3 focus-within:border-nexus-blue/50 transition-colors animate-fadeIn">
                                <label className="text-[10px] text-nexus-subtext uppercase font-bold block mb-1">Limit Price</label>
                                <input
                                    type="number"
                                    value={limitPrice}
                                    onChange={(e) => setLimitPrice(e.target.value)}
                                    className="w-full bg-transparent text-white font-mono outline-none"
                                    placeholder={price?.toFixed(2)}
                                />
                            </div>
                        )}

                        <div className="grid grid-cols-4 gap-2">
                            {[25, 50, 75, 100].map(pct => (
                                <button key={pct} onClick={() => setAmount((0.1542 * (pct / 100)).toFixed(4))} className="bg-white/5 hover:bg-white/10 text-xs text-nexus-subtext py-1 rounded-lg transition-colors">{pct}%</button>
                            ))}
                        </div>

                        <button
                            onClick={handleTrade}
                            disabled={loading}
                            className={`w-full py-3.5 rounded-xl font-bold text-sm transition-all active:scale-[0.98] ${side === 'buy'
                                ? 'bg-nexus-green text-black hover:bg-[#00DD80] shadow-[0_0_20px_rgba(0,255,148,0.2)]'
                                : 'bg-nexus-red text-white hover:bg-[#E03020] shadow-[0_0_20px_rgba(255,59,48,0.2)]'
                                }`}
                        >
                            {loading ? 'Processing...' : (side === 'buy' ? `Buy ${selectedAsset.symbol}` : `Sell ${selectedAsset.symbol}`)}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TradePage;

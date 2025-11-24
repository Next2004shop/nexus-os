import React, { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Activity, Wallet, History } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { marketData } from '../services/marketData';
import { userRepository } from '../services/userRepository';
import { useAuth } from '../context/AuthContext';

const OrderBookRow = ({ price, amount, total, type }) => (
    <div className="grid grid-cols-3 text-xs py-1 hover:bg-white/5 cursor-pointer font-mono">
        <span className={type === 'buy' ? 'text-nexus-green' : 'text-nexus-red'}>{price}</span>
        <span className="text-right text-nexus-subtext">{amount}</span>
        <span className="text-right text-white">{total}</span>
    </div>
);

const TradePage = () => {
    const [side, setSide] = useState('buy');
    const [amount, setAmount] = useState('');
    const [price, setPrice] = useState(null); // Real price
    const [loading, setLoading] = useState(true);
    const [wallet, setWallet] = useState(null);

    const { showToast } = useToast();
    const { currentUser } = useAuth();

    // Fetch Data & Wallet
    useEffect(() => {
        const init = async () => {
            try {
                // 1. Get BTC Price
                const btcData = await marketData.getCryptoDetails('bitcoin');
                if (btcData) {
                    setPrice(btcData.market_data.current_price.usd);
                }

                // 2. Get Wallet
                if (currentUser) {
                    const userWallet = await userRepository.getWallet(currentUser.uid);
                    setWallet(userWallet);
                }
            } catch (err) {
                console.error("Trade Init Error:", err);
            } finally {
                setLoading(false);
            }
        };
        init();
        const interval = setInterval(init, 10000); // Update every 10s
        return () => clearInterval(interval);
    }, [currentUser]);

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
            await userRepository.executeTrade(
                currentUser.uid,
                side,
                'btc',
                parseFloat(amount),
                price
            );

            showToast(`${side === 'buy' ? 'Buy' : 'Sell'} Order Placed Successfully!`, 'success');
            setAmount('');

            // Refresh Wallet
            const updatedWallet = await userRepository.getWallet(currentUser.uid);
            setWallet(updatedWallet);

        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    if (!price && loading) return <div className="p-8 text-nexus-blue animate-pulse">Connecting to Exchange...</div>;

    // Generate Mock Order Book based on Real Price
    const generateOrderBook = (basePrice) => {
        const rows = [];
        for (let i = 1; i <= 5; i++) {
            rows.push({ price: (basePrice + i * 50).toFixed(2), amount: (Math.random() * 2).toFixed(4), total: ((basePrice + i * 50) * 0.5).toFixed(2) });
        }
        return rows.reverse();
    };
    const asks = generateOrderBook(price || 40000);
    const bids = generateOrderBook(price ? price - 250 : 39750);

    return (
        <div className="h-[calc(100vh-80px)] flex flex-col lg:flex-row overflow-hidden animate-fadeIn">

            {/* LEFT: CHART (Mocked for now, but could use TradingView widget) */}
            <div className="flex-1 bg-[#050505] border-r border-nexus-border flex flex-col">
                <div className="h-16 border-b border-nexus-border flex items-center px-6 justify-between bg-nexus-card/50 backdrop-blur-sm">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <img src="https://assets.coingecko.com/coins/images/1/large/bitcoin.png" className="w-8 h-8" alt="BTC" />
                            <div>
                                <h2 className="text-white font-bold text-lg leading-none">BTC/USDT</h2>
                                <span className="text-nexus-subtext text-xs">Bitcoin</span>
                            </div>
                        </div>
                        <div className="h-8 w-[1px] bg-white/10 mx-2"></div>
                        <div>
                            <div className={`text-lg font-mono font-bold ${price ? 'text-nexus-green' : 'text-white'}`}>
                                ${price?.toLocaleString() || '---'}
                            </div>
                            <span className="text-xs text-nexus-subtext">Mark Price</span>
                        </div>
                    </div>
                </div>

                {/* Chart Placeholder */}
                <div className="flex-1 relative group overflow-hidden">
                    <div className="absolute inset-0 flex items-center justify-center text-nexus-subtext/20 text-4xl font-bold select-none">
                        TRADING VIEW CHART
                    </div>
                    {/* Grid Lines for effect */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px]"></div>
                </div>
            </div>

            {/* RIGHT: ORDER BOOK & TRADE FORM */}
            <div className="w-full lg:w-[350px] bg-nexus-card flex flex-col border-l border-nexus-border">

                {/* ORDER BOOK */}
                <div className="flex-1 p-4 overflow-y-auto border-b border-nexus-border">
                    <div className="flex justify-between text-xs text-nexus-subtext font-bold mb-2 uppercase">
                        <span>Price (USDT)</span>
                        <span>Amount (BTC)</span>
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
                    <div className="flex bg-black rounded-lg p-1 mb-4 border border-white/10">
                        <button
                            onClick={() => setSide('buy')}
                            className={`flex-1 py-2 rounded-md text-sm font-bold transition-all ${side === 'buy' ? 'bg-nexus-green text-black shadow-[0_0_15px_rgba(0,255,148,0.3)]' : 'text-nexus-subtext hover:text-white'}`}
                        >
                            Buy
                        </button>
                        <button
                            onClick={() => setSide('sell')}
                            className={`flex-1 py-2 rounded-md text-sm font-bold transition-all ${side === 'sell' ? 'bg-nexus-red text-white shadow-[0_0_15px_rgba(255,59,48,0.3)]' : 'text-nexus-subtext hover:text-white'}`}
                        >
                            Sell
                        </button>
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between text-xs text-nexus-subtext">
                            <span>Avail:</span>
                            <span className="text-white font-mono">
                                {side === 'buy'
                                    ? `${wallet?.usdt?.toLocaleString() || 0} USDT`
                                    : `${wallet?.btc?.toFixed(6) || 0} BTC`}
                            </span>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-lg p-3 focus-within:border-nexus-blue/50 transition-colors">
                            <label className="text-[10px] text-nexus-subtext uppercase font-bold block mb-1">Amount (BTC)</label>
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="w-full bg-transparent text-white font-mono outline-none"
                                placeholder="0.00"
                            />
                        </div>

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
                            {loading ? 'Processing...' : (side === 'buy' ? 'Buy BTC' : 'Sell BTC')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TradePage;

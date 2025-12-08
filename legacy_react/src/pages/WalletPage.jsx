import React, { useState, useEffect } from 'react';
import { Wallet, ArrowUpRight, ArrowDownLeft, Shield, PieChart, Activity, Building, Smartphone, CreditCard, Bitcoin, Landmark, ChevronRight, Copy, Check } from 'lucide-react';
import { bridgeService } from '../services/bridgeService';
import { brokerService } from '../services/brokerService';
import { BrokerSelector } from '../components/banking/BrokerSelector';
import { useToast } from '../context/ToastContext';

export const WalletPage = () => {
    const [activeTab, setActiveTab] = useState('deposit');
    const [selectedBroker, setSelectedBroker] = useState(null);
    const [selectedMethod, setSelectedMethod] = useState(null);
    const [paymentDetails, setPaymentDetails] = useState(null);
    const [copied, setCopied] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [statusMessage, setStatusMessage] = useState(null);

    const { showToast } = useToast();

    // Load Brokers
    const brokers = brokerService.getBrokers();

    const [balance, setBalance] = useState({
        total: 0.00,
        crypto: 0.00,
        stocks: 0.00,
        cash: 0.00
    });
    const [loading, setLoading] = useState(true);
    const [cloudProfit, setCloudProfit] = useState(0);
    const [history, setHistory] = useState([]);

    // 1. Bridge Status (Live Balance & History)
    useEffect(() => {
        const fetchBridgeData = async () => {
            // Balance
            const status = await bridgeService.getStatus();
            const positions = await bridgeService.getPositions();

            let cryptoPL = 0;
            let stocksPL = 0;

            if (Array.isArray(positions)) {
                positions.forEach(p => {
                    const sym = p.symbol.toUpperCase();
                    if (sym.includes('BTC') || sym.includes('ETH') || sym.includes('XRP') || sym.includes('LTC')) {
                        cryptoPL += p.profit;
                    } else if (['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOG', 'AMZN', 'US30', 'NAS100', 'SPX500'].some(s => sym.includes(s))) {
                        stocksPL += p.profit;
                    }
                });
            }

            if (status && status.balance) {
                setBalance({
                    total: status.equity || status.balance,
                    crypto: cryptoPL,
                    stocks: stocksPL,
                    cash: status.balance
                });
            }

            // History
            const historyData = await bridgeService.getHistory();
            if (historyData && Array.isArray(historyData)) {
                setHistory(historyData.reverse()); // Show newest first
                const totalRealized = historyData.reduce((acc, curr) => acc + (curr.profit || 0), 0);
                setCloudProfit(totalRealized);
            }

            setLoading(false);
        };
        fetchBridgeData();
        const interval = setInterval(fetchBridgeData, 5000); // Faster updates
        return () => clearInterval(interval);
    }, []);

    const handleMethodSelect = (method) => {
        console.log("Selecting method:", method);
        const details = brokerService.getPaymentDetails(method);
        console.log("Payment Details:", details);
        setSelectedMethod(method);
        setPaymentDetails(details);
    };

    const handleDeposit = async () => {
        setProcessing(true);
        setStatusMessage(null);
        try {
            // Use local API instead of Python Bridge
            const res = await fetch('/api/wallet/deposit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: 1000, // TODO: Make dynamic
                    method: selectedMethod,
                    broker: selectedBroker?.id,
                    details: paymentDetails?.fields.reduce((acc, field) => {
                        // Gather inputs from a form reference or state (simplified for now)
                        // In a real app we'd bind input values to state dynamically
                        acc[field.name] = "TEST_VALUE";
                        return acc;
                    }, {})
                })
            });
            const data = await res.json();

            if (res.ok) {
                // Handle complex response types
                if (data.status === 'AWAITING_WIRE') {
                    setStatusMessage({ type: 'success', text: "Instructions Generated below" });
                    // We would ideally show a modal or expand a section with data.instructions
                    console.log("Wire Instructions:", data.instructions);
                    showToast("Wire Instructions Generated", "success");
                } else if (data.address) {
                    setStatusMessage({ type: 'success', text: `Send to: ${data.address}` });
                    handleCopy(data.address);
                } else {
                    setStatusMessage({ type: 'success', text: data.message });
                    showToast(data.message, "success");
                }
            } else {
                setStatusMessage({ type: 'error', text: data.error || "Deposit Failed" });
            }
        } catch (e) {
            console.error(e);
            setStatusMessage({ type: 'error', text: "Network Error" });
        } finally {
            setProcessing(false);
        }
    };

    const handleCopy = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        showToast("Copied to clipboard", "success");
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="p-6 space-y-6 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Hedge Fund Wallet</h1>
                    <p className="text-nexus-subtext">Global Asset Management & Transfers</p>
                </div>
                <div className="bg-nexus-green/10 px-4 py-2 rounded-lg border border-nexus-green/20">
                    <span className="text-nexus-green font-mono font-bold">
                        {loading ? "SYNCING..." : "STATUS: LIVE (MT5 CONNECTED)"}
                    </span>
                </div>
            </div>

            {/* MAIN DASHBOARD CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* TOTAL EQUITY */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <PieChart size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Total Equity (AUM)</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.total.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-green text-sm">
                        <Activity size={16} className="mr-1" />
                        <span>{cloudProfit >= 0 ? '+' : ''}${cloudProfit.toFixed(2)} (Realized Profit)</span>
                    </div>
                </div>

                {/* LIQUID CASH */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Building size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Liquid Capital</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.cash.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-subtext text-sm">
                        <Shield size={16} className="mr-1" />
                        <span>Insured & Protected</span>
                    </div>
                </div>

                {/* CRYPTO ASSETS */}
                <div className="bg-card p-6 rounded-xl border border-white/5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Wallet size={64} />
                    </div>
                    <h3 className="text-nexus-subtext text-sm font-medium">Digital Assets</h3>
                    <p className="text-3xl font-bold text-white mt-2 font-mono-numbers">
                        ${balance.crypto.toLocaleString()}
                    </p>
                    <div className="mt-4 flex items-center text-nexus-yellow text-sm">
                        <ArrowUpRight size={16} className="mr-1" />
                        <span>Floating P/L (Live)</span>
                    </div>
                </div>
            </div>

            {/* ACTION AREA */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* DEPOSIT / WITHDRAW FORM */}
                <div className="lg:col-span-2 bg-card rounded-xl border border-white/5 overflow-hidden">
                    <div className="flex border-b border-white/5">
                        <button
                            onClick={() => setActiveTab('deposit')}
                            className={`flex-1 py-4 text-sm font-bold transition-colors ${activeTab === 'deposit'
                                ? 'bg-nexus-green/10 text-nexus-green border-b-2 border-nexus-green'
                                : 'text-nexus-subtext hover:text-white'
                                }`}
                        >
                            <div className="flex items-center justify-center gap-2">
                                <ArrowDownLeft size={18} />
                                DEPOSIT FUNDS
                            </div>
                        </button>
                        <button
                            onClick={() => setActiveTab('withdraw')}
                            className={`flex-1 py-4 text-sm font-bold transition-colors ${activeTab === 'withdraw'
                                ? 'bg-nexus-red/10 text-nexus-red border-b-2 border-nexus-red'
                                : 'text-nexus-subtext hover:text-white'
                                }`}
                        >
                            <div className="flex items-center justify-center gap-2">
                                <ArrowUpRight size={18} />
                                WITHDRAW FUNDS
                            </div>
                        </button>
                    </div>

                    <div className="p-6">
                        {activeTab === 'deposit' ? (
                            <div className="space-y-6 animate-fadeIn">
                                {/* 1. SELECT BROKER */}
                                <div>
                                    <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                                        <span className="w-6 h-6 rounded-full bg-nexus-green text-black flex items-center justify-center text-xs">1</span>
                                        Select Broker
                                    </h3>
                                    <BrokerSelector
                                        brokers={brokers}
                                        selected={selectedBroker}
                                        onSelect={(b) => {
                                            setSelectedBroker(b);
                                            setSelectedMethod(null);
                                            setPaymentDetails(null);
                                        }}
                                    />
                                </div>

                                {/* 2. SELECT METHOD */}
                                {selectedBroker && (
                                    <div className="animate-fadeIn">
                                        <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                                            <span className="w-6 h-6 rounded-full bg-nexus-green text-black flex items-center justify-center text-xs">2</span>
                                            Select Payment Method
                                        </h3>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                            {selectedBroker.methods.map(method => {
                                                const details = brokerService.getPaymentDetails(method);
                                                if (!details) return null;
                                                const Icon = {
                                                    Smartphone, CreditCard, Bitcoin, Landmark
                                                }[details.icon] || CreditCard;

                                                return (
                                                    <button
                                                        key={method}
                                                        onClick={() => handleMethodSelect(method)}
                                                        className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-all ${selectedMethod === method
                                                            ? 'bg-white/10 border-white text-white'
                                                            : 'bg-black/40 border-white/5 text-nexus-subtext hover:bg-white/5'
                                                            }`}
                                                    >
                                                        <Icon size={20} style={{ color: details.color }} />
                                                        <span className="text-xs font-bold">{details.title}</span>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                {/* 3. PAYMENT DETAILS */}
                                {paymentDetails && (
                                    <div className="animate-fadeIn bg-black/40 border border-white/10 rounded-xl p-6 mt-6">
                                        <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                                            <span className="w-6 h-6 rounded-full bg-nexus-green text-black flex items-center justify-center text-xs">3</span>
                                            Complete Transaction
                                        </h3>

                                        <div className="space-y-4">
                                            {paymentDetails.fields.map(field => (
                                                <div key={field.name}>
                                                    <label className="block text-xs text-nexus-subtext mb-1 uppercase font-bold">{field.label}</label>
                                                    {field.type === 'select' ? (
                                                        <select className="w-full bg-nexus-black border border-white/10 rounded-lg p-3 text-white outline-none focus:border-nexus-green">
                                                            {field.options.map(opt => <option key={opt}>{opt}</option>)}
                                                        </select>
                                                    ) : (
                                                        <input
                                                            type="text"
                                                            placeholder={field.placeholder}
                                                            className="w-full bg-nexus-black border border-white/10 rounded-lg p-3 text-white outline-none focus:border-nexus-green font-mono"
                                                        />
                                                    )}
                                                </div>
                                            ))}

                                            {selectedMethod === 'binance' && (
                                                <div className="bg-white/5 p-4 rounded-lg flex items-center justify-between border border-white/10 mt-4">
                                                    <div>
                                                        <p className="text-xs text-nexus-subtext mb-1">Deposit Address (TRC20)</p>
                                                        <code className="text-nexus-green font-mono text-sm">TE7w...XyZ9</code>
                                                    </div>
                                                    <button onClick={() => handleCopy("TE7w...XyZ9")} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                        {copied ? <Check size={16} className="text-nexus-green" /> : <Copy size={16} className="text-white" />}
                                                    </button>
                                                </div>
                                            )}

                                            <button
                                                onClick={handleDeposit}
                                                disabled={processing}
                                                className={`w-full bg-nexus-green text-black font-bold py-4 rounded-xl hover:bg-[#00DD80] transition-all shadow-[0_0_20px_rgba(0,221,128,0.2)] mt-4 flex items-center justify-center gap-2 ${processing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                                {processing ? 'PROCESSING...' : paymentDetails.action} <ChevronRight size={18} />
                                            </button>
                                            {statusMessage && (
                                                <div className={`mt-4 p-4 rounded-lg text-center font-bold text-sm ${statusMessage.type === 'success' ? 'bg-nexus-green/20 text-nexus-green' : 'bg-red-500/20 text-red-500'}`}>
                                                    {statusMessage.text}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-4 animate-fadeIn">
                                <div className="bg-nexus-red/5 border border-nexus-red/20 p-4 rounded-lg mb-6">
                                    <h4 className="text-nexus-red font-bold flex items-center gap-2">
                                        <Activity size={16} /> High-Value Withdrawal
                                    </h4>
                                    <p className="text-xs text-nexus-subtext mt-1">
                                        Unlimited withdrawals enabled. Processing time: Instant - 24h.
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Withdraw From</label>
                                    <select className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-red">
                                        <option>Liquid Cash (${balance.cash.toLocaleString()})</option>
                                        <option>Crypto Vault (${balance.crypto.toLocaleString()})</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Amount</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-3 text-nexus-subtext">$</span>
                                        <input
                                            type="number"
                                            placeholder="0.00"
                                            className="w-full bg-nexus-black border border-white/10 rounded p-3 pl-8 text-white outline-none focus:border-nexus-red font-mono text-lg"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs text-nexus-subtext mb-1">Destination</label>
                                    <input
                                        type="text"
                                        placeholder="Bank Account / Wallet Address"
                                        className="w-full bg-nexus-black border border-white/10 rounded p-3 text-white outline-none focus:border-nexus-red"
                                    />
                                </div>

                                <button className="w-full bg-nexus-red text-white font-bold py-4 rounded-lg hover:bg-red-600 transition-colors mt-4 flex items-center justify-center gap-2">
                                    <ArrowUpRight size={20} />
                                    PROCESS WITHDRAWAL
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* RECENT TRANSACTIONS */}
                <div className="bg-card rounded-xl border border-white/5 p-6 h-fit">
                    <h3 className="text-lg font-bold text-white mb-4">Recent Institutional Transfers</h3>
                    <div className="space-y-4">
                        {history.length > 0 ? (
                            history.map((tx, i) => (
                                <div key={i} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors cursor-pointer group">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.profit >= 0
                                            ? 'bg-nexus-green/10 text-nexus-green'
                                            : 'bg-nexus-red/10 text-nexus-red'
                                            }`}>
                                            {tx.profit >= 0 ? <ArrowDownLeft size={18} /> : <ArrowUpRight size={18} />}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white">{tx.symbol} {tx.profit >= 0 ? 'Profit' : 'Loss'}</p>
                                            <p className="text-xs text-nexus-subtext">Ticket: #{tx.ticket}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={`font-mono font-bold ${tx.profit >= 0
                                            ? 'text-nexus-green'
                                            : 'text-nexus-red'
                                            }`}>
                                            {tx.profit >= 0 ? '+' : ''}{tx.profit.toFixed(2)}
                                        </p>
                                        <p className="text-xs text-nexus-subtext group-hover:text-nexus-yellow transition-colors">Completed</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-nexus-subtext text-sm">
                                No recent transactions found.
                            </div>
                        )}
                    </div>
                    <button className="w-full mt-6 py-3 text-sm text-nexus-subtext hover:text-white border border-white/10 rounded hover:bg-white/5 transition-colors">
                        View All Transactions
                    </button>
                </div>
            </div>
        </div>
    );
};

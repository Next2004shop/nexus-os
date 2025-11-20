import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Globe, Cpu, Shield, TrendingUp, Users, MessageSquare, 
  Zap, AlertTriangle, Menu, X, Server, DollarSign, Truck, 
  Sparkles, XCircle, BarChart4, Coins, Terminal, ChevronRight,
  Lock, Unlock, Wifi, Crosshair, Eye, Skull, Scale, Radio, Power, Mic,
  Briefcase, RefreshCw, TrendingDown, ArrowUpRight, ArrowDownRight,
  Layers, MoreHorizontal, Bell, Wallet, PieChart, Settings, Send, Download, Repeat
} from 'lucide-react';

// ==============================================================================
// 👇👇👇 PASTE YOUR API KEY BELOW THIS LINE 👇👇👇
//
const apiKey = "AIzaSyCzHZHnR6BNRFid1h7O-EH32jHUgVlkWYU"; 
//
// 👆👆👆 PASTE YOUR API KEY ABOVE THIS LINE 👆👆👆
// ==============================================================================

const GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025";

// --- VOICE MODULE ---
const speak = (text) => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    const techVoice = voices.find(v => v.name.includes("Google US English")) || voices[0];
    utterance.voice = techVoice;
    utterance.rate = 1.1; 
    utterance.pitch = 0.9;
    window.speechSynthesis.speak(utterance);
  }
};

// --- AI BRIDGE ---
const callGemini = async (prompt, systemInstruction = "") => {
  if (!apiKey || apiKey === "") return "⚠️ SYSTEM ALERT: API Key missing.";
  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          systemInstruction: { parts: [{ text: systemInstruction }] }
        })
      }
    );
    const data = await response.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || "Signal lost.";
  } catch (error) {
    console.error("Gemini Error", error);
    return "⚠️ NEURAL LINK OFFLINE.";
  }
};

// --- COMPONENTS ---

const MobileNav = ({ active, setTab }) => (
  <div className="fixed bottom-0 left-0 right-0 h-[70px] bg-[#121212] border-t border-white/10 flex justify-around items-center z-50 md:hidden pb-2 backdrop-blur-lg">
    <button onClick={() => setTab('trade')} className={`flex flex-col items-center gap-1 p-2 ${active === 'trade' ? 'text-amber-500' : 'text-zinc-500'}`}>
       <Terminal size={20} /> <span className="text-[10px] font-medium">Trade</span>
    </button>
    <button onClick={() => setTab('wallet')} className={`flex flex-col items-center gap-1 p-2 ${active === 'wallet' ? 'text-amber-500' : 'text-zinc-500'}`}>
       <Wallet size={20} /> <span className="text-[10px] font-medium">Wallet</span>
    </button>
    <button onClick={() => setTab('brokers')} className={`flex flex-col items-center gap-1 p-2 ${active === 'brokers' ? 'text-amber-500' : 'text-zinc-500'}`}>
       <Activity size={20} /> <span className="text-[10px] font-medium">Brokers</span>
    </button>
    <button onClick={() => setTab('tax')} className={`flex flex-col items-center gap-1 p-2 ${active === 'tax' ? 'text-amber-500' : 'text-zinc-500'}`}>
       <PieChart size={20} /> <span className="text-[10px] font-medium">Tax</span>
    </button>
  </div>
);

const QuickAction = ({ icon: Icon, label, color }) => (
  <button className="flex flex-col items-center gap-2 group">
    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${color} shadow-lg group-hover:scale-110 transition-transform`}>
      <Icon size={20} className="text-white" />
    </div>
    <span className="text-[10px] text-zinc-400 font-medium">{label}</span>
  </button>
);

const OrderBookRow = ({ price, amount, type }) => (
  <div className="flex justify-between text-[10px] font-mono py-0.5">
    <span className={type === 'buy' ? 'text-emerald-500' : 'text-rose-500'}>{price.toLocaleString()}</span>
    <span className="text-zinc-500">{amount.toFixed(4)}</span>
  </div>
);

export default function NexusAI() {
  const getInitialTab = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('tab') || 'trade';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [marketType, setMarketType] = useState('CRYPTO');
  const [ticker, setTicker] = useState('BTC/USD');
  const [price, setPrice] = useState(0);
  const [trend, setTrend] = useState(0);
  const [balance, setBalance] = useState(24593.42);
  const [trades, setTrades] = useState([]);
  const [aiSentiment, setAiSentiment] = useState("NEUTRAL");
  const [winProb, setWinProb] = useState(0);
  const [autoPilot, setAutoPilot] = useState(false);
  const [brokerStatus, setBrokerStatus] = useState({ fxpesa: false, mt5: false });
  
  // Fake Order Book
  const [asks, setAsks] = useState([]);
  const [bids, setBids] = useState([]);

  // --- ENGINE ---
  useEffect(() => {
    const interval = setInterval(async () => {
      // 1. Fetch Price
      let newPrice = price;
      if (marketType === 'CRYPTO') {
        try {
          const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
          const data = await res.json();
          newPrice = data.bitcoin.usd;
          setPrice(newPrice);
          setTrend(data.bitcoin.usd_24h_change);
        } catch (e) { /* Ignore API limits */ }
      } else {
        // Sim Stocks
        newPrice = price > 0 ? price + (Math.random() - 0.5) * 2 : 890;
        setPrice(newPrice);
        setTrend(prev => prev + (Math.random() - 0.5) * 0.1);
      }

      // 2. Update Order Book
      const base = newPrice || 60000;
      setAsks(Array.from({length: 5}, (_, i) => ({ p: base + i*5 + Math.random(), a: Math.random() })));
      setBids(Array.from({length: 5}, (_, i) => ({ p: base - i*5 - Math.random(), a: Math.random() })));

      // 3. Auto Pilot
      if (autoPilot && Math.random() > 0.9) {
        executeTrade(Math.random() > 0.5 ? 'BUY' : 'SELL', true);
      }

    }, 3000);
    return () => clearInterval(interval);
  }, [marketType, price, autoPilot]);

  const executeTrade = (type, isAuto = false) => {
    const trade = { id: Date.now(), ticker, type, entry: price, pnl: "0.00", status: 'OPEN' };
    setTrades(prev => [trade, ...prev]);
    if (!isAuto) speak(`${type} order placed at ${price}`);
  };

  const scanMarket = async () => {
    const text = await callGemini(`Analyze ${ticker} price ${price}. Return SENTIMENT|CONFIDENCE%`);
    const parts = text.split('|');
    if (parts.length === 2) {
      setAiSentiment(parts[0]);
      setWinProb(parts[1]);
      speak(`Market is ${parts[0]}. Confidence ${parts[1]}`);
    }
  };

  return (
    <div className="flex h-screen bg-[#000000] text-white font-sans overflow-hidden selection:bg-amber-500/30">
      
      {/* --- DESKTOP SIDEBAR (Hidden on Mobile) --- */}
      <div className="hidden md:flex w-20 border-r border-white/5 flex-col items-center py-8 bg-zinc-950/50">
        <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center text-black font-black mb-8">N</div>
        <div className="space-y-8">
          <button onClick={() => setActiveTab('trade')} className={`p-3 rounded-xl transition-all ${activeTab === 'trade' ? 'bg-white/10 text-amber-500' : 'text-zinc-600'}`}><Terminal /></button>
          <button onClick={() => setActiveTab('wallet')} className={`p-3 rounded-xl transition-all ${activeTab === 'wallet' ? 'bg-white/10 text-amber-500' : 'text-zinc-600'}`}><Wallet /></button>
          <button onClick={() => setActiveTab('brokers')} className={`p-3 rounded-xl transition-all ${activeTab === 'brokers' ? 'bg-white/10 text-amber-500' : 'text-zinc-600'}`}><Server /></button>
        </div>
      </div>

      {/* --- MAIN CONTENT --- */}
      <div className="flex-1 flex flex-col relative pb-[70px] md:pb-0 overflow-hidden">
        
        {/* HEADER */}
        <header className="h-16 flex items-center justify-between px-6 bg-black/50 backdrop-blur-md border-b border-white/5 z-20">
          <div className="flex items-center gap-4">
            <div className="md:hidden w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center text-black font-bold">N</div>
            <div className="hidden md:block text-sm font-bold text-zinc-400">NEXUS TERMINAL</div>
            <div className="flex bg-zinc-900/80 rounded-lg p-0.5 border border-white/5">
               <button onClick={() => setMarketType('CRYPTO')} className={`px-3 py-1 text-[10px] font-bold rounded ${marketType === 'CRYPTO' ? 'bg-zinc-800 text-white' : 'text-zinc-500'}`}>CRYPTO</button>
               <button onClick={() => setMarketType('STOCKS')} className={`px-3 py-1 text-[10px] font-bold rounded ${marketType === 'STOCKS' ? 'bg-zinc-800 text-white' : 'text-zinc-500'}`}>STOCKS</button>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Mic className="text-zinc-500" size={20} />
            <Bell className="text-zinc-500" size={20} />
          </div>
        </header>

        {/* SCROLLABLE AREA */}
        <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top,#111_0%,#000_100%)]">
          
          {/* === TRADE TAB === */}
          {activeTab === 'trade' && (
            <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-6">
              
              {/* PRICE HEADER */}
              <div className="flex justify-between items-end">
                <div>
                  <div className="flex items-center gap-2 text-zinc-400 text-xs font-bold mb-1">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> LIVE MARKET
                  </div>
                  <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-white">{ticker}</h1>
                  <div className={`text-2xl font-mono font-bold flex items-center gap-3 ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    ${price.toLocaleString()}
                    <span className="text-sm px-2 py-0.5 bg-white/5 rounded">{trend >= 0 ? '+' : ''}{trend.toFixed(2)}%</span>
                  </div>
                </div>
                <div className="text-right hidden md:block">
                  <div className="text-xs text-zinc-500 uppercase">24h Volume</div>
                  <div className="text-white font-mono">$42.8B</div>
                </div>
              </div>

              {/* CHART & ORDER BOOK */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* MAIN CHART */}
                <div className="lg:col-span-2 h-80 bg-zinc-900/30 border border-white/5 rounded-2xl relative overflow-hidden flex flex-col justify-between p-6 shadow-2xl">
                  <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent pointer-events-none"></div>
                  <div className="flex justify-between relative z-10">
                    <div className="flex gap-2">
                      {['1H', '4H', '1D', '1W'].map(t => <button key={t} className="text-[10px] text-zinc-500 hover:text-white px-2 py-1 rounded hover:bg-white/5">{t}</button>)}
                    </div>
                    <button onClick={scanMarket} className="flex items-center gap-2 text-xs font-bold text-amber-500 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20 animate-pulse">
                      <Sparkles size={14} /> AI SCAN
                    </button>
                  </div>
                  {/* Simulated Graph Lines */}
                  <div className="flex items-end space-x-1 h-40 opacity-40">
                    {Array.from({length: 40}).map((_,i) => (
                      <div key={i} className="flex-1 bg-emerald-500/50 rounded-t-sm" style={{height: `${20 + Math.random()*80}%`}}></div>
                    ))}
                  </div>
                </div>

                {/* ORDER BOOK & CONTROLS */}
                <div className="space-y-4">
                  <div className="bg-zinc-900/30 border border-white/5 rounded-2xl p-4">
                    <div className="flex justify-between text-[10px] text-zinc-500 mb-2"><span>Price</span><span>Amount</span></div>
                    <div className="space-y-0.5">
                      {asks.map((a, i) => <OrderBookRow key={i} price={a.p} amount={a.a} type="sell" />)}
                      <div className={`text-center text-sm font-mono font-bold py-1 ${trend>=0?'text-emerald-500':'text-rose-500'}`}>${price.toFixed(2)}</div>
                      {bids.map((b, i) => <OrderBookRow key={i} price={b.p} amount={b.a} type="buy" />)}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <button onClick={() => executeTrade('BUY')} className="py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-black rounded-xl shadow-lg shadow-emerald-900/20 active:scale-95 transition-transform">BUY</button>
                    <button onClick={() => executeTrade('SELL')} className="py-3 bg-rose-500 hover:bg-rose-400 text-white font-black rounded-xl shadow-lg shadow-rose-900/20 active:scale-95 transition-transform">SELL</button>
                  </div>
                </div>
              </div>

              {/* ACTIVE POSITIONS */}
              <div>
                <h3 className="text-xs font-bold text-zinc-500 uppercase mb-4 tracking-widest">Active Positions</h3>
                <div className="space-y-2">
                  {trades.map((t) => (
                    <div key={t.id} className="flex justify-between items-center p-4 bg-zinc-900/50 border border-white/5 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${t.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                          {t.type === 'BUY' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        </div>
                        <div>
                          <div className="font-bold text-sm text-white">{t.ticker}</div>
                          <div className="text-[10px] text-zinc-500 font-mono">Entry: {t.entry}</div>
                        </div>
                      </div>
                      <div className={`font-mono font-bold ${parseFloat(t.pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {t.pnl}
                      </div>
                    </div>
                  ))}
                  {trades.length === 0 && <div className="text-center text-zinc-700 text-xs py-8">NO ACTIVE TRADES</div>}
                </div>
              </div>
            </div>
          )}

          {/* === WALLET TAB === */}
          {activeTab === 'wallet' && (
            <div className="p-4 md:p-8 max-w-2xl mx-auto space-y-8">
              {/* Balance Card */}
              <div className="bg-gradient-to-br from-zinc-800 to-black p-8 rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/20 blur-[80px] rounded-full"></div>
                <div className="relative z-10">
                  <div className="text-zinc-400 text-xs font-bold uppercase tracking-widest mb-2">Total Balance</div>
                  <div className="text-5xl font-mono font-bold text-white mb-6">${balance.toLocaleString()}</div>
                  <div className="flex gap-2">
                    <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full border border-emerald-500/20">+2.4% Today</span>
                    <span className="px-3 py-1 bg-zinc-800 text-zinc-400 text-xs rounded-full border border-white/10">BTC, USD, KES</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-between px-4">
                <QuickAction icon={Send} label="Send" color="bg-blue-500" />
                <QuickAction icon={Download} label="Receive" color="bg-emerald-500" />
                <QuickAction icon={Repeat} label="Swap" color="bg-purple-500" />
                <QuickAction icon={Layers} label="More" color="bg-zinc-700" />
              </div>

              {/* Assets List */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-zinc-500 uppercase mb-2">Your Assets</h3>
                <div className="flex items-center justify-between p-4 bg-zinc-900/50 border border-white/5 rounded-2xl">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-500"><Coins size={20} /></div>
                    <div>
                      <div className="font-bold text-white">Bitcoin</div>
                      <div className="text-xs text-zinc-500">0.42 BTC</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white">${(price * 0.42).toLocaleString()}</div>
                    <div className="text-xs text-emerald-500">+$124.00</div>
                  </div>
                </div>
                {/* MPesa */}
                <div className="flex items-center justify-between p-4 bg-zinc-900/50 border border-white/5 rounded-2xl">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-green-600/20 flex items-center justify-center text-green-500 font-bold text-xs">MP</div>
                    <div>
                      <div className="font-bold text-white">M-Pesa</div>
                      <div className="text-xs text-zinc-500">Mobile Money</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white">KES 45,200</div>
                    <div className="text-xs text-zinc-600">Available</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* === BROKERS TAB === */}
          {activeTab === 'brokers' && (
             <div className="p-4 md:p-8 max-w-2xl mx-auto space-y-6">
                <h2 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Institutional Gateways</h2>
                
                <div className="p-6 bg-zinc-900/40 border border-white/5 rounded-3xl flex items-center justify-between">
                   <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-600/10 rounded-xl flex items-center justify-center text-blue-500"><Globe /></div>
                      <div>
                         <h3 className="font-bold text-white">FxPesa Direct</h3>
                         <p className="text-xs text-zinc-500">Latency: {brokerStatus.fxpesa ? '14ms' : '--'}</p>
                      </div>
                   </div>
                   <button onClick={() => {speak("Connecting FxPesa"); setBrokerStatus(p=>({...p, fxpesa: !p.fxpesa}))}} className={`px-6 py-2 rounded-xl text-xs font-bold border ${brokerStatus.fxpesa ? 'border-emerald-500 text-emerald-500' : 'border-zinc-700 text-zinc-400'}`}>
                      {brokerStatus.fxpesa ? 'CONNECTED' : 'CONNECT'}
                   </button>
                </div>

                <div className="p-6 bg-zinc-900/40 border border-white/5 rounded-3xl flex items-center justify-between">
                   <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-orange-600/10 rounded-xl flex items-center justify-center text-orange-500"><Server /></div>
                      <div>
                         <h3 className="font-bold text-white">MetaTrader 5</h3>
                         <p className="text-xs text-zinc-500">Bridge Status: {brokerStatus.mt5 ? 'Online' : 'Offline'}</p>
                      </div>
                   </div>
                   <button onClick={() => {speak("Connecting MetaTrader"); setBrokerStatus(p=>({...p, mt5: !p.mt5}))}} className={`px-6 py-2 rounded-xl text-xs font-bold border ${brokerStatus.mt5 ? 'border-emerald-500 text-emerald-500' : 'border-zinc-700 text-zinc-400'}`}>
                      {brokerStatus.mt5 ? 'SYNCED' : 'LINK'}
                   </button>
                </div>
             </div>
          )}

        </div>
      </div>

      {/* MOBILE NAV */}
      <MobileNav active={activeTab} setTab={setActiveTab} />

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out forwards; }
        ::-webkit-scrollbar { width: 0px; }
      `}</style>
    </div>
  );
}
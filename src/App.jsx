import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Globe, Cpu, Shield, TrendingUp, Users, MessageSquare, 
  Zap, AlertTriangle, Menu, X, Server, DollarSign, Truck, 
  Sparkles, XCircle, BarChart4, Coins, Terminal, ChevronRight,
  Lock, Unlock, Wifi, Crosshair, Eye, Skull, Scale, Radio, Power, Mic,
  Briefcase, RefreshCw, TrendingDown, ArrowUpRight, ArrowDownRight,
  Wallet, PieChart, Settings, Send, Download, Repeat, Bell, Layers,
  CreditCard, Landmark, History
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

// --- SUB-COMPONENTS ---

const Modal = ({ title, children, onClose }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fadeIn p-4">
    <div className="bg-zinc-900 border border-white/10 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl">
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-zinc-800/50">
        <h3 className="font-bold text-white font-mono">{title}</h3>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-full transition-colors"><X size={20} /></button>
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  </div>
);

const QuickAction = ({ icon: Icon, label, color, onClick }) => (
  <button onClick={onClick} className="flex flex-col items-center gap-2 group w-full">
    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${color} shadow-lg group-hover:scale-105 transition-all border border-white/10`}>
      <Icon size={24} className="text-white" />
    </div>
    <span className="text-[10px] text-zinc-400 font-medium group-hover:text-white transition-colors">{label}</span>
  </button>
);

// Professional SVG Chart
const PriceChart = ({ data, color }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  
  // Create SVG Path
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((d - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full h-full relative">
      <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible" preserveAspectRatio="none">
        {/* Gradient Fill */}
        <defs>
          <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
            <stop offset="100%" stopColor={color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        <path d={`M0,100 L${points} L100,100 Z`} fill="url(#chartGradient)" stroke="none" />
        {/* Line */}
        <polyline fill="none" stroke={color} strokeWidth="2" points={points} vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

export default function NexusAI() {
  const getInitialTab = () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('tab') || 'trade';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  
  // Core State
  const [marketType, setMarketType] = useState('CRYPTO');
  const [ticker, setTicker] = useState('BTC/USD');
  const [price, setPrice] = useState(0);
  const [trend, setTrend] = useState(0);
  const [chartData, setChartData] = useState([]);
  const [balance, setBalance] = useState(24593.42);
  
  // Trade State
  const [trades, setTrades] = useState([]);
  const [aiSentiment, setAiSentiment] = useState("NEUTRAL");
  const [winProb, setWinProb] = useState(0);
  const [autoPilot, setAutoPilot] = useState(false);
  
  // Features
  const [activeModal, setActiveModal] = useState(null); // 'send', 'receive', 'swap'
  const [brokerStatus, setBrokerStatus] = useState({ fxpesa: false, mt5: false });
  const [isListening, setIsListening] = useState(false);
  
  // Order Book
  const [asks, setAsks] = useState([]);
  const [bids, setBids] = useState([]);

  // --- INITIALIZATION ---
  useEffect(() => {
    // Initialize chart with dummy data so it's not empty
    setChartData(Array.from({ length: 20 }, () => Math.random() * 100 + 50000));
  }, []);

  // --- MARKET ENGINE ---
  useEffect(() => {
    const interval = setInterval(async () => {
      let newPrice = price;
      let newTrend = trend;

      if (marketType === 'CRYPTO') {
        try {
          const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
          const data = await res.json();
          newPrice = data.bitcoin.usd;
          newTrend = data.bitcoin.usd_24h_change;
          // Ensure ticker is correct
          if(ticker !== 'BTC/USD') setTicker('BTC/USD');
        } catch (e) { /* Silent fail */ }
      } else {
        // Stock Simulation
        // Ensure ticker is correct if we just switched
        if (ticker === 'BTC/USD') setTicker('NVDA'); 
        
        const base = ticker === 'NVDA' ? 890 : ticker === 'TSLA' ? 175 : 180;
        newPrice = price > 0 ? price + (Math.random() - 0.5) * 2 : base;
        newTrend = trend + (Math.random() - 0.5) * 0.1;
      }

      setPrice(newPrice);
      setTrend(newTrend);

      // Update Chart
      setChartData(prev => {
        const newData = [...prev, newPrice];
        if (newData.length > 40) newData.shift(); // Keep chart moving
        return newData;
      });

      // Simulate Order Book
      const spread = newPrice * 0.0005;
      setAsks(Array.from({length: 5}, (_, i) => ({ p: newPrice + spread + (i*spread), a: Math.random() * 2 })));
      setBids(Array.from({length: 5}, (_, i) => ({ p: newPrice - spread - (i*spread), a: Math.random() * 2 })));

      // Auto Pilot Logic
      if (autoPilot && Math.random() > 0.92) {
        executeTrade(Math.random() > 0.5 ? 'BUY' : 'SELL', true);
      }

    }, 3000);
    return () => clearInterval(interval);
  }, [marketType, price, ticker, autoPilot]);

  // --- ACTIONS ---

  const executeTrade = (type, isAuto = false) => {
    if (!isAuto && winProb < 70 && winProb > 0) {
      speak("Trade rejected. Risk too high.");
      alert("🛑 RISK GUARD: Win Probability must be > 70%");
      return;
    }
    const trade = { id: Date.now(), ticker, type, entry: price, pnl: "0.00", status: 'OPEN' };
    setTrades(prev => [trade, ...prev]);
    if (!isAuto) speak(`${type} order placed at ${price.toFixed(2)}`);
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

  const startListening = () => {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          const recognition = new SpeechRecognition();
          recognition.continuous = false;
          recognition.lang = 'en-US';
          setIsListening(true);
          recognition.start();
          recognition.onresult = (event) => {
              const transcript = event.results[0][0].transcript.toLowerCase();
              setIsListening(false);
              if (transcript.includes('buy')) executeTrade('BUY');
              else if (transcript.includes('sell')) executeTrade('SELL');
              else if (transcript.includes('scan')) scanMarket();
              speak(`Command received: ${transcript}`);
          };
          recognition.onerror = () => setIsListening(false);
      } else {
          alert("Voice control not supported.");
      }
    };

  // --- RENDER ---

  return (
    <div className="flex h-screen bg-[#000000] text-white font-sans overflow-hidden selection:bg-amber-500/30">
      
      {/* --- DESKTOP SIDEBAR --- */}
      <div className="hidden md:flex w-20 border-r border-white/5 flex-col items-center py-8 bg-zinc-950/50 z-50">
        <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center text-black font-black mb-8">N</div>
        <div className="space-y-6">
          {[
            { id: 'trade', icon: Terminal },
            { id: 'wallet', icon: Wallet },
            { id: 'brokers', icon: Server },
            { id: 'tax', icon: PieChart }
          ].map(item => (
             <button key={item.id} onClick={() => setActiveTab(item.id)} 
               className={`p-3 rounded-xl transition-all ${activeTab === item.id ? 'bg-white/10 text-amber-500 ring-1 ring-amber-500/50' : 'text-zinc-600 hover:text-zinc-300'}`}>
               <item.icon size={24} />
             </button>
          ))}
        </div>
      </div>

      {/* --- MAIN AREA --- */}
      <div className="flex-1 flex flex-col relative pb-[80px] md:pb-0 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(#ffffff05_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>

        {/* HEADER */}
        <header className="h-16 flex items-center justify-between px-6 bg-black/40 backdrop-blur-md border-b border-white/5 z-20 shrink-0">
          <div className="flex items-center gap-4">
             <div className="md:hidden w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center text-black font-bold">N</div>
             <div className="flex bg-zinc-900/80 rounded-lg p-0.5 border border-white/5">
               <button onClick={() => { setMarketType('CRYPTO'); setTicker('BTC/USD'); }} className={`px-4 py-1.5 text-[10px] font-bold rounded-md transition-all ${marketType === 'CRYPTO' ? 'bg-zinc-800 text-white shadow-lg' : 'text-zinc-500 hover:text-zinc-300'}`}>CRYPTO</button>
               <button onClick={() => { setMarketType('STOCKS'); setTicker('NVDA'); }} className={`px-4 py-1.5 text-[10px] font-bold rounded-md transition-all ${marketType === 'STOCKS' ? 'bg-zinc-800 text-white shadow-lg' : 'text-zinc-500 hover:text-zinc-300'}`}>STOCKS</button>
             </div>
             {marketType === 'STOCKS' && (
               <div className="hidden sm:flex space-x-1">
                  {['NVDA', 'TSLA', 'AAPL'].map(sym => (
                     <button key={sym} onClick={() => setTicker(sym)} className={`text-[10px] font-mono px-2 py-1 rounded border ${ticker === sym ? 'border-blue-500 text-blue-500 bg-blue-500/10' : 'border-zinc-800 text-zinc-600'}`}>{sym}</button>
                  ))}
               </div>
             )}
          </div>
          <div className="flex items-center gap-3">
             <div className="text-right hidden sm:block">
                <div className="text-[9px] text-zinc-500 uppercase font-mono">Balance</div>
                <div className="text-sm font-mono font-bold text-white">${balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
             </div>
             <button onClick={startListening} className={`p-2 rounded-full transition-all ${isListening ? 'bg-rose-600 animate-pulse' : 'bg-white/5 hover:bg-white/10'}`}><Mic size={18} className={isListening ? 'text-white' : 'text-zinc-400'} /></button>
          </div>
        </header>

        {/* CONTENT SCROLLABLE */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 z-10">
          
          {/* === TRADE TAB === */}
          {activeTab === 'trade' && (
             <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* LEFT: CHART & ANALYSIS */}
                <div className="lg:col-span-8 flex flex-col gap-6">
                   {/* MAIN CHART CARD */}
                   <div className="h-[400px] bg-[#0f0f0f] border border-white/5 rounded-3xl p-6 relative overflow-hidden shadow-2xl flex flex-col">
                      <div className="flex justify-between items-start mb-4 z-10">
                         <div>
                            <div className="flex items-baseline gap-3">
                               <h1 className="text-4xl md:text-6xl font-black text-white tracking-tighter">{ticker}</h1>
                               <span className={`text-xl font-mono font-bold ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                  {trend >= 0 ? '+' : ''}{trend.toFixed(2)}%
                               </span>
                            </div>
                            <div className="text-2xl font-mono text-zinc-400 mt-1">${price.toLocaleString()}</div>
                         </div>
                         <div className="text-right hidden md:block">
                            <div className={`px-3 py-1 rounded-full text-xs font-bold mb-1 inline-block ${aiSentiment === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>
                               {aiSentiment}
                            </div>
                            <div className="text-[10px] text-zinc-500 font-mono">CONFIDENCE: {winProb}%</div>
                         </div>
                      </div>
                      
                      {/* CHART VISUALIZATION */}
                      <div className="flex-1 w-full relative opacity-80">
                         <PriceChart data={chartData} color={trend >= 0 ? '#10b981' : '#f43f5e'} />
                      </div>

                      {/* TIMEFRAMES */}
                      <div className="flex gap-2 mt-4 border-t border-white/5 pt-4">
                         {['1H', '4H', '1D', '1W'].map(t => <button key={t} className="px-3 py-1 rounded-lg text-[10px] font-bold bg-zinc-900 text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors">{t}</button>)}
                         <button onClick={scanMarket} className="ml-auto flex items-center gap-2 px-4 py-1 rounded-lg text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500/20">
                            <Sparkles size={12} /> AI ANALYSIS
                         </button>
                      </div>
                   </div>

                   {/* ORDER BOOK */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-[#0f0f0f] border border-white/5 rounded-3xl p-5">
                         <div className="flex justify-between text-[10px] text-zinc-500 font-mono mb-3 uppercase tracking-wider">
                            <span>Price (USD)</span><span>Amount</span><span>Total</span>
                         </div>
                         <div className="space-y-1 font-mono text-xs">
                            {asks.map((a, i) => (
                               <div key={i} className="flex justify-between relative">
                                  <div className="absolute right-0 top-0 bottom-0 bg-rose-500/10 transition-all duration-300" style={{ width: `${Math.random() * 60}%` }}></div>
                                  <span className="text-rose-400 relative z-10">{a.p.toFixed(2)}</span>
                                  <span className="text-zinc-400 relative z-10">{a.a.toFixed(4)}</span>
                                  <span className="text-zinc-500 relative z-10">{(a.p * a.a).toFixed(0)}</span>
                               </div>
                            ))}
                            <div className={`text-center py-2 font-bold ${trend >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                               ${price.toFixed(2)}
                            </div>
                            {bids.map((b, i) => (
                               <div key={i} className="flex justify-between relative">
                                  <div className="absolute right-0 top-0 bottom-0 bg-emerald-500/10 transition-all duration-300" style={{ width: `${Math.random() * 60}%` }}></div>
                                  <span className="text-emerald-400 relative z-10">{b.p.toFixed(2)}</span>
                                  <span className="text-zinc-400 relative z-10">{b.a.toFixed(4)}</span>
                                  <span className="text-zinc-500 relative z-10">{(b.p * b.a).toFixed(0)}</span>
                               </div>
                            ))}
                         </div>
                      </div>
                      <div className="bg-[#0f0f0f] border border-white/5 rounded-3xl p-5 flex flex-col justify-center items-center text-center">
                         <div className="w-16 h-16 rounded-full bg-zinc-900 border border-white/10 flex items-center justify-center mb-4">
                            <Radio className="text-amber-500 animate-pulse" />
                         </div>
                         <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-2">Live Intelligence</div>
                         <p className="text-sm font-mono text-white leading-relaxed mb-4">"{newsHeadline}"</p>
                      </div>
                   </div>
                </div>

                {/* RIGHT: EXECUTION & POSITIONS */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                   <div className="bg-[#0f0f0f] border border-white/5 rounded-3xl p-6 shadow-xl">
                      <div className="flex justify-between items-center mb-6">
                         <span className="text-xs font-bold text-white tracking-widest">ORDER ENTRY</span>
                         <button onClick={() => setAutoPilot(!autoPilot)} className={`text-[10px] px-3 py-1 rounded-full border transition-all flex items-center gap-2 ${autoPilot ? 'bg-purple-500/20 border-purple-500 text-purple-400' : 'border-zinc-700 text-zinc-500'}`}>
                            <Cpu size={12} /> {autoPilot ? 'AI PILOT: ON' : 'AI PILOT: OFF'}
                         </button>
                      </div>
                      <div className="space-y-3">
                         <button onClick={() => executeTrade('BUY')} className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-black rounded-xl shadow-lg shadow-emerald-500/20 transition-all active:scale-95 flex items-center justify-center gap-2">
                            <ArrowUpRight strokeWidth={3} /> BUY / LONG
                         </button>
                         <button onClick={() => executeTrade('SELL')} className="w-full py-4 bg-rose-500 hover:bg-rose-400 text-white font-black rounded-xl shadow-lg shadow-rose-500/20 transition-all active:scale-95 flex items-center justify-center gap-2">
                            <ArrowDownRight strokeWidth={3} /> SELL / SHORT
                         </button>
                      </div>
                      <div className="mt-6 pt-6 border-t border-white/5 grid grid-cols-2 gap-4">
                         <div className="text-center">
                            <div className="text-[10px] text-zinc-500 uppercase">Available</div>
                            <div className="font-mono text-white">${balance.toLocaleString()}</div>
                         </div>
                         <div className="text-center">
                            <div className="text-[10px] text-zinc-500 uppercase">Leverage</div>
                            <div className="font-mono text-amber-500">20x</div>
                         </div>
                      </div>
                   </div>

                   {/* ACTIVE TRADES */}
                   <div className="flex-1 bg-[#0f0f0f] border border-white/5 rounded-3xl p-0 overflow-hidden flex flex-col min-h-[300px]">
                      <div className="p-5 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                         <span className="text-xs font-bold text-white tracking-widest">OPEN POSITIONS</span>
                         <span className="text-xs font-mono text-zinc-500">{trades.length}</span>
                      </div>
                      <div className="flex-1 overflow-y-auto">
                         {trades.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-zinc-700 gap-3 opacity-50">
                               <Layers size={32} />
                               <span className="text-xs font-mono">NO ACTIVE PROTOCOLS</span>
                            </div>
                         )}
                         {trades.map((t) => (
                            <div key={t.id} className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors">
                               <div className="flex justify-between items-center mb-1">
                                  <span className="font-bold text-white text-sm">{t.ticker}</span>
                                  <span className={`font-mono text-sm font-bold ${parseFloat(t.pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{t.pnl}</span>
                               </div>
                               <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                                  <span className={`uppercase ${t.type === 'BUY' ? 'text-emerald-500' : 'text-rose-500'}`}>{t.type} 20x</span>
                                  <span>Entry: {t.entry.toLocaleString()}</span>
                               </div>
                            </div>
                         ))}
                      </div>
                   </div>
                </div>
             </div>
          )}

          {/* === WALLET TAB === */}
          {activeTab === 'wallet' && (
             <div className="max-w-2xl mx-auto space-y-8 animate-fadeIn">
                <div className="bg-gradient-to-br from-zinc-900 to-black border border-white/10 rounded-[32px] p-8 shadow-2xl relative overflow-hidden">
                   <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 blur-[80px] rounded-full pointer-events-none"></div>
                   <div className="relative z-10 text-center">
                      <div className="text-zinc-500 text-xs font-bold uppercase tracking-[0.2em] mb-2">Total Balance</div>
                      <div className="text-6xl font-mono font-black text-white mb-8 tracking-tighter">${balance.toLocaleString()}</div>
                      <div className="flex justify-center gap-6">
                         <QuickAction icon={Download} label="Deposit" color="bg-emerald-600" onClick={() => setActiveModal('deposit')} />
                         <QuickAction icon={Send} label="Send" color="bg-blue-600" onClick={() => setActiveModal('send')} />
                         <QuickAction icon={Repeat} label="Swap" color="bg-purple-600" onClick={() => setActiveModal('swap')} />
                      </div>
                   </div>
                </div>

                <div className="space-y-3">
                   <h3 className="text-xs font-bold text-zinc-500 uppercase ml-4 mb-2">Assets</h3>
                   {[
                     { n: 'Bitcoin', s: 'BTC', b: '0.424', v: '$37,500', c: 'text-orange-500' },
                     { n: 'Tether', s: 'USDT', b: '12,450', v: '$12,450', c: 'text-emerald-500' },
                     { n: 'M-Pesa', s: 'KES', b: '45,200', v: '$350', c: 'text-green-600' }
                   ].map((a, i) => (
                      <div key={i} className="flex items-center justify-between p-4 bg-zinc-900/50 border border-white/5 rounded-2xl hover:bg-zinc-900 transition-colors">
                         <div className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-full bg-white/5 flex items-center justify-center font-bold ${a.c}`}>{a.s[0]}</div>
                            <div>
                               <div className="font-bold text-white text-sm">{a.n}</div>
                               <div className="text-xs text-zinc-500 font-mono">{a.b} {a.s}</div>
                            </div>
                         </div>
                         <div className="text-right font-mono font-bold text-white text-sm">{a.v}</div>
                      </div>
                   ))}
                </div>
             </div>
          )}
          
          {/* === BROKERS TAB === */}
          {activeTab === 'brokers' && (
             <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn">
                {['fxpesa', 'mt5'].map(b => (
                   <div key={b} className="bg-zinc-900/40 border border-white/5 p-6 rounded-3xl flex items-center justify-between group hover:border-white/10 transition-all">
                      <div className="flex items-center gap-5">
                         <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-xl ${b === 'fxpesa' ? 'bg-blue-500/10 text-blue-500' : 'bg-orange-500/10 text-orange-500'}`}>
                            {b === 'fxpesa' ? <Globe /> : <Server />}
                         </div>
                         <div>
                            <h3 className="font-bold text-white text-lg capitalize">{b === 'fxpesa' ? 'FxPesa Direct' : 'MetaTrader 5'}</h3>
                            <div className="flex items-center gap-2 mt-1">
                               <div className={`w-1.5 h-1.5 rounded-full ${brokerStatus[b] ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                               <span className="text-xs text-zinc-500 font-mono">{brokerStatus[b] ? 'CONNECTED' : 'DISCONNECTED'}</span>
                            </div>
                         </div>
                      </div>
                      <button onClick={() => {speak(`Connecting ${b}`); setBrokerStatus(p=>({...p, [b]: !p[b]}))}} 
                        className={`px-6 py-3 rounded-xl text-xs font-bold tracking-wider border transition-all ${brokerStatus[b] ? 'border-emerald-500 text-emerald-500 bg-emerald-500/10' : 'border-zinc-700 text-zinc-400 hover:bg-white/5'}`}>
                        {brokerStatus[b] ? 'LINKED' : 'CONNECT'}
                      </button>
                   </div>
                ))}
             </div>
          )}

          {/* === TAX TAB === */}
          {activeTab === 'tax' && (
             <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 animate-fadeIn">
                <div className="bg-zinc-900/40 border border-white/5 p-8 rounded-3xl">
                   <div className="text-xs text-zinc-500 font-bold uppercase tracking-widest mb-4">Tax Liability</div>
                   <div className="text-5xl font-mono text-white font-light mb-2">${taxLiability.toFixed(2)}</div>
                   <div className="text-xs text-rose-400 flex items-center gap-2"><AlertTriangle size={12} /> Estimate</div>
                </div>
                <div className="bg-gradient-to-br from-amber-900/20 to-black border border-amber-500/20 p-8 rounded-3xl">
                   <div className="text-xs text-amber-500 font-bold uppercase tracking-widest mb-4">Optimized Savings</div>
                   <div className="text-5xl font-mono text-emerald-400 font-light mb-2">-${taxSaved.toFixed(2)}</div>
                   <div className="text-xs text-zinc-400 font-mono">Harvesting Protocol Active</div>
                </div>
             </div>
          )}
          
        </div>
      </div>

      {/* MODALS */}
      {activeModal && (
        <Modal title={activeModal.toUpperCase()} onClose={() => setActiveModal(null)}>
           <div className="space-y-4">
              <div className="bg-black/50 p-4 rounded-xl border border-white/10 text-center">
                 <div className="text-xs text-zinc-500 mb-1">Select Asset</div>
                 <div className="font-bold text-white text-lg">Bitcoin (BTC)</div>
              </div>
              <input type="number" placeholder="Amount" className="w-full bg-transparent border-b border-white/20 py-2 text-2xl text-white placeholder:text-zinc-700 font-mono outline-none focus:border-amber-500 transition-colors" />
              <button className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-amber-400 transition-colors" onClick={() => {speak("Transaction Processed"); setActiveModal(null)}}>
                 CONFIRM {activeModal.toUpperCase()}
              </button>
           </div>
        </Modal>
      )}

      {/* MOBILE NAVIGATION BAR */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 h-[80px] bg-black/80 backdrop-blur-xl border-t border-white/10 flex justify-around items-center pb-4 z-50">
         {[
           { id: 'trade', icon: Activity, label: 'Trade' },
           { id: 'wallet', icon: Wallet, label: 'Wallet' },
           { id: 'brokers', icon: Server, label: 'Brokers' },
           { id: 'tax', icon: PieChart, label: 'Tax' }
         ].map(item => (
            <button key={item.id} onClick={() => setActiveTab(item.id)} className={`flex flex-col items-center gap-1 p-2 transition-colors ${activeTab === item.id ? 'text-amber-500' : 'text-zinc-600'}`}>
               <item.icon size={22} />
               <span className="text-[10px] font-medium">{item.label}</span>
            </button>
         ))}
      </div>
    </div>
  );
}
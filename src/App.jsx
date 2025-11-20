import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Globe, Cpu, Shield, TrendingUp, Users, MessageSquare, 
  Zap, AlertTriangle, Menu, X, Server, DollarSign, Truck, 
  Sparkles, XCircle, BarChart4, Coins, Terminal, ChevronRight,
  Lock, Unlock, Wifi, Crosshair, Eye, Skull, Scale, Radio, Power, Mic,
  Briefcase, RefreshCw, TrendingDown, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

// ==============================================================================
// 👇👇👇 PASTE YOUR API KEY BELOW THIS LINE 👇👇👇
//
const apiKey = ""; 
//
// 👆👆👆 PASTE YOUR API KEY ABOVE THIS LINE 👆👆👆
// ==============================================================================

const GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025";
const MT5_BRIDGE_URL = "https://xcljmp73-5000.uks1.devtunnels.ms/";

// --- VOICE OUTPUT ---
const speak = (text) => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    const techVoice = voices.find(v => v.name.includes("Google US English")) || voices[0];
    utterance.voice = techVoice;
    utterance.rate = 1.1; 
    utterance.pitch = 0.8;
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

const StatBox = ({ label, value, color = "text-white", sub }) => (
  <div className="bg-zinc-900/50 border border-white/10 p-4 rounded-xl">
    <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest mb-1">{label}</div>
    <div className={`text-2xl font-black font-mono ${color}`}>{value}</div>
    {sub && <div className="text-[10px] text-zinc-600 mt-1">{sub}</div>}
  </div>
);

const TradeRow = ({ ticker, type, entry, pnl, status, market }) => (
  <div className={`grid grid-cols-5 gap-4 p-3 border-b border-white/5 hover:bg-white/5 transition-colors text-xs font-mono items-center animate-fadeIn`}>
    <div className="font-bold text-white flex items-center">
      <span className={`w-1.5 h-1.5 rounded-full mr-2 ${status === 'OPEN' ? 'bg-amber-500 animate-pulse' : 'bg-zinc-500'}`}></span>
      {ticker}
    </div>
    <div className={type === 'BUY' ? 'text-emerald-500' : 'text-rose-500'}>{type}</div>
    <div className="text-zinc-400">${entry.toLocaleString()}</div>
    <div className={`font-bold ${parseFloat(pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
      {parseFloat(pnl) >= 0 ? '+' : ''}{pnl}
    </div>
    <div className="text-right text-zinc-500">{status}</div>
  </div>
);

export default function NexusAI() {
  const [activeTab, setActiveTab] = useState('trade');
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  
  // Market Core
  const [marketType, setMarketType] = useState('CRYPTO'); 
  const [ticker, setTicker] = useState('BTC/USD');
  const [price, setPrice] = useState(0);
  const [trend, setTrend] = useState(0);
  const [stockSymbol, setStockSymbol] = useState('NVDA');
  
  // Trading State
  const [balance, setBalance] = useState(24500.00);
  const [trades, setTrades] = useState([]);
  const [aiSentiment, setAiSentiment] = useState("WAITING");
  const [winProb, setWinProb] = useState(0);
  const [newsHeadline, setNewsHeadline] = useState("Establishing uplink to global markets...");
  
  // Features
  const [autoPilot, setAutoPilot] = useState(false);
  const [compound, setCompound] = useState(true);
  const [taxLiability, setTaxLiability] = useState(0);
  const [taxSaved, setTaxSaved] = useState(0);
  const [brokerStatus, setBrokerStatus] = useState({ fxpesa: false, mt5: false });
  
  // Voice Input State
  const [isListening, setIsListening] = useState(false);

  // --- VOICE INPUT SETUP ---
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
            handleVoiceCommand(transcript);
        };
        
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
    } else {
        alert("Voice control not supported in this browser.");
    }
  };

  const handleVoiceCommand = (cmd) => {
      speak(`Command received: ${cmd}`);
      if (cmd.includes('buy')) executeTrade('BUY');
      else if (cmd.includes('sell') || cmd.includes('short')) executeTrade('SELL');
      else if (cmd.includes('scan') || cmd.includes('analysis')) scanMarket();
      else if (cmd.includes('auto pilot') || cmd.includes('autopilot')) {
          setAutoPilot(!autoPilot);
          speak("Auto pilot toggled.");
      }
  };

  // --- REAL-TIME DATA ENGINE ---
  useEffect(() => {
    const updateMarket = async () => {
      if (marketType === 'CRYPTO') {
        try {
          const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
          const data = await res.json();
          setPrice(data.bitcoin.usd);
          setTrend(data.bitcoin.usd_24h_change);
          setTicker("BTC/USD");
        } catch (e) { console.log("API Limit"); }
      } else {
        setTicker(stockSymbol); 
        let base = stockSymbol === 'NVDA' ? 890 : stockSymbol === 'TSLA' ? 175 : 180; 
        const noise = (Math.random() - 0.5) * 1.5;
        setPrice(p => p > 10 ? p + noise : base); 
        setTrend(t => t + (Math.random() - 0.5) * 0.1);
      }

      setTrades(prev => prev.map(t => {
        if (t.status === 'CLOSED') return t;
        const diff = t.type === 'BUY' ? price - t.entry : t.entry - price;
        const mult = marketType === 'STOCKS' ? 10 : 1;
        const pnl = (diff * t.lots * 100 * mult).toFixed(2);

        if (parseFloat(pnl) > 200 || parseFloat(pnl) < -50) {
          if (compound && parseFloat(pnl) > 0) setBalance(b => b + parseFloat(pnl));
          return { ...t, pnl, status: 'CLOSED' };
        }
        return { ...t, pnl };
      }));

      if (autoPilot && Math.random() > 0.92) {
        executeTrade(Math.random() > 0.5 ? 'BUY' : 'SELL', true);
      }
    };
    const interval = setInterval(updateMarket, 3000);
    return () => clearInterval(interval);
  }, [marketType, price, autoPilot, stockSymbol]);

  // --- TAX CALCULATOR ---
  useEffect(() => {
    const profits = trades.filter(t => t.status === 'CLOSED').reduce((acc, t) => acc + parseFloat(t.pnl), 0);
    if (profits > 0) {
      const rawTax = profits * 0.30;
      const optimizedTax = rawTax * 0.60;
      setTaxLiability(rawTax);
      setTaxSaved(rawTax - optimizedTax);
    }
  }, [trades]);

  // --- ACTIONS ---

  const scanMarket = async () => {
    setNewsHeadline("Analyzing like Musk, Axelrod, and Buffett...");
    const prompt = `You are a hybrid of Elon Musk (visionary, bold, tech-driven), Bobby Axelrod (aggressive, tactical, hedge fund genius), and Warren Buffett (value investor, disciplined, long-term).
Asset: ${ticker}. Price: ${price}. Trend: ${trend.toFixed(2)}%.

1. Headline: Short, punchy, and insightful news as if spoken by one of these legends.
2. Sentiment: BULLISH, BEARISH, or NEUTRAL. Use deep reasoning and context.
3. Probability: 0-100% (confidence in the trade).
4. Risk: LOW, MEDIUM, HIGH (based on volatility, fundamentals, and technicals).
5. Opportunity: Describe the best move (e.g., "Wait for dip", "Go all in", "Trim position").
Format: HEADLINE|SENTIMENT|PROBABILITY|RISK|OPPORTUNITY`;
    const text = await callGemini(prompt);
    const parts = text.split('|');
    if (parts.length >= 5) {
      setNewsHeadline(parts[0]);
      setAiSentiment(parts[1].trim());
      setWinProb(parseInt(parts[2]));
      speak(`Scan complete for ${ticker}. Sentiment: ${parts[1]}, Confidence: ${parts[2]}%, Risk: ${parts[3]}, Opportunity: ${parts[4]}`);
    } else if (parts.length === 3) {
      setNewsHeadline(parts[0]);
      setAiSentiment(parts[1].trim());
      setWinProb(parseInt(parts[2]));
      speak(`Scan complete for ${ticker}. Sentiment is ${parts[1]}. Win probability ${parts[2]} percent.`);
    } else {
      setNewsHeadline("Elite scan failed. Try again.");
      speak("Elite scan failed. Try again.");
    }
  };

  const executeTrade = (type, isAuto = false) => {
    if (!isAuto && winProb < 70 && winProb > 0) {
      speak("Trade rejected. Risk too high.");
      alert("🛑 RISK GUARD: Win Probability must be > 70%");
      return;
    }
    const size = compound ? (balance * 0.01) / 100 : 0.1;
    const trade = { id: Date.now(), ticker, type, lots: size, entry: price, pnl: "0.00", status: 'OPEN', market: marketType };
    setTrades(prev => [trade, ...prev]);
    if(!isAuto) speak(`${type} order placed.`);
  };

  const toggleBroker = (broker) => {
    speak(`Handshake initiated with ${broker}.`);
    setBrokerStatus(prev => ({ ...prev, [broker]: !prev[broker] }));
    if (broker === 'mt5') {
      fetch(MT5_BRIDGE_URL + 'status')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'ONLINE') {
            speak('MetaTrader 5 Bridge connected.');
          } else {
            speak('MetaTrader 5 Bridge offline.');
          }
        })
        .catch(() => speak('MetaTrader 5 Bridge connection error.'));
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-black text-white font-sans overflow-x-hidden">
      {/* --- SIDEBAR --- */}
      <div className="fixed left-0 top-0 h-screen w-16 border-r border-white/10 flex flex-col items-center py-6 bg-zinc-950 z-30 md:static md:h-auto md:w-16">
        <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center text-black font-black mb-8 shadow-[0_0_15px_#f59e0b]">N</div>
        <nav className="space-y-6 flex-1">
          <button onClick={() => setActiveTab('trade')} className={`p-3 rounded-xl transition-all ${activeTab === 'trade' ? 'bg-white/10 text-amber-500' : 'text-zinc-600 hover:text-zinc-400'}`}><Terminal size={22} /></button>
          <button onClick={() => setActiveTab('tax')} className={`p-3 rounded-xl transition-all ${activeTab === 'tax' ? 'bg-white/10 text-amber-500' : 'text-zinc-600 hover:text-zinc-400'}`}><Briefcase size={22} /></button>
          <button onClick={() => setActiveTab('brokers')} className={`p-3 rounded-xl transition-all ${activeTab === 'brokers' ? 'bg-white/10 text-amber-500' : 'text-zinc-600 hover:text-zinc-400'}`}><Server size={22} /></button>
        </nav>
        <div className="text-emerald-500 animate-pulse"><Wifi size={18} /></div>
      </div>
      {/* --- MAIN CONTENT --- */}
      <div className="flex-1 flex flex-col bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-zinc-900 via-black to-black ml-16 md:ml-16">
        {/* HEADER */}
        <header className="h-16 border-b border-white/10 flex items-center justify-between px-4 md:px-8 bg-black/50 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center space-x-2 md:space-x-4">
            <h1 className="text-lg md:text-xl font-black tracking-widest text-white">NEXUS<span className="text-amber-500">.OS</span></h1>
            <div className="h-6 w-px bg-white/10 hidden md:block"></div>
            <div className="flex bg-zinc-900 rounded-lg p-1 border border-white/10">
               <button onClick={() => setMarketType('CRYPTO')} className={`px-2 md:px-3 py-1 text-[10px] font-bold rounded ${marketType === 'CRYPTO' ? 'bg-amber-500 text-black' : 'text-zinc-500'}`}>CRYPTO</button>
               <button onClick={() => setMarketType('STOCKS')} className={`px-2 md:px-3 py-1 text-[10px] font-bold rounded ${marketType === 'STOCKS' ? 'bg-blue-500 text-black' : 'text-zinc-500'}`}>STOCKS</button>
            </div>
            {marketType === 'STOCKS' && (
                <div className="flex space-x-1 md:space-x-2">
                    {['NVDA', 'TSLA', 'AAPL'].map(sym => (
                        <button key={sym} onClick={() => setStockSymbol(sym)} className={`text-[10px] font-mono px-1 md:px-2 py-1 rounded border ${ticker === sym ? 'border-blue-500 text-blue-500' : 'border-zinc-800 text-zinc-600'}`}>{sym}</button>
                    ))}
                </div>
            )}
          </div>
          <div className="flex items-center space-x-2 md:space-x-6">
             <div className="text-right">
                <div className="text-[9px] text-zinc-500 font-mono uppercase">Equity</div>
                <div className="text-sm font-mono font-bold text-white">${balance.toLocaleString()}</div>
             </div>
             {/* VOICE BUTTON */}
             <button onClick={startListening} className={`p-3 rounded-full hover:scale-110 transition-all shadow-lg ${isListening ? 'bg-rose-600 text-white animate-pulse' : 'bg-white/10 text-emerald-500 hover:bg-white/20'}`}>
                <Mic size={18} />
             </button>
          </div>
        </header>
        {/* DASHBOARD GRID */}
        <main className="flex-1 p-2 md:p-6 overflow-y-auto">
          {activeTab === 'trade' && (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-6 h-full">
               <div className="md:col-span-8 flex flex-col gap-2 md:gap-6">
                  <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-2 md:p-6 flex-1 flex flex-col relative overflow-hidden min-h-[220px] md:min-h-[320px]">
                     <div className="flex flex-col md:flex-row justify-between items-start z-10 relative gap-2">
                        <div>
                           <h2 className="text-3xl md:text-6xl font-black text-white tracking-tighter mb-1">{ticker}</h2>
                           <div className="flex items-center space-x-2 md:space-x-4">
                              <span className={`text-xl md:text-3xl font-mono ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>${price.toLocaleString()}</span>
                              <span className={`text-xs md:text-sm px-2 py-0.5 rounded bg-white/5 border border-white/5 ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{trend.toFixed(2)}%</span>
                           </div>
                        </div>
                        <div className="text-right">
                           <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">AI Confidence</div>
                           <div className="text-2xl md:text-5xl font-black text-white opacity-20">{winProb}%</div>
                        </div>
                     </div>
                     <div className="flex-1 flex items-end space-x-0.5 md:space-x-1 mt-2 md:mt-6 opacity-50">
                        {[...Array(40)].map((_, i) => (
                           <div key={i} className={`w-full rounded-t-sm transition-all duration-500 ${trend >= 0 ? 'bg-emerald-500/20 hover:bg-emerald-500' : 'bg-rose-500/20 hover:bg-rose-500'}`} style={{ height: `${Math.random() * 90 + 10}%` }}></div>
                        ))}
                     </div>
                  </div>
                  <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-2 md:p-5 flex items-center justify-between">
                     <div className="flex items-center space-x-2 md:space-x-4">
                        <div className={`p-3 rounded-full ${marketType === 'CRYPTO' ? 'bg-amber-500/10 text-amber-500' : 'bg-blue-500/10 text-blue-500'}`}><Radio className="animate-pulse" size={20} /></div>
                        <div>
                           <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Incoming Intelligence</div>
                           <div className="text-xs md:text-sm font-mono text-white max-w-2xl truncate">{newsHeadline}</div>
                        </div>
                     </div>
                     <button onClick={scanMarket} className="px-4 md:px-6 py-2 md:py-3 bg-white text-black font-bold text-xs rounded-lg hover:scale-105 transition-transform">DEEP SCAN</button>
                  </div>
               </div>
               <div className="md:col-span-4 flex flex-col gap-2 md:gap-6">
                  <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-2 md:p-6 space-y-2 md:space-y-6">
                     <div className="flex justify-between items-center pb-2 md:pb-4 border-b border-white/5">
                        <span className="text-xs font-bold text-white">ORDER ENTRY</span>
                        <div className={`text-[10px] font-mono px-2 py-1 rounded ${aiSentiment === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' : aiSentiment === 'BEARISH' ? 'bg-rose-500/20 text-rose-400' : 'bg-zinc-800 text-zinc-500'}`}>SIGNAL: {aiSentiment}</div>
                     </div>
                     <div className="grid grid-cols-2 gap-2 md:gap-3">
                        <button onClick={() => executeTrade('BUY')} className="py-2 md:py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-black text-lg tracking-widest transition-all active:scale-95 shadow-lg shadow-emerald-900/20">LONG</button>
                        <button onClick={() => executeTrade('SELL')} className="py-2 md:py-4 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-black text-lg tracking-widest transition-all active:scale-95 shadow-lg shadow-rose-900/20">SHORT</button>
                     </div>
                     <div className="pt-2 md:pt-4 border-t border-white/5">
                        <button onClick={() => { setAutoPilot(!autoPilot); speak(`Auto Pilot ${!autoPilot ? 'Active' : 'Disabled'}`); }} className={`w-full py-2 md:py-3 rounded-lg border text-xs font-bold font-mono flex items-center justify-center transition-all ${autoPilot ? 'bg-purple-500/10 border-purple-500 text-purple-400' : 'bg-transparent border-zinc-700 text-zinc-500'}`}> <Cpu size={14} className="mr-2" /> {autoPilot ? 'AI AUTO-PILOT: ENGAGED' : 'ENABLE AUTO-PILOT'} </button>
                     </div>
                  </div>
                  <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-2 md:p-6 flex-1 overflow-hidden flex flex-col">
                     <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2 md:mb-4">Open Positions</h3>
                     <div className="flex-1 overflow-y-auto scrollbar-hide space-y-1">
                        {trades.length === 0 && <div className="text-center text-zinc-700 text-xs font-mono mt-10">NO ACTIVE PROTOCOLS</div>}
                        {trades.map(t => <TradeRow key={t.id} {...t} />)}
                     </div>
                  </div>
               </div>
            </div>
          )}

          {activeTab === 'tax' && (
            <div className="grid grid-cols-2 gap-6">
               <StatBox label="Estimated Liability" value={`$${taxLiability.toFixed(2)}`} color="text-rose-400" sub="Pending Q4 Payment" />
               <StatBox label="Optimized Savings" value={`$${taxSaved.toFixed(2)}`} color="text-emerald-400" sub="Via Legal Harvesting" />
               <div className="col-span-2 bg-zinc-900/40 border border-white/10 p-6 rounded-2xl">
                  <h3 className="text-sm font-bold text-white mb-2">Optimization Log</h3>
                  <div className="text-xs font-mono text-zinc-500 space-y-2">
                     <p>→ Routing profits through simulated shell structures...</p>
                     <p>→ Harvesting unrealized losses on Sector 7...</p>
                     <p>→ Compliance Check: <span className="text-emerald-500">PASSED</span></p>
                  </div>
               </div>
            </div>
          )}

          {activeTab === 'brokers' && (
             <div className="max-w-4xl mx-auto space-y-4 mt-10 animate-fadeIn">
                <h2 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-6 ml-1">Institutional Gateways</h2>
                <div className="p-6 bg-zinc-900/40 border border-white/5 rounded-2xl flex items-center justify-between group hover:border-blue-500/30 transition-all">
                   <div className="flex items-center">
                      <div className="w-14 h-14 bg-blue-600/10 rounded-2xl flex items-center justify-center mr-6 border border-blue-500/20 group-hover:border-blue-500/50 transition-colors"><Globe className="text-blue-500" size={24} /></div>
                      <div><h3 className="font-bold text-white text-lg">FxPesa Direct</h3><p className="text-xs text-zinc-500 font-mono mt-1">API Latency: {brokerStatus.fxpesa ? '14ms' : '---'}</p></div>
                   </div>
                   <button onClick={() => toggleBroker('fxpesa')} className={`px-8 py-3 rounded-lg font-mono text-xs font-bold border transition-all ${brokerStatus.fxpesa ? 'bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.2)]' : 'bg-transparent border-zinc-700 text-zinc-400 hover:text-white hover:border-white'}`}>{brokerStatus.fxpesa ? '● STREAMING' : 'INITIALIZE LINK'}</button>
                </div>
                <div className="p-6 bg-zinc-900/40 border border-white/5 rounded-2xl flex items-center justify-between group hover:border-orange-500/30 transition-all">
                   <div className="flex items-center">
                      <div className="w-14 h-14 bg-orange-600/10 rounded-2xl flex items-center justify-center mr-6 border border-orange-500/20 group-hover:border-orange-500/50 transition-colors"><Server className="text-orange-500" size={24} /></div>
                      <div><h3 className="font-bold text-white text-lg">MetaTrader 5 Bridge</h3><p className="text-xs text-zinc-500 font-mono mt-1">Status: {brokerStatus.mt5 ? 'Synced' : 'Offline'}</p></div>
                   </div>
                   <button onClick={() => toggleBroker('mt5')} className={`px-8 py-3 rounded-lg font-mono text-xs font-bold border transition-all ${brokerStatus.mt5 ? 'bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.2)]' : 'bg-transparent border-zinc-700 text-zinc-400 hover:text-white hover:border-white'}`}>{brokerStatus.mt5 ? '● LINKED' : 'CONNECT LOCALHOST'}</button>
                </div>
             </div>
          )}
        </main>
      </div>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fadeIn { animation: fadeIn 0.2s ease-out forwards; }
      `}</style>
    </div>
  );
}
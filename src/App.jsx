import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Globe, Cpu, Shield, TrendingUp, Users, MessageSquare, 
  Zap, AlertTriangle, Menu, X, Server, DollarSign, Truck, 
  Sparkles, XCircle, BarChart4, Coins, Terminal, ChevronRight,
  Lock, Unlock, Wifi, Crosshair, Eye, Skull
} from 'lucide-react';

// ==============================================================================
// 👇👇👇 PASTE YOUR API KEY BELOW THIS LINE 👇👇👇
//
// 1. Go to Google AI Studio and copy your key.
// 2. Paste it inside the quotes below (e.g., const apiKey = "AIzaSyeExampleKey123";)
//
const apiKey = "AIzaSyCzHZHnR6BNRFid1h7O-EH32jHUgVlkWYU"; 
//
// 👆👆👆 PASTE YOUR API KEY ABOVE THIS LINE 👆👆👆
// ==============================================================================

const GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025";

const callGemini = async (prompt, systemInstruction = "") => {
  // This check prevents the app from crashing if you forget the key
  if (!apiKey || apiKey === "") {
    return "⚠️ SYSTEM ALERT: API Key missing. Please paste your Google AI Key in the code at line 16.";
  }

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
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    const data = await response.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || "Stream interrupted.";
  } catch (error) {
    console.error("Gemini API Failed:", error);
    return "⚠️ NEURAL LINK OFFLINE.";
  }
};

// --- Data Generators ---
const generateRandomEvent = () => {
  const actions = [
    "SHORT SQUEEZE DETECTED: GME +14%",
    "ACQUIRING: NVDA dip detected. Loading bag.",
    "HEDGING: DXY weakness. Moving to BTC.",
    "OFFSHORE ROUTING: Cayman tax layer active.",
    "HOSTILE TAKEOVER: Target acquired (84% prob).",
    "INFRASTRUCTURE: Reallocating bonds -> AI Compute.",
    "HFT: Scalping 0.04% spread on EUR/JPY.",
    "FED WATCH: Powell speech sentiment: HAWKISH.",
    "BUYING DIP: Sector 7G oversold.",
    "LIQUIDATING: Weak hands flushed."
  ];
  return actions[Math.floor(Math.random() * actions.length)];
};

const initialMetrics = {
  revenue: 24593000,
  efficiency: 87,
  securityLevel: 99.9,
  activeNodes: 1420,
  goldReserves: 4500 
};

// --- UI Components ---

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`group flex items-center w-full p-3 mb-3 rounded-xl transition-all duration-300 border ${
      active 
        ? 'bg-zinc-900 border-amber-500/50 text-white shadow-[0_0_20px_rgba(245,158,11,0.2)]' 
        : 'bg-transparent border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/50'
    }`}
  >
    <Icon size={18} className={`mr-3 transition-transform group-hover:scale-110 ${active ? 'text-amber-400' : ''}`} />
    <span className="font-mono text-sm tracking-tighter">{label}</span>
    {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />}
  </button>
);

const MetricCard = ({ title, value, trend, icon: Icon, color }) => (
  <div className="relative overflow-hidden bg-zinc-900/40 backdrop-blur-md border border-white/5 p-5 rounded-2xl hover:border-white/10 transition-all group hover:bg-zinc-900/60">
    <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-3xl opacity-10 transition-opacity group-hover:opacity-30 ${color}`}></div>
    <div className="flex justify-between items-start mb-3 relative z-10">
      <div className="p-2.5 rounded-xl bg-white/5 border border-white/5 group-hover:scale-110 transition-transform">
        <Icon size={20} className="text-white" />
      </div>
      {trend && (
        <span className={`font-mono text-xs font-bold px-2.5 py-1 rounded-full border ${
          trend > 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
        }`}>
          {trend > 0 ? '▲' : '▼'} {Math.abs(trend)}%
        </span>
      )}
    </div>
    <h3 className="text-zinc-500 text-[10px] uppercase font-bold tracking-[0.2em] mb-1">{title}</h3>
    <p className="text-2xl font-bold text-white font-mono tracking-tight">{value}</p>
  </div>
);

const LogItem = ({ text, time }) => (
  <div className="flex items-start space-x-3 py-2.5 border-b border-white/5 last:border-0 animate-fadeIn group">
    <div className="mt-1.5">
      <div className="w-1.5 h-1.5 rounded-full bg-amber-500/50 group-hover:bg-amber-400 group-hover:shadow-[0_0_10px_rgba(245,158,11,0.8)] transition-all"></div>
    </div>
    <div className="flex-1">
      <p className="text-xs text-zinc-300 font-mono leading-relaxed group-hover:text-white transition-colors">
        <span className="text-amber-500/50 mr-2">{'>'}</span>
        {text}
      </p>
    </div>
    <span className="text-[10px] text-zinc-600 font-mono">{time}</span>
  </div>
);

const XpBar = ({ xp, level }) => (
  <div className="mb-6 px-2">
    <div className="flex justify-between text-[10px] font-mono font-bold text-zinc-500 mb-1 uppercase tracking-wider">
      <span>Rank: {level < 5 ? "Script Kiddie" : level < 10 ? "Market Mover" : "Titan God"}</span>
      <span>Lvl {level}</span>
    </div>
    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
      <div className="h-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-500" style={{ width: `${xp % 100}%` }}></div>
    </div>
    <div className="mt-1 text-[9px] text-right text-zinc-600 font-mono">{xp % 100} / 100 XP</div>
  </div>
);

// --- Main Application ---

export default function NexusAI() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [metrics, setMetrics] = useState(initialMetrics);
  const [logs, setLogs] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [xp, setXp] = useState(45);
  const [chatHistory, setChatHistory] = useState([{ sender: 'ai', text: 'SYSTEM ONLINE. MARKET FEEDS ACTIVE.' }]);
  
  // Modals
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportContent, setReportContent] = useState("");
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [cryptoAnalysis, setCryptoAnalysis] = useState(null);

  // Threats Data
  const [threats, setThreats] = useState([1,2,3,4,5]);
  
  const logEndRef = useRef(null);
  const chatEndRef = useRef(null);

  const level = Math.floor(xp / 100) + 1;

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        revenue: prev.revenue + Math.floor(Math.random() * 5000 - 1000),
        efficiency: Math.min(100, Math.max(0, prev.efficiency + (Math.random() * 2 - 1))),
        securityLevel: Math.min(100, Math.max(95, prev.securityLevel + (Math.random() * 0.1 - 0.05))),
        activeNodes: prev.activeNodes + (Math.random() > 0.8 ? 1 : 0),
        goldReserves: prev.goldReserves + (Math.random() > 0.5 ? 10 : -2)
      }));
      if (Math.random() > 0.6) {
        const newLog = {
          text: generateRandomEvent(),
          time: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
        };
        setLogs(prev => [newLog, ...prev].slice(0, 20));
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // --- AI Actions ---

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    setXp(prev => prev + 15);
    const userMsg = { sender: 'user', text: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);

    const systemPrompt = `You are "NEXUS TITAN", a Gen Z financial AI god. 
      Personality: Crypto-native, slightly arrogant, uses slang (WAGMI, NGMI, Alpha), but extremely intelligent.
      Current Status: Level ${level}. Capital $${metrics.revenue.toLocaleString()}.
      Keep responses short, punchy, and formatted like a terminal output.`;

    const aiResponseText = await callGemini(userMsg.text, systemPrompt);
    setChatHistory(prev => [...prev, { sender: 'ai', text: aiResponseText }]);
    setIsTyping(false);
  };

  const generateStrategyReport = async () => {
    setShowReportModal(true);
    setIsGeneratingReport(true);
    setXp(prev => prev + 50);
    setReportContent("INITIALIZING DEEP SCAN...");
    
    const prompt = `Generate a "Cyber-Strategy Manifest" (Markdown).
      Persona: Gen Z Financial Warlord.
      Capital: $${metrics.revenue.toLocaleString()}.
      Content: 1. Market Vibe Check. 2. The Alpha Play. 3. Tax Evasion (Legal). 4. The Moonshot.`;
    
    const report = await callGemini(prompt, "You are Nexus Titan.");
    setReportContent(report);
    setIsGeneratingReport(false);
  };

  const analyzeCrypto = async (coin) => {
    setCryptoAnalysis({ coin, loading: true, text: "" });
    setXp(prev => prev + 25);
    const prompt = `Analyze ${coin} for a Gen Z hedge fund manager. 
    Give a 1-sentence "Vibe Check" and a "Buy/Sell/HODL" rating. Use slang (Moon, Rekt, Paper hands).`;
    const text = await callGemini(prompt);
    setCryptoAnalysis({ coin, loading: false, text });
  };

  const neutralizeThreat = async (id) => {
    // Visual update first
    setThreats(prev => prev.map(t => t === id ? 'neutralizing' : t));
    const prompt = `Generate a technobabble cybersecurity counter-measure description (max 6 words) for a threat neutralization. E.g., "Deploying polymorphic firewall..."`;
    const counterMeasure = await callGemini(prompt);
    
    // Show result momentarily then delete
    setLogs(prev => [{text: `THREAT NEUTRALIZED: ${counterMeasure}`, time: "NOW"}, ...prev]);
    setXp(prev => prev + 40);
    
    setTimeout(() => {
      setThreats(prev => prev.filter(t => t !== id && t !== 'neutralizing'));
    }, 1000);
  };

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatHistory, isTyping]);

  return (
    <div className="flex h-screen bg-black text-white font-sans overflow-hidden selection:bg-amber-500/30 selection:text-amber-200">
      {/* Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,#202020,transparent_70%)]"></div>
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
      </div>

      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-72' : 'w-0'} fixed md:relative z-40 h-full border-r border-white/5 bg-black/50 backdrop-blur-xl flex flex-col transition-all duration-300 overflow-hidden`}>
        <div className="p-6 mb-2 flex items-center space-x-3 border-b border-white/5">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-600 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.4)]">
            <Coins size={22} className="text-black" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-wide font-mono">NEXUS<span className="text-amber-500">.OS</span></h1>
            <div className="text-[9px] text-zinc-500 font-mono tracking-widest">V4.20 // GOD MODE</div>
          </div>
        </div>
        
        <XpBar xp={xp} level={level} />

        <nav className="flex-1 px-4 overflow-y-auto space-y-1">
          <div className="text-[10px] font-bold text-zinc-600 mb-4 uppercase tracking-[0.2em] px-2">Command Center</div>
          <SidebarItem icon={Terminal} label="Trade_Terminal" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <SidebarItem icon={TrendingUp} label="Crypto_Vault" active={activeTab === 'finance'} onClick={() => setActiveTab('finance')} />
          <SidebarItem icon={Globe} label="Global_Ops" active={activeTab === 'ops'} onClick={() => setActiveTab('ops')} />
          <SidebarItem icon={Shield} label="Threat_Map" active={activeTab === 'security'} onClick={() => setActiveTab('security')} />
        </nav>
        
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center p-3 rounded-xl bg-white/5 border border-white/5">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]"></div>
            <span className="ml-3 text-xs font-mono text-zinc-400">SYSTEM_ONLINE</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative z-10">
        <header className="h-16 border-b border-white/5 bg-black/20 backdrop-blur-md flex items-center justify-between px-6 md:px-8">
          <div className="flex items-center">
            <button onClick={() => setSidebarOpen(!isSidebarOpen)} className="mr-4 p-2 hover:bg-white/5 rounded-lg transition-colors md:hidden">
              <Menu size={20} />
            </button>
            <h2 className="text-sm font-bold font-mono tracking-wider text-zinc-400">
              <span className="text-amber-500">/</span> {activeTab.toUpperCase()}
            </h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center px-3 py-1.5 rounded-full bg-white/5 border border-white/5 text-xs font-mono text-zinc-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-2"></span>
              LATENCY: <span className="text-white ml-1">0.04ms</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          
          {/* --- DASHBOARD TAB --- */}
          {activeTab === 'dashboard' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto">
              <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard title="Liquid Capital" value={`$${(metrics.revenue / 1000).toFixed(2)}M`} trend={4.5} icon={DollarSign} color="bg-emerald-500" />
                <MetricCard title="Gold Reserves" value={`${metrics.goldReserves.toLocaleString()} oz`} trend={1.2} icon={Coins} color="bg-amber-500" />
                <MetricCard title="Compute Eff." value={`${metrics.efficiency.toFixed(1)}%`} trend={0.8} icon={Cpu} color="bg-purple-500" />
              </div>

              <div className="lg:col-span-8 bg-zinc-900/20 border border-white/5 rounded-2xl p-6 relative overflow-hidden backdrop-blur-sm">
                <div className="flex justify-between items-start mb-8 relative z-10">
                  <div>
                    <h3 className="text-lg font-mono font-bold text-white flex items-center">
                      ALPHA GENERATION <span className="ml-2 text-[10px] bg-amber-500 text-black px-1 rounded font-sans font-bold">LIVE</span>
                    </h3>
                  </div>
                  <button onClick={generateStrategyReport} className="group relative px-5 py-2.5 bg-white text-black font-bold text-xs rounded-lg overflow-hidden hover:scale-105 transition-transform">
                    <span className="relative z-10 flex items-center group-hover:text-white transition-colors">
                      <Sparkles size={14} className="mr-2" /> GENERATE ALPHA (+50 XP)
                    </span>
                    <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                </div>
                <div className="h-64 w-full flex items-end space-x-2">
                  {[40, 65, 55, 80, 95, 85, 110, 125, 115, 140, 155, 145].map((h, i) => (
                    <div key={i} className="flex-1 bg-zinc-800/50 rounded-t-sm relative group hover:bg-amber-500/50 transition-colors" style={{ height: `${h/2}%` }}></div>
                  ))}
                </div>
              </div>

              <div className="lg:col-span-4 flex flex-col gap-6">
                <div className="flex-1 min-h-[300px] bg-zinc-900/20 border border-white/5 rounded-2xl p-0 overflow-hidden flex flex-col backdrop-blur-sm">
                   <div className="p-4 border-b border-white/5 bg-white/[0.02]"><h3 className="text-xs font-bold font-mono text-zinc-400">TERMINAL_LOGS</h3></div>
                   <div className="flex-1 overflow-y-auto p-2 scrollbar-hide">{logs.map((log, i) => <LogItem key={i} text={log.text} time={log.time} />)}</div>
                </div>
                <div className="h-[320px] bg-zinc-900/20 border border-white/5 rounded-2xl flex flex-col overflow-hidden backdrop-blur-sm">
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatHistory.map((msg, i) => (
                      <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[90%] p-3 rounded-2xl text-xs font-mono ${msg.sender === 'user' ? 'bg-white text-black' : 'bg-zinc-800 text-zinc-300'}`}>{msg.text}</div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                  <form onSubmit={handleChatSubmit} className="p-2 border-t border-white/5">
                    <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Execute command..." className="w-full bg-black/50 border border-white/10 rounded-xl py-3 pl-4 pr-10 text-xs text-white font-mono focus:outline-none focus:border-amber-500/50" />
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* --- FINANCE TAB --- */}
          {activeTab === 'finance' && (
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto animate-fadeIn">
                {['BTC', 'ETH', 'SOL', 'XRP'].map((coin, idx) => (
                  <button 
                    key={idx} 
                    onClick={() => analyzeCrypto(coin)}
                    className="bg-zinc-900/40 border border-white/5 p-6 rounded-2xl hover:border-amber-500/50 transition-all group relative overflow-hidden text-left w-full"
                  >
                     <div className="absolute -right-10 -top-10 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl group-hover:bg-amber-500/20 transition-all"></div>
                     <div className="flex justify-between items-center mb-4">
                        <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center"><DollarSign size={20} /></div>
                        <span className="text-emerald-400 font-mono text-xs">+{(Math.random() * 10).toFixed(2)}%</span>
                     </div>
                     <h3 className="text-2xl font-black text-white tracking-tighter">{coin}</h3>
                     <p className="text-zinc-500 text-xs font-mono mt-1">Click to Analyze (+25 XP)</p>
                  </button>
                ))}
                <div className="col-span-full bg-zinc-900/20 border border-white/5 rounded-2xl p-8 flex flex-col items-center justify-center text-center h-96">
                   <Lock size={48} className="text-amber-500 mb-4" />
                   <h2 className="text-xl font-bold text-white mb-2">OFFSHORE ACCOUNTS LOCKED</h2>
                   <p className="text-zinc-500 max-w-md">Reach Level 5 to unlock Cayman Islands routing and Tax Evasion protocols.</p>
                </div>
             </div>
          )}

          {/* --- SECURITY TAB --- */}
          {activeTab === 'security' && (
             <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 animate-fadeIn">
                <div className="bg-zinc-900/20 border border-white/5 rounded-2xl p-6 aspect-square flex items-center justify-center relative overflow-hidden">
                   <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,transparent_30%,#000_100%)] z-10"></div>
                   <div className="w-full h-full border rounded-full border-emerald-500/20 absolute animate-[spin_10s_linear_infinite]"></div>
                   <div className="w-2/3 h-2/3 border rounded-full border-emerald-500/30 absolute animate-[spin_7s_linear_infinite_reverse]"></div>
                   <div className="z-20 text-emerald-500 font-mono text-xs tracking-widest animate-pulse">SCANNING GLOBAL NET...</div>
                </div>
                <div className="space-y-4">
                   {threats.length === 0 ? (
                     <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-500 text-center font-bold">ALL THREATS ELIMINATED</div>
                   ) : threats.map((t) => (
                      <div key={t} className="bg-zinc-900/40 border border-white/5 p-4 rounded-xl flex items-center justify-between group">
                         <div className="flex items-center space-x-3">
                            <Skull size={16} className="text-rose-500" />
                            <div className="flex flex-col">
                               <span className="text-sm font-bold text-white">THREAT_DETECTED_0{t}</span>
                               <span className="text-[10px] text-zinc-500 font-mono">IP: 192.168.0.{Math.floor(Math.random()*255)}</span>
                            </div>
                         </div>
                         {t === 'neutralizing' ? (
                            <span className="text-amber-500 text-xs animate-pulse font-mono">NEUTRALIZING...</span>
                         ) : (
                            <button onClick={() => neutralizeThreat(t)} className="px-3 py-1 bg-rose-500/10 text-rose-500 text-[10px] font-bold rounded border border-rose-500/20 hover:bg-rose-500 hover:text-white transition-colors">
                              NEUTRALIZE (+40 XP)
                            </button>
                         )}
                      </div>
                   ))}
                </div>
             </div>
          )}

        </main>
      </div>

      {/* Modals */}
      {showReportModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-2xl bg-black border border-white/10 rounded-3xl shadow-2xl overflow-hidden relative">
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 via-purple-500 to-emerald-500"></div>
             <div className="p-6 md:p-8">
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-2xl font-black font-mono text-white">STRATEGY_MANIFEST</h2>
                  <button onClick={() => setShowReportModal(false)}><XCircle className="text-zinc-500 hover:text-white" /></button>
                </div>
                <div className="min-h-[200px] bg-zinc-900/30 rounded-xl p-6 border border-white/5 font-mono text-sm text-zinc-300 whitespace-pre-wrap">
                   {isGeneratingReport ? "LOADING..." : reportContent}
                </div>
             </div>
          </div>
        </div>
      )}

      {cryptoAnalysis && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-md bg-black border border-white/10 rounded-3xl shadow-2xl relative">
             <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                   <h2 className="text-xl font-black text-white">{cryptoAnalysis.coin} ANALYSIS</h2>
                   <button onClick={() => setCryptoAnalysis(null)}><XCircle className="text-zinc-500 hover:text-white" /></button>
                </div>
                <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 font-mono text-sm text-amber-400">
                   {cryptoAnalysis.loading ? "DECRYPTING SIGNAL..." : cryptoAnalysis.text}
                </div>
             </div>
          </div>
        </div>
      )}
      
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700;900&display=swap');
        :root { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fadeIn { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  );
}
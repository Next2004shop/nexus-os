import React, { useState } from 'react';
import { User, Settings, Shield, LogOut, ChevronRight, Mail, Crown, Star, Share2, Bell, Globe, Moon, CreditCard, HelpCircle, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// eslint-disable-next-line no-unused-vars
const ProfileItem = ({ icon: Icon, label, value, onClick, isDanger, hasToggle }) => (
    <button onClick={onClick} className="w-full flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-colors group border border-transparent hover:border-white/5">
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isDanger ? 'bg-nexus-red/10 text-nexus-red' : 'bg-nexus-blue/10 text-nexus-blue'}`}>
                <Icon size={20} />
            </div>
            <div className="text-left">
                <div className={`font-medium ${isDanger ? 'text-nexus-red' : 'text-white'}`}>{label}</div>
                {value && <div className="text-xs text-nexus-subtext">{value}</div>}
            </div>
        </div>
        {hasToggle ? (
            <div className="w-10 h-6 bg-nexus-blue/20 rounded-full relative">
                <div className="absolute right-1 top-1 w-4 h-4 bg-nexus-blue rounded-full shadow-sm"></div>
            </div>
        ) : (
            <ChevronRight size={16} className="text-nexus-subtext group-hover:translate-x-1 transition-transform" />
        )}
    </button>
);

const SecurityCard = () => (
    <div className="bg-nexus-card border border-nexus-border p-5 rounded-2xl relative overflow-hidden">
        <div className="flex justify-between items-start mb-4">
            <div>
                <h3 className="text-white font-bold flex items-center gap-2">
                    <Shield size={18} className="text-nexus-green" />
                    Security Status
                </h3>
                <p className="text-nexus-subtext text-xs mt-1">Your account is well protected.</p>
            </div>
            <div className="text-right">
                <div className="text-2xl font-bold text-nexus-green">92%</div>
                <div className="text-[10px] text-nexus-subtext uppercase font-bold">Secure</div>
            </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-4">
            <div className="h-full w-[92%] bg-gradient-to-r from-nexus-blue to-nexus-green"></div>
        </div>

        <div className="grid grid-cols-2 gap-2">
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">2FA Enabled</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">Email Verified</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-green"></div>
                <span className="text-xs text-white/80">Phone Linked</span>
            </div>
            <div className="bg-black/20 p-2 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-nexus-yellow"></div>
                <span className="text-xs text-white/80">Anti-Phishing</span>
            </div>
        </div>
    </div>
);

const ReferralCard = () => (
    <div className="bg-gradient-to-br from-nexus-purple/20 to-nexus-blue/20 border border-nexus-purple/30 p-5 rounded-2xl relative overflow-hidden group cursor-pointer hover:border-nexus-purple/50 transition-all">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Crown size={80} />
        </div>
        <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
                <Crown size={18} className="text-nexus-yellow" />
                <span className="text-xs font-bold text-nexus-yellow uppercase tracking-wider">VIP Referral Hub</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Invite Friends, Earn Crypto</h3>
            <p className="text-nexus-subtext text-xs mb-4 max-w-[80%]">Get 20% of trading fees from every friend you invite to Nexus AI.</p>

            <div className="flex gap-3">
                <button className="flex-1 bg-white/10 hover:bg-white/20 text-white text-xs font-bold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2">
                    <Share2 size={14} /> Share Link
                </button>
                <div className="px-4 py-2 bg-black/30 rounded-xl border border-white/10 text-white font-mono text-xs flex items-center">
                    NEXUS-2024
                </div>
            </div>
        </div>
    </div>
);

const SettingsModal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
            <div className="bg-nexus-card border border-nexus-border w-full max-w-md rounded-2xl overflow-hidden shadow-2xl animate-slideUp">
                <div className="p-4 border-b border-white/10 flex justify-between items-center">
                    <h3 className="font-bold text-white">{title}</h3>
                    <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-full transition-colors">
                        <ChevronRight className="rotate-90" size={20} />
                    </button>
                </div>
                <div className="p-4">
                    {children}
                </div>
            </div>
        </div>
    );
};

export const ProfilePage = () => {
    const { currentUser, logout } = useAuth();
    const [activeModal, setActiveModal] = useState(null); // 'personal', 'payment', 'language'
    const [language, setLanguage] = useState('English (US)');
    const [cards, setCards] = useState([
        { type: 'Visa', last4: '4242', expiry: '12/25' },
        { type: 'Mastercard', last4: '8899', expiry: '09/26' }
    ]);

    const handleSavePersonal = (e) => {
        e.preventDefault();
        setActiveModal(null);
        alert("Personal Information Updated Successfully!");
    };

    const handleAddCard = (e) => {
        e.preventDefault();
        const newCard = { type: 'Visa', last4: Math.floor(1000 + Math.random() * 9000).toString(), expiry: '12/28' };
        setCards([...cards, newCard]);
        setActiveModal(null);
        alert("New Payment Method Added Successfully!");
    };

    return (
        <div className="min-h-screen bg-nexus-black pb-32 overflow-y-auto">
            <div className="max-w-2xl mx-auto p-4 space-y-6">

                {/* HEADER */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-white">Profile</h1>
                    <button className="p-2 hover:bg-white/10 rounded-full transition-colors text-nexus-subtext hover:text-white">
                        <Settings size={20} />
                    </button>
                </div>

                {/* USER CARD */}
                <div className="bg-nexus-card border border-nexus-border rounded-3xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6">
                        <div className="bg-nexus-yellow/10 text-nexus-yellow text-[10px] font-bold px-3 py-1 rounded-full border border-nexus-yellow/20 flex items-center gap-1">
                            <Crown size={12} /> PLATINUM TRADER
                        </div>
                    </div>

                    <div className="flex items-center gap-5 relative z-10">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-nexus-blue to-purple-600 p-[2px]">
                            <div className="w-full h-full rounded-full bg-nexus-black flex items-center justify-center overflow-hidden">
                                {currentUser?.photoURL ? (
                                    <img src={currentUser.photoURL} alt="Profile" className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-2xl font-bold text-white">{currentUser?.email?.[0].toUpperCase()}</span>
                                )}
                            </div>
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{currentUser?.displayName || 'Nexus Trader'}</h2>
                            <p className="text-nexus-subtext text-sm flex items-center gap-1 mb-2">
                                <Mail size={12} /> {currentUser?.email}
                            </p>
                            <div className="flex items-center gap-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-nexus-green/10 text-nexus-green border border-nexus-green/20">
                                    Verified
                                </span>
                                <span className="text-nexus-subtext text-[10px]">ID: 8493021</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SECURITY CENTER */}
                <SecurityCard />

                {/* REFERRAL HUB */}
                <ReferralCard />

                {/* SETTINGS GROUPS */}
                <div className="space-y-6">
                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Account Settings</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={User} label="Personal Information" value="KYC Level 2" onClick={() => setActiveModal('personal')} />
                            <ProfileItem icon={CreditCard} label="Payment Methods" value={`${cards.length} Linked`} onClick={() => setActiveModal('payment')} />
                            <ProfileItem icon={Globe} label="Language" value={language} onClick={() => setActiveModal('language')} />
                            <ProfileItem icon={Moon} label="Dark Mode" hasToggle onClick={() => alert("Dark Mode is already active!")} />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Notifications</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={Bell} label="Push Notifications" hasToggle onClick={() => alert("Push Notifications toggled")} />
                            <ProfileItem icon={Mail} label="Email Alerts" hasToggle onClick={() => alert("Email Alerts toggled")} />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-xs font-bold text-nexus-subtext uppercase tracking-wider mb-3 px-2">Support</h3>
                        <div className="bg-nexus-card border border-nexus-border rounded-2xl overflow-hidden">
                            <ProfileItem icon={HelpCircle} label="Help Center" onClick={() => window.location.href = '/help'} />
                            <ProfileItem icon={MessageSquare} label="Live Chat" value="Online" onClick={() => window.location.href = '/help'} />
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="w-full py-4 rounded-2xl bg-nexus-red/10 text-nexus-red font-bold text-sm hover:bg-nexus-red/20 transition-colors flex items-center justify-center gap-2"
                    >
                        <LogOut size={18} /> Log Out
                    </button>

                    <div className="text-center text-nexus-subtext text-[10px] pb-4">
                        Nexus AI v2.4.0 (Build 892)
                    </div>
                </div>
            </div>

            {/* MODALS */}
            <SettingsModal isOpen={activeModal === 'personal'} onClose={() => setActiveModal(null)} title="Edit Personal Info">
                <form onSubmit={handleSavePersonal} className="space-y-4">
                    <div>
                        <label className="text-xs text-nexus-subtext block mb-1">Full Name</label>
                        <input type="text" defaultValue={currentUser?.displayName || "Nexus Trader"} className="w-full bg-nexus-black border border-white/10 rounded-lg p-3 text-white outline-none focus:border-nexus-blue" />
                    </div>
                    <div>
                        <label className="text-xs text-nexus-subtext block mb-1">Email Address</label>
                        <input type="email" defaultValue={currentUser?.email} disabled className="w-full bg-nexus-black/50 border border-white/5 rounded-lg p-3 text-nexus-subtext outline-none cursor-not-allowed" />
                    </div>
                    <div>
                        <label className="text-xs text-nexus-subtext block mb-1">Phone Number</label>
                        <input type="tel" defaultValue="+254 712 345 678" className="w-full bg-nexus-black border border-white/10 rounded-lg p-3 text-white outline-none focus:border-nexus-blue" />
                    </div>
                    <button type="submit" className="w-full bg-nexus-blue text-black font-bold py-3 rounded-lg mt-2">Save Changes</button>
                </form>
            </SettingsModal>

            <SettingsModal isOpen={activeModal === 'payment'} onClose={() => setActiveModal(null)} title="Payment Methods">
                <div className="space-y-3 mb-4">
                    {cards.map((card, i) => (
                        <div key={i} className="bg-nexus-black border border-white/10 p-3 rounded-lg flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-6 bg-white/10 rounded flex items-center justify-center text-[10px] font-bold text-white">{card.type}</div>
                                <div>
                                    <div className="text-sm text-white">•••• {card.last4}</div>
                                    <div className="text-xs text-nexus-subtext">Expires {card.expiry}</div>
                                </div>
                            </div>
                            <button className="text-nexus-red text-xs hover:underline">Remove</button>
                        </div>
                    ))}
                </div>
                <button onClick={handleAddCard} className="w-full border border-dashed border-white/20 text-nexus-subtext font-bold py-3 rounded-lg hover:bg-white/5 hover:text-white transition-colors">
                    + Add New Card
                </button>
            </SettingsModal>

            <SettingsModal isOpen={activeModal === 'language'} onClose={() => setActiveModal(null)} title="Select Language">
                <div className="space-y-2">
                    {['English (US)', 'Spanish', 'French', 'Swahili', 'Chinese'].map((lang) => (
                        <button
                            key={lang}
                            onClick={() => { setLanguage(lang); setActiveModal(null); }}
                            className={`w-full p-3 rounded-lg text-left flex justify-between items-center ${language === lang ? 'bg-nexus-blue/10 text-nexus-blue border border-nexus-blue/30' : 'bg-nexus-black border border-white/10 text-white hover:bg-white/5'}`}
                        >
                            {lang}
                            {language === lang && <div className="w-2 h-2 rounded-full bg-nexus-blue"></div>}
                        </button>
                    ))}
                </div>
            </SettingsModal>
        </div>
    );
};

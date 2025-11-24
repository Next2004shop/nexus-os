import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, X, Zap, Shield, Globe } from 'lucide-react';
import { GoogleAuthProvider, signInWithPopup, signInWithRedirect, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail } from 'firebase/auth';
import { auth } from '../services/firebase';
import { useAuth } from '../context/AuthContext';

export const AuthPage = ({ onClose }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [showPassword, setShowPassword] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const { currentUser, login } = useAuth();

    useEffect(() => {
        if (currentUser) {
            onClose();
        }
    }, [currentUser, onClose]);

    const handleGoogleLogin = async () => {
        try {
            setLoading(true);
            setError('');
            const provider = new GoogleAuthProvider();
            try {
                await signInWithPopup(auth, provider);
            } catch (popupErr) {
                console.log("Popup failed, trying redirect...", popupErr);
                await signInWithRedirect(auth, provider);
            }
        } catch (err) {
            console.error("Google Login Error:", err);
            let msg = "Google Sign-In failed.";
            if (err.code === 'auth/unauthorized-domain' || err.message.includes('unauthorized domain')) {
                msg = `Domain not authorized: ${window.location.hostname}. Add this to Firebase Console.`;
            }
            setError(`${msg} (${err.code || err.message})`);
        } finally {
            setLoading(false);
        }
    };

    const handleDemoLogin = async () => {
        try {
            setLoading(true);
            setError('');
            await login('demo@nexus.ai', 'demo123');
        } catch (err) {
            console.error("Demo login error:", err);
            setError("Demo login failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleEmailAuth = async () => {
        if (!email || (!password && isLogin)) {
            setError('Please enter email and password.');
            return;
        }
        try {
            setLoading(true);
            setError('');
            if (isLogin) {
                await signInWithEmailAndPassword(auth, email, password);
            } else {
                await createUserWithEmailAndPassword(auth, email, password);
            }
            onClose();
        } catch (err) {
            setError(err.message.replace('Firebase: ', ''));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* BACKDROP */}
            <div className="absolute inset-0 bg-nexus-black/90 backdrop-blur-md" onClick={onClose}></div>

            {/* MAIN CARD */}
            <div className="relative w-full max-w-md bg-[#0A0A0A] border border-nexus-blue/20 rounded-3xl shadow-[0_0_50px_rgba(0,240,255,0.1)] overflow-hidden animate-slideUp">

                {/* DECORATIVE GLOWS */}
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-nexus-blue to-transparent"></div>
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-nexus-blue/20 rounded-full blur-3xl pointer-events-none"></div>
                <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-nexus-green/20 rounded-full blur-3xl pointer-events-none"></div>

                {/* HEADER */}
                <div className="p-8 pb-0 text-center">
                    <div className="w-16 h-16 mx-auto bg-nexus-blue/10 rounded-2xl flex items-center justify-center mb-4 border border-nexus-blue/30 shadow-[0_0_20px_rgba(0,240,255,0.2)]">
                        <Globe size={32} className="text-nexus-blue animate-pulse" />
                    </div>
                    <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">
                        NXTradex<span className="text-nexus-blue">OS</span>
                    </h2>
                    <p className="text-nexus-subtext text-sm">Institutional Grade Terminal</p>
                </div>

                {/* FORM */}
                <div className="p-8 space-y-5">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-3 rounded-xl text-xs text-center">
                            {error}
                        </div>
                    )}

                    {/* DEMO BUTTON (PRIMARY) */}
                    <button
                        onClick={handleDemoLogin}
                        disabled={loading}
                        className="w-full group relative overflow-hidden bg-gradient-to-r from-nexus-blue to-cyan-600 text-black font-bold py-4 rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] shadow-[0_0_20px_rgba(0,240,255,0.3)]"
                    >
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                        <div className="relative flex items-center justify-center gap-2">
                            <Zap size={20} className="fill-black" />
                            <span>ENTER GOD MODE (DEMO)</span>
                        </div>
                    </button>

                    <div className="flex items-center gap-4">
                        <div className="h-[1px] bg-white/10 flex-1"></div>
                        <span className="text-nexus-subtext text-xs uppercase tracking-wider">Or Secure Login</span>
                        <div className="h-[1px] bg-white/10 flex-1"></div>
                    </div>

                    {/* INPUTS */}
                    <div className="space-y-3">
                        <div className="group bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus-within:border-nexus-blue/50 focus-within:bg-white/10 transition-all">
                            <label className="text-[10px] text-nexus-subtext uppercase tracking-wider font-bold mb-1 block">Email Access</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-transparent text-white outline-none font-medium placeholder-white/20"
                                placeholder="trader@nexus.ai"
                            />
                        </div>
                        <div className="group bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus-within:border-nexus-blue/50 focus-within:bg-white/10 transition-all relative">
                            <label className="text-[10px] text-nexus-subtext uppercase tracking-wider font-bold mb-1 block">Security Key</label>
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-transparent text-white outline-none font-medium placeholder-white/20"
                                placeholder="••••••••"
                            />
                            <button
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-nexus-subtext hover:text-white transition-colors"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {/* SECONDARY ACTIONS */}
                    <div className="flex gap-3">
                        <button
                            onClick={handleEmailAuth}
                            disabled={loading}
                            className="flex-1 bg-white/5 border border-white/10 text-white font-bold py-3 rounded-xl hover:bg-white/10 transition-colors"
                        >
                            {isLogin ? 'Login' : 'Register'}
                        </button>
                        <button
                            onClick={handleGoogleLogin}
                            disabled={loading}
                            className="flex-1 bg-white/5 border border-white/10 text-white font-bold py-3 rounded-xl hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
                        >
                            <img src="https://www.svgrepo.com/show/475656/google-color.svg" className="w-5 h-5" alt="Google" />
                            Google
                        </button>
                    </div>

                    <div className="text-center">
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-nexus-subtext text-xs hover:text-nexus-blue transition-colors"
                        >
                            {isLogin ? "Need an account? Initialize Protocol" : "Already have access? Login"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

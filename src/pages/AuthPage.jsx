import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, X } from 'lucide-react';
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

    const { currentUser } = useAuth();

    // Auto-close if user is detected (double safety)
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
            // Try popup first, if it fails (e.g. mobile), try redirect
            try {
                await signInWithPopup(auth, provider);
                onClose();
            } catch (popupErr) {
                console.log("Popup failed, trying redirect...", popupErr);
                await signInWithRedirect(auth, provider);
            }
        } catch (err) {
            console.error("Google Login Error:", err);
            let msg = "Google Sign-In failed.";

            // Check for unauthorized domain specifically
            if (err.code === 'auth/unauthorized-domain' || err.message.includes('unauthorized domain')) {
                msg = `Domain not authorized: ${window.location.hostname}. Add this to Firebase Console -> Authentication -> Settings.`;
            } else if (err.code === 'auth/popup-closed-by-user') {
                msg = "Sign-in cancelled.";
            } else if (err.code === 'auth/cancelled-popup-request') {
                msg = "Popup cancelled.";
            } else if (err.code === 'auth/popup-blocked') {
                msg = "Popup blocked. Please allow popups.";
            } else if (err.code === 'auth/operation-not-allowed') {
                msg = "Google Sign-In is not enabled in Firebase Console.";
            } else if (err.code === 'auth/configuration-not-found') {
                msg = "Google Sign-In provider is disabled in Firebase Console. Please enable it.";
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
            await signInWithEmailAndPassword(auth, 'demo@nexus.ai', 'password123');
            onClose();
        } catch (err) {
            // If demo user doesn't exist, create it
            if (err.code === 'auth/user-not-found' || err.code === 'auth/invalid-credential') {
                try {
                    await createUserWithEmailAndPassword(auth, 'demo@nexus.ai', 'password123');
                    onClose();
                } catch (createErr) {
                    setError("Failed to create demo account.");
                }
            } else {
                setError("Demo login failed.");
            }
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
            console.error(err);
            let msg = err.message;
            if (msg.includes('auth/invalid-email')) msg = 'Invalid email address.';
            if (msg.includes('auth/user-not-found')) msg = 'No account found with this email.';
            if (msg.includes('auth/wrong-password')) msg = 'Incorrect password.';
            if (msg.includes('auth/email-already-in-use')) msg = 'Email already in use.';
            setError(msg.replace('Firebase: ', ''));
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async () => {
        if (!email) {
            setError('Please enter your email to reset password.');
            return;
        }
        try {
            setLoading(true);
            await sendPasswordResetEmail(auth, email);
            setSuccess('Password reset email sent! Check your inbox.');
            setError('');
        } catch (err) {
            setError(err.message.replace('Firebase: ', ''));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-nexus-black flex flex-col animate-fadeIn">
            {/* HEADER */}
            <div className="flex justify-between items-center p-4">
                <button onClick={onClose}>
                    <X size={24} className="text-nexus-text" />
                </button>
                <div className="text-nexus-subtext text-sm">Help</div>
            </div>

            {/* CONTENT */}
            <div className="px-6 mt-4">
                <h1 className="text-3xl font-bold text-nexus-text mb-8">
                    {isLogin ? 'Log In' : 'Create Account'}
                </h1>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg mb-4 text-sm">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="bg-green-500/10 border border-green-500/50 text-green-500 p-3 rounded-lg mb-4 text-sm">
                        {success}
                    </div>
                )}

                <div className="space-y-6">
                    <div>
                        <label className="block text-nexus-subtext text-sm mb-2">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-nexus-card border border-nexus-border rounded-lg p-3 text-nexus-text focus:border-nexus-yellow outline-none transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-nexus-subtext text-sm mb-2">Password</label>
                        <div className="relative">
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-nexus-card border border-nexus-border rounded-lg p-3 text-nexus-text focus:border-nexus-yellow outline-none transition-colors pr-10"
                            />
                            <button
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-3 text-nexus-subtext"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                        {isLogin && (
                            <button onClick={handleResetPassword} className="text-nexus-yellow text-xs mt-2 font-medium">
                                Forgot Password?
                            </button>
                        )}
                    </div>

                    <button
                        onClick={handleEmailAuth}
                        disabled={loading}
                        className="w-full bg-nexus-yellow text-nexus-black font-bold py-3 rounded-lg hover:bg-[#FDE059] transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Processing...' : (isLogin ? 'Log In' : 'Create Account')}
                    </button>

                    <div className="flex items-center gap-4 my-6">
                        <div className="h-[1px] bg-nexus-border flex-1"></div>
                        <span className="text-nexus-subtext text-sm">or</span>
                        <div className="h-[1px] bg-nexus-border flex-1"></div>
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        disabled={loading}
                        className="w-full bg-nexus-card border border-nexus-border text-nexus-text font-bold py-3 rounded-lg hover:bg-nexus-border transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        <img src="https://www.svgrepo.com/show/475656/google-color.svg" className="w-5 h-5" alt="Google" />
                        Continue with Google
                    </button>

                    <button
                        onClick={handleDemoLogin}
                        disabled={loading}
                        className="w-full mt-3 bg-nexus-card border border-nexus-yellow/50 text-nexus-yellow font-bold py-3 rounded-lg hover:bg-nexus-yellow/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        ⚡ Quick Demo Login (Auto)
                    </button>

                    <div className="text-center mt-6">
                        <span className="text-nexus-subtext text-sm">
                            {isLogin ? "Don't have an account? " : "Already have an account? "}
                        </span>
                        <button
                            onClick={() => {
                                setIsLogin(!isLogin);
                                setError('');
                                setSuccess('');
                            }}
                            className="text-nexus-yellow font-bold text-sm"
                        >
                            {isLogin ? 'Register' : 'Log In'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

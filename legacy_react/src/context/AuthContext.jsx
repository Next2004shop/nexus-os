/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../services/firebase';
import { onAuthStateChanged, signInWithEmailAndPassword, signOut, setPersistence, browserLocalPersistence } from 'firebase/auth';
import { userRepository } from '../services/userRepository';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let unsubscribe;

        const initAuth = async () => {
            try {
                // 1. Set Persistence FIRST
                await setPersistence(auth, browserLocalPersistence);

                // 2. Listen for Auth Changes
                unsubscribe = onAuthStateChanged(auth, async (user) => {
                    if (user) {
                        console.log("Auth State: User Detected", user.uid);
                        setCurrentUser(user);

                        // Initialize Firestore (Non-blocking)
                        userRepository.initializeUser(user).catch(err =>
                            console.error("User Repo Init Failed:", err)
                        );
                    } else {
                        console.log("Auth State: No User");
                        // Check for local demo session as fallback
                        const demoUser = localStorage.getItem('nexus_demo_user');
                        if (demoUser) {
                            console.log("Restoring Demo User");
                            setCurrentUser(JSON.parse(demoUser));
                        } else {
                            setCurrentUser(null);
                        }
                    }
                    setLoading(false);
                });
            } catch (error) {
                console.error("Auth Init Error:", error);
                setLoading(false);
            }
        };

        initAuth();

        return () => {
            if (unsubscribe) unsubscribe();
        };
    }, []);

    const login = async (email, password) => {
        if (email === 'demo@nexus.ai' && password === 'demo123') {
            const demoUser = {
                uid: 'demo-user-123',
                email: 'demo@nexus.ai',
                displayName: 'Demo Commander',
                photoURL: null,
                isAnonymous: true
            };
            localStorage.setItem('nexus_demo_user', JSON.stringify(demoUser));
            setCurrentUser(demoUser);
            return Promise.resolve(demoUser);
        }
        return signInWithEmailAndPassword(auth, email, password);
    };

    const logout = async () => {
        localStorage.removeItem('nexus_demo_user');
        return signOut(auth);
    };

    const value = {
        currentUser,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

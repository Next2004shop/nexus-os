import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../services/firebase';
import { onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'firebase/auth';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            if (user) {
                setCurrentUser(user);
            } else {
                // Check for local demo session
                const demoUser = localStorage.getItem('nexus_demo_user');
                if (demoUser) {
                    setCurrentUser(JSON.parse(demoUser));
                } else {
                    setCurrentUser(null);
                }
            }
            setLoading(false);
        });
        return unsubscribe;
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

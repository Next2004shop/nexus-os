import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import api from '../api/client';

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(() => {
        return sessionStorage.getItem('nexus_token');
    });
    const [isLoading, setIsLoading] = useState(true);

    const isAuthenticated = !!token && !!user;

    // Check auth on mount
    useEffect(() => {
        if (token) {
            checkAuth();
        } else {
            setIsLoading(false);
        }
    }, []);

    const checkAuth = async () => {
        try {
            const response = await api.get('/auth/me', {
                headers: { Authorization: `Bearer ${token}` },
            });
            setUser(response.data.user);
        } catch {
            sessionStorage.removeItem('nexus_token');
            setToken(null);
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = useCallback(async (username: string, password: string) => {
        try {
            const response = await api.post('/auth/login', { username, password });
            const { access_token, user: userData } = response.data;

            sessionStorage.setItem('nexus_token', access_token);
            setToken(access_token);
            setUser(userData);

            return { success: true };
        } catch (err: any) {
            const message = err.response?.data?.error || 'Login failed';
            return { success: false, error: message };
        }
    }, []);

    const logout = useCallback(async () => {
        try {
            await api.post('/auth/logout');
        } catch {
            // Logout locally even if server call fails
        }
        sessionStorage.removeItem('nexus_token');
        setToken(null);
        setUser(null);
    }, []);

    const refreshToken = useCallback(async () => {
        try {
            const response = await api.post('/auth/refresh');
            const { access_token } = response.data;
            sessionStorage.setItem('nexus_token', access_token);
            setToken(access_token);
            return true;
        } catch {
            sessionStorage.removeItem('nexus_token');
            setToken(null);
            setUser(null);
            return false;
        }
    }, []);

    return (
        <AuthContext.Provider value={{ user, token, isAuthenticated, isLoading, login, logout, refreshToken }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}

export default AuthContext;

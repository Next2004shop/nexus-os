import axios from 'axios';

/**
 * Resolve API base URL from environment.
 * Priority: window.NEXUS_CONFIG (desktop/container) > VITE_API_URL (dev) > localhost fallback
 */
function getApiBaseUrl(): string {
    if (typeof window !== 'undefined' && (window as any).NEXUS_CONFIG?.VITE_API_URL) {
        return (window as any).NEXUS_CONFIG.VITE_API_URL;
    }
    return import.meta.env.VITE_API_URL || 'http://localhost:8080';
}

const api = axios.create({
    baseURL: getApiBaseUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Send cookies for auth
});

// JWT interceptor — attach token to every request
api.interceptors.request.use((config) => {
    const token = sessionStorage.getItem('nexus_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor — handle 401 (try refresh, then redirect to login)
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshResponse = await axios.post(
                    `${getApiBaseUrl()}/auth/refresh`,
                    {},
                    { withCredentials: true }
                );
                const newToken = refreshResponse.data.access_token;
                sessionStorage.setItem('nexus_token', newToken);
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
            } catch {
                sessionStorage.removeItem('nexus_token');
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

// API Methods
export const checkHealth = async () => {
    const response = await api.get('/health');
    return response.data;
};

export const getStatus = async () => {
    const response = await api.get('/status');
    return response.data;
};

export const executeTrade = async (symbol: string, side: 'buy' | 'sell', quantity: number) => {
    const response = await api.post('/trade', { symbol, side, quantity });
    return response.data;
};

export const triggerKillSwitch = async (symbol?: string) => {
    const response = await api.post('/kill', { symbol });
    return response.data;
};

export const triggerAnalysis = async (symbol: string, data: any) => {
    const response = await api.post('/analyze', { symbol, data });
    return response.data;
};

// Meta-Intelligence (Phase 10)
export const getSystemEvolution = async () => {
    const response = await api.get('/api/meta/evolution');
    return response.data;
};

export const getTradeledger = async (count: number = 30) => {
    const response = await api.get(`/api/meta/ledger?count=${count}`);
    return response.data;
};

export const forceMetaAnalysis = async () => {
    const response = await api.post('/api/meta/analyze');
    return response.data;
};

export default api;

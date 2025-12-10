const API_BASE_URL = 'http://localhost:5002'; // New FastAPI Backend Port

// Helper for JWT Auth (to be implemented fully later)
let authToken = '';

async function login() {
    // Auto-login as admin for now
    try {
        const formData = new FormData();
        formData.append('username', 'admin');
        formData.append('password', 'securepassword');

        const res = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        if (data.access_token) {
            authToken = data.access_token;
            console.log("Authenticated with Backend");
        }
    } catch (e) {
        console.error("Login Failed", e);
    }
}

// Initialize Auth
login();

export const nexusApi = {
    async getStatus() {
        try {
            const res = await fetch(`${API_BASE_URL}/`);
            return await res.json();
        } catch (e) {
            return { status: "offline" };
        }
    },

    async getPrices() {
        if (!authToken) await login();
        try {
            const res = await fetch(`${API_BASE_URL}/market/prices`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            return await res.json();
        } catch (e) {
            console.error("Get Prices Failed", e);
            return {};
        }
    },

    async placeTrade(symbol: string, type: 'BUY' | 'SELL', lots: number, sl?: number, tp?: number) {
        if (!authToken) await login();
        const res = await fetch(`${API_BASE_URL}/trade/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ symbol, type, lots, sl, tp })
        });
        return await res.json();
    },

    async aiChat(message: string) {
        if (!authToken) await login();
        const res = await fetch(`${API_BASE_URL}/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message })
        });
        return await res.json();
    }
};

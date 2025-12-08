// Nexus API Bridge
const API_BASE = 'http://localhost:5001';
const AUTH_HEADER = 'Basic ' + btoa('admin:securepassword');

const NexusAPI = {
    async getStatus() {
        try {
            const res = await fetch(`${API_BASE}/status`, {
                headers: { 'Authorization': AUTH_HEADER }
            });
            return await res.json();
        } catch (e) {
            console.error("API Error:", e);
            return { status: "OFFLINE" };
        }
    },

    async placeTrade(symbol, type, lots) {
        try {
            const res = await fetch(`${API_BASE}/trade`, {
                method: 'POST',
                headers: {
                    'Authorization': AUTH_HEADER,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    symbol: symbol,
                    type: type, // BUY or SELL
                    lots: parseFloat(lots)
                })
            });
            return await res.json();
        } catch (e) {
            return { error: e.message };
        }
    },

    async aiChat(message, history = []) {
        try {
            const res = await fetch(`${API_BASE}/ai/chat`, {
                method: 'POST',
                headers: {
                    'Authorization': AUTH_HEADER,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    history: history
                })
            });
            return await res.json();
        } catch (e) {
            return { response: "❌ Connection Error: Backend Offline" };
        }
    }
};

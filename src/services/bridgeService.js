import axios from 'axios';

// Default to localhost for desktop/emulator. 
// User can update this in settings if running on a separate device.
const BRIDGE_URL = 'http://localhost:5000';
const AUTH = { username: 'admin', password: 'securepassword' };

export const bridgeService = {
    // Check Bridge Status
    getStatus: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/status`, { auth: AUTH });
            return response.data;
        } catch (error) {
            console.error("Bridge Status Error:", error);
            return { status: 'OFFLINE', msg: "Bridge Disconnected" };
        }
    },

    // Execute Trade (Buy/Sell)
    executeTrade: async (symbol, type, lots, sl = 0, tp = 0) => {
        try {
            const response = await axios.post(`${BRIDGE_URL}/trade`, {
                symbol,
                type: type.toUpperCase(),
                lots,
                sl,
                tp
            }, { auth: AUTH });
            return response.data;
        } catch (error) {
            console.error("Bridge Trade Error:", error);
            throw new Error(error.response?.data?.error || "Trade Failed");
        }
    },

    // Get Open Positions
    getPositions: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/positions`, { auth: AUTH });
            return response.data;
        } catch (error) {
            console.error("Bridge Positions Error:", error);
            return [];
        }
    },

    // Get Trade History
    getHistory: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/history`, { auth: AUTH });
            return response.data;
        } catch (error) {
            console.error("Bridge History Error:", error);
            return [];
        }
    },

    // AI Analysis via Bridge
    analyzeMarket: async (symbol) => {
        try {
            const response = await axios.post(`${BRIDGE_URL}/ai/analyze`, { symbol }, { auth: AUTH });
            return response.data;
        } catch (error) {
            console.error("Bridge AI Error:", error);
            return null;
        }
    }
};

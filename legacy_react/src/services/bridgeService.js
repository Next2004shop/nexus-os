import axios from 'axios';

const BRIDGE_URL = import.meta.env.VITE_BRIDGE_URL || '/api/bridge';

export const bridgeService = {
    // Check Bridge Status
    getStatus: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/status`);
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
            });
            return response.data;
        } catch (error) {
            console.error("Bridge Trade Error:", error);
            throw new Error(error.response?.data?.error || "Trade Failed");
        }
    },

    // Get Open Positions
    getPositions: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/positions`);
            return response.data;
        } catch (error) {
            console.error("Bridge Positions Error:", error);
            return [];
        }
    },

    // Get Trade History
    getHistory: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/history`);
            return response.data;
        } catch (error) {
            console.error("Bridge History Error:", error);
            return [];
        }
    },

    // AI Analysis via Bridge
    analyzeMarket: async (symbol) => {
        try {
            const response = await axios.post(`${BRIDGE_URL}/ai/analyze`, { symbol });
            return response.data;
        } catch (error) {
            console.error("Bridge AI Error:", error);
            return null;
        }
    },

    // Get Real-Time Market Prices
    getMarketPrices: async () => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/market/prices`);
            return response.data;
        } catch (error) {
            console.error("Bridge Prices Error:", error);
            return [];
        }
    },

    // Get OHLC Candles
    getCandles: async (symbol, timeframe = 'M15') => {
        try {
            const response = await axios.get(`${BRIDGE_URL}/market/candles`, {
                params: { symbol, timeframe }
            });
            return response.data;
        } catch (error) {
            console.error("Bridge Candles Error:", error);
            return [];
        }
    }
};

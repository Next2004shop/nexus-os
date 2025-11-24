import axios from 'axios';

// CoinGecko API (Free Tier: 10-30 calls/min)
const CG_BASE_URL = 'https://api.coingecko.com/api/v3';

// Finnhub API (Free Tier) - You might need a key later, but we'll try public endpoints or mock fallback
const FINNHUB_BASE_URL = 'https://finnhub.io/api/v1';

export const marketData = {
    // Fetch Top Cryptos
    getTopCryptos: async (currency = 'usd') => {
        try {
            const response = await axios.get(`${CG_BASE_URL}/coins/markets`, {
                params: {
                    vs_currency: currency,
                    order: 'market_cap_desc',
                    per_page: 20,
                    page: 1,
                    sparkline: true,
                    price_change_percentage: '24h'
                }
            });
            return response.data;
        } catch (error) {
            console.error("Market Data Error (Crypto):", error);
            return []; // Return empty array on failure to prevent crash
        }
    },

    // Fetch Specific Crypto Details
    getCryptoDetails: async (id) => {
        try {
            const response = await axios.get(`${CG_BASE_URL}/coins/${id}`, {
                params: {
                    localization: false,
                    tickers: false,
                    market_data: true,
                    community_data: false,
                    developer_data: false,
                    sparkline: true
                }
            });
            return response.data;
        } catch (error) {
            console.error("Crypto Details Error:", error);
            return null;
        }
    },

    // Fetch Global News (Crypto)
    getNews: async () => {
        try {
            // Using CoinGecko Status Updates as a proxy for news to avoid API Key requirements for NewsAPI
            const response = await axios.get(`${CG_BASE_URL}/status_updates`);
            return response.data.status_updates;
        } catch (error) {
            console.error("News Error:", error);
            return [];
        }
    },

    // Mock Stock Data (Real API requires Key)
    getStocks: () => {
        return [
            { symbol: 'AAPL', name: 'Apple Inc.', price: 185.92, change: 1.25 },
            { symbol: 'TSLA', name: 'Tesla, Inc.', price: 242.50, change: -0.85 },
            { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 485.09, change: 2.10 },
            { symbol: 'MSFT', name: 'Microsoft', price: 375.20, change: 0.55 },
            { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 138.40, change: 0.90 },
        ];
    }
};

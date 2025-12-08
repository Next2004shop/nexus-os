import { bridgeService } from './bridgeService';

// MAPPING: Frontend ID -> MT5 Symbol
const ASSET_MAP = {
    // Crypto
    'bitcoin': 'BTCUSD',
    'ethereum': 'ETHUSD',
    'solana': 'SOLUSD',

    // Stocks
    'aapl': 'AAPL',
    'tsla': 'TSLA',
    'nvda': 'NVDA',
    'msft': 'MSFT',
    'googl': 'GOOGL',
    'amzn': 'AMZN',
    'meta': 'META',
    'nflx': 'NFLX',
    'us30': 'US30',
    'nas100': 'NAS100',
    'spx500': 'SPX500',

    // Commodities
    'xau': 'XAUUSD',
    'xag': 'XAGUSD',
    'wti': 'USOIL', // Common MT5 name
    'brent': 'UKOIL'
};

export const marketData = {
    // Fetch Top Cryptos (Now from MT5)
    getTopCryptos: async () => {
        const prices = await bridgeService.getMarketPrices();
        if (!prices || prices.length === 0) return [];

        // Filter for Crypto
        const cryptoSymbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD'];
        return prices.filter(p => cryptoSymbols.includes(p.symbol)).map(p => ({
            id: p.symbol.toLowerCase(),
            symbol: p.symbol,
            name: p.symbol,
            current_price: p.last,
            price_change_percentage_24h: p.change,
            image: `https://assets.coingecko.com/coins/images/1/large/bitcoin.png` // Placeholder or map
        }));
    },

    // Fetch Real Stock Data (From MT5)
    getStocks: async () => {
        const prices = await bridgeService.getMarketPrices();
        if (!prices || prices.length === 0) return [];

        // Filter for Stocks
        const stockSymbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX'];
        return prices.filter(p => stockSymbols.includes(p.symbol)).map(p => ({
            id: p.symbol.toLowerCase(),
            symbol: p.symbol,
            name: p.symbol,
            price: p.last,
            change: p.change,
            type: 'stock'
        }));
    },

    // Fetch Commodities (From MT5)
    getCommodities: async () => {
        const prices = await bridgeService.getMarketPrices();
        if (!prices || prices.length === 0) return [];

        // Filter for Commodities
        const commSymbols = ['XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL'];
        return prices.filter(p => commSymbols.includes(p.symbol)).map(p => ({
            id: p.symbol.toLowerCase(),
            symbol: p.symbol,
            name: p.symbol,
            price: p.last,
            change: p.change,
            type: 'commodity'
        }));
    },

    // Get Latest Price for Single Asset
    getLatestPrice: async (asset) => {
        if (!asset) return null;
        // We can re-use getMarketPrices or add a specific endpoint. 
        // For efficiency, we'll use the bulk fetch for now or fallback to asset.price
        // Ideally, bridgeService should have getPrice(symbol)
        return asset.price;
    },

    // Get OHLC Candles (Bridge AI Analyze returns candles!)
    // Get OHLC Candles (Bridge AI Analyze returns candles!)
    getCandles: async (assetId) => {
        const mt5Symbol = ASSET_MAP[assetId] || assetId.toUpperCase();
        // Use the new Bridge Endpoint
        const candles = await bridgeService.getCandles(mt5Symbol, 'M15'); // Default to M15 for now

        // Format for Chart (Lightweight Charts expects: time (seconds), open, high, low, close)
        return candles.map(c => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        }));
    },

    // Get Market News
    getNews: async () => {
        // Placeholder for Bridge News API
        // If the bridge has a news endpoint, call it here.
        // For now, return empty to avoid "undefined" errors in HomePage
        return [];
    }
};

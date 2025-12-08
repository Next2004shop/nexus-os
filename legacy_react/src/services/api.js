import axios from 'axios';
import { logTradeToCloud } from './firebase';

// Use environment variable or fallback to local IP (change this to your computer's IP)
// Use environment variable or fallback to local IP (change this to your computer's IP)
const API_URL = 'http://35.239.252.226:3000/api/bridge'; // Hardcoded for APK Connectivity
const AUTH_USERNAME = 'admin';
const AUTH_PASSWORD = 'securepassword';

const api = axios.create({
  baseURL: API_URL,
  auth: {
    username: AUTH_USERNAME,
    password: AUTH_PASSWORD
  },
  timeout: 3000 // Faster timeout for better UX
});

// Mock Data for Demo Mode
const MOCK_POSITIONS = [
  { ticket: 123456, symbol: 'BTCUSD', volume: 0.5, price_open: 64000, profit: 1250.50 },
  { ticket: 123457, symbol: 'EURUSD', volume: 1.0, price_open: 1.0850, profit: -25.00 },
];

export const checkStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch {
    console.warn("Bridge Disconnected. Switching to DEMO MODE.");
    return { status: "DEMO", msg: "Demo Mode Active" };
  }
};

export const getPositions = async () => {
  try {
    const response = await api.get('/positions');
    return response.data;
  } catch {
    // Return mock positions in Demo Mode
    return MOCK_POSITIONS;
  }
};

export const placeTrade = async (symbol, type, volume, sl = 0, tp = 0) => {
  try {
    const response = await api.post('/trade', {
      symbol,
      type,
      lots: volume,
      sl,
      tp
    });
    return response.data;
  } catch {
    // Simulate trade execution in Demo Mode
    console.log(`[DEMO] Trade Placed: ${type} ${volume} ${symbol}`);

    const tradeResult = {
      status: "EXECUTED",
      ticket: Math.floor(Math.random() * 1000000),
      msg: "Demo Trade Executed"
    };

    // Log to Firebase if available
    logTradeToCloud({
      ticket: tradeResult.ticket,
      symbol,
      type,
      volume,
      price: 0, // Mock price
      status: 'EXECUTED'
    });

    return tradeResult;
  }
};

export default api;

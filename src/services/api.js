import axios from 'axios';

const API_URL = 'http://192.168.43.153:5000';
const AUTH_USERNAME = 'admin';
const AUTH_PASSWORD = 'securepassword';

const api = axios.create({
  baseURL: API_URL,
  auth: {
    username: AUTH_USERNAME,
    password: AUTH_PASSWORD
  },
  timeout: 5000
});

export const checkStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch (error) {
    console.error("Bridge Status Error:", error);
    return { status: "OFFLINE", msg: "Bridge Disconnected" };
  }
};

export const getPositions = async () => {
  try {
    const response = await api.get('/positions');
    return response.data;
  } catch (error) {
    return [];
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
  } catch (error) {
    return { status: "FAILED", error: error.message };
  }
};

export default api;

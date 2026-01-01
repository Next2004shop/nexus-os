import axios from 'axios';

const client = axios.create({
    baseURL: 'http://localhost:8080',
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Verifies if the Nexus Core backend is alive.
 */
export const checkHealth = async () => {
    const response = await client.get('/health');
    return response.data;
};

/**
 * Sends data to Vertex AI for trade analysis.
 */
export const triggerAnalysis = async (symbol: string, data: any) => {
    const response = await client.post('/analyze', {
        symbol,
        data,
    });
    return response.data;
};

/**
 * Executes a trade via the backend body.
 */
export const executeTrade = async (symbol: string, side: 'buy' | 'sell', quantity: number) => {
    const response = await client.post('/trade', {
        symbol,
        side,
        quantity,
    });
    return response.data;
};

/**
 * Activates the emergency kill switch.
 */
export const triggerKillSwitch = async (symbol?: string) => {
    const response = await client.post('/kill', {
        symbol,
    });
    return response.data;
};

export default client;

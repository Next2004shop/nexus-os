import axios from 'axios';

// Bridge Configuration
// Bridge Configuration
const BRIDGE_URL = 'http://35.239.252.226:3000/api/bridge';
const AUTH = { username: 'admin', password: 'securepassword' };

export const aiService = {
    // Send message to Gemini via Vertex AI Bridge
    chat: async (message, history = []) => {
        try {
            const response = await axios.post(`${BRIDGE_URL}/ai/chat`, {
                message,
                history
            }, { auth: AUTH });

            return response.data.response;
        } catch (error) {
            console.error("AI Service Error:", error);
            return "System: Unable to reach Nexus Brain. Please check connection.";
        }
    },

    // Analyze Market Structure via Vertex AI
    analyzeMarket: async (symbol, timeframe = 'M15') => {
        try {
            const response = await axios.post(`${BRIDGE_URL}/ai/analyze`, {
                symbol,
                timeframe
            }, { auth: AUTH });

            return response.data;
        } catch (error) {
            console.error("AI Analysis Error:", error);
            return null;
        }
    }
};

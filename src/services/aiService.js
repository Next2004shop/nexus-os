import axios from 'axios';

// Bridge Configuration
const BRIDGE_URL = '/api/bridge';
const AUTH = { username: 'admin', password: 'securepassword' };

export const aiService = {
    // Send message to Gemini via Vertex AI Bridge
    sendMessage: async (message, history = []) => {
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
    }
};

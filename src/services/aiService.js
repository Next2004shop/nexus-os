import { GoogleGenerativeAI } from "@google/generative-ai";

// Initialize Gemini API
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);

export const aiService = {
    // Send message to Gemini
    sendMessage: async (message, history = []) => {
        try {
            if (!API_KEY) throw new Error("API Key missing");

            const model = genAI.getGenerativeModel({ model: "gemini-pro" });

            // Convert history to Gemini format
            const chat = model.startChat({
                history: history.map(msg => ({
                    role: msg.role === 'user' ? 'user' : 'model',
                    parts: [{ text: msg.text }]
                })),
                generationConfig: {
                    maxOutputTokens: 1000,
                },
            });

            const result = await chat.sendMessage(message);
            const response = await result.response;
            return response.text();

        } catch (error) {
            console.error("AI Service Error:", error);
            return "I'm having trouble connecting to the neural network right now. Please try again later.";
        }
    }
};

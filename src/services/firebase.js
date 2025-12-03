// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCwFJpSw4L5Xf5HYZH3aKuWbsGvgHeZESU",
    authDomain: "nexus-d7b05.firebaseapp.com",
    projectId: "nexus-d7b05",
    storageBucket: "nexus-d7b05.firebasestorage.app",
    messagingSenderId: "691725766314",
    appId: "1:691725766314:web:18e4af3ca4d86eeaa64ad3",
    measurementId: "G-YD5P4FZD3D",
    databaseURL: "https://nexus-d7b05-default-rtdb.firebaseio.com" // Added for RTDB
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const rtdb = getDatabase(app);

export const logTradeToCloud = async (tradeData) => {
    try {
        const { collection, addDoc } = await import("firebase/firestore");
        await addDoc(collection(db, "trades"), {
            ...tradeData,
            timestamp: new Date()
        });
        console.log("Trade logged to cloud:", tradeData.ticket);
    } catch (e) {
        console.error("Error logging trade to cloud:", e);
    }
};

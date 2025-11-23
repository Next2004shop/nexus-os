import { initializeApp } from 'firebase/app';
import { getFirestore, collection, addDoc, getDocs, query, orderBy, limit, onSnapshot } from 'firebase/firestore';

// TODO: Replace with your actual Firebase config
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "your-app.firebaseapp.com",
    projectId: "your-app",
    storageBucket: "your-app.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef"
};

// Initialize Firebase (wrapped in try-catch to prevent crash if config is missing)
let db;
try {
    const app = initializeApp(firebaseConfig);
    db = getFirestore(app);
} catch (error) {
    console.warn("Firebase not configured. Cloud features will use mock data.");
}

export const logTradeToCloud = async (trade) => {
    if (!db) return;
    try {
        await addDoc(collection(db, "trades"), {
            ...trade,
            timestamp: new Date()
        });
    } catch (e) {
        console.error("Error logging trade to cloud:", e);
    }
};

export const subscribeToCloudTrades = (callback) => {
    if (!db) return () => { };
    const q = query(collection(db, "trades"), orderBy("timestamp", "desc"), limit(50));
    return onSnapshot(q, (snapshot) => {
        const trades = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        callback(trades);
    });
};

export { db };

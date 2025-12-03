import { rtdb } from './firebase';
import { ref, set, get, update, onValue, push, serverTimestamp, runTransaction } from 'firebase/database';

export const userRepository = {
    // Initialize User Profile if not exists (RTDB)
    initializeUser: async (user) => {
        if (!user) return;
        const userRef = ref(rtdb, `users/${user.uid}`);
        const snapshot = await get(userRef);

        if (!snapshot.exists()) {
            await set(userRef, {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName,
                createdAt: serverTimestamp(),
                wallet: {
                    usdt: 0, // Start with 0
                    btc: 0,
                    eth: 0,
                    sol: 0
                },
                bankAccounts: [],
                investments: []
            });
        }
    },

    // Get User Wallet (One-time fetch)
    getWallet: async (userId) => {
        const walletRef = ref(rtdb, `users/${userId}/wallet`);
        const snapshot = await get(walletRef);
        if (snapshot.exists()) {
            return snapshot.val();
        }
        return null;
    },

    // Subscribe to Wallet Updates (Real-time)
    subscribeToWallet: (userId, callback) => {
        const walletRef = ref(rtdb, `users/${userId}/wallet`);
        const unsubscribe = onValue(walletRef, (snapshot) => {
            if (snapshot.exists()) {
                callback(snapshot.val());
            } else {
                callback(null);
            }
        });
        return unsubscribe; // Return unsubscribe function
    },

    // Execute Trade (Atomic Transaction)
    executeTrade: async (userId, type, asset, amount, price) => {
        const userWalletRef = ref(rtdb, `users/${userId}/wallet`);
        const totalCost = amount * price;
        const assetKey = asset.toLowerCase();

        try {
            await runTransaction(userWalletRef, (wallet) => {
                if (!wallet) return wallet; // Abort if null

                if (type === 'buy') {
                    if ((wallet.usdt || 0) < totalCost) throw new Error("Insufficient USDT Balance");
                    wallet.usdt = (wallet.usdt || 0) - totalCost;
                    wallet[assetKey] = (wallet[assetKey] || 0) + amount;
                } else {
                    if ((wallet[assetKey] || 0) < amount) throw new Error(`Insufficient ${asset} Balance`);
                    wallet.usdt = (wallet.usdt || 0) + totalCost;
                    wallet[assetKey] = (wallet[assetKey] || 0) - amount;
                }
                return wallet;
            });

            // Log Trade
            const tradesRef = ref(rtdb, `trades/${userId}`);
            const newTradeRef = push(tradesRef);
            await set(newTradeRef, {
                type,
                asset,
                amount,
                price,
                total: totalCost,
                timestamp: serverTimestamp()
            });

        } catch (error) {
            console.error("Trade Transaction Failed:", error);
            throw error; // Re-throw for UI handling
        }
    },

    // Place Limit Order
    placeLimitOrder: async (userId, type, asset, amount, price) => {
        const ordersRef = ref(rtdb, `limit_orders/${userId}`);
        const newOrderRef = push(ordersRef);
        await set(newOrderRef, {
            type,
            asset,
            amount,
            price,
            status: 'open',
            timestamp: serverTimestamp()
        });
    },

    // Add Offshore Bank Account
    addBankAccount: async (userId, accountDetails) => {
        const accountsRef = ref(rtdb, `users/${userId}/bankAccounts`);
        // RTDB arrays are tricky, better to use push for list
        // But to keep structure similar to previous, we can read-modify-write or use push
        // Let's use push to add a new entry
        const newAccountRef = push(accountsRef);
        await set(newAccountRef, {
            ...accountDetails,
            id: Date.now(),
            balance: 0
        });
    }
};

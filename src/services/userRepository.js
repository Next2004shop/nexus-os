import { db } from './firebase';
import { doc, getDoc, setDoc, updateDoc, arrayUnion, increment, collection, addDoc, serverTimestamp } from 'firebase/firestore';

export const userRepository = {
    // Initialize User Profile if not exists
    initializeUser: async (user) => {
        if (!user) return;
        const userRef = doc(db, 'users', user.uid);
        const userSnap = await getDoc(userRef);

        if (!userSnap.exists()) {
            await setDoc(userRef, {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName,
                createdAt: serverTimestamp(),
                wallet: {
                    usdt: 0, // Real Mode: Start with 0
                    btc: 0,
                    eth: 0,
                    sol: 0
                },
                bankAccounts: [],
                investments: []
            });
        }
    },

    // Get User Wallet
    getWallet: async (userId) => {
        const userRef = doc(db, 'users', userId);
        const userSnap = await getDoc(userRef);
        if (userSnap.exists()) {
            return userSnap.data().wallet;
        }
        return null;
    },

    // Execute Trade
    executeTrade: async (userId, type, asset, amount, price) => {
        const userRef = doc(db, 'users', userId);
        const totalCost = amount * price;
        const assetKey = `wallet.${asset.toLowerCase()}`;

        // Simple Validation
        const userSnap = await getDoc(userRef);
        const wallet = userSnap.data().wallet;

        if (type === 'buy') {
            if (wallet.usdt < totalCost) throw new Error("Insufficient USDT Balance");
            await updateDoc(userRef, {
                "wallet.usdt": increment(-totalCost),
                [assetKey]: increment(amount)
            });
        } else {
            if ((wallet[asset.toLowerCase()] || 0) < amount) throw new Error(`Insufficient ${asset} Balance`);
            await updateDoc(userRef, {
                "wallet.usdt": increment(totalCost),
                [assetKey]: increment(-amount)
            });
        }

        // Log Trade
        await addDoc(collection(db, 'trades'), {
            userId,
            type,
            asset,
            amount,
            price,
            total: totalCost,
            timestamp: serverTimestamp()
        });
    },

    // Place Limit Order
    placeLimitOrder: async (userId, type, asset, amount, price) => {
        await addDoc(collection(db, 'limit_orders'), {
            userId,
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
        const userRef = doc(db, 'users', userId);
        await updateDoc(userRef, {
            bankAccounts: arrayUnion({
                ...accountDetails,
                id: Date.now(),
                balance: 0 // Initial balance
            })
        });
    }
};

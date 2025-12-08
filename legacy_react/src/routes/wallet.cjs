const express = require('express');
const router = express.Router();

// MOCK DATABASE (In-Memory)
let transactions = [];
let balances = {
    usd: 0,
    crypto: 0
};

// HELPER: Generate Transaction ID
const generateTxId = () => {
    return 'TX-' + Math.random().toString(36).substr(2, 9).toUpperCase();
};

// HELPER: Generate Mock Crypto Address
const generateCryptoAddress = (network) => {
    const prefixes = {
        'TRC20': 'T',
        'ERC20': '0x',
        'BEP20': '0x',
        'BTC': '1'
    };
    return (prefixes[network] || '0x') + Math.random().toString(16).substr(2, 32).toUpperCase();
};

// API: DEPOSIT FUNDS
router.post('/deposit', (req, res) => {
    const { amount, method, broker, details } = req.body;

    if (!amount || amount <= 0) {
        return res.status(400).json({ error: "Invalid amount" });
    }

    const txId = generateTxId();
    let responseData = {
        txId,
        status: 'PENDING',
        message: 'Transaction Initiated'
    };

    // LOGIC PER METHOD
    switch (method) {
        case 'mpesa':
            if (!details.phone) return res.status(400).json({ error: "Phone number required" });
            // Simulate STK Push
            responseData.message = `STK Push sent to ${details.phone}. Please enter PIN.`;
            responseData.providerRef = `MPS${Date.now()}`;
            break;

        case 'binance':
        case 'crypto':
            if (!details.network) return res.status(400).json({ error: "Network required" });
            responseData.address = generateCryptoAddress(details.network);
            responseData.message = `Send ${amount} to the generated address.`;
            responseData.qr = `mock-qr-${responseData.address}`;
            break;

        case 'bank':
            responseData.status = 'AWAITING_WIRE';
            responseData.instructions = {
                bankName: "Nexus Global Bank",
                accountName: `Nexus Fund - ${broker || 'Main'}`,
                accountNumber: "882939102",
                swift: "NEXUSUS33",
                reference: txId
            };
            responseData.message = "Please complete the wire transfer using these details.";
            break;

        case 'card':
            responseData.status = 'COMPLETED'; // Instant
            responseData.message = "Card payment processed successfully.";
            break;

        default:
            return res.status(400).json({ error: "Unsupported method" });
    }

    // Record Transaction
    transactions.unshift({
        id: txId,
        type: 'DEPOSIT',
        amount,
        method,
        broker,
        status: responseData.status,
        timestamp: new Date().toISOString()
    });

    // Simulate async completion for MPESA/CRYPTO after 5s (optional, but good for UI)
    // For now, we return immediate instructions.

    res.json(responseData);
});

// API: WITHDRAW FUNDS
router.post('/withdraw', (req, res) => {
    const { amount, method, destination } = req.body;
    const txId = generateTxId();

    transactions.unshift({
        id: txId,
        type: 'WITHDRAWAL',
        amount,
        method,
        destination,
        status: 'PROCESSING',
        timestamp: new Date().toISOString()
    });

    res.json({
        txId,
        status: 'PROCESSING',
        message: 'Withdrawal request received. Processing time: 10-30 mins.'
    });
});

// API: GET HISTORY
router.get('/history', (req, res) => {
    res.json(transactions);
});

module.exports = router;

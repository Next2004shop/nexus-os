export const brokerService = {
    getBrokers: () => [
        {
            id: 'fxpro',
            name: 'FxPro',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/e/e8/FxPro_Group_Logo.png', // Placeholder or local asset
            color: '#EB1C24',
            minDeposit: 100,
            leverage: '1:500',
            methods: ['mpesa', 'card', 'bank', 'crypto', 'paypal']
        },
        {
            id: 'exness',
            name: 'Exness',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Exness_logo.svg/2560px-Exness_logo.svg.png',
            color: '#FFD700',
            minDeposit: 10,
            leverage: '1:Unlimited',
            methods: ['mpesa', 'binance', 'bank', 'skrill']
        },
        {
            id: 'xm',
            name: 'XM Global',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/XM_Logo.svg/1200px-XM_Logo.svg.png',
            color: '#000000',
            minDeposit: 5,
            leverage: '1:1000',
            methods: ['mpesa', 'card', 'bank']
        },
        {
            id: 'binance',
            name: 'Binance Exchange',
            logo: 'https://upload.wikimedia.org/wikipedia/commons/e/e8/Binance_Logo.svg',
            color: '#F3BA2F',
            minDeposit: 10,
            leverage: '1:125',
            methods: ['p2p', 'crypto', 'bank']
        }
    ],

    getPaymentDetails: (method) => {
        switch (method) {
            case 'mpesa':
                return {
                    title: 'M-Pesa Express',
                    icon: 'Smartphone',
                    color: '#4CAF50',
                    fields: [
                        { name: 'phone', label: 'M-Pesa Phone Number', placeholder: '2547...' },
                        { name: 'amount', label: 'Amount (KES)', placeholder: 'Min 100' }
                    ],
                    action: 'PUSH STK MENU'
                };
            case 'paypal':
                return {
                    title: 'PayPal',
                    icon: 'CreditCard',
                    color: '#003087',
                    fields: [
                        { name: 'email', label: 'PayPal Email', placeholder: 'you@example.com' },
                        { name: 'amount', label: 'Amount (USD)', placeholder: 'Min 10' }
                    ],
                    action: 'PROCEED TO PAYPAL'
                };
            case 'binance':
            case 'crypto': // Alias for crypto payments
                return {
                    title: 'Binance Pay / Crypto',
                    icon: 'Bitcoin',
                    color: '#F3BA2F',
                    fields: [
                        { name: 'network', label: 'Network', type: 'select', options: ['TRC20', 'ERC20', 'BEP20'] },
                        { name: 'amount', label: 'Amount (USDT)', placeholder: 'Min 10' }
                    ],
                    action: 'GENERATE ADDRESS'
                };
            case 'p2p':
                return {
                    title: 'P2P Trading',
                    icon: 'Activity',
                    color: '#F3BA2F',
                    fields: [
                        { name: 'amount', label: 'Amount (USDT)', placeholder: 'Min 10' }
                    ],
                    action: 'FIND P2P ORDERS'
                };
            case 'bank':
                return {
                    title: 'Bank Wire Transfer',
                    icon: 'Landmark',
                    color: '#9E9E9E',
                    fields: [
                        { name: 'bank', label: 'Select Bank', type: 'select', options: ['Equity Bank', 'KCB', 'Co-op Bank', 'Standard Chartered'] },
                        { name: 'account', label: 'Account Number', placeholder: 'Enter Account No' }
                    ],
                    action: 'GET WIRE INSTRUCTIONS'
                };
            default:
                return null;
        }
    }
};

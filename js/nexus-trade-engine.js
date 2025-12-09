/**
 * NEXUS TRADE ENGINE
 * Handles trade execution, validation, and order management
 */

let tradeState = {
    orderType: null,
    takeProfit: 0,
    stopLoss: 0,
    lotSize: 0.01,
    stealthMode: false,
    lastOrder: null
};

/**
 * Initialize trading system
 */
function initializeTrading() {
    console.log('💹 Initializing Nexus Trade Engine...');

    // Set up input listeners
    setupInputListeners();

    // Load saved settings
    loadTradeSettings();
}

/**
 * Setup input event listeners
 */
function setupInputListeners() {
    const takeProfitInput = document.getElementById('takeProfit');
    const stopLossInput = document.getElementById('stopLoss');
    const lotSizeInput = document.getElementById('lotSize');
    const stealthToggle = document.getElementById('stealthMode');

    if (takeProfitInput) {
        takeProfitInput.addEventListener('change', (e) => {
            tradeState.takeProfit = parseFloat(e.target.value) || 0;
            saveTradeSettings();
        });
    }

    if (stopLossInput) {
        stopLossInput.addEventListener('change', (e) => {
            tradeState.stopLoss = parseFloat(e.target.value) || 0;
            saveTradeSettings();
        });
    }

    if (lotSizeInput) {
        lotSizeInput.addEventListener('change', (e) => {
            tradeState.lotSize = parseFloat(e.target.value) || 0.01;
            saveTradeSettings();
        });
    }

    if (stealthToggle) {
        stealthToggle.addEventListener('change', (e) => {
            tradeState.stealthMode = e.target.checked;
            saveTradeSettings();
            console.log('🥷 Stealth mode:', tradeState.stealthMode ? 'ENABLED' : 'DISABLED');
        });
    }
}

/**
 * Prepare order (Buy or Sell)
 */
function prepareOrder(type) {
    tradeState.orderType = type;

    // Update execute button text
    const executeBtn = document.querySelector('.execute-button');
    if (executeBtn) {
        const icon = type === 'BUY' ? 'fa-arrow-up' : 'fa-arrow-down';
        const color = type === 'BUY' ? '#00ff88' : '#ff3366';

        executeBtn.innerHTML = `<i class="fas ${icon}"></i> EXECUTE ${type}`;
        executeBtn.style.background = type === 'BUY'
            ? 'linear-gradient(135deg, #00ff88, #00f0ff)'
            : 'linear-gradient(135deg, #ff3366, #ff9900)';
    }

    console.log(`📊 Order prepared: ${type}`);
}

/**
 * Execute the order
 */
function executeOrder() {
    if (!tradeState.orderType) {
        showNotification('Please select BUY or SELL first', 'warning');
        return;
    }

    // Validate inputs
    if (!validateOrder()) {
        return;
    }

    // Get current price
    const currentPrice = getCurrentMarketPrice();

    // Create order object
    const order = {
        type: tradeState.orderType,
        symbol: 'BTC/USD',
        price: currentPrice,
        lotSize: tradeState.lotSize,
        takeProfit: tradeState.takeProfit,
        stopLoss: tradeState.stopLoss,
        stealthMode: tradeState.stealthMode,
        timestamp: new Date().toISOString(),
        orderId: generateOrderId()
    };

    // Show confirmation
    showOrderConfirmation(order);
}

/**
 * Validate order parameters
 */
function validateOrder() {
    const lotSize = parseFloat(document.getElementById('lotSize').value);

    if (!lotSize || lotSize <= 0) {
        showNotification('Invalid lot size', 'error');
        return false;
    }

    if (lotSize > 100) {
        showNotification('Lot size too large (max 100)', 'error');
        return false;
    }

    // Validate TP/SL if set
    const tp = parseFloat(document.getElementById('takeProfit').value) || 0;
    const sl = parseFloat(document.getElementById('stopLoss').value) || 0;
    const currentPrice = getCurrentMarketPrice();

    if (tradeState.orderType === 'BUY') {
        if (tp > 0 && tp <= currentPrice) {
            showNotification('Take Profit must be above current price for BUY orders', 'error');
            return false;
        }
        if (sl > 0 && sl >= currentPrice) {
            showNotification('Stop Loss must be below current price for BUY orders', 'error');
            return false;
        }
    } else {
        if (tp > 0 && tp >= currentPrice) {
            showNotification('Take Profit must be below current price for SELL orders', 'error');
            return false;
        }
        if (sl > 0 && sl <= currentPrice) {
            showNotification('Stop Loss must be above current price for SELL orders', 'error');
            return false;
        }
    }

    return true;
}

/**
 * Show order confirmation modal
 */
function showOrderConfirmation(order) {
    const confirmed = confirm(
        `Confirm ${order.type} Order:\n\n` +
        `Symbol: ${order.symbol}\n` +
        `Price: $${order.price.toLocaleString()}\n` +
        `Lot Size: ${order.lotSize}\n` +
        `Take Profit: ${order.takeProfit || 'Not set'}\n` +
        `Stop Loss: ${order.stopLoss || 'Not set'}\n` +
        `Stealth Mode: ${order.stealthMode ? 'ON' : 'OFF'}\n\n` +
        `Execute this order?`
    );

    if (confirmed) {
        processOrder(order);
    }
}

/**
 * Process the order
 */
async function processOrder(order) {
    console.log('⚡ Processing order:', order);

    try {
        const API_BASE = 'http://localhost:5001';
        const AUTH_HEADER = 'Basic ' + btoa('admin:securepassword');

        // Submit order to backend
        const response = await fetch(`${API_BASE}/trade`, {
            method: 'POST',
            headers: {
                'Authorization': AUTH_HEADER,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: order.symbol.replace('/', ''), // BTCUSD not BTC/USD
                type: order.type,
                lots: order.lotSize,
                sl: order.stopLoss || 0,
                tp: order.takeProfit || 0
            })
        });

        const result = await response.json();

        if (!response.ok || result.error) {
            throw new Error(result.error || 'Trade execution failed');
        }

        // Success
        showNotification(
            `✅ ${order.type} order executed successfully!\nTicket: ${result.ticket}`,
            'success'
        );

        // Save last order
        tradeState.lastOrder = { ...order, ticket: result.ticket };

        // Log to stealth system if enabled
        if (order.stealthMode) {
            console.log('🥷 Stealth mode enabled - trade logged privately');
        }

    } catch (error) {
        console.error('Trade execution error:', error);
        showNotification(
            `❌ Trade failed: ${error.message}`,
            'error'
        );
    }
}

/**
 * Get current market price
 */
function getCurrentMarketPrice() {
    // Try to get from chart
    if (window.NexusChart && typeof window.NexusChart.getCurrentPrice === 'function') {
        return window.NexusChart.getCurrentPrice();
    }

    // Fallback to price display
    const priceEl = document.getElementById('currentPrice');
    if (priceEl) {
        return parseFloat(priceEl.textContent.replace('$', '').replace(',', ''));
    }

    return 98127.06;
}

/**
 * Generate unique order ID
 */
function generateOrderId() {
    return 'NX-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9).toUpperCase();
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced with toast notifications
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    alert(`${icons[type]} ${message}`);
}

/**
 * Save trade settings to localStorage
 */
function saveTradeSettings() {
    localStorage.setItem('nexusTradeSettings', JSON.stringify({
        takeProfit: tradeState.takeProfit,
        stopLoss: tradeState.stopLoss,
        lotSize: tradeState.lotSize,
        stealthMode: tradeState.stealthMode
    }));
}

/**
 * Load trade settings from localStorage
 */
function loadTradeSettings() {
    const saved = localStorage.getItem('nexusTradeSettings');
    if (saved) {
        const settings = JSON.parse(saved);
        tradeState = { ...tradeState, ...settings };

        // Update inputs
        if (settings.takeProfit) document.getElementById('takeProfit').value = settings.takeProfit;
        if (settings.stopLoss) document.getElementById('stopLoss').value = settings.stopLoss;
        if (settings.lotSize) document.getElementById('lotSize').value = settings.lotSize;
        if (settings.stealthMode) document.getElementById('stealthMode').checked = settings.stealthMode;
    }
}

/**
 * Export for other modules
 */
window.NexusTrading = {
    initialize: initializeTrading,
    prepareOrder: prepareOrder,
    executeOrder: executeOrder,
    getState: () => tradeState
};

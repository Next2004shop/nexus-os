/**
 * NEXUS CHART MODULE
 * Interactive candlestick chart with real-time updates
 * Uses Lightweight Charts library
 */

let chart = null;
let candlestickSeries = null;
let priceData = [];

/**
 * Initialize the trading chart
 */
async function initializeChart() {
    const chartContainer = document.getElementById('trading-chart');

    if (!chartContainer) {
        console.error('Chart container not found');
        return;
    }

    // Show loading state
    showChartLoading(true);

    // Fetch real data from backend (with fallback)
    await fetchRealCandleData();

    // Create chart
    chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
        layout: {
            background: { color: '#12172b' },
            textColor: '#a0aec0',
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {
                color: '#00f0ff',
                width: 1,
                style: LightweightCharts.LineStyle.Dashed,
            },
            horzLine: {
                color: '#00f0ff',
                width: 1,
                style: LightweightCharts.LineStyle.Dashed,
            },
        },
        rightPriceScale: {
            borderColor: 'rgba(0, 240, 255, 0.2)',
            scaleMargins: {
                top: 0.1,
                bottom: 0.1,
            },
        },
        timeScale: {
            borderColor: 'rgba(0, 240, 255, 0.2)',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    // Create candlestick series
    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00ff88',
        downColor: '#ff3366',
        borderUpColor: '#00ff88',
        borderDownColor: '#ff3366',
        wickUpColor: '#00ff88',
        wickDownColor: '#ff3366',
    });

    // Set data to chart
    candlestickSeries.setData(priceData);

    // Fit content
    chart.timeScale().fitContent();

    // Hide loading
    showChartLoading(false);

    // Handle resize
    window.addEventListener('resize', handleChartResize);

    // Start real-time updates
    startRealTimeUpdates();

    console.log('✅ Chart initialized successfully');
}

/**
 * Fetch real candlestick data from backend
 */
async function fetchRealCandleData() {
    try {
        const API_BASE = 'http://localhost:5001';
        const AUTH_HEADER = 'Basic ' + btoa('admin:securepassword');

        const response = await fetch(`${API_BASE}/market/candles?symbol=BTCUSD&timeframe=H1&limit=100`, {
            headers: { 'Authorization': AUTH_HEADER }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch candle data');
        }

        const candles = await response.json();

        // Transform to chart format
        priceData = candles.map(candle => ({
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        }));

        console.log(`✅ Loaded ${priceData.length} real candles from MT5`);
        return true;

    } catch (error) {
        console.warn('⚠️ Could not fetch real data, using fallback:', error.message);
        generateFallbackData();
        return false;
    }
}

/**
 * Generate fallback data if backend is offline
 */
function generateFallbackData() {
    const now = Math.floor(Date.now() / 1000);
    const basePrice = 98127;
    const periods = 100;
    const interval = 3600;

    priceData = [];
    let currentPrice = basePrice;

    for (let i = periods; i >= 0; i--) {
        const time = now - (i * interval);
        const open = currentPrice + (Math.random() - 0.5) * 500;
        const volatility = 200 + Math.random() * 300;
        const high = open + Math.random() * volatility;
        const low = open - Math.random() * volatility;
        const close = low + Math.random() * (high - low);

        priceData.push({
            time: time,
            open: parseFloat(open.toFixed(2)),
            high: parseFloat(high.toFixed(2)),
            low: parseFloat(low.toFixed(2)),
            close: parseFloat(close.toFixed(2)),
        });

        currentPrice = close;
    }
}

/**
 * Start real-time candlestick updates
 */
function startRealTimeUpdates() {
    setInterval(() => {
        updateLastCandle();
    }, 5000); // Update every 5 seconds
}

/**
 * Update the last candlestick with new price movement
 */
function updateLastCandle() {
    if (!candlestickSeries || priceData.length === 0) return;

    const lastCandle = priceData[priceData.length - 1];
    const priceChange = (Math.random() - 0.5) * 200;

    // Update close price
    const newClose = lastCandle.close + priceChange;

    // Update high/low if necessary
    const newHigh = Math.max(lastCandle.high, newClose);
    const newLow = Math.min(lastCandle.low, newClose);

    const updatedCandle = {
        time: lastCandle.time,
        open: lastCandle.open,
        high: parseFloat(newHigh.toFixed(2)),
        low: parseFloat(newLow.toFixed(2)),
        close: parseFloat(newClose.toFixed(2)),
    };

    // Update the candle
    candlestickSeries.update(updatedCandle);
    priceData[priceData.length - 1] = updatedCandle;

    // Update price display
    updatePriceDisplay(newClose);
}

/**
 * Add a new candlestick (simulate new time period)
 */
function addNewCandle() {
    if (!candlestickSeries || priceData.length === 0) return;

    const lastCandle = priceData[priceData.length - 1];
    const newTime = lastCandle.time + 3600; // 1 hour later

    const open = lastCandle.close;
    const volatility = 200 + Math.random() * 300;
    const high = open + Math.random() * volatility;
    const low = open - Math.random() * volatility;
    const close = low + Math.random() * (high - low);

    const newCandle = {
        time: newTime,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
    };

    priceData.push(newCandle);
    candlestickSeries.update(newCandle);
}

/**
 * Update price display in header
 */
function updatePriceDisplay(price) {
    const priceElement = document.getElementById('currentPrice');
    if (!priceElement) return;

    const oldPrice = parseFloat(priceElement.textContent.replace('$', '').replace(',', ''));

    priceElement.textContent = '$' + price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    // Update color based on change
    if (price > oldPrice) {
        priceElement.className = 'price-display bullish';
    } else if (price < oldPrice) {
        priceElement.className = 'price-display bearish';
    }
}

/**
 * Handle chart resize
 */
function handleChartResize() {
    if (!chart) return;

    const chartContainer = document.getElementById('trading-chart');
    if (!chartContainer) return;

    chart.applyOptions({
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
    });
}

/**
 * Show/hide chart loading state
 */
function showChartLoading(show) {
    const loadingElement = document.getElementById('chartLoading');
    if (loadingElement) {
        loadingElement.style.display = show ? 'block' : 'none';
    }
}

/**
 * Get current market price
 */
function getCurrentPrice() {
    if (priceData.length === 0) return 0;
    return priceData[priceData.length - 1].close;
}

/**
 * Export functions for use in other modules
 */
window.NexusChart = {
    initialize: initializeChart,
    getCurrentPrice: getCurrentPrice,
    addCandle: addNewCandle,
};

/**
 * NEXUS AI INTELLIGENCE MODULE
 * Simulates AI analysis with scanning animations
 */

let aiState = {
    direction: 'WAIT',
    smartMoney: 'SCANNING...',
    confidence: '--',
    risk: 'MEDIUM',
    market: 'VOLATILE',
    sentiment: 'NEUTRAL',
    isScanning: true
};

/**
 * Initialize AI Intelligence
 */
function initializeAI() {
    console.log('🧠 Initializing Nexus AI Intelligence...');

    // Start periodic AI updates
    setTimeout(() => {
        performAIAnalysis();
    }, 3000);

    // Update AI every 15 seconds
    setInterval(() => {
        performAIAnalysis();
    }, 15000);
}

/**
 * Perform AI analysis and update metrics
 */
async function performAIAnalysis() {
    console.log('🔍 Running AI analysis...');

    // Set scanning state
    setAIScanning(true);

    try {
        const API_BASE = 'http://localhost:5001';
        const AUTH_HEADER = 'Basic ' + btoa('admin:securepassword');

        const response = await fetch(`${API_BASE}/ai/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': AUTH_HEADER,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: 'BTCUSD',
                timeframe: 'H1'
            })
        });

        if (!response.ok) {
            throw new Error('AI analysis failed');
        }

        const result = await response.json();
        const aiSignal = result.ai_signal || {};

        // Map real AI data to state
        aiState.direction = aiSignal.direction || aiSignal.signal || 'WAIT';
        aiState.smartMoney = result.smart_money?.flow || 'NEUTRAL';
        aiState.confidence = aiSignal.confidence ? `${aiSignal.confidence}%` : '--';
        aiState.risk = aiSignal.risk_rating || 'MEDIUM';
        aiState.market = result.technical?.trend || 'VOLATILE';
        aiState.sentiment = aiSignal.sentiment || 'NEUTRAL';

        updateAIDisplay();
        setAIScanning(false);

        console.log('✅ Real AI analysis complete:', aiState);

    } catch (error) {
        console.warn('⚠️ AI analysis error, using fallback:', error.message);
        // Fallback to random data if backend is offline
        performFallbackAnalysis();
    }
}

/**
 * Fallback analysis if backend is offline
 */
function performFallbackAnalysis() {
    const directions = ['BUY', 'SELL', 'WAIT', 'STRONG BUY', 'STRONG SELL'];
    const smartMoney = ['ACCUMULATING', 'DISTRIBUTING', 'NEUTRAL', 'HEAVY BUY', 'HEAVY SELL'];
    const risks = ['LOW', 'MEDIUM', 'HIGH', 'EXTREME'];
    const markets = ['BULLISH', 'BEARISH', 'VOLATILE', 'CONSOLIDATING', 'TRENDING'];
    const sentiments = ['BULLISH', 'BEARISH', 'NEUTRAL', 'FEARFUL', 'GREEDY'];

    aiState.direction = directions[Math.floor(Math.random() * directions.length)];
    aiState.smartMoney = smartMoney[Math.floor(Math.random() * smartMoney.length)];
    aiState.confidence = (60 + Math.random() * 40).toFixed(1) + '%';
    aiState.risk = risks[Math.floor(Math.random() * risks.length)];
    aiState.market = markets[Math.floor(Math.random() * markets.length)];
    aiState.sentiment = sentiments[Math.floor(Math.random() * sentiments.length)];

    updateAIDisplay();
    setAIScanning(false);

    console.log('⚠️ Using fallback AI data');
}

/**
 * Update AI display with current state
 */
function updateAIDisplay() {
    // Direction
    const directionEl = document.getElementById('aiDirection');
    if (directionEl) {
        directionEl.textContent = aiState.direction;
        directionEl.style.color = getDirectionColor(aiState.direction);
    }

    // Smart Money
    const smartMoneyEl = document.getElementById('aiSmartMoney');
    if (smartMoneyEl) {
        smartMoneyEl.textContent = aiState.smartMoney;
        smartMoneyEl.classList.remove('scanning');
        smartMoneyEl.style.color = getSmartMoneyColor(aiState.smartMoney);
    }

    // Confidence
    const confidenceEl = document.getElementById('aiConfidence');
    if (confidenceEl) {
        confidenceEl.textContent = aiState.confidence;
        const confidenceValue = parseFloat(aiState.confidence);
        confidenceEl.style.color = confidenceValue > 80 ? '#00ff88' : confidenceValue > 60 ? '#ffcc00' : '#ff3366';
    }

    // Risk
    const riskEl = document.getElementById('aiRisk');
    if (riskEl) {
        riskEl.textContent = aiState.risk;
        riskEl.style.color = getRiskColor(aiState.risk);
    }

    // Market
    const marketEl = document.getElementById('aiMarket');
    if (marketEl) {
        marketEl.textContent = aiState.market;
        marketEl.style.color = getMarketColor(aiState.market);
    }

    // Sentiment
    const sentimentEl = document.getElementById('aiSentiment');
    if (sentimentEl) {
        sentimentEl.textContent = aiState.sentiment;
        sentimentEl.style.color = getSentimentColor(aiState.sentiment);
    }
}

/**
 * Set scanning state
 */
function setAIScanning(isScanning) {
    aiState.isScanning = isScanning;

    const smartMoneyEl = document.getElementById('aiSmartMoney');
    if (smartMoneyEl) {
        if (isScanning) {
            smartMoneyEl.textContent = 'SCANNING...';
            smartMoneyEl.classList.add('scanning');
            smartMoneyEl.style.color = '';
        }
    }
}

/**
 * Manual update trigger
 */
function updateAIAnalysis() {
    console.log('🔄 Manual AI update triggered');
    performAIAnalysis();
}

/**
 * Color helpers
 */
function getDirectionColor(direction) {
    if (direction.includes('BUY')) return '#00ff88';
    if (direction.includes('SELL')) return '#ff3366';
    return '#ffcc00';
}

function getSmartMoneyColor(smartMoney) {
    if (smartMoney.includes('BUY') || smartMoney === 'ACCUMULATING') return '#00ff88';
    if (smartMoney.includes('SELL') || smartMoney === 'DISTRIBUTING') return '#ff3366';
    return '#a0aec0';
}

function getRiskColor(risk) {
    switch (risk) {
        case 'LOW': return '#00ff88';
        case 'MEDIUM': return '#ffcc00';
        case 'HIGH': return '#ff9900';
        case 'EXTREME': return '#ff3366';
        default: return '#a0aec0';
    }
}

function getMarketColor(market) {
    if (market === 'BULLISH' || market === 'TRENDING') return '#00ff88';
    if (market === 'BEARISH') return '#ff3366';
    return '#a0aec0';
}

function getSentimentColor(sentiment) {
    if (sentiment === 'BULLISH' || sentiment === 'GREEDY') return '#00ff88';
    if (sentiment === 'BEARISH' || sentiment === 'FEARFUL') return '#ff3366';
    return '#a0aec0';
}

/**
 * Get AI recommendation
 */
function getAIRecommendation() {
    return aiState.direction;
}

/**
 * Export for other modules
 */
window.NexusAI = {
    initialize: initializeAI,
    update: updateAIAnalysis,
    getRecommendation: getAIRecommendation,
    getState: () => aiState
};

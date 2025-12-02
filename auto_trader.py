import time
import requests
import logging
from nexus_brain import brain

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutoPilot")

BRIDGE_URL = "http://127.0.0.1:5000"
AUTH = ("admin", "securepassword")
# GROWTH PHASE: Focus ONLY on Gold (XAUUSD) to build capital quickly.
# Once balance > $100, we can add EURUSD and BTCUSD.
SYMBOLS = ["XAUUSD"]

def get_market_price(symbol):
    # In a real scenario, this would fetch live price from MT5 via Bridge
    # For now, we simulate or fetch if endpoint exists
    return {"price": 1.0500, "trend": "Bullish", "rsi": 55} 

def run_autopilot():
    logger.info("🚀 NEXUS AUTO-PILOT: ENGAGED (AGGRESSIVE SCALPING MODE)")
    logger.info(f"📡 WATCHING SYMBOLS: {SYMBOLS}")
    
    # Track open trades: { ticket: { start_time: timestamp, symbol: symbol, type: BUY/SELL, scaled: bool } }
    active_trades = {} 
    MAX_PYRAMID_LAYERS = 12 # Increased to 12 as requested
    TIME_EXIT_SECONDS = 20 * 60 
    MOMENTUM_THRESHOLD = 0.50 # If profit > $0.50 in < 5 mins, SCALE IN.
    session_profit = 0.0 # Track "Good Day" status

    while True:
        try:
            # 0. Sync with Bridge (Get real open positions)
            try:
                res = requests.get(f"{BRIDGE_URL}/positions", auth=AUTH)
                if res.status_code == 200:
                    real_positions = res.json()
                    current_tickets = [p['ticket'] for p in real_positions]
                    
                    # Remove closed trades from our tracker
                    for ticket in list(active_trades.keys()):
                        if ticket not in current_tickets:
                            # Trade closed externally or by us. 
                            # Ideally we'd fetch history to update session_profit, but for now we assume neutral or check history later.
                            del active_trades[ticket]
                    
                    # Add any manual trades to tracker
                    for p in real_positions:
                        if p['ticket'] not in active_trades:
                            active_trades[p['ticket']] = {
                                "start_time": time.time(), 
                                "symbol": p['symbol'],
                                "type": "BUY" if p['volume'] > 0 else "SELL",
                                "scaled": False # Track if we already scaled this one
                            }
            except Exception as e:
                logger.error(f"⚠️ SYNC ERROR: {e}")

            # 1. Smart Exit & Momentum Logic
            now = time.time()
            for ticket, trade in list(active_trades.items()):
                duration = now - trade['start_time']
                
                # Get current profit
                current_profit = 0.0
                for p in real_positions:
                    if p['ticket'] == ticket:
                        current_profit = p['profit']
                        break
                
                # --- MOMENTUM SCALING (The "Good Day" Logic) ---
                # If trade is young (< 5 mins) AND profitable (> $0.50) AND not yet scaled:
                if duration < 300 and current_profit > MOMENTUM_THRESHOLD and not trade.get('scaled'):
                    logger.info(f"🚀 MOMENTUM DETECTED (Profit: ${current_profit} in {duration:.0f}s). SCALING IN!")
                    
                    # Ask AI for Lot Size
                    # We pass the current number of layers so it knows to increase size
                    current_layers = len([t for t in active_trades.values() if t['symbol'] == trade['symbol']])
                    scale_lots = brain.decide_scaling_lots(trade['symbol'], current_profit, current_layers)
                    logger.info(f"🤖 AI DECIDED SCALE LOTS (Layer {current_layers+1}): {scale_lots}")
                    
                    # Execute Scale-In Trade
                    payload = {
                        "symbol": trade['symbol'],
                        "type": trade['type'],
                        "lots": scale_lots,
                        "sl": 0, "tp": 0
                    }
                    try:
                        res = requests.post(f"{BRIDGE_URL}/trade", json=payload, auth=AUTH)
                        if res.status_code == 200:
                            logger.info(f"✅ SCALE-IN SUCCESS")
                            trade['scaled'] = True # Mark as scaled so we don't do it infinitely
                    except Exception as e:
                        logger.error(f"❌ SCALE-IN FAILED: {e}")

                # --- STOP LOSS ---
                if current_profit < -1.0:
                    logger.info(f"🛡️ STOP LOSS TRIGGERED (Profit: ${current_profit}). CLOSING TICKET {ticket}...")
                    requests.post(f"{BRIDGE_URL}/close", json={"ticket": ticket}, auth=AUTH)
                    del active_trades[ticket]
                    session_profit -= 1.0 # Approximate
                    continue

                # --- DYNAMIC TIME EXIT ---
                is_high_confidence = trade.get('confidence', 0) > 90
                max_duration = 60 * 60 if is_high_confidence else (30 * 60 if current_profit > 0 else 5 * 60)
                
                if duration > max_duration:
                    reason = "TAKE PROFIT" if current_profit > 0 else "TIME STOP"
                    logger.info(f"⏰ {reason} ({duration/60:.1f}m, Profit: ${current_profit}). CLOSING TICKET {ticket}...")
                    try:
                        requests.post(f"{BRIDGE_URL}/close", json={"ticket": ticket}, auth=AUTH)
                        del active_trades[ticket]
                        session_profit += current_profit
                    except Exception as e:
                        logger.error(f"❌ CLOSE FAILED: {e}")

            # 2. Market Scan
            for symbol in SYMBOLS:
                symbol_trades = [t for t in active_trades.values() if t['symbol'] == symbol]
                price_data = get_market_price(symbol)
                decision = brain.analyze_market(symbol, price_data)
                
                if decision["signal"] in ["BUY", "SELL"] and decision["confidence"] > 80:
                    if len(symbol_trades) >= MAX_PYRAMID_LAYERS:
                        continue

                    logger.info(f"⚡ EXECUTING {decision['signal']} {symbol} (Confidence: {decision['confidence']}%)")
                    
                    # ADAPTIVE LOT SIZING
                    # If we are having a "Good Day" (Session Profit > $5), increase aggression.
                    base_lots = brain.calculate_position_size(10000)
                    lots = base_lots * 1.5 if session_profit > 5.0 else base_lots
                    lots = round(lots, 2)
                    
                    if session_profit > 5.0:
                        logger.info(f"🔥 GOOD DAY DETECTED (Profit: ${session_profit:.2f}). INCREASING LOTS TO {lots}")

                    payload = {
                        "symbol": symbol,
                        "type": decision["signal"],
                        "lots": lots,
                        "sl": 0, "tp": 0
                    }
                    
                    try:
                        res = requests.post(f"{BRIDGE_URL}/trade", json=payload, auth=AUTH)
                        if res.status_code == 200:
                            data = res.json()
                            ticket = data.get('ticket')
                            if ticket:
                                active_trades[ticket] = {
                                    "start_time": time.time(),
                                    "symbol": symbol,
                                    "type": decision["signal"],
                                    "confidence": decision["confidence"],
                                    "scaled": False
                                }
                                logger.info(f"✅ TRADE SUCCESS: Ticket {ticket}")
                    except Exception as e:
                        logger.error(f"❌ BRIDGE CONNECTION FAILED: {e}")

        except Exception as e:
            logger.error(f"⚠️ LOOP ERROR: {e}")

        logger.info(f"⏳ SCAN COMPLETE. Session Profit: ${session_profit:.2f}. SLEEPING 60s...")
        time.sleep(60)

if __name__ == "__main__":
    run_autopilot()

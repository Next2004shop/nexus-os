import MetaTrader5 as mt5
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import time
import pandas as pd
import threading
import os
from nexus_security import security

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBridge")

# --- CONFIGURATION ---
SERVER_PORT = 5001
DEVIATION = 20
MAGIC_NUMBER = 234000

# FORCED PATH - We found this is where it is running
FORCED_MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# WATCHLIST FOR AUTO-TRADER (Global)
WATCHLIST = [
    "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", 
    "US30", "NAS100", "SPX500", 
    "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX"
]

app = Flask(__name__)
CORS(app)

# Global State
connection_state = {
    "status": "DISCONNECTED",
    "path": None,
    "account": None,
    "last_check": 0
}

# --- SECURITY MIDDLEWARE ---
@app.before_request
def check_security():
    if not security.check_request(request.remote_addr, request.path):
        abort(403, description="Security Alert: Request Blocked by Nexus Defense Protocol")

# --- AUTHENTICATION ---
auth = HTTPBasicAuth()
users = {
    "admin": generate_password_hash("securepassword")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    security.record_failed_login(request.remote_addr)

# --- CONNECTION LOGIC ---

def connection_manager():
    """Background thread to maintain MT5 connection."""
    global connection_state
    
    logger.info("--- NEXUS BRIDGE: CONNECTION MANAGER STARTED ---")
    logger.info(f"Targeting MT5 at: {FORCED_MT5_PATH}")
    
    while True:
        try:
            # Check if connected
            if not mt5.initialize(path=FORCED_MT5_PATH):
                 # Try without path if specific path fails, or retry
                 err = mt5.last_error()
                 logger.error(f"Initialize failed with path {FORCED_MT5_PATH}. Error: {err}")
                 
                 # Retry without path (uses registry)
                 if not mt5.initialize():
                     logger.error(f"Initialize (default) failed. Error: {mt5.last_error()}")
                     connection_state["status"] = "DISCONNECTED"
                 else:
                     logger.info("✅ SUCCESS: Connected to MetaTrader 5 (Default Path)")
                     connection_state["status"] = "CONNECTED"
                     connection_state["path"] = "Default"
            else:
                 # logger.info(f"✅ SUCCESS: Connected to MetaTrader 5 at {FORCED_MT5_PATH}")
                 connection_state["status"] = "CONNECTED"
                 connection_state["path"] = FORCED_MT5_PATH
            
            # Update Account Info if connected
            if connection_state["status"] == "CONNECTED":
                account_info = mt5.account_info()
                if account_info:
                    connection_state["account"] = {
                        "login": account_info.login,
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "server": account_info.server,
                        "currency": account_info.currency
                    }
                else:
                    connection_state["status"] = "CONNECTED_NO_ACCOUNT"
                    
            connection_state["last_check"] = time.time()
            
        except Exception as e:
            logger.error(f"Connection Manager Error: {e}")
            connection_state["status"] = "ERROR"
            
        time.sleep(10) # Check every 10 seconds

def auto_trader():
    """Background thread that scans markets and executes trades."""
    logger.info("--- NEXUS AUTO-TRADER: ENGAGED ---")
    
    # Wait for connection
    while connection_state["status"] != "CONNECTED":
        time.sleep(5)

    logger.info("--- AUTO-TRADER: SCANNING MARKETS ---")
    
    while True:
        try:
            if connection_state["status"] == "CONNECTED":
                for symbol in WATCHLIST:
                    # 1. Check if symbol is valid/visible
                    s_info = mt5.symbol_info(symbol)
                    if s_info is None:
                        # Try adding it
                        if not mt5.symbol_select(symbol, True):
                            continue
                        s_info = mt5.symbol_info(symbol)
                        if s_info is None: continue
                    
                    if not s_info.visible:
                        mt5.symbol_select(symbol, True)

                    # 2. Get Data
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
                    if rates is None or len(rates) < 50:
                        continue

                    # 3. Analyze
                    # Convert to list of dicts for brain
                    price_data = []
                    for rate in rates:
                        price_data.append({
                            "time": int(rate['time']),
                            "open": float(rate['open']),
                            "high": float(rate['high']),
                            "low": float(rate['low']),
                            "close": float(rate['close']),
                            "tick_volume": int(rate['tick_volume'])
                        })
                    
                    from nexus_brain import brain
                    analysis = brain.analyze_market(symbol, price_data)
                    
                    # 4. Execute Trade if Confidence is High
                    if analysis['confidence'] >= 85 and analysis['signal'] in ["BUY", "SELL"]:
                        logger.info(f"🚨 SIGNAL DETECTED: {symbol} {analysis['signal']} ({analysis['confidence']}%)")
                        
                        # Check if we already have a position to avoid spamming
                        positions = mt5.positions_get(symbol=symbol)
                        if positions and len(positions) > 0:
                            # logger.info(f"Skipping {symbol}: Position already open.")
                            continue

                        # Execute
                        action = mt5.ORDER_TYPE_BUY if analysis['signal'] == "BUY" else mt5.ORDER_TYPE_SELL
                        price = mt5.symbol_info_tick(symbol).ask if analysis['signal'] == "BUY" else mt5.symbol_info_tick(symbol).bid
                        
                        request_trade = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": 0.01, # Fixed lot for safety
                            "type": action,
                            "price": price,
                            "deviation": DEVIATION,
                            "magic": MAGIC_NUMBER,
                            "comment": "Nexus AI Auto",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        
                        result = mt5.order_send(request_trade)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            logger.info(f"✅ TRADE EXECUTED: {symbol} {analysis['signal']}")
                        else:
                            logger.error(f"❌ TRADE FAILED: {result.comment}")

            time.sleep(60) # Scan every 60 seconds

        except Exception as e:
            logger.error(f"Auto-Trader Error: {e}")
            time.sleep(60)

# Start connection manager in background
threading.Thread(target=connection_manager, daemon=True).start()
# Start auto-trader in background
threading.Thread(target=auto_trader, daemon=True).start()

# --- ROUTES ---

@app.route('/status', methods=['GET'])
@auth.login_required
def status():
    """Returns detailed connection status"""
    global connection_state
    
    response = {
        "bridge_status": "ONLINE",
        "mt5_status": connection_state["status"],
        "mt5_path": connection_state["path"],
        "timestamp": time.time()
    }
    
    if connection_state["account"]:
        response.update(connection_state["account"])
        
    return jsonify(response)

@app.route('/trade', methods=['POST'])
@auth.login_required
def place_trade():
    """Executes a BUY or SELL order"""
    if connection_state["status"] != "CONNECTED":
        return jsonify({"error": "MT5 Not Connected", "status": connection_state["status"]}), 503

    data = request.json
    symbol = data.get('symbol', 'EURUSD')
    action_type = data.get('type', 'BUY')
    volume = float(data.get('lots', 0.01))
    stop_loss = float(data.get('sl', 0.0))
    take_profit = float(data.get('tp', 0.0))

    # Ensure symbol is available
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return jsonify({"error": f"Symbol {symbol} not found"}), 404
    
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
             return jsonify({"error": f"Symbol {symbol} not visible"}), 404

    # Determine Order Type
    order_type = mt5.ORDER_TYPE_BUY if action_type == 'BUY' else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if action_type == 'BUY' else mt5.symbol_info_tick(symbol).bid
    
    request_data = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": "Nexus AI Auto-Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request_data)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return jsonify({"error": "Trade Failed", "retcode": result.retcode, "comment": result.comment}), 400
        
    return jsonify({"status": "Trade Executed", "ticket": result.order})

@app.route('/ai/chat', methods=['POST'])
@auth.login_required
def ai_chat():
    """General AI Chat Endpoint"""
    try:
        from nexus_brain import brain
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        
        response_text = brain.ask_gemini_chat(message, history)
        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ai/analyze', methods=['POST'])
@auth.login_required
def analyze_symbol():
    """Triggers AI analysis for a specific symbol"""
    try:
        from nexus_brain import brain
        data = request.json
        symbol = data.get('symbol', 'EURUSD')
        timeframe_str = data.get('timeframe', 'M15')
        
        # Map timeframe string to MT5 constant
        tf_map = {
            'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        timeframe = tf_map.get(timeframe_str, mt5.TIMEFRAME_M15)

        rates = None
        if connection_state["status"] == "CONNECTED":
            # Fetch recent data (100 candles)
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        
        if rates is None or len(rates) == 0:
             # Fallback for offline mode testing
             logger.warning(f"No data for {symbol} (MT5 Offline/Unavailable). Using Mock Data.")
             import numpy as np
             mock_data = []
             base_price = 2000.0 if symbol == "XAUUSD" else 1.1000
             for i in range(100):
                 mock_data.append({
                     "time": int(time.time()) - (100-i)*900,
                     "open": base_price,
                     "high": base_price + 5,
                     "low": base_price - 5,
                     "close": base_price + (np.sin(i/10) * 10),
                     "tick_volume": 1000
                 })
             result = brain.analyze_market(symbol, mock_data)
             result['note'] = "MOCK DATA USED (MT5 Offline)"
             return jsonify(result)

        price_data = []
        for rate in rates:
            price_data.append({
                "time": int(rate['time']),
                "open": float(rate['open']),
                "high": float(rate['high']),
                "low": float(rate['low']),
                "close": float(rate['close']),
                "tick_volume": int(rate['tick_volume'])
            })

        result = brain.analyze_market(symbol, price_data)
        return jsonify(result)
    except ImportError:
        return jsonify({"error": "AI Module missing"}), 500
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/positions', methods=['GET'])
@auth.login_required
def get_positions():
    """Fetches all open positions"""
    if connection_state["status"] != "CONNECTED":
        return jsonify({"error": "MT5 Not Connected"}), 503
        
    positions = mt5.positions_get()
    if positions is None:
        return jsonify({"error": "Could not retrieve positions"}), 500

    positions_list = []
    for pos in positions:
        positions_list.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "price_open": pos.price_open,
            "profit": pos.profit
        })
    return jsonify(positions_list)

@app.route('/history', methods=['GET'])
@auth.login_required
def get_history():
    """Fetches trade history for the current account"""
    if connection_state["status"] != "CONNECTED":
        return jsonify({"error": "MT5 Not Connected"}), 503

    start_time = request.args.get('start', int(time.time()) - 86400)
    end_time = request.args.get('end', int(time.time()))

    history = mt5.history_deals_get(start_time, end_time)
    if history is None:
        return jsonify({"error": "Could not retrieve history"}), 500

    history_list = []
    for deal in history:
        history_list.append({
            "ticket": deal.ticket,
            "symbol": deal.symbol,
            "volume": deal.volume,
            "price": deal.price,
            "profit": deal.profit
        })
    return jsonify(history_list)

@app.route('/market/prices', methods=['GET'])
@auth.login_required
def get_market_prices():
    """Fetches real-time prices for all watchlist assets"""
    if connection_state["status"] != "CONNECTED":
        # Return Mock Data if offline (so app doesn't crash)
        return jsonify({"status": "OFFLINE", "prices": []}), 503

    prices = []
    for symbol in WATCHLIST:
        # Ensure symbol is selected
        if not mt5.symbol_info(symbol):
            # Try variations if standard fails (e.g. NAS100 vs USTEC)
            continue
            
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            prices.append({
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "time": tick.time,
                "change": 0.0 # MT5 tick doesn't give 24h change easily, handled in frontend or separate call
            })
    
    return jsonify(prices)

@app.route('/market/candles', methods=['GET'])
@auth.login_required
def get_market_candles():
    """Fetches OHLC candles for a symbol"""
    if connection_state["status"] != "CONNECTED":
        return jsonify({"error": "MT5 Not Connected"}), 503

    symbol = request.args.get('symbol', 'EURUSD')
    timeframe_str = request.args.get('timeframe', 'M15')
    limit = int(request.args.get('limit', 100))

    # Map timeframe string to MT5 constant
    tf_map = {
        'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    timeframe = tf_map.get(timeframe_str, mt5.TIMEFRAME_M15)

    # Ensure symbol is selected
    if not mt5.symbol_info(symbol):
         if not mt5.symbol_select(symbol, True):
             return jsonify({"error": f"Symbol {symbol} not found"}), 404

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, limit)
    
    if rates is None or len(rates) == 0:
        return jsonify([])

    candles = []
    for rate in rates:
        candles.append({
            "time": int(rate['time']), # Unix timestamp
            "open": float(rate['open']),
            "high": float(rate['high']),
            "low": float(rate['low']),
            "close": float(rate['close']),
            "volume": int(rate['tick_volume'])
        })
    
    return jsonify(candles)

if __name__ == '__main__':
    logger.info("🚀 NEXUS BRIDGE UPGRADED (v2.0) LISTENING ON PORT %d...", SERVER_PORT)
    app.run(host='0.0.0.0', port=SERVER_PORT, threaded=True)
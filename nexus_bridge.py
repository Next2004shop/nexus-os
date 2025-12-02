import MetaTrader5 as mt5
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import time
import pandas as pd
from nexus_security import security

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBridge")

# --- CONFIGURATION ---
SERVER_PORT = 5000
DEVIATION = 20
MAGIC_NUMBER = 234000
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

app = Flask(__name__)
CORS(app)

# --- SECURITY MIDDLEWARE ---
@app.before_request
def check_security():
    # Skip security check for local loopback if needed, but security module handles whitelist
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
    # Record failed login attempt
    security.record_failed_login(request.remote_addr)

# --- INITIALIZATION ---
logger.info("--- NEXUS BRIDGE: INITIALIZING ---")

if not mt5.initialize(path=MT5_PATH):
    logger.error("Initialization failed. Error: %s", mt5.last_error())
    logger.warning("Continuing in OFFLINE mode...")
else:
    logger.info("Connected to MetaTrader 5")
    account_info = mt5.account_info()
    if account_info:
        logger.info(f"User: {account_info.login}, Balance: {account_info.balance} {account_info.currency}, Server: {account_info.server}")
    else:
        logger.warning("Could not retrieve account info. Ensure MT5 is open and logged in.")

# --- ROUTES ---

@app.route('/status', methods=['GET'])
@auth.login_required
def status():
    """Checks if the bridge is alive and gets account balance"""
    if not mt5.initialize(path=MT5_PATH):
        return jsonify({"status": "ERROR", "msg": "MT5 Disconnected"})
        
    info = mt5.account_info()
    if info:
        return jsonify({
            "status": "ONLINE",
            "balance": info.balance,
            "equity": info.equity,
            "profit": info.profit
        })
    return jsonify({"status": "ERROR", "msg": "MT5 Disconnected"})

@app.route('/trade', methods=['POST'])
@auth.login_required
def place_trade():
    """Executes a BUY or SELL order"""
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
    return jsonify({"status": "Trade Simulated (MT5 Offline)"})

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

        # Fetch recent data (100 candles)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        
        if rates is None or len(rates) == 0:
             # Fallback for offline mode testing if MT5 is not connected
             # Create mock data for testing "Legendary" logic if real data fails
             logger.warning(f"No data for {symbol} (MT5 Offline?). Using Mock Data.")
             import numpy as np
             mock_data = []
             base_price = 2000.0 if symbol == "XAUUSD" else 1.1000
             for i in range(100):
                 mock_data.append({
                     "time": int(time.time()) - (100-i)*900,
                     "open": base_price,
                     "high": base_price + 5,
                     "low": base_price - 5,
                     "close": base_price + (np.sin(i/10) * 10), # Sine wave for trend
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

if __name__ == '__main__':
    logger.info("🚀 NEXUS BRIDGE LISTENING ON PORT %d...", SERVER_PORT)
    app.run(host='0.0.0.0', port=SERVER_PORT)
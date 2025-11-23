import MetaTrader5 as mt5
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import time

# --- CONFIGURATION ---
SERVER_PORT = 5000
DEVIATION = 20
MAGIC_NUMBER = 234000

app = Flask(__name__)
CORS(app)

# --- AUTHENTICATION ---
auth = HTTPBasicAuth()
users = {
    "admin": generate_password_hash("securepassword")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBridge")

# --- INITIALIZATION ---
logger.info("--- NEXUS BRIDGE: INITIALIZING ---")

if not mt5.initialize():
    logger.error("Initialization failed. Error: %s", mt5.last_error())
    quit()
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
    if not mt5.initialize():
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

    # Send Order
    result = mt5.order_send(request_data)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error("Trade failed: %s", result.comment)
        return jsonify({"status": "FAILED", "error": result.comment})
    
    # Log to Ledger
    try:
        from nexus_security import ledger
        ledger.record_transaction("TRADE", 0, f"{action_type} {volume} {symbol} @ {price}")
    except ImportError:
        logger.warning("Security module not found, skipping ledger.")

    logger.info("%s ORDER EXECUTED: %s @ %s", action_type, symbol, price)
    return jsonify({"status": "EXECUTED", "ticket": result.order})

@app.route('/withdraw', methods=['POST'])
@auth.login_required
def withdraw():
    """Process a secure withdrawal"""
    try:
        from nexus_security import vault, ledger
        data = request.json
        amount = float(data.get('amount', 0))
        address = data.get('address', 'Unknown')
        
        success, msg = vault.verify_withdrawal(amount, "admin")
        if not success:
            return jsonify({"status": "BLOCKED", "error": msg}), 403
            
        # Log to Ledger
        tx_id = ledger.record_transaction("WITHDRAWAL", amount, f"To: {address}")
        return jsonify({"status": "APPROVED", "tx_id": tx_id, "msg": "Funds released to blockchain"})
    except ImportError:
        return jsonify({"status": "ERROR", "msg": "Security module missing"}), 500

# --- AI ENDPOINTS ---

@app.route('/ai/insight', methods=['GET'])
@auth.login_required
def get_insight():
    """Returns a live insight from the AI brain"""
    try:
        from nexus_brain import brain
        return jsonify({"insight": brain.get_ai_insights()})
    except ImportError:
        return jsonify({"insight": "AI Module Loading..."})

@app.route('/ai/analyze', methods=['POST'])
@auth.login_required
def analyze_symbol():
    """Triggers AI analysis for a specific symbol"""
    try:
        from nexus_brain import brain
        data = request.json
        symbol = data.get('symbol', 'EURUSD')
        result = brain.analyze_market(symbol)
        return jsonify(result)
    except ImportError:
        return jsonify({"error": "AI Module missing"}), 500

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
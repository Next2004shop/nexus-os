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
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Literal
from nexus_core import MarketIntake, TechnicalAnalysisEngine, SmartMoneyEngine, StealthVault, BurnProtocol
import jwt
from functools import wraps

# Initialize Core Modules
market_intake = MarketIntake()
ta_engine = TechnicalAnalysisEngine()
smc_engine = SmartMoneyEngine()
stealth_vault = StealthVault()

# CONFIG
NEXUS_API_KEY = "nexus-local-key-123"
# For Admin JWT (using HS256 for local dev simplicity unless RS256 keys provided)
NEXUS_JWT_SECRET = "nexus-super-secret-admin-key" 

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key and api_key == NEXUS_API_KEY:
            return f(*args, **kwargs)
        return jsonify({"message": "Forbidden: Invalid API Key"}), 401
    return decorated

def require_admin_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"message": "Missing Token"}), 401
            
        try:
            # Decode (Skipping RS256 verification for local POC, using HS256)
            # In fully strict mode, load public key.
            data = jwt.decode(token, NEXUS_JWT_SECRET, algorithms=["HS256"])
            # verify audience if needed
        except Exception as e:
            return jsonify({"message": "Invalid Token", "error": str(e)}), 403
            
        return f(*args, **kwargs)
    return decorated

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBridge")

# --- CONFIGURATION ---
SERVER_PORT = 5001
DEVIATION = 20
FORCED_MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe" # Ensure this is defined or handled
WATCHLIST = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "US30", "NAS100"] # Default watchlist
MAGIC_NUMBER = 123456

app = Flask(__name__)
CORS(app)

# --- VALIDATION MODELS ---
class TradeRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=10)
    type: Literal['BUY', 'SELL']
    lots: float = Field(..., gt=0.0, le=100.0)
    sl: Optional[float] = Field(0.0, ge=0.0)
    tp: Optional[float] = Field(0.0, ge=0.0)

class AIAnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=10)
    timeframe: Literal['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'] = 'M15'

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[dict] = Field(default_factory=list)

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
    if request.method == "OPTIONS":
        return
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
    # logger.info(f"Targeting MT5 at: {FORCED_MT5_PATH}")
    
    while True:
        try:
            # Check if connected
            if not mt5.initialize():
                 # Try with specific path if default fails
                 # if not mt5.initialize(path=FORCED_MT5_PATH):
                 err = mt5.last_error()
                 logger.error(f"Initialize failed. Error: {err}")
                 connection_state["status"] = "DISCONNECTED"
            else:
                 connection_state["status"] = "CONNECTED"
                 connection_state["path"] = "Default"
            
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
    # Wait for connection
    while connection_state["status"] != "CONNECTED":
        time.sleep(5)

    logger.info("--- AUTO-TRADER: SCANNING MARKETS ---")
    
    while True:
        try:
            if connection_state["status"] == "CONNECTED":
                # DYNAMIC WATCHLIST: Get all visible symbols in Market Watch
                symbols = mt5.symbols_get(visible=True) 
                current_watchlist = [s.name for s in symbols] if symbols else WATCHLIST
                
                for symbol in current_watchlist:
                    # 1. Check if symbol is valid/visible
                    s_info = mt5.symbol_info(symbol)
                    if s_info is None: continue
                    
                    # 2. Get Data
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
                    if rates is None or len(rates) < 50:
                        continue

                    # 3. Analyze
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
                        
                    # 4. AI Analysis
                    from nexus_brain import brain
                    analysis = brain.analyze_market(symbol, price_data)
                    
                    # 5. Execute Trade (Strict 85% Confidence Rule)
                    if analysis['signal'] in ["BUY", "SELL"] and analysis['confidence'] >= 85:
                        
                        # Check if we already have a position
                        positions = mt5.positions_get(symbol=symbol)
                        if positions and len(positions) > 0:
                            continue

                        # Execute
                        action = mt5.ORDER_TYPE_BUY if analysis['signal'] == "BUY" else mt5.ORDER_TYPE_SELL
                        price = mt5.symbol_info_tick(symbol).ask if analysis['signal'] == "BUY" else mt5.symbol_info_tick(symbol).bid
                        
                        sl = analysis.get('sl', 0.0)
                        tp = analysis.get('tp', 0.0)
                        
                        request_trade = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": 0.01, 
                            "type": action,
                            "price": price,
                            "sl": float(sl),
                            "tp": float(tp),
                            "deviation": DEVIATION,
                            "magic": MAGIC_NUMBER,
                            "comment": f"Nexus AI {analysis['confidence']}%",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        
                        result = mt5.order_send(request_trade)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            logger.info(f"✅ TRADE EXECUTED: {symbol} {analysis['signal']} @ {price}")
                        else:
                            logger.error(f"❌ TRADE FAILED: {result.comment}")

            time.sleep(60) # Scan every 60 seconds

        except Exception as e:
            logger.error(f"Auto-Trader Error: {e}")
            time.sleep(60)

def ma_auto_trader():
    """Background thread that scans for M&A news and executes 'Insider' trades."""
    logger.info("--- NEXUS M&A INSIDER: ENGAGED ---")
    
    while connection_state["status"] != "CONNECTED":
        time.sleep(10)

    while True:
        try:
            # logger.info("🕵️ M&A SCANNER: Searching for opportunities...")
            import ma_scanner
            import importlib
            importlib.reload(ma_scanner)
            
            news = ma_scanner.fetch_financial_news()
            opportunities = ma_scanner.analyze_opportunities(news)
            
            for opp in opportunities:
                score = opp.get('likelihood_score', 0)
                ticker = opp.get('target_ticker')
                
                if score >= 80 and ticker:
                    logger.info(f"🚨 HIGH CONFIDENCE M&A SIGNAL: {opp['target_company']} ({ticker}) - {score}%")
                    
                    if mt5.symbol_select(ticker, True):
                        tick = mt5.symbol_info_tick(ticker)
                        if tick:
                            price = tick.ask
                            request_trade = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": ticker,
                                "volume": 1.0, 
                                "type": mt5.ORDER_TYPE_BUY,
                                "price": price,
                                "deviation": 50,
                                "magic": 777000,
                                "comment": f"M&A: {opp['acquirer']}->{opp['target_company']}",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            result = mt5.order_send(request_trade)
                            if result.retcode == mt5.TRADE_RETCODE_DONE:
                                logger.info(f"🚀 M&A TRADE EXECUTED: BOUGHT {ticker} @ {price}")
                            else:
                                logger.error(f"❌ M&A TRADE FAILED: {result.comment}")
            
            time.sleep(900) 

        except Exception as e:
            logger.error(f"M&A Auto-Trader Error: {e}")
            time.sleep(60)

@app.route('/status', methods=['GET'])
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

    try:
        # Validate Request
        trade_req = TradeRequest(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Validation Error", "details": e.errors()}), 400

    symbol = trade_req.symbol
    action_type = trade_req.type
    volume = trade_req.lots
    stop_loss = trade_req.sl
    take_profit = trade_req.tp

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
        try:
            chat_req = AIChatRequest(**request.json)
        except ValidationError as ve:
            return jsonify({"error": "Validation Error", "details": ve.errors()}), 400
            
        from nexus_brain import brain
        message = chat_req.message
        
        history = chat_req.history
        response_data = brain.ask_gemini_chat(message, history)
        
        if isinstance(response_data, dict) and response_data.get('type') == 'trade_command':
             # STOP! DO NOT AUTO-EXECUTE.
             # Return the proposal to the User for "Supervisor Approval".
             return jsonify({
                 "response": {
                     "type": "trade_proposal",
                     "symbol": response_data.get('symbol'),
                     "action": response_data.get('action'),
                     "volume": response_data.get('volume'),
                     "reason": "High Confidence Setup Identified."
                 }
             })
        
        # Normal Text Response
        return jsonify({"response": response_data.get('content')})

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        return jsonify({"error": str(e)}), 500

class PredictRequest(BaseModel):
    asset: str
    timeframe: str
    mode: Literal['Scout', 'Hunter', 'Titan', 'Oracle'] = 'Hunter'
    context: Optional[dict] = {}

# Internal Core Logic
def core_predict_logic(symbol, timeframe, mode):
    # 1. Fetch Data
    df = market_intake.get_candles(symbol, timeframe, n=100)
    if df.empty: return None
         
    # 2. Tech Analysis
    df_analyzed = ta_engine.analyze(df)
    ta_summary = ta_engine.get_signal_summary(df_analyzed)
    
    # 3. Smart Money
    df_smc = smc_engine.analyze(df_analyzed)
    smc_summary = smc_engine.get_smc_summary(df_smc)
    
    # 4. AI Brain Analysis
    price_data = df.tail(20).to_dict(orient='records')
    from nexus_brain import brain
    ai_analysis = brain.analyze_market(symbol, price_data)
    
    # 5. Format Response
    return {
        "asset": symbol,
        "direction": ai_analysis.get("direction", "NEUTRAL"),
        "strength": ai_analysis.get("strength", "Weak"),
        "confidence": ai_analysis.get("confidence", 0) / 100.0,
        "timeframe": timeframe,
        "entry": ai_analysis.get("entry", 0.0),
        "stop_loss": ai_analysis.get("sl", 0.0),
        "take_profit": ai_analysis.get("tp", 0.0),
        "risk_rating": ai_analysis.get("risk_rating", "Medium"),
        "reason": ai_analysis.get("reason", "Analysis Complete"),
        "mode": mode,
        "technical": ta_summary, # Extra for legacy
        "smart_money": smc_summary, # Extra for legacy
        "ai_signal": ai_analysis # Extra for legacy
    }

@app.route('/predict', methods=['POST'])
@require_api_key
def predict_endpoint():
    """OpenAPI Predict Endpoint"""
    try:
        req_model = PredictRequest(**request.json)
    except ValidationError as ve:
        return jsonify({"error": "Validation Error", "details": ve.errors()}), 400
        
    result = core_predict_logic(req_model.asset, req_model.timeframe, req_model.mode)
    
    if not result:
        return jsonify({"error": "No Data Found"}), 404
        
    # Filter for strict OpenAPI response
    response = {k: v for k, v in result.items() if k in ['asset', 'direction', 'strength', 'confidence', 'timeframe', 'entry', 'stop_loss', 'take_profit', 'risk_rating', 'reason']}
    response['timestamp'] = datetime.utcnow().isoformat() + "Z"
    
    return jsonify(response)

@app.route('/ai/analyze', methods=['POST'])
@auth.login_required
def analyze_symbol():
    """Legacy Endpoint (Wrapper)"""
    try:
        req_model = AIAnalysisRequest(**request.json)
        # Map legacy to new logic
        result = core_predict_logic(req_model.symbol, req_model.timeframe, 'Hunter')
        
        if not result:
             return jsonify({"error": "No Data Found"}), 404
             
        # Reconstruct Legacy Format
        final_result = {
            "symbol": result['asset'],
            "timeframe": result['timeframe'],
            "technical": result['technical'],
            "smart_money": result['smart_money'],
            "ai_signal": result['ai_signal']
        }
        return jsonify(final_result)
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/positions', methods=['GET'])
@auth.login_required
def get_positions():
    """Fetches current open positions"""
    if connection_state["status"] != "CONNECTED":
        return jsonify({"error": "MT5 Not Connected"}), 503

    positions = mt5.positions_get()
    if positions is None:
        return jsonify([])

    positions_list = []
    for pos in positions:
        positions_list.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "price_open": pos.price_open,
            "profit": pos.profit,
            "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
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
        # FALLBACK MODE FOR BLANK PAGES
        return jsonify({
            "status": "FALLBACK",
            "prices": [
                {"symbol": "EURUSD", "bid": 1.1050, "ask": 1.1052, "change": 0.15},
                {"symbol": "GBPUSD", "bid": 1.2750, "ask": 1.2753, "change": -0.05},
                {"symbol": "XAUUSD", "bid": 2400.00, "ask": 2400.50, "change": 1.2},
                {"symbol": "BTCUSD", "bid": 65000.00, "ask": 65005.00, "change": 2.5},
                {"symbol": "US30", "bid": 39000.00, "ask": 39005.00, "change": 0.5},
                {"symbol": "AAPL", "bid": 220.50, "ask": 220.60, "change": 0.8},
                {"symbol": "TSLA", "bid": 175.20, "ask": 175.30, "change": -1.2},
                {"symbol": "NVDA", "bid": 120.00, "ask": 120.10, "change": 3.4}
            ]
        })

    prices = []
    symbols = mt5.symbols_get(visible=True)
    current_watchlist = [s.name for s in symbols] if symbols else WATCHLIST

    for symbol in current_watchlist:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            # Calculate approx daily change (mock calculation as real daily change needs history)
            change = 0.0
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1)
            if rates is not None and len(rates) > 0:
                open_price = rates[0]['open']
                change = ((tick.bid - open_price) / open_price) * 100

            prices.append({
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "change": round(change, 2)
            })
    
    return jsonify({"status": "ONLINE", "prices": prices})

@app.route('/wallet/deposit', methods=['POST'])
@auth.login_required
def process_deposit():
    """Simulates a crypto deposit"""
    data = request.json
    amount = data.get('amount', 0)
    method = data.get('method', 'BTC')
    
    # In a real app, this would check blockchain tx
    time.sleep(2) # Simulate processing
    
    # We can't actually update MT5 balance easily via Python API (usually read-only for balance)
    # So we'll return a success message for the UI to display 'Pending' or 'Success'
    
    return jsonify({
        "status": "SUCCESS",
        "tx_id": f"0x{int(time.time())}abcdef",
        "message": f"Deposit of {amount} {method} received. Balance will update shortly."
    })

@app.route('/market/candles', methods=['GET'])
@auth.login_required
def get_candles():
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

@app.route('/stealth/burn', methods=['POST'])
@auth.login_required
def burn_protocol():
    """Triggers the Burn Protocol (Wipe Logs)"""
    wiped_files = BurnProtocol.execute_burn()
    return jsonify({"status": "BURN_COMPLETE", "wiped": wiped_files})

@app.route('/stealth/encrypt', methods=['POST'])
@auth.login_required
def encrypt_data():
    """Test Endpoint for Encryption"""
    data = request.json.get('data', '')
    encrypted = stealth_vault.encrypt(data)
    return jsonify({"encrypted": encrypted.decode()})


# --- START BACKGROUND THREADS ---
if __name__ == '__main__':
    # Start connection manager
    threading.Thread(target=connection_manager, daemon=True).start()
    # Start auto-trader
    threading.Thread(target=auto_trader, daemon=True).start()
    # Start M&A auto-trader
    threading.Thread(target=ma_auto_trader, daemon=True).start()

    logger.info("🚀 NEXUS BRIDGE UPGRADED (v2.0) LISTENING ON PORT %d...", SERVER_PORT)
    app.run(host='127.0.0.1', port=SERVER_PORT, threaded=True)
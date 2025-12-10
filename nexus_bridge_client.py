
import asyncio
import websockets
import json
import MetaTrader5 as mt5
import os
import logging
from dotenv import load_dotenv
import requests

# Load Config
load_dotenv(".env.local")
API_URL = os.getenv("CLOUD_API_URL", "https://nexus-backend-xyz.a.run.app") # Will replace with real URL
WS_URL = API_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws/bridge"
USERNAME = "admin"
PASSWORD = "securepassword"

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - BRIDGE - %(message)s')
logger = logging.getLogger("NexusBridge")

async def connect_to_mt5():
    if not mt5.initialize():
        logger.error(f"❌ MT5 Initialization Failed: {mt5.last_error()}")
        return False
    logger.info(f"✅ MT5 Connected to: {mt5.account_info().login}")
    return True

async def authenticate():
    try:
        data = {"username": USERNAME, "password": PASSWORD}
        resp = requests.post(f"{API_URL}/auth/token", data=data)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            logger.info("🔑 Authenticated with Cloud Brain")
            return token
        else:
            logger.error(f"❌ Auth Failed: {resp.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")
        return None

async def listen_for_commands(token):
    uri = f"{WS_URL}?token={token}"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("⚡ Connected to Nexus Cloud Stream")
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    logger.info(f"📩 Received: {data}")
                    
                    if data.get("type") == "TRADE_COMMAND":
                        execute_mt5_trade(data)
                        
        except Exception as e:
            logger.warning(f"⚠️ Connection Lost: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

def execute_mt5_trade(cmd):
    symbol = cmd.get("symbol")
    action = cmd.get("action") # BUY/SELL
    volume = float(cmd.get("volume", 0.01))
    
    order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if action == "BUY" else mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Nexus AI Cloud Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"❌ Trade Failed: {result.comment}")
    else:
        logger.info(f"✅ Trade Executed: {result.order}")

async def main():
    if not await connect_to_mt5():
        return

    token = await authenticate()
    if token:
        await listen_for_commands(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        mt5.shutdown()

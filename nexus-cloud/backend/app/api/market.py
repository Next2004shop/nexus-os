from fastapi import APIRouter, Depends, HTTPException
import MetaTrader5 as mt5
from typing import List, Optional
from pydantic import BaseModel
from app.api.auth import get_current_user

router = APIRouter()

class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int

@router.get("/prices", response_model=dict)
def get_live_prices(current_user: dict = Depends(get_current_user)):
    # Assuming MT5 is initialized in main or middleware
    if not mt5.initialize():
        headers = {"X-Offline-Mode": "true"}
        # Return mock data if MT5 is down (Cloud run might not have MT5 access directly)
        return {"BTCUSD": 98000.50, "EURUSD": 1.0850}
    
    symbols = ["BTCUSD", "EURUSD", "GBPUSD", "XAUUSD"]
    prices = {}
    for sym in symbols:
        tick = mt5.symbol_info_tick(sym)
        if tick:
            prices[sym] = tick.bid
    
    return prices

@router.get("/candles/{symbol}", response_model=List[Candle])
def get_candles(symbol: str, timeframe: str = "H1", limit: int = 100, current_user: dict = Depends(get_current_user)):
    # MT5 Logic here
    # For now, return mock if offline
    import time
    import random
    
    data = []
    t = int(time.time()) - (limit * 3600)
    p = 50000.0
    
    for _ in range(limit):
        open_p = p + (random.random() - 0.5) * 100
        close_p = open_p + (random.random() - 0.5) * 100
        high_p = max(open_p, close_p) + random.random() * 50
        low_p = min(open_p, close_p) - random.random() * 50
        
        data.append({
            "time": t,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "tick_volume": int(random.random() * 1000)
        })
        t += 3600
        p = close_p
        
    return data

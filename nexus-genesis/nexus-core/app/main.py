import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from app.services import intelligence, execution, risk_governor, ancient_logic, scheduler

# Configure central logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nexus.nervous_system")

app = FastAPI(title="NEXUS SOVEREIGN SYSTEM")

@app.on_event("startup")
async def startup_event():
    logger.info("NEXUS CORE ONLINE. ARCHITECTURE: ANCIENT X AXELROD. BRAIN: CLAUDE-3.5-HAIKU.")
    # Start the Heartbeat Scheduler
    scheduler.start_scheduler()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "Nexus Online"}

@app.post("/analyze")
async def analyze_market(data: Dict[str, Any] = Body(...)):
    logger.info("Received analysis request")
    try:
        result = intelligence.analyze_market(data)
        return result
    except Exception as e:
        logger.error(f"Analysis route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def place_trade(
    symbol: str = Body(...),
    side: str = Body(...),
    quantity: float = Body(...),
    market_context: Dict[str, Any] = Body(...)
):
    """
    The Nervous System: Orchestrates Trade Execution with Governor Overrides.
    """
    logger.info(f"NEXUS_TRADE_COMMAND: {side} {quantity} {symbol}")
    
    try:
        # STEP 1: ANCIENT LOGIC OVERRIDE
        market_context["signal"] = side
        cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
        if not cycle_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Ancient Logic): {cycle_msg}")
            return {"status": "REJECTED_BY_GOVERNOR", "reason": cycle_msg}

        # STEP 2: RISK GOVERNOR VALIDATION
        # Mock price and ATR for validation (Production would fetch real-time)
        price = market_context.get("price", 0.0) 
        atr_data = market_context.get("atr_data", {})
        
        risk_ok, risk_msg = risk_governor.validate_trade(symbol, quantity, price, atr_data)
        if not risk_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Risk Filter): {risk_msg}")
            return {"status": "REJECTED_BY_GOVERNOR", "reason": risk_msg}

        # STEP 3: EXECUTION
        result = execution.execute_trade(symbol, side, quantity)
        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
        
        return result

    except Exception as e:
        logger.error(f"Trade route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/kill")
async def emergency_kill(symbol: str = Body(None)):
    logger.warning("EMERGENCY KILL TRIGGERED VIA API")
    try:
        result = execution.kill_switch(symbol)
        return result
    except Exception as e:
        logger.error(f"Kill switch route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_equity")
async def update_equity(equity: float = Body(...)):
    """Update governor equity for drawdown tracking."""
    risk_governor.update_equity(equity)
    return {"status": "updated", "current_equity": equity}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

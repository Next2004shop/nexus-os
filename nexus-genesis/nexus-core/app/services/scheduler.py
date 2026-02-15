import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services import intelligence, ancient_logic, risk_governor, execution

logger = logging.getLogger("nexus.heartbeat")

async def heartbeat_task():
    """
    The 15-minute Candle Period Heartbeat.

    ARCHITECTURE: Interface → Intent → Risk → Execution
    All trade execution routes through execution.execute_trade().
    NO direct MT5/bridge calls from scheduler.

    1. Wake up Intelligence (Intent Layer)
    2. Check Ancient Logic (Intent Layer)
    3. Run Risk Governor (Risk Layer)
    4. Execute Trade via ExecutionEngine (Execution Layer)
    """
    logger.info(f"HEARTBEAT_INITIATED: {datetime.now()}")
    
    try:
        symbol = "BTCUSD"
        
        # 0. Sync Governor with live equity (via execution engine's MT5 status)
        engine = execution.get_engine()
        if engine.mt5._initialized and engine.mt5._mt5:
            try:
                account_info = engine.mt5._mt5.account_info()
                equity = account_info.equity if account_info else 10000.0
            except Exception:
                equity = 10000.0
        else:
            equity = 10000.0
        risk_governor.update_equity(equity)
        
        # 1. THE BRAIN: Analyze (Intent Layer)
        analysis_result = intelligence.analyze_market({"symbol": symbol, "equity": equity})
        signal = analysis_result.get("signal", "WAIT")
        
        if signal == "WAIT":
            logger.info("BRAIN_STATUS: NO_SIGNAL_GENERATED")
            return

        # 2. ANCIENT LOGIC: Cycle Check (Intent Layer)
        market_context = {"cycle": "EXPANSION", "signal": signal, "price": 65000}
        cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
        
        if not cycle_ok:
            logger.warning(f"HANDSHAKE_REJECTED: {cycle_msg}")
            return

        # 3. RISK GOVERNOR: Survival Filter (Risk Layer)
        atr_data = {"current_atr": 50, "normal_atr": 45}
        risk_ok, risk_msg = risk_governor.validate_trade(symbol, 0.01, 65000, atr_data)
        
        if not risk_ok:
            logger.warning(f"RISK_REJECTED: {risk_msg}")
            return

        # 4. THE BODY: Execute via ExecutionEngine (Execution Layer)
        # skip_risk_check=True because we already validated above (defense-in-depth)
        logger.info(f"NEXUS_DEPLOYING_ORDER: {signal} 0.01 {symbol}")
        result = engine.execute_trade(
            symbol=symbol,
            side=signal,
            quantity=0.01,
            skip_risk_check=True
        )
        logger.info(f"ORDER_STATUS: {result.status.value} | Order: {result.order_id}")

    except Exception as e:
        logger.error(f"HEARTBEAT_FAILURE: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Every 15 minutes (aligned with M15 candles)
    scheduler.add_job(heartbeat_task, 'interval', minutes=15)
    scheduler.start()
    logger.info("HEARTBEAT_SCHEDULER_ACTIVE. INTERVAL: 15M.")
    return scheduler

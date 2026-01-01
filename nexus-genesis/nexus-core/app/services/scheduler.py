import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services import intelligence, ancient_logic, risk_governor, broker_mt5

logger = logging.getLogger("nexus.heartbeat")

async def heartbeat_task():
    """
    The 15-minute Candle Period Heartbeat.
    1. Wake up Intelligence.
    2. Check Ancient Logic.
    3. Run Risk Governor.
    4. Execute Trade.
    """
    logger.info(f"HEARTBEAT_INITIATED: {datetime.now()}")
    
    try:
        # Mock data for demonstration (In production, fetch real OHLCV from MT5)
        symbol = "BTCUSD"
        account = broker_mt5.get_account_info()
        
        # 0. Sync Governor with Live Equity
        risk_governor.update_equity(account["equity"])
        
        # 1. THE BRAIN: Analyze
        analysis_result = intelligence.analyze_market({"symbol": symbol, "equity": account["equity"]})
        signal = analysis_result.get("signal", "WAIT")
        
        if signal == "WAIT":
            logger.info("BRAIN_STATUS: NO_SIGNAL_GENERATED")
            return

        # 2. ANCIENT LOGIC: Cycle Check
        # Mock cycle for handshake (Production fetches from BigQuery/Intelligence)
        market_context = {"cycle": "EXPANSION", "signal": signal, "price": 65000}
        cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
        
        if not cycle_ok:
            logger.warning(f"HANDSHAKE_REJECTED: {cycle_msg}")
            return

        # 3. RISK GOVERNOR: Survival Filter
        # Mock ATR data
        atr_data = {"current_atr": 50, "normal_atr": 45}
        risk_ok, risk_msg = risk_governor.validate_trade(symbol, 0.01, 65000, atr_data)
        
        if not risk_ok:
            logger.warning(f"RISK_REJECTED: {risk_msg}")
            return

        # 4. THE BODY: Execution
        logger.info(f"NEXUS_DEPLOYING_ORDER: {signal} 0.01 {symbol}")
        order_result = broker_mt5.send_order(symbol, 0.01, signal)
        logger.info(f"ORDER_STATUS: {order_result['status']}")

    except Exception as e:
        logger.error(f"HEARTBEAT_FAILURE: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Every 15 minutes (aligned with M15 candles)
    scheduler.add_job(heartbeat_task, 'interval', minutes=15)
    scheduler.start()
    logger.info("HEARTBEAT_SCHEDULER_ACTIVE. INTERVAL: 15M.")
    return scheduler

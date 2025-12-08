import logging

logger = logging.getLogger("NexusRisk")

class RiskManager:
    """
    The Guardian of Capital.
    Enforces strict risk limits and survival protocols.
    """
    
    def __init__(self):
        self.max_drawdown_percent = 0.05 # 5% Hard Stop
        self.max_exposure_per_asset = 0.10 # 10% of capital
        self.kill_switch_active = False
        self.daily_loss = 0.0
        self.account_info = {}

    def update_account_info(self, info: dict):
        self.account_info = info

    def check_trade(self, decision: dict, account_info: dict) -> bool:
        """
        Validates if a trade is safe to execute.
        """
        if self.kill_switch_active:
            logger.warning("⛔ TRADE BLOCKED: KILL SWITCH ACTIVE")
            return False
            
        if decision['signal'] == "HOLD":
            return True
            
        # Check Drawdown
        balance = account_info.get('balance', 10000)
        equity = account_info.get('equity', 10000)

        # Avoid division by zero
        if balance == 0:
            return False

        drawdown = (balance - equity) / balance
        
        if drawdown > self.max_drawdown_percent:
            logger.critical(f"⛔ TRADE BLOCKED: Max Drawdown Exceeded ({drawdown*100:.2f}%)")
            self.trigger_kill_switch("Max Drawdown Hit")
            return False
            
        return True

    def trigger_kill_switch(self, reason: str):
        self.kill_switch_active = True
        logger.critical(f"💀 KILL SWITCH ENGAGED: {reason}")

        # Attempt to close all positions via MT5 if available
        try:
            import MetaTrader5 as mt5
            # We assume mt5 is initialized in the main thread/bridge
            if mt5.terminal_info() is not None:
                positions = mt5.positions_get()
                if positions:
                    logger.info(f"💀 Closing {len(positions)} open positions...")
                    for pos in positions:
                        # Close logic
                        type_op = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        price = mt5.symbol_info_tick(pos.symbol).bid if type_op == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(pos.symbol).ask

                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": pos.symbol,
                            "volume": pos.volume,
                            "type": type_op,
                            "position": pos.ticket,
                            "price": price,
                            "deviation": 20,
                            "magic": 234000,
                            "comment": "KILL SWITCH EXECUTION",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_IOC,
                        }
                        result = mt5.order_send(request)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            logger.info(f"✅ Closed Position {pos.ticket}")
                        else:
                            logger.error(f"❌ Failed to close {pos.ticket}: {result.comment}")
                else:
                    logger.info("💀 No open positions to close.")
        except ImportError:
            logger.error("❌ MT5 Module not found. Cannot auto-close positions.")
        except Exception as e:
            logger.error(f"❌ KILL SWITCH ERROR: {e}")

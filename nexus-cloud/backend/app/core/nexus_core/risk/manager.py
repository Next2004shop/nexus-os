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
        drawdown = (balance - equity) / balance
        
        if drawdown > self.max_drawdown_percent:
            logger.critical(f"⛔ TRADE BLOCKED: Max Drawdown Exceeded ({drawdown*100:.2f}%)")
            self.trigger_kill_switch("Max Drawdown Hit")
            return False
            
        return True

    def trigger_kill_switch(self, reason: str):
        self.kill_switch_active = True
        logger.critical(f"💀 KILL SWITCH ENGAGED: {reason}")
        # TODO: Close all positions immediately

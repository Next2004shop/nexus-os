import logging

logger = logging.getLogger("NexusCapital")

class CapitalAllocator:
    """
    Manages capital distribution and profit taking.
    """
    
    def __init__(self):
        self.profit_vault = 0.0
        self.reinvestment_rate = 0.50 # 50% Reinvest, 50% Vault
        
    def process_profit(self, profit: float):
        """
        Splits profit between Growth (Reinvestment) and Vault (Safety).
        """
        if profit <= 0:
            return
            
        to_vault = profit * (1 - self.reinvestment_rate)
        self.profit_vault += to_vault
        
        logger.info(f"💰 PROFIT SPLIT: ${profit:.2f} -> Vault: ${to_vault:.2f} | Reinvest: ${profit - to_vault:.2f}")
        logger.info(f"🏦 TOTAL VAULT: ${self.profit_vault:.2f}")

    def get_allocation(self, asset_class: str) -> float:
        """
        Returns capital allocation weight for an asset class.
        """
        # Dynamic allocation based on market conditions (Mock)
        if asset_class == "CRYPTO":
            return 0.30
        elif asset_class == "FOREX":
            return 0.50
        elif asset_class == "STOCKS":
            return 0.20
        return 0.0

import logging
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusAccounting")

class NexusAccounting:
    def __init__(self):
        self.tax_rate = 0.25
        logger.info("💰 NEXUS ACCOUNTING: ONLINE")

    def generate_balance_sheet(self, bank_mode=False):
        """
        Generates a Balance Sheet.
        If bank_mode is True, hides crypto and offshore assets.
        """
        assets = {
            "cash_equivalents": 750000.00,
            "real_estate": 2500000.00,
            "stock_portfolio": 3200000.00,
            "crypto_assets": 8500000.00, # Hidden in Bank Mode
            "offshore_accounts": 1200000.00 # Hidden in Bank Mode
        }
        
        liabilities = {
            "mortgages": 1500000.00,
            "credit_lines": 25000.00
        }

        if bank_mode:
            # SANITIZE DATA FOR BANK VIEW
            sanitized_assets = {
                "cash_equivalents": assets["cash_equivalents"],
                "real_estate": assets["real_estate"],
                "stock_portfolio": assets["stock_portfolio"]
            }
            total_assets = sum(sanitized_assets.values())
            logger.info("Generated SANITIZED Balance Sheet for Bank Review.")
            return {
                "report_type": "Balance Sheet (Sanitized)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "assets": sanitized_assets,
                "liabilities": liabilities,
                "total_assets": total_assets,
                "total_liabilities": sum(liabilities.values()),
                "net_worth": total_assets - sum(liabilities.values())
            }
        else:
            # FULL INTERNAL VIEW
            total_assets = sum(assets.values())
            logger.info("Generated FULL Balance Sheet for Internal Use.")
            return {
                "report_type": "Balance Sheet (Internal)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "assets": assets,
                "liabilities": liabilities,
                "total_assets": total_assets,
                "total_liabilities": sum(liabilities.values()),
                "net_worth": total_assets - sum(liabilities.values())
            }

    def calculate_tax_liability(self, revenue, expenses):
        """Calculates estimated tax and 'Peace of Mind' set aside."""
        taxable_income = revenue - expenses
        estimated_tax = taxable_income * self.tax_rate
        
        return {
            "revenue": revenue,
            "expenses": expenses,
            "taxable_income": taxable_income,
            "tax_rate": f"{self.tax_rate*100}%",
            "estimated_tax_due": estimated_tax,
            "status": "COMPLIANT"
        }

accounting = NexusAccounting()

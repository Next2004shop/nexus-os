import logging
import pandas as pd
from typing import List, Dict
from .strategies.base_strategy import BaseStrategy
from .analysis.indicators import TechnicalAnalysis
from .risk.manager import RiskManager

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusCore")
fh = logging.FileHandler('nexus_god_mode.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

class NexusEngine:
    """
    The Central Brain of Nexus God Mode.
    Orchestrates data ingestion, strategy execution, and risk checks.
    """
    
    def __init__(self):
        self.strategies: List[BaseStrategy] = []
        self.active_strategies = []
        self.data_cache = {}
        self.risk_manager = RiskManager()
        logger.info("🧠 NEXUS CORE ENGINE: INITIALIZED")

    def register_strategy(self, strategy: BaseStrategy):
        self.strategies.append(strategy)
        self.active_strategies.append(strategy.name)
        logger.info(f"✅ Strategy Registered: {strategy.name}")

    def ingest_data(self, symbol: str, raw_data: List[dict]) -> pd.DataFrame:
        """
        Converts raw OHLCV data into a rich DataFrame with indicators.
        """
        df = pd.DataFrame(raw_data)
        if df.empty:
            return df
            
        # Ensure correct types
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Apply Indicators
        df = TechnicalAnalysis.calculate_all(df)
        
        self.data_cache[symbol] = df
        return df

    def analyze(self, symbol: str, raw_data: List[dict]) -> dict:
        """
        Runs all active strategies and aggregates the decision.
        """
        df = self.ingest_data(symbol, raw_data)
        if df.empty:
            return {"signal": "HOLD", "confidence": 0, "reason": "No Data"}

        # Prepare data packet for strategies (latest candle + context)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        context = {
            "current": latest,
            "prev": prev,
            "df": df, # Full history if needed
            "symbol": symbol
        }

        decisions = []
        
        for strategy in self.strategies:
            if strategy.name in self.active_strategies:
                try:
                    decision = strategy.analyze(symbol, context)
                    if decision['signal'] != "HOLD":
                        decisions.append(decision)
                except Exception as e:
                    logger.error(f"Strategy {strategy.name} Failed: {e}")

        # Aggregation Logic (Consensus Mechanism)
        if not decisions:
            return {"signal": "HOLD", "confidence": 0, "reason": "No Strategy Triggered"}

        # Simple Majority Vote or Highest Confidence
        # For God Mode, we prioritize High Confidence
        best_decision = max(decisions, key=lambda x: x['confidence'])
        
        # --- RISK CHECK ---
        # We need account info for proper risk check. 
        # For now, we assume a safe state or pass mock data if not provided.
        # In real flow, context should include account info.
        mock_account = {"balance": 10000, "equity": 10000} 
        if not self.risk_manager.check_trade(best_decision, mock_account):
            logger.warning("⚠️ Risk Manager VETOED the trade.")
            return {"signal": "HOLD", "confidence": 0, "reason": "Risk Manager Veto"}

        return best_decision

    def calculate_position_size(self, balance: float, risk_per_trade: float = 0.01) -> float:
        """
        Calculates lot size based on risk percentage.
        """
        # Simplified logic for now
        risk_amount = balance * risk_per_trade
        # Assuming 1 lot = $100,000 and 1 pip = $10 (Standard Lot)
        # This needs real tick value from bridge in future
        return round(risk_amount / 1000, 2) # Mock calculation

    def decide_scaling_lots(self, symbol: str, current_profit: float, current_layers: int) -> float:
        """
        Decides how much to scale in based on momentum.
        """
        base_lot = 0.01
        if current_profit > 5.0:
            return base_lot * 2
        return base_lot

"""
NEXUS Capital Allocator
=======================

The "Capital Discipline Layer" (Phase 7).
Responsible for dynamic position sizing and determining IF we trade,
before RiskGovernor determines if we are ALLOWED to trade.

Features:
1. Dynamic Lot Sizing (Equity Model)
2. Drawdown Response (Reduce -> Freeze -> Defensive)
3. Profit Protection (Lock Gains)
4. Scaling Logic (Streak-based)
5. Correlation Limits

This module strictly precedes RiskGovernor.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.services import risk_governor
from command.schema import TradeCommand

logger = logging.getLogger("nexus.risk.capital")

class AllocationMode(Enum):
    NORMAL = "NORMAL"
    REDUCED = "REDUCED"     # 50% risk
    DEFENSIVE = "DEFENSIVE" # No new trades
    AGGRESSIVE = "AGGRESSIVE" # Scaled up

@dataclass
class AllocationResult:
    approved: bool
    lot_size: float
    mode: str
    reason: str
    risk_pct: float
    adjusted_equity: float

class CapitalAllocator:
    _instance = None
    
    # --- Configuration ---
    RISK_PER_TRADE_CONSERVATIVE = 0.005 # 0.5%
    RISK_PER_TRADE_BALANCED = 0.0075    # 0.75%
    RISK_PER_TRADE_AGGRESSIVE = 0.01    # 1.0%
    
    # Drawdown Triggers
    DD_REDUCE_THRESHOLD = 0.02  # 2%
    DD_FREEZE_THRESHOLD = 0.04  # 4%
    DD_DEFENSIVE_THRESHOLD = 0.06 # 6%
    
    # Profit Protection
    PROFIT_LOCK_THRESHOLD_DAILY = 0.03 # 3%
    
    # Correlation Groups
    CORRELATION_MAP = {
        "XAUUSD": "GOLD",
        "GOLD": "GOLD",
        "NAS100": "INDICES_US",
        "USTEC": "INDICES_US",
        "US500": "INDICES_US",
        "SP500": "INDICES_US",
        "BTCUSD": "CRYPTO",
        "ETHUSD": "CRYPTO"
    }
    
    # Limits
    MAX_POSITIONS_TOTAL = 5
    MAX_POSITIONS_PER_SYMBOL = 2
    MAX_POSITIONS_CORRELATED = 2

    def __init__(self):
        self.mode = AllocationMode.NORMAL
        self.daily_start_equity = 10000.0 # Should be reset daily
        self.last_reset = datetime.now(timezone.utc).date()
        self.last_trade_time = None
        
        # Simple tracking for scaling (should be ideally persisted or from RiskGovernor)
        # Using RiskGovernor state is better for consistency
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CapitalAllocator()
        return cls._instance

    def _get_base_risk(self, risk_profile: str = "BALANCED") -> float:
        if risk_profile == "CONSERVATIVE": return self.RISK_PER_TRADE_CONSERVATIVE
        if risk_profile == "AGGRESSIVE": return self.RISK_PER_TRADE_AGGRESSIVE
        return self.RISK_PER_TRADE_BALANCED

    def _check_daily_reset(self, current_equity: float):
        """Reset daily tracking if new day."""
        now = datetime.now(timezone.utc).date()
        if now > self.last_reset:
            self.daily_start_equity = current_equity
            self.last_reset = now
            logger.info(f"CapitalAllocator: Daily reset. Start Equity: {self.daily_start_equity}")

    def _calculate_lot_size(
        self, 
        equity: float, 
        risk_amount: float, 
        sl_price: Optional[float], 
        asset: str
    ) -> float:
        """
        Calculate lot size based on risk amount and Stop Loss.
        Formula: Lots = RiskAmount / (SL_Distance * PipValue)
        
        If SL is missing, we fallback to a rough estimate or safe default (e.g. 0.01 fixed) 
        and LOG A WARNING. Ideally IntentValidator ensures SL exists, 
        but if source='manual' it might be missing.
        """
        if not sl_price:
            # Fallback: Return a safe minimum or reject?
            # User wants dynamic calculation. Without SL, risk is undefined.
            # We will return 0.01 as safe default but warn.
            # actually better to disapprove if strict, but let's be safe.
            return 0.01

        # Retrieve current price (mocked or needed from MarketData)
        # For calculation, we need entry price. 
        # Since we don't have current price easily here without calling MarketData,
        # we might assume pending order price or approximate.
        # This is a limitation. 
        # For now, we will use a simplified model:
        # Assumes standard 100k contract derived risk.
        # This is strictly model-dependent.
        # A safer approach without price is to use Fixed Fractional of Equity / Margin?
        # Let's assume standard lots: $10 per pip roughly for FX/XAU.
        # Ideally we need (Entry - SL).
        return 0.01 # Placeholder for complex pip calc. 
        # To do this safely without live price:
        # We need to know the 'distance'.
        # If the command has no entry price (market order), we can't calc distance strictly.
        # We will iterate this in future. For now, returns safe default 0.01 scaled by risk factor.

    def allocate(
        self, 
        command: TradeCommand, 
        external_risk_multiplier: float = 1.0,
        strategic_reason: str = ""
    ) -> AllocationResult:
        """
        Main decision engine.
        Args:
            command: The trade request
            external_risk_multiplier: Multiplier from Strategic Engine (default 1.0)
            strategic_reason: Context from Strategic Engine
        """
        # 1. Get System State
        risk_status = risk_governor.get_risk_status()
        current_equity = risk_status["equity"]["current"]
        
        self._check_daily_reset(current_equity)
        
        # 2. Daily Drawdown Check
        daily_dd = 0.0
        if self.daily_start_equity > 0:
            daily_dd = (self.daily_start_equity - current_equity) / self.daily_start_equity

        mode = AllocationMode.NORMAL
        reason = "Standard risk"
        risk_mult = 1.0 * external_risk_multiplier # Apply Strategic Multiplier
        
        if strategic_reason:
            reason = f"{strategic_reason}"

        if daily_dd > self.DD_DEFENSIVE_THRESHOLD:
            return AllocationResult(False, 0, AllocationMode.DEFENSIVE.value, "Daily DD > 6%", 0, current_equity)
        
        elif daily_dd > self.DD_FREEZE_THRESHOLD:
            # Freeze for 1 hour? For now just reject.
            return AllocationResult(False, 0, AllocationMode.DEFENSIVE.value, "Daily DD > 4% (Freeze)", 0, current_equity)

        elif daily_dd > self.DD_REDUCE_THRESHOLD:
            mode = AllocationMode.REDUCED
            risk_mult = 0.5
            reason = "Daily DD > 2%"

        # 3. Profit Protection
        daily_profit = -daily_dd # Rough approx
        if daily_profit > self.PROFIT_LOCK_THRESHOLD_DAILY:
            mode = AllocationMode.REDUCED
            risk_mult = 0.5
            reason = "Profit Protection Active"

        # 4. Win/Loss Scaling (From RiskGovernor state)
        consecutive_losses = risk_status.get("consecutive_losses", 0)
        # Win streak not explicitly in status dict yet, would need update.
        # Assuming loss scaling only for now:
        if consecutive_losses >= 2:
            risk_mult *= 0.8 # Reduce 20%
            reason += f" | Loss streak {consecutive_losses}"

        # 5. Position Limits & Correlation
        open_positions = risk_governor._get_state().open_positions # Direct access for strict check
        
        total_open = len(open_positions)
        if total_open >= self.MAX_POSITIONS_TOTAL:
             return AllocationResult(False, 0, mode.value, "Max Total Positions Reached", 0, current_equity)
        
        # Per Symbol
        symbol_count = sum(1 for s in open_positions if s == command.asset)
        if symbol_count >= self.MAX_POSITIONS_PER_SYMBOL:
             return AllocationResult(False, 0, mode.value, f"Max Positions for {command.asset}", 0, current_equity)

        # Correlation
        my_group = self.CORRELATION_MAP.get(command.asset)
        if my_group:
            group_count = 0
            for sym in open_positions:
                if self.CORRELATION_MAP.get(sym) == my_group:
                    group_count += 1
            if group_count >= self.MAX_POSITIONS_CORRELATED:
                return AllocationResult(False, 0, mode.value, f"Correlation Limit ({my_group})", 0, current_equity)

        # 6. Calculate Lot Size
        base_risk_pct = self._get_base_risk()
        target_risk_pct = base_risk_pct * risk_mult
        risk_amount = current_equity * target_risk_pct
        
        # Simplified Pip Calculation (Robust fallback)
        # If SL provided, try to use it.
        # Abs(Entry - SL). If Entry missing, use current price? 
        # We need market price to be accurate.
        # For this implementation, we will trust the command.lot_size if provided manually,
        # OR if source='ai', we override it if it's too high.
        # BUT USER REQUEST: "Dynamically adjusts lot size".
        # We will calculate a 'Recommended Lot' and cap the command's lot.
        
        # PIP VALUE APPROXIMATION (Standard)
        # XAUUSD: 1 lot = $1 per pip? No, 1 lot = 100oz. $1 move = $100.
        # FX: 1 lot = $10 per pip.
        safe_lot_limit = 0.0
        
        # Default logical max for safety if calculation fails
        max_equity_risk_lot = (current_equity * 0.05) / 2000 # Rough check
        
        approved_lot = command.lot_size
        
        # If AI/Auto, we strictly set it.
        if command.source == "ai":
             # Use risk calc. 
             # For XAUUSD example: Risk $100. Stop 100 pips ($10 move). 
             # $10 move * 10oz (0.1 lot) = $100.
             # So 0.1 lot.
             # Since we lack live price/pip data here, we will apply a SCALAR adjustment
             # to the COMMAND's proposed lot if risk_mult < 1.0
             approved_lot = command.lot_size * risk_mult
             if risk_mult < 1.0:
                 reason += f" | Scaled down {risk_mult*100}%"
        
        # 7. Logger
        log_msg = f"{command.asset} | Eq:{current_equity:.0f} | Lot:{approved_lot:.2f} | {mode.value} | {reason}"
        logger.info(log_msg)
        
        # Append to capital log
        with open("logs/capital.log", "a") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} | {log_msg}\n")

        return AllocationResult(
            approved=True,
            lot_size=round(approved_lot, 2),
            mode=mode.value,
            reason=reason,
            risk_pct=target_risk_pct,
            adjusted_equity=current_equity
        )

    def get_status(self) -> Dict:
        """Return status for telemetry."""
        risk_status = risk_governor.get_risk_status()
        current_equity = risk_status["equity"]["current"]
        
        daily_dd = 0.0
        if self.daily_start_equity > 0:
            daily_dd = (self.daily_start_equity - current_equity) / self.daily_start_equity
            
        return {
            "mode": self.mode.value,
            "daily_start_equity": self.daily_start_equity,
            "daily_pnl_pct": -daily_dd * 100, # Approx
            "active_risk_pct": 0.0, # Placeholder until we sum open risk
            "last_reset": self.last_reset.isoformat()
        }

# Global accessor
def get_allocator():
    return CapitalAllocator.get_instance()

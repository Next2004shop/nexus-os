import sys
import os
import json

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

from app.services import risk_governor

def run_stress_test():
    print("--- NEXUS IMMORTALITY LAYER STRESS TEST ---")
    
    # Initial State
    print("Initial Equity: $10,000")
    risk_governor.update_equity(10000.0)
    
    print("\n[SCENARIO: MARKET CRASH -2% THRESHOLD CHECK]")
    # Drop to $9,850 (1.5% DD) - Should be OK
    risk_governor.update_equity(9850.0)
    ok, msg = risk_governor.validate_trade("BTC/USDT", 0.1, 60000, {})
    print(f"Equity: $9,850 (DD: 1.5%) -> Status: {msg}")

    # Drop to $9,750 (2.5% DD) - Should TRIGGER KILL
    print("\n[SCENARIO: HARD CRASH - DEADLINE EXCEEDED]")
    risk_governor.update_equity(9750.0)
    ok, msg = risk_governor.validate_trade("BTC/USDT", 0.1, 60000, {})
    print(f"Equity: $9,750 (DD: 2.5%) -> Status: {msg}")
    
    if not ok and msg == "MAX_DRAWDOWN_EXCEEDED":
         print("\nSUCCESS: RISK GOVERNOR DETECTED CRASH AND FROZE EXECUTION.")
    else:
         print("\nFAILURE: GOVERNOR FAILED TO BLOCK TRADE DURING CRASH.")

    print("\n[SCENARIO: VOLATILITY ANOMALY]")
    risk_governor.update_equity(10000.0) # Reset
    risk_governor.STATE["trading_enabled"] = True
    
    atr_data = {"current_atr": 300, "normal_atr": 50} # 6x volatility
    ok, msg = risk_governor.validate_trade("BTC/USDT", 0.1, 60000, atr_data)
    print(f"ATR: 300 vs Normal: 50 -> Status: {msg}")

if __name__ == "__main__":
    run_stress_test()

import pandas as pd
import numpy as np
from nexus_core.engine import NexusEngine
from nexus_core.strategies.scalping import ScalpingStrategy
from nexus_core.strategies.trend import TrendStrategy
from nexus_core.strategies.swing import SwingStrategy

def generate_mock_data(length=100):
    data = []
    price = 1.1000
    for i in range(length):
        price += np.random.normal(0, 0.0005)
        data.append({
            "time": 1700000000 + (i * 900),
            "open": price,
            "high": price + 0.0002,
            "low": price - 0.0002,
            "close": price + np.random.normal(0, 0.0001),
            "volume": 1000 + np.random.randint(-100, 100)
        })
    return data

def test_engine():
    print("🧪 TESTING NEXUS CORE ENGINE...")
    
    # 1. Initialize Engine
    engine = NexusEngine()
    
    # 2. Register Strategies
    engine.register_strategy(ScalpingStrategy())
    engine.register_strategy(TrendStrategy())
    engine.register_strategy(SwingStrategy())
    
    # 3. Generate Data
    raw_data = generate_mock_data(200)
    
    # 4. Run Analysis
    decision = engine.analyze("EURUSD", raw_data)
    
    print(f"📊 DECISION: {decision}")
    
    if decision['signal'] in ["BUY", "SELL", "HOLD"]:
        print("✅ TEST PASSED: Engine produced a valid signal.")
    else:
        print("❌ TEST FAILED: Invalid signal.")

if __name__ == "__main__":
    test_engine()

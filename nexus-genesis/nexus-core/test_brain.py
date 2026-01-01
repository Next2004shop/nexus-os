import sys
import os
import json

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

from app.services import intelligence

def run_ignition_test():
    print("--- NEXUS BRAIN IGNITION TEST ---")
    print("Targeting: Claude-3.5-Haiku via Vertex AI")
    
    # Sample OHLCV-style mock data
    mock_data = {
        "symbol": "BTC/USDT",
        "regime": "Expansionary",
        "last_5_candles": [
            {"o": 65000, "h": 65500, "l": 64900, "c": 65400, "v": 120},
            {"o": 65400, "h": 65800, "l": 65300, "c": 65700, "v": 150},
            {"o": 65700, "h": 65750, "l": 65200, "c": 65300, "v": 90},
            {"o": 65300, "h": 65900, "l": 65200, "c": 65850, "v": 200},
            {"o": 65850, "h": 66200, "l": 65800, "c": 66100, "v": 180}
        ]
    }

    try:
        print("Sending data to The Eye...")
        result = intelligence.analyze_market(mock_data)
        
        print("\n[VERDICT RECEIVED]")
        print(json.dumps(result, indent=4))
        
        if "signal" in result:
            print(f"\nSTATUS: 100% ACTIVE. SIGNAL: {result['signal']}")
        else:
            print("\nSTATUS: RESPONSE RECEIVED BUT MALFORMED.")
            
    except Exception as e:
        print(f"\nIGNITION FAILED: {e}")

if __name__ == "__main__":
    run_ignition_test()

import requests
import json

url = "http://localhost:5001/predict"
headers = {
    "X-API-KEY": "nexus-local-key-123",
    "Content-Type": "application/json"
}
data = {
    "asset": "BTCUSD",
    "timeframe": "M15",
    "mode": "Hunter"
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
# api_key = os.getenv("VITE_GEMINI_API_KEY").strip()
api_key = "AIzaSyBet7k0Q9UKxjXKj3uFHH173Aehmb-2yhk"

print(f"Testing Key Length: {len(api_key)}")
print(f"Testing Key Repr: {repr(api_key)}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/text-bison-001:generateText?key={api_key}"
headers = {'Content-Type': 'application/json'}
data = {
    "prompt": {"text": "Hello"}
}

response = requests.post(url, headers=headers, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

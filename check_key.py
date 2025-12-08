import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
api_key = os.getenv("VITE_GEMINI_API_KEY")

print(f"Checking Key: {api_key[:5]}...")
genai.configure(api_key=api_key)

try:
    print("Listing models...")
    for m in genai.list_models():
        print(f" - {m.name}")
    print("Key is VALID ✅")
except Exception as e:
    print(f"Key is INVALID ❌: {e}")

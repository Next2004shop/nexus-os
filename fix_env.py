key = "OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE"
with open(".env.local", "w", encoding="utf-8") as f:
    f.write(key)
print("Wrote .env.local with OpenAI Key")

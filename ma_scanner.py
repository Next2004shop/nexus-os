import feedparser
import openai
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")

def init_ai():
    """Initializes OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env.local")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"Failed to initialize OpenAI: {e}")
        return None

def fetch_financial_news():
    """Fetches financial news from RSS feeds."""
    rss_urls = [
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.content.dowjones.com/public/rss/mw_topstories",
        "http://feeds.marketwatch.com/marketwatch/topstories/"
    ]
    
    news_items = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]: # Limit to top 10 per feed
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": getattr(entry, "summary", ""),
                    "published": getattr(entry, "published", str(datetime.now()))
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            
    return news_items

def analyze_opportunities(news_items):
    """Analyzes news items for M&A signals using OpenAI GPT-4o."""
    client = init_ai()
    if not client:
        return []
    
    opportunities = []
    
    system_prompt = """
    You are an expert financial analyst specializing in Mergers and Acquisitions (M&A).
    Your job is to analyze news headlines and summaries to identify potential M&A activity.
    Look for keywords like "buyout", "acquisition", "merger", "takeover", "exploring sale", "strategic alternatives".
    
    For each potential opportunity, return a JSON object with:
    - target_company: Name of the company being bought or sold
    - target_ticker: The stock ticker symbol of the target (e.g., "PTON", "RIVN"). If unknown, use null.
    - acquirer: Name of the potential buyer (if known, else "Unknown")
    - likelihood_score: 0-100 confidence score
    - reasoning: Brief explanation of why this is an opportunity
    - source_title: The headline used
    
    Return a JSON list of these objects. If no opportunities are found, return an empty list [].
    Ensure the output is valid JSON.
    """
    
    chunk_size = 5
    for i in range(0, len(news_items), chunk_size):
        chunk = news_items[i:i+chunk_size]
        chunk_text = "\n".join([f"- Title: {item['title']}\n  Summary: {item['summary']}" for item in chunk])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o", # Or gpt-3.5-turbo if preferred
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze these news items:\n{chunk_text}"}
                ],
                response_format={"type": "json_object"}
            )
            
            text_response = response.choices[0].message.content
            
            try:
                # OpenAI json_object mode returns a dict, usually {"opportunities": [...]} or just the list if prompted well.
                # We'll try to parse it flexibly.
                data = json.loads(text_response)
                
                results = []
                if isinstance(data, list):
                    results = data
                elif isinstance(data, dict):
                    # Check for common keys
                    for key in ["opportunities", "results", "items"]:
                        if key in data and isinstance(data[key], list):
                            results = data[key]
                            break
                    # If no list found, maybe the dict itself is a single result? Unlikely with current prompt.
                
                for res in results:
                    # Find original link
                    for item in chunk:
                        if item['title'] == res.get('source_title'):
                            res['link'] = item['link']
                            break
                    opportunities.extend(results)
                    
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from AI response: {text_response}")
                
        except Exception as e:
            print(f"Error analyzing chunk: {e}")
            import traceback
            traceback.print_exc()
            
    return opportunities

def generate_mock_opportunities():
    """Generates fake M&A opportunities for demo purposes."""
    return [
        {
            "target_company": "Peloton Interactive",
            "target_ticker": "PTON",
            "acquirer": "Apple Inc.",
            "likelihood_score": 85,
            "reasoning": "Apple looking to expand Apple Fitness+ ecosystem with hardware integration. Peloton's valuation has dropped significantly, making it an attractive target.",
            "source_title": "Apple Exploring Strategic Acquisition in Fitness Space",
            "link": "https://finance.yahoo.com/news/mock-apple-peloton"
        },
        {
            "target_company": "Rivian Automotive",
            "target_ticker": "RIVN",
            "acquirer": "Amazon",
            "likelihood_score": 72,
            "reasoning": "Amazon already owns a large stake and could look to fully integrate Rivian for its logistics fleet and consumer EV push.",
            "source_title": "Amazon Rumored to Increase Stake in Rivian",
            "link": "https://www.marketwatch.com/mock-amazon-rivian"
        },
        {
            "target_company": "Electronic Arts (EA)",
            "target_ticker": "EA",
            "acquirer": "Disney",
            "likelihood_score": 60,
            "reasoning": "Disney CEO hinting at deeper gaming integration. EA's IP library matches well with Disney's franchise strategy.",
            "source_title": "Disney CEO Iger Comments on Gaming Strategy",
            "link": "https://www.bloomberg.com/mock-disney-ea"
        }
    ]

if __name__ == "__main__":
    print("Fetching news...")
    news = fetch_financial_news()
    print(f"Found {len(news)} articles.")
    
    print("Analyzing for M&A opportunities (OpenAI)...")
    opps = analyze_opportunities(news)
    
    print(json.dumps(opps, indent=2))

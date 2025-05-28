from fastapi import FastAPI, Request
import pandas as pd
import numpy as np
import logging
import re
app = FastAPI()
logging.basicConfig(level=logging.INFO)

def is_asia_tech(ticker):
    """Identify Asia tech tickers based on known exchanges or patterns."""
    asia_exchanges = [".KS", ".TW", ".HK"]  # Korean, Taiwan, Hong Kong exchanges
    return any(ticker.endswith(ext) for ext in asia_exchanges)

def analyze_earnings_snippet(snippet):
    """Extract earnings surprises from news snippets with percentage detection."""
    snippet = snippet.lower()
    if "beat" in snippet:
        match = re.search(r"beat.*by\s*(\d+\.?\d*%)", snippet)
        return f"beat earnings estimates by {match.group(1)}" if match else "beat earnings estimates"
    elif "miss" in snippet:
        match = re.search(r"miss.*by\s*(\d+\.?\d*%)", snippet)
        return f"missed earnings estimates by {match.group(1)}" if match else "missed earnings estimates"
    return "no earnings data"

def compute_aum_allocation(api_data, tickers, query):
    """Calculate AUM allocation for Asia tech stocks if relevant."""
    if "asia tech" not in query.lower():
        return "N/A"
    
    total_aum = 100  # Simplified total AUM
    allocation = 0
    asia_tech_tickers = [t for t in tickers if is_asia_tech(t)]
    
    if not asia_tech_tickers:
        logging.info("[Analysis Agent] No Asia tech tickers found")
        return "0% of AUM, no Asia tech stocks identified"
    
    for ticker in asia_tech_tickers:
        if ticker in api_data and "error" not in api_data.get(ticker, {}):
            try:
                latest_close = api_data[ticker][-1]["Close"]
                allocation += latest_close * 0.1  # Simplified weighting
            except (IndexError, KeyError) as e:
                logging.error(f"[Analysis Agent] Error processing {ticker}: {e}")
                continue
    percentage = (allocation / total_aum) * 100
    previous_percentage = percentage - 0.5 if percentage > 0 else 0  # Simulated change
    direction = "up" if percentage > previous_percentage else "down"
    result = f"{percentage:.1f}% of AUM, {direction} from {previous_percentage:.1f}%"
    logging.info(f"[Analysis Agent] AUM allocation: {result}")
    return result

@app.post("/analyze")
async def analyze_data(request: Request):
    body = await request.json()
    api_data = body.get("api_data", {})
    scrape_data = body.get("scrape_data", {})
    tickers = body.get("tickers", [])
    query = body.get("query", "")

    if not tickers:
        logging.error("[Analysis Agent] No tickers provided")
        return {"error": "No tickers provided"}

    # Compute AUM allocation
    aum_allocation = compute_aum_allocation(api_data, tickers, query)

    # Analyze earnings surprises
    earnings = {}
    for ticker in tickers:
        snippets = [item["snippet"] for item in scrape_data.get(ticker, [])]
        earnings[ticker] = analyze_earnings_snippet(" ".join(snippets))

    # Simplified sentiment analysis
    sentiment = "neutral with a cautionary tilt" if any("miss" in e.lower() for e in earnings.values()) else "neutral"
    logging.info(f"[Analysis Agent] Sentiment: {sentiment}")

    return {
        "aum": aum_allocation,
        "earnings": earnings,
        "sentiment": sentiment
    }
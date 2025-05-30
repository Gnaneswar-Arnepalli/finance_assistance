from fastapi import FastAPI, Request
import pandas as pd
import numpy as np
import logging
import re

app = FastAPI()
logging.basicConfig(level=logging.INFO)

def is_asia_tech(ticker):
    asia_exchanges = [".KS", ".TW", ".HK"]
    return any(ticker.endswith(ext) for ext in asia_exchanges)

def analyze_earnings_snippet(snippet):
    snippet = snippet.lower()
    if "beat" in snippet:
        match = re.search(r"beat.*by\s*(\d+\.?\d*%)", snippet)
        return f"beat earnings estimates by {match.group(1)}" if match else "beat earnings estimates"
    elif "miss" in snippet:
        match = re.search(r"miss.*by\s*(\d+\.?\d*%)", snippet)
        return f"missed earnings estimates by {match.group(1)}" if match else "missed earnings estimates"
    return "no earnings data"

def compute_aum_allocation(api_data, tickers, query):
    if "asia tech" not in query.lower():
        return {"percentage": "N/A", "change": "N/A", "direction": "N/A"}

    # Assume a hypothetical portfolio of $1M
    total_portfolio_value = 1_000_000
    allocation = 0
    asia_tech_tickers = [t for t in tickers if is_asia_tech(t)]

    if not asia_tech_tickers:
        logging.info("[Analysis Agent] No Asia tech tickers found")
        return {"percentage": "0%", "change": "0%", "direction": "N/A"}

    total_volume = 0
    for ticker in asia_tech_tickers:
        if ticker in api_data and api_data[ticker] and "error" not in api_data.get(ticker, {}):
            try:
                latest_data = api_data[ticker][-1]
                volume = latest_data["Volume"]
                total_volume += volume
            except (IndexError, KeyError) as e:
                logging.error(f"[Analysis Agent] Error processing {ticker}: {e}")
                continue

    if total_volume == 0:
        return {"percentage": "0%", "change": "0%", "direction": "N/A"}

    for ticker in asia_tech_tickers:
        if ticker in api_data and api_data[ticker] and "error" not in api_data.get(ticker, {}):
            try:
                latest_data = api_data[ticker][-1]
                volume = latest_data["Volume"]
                # Allocate based on volume proportion
                allocation += (volume / total_volume) * total_portfolio_value * 0.1  # 10% of portfolio to Asia tech
            except (IndexError, KeyError) as e:
                logging.error(f"[Analysis Agent] Error processing {ticker}: {e}")
                continue

    percentage = (allocation / total_portfolio_value) * 100
    # Simulate a small previous change for demonstration
    previous_percentage = max(0, percentage - 0.3)
    direction = "up" if percentage > previous_percentage else "down"
    result = {
        "percentage": f"{percentage:.1f}%",
        "change": f"{percentage - previous_percentage:.1f}%",
        "direction": direction
    }
    logging.info(f"[Analysis Agent] AUM allocation: {result}")
    return result

def compute_sentiment(api_data, earnings, tickers):
    sentiment_score = 0
    for ticker in tickers:
        # Check earnings
        if "miss" in earnings.get(ticker, "").lower():
            sentiment_score -= 1
        elif "beat" in earnings.get(ticker, "").lower():
            sentiment_score += 1
        # Check price movement
        if ticker in api_data and api_data[ticker] and len(api_data[ticker]) >= 2:
            try:
                latest_close = api_data[ticker][-1]["Close"]
                previous_close = api_data[ticker][-2]["Close"]
                change_percent = ((latest_close - previous_close) / previous_close) * 100
                if change_percent < -2:
                    sentiment_score -= 1
                elif change_percent > 2:
                    sentiment_score += 1
            except (IndexError, KeyError):
                continue

    if sentiment_score < 0:
        return "negative"
    elif sentiment_score > 0:
        return "positive"
    else:
        return "neutral"

@app.get("/health")
async def health():
    return {"status": "Analysis Agent is running"}

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

    aum_allocation = compute_aum_allocation(api_data, tickers, query)
    earnings = {}
    for ticker in tickers:
        # Check if API data includes earnings
        if ticker in api_data and "earnings" in api_data[ticker]:
            earnings[ticker] = api_data[ticker]["earnings"]
        else:
            snippets = [item["snippet"] for item in scrape_data.get(ticker, [])]
            earnings[ticker] = analyze_earnings_snippet(" ".join(snippets))

    sentiment = compute_sentiment(api_data, earnings, tickers)
    logging.info(f"[Analysis Agent] Sentiment: {sentiment}")

    return {
        "aum": aum_allocation,
        "earnings": earnings,
        "sentiment": sentiment
    }
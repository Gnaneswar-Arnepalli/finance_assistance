# agents/api_agent.py
import yfinance as yf
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.post("/run")
async def run(tickers: dict):
    tickers_list = tickers.get("tickers", [])
    stock_data = {}
    for ticker in tickers_list:
        try:
            stock = yf.Ticker(ticker)
            # Fetch the latest available data (intraday or last close)
            hist = stock.history(period="5d")  # Last 5 days to ensure we get May 29
            if not hist.empty:
                latest_data = hist.iloc[-1]  # Get the most recent row
                stock_data[ticker] = [
                    {
                        "Date": str(latest_data.name.date()),
                        "Open": latest_data["Open"],
                        "High": latest_data["High"],
                        "Low": latest_data["Low"],
                        "Close": latest_data["Close"],
                        "Volume": latest_data["Volume"],
                    }
                ]
            else:
                stock_data[ticker] = []
        except Exception as e:
            stock_data[ticker] = []
    return stock_data
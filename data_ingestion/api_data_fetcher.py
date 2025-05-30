import os
import yfinance as yf
import pandas as pd
import requests
from dotenv import load_dotenv
import logging

load_dotenv()
ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
logging.basicConfig(level=logging.INFO)

def get_stock_data_yfinance(tickers, period="5d"):
    """
    Get stock data using yfinance for multiple tickers.
    Returns dictionary with cleaned data.
    """
    try:
        if not tickers:
            return {"error": "No tickers provided"}
        joined_tickers = " ".join(tickers)
        data = yf.download(joined_tickers, period=period, group_by="ticker", auto_adjust=True)

        result = {}
        if isinstance(data.columns, pd.MultiIndex):
            for ticker in tickers:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].copy().fillna(0).replace([float("inf"), float("-inf")], 0)
                    result[ticker] = df.reset_index().to_dict(orient="records")
                else:
                    result[ticker] = {"error": f"No data found for {ticker}"}
        else:
            df = data.copy().fillna(0).replace([float("inf"), float("-inf")], 0)
            result[tickers[0]] = df.reset_index().to_dict(orient="records")

        logging.info(f"[YFinance] Successfully fetched data for {tickers}")
        return result
    except Exception as e:
        logging.error(f"[YFinance Error] {e}")
        return {ticker: {"error": f"YFinance failed: {e}"} for ticker in tickers}

def get_stock_data_alphavantage(ticker, outputsize="compact"):
    """
    Get stock data using Alpha Vantage for a single ticker.
    Returns JSON-safe dictionary of daily data.
    """
    try:
        url = (
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED"
            f"&symbol={ticker}&outputsize={outputsize}&apikey={ALPHA_API_KEY}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Time Series (Daily)" not in data:
            return {"error": "AlphaVantage returned no data"}

        daily_data = data["Time Series (Daily)"]
        formatted_data = [
            {
                "Date": date,
                "Open": float(info["1. open"]),
                "High": float(info["2. high"]),
                "Low": float(info["3. low"]),
                "Close": float(info["4. close"]),
                "Volume": float(info["6. volume"]),
            }
            for date, info in daily_data.items()
        ]

        logging.info(f"[AlphaVantage] Successfully fetched data for {ticker}")
        return list(reversed(formatted_data))[:1]  # Return only the latest day
    except Exception as e:
        logging.error(f"[AlphaVantage Error for {ticker}] {e}")
        return {"error": f"AlphaVantage failed: {e}"}

def get_multiple_stocks_data(tickers, period="5d", fallback_to_alpha=True):
    """
    Attempts to fetch from YFinance first, falls back to AlphaVantage if enabled.
    """
    if not tickers:
        return {"error": "No tickers provided"}

    yf_data = get_stock_data_yfinance(tickers, period)
    failed_tickers = [t for t in tickers if "error" in yf_data.get(t, {})]

    if not failed_tickers:
        return yf_data

    if fallback_to_alpha:
        alpha_data = {}
        for ticker in failed_tickers:
            data = get_stock_data_alphavantage(ticker)
            alpha_data[ticker] = data
        # Merge yfinance and Alpha Vantage data
        for ticker in tickers:
            if ticker in alpha_data and "error" not in alpha_data[ticker]:
                yf_data[ticker] = alpha_data[ticker]
        return yf_data
    else:
        return {"error": "YFinance failed and fallback disabled."}
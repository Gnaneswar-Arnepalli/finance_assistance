# api_data_fetcher.py
import yfinance as yf
import pandas as pd

def get_multiple_stocks_data(tickers=["TSLA", "TSM", "005930.KS"], period="5d"):
    """
    Fetch and return cleaned historical data for multiple stocks.

    Returns:
        dict: JSON-safe dict with cleaned data
    """
    try:
        joined_tickers = " ".join(tickers)
        data = yf.download(joined_tickers, period=period, group_by='ticker')

        # Handle single ticker edge case
        if isinstance(data.columns, pd.MultiIndex):
            result = {}
            for ticker in tickers:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].copy()
                    df = df.fillna(0).replace([float('inf'), float('-inf')], 0)
                    result[ticker] = df.reset_index().to_dict(orient="records")
                else:
                    result[ticker] = {"error": f"No data found for {ticker}"}
            return result
        else:
            # Single ticker fallback
            df = data.copy()
            df = df.fillna(0).replace([float('inf'), float('-inf')], 0)
            return {tickers[0]: df.reset_index().to_dict(orient="records")}

    except Exception as e:
        return {"error": f"Exception during fetch: {str(e)}"}

import yfinance as yf

def get_multiple_stocks_data(tickers=["TSLA", "TSM", "005930.KS"], period="5y"):
    """
    Fetch historical data for multiple stocks at once.

    Args:
        tickers (list): List of ticker symbols.
        period (str): Period like '5y'.

    Returns:
        dict: Dictionary with ticker as key and historical data as nested dict.
    """
    try:
        joined_tickers = " ".join(tickers)
        data = yf.download(joined_tickers, period=period, group_by='ticker')
        return data.to_dict()
    except Exception as e:
        print(f"Error fetching data for tickers {tickers}: {e}")
        return {}

# Test run
if __name__ == "__main__":
    tickers = ["TSLA", "TSM", "005930.KS"]  # Tesla, TSMC, Samsung
    result = get_multiple_stocks_data(tickers)
    for key in list(result.keys())[:3]:
        print(f"{key}: {list(result[key].items())[:1]}")  # Show just one row per key

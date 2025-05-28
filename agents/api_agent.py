from fastapi import FastAPI, Request
from data_ingestion.api_data_fetcher import get_multiple_stocks_data

app = FastAPI()

@app.get("/run")
def run_api_agent():
    tickers = ["TSLA", "AAPL", "005930.KS", "TSM"]  # Add more as needed
    return get_multiple_stocks_data(tickers)
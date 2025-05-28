from fastapi import FastAPI, Request
from data_ingestion.api_data_fetcher import get_multiple_stocks_data

app = FastAPI()

@app.post("/run")
async def run_api_agent(request: Request):
    body = await request.json()
    tickers = body.get("tickers", [])
    if not tickers:
        return {"error": "No tickers provided"}
    return get_multiple_stocks_data(tickers)
from fastapi import FastAPI
from data_ingestion.api_data_fetcher import get_stock_data

app = FastAPI()

@app.get("/run")
def run_agent():
    return get_stock_data("TSLA")
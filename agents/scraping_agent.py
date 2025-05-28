from fastapi import FastAPI, Request
from data_ingestion.scraper import scrape_stocks_news

app = FastAPI()

@app.get("/run")
def run_scraping_agent():
    tickers = ["TSLA", "AAPL", "005930.KS", "TSM"]
    result = scrape_stocks_news(tickers)
    return {"articles": result}

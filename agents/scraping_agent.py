from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import requests
import logging
import re

app = FastAPI()
logging.basicConfig(level=logging.INFO)

def is_valid_ticker(ticker):
    """Validate ticker format."""
    invalid_patterns = [r"^\^", r"\.SA$", r"\.F$", r"\.SG$", r"\.DU$"]
    return ticker and not any(re.match(pattern, ticker) for pattern in invalid_patterns)

@app.post("/run")
async def scrape_news(request: Request):
    body = await request.json()
    tickers = body.get("tickers", [])
    articles = {}

    for ticker in tickers:
        if not is_valid_ticker(ticker):
            logging.warning(f"[Scraping Agent] Skipping invalid ticker: {ticker}")
            continue
        try:
            logging.info(f"📥 Scraping news for: {ticker}")
            url = f"https://finance.yahoo.com/quote/{ticker}/news/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('h3', class_='Mb(5px)')
            ticker_articles = []
            for item in news_items[:3]:  # Limit to top 3 articles
                link = item.find('a')
                if link and link['href']:
                    full_url = f"https://finance.yahoo.com{link['href']}" if link['href'].startswith('/') else link['href']
                    if not full_url.startswith("https://finance.yahoo.com"):
                        continue
                    try:
                        article_response = requests.get(full_url, headers=headers, timeout=5)
                        article_response.raise_for_status()
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        content = article_soup.find('div', class_='caas-body')
                        snippet = content.get_text(strip=True)[:200] + "..." if content else "No content available."
                        ticker_articles.append({"url": full_url, "snippet": snippet})
                    except Exception as e:
                        logging.error(f"[Scrape Error for {full_url}] {e}")
            articles[ticker] = ticker_articles
        except Exception as e:
            logging.error(f"[Yahoo News Error for {ticker}] {e}")
            articles[ticker] = [{"url": None, "snippet": f"Error: {e}"}]

    return {"articles": articles}
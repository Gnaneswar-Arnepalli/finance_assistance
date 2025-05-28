import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from retrying import retry
import logging
import pickle
import os

logging.basicConfig(level=logging.INFO)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_yahoo_finance_news_articles(ticker, max_articles=3):
    """
    Scrapes Yahoo Finance news URLs related to a given ticker.
    """
    base_url = f"https://finance.yahoo.com/quote/{ticker}/news"
    headers = {'User-Agent': 'Mozilla/5.0'}
    articles = []

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for a_tag in soup.select("a[href*='/news/']"):
            href = a_tag.get("href")
            if not href:
                continue

            full_url = urljoin("https://finance.yahoo.com", href)
            if (ticker.lower() in full_url.lower() and
                "/news/" in full_url and
                not any(ex in full_url.lower() for ex in ["signup", "email", "privacy", "terms"]) and
                full_url not in articles):
                articles.append(full_url)

            if len(articles) >= max_articles:
                break

        return articles
    except Exception as e:
        logging.error(f"[Yahoo News Error for {ticker}] {e}")
        return []

def scrape_article_text(url):
    """
    Scrapes and returns cleaned text content from a news article.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        if not text or len(text) < 100:
            return "⚠️ Content too short or unavailable"

        return text[:500] + "..." if len(text) > 500 else text
    except Exception as e:
        logging.error(f"[Scrape Error] {e}")
        return f"Error scraping {url}: {e}"

def scrape_stocks_news(tickers):
    """
    Retrieves news article URLs and summaries for multiple tickers.
    """
    if not tickers:
        return {"error": "No tickers provided"}

    cache_file = "news_cache.pkl"
    all_news = {}

    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            all_news = pickle.load(f)

    for ticker in tickers:
        logging.info(f"📥 Scraping news for: {ticker}")
        urls = get_yahoo_finance_news_articles(ticker)
        if not urls:
            all_news[ticker] = [{"url": None, "snippet": "⚠️ No articles found."}]
            continue

        snippets = []
        for url in urls:
            snippet = scrape_article_text(url)
            snippets.append({"url": url, "snippet": snippet})

        all_news[ticker] = snippets

    with open(cache_file, "wb") as f:
        pickle.dump(all_news, f)

    return all_news
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

def get_yahoo_finance_news_articles(ticker, max_articles=3):
    base_url = f"https://finance.yahoo.com/quote/{ticker}/news"
    headers = {'User-Agent': 'Mozilla/5.0'}
    articles = []

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a_tag in soup.select("a[href*='/news/']"):
            href = a_tag['href']
            full_url = urljoin("https://finance.yahoo.com", href)
            if ticker.lower() in full_url.lower() and full_url not in articles:
                articles.append(full_url)
            if len(articles) >= max_articles:
                break
        return articles
    except Exception as e:
        return []

def scrape_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))
        return text[:400] + '...' if text else 'No meaningful content'
    except Exception as e:
        return f"Error: {e}"

def scrape_stocks_news(tickers):
    news_result = {}
    for ticker in tickers:
        urls = get_yahoo_finance_news_articles(ticker)
        snippets = [scrape_article_text(url) for url in urls]
        news_result[ticker] = list(zip(urls, snippets))
    return news_result
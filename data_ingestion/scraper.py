import requests
from bs4 import BeautifulSoup

def get_latest_headlines(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.strip() for h in soup.find_all('h2') if h.text.strip()]
        return headlines[:5]
    except Exception as e:
        print(f"Failed to fetch headlines from {url}: {e}")
        return []

def scrape_full_article_text(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text(strip=True) for p in paragraphs)
        return content
    except Exception as e:
        print(f"Failed to scrape full text from {url}: {e}")
        return ""

def scrape_multiple_companies(urls: dict):
    """
    Scrape headlines and full text for multiple companies.

    Args:
        urls (dict): Dictionary with {ticker: url}
    """
    for ticker, url in urls.items():
        print(f"\n=== {ticker} ===")
        
        headlines = get_latest_headlines(url)
        print("📰 Headlines:")
        for i, headline in enumerate(headlines, 1):
            print(f"{i}. {headline}")
        
        full_text = scrape_full_article_text(url)
        print(f"\n📄 Article Snippet (first 300 characters):\n{full_text[:300]}...")

# Run test
if __name__ == "__main__":
    stock_urls = {
        "TSM": "https://finance.yahoo.com/quote/TSM?p=TSM",
        "005930.KS": "https://finance.yahoo.com/quote/005930.KS?p=005930.KS",  # Samsung
        "AAPL": "https://finance.yahoo.com/quote/AAPL?p=AAPL",  # Apple
        "TSLA": "https://finance.yahoo.com/quote/TSLA?p=TSLA",  # Tesla
    }

    scrape_multiple_companies(stock_urls)

# document_loader.py

import requests
from bs4 import BeautifulSoup
from typing import List

def load_article_text_from_urls(urls: List[str]) -> List[str]:
    """
    Fetch and extract text from list of article URLs.

    Args:
        urls (List[str]): List of article URLs.

    Returns:
        List[str]: List of article text chunks.
    """
    all_chunks = []

    for url in urls:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # Basic sanitization
            if any(bad in text.lower() for bad in ["enable js", "internal server error", "please enable"]):
                print(f"⚠️ Possibly JS-blocked or invalid content: {url}")
                continue

            if len(text) > 300:
                all_chunks.append(text)
                print(f"✅ Extracted from: {url}")
            else:
                print(f"⚠️ Too little content in: {url}")

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")

    return all_chunks

# Test run
if __name__ == "__main__":
    article_urls = [
        "https://www.reuters.com/technology/apple-unveils-new-ai-features-2024-06-10/",  # Likely JS-blocked
        "https://www.bbc.com/news/technology-68935618",  # Works
        "https://techcrunch.com/2024/06/10/apple-wwdc-ai-overview/"  # Works
    ]
    chunks = load_article_text_from_urls(article_urls)

    print(f"\n📰 Loaded {len(chunks)} articles")
    if chunks:
        print("\n🧾 Preview of first article:\n", chunks[0][:500])

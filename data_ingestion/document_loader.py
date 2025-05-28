import requests
from bs4 import BeautifulSoup
from typing import List
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384
index = faiss.IndexFlatL2(dimension)
metadata = []

def scrape_article_text(url: str, min_length: int = 300) -> str:
    """
    Scrapes article text from a URL using BeautifulSoup.
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        if any(term in text.lower() for term in ["enable js", "internal server error", "please enable"]):
            logging.warning(f"⚠️ JS-blocked or invalid content: {url}")
            return ""

        if len(text) < min_length:
            logging.warning(f"⚠️ Insufficient content: {url}")
            return ""

        logging.info(f"✅ Scraped: {url}")
        return text
    except Exception as e:
        logging.error(f"❌ Error scraping {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """
    Splits the text into chunks of given size (by word count).
    """
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def index_documents_from_urls(urls: List[str]):
    """
    Scrapes and indexes documents from a list of URLs.
    """
    global metadata
    for url in urls:
        article = scrape_article_text(url)
        if not article:
            continue
        chunks = chunk_text(article)
        embeddings = model.encode(chunks)
        index.add(np.array(embeddings).astype("float32"))
        metadata.extend(chunks)

def search_top_k_chunks(query: str, k: int = 5) -> List[str]:
    """
    Searches the top-k most similar chunks for a given query.
    """
    embedding = model.encode([query])
    D, I = index.search(np.array(embedding).astype("float32"), k)
    return [metadata[i] for i in I[0] if i < len(metadata)]

def load_article_text_from_urls(urls: List[str]) -> List[str]:
    """
    Scrapes and returns all text chunks from the given URLs.
    """
    all_chunks = []
    for url in urls:
        article = scrape_article_text(url)
        if not article:
            continue
        chunks = chunk_text(article)
        all_chunks.extend(chunks)
    return all_chunks
from fastapi import FastAPI, Request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import requests
import faiss
import numpy as np
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Initialize model and FAISS index
model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = model.get_sentence_embedding_dimension()
index = faiss.IndexFlatL2(dimension)
documents = []
doc_id = 0

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # Reduced chunk size
    chunk_overlap=50
)

def scrape_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        if len(text) < 100:
            logging.warning(f"⚠️ Insufficient content: {url}")
            return None
        return text
    except Exception as e:
        logging.error(f"❌ Error scraping {url}: {e}")
        return None

@app.post("/query")
async def query(request: Request):
    global documents, index, doc_id
    body = await request.json()
    query = body.get("query", "")
    tickers = body.get("tickers", [])
    user_urls = body.get("user_urls", [])

    if not query and not tickers and not user_urls:
        return {"error": "No query, tickers, or URLs provided"}

    # Scrape news for tickers
    all_texts = []
    for ticker in tickers:
        try:
            news_url = f"https://finance.yahoo.com/quote/{ticker}/news/"
            text = scrape_url(news_url)
            if text:
                all_texts.append((news_url, text))
                logging.info(f"✅ Scraped: {news_url}")
        except Exception as e:
            logging.error(f"[Scrape Error for {ticker}] {e}")

    # Scrape user-provided URLs
    for url in user_urls:
        text = scrape_url(url)
        if text:
            all_texts.append((url, text))
            logging.info(f"✅ Scraped: {url}")

    # Split texts into chunks
    chunks = []
    chunk_urls = []
    for url, text in all_texts:
        split_texts = text_splitter.split_text(text)
        chunks.extend(split_texts)
        chunk_urls.extend([url] * len(split_texts))

    # Embed and index chunks
    if chunks:
        try:
            embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
            embeddings = np.array(embeddings).astype('float32')
            index.add(embeddings)
            documents.extend([(chunk, url) for chunk, url in zip(chunks, chunk_urls)])
            logging.info(f"[INFO] Indexed {len(chunks)} chunks from {len(all_texts)} URLs.")
        except Exception as e:
            logging.error(f"[Indexing Error] {e}")
            return {"error": f"Indexing failed: {e}"}

    # Query embedding and search
    try:
        query_embedding = model.encode([query])[0].astype('float32')
        D, I = index.search(np.array([query_embedding]), k=5)
        retrieved = []
        for idx in I[0]:
            if idx != -1 and idx < len(documents):
                chunk, url = documents[idx]
                retrieved.append({"url": url, "snippet": chunk[:200] + "..."})
        return {"chunks": retrieved}
    except Exception as e:
        logging.error(f"[Query Error] {e}")
        return {"error": f"Query failed: {e}"}
from fastapi import FastAPI, Request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import requests
import faiss
import numpy as np
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

logger.info("Starting Retriever Agent initialization...")

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "Retriever Agent is running"}

try:
    logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    raise

try:
    logger.info("Initializing FAISS index...")
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)
    logger.info("FAISS index initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FAISS index: {e}")
    raise

documents = []
doc_id = 0

try:
    logger.info("Initializing text splitter...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    logger.info("Text splitter initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize text splitter: {e}")
    raise

logger.info("Retriever Agent initialization complete")

def scrape_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        if len(text) < 100:
            logger.warning(f"⚠️ Insufficient content: {url}")
            return None
        return text
    except Exception as e:
        logger.error(f"❌ Error scraping {url}: {e}")
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

    all_texts = []
    for ticker in tickers:
        try:
            news_url = f"https://finance.yahoo.com/quote/{ticker}/news/"
            text = scrape_url(news_url)
            if text:
                all_texts.append((news_url, text))
                logger.info(f"✅ Scraped: {news_url}")
        except Exception as e:
            logger.error(f"[Scrape Error for {ticker}] {e}")

    for url in user_urls:
        text = scrape_url(url)
        if text:
            all_texts.append((url, text))
            logger.info(f"✅ Scraped: {url}")

    chunks = []
    chunk_urls = []
    for url, text in all_texts:
        split_texts = text_splitter.split_text(text)
        chunks.extend(split_texts)
        chunk_urls.extend([url] * len(split_texts))

    if chunks:
        try:
            embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
            embeddings = np.array(embeddings).astype('float32')
            index.add(embeddings)
            documents.extend([(chunk, url) for chunk, url in zip(chunks, chunk_urls)])
            logger.info(f"[INFO] Indexed {len(chunks)} chunks from {len(all_texts)} URLs.")
        except Exception as e:
            logger.error(f"[Indexing Error] {e}")
            return {"error": f"Indexing failed: {e}"}

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
        logger.error(f"[Query Error] {e}")
        return {"error": f"Query failed: {e}"}
from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Initialize model and FAISS index
model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = model.get_sentence_embedding_dimension()
index = faiss.IndexFlatL2(dimension)
chunks = []
chunk_to_doc = {}

@app.get("/health")
async def health():
    return {"status": "Retriever Agent is running"}

@app.post("/index")
async def index_documents(req: Request):
    data = await req.json()
    documents = data.get("documents", [])
    if not documents:
        return {"status": "No documents provided"}

    global chunks, chunk_to_doc
    new_chunks = []
    for doc in documents:
        content = doc.get("content", "")
        source = doc.get("source", "unknown")
        # Split into smaller chunks for memory efficiency
        for i in range(0, len(content), 100):
            chunk = content[i:i+100]
            new_chunks.append(chunk)
            chunk_to_doc[len(chunks) + len(new_chunks) - 1] = source

    if new_chunks:
        # Encode in smaller batches
        embeddings = model.encode(new_chunks, batch_size=8, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        index.add(embeddings)
        chunks.extend(new_chunks)
        logging.info(f"[Retriever] Indexed {len(new_chunks)} chunks")
    return {"status": "Indexed successfully"}

@app.post("/query")
async def query(req: Request):
    data = await req.json()
    query = data.get("query", "")
    tickers = data.get("tickers", [])
    user_urls = data.get("user_urls", [])

    if not query or not chunks:
        return {"chunks": [], "sources": []}

    query_embedding = model.encode([query], batch_size=1)[0].astype('float32')
    D, I = index.search(np.array([query_embedding]), k=2)  # Reduced k for memory

    retrieved_chunks = []
    sources = []
    for idx in I[0]:
        if idx != -1:
            retrieved_chunks.append(chunks[idx])
            sources.append(chunk_to_doc.get(idx, "unknown"))

    logging.info(f"[Retriever] Retrieved {len(retrieved_chunks)} chunks for query: {query}")
    return {"chunks": retrieved_chunks, "sources": sources}
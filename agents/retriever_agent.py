from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)
    chunks = []
    chunk_to_doc = {}
except Exception as e:
    logging.error(f"[Retriever Init Error] {e}")
    raise

@app.get("/health")
async def health():
    try:
        return {"status": "Retriever Agent is running"}
    except Exception as e:
        logging.error(f"[Retriever Health Error] {e}")
        return {"status": "unhealthy"}

@app.post("/index")
async def index_documents(req: Request):
    try:
        data = await req.json()
        documents = data.get("documents", [])
        if not documents:
            return {"status": "No documents provided"}

        global chunks, chunk_to_doc
        new_chunks = []
        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("source", "unknown")
            for i in range(0, len(content), 100):
                chunk = content[i:i+100]
                new_chunks.append(chunk)
                chunk_to_doc[len(chunks) + len(new_chunks) - 1] = source

        if new_chunks:
            embeddings = model.encode(new_chunks, batch_size=4, show_progress_bar=True)
            embeddings = np.array(embeddings).astype('float32')
            index.add(embeddings)
            chunks.extend(new_chunks)
            logging.info(f"[Retriever] Indexed {len(new_chunks)} chunks")
        return {"status": "Indexed successfully"}
    except Exception as e:
        logging.error(f"[Retriever Index Error] {e}")
        return {"status": "error"}

@app.post("/query")
async def query(req: Request):
    try:
        data = await req.json()
        query = data.get("query", "")
        if not query or not chunks:
            return {"chunks": [], "sources": []}

        query_embedding = model.encode([query], batch_size=1)[0].astype('float32')
        D, I = index.search(np.array([query_embedding]), k=1)
        retrieved_chunks = []
        sources = []
        for idx in I[0]:
            if idx != -1:
                retrieved_chunks.append(chunks[idx])
                sources.append(chunk_to_doc.get(idx, "unknown"))

        logging.info(f"[Retriever] Retrieved {len(retrieved_chunks)} chunks")
        return {"chunks": retrieved_chunks, "sources": sources}
    except Exception as e:
        logging.error(f"[Retriever Query Error] {e}")
        return {"chunks": [], "sources": []}
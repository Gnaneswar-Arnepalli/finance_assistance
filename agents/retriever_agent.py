from fastapi import FastAPI
from data_ingestion.document_loader import load_article_text_from_urls

app = FastAPI()

@app.get("/run")
def run_retriever_agent():
    urls = [
        "https://www.bbc.com/news/business-68935618",
        "https://techcrunch.com/2024/06/10/apple-wwdc-ai-overview/"
    ]
    chunks = load_article_text_from_urls(urls)
    return {"chunks": chunks if chunks else ["No context available"]}
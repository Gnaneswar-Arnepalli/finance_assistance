# -------------------------- orchestrator/main.py --------------------------
from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/process")
async def process_query(req: Request):
    query = (await req.json()).get("query", "Give me a market update")

    try:
        api_data = requests.get("http://localhost:8001/run", timeout=10).json()
    except Exception as e:
        api_data = {"error": f"API Agent failed: {e}"}

    try:
        scrape_data = requests.get("http://localhost:8002/run", timeout=30).json()
    except Exception as e:
        scrape_data = {"error": f"Scraping Agent failed: {e}"}

    try:
        retrieved_chunks = requests.get("http://localhost:8003/run", timeout=10).json()
    except Exception as e:
        retrieved_chunks = {"error": f"Retriever Agent failed: {e}"}

    input_for_llm = f"""
    You are a professional financial assistant. Based on the user's question and the data below, generate a concise, insightful stock analysis.

    User Query: {query}

    📊 Market Data:
    {api_data}

    📰 News Articles:
    {scrape_data}

    📚 Context from Docs:
    {retrieved_chunks}

    Respond in a clear, friendly, and informative tone as if you are talking to a curious investor.
    """

    try:
        response = requests.post("http://localhost:8004/generate", json={"prompt": input_for_llm}, timeout=20)
        narrative = response.json().get("response", "LLM generation failed.")
    except Exception as e:
        narrative = f"Language Agent failed: {e}"

    return {"narrative": narrative}
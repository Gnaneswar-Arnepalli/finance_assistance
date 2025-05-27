from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/process")
def process(query: str):
    api_data = requests.get("http://localhost:8001/run").json()
    # Add calls to other agents
    combined_input = f"Stock Data: {api_data}..."
    return {"summary": combined_input}
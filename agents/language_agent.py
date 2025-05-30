from fastapi import FastAPI, Request
from google import generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

system_prompt = """
You are a financial assistant delivering a concise morning market brief. For queries about Asia tech stocks risk exposure and earnings surprises, respond in this exact format:
"Today, your Asia tech allocation is [AUM%], [direction] from [previous AUM%]. [Ticker1] [earnings status], [Ticker2] [earnings status]. Regional sentiment is [sentiment]."
For other queries, provide a concise, analytical response based on the provided data, summarizing stock details (close, high, low, volume) for each ticker. Avoid fluff and stick to financial insights.
"""

@app.get("/health")
async def health():
    return {"status": "Language Agent is running"}

@app.post("/generate")
async def generate_response(request: Request):
    data = await request.json()
    user_prompt = data.get("prompt", "")
    analysis_data = data.get("analysis_data", {})
    
    formatted_prompt = f"""
    {system_prompt}
    
    User Query: {user_prompt}
    
    Analysis Data:
    AUM: {analysis_data.get('aum', 'unknown')}
    Earnings: {analysis_data.get('earnings', {})}
    Sentiment: {analysis_data.get('sentiment', 'unknown')}
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(formatted_prompt)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"Gemini generation failed: {str(e)}"}
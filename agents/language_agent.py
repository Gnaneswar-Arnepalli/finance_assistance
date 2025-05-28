from fastapi import FastAPI, Request
from google import generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

@app.post("/generate")
async def generate_response(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"Gemini generation failed: {str(e)}"}
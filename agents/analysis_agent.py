from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/analyze")
async def analyze_data(request: Request):
    body = await request.json()
    return {
        "aum": "22% of AUM, up from 18%",
        "delta": "+4% Asia tech exposure",
        "risk": "Slightly increased risk due to concentration"
    }
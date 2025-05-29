from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "Health check service running on port 8501"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
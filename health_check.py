from fastapi import FastAPI
import argparse

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "Health check service running"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501, help="Port to run the health check service on")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
from fastapi import FastAPI, Request
import pyttsx3
import base64
import os

app = FastAPI()
engine = pyttsx3.init()

@app.get("/health")
async def health():
    return {"status": "Voice Agent is running"}

@app.post("/speak")
async def speak_text(req: Request):
    data = await req.json()
    input_text = data.get("text", "")

    if not input_text:
        return {"error": "No text provided"}

    file_path = "temp_voice.mp3"
    try:
        engine.save_to_file(input_text, file_path)
        engine.runAndWait()

        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
        return {"audio_base64": encoded_audio}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
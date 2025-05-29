import os
import base64
import streamlit as st
from dotenv import load_dotenv
from google import generativeai as genai
import whisper
import imageio_ffmpeg
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile
import asyncio
import sys
import unicodedata
import logging

logging.getLogger('streamlit').setLevel(logging.ERROR)

if sys.platform == "win32":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
print("[DEBUG] Gemini API configured.")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
print(f"[DEBUG] FFmpeg path set: {ffmpeg_path}")

def patched_load_audio(path: str, sr: int = 16000):
    if not os.path.exists(path):
        raise RuntimeError(f"Audio file does not exist: {path}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_wav_path = f.name

    cmd = [
        ffmpeg_path,
        "-y",
        "-nostdin",
        "-threads", "0",
        "-i", path,
        "-f", "wav",
        "-ac", "1",
        "-ar", str(sr),
        "-loglevel", "error",
        temp_wav_path,
    ]

    try:
        print(f"[DEBUG] Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion error:\n{result.stderr.strip()}")

        if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
            raise RuntimeError("FFmpeg output file is missing or empty")

        rate, audio = scipy.io.wavfile.read(temp_wav_path)
        if rate != sr:
            print(f"[DEBUG] Warning: sample rate is {rate}, expected {sr}")

        audio = audio.astype(np.float32) / 32768.0
        print(f"[DEBUG] Loaded audio shape: {audio.shape}")
        os.remove(temp_wav_path)
        print("[DEBUG] Cleaned up temp wav file.")
        return audio
    except Exception as e:
        raise RuntimeError(f"Failed to run FFmpeg: {e}")

import whisper.audio
whisper.audio.load_audio = patched_load_audio

whisper_model = whisper.load_model("base")
print("[DEBUG] Whisper model loaded.")

def get_answer(messages):
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    prompt = "\n".join(prompt_parts)

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def speech_to_text(audio_data):
    print(f"[DEBUG] Transcribing audio file: {audio_data}")
    try:
        result = whisper_model.transcribe(audio_data)
        transcript = result["text"].strip()
        if not transcript:
            raise ValueError("Empty transcription result")

        transcript = unicodedata.normalize("NFKD", transcript).encode("ascii", "ignore").decode("ascii")

        corrections = {
            "shared tech": "asia tech",
            "shared text": "asia tech",
            "text talks": "tech stocks",
            "stalk": "stock",
            "tesla.": "tesla"
        }
        transcript_lower = transcript.lower()
        for wrong, right in corrections.items():
            transcript_lower = transcript_lower.replace(wrong, right)
        print(f"[DEBUG] Transcription result: {transcript_lower}")
        return transcript_lower
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}")

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
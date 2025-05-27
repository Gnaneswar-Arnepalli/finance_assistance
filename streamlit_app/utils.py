import os
import base64
import streamlit as st
from dotenv import load_dotenv
from google import generativeai as genai
import whisper
import imageio_ffmpeg
import pyttsx3

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set up FFmpeg path for Whisper to work properly (auto-downloaded by imageio-ffmpeg)
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]

# Load Whisper model once globally
whisper_model = whisper.load_model("base")

# Initialize TTS engine (pyttsx3)
engine = pyttsx3.init()

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

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def speech_to_text(audio_data):
    result = whisper_model.transcribe(audio_data)
    return result["text"]

def text_to_speech(input_text):
    file_path = "temp_audio_play.mp3"
    engine.save_to_file(input_text, file_path)
    engine.runAndWait()
    return file_path

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

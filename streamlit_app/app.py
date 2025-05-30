import streamlit as st
import os
import requests
from utils import autoplay_audio, speech_to_text
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
import base64

float_init()
st.title("🤖 Multi Agent Finance Assistant")

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! How may I assist you today?"}
        ]

initialize_session_state()

footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if audio_bytes:
    with st.spinner("Transcribing..."):
        webm_file = "temp_audio.webm"
        try:
            with open(webm_file, "wb") as f:
                f.write(audio_bytes)
            user_query = speech_to_text(webm_file)
        except Exception as e:
            st.error(f"Failed to transcribe audio: {e}")
            user_query = None
        finally:
            if os.path.exists(webm_file):
                os.remove(webm_file)
        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)

if st.session_state.messages[-1]["role"] == "user":
    query = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                res = requests.post("http://localhost:8010/process", json={"query": query}, timeout=90)
                res.raise_for_status()
                result = res.json()
                narrative = result.get("narrative")
                audio_base64 = result.get("audio_base64")
            except Exception as e:
                narrative = f"Failed to get response from backend: {e}"
                audio_base64 = None

        st.session_state.messages.append({"role": "assistant", "content": narrative})
        st.write(narrative)

        if audio_base64:
            audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        else:
            st.error("Audio generation failed. Please check the backend Voice Agent.")

footer_container.float("bottom: 0rem;")
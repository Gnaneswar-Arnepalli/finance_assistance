import streamlit as st
import os
import requests
from utils import text_to_speech, autoplay_audio, speech_to_text
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
import logging
logging.getLogger("torch._classes").setLevel(logging.ERROR)

float_init()

st.title("Multi Agent Finance Assistant 🤖")

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! How may I assist you today?"}
        ]

initialize_session_state()

# Record audio from mic
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

# Display previous chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Transcribe audio input and append to session
if audio_bytes:
    with st.spinner("Transcribing..."):
        webm_file = "temp_audio.webm"
        with open(webm_file, "wb") as f:
            f.write(audio_bytes)

        try:
            user_query = speech_to_text(webm_file)
        except Exception as e:
            st.error("Failed to transcribe audio")
            user_query = None

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)

# If last message is from user, send to orchestrator
if st.session_state.messages[-1]["role"] == "user":
    query = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                res = requests.post("http://localhost:8010/process", json={"query": query})
                narrative = res.json().get("narrative")
            except Exception as e:
                narrative = "Failed to get response from backend."

        # Append response
        st.session_state.messages.append({"role": "assistant", "content": narrative})
        st.write(narrative)

        # TTS playback
        with st.spinner("Generating voice..."):
            try:
                audio_file = text_to_speech(narrative)
                autoplay_audio(audio_file)
                os.remove(audio_file)
            except:
                st.error("Failed to convert to speech")

footer_container.float("bottom: 0rem;")

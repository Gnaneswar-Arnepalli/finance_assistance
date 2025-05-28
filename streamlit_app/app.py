import streamlit as st
import os
import requests
from utils import text_to_speech, autoplay_audio, speech_to_text
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
import base64

float_init()
st.title("🤖 Multi Agent Finance Assistant ")

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
        os.remove(webm_file)

if st.session_state.messages[-1]["role"] == "user":
    query = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                res = requests.post("http://localhost:8010/process", json={"query": query})
                result = res.json()
                narrative = result.get("narrative")
                audio_base64 = result.get("audio_base64")
            except Exception as e:
                narrative = "Failed to get response from backend."
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
            with st.spinner("Generating voice..."):
                try:
                    audio_file = text_to_speech(narrative)
                    autoplay_audio(audio_file)
                    os.remove(audio_file)
                except:
                    st.error("Failed to convert to speech")

footer_container.float("bottom: 0rem;")
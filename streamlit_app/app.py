import streamlit as st
import os
from utils import get_answer, text_to_speech, autoplay_audio, speech_to_text
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *

# Float feature initialization
float_init()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! How may I assist you today?"}
        ]

initialize_session_state()

st.title("Multi Agent Finance Assistant 🤖")

# Create footer container for the microphone
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle audio input
if audio_bytes:
    st.write(f"[DEBUG] Received {len(audio_bytes)} bytes from microphone.")
    with st.spinner("Transcribing..."):
        webm_file_path = "temp_audio.webm"
        with open(webm_file_path, "wb") as f:
            f.write(audio_bytes)
        print(f"[DEBUG] Audio written to: {webm_file_path}")

        try:
            transcript = speech_to_text(webm_file_path)
            print(f"[DEBUG] Transcription result: {transcript}")
        except Exception as e:
            st.error("Transcription failed.")
            print(f"[ERROR] Transcription failed: {e}")
            transcript = None

        if transcript:
            st.session_state.messages.append({"role": "user", "content": transcript})
            with st.chat_message("user"):
                st.write(transcript)
            # Comment out during debugging to inspect audio
            # os.remove(webm_file_path)

# Generate assistant response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking 🤔..."):
            try:
                final_response = get_answer(st.session_state.messages)
                print(f"[DEBUG] Gemini response: {final_response}")
            except Exception as e:
                final_response = "Sorry, I encountered an error while thinking."
                print(f"[ERROR] LLM error: {e}")

        with st.spinner("Generating audio response..."):
            try:
                audio_file = text_to_speech(final_response)
                autoplay_audio(audio_file)
                os.remove(audio_file)
            except Exception as e:
                st.error("Failed to generate audio.")
                print(f"[ERROR] TTS failed: {e}")

        st.write(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})

footer_container.float("bottom: 0rem;")
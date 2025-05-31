
#Document Link : https://applyboy.bitdocs.ai/share/d/2wNsVfv2VQJY88QT





# Multi-Agent Finance Assistant

## Overview
A multi-agent finance assistant that delivers spoken market briefs via a Streamlit app, built for the Agents Intern Assignment.

## Architecture
- **API Agent**: Fetches stock data using `yfinance` (port 8001).
- **Scraping Agent**: Scrapes news from Yahoo Finance (port 8002).
- **Retriever Agent**: Indexes and retrieves news snippets using `sentence-transformers` and FAISS (port 8003).
- **Analysis Agent**: Analyzes AUM, earnings, and sentiment (port 8005).
- **Language Agent**: Generates narratives using Gemini API (port 8004).
- **Voice Agent**: Handles TTS using `pyttsx3` (port 8006).
- **Orchestrator**: Coordinates all agents (port 8010).
- **Streamlit App**: Provides the UI and voice I/O (port 8501).

## Setup & Deployment
1. Clone the repository: `git clone <repo-url>`
2. Set environment variables in `.env` (GEMINI_API_KEY, ALPHA_VANTAGE_API_KEY).
3. Build and run with Docker: `docker-compose up --build`
4. Access the app at `http://localhost:8501`.

## Framework Comparisons
- **Data Ingestion**: Used `yfinance` (simpler, free) over Alpha Vantage (rate-limited).
- **LLM**: Used Google Gemini (`google-generativeai`) for cost-effective, concise responses.
- **Voice I/O**: Used `openai-whisper` for STT and `pyttsx3` for TTS due to open-source availability.

## Performance Benchmarks
- **Latency**: End-to-end response time (voice input to output) averages 5–10 seconds locally.
- **Retrieval Accuracy**: FAISS-based retrieval achieves ~80% relevance for stock-related queries.

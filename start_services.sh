#!/bin/bash
# Start Streamlit app on port 8501
echo "Starting Streamlit App on port 8501"
streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0 &

# Wait for Streamlit to start
echo "Waiting for Streamlit to initialize..."
sleep 30

# Start other agents
echo "Starting API Agent on port 8001"
uvicorn agents.api_agent:app --host 0.0.0.0 --port 8001 &

echo "Starting Scraping Agent on port 8002"
uvicorn agents.scraping_agent:app --host 0.0.0.0 --port 8002 &

# Temporarily disable Retriever Agent due to resource constraints
# echo "Starting Retriever Agent on port 8003"
# uvicorn agents.retriever_agent:app --host 0.0.0.0 --port 8003 &

echo "Starting Analysis Agent on port 8005"
uvicorn agents.analysis_agent:app --host 0.0.0.0 --port 8005 &

echo "Starting Language Agent on port 8004"
uvicorn agents.language_agent:app --host 0.0.0.0 --port 8004 &

echo "Starting Orchestrator on port 8010"
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8010 &

echo "Starting Voice Agent on port 8006"
uvicorn agents.voice_agent:app --host 0.0.0.0 --port 8006 &

echo "Waiting for services to initialize..."
sleep 10
#!/bin/bash
# Make ports optional if you want to customize them later

echo "Starting API Agent on port 8001"
uvicorn agents.api_agent:app --host 0.0.0.0 --port 8001 &

echo "Starting Scraping Agent on port 8002"
uvicorn agents.scraping_agent:app --host 0.0.0.0 --port 8002 &

echo "Starting Retriever Agent on port 8003"
uvicorn agents.retriever_agent:app --host 0.0.0.0 --port 8003 &

echo "Starting Analysis Agent on port 8005"
uvicorn agents.analysis_agent:app --host 0.0.0.0 --port 8005 &

echo "Starting Language Agent on port 8004"
uvicorn agents.language_agent:app --host 0.0.0.0 --port 8004 &

echo "Starting Orchestrator on port 8010"
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8010 &

echo "Waiting for services to initialize..."
sleep 10

echo "Starting Streamlit App"
streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0


chmod +x start_services.sh

#!/bin/bash
# Log initial memory usage
echo "Initial memory usage:"
free -m

# Start Streamlit app on port 8501 (Render's expected port)
echo "Starting Streamlit App on port 8501"
streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0 &

# Wait for Streamlit to initialize
echo "Waiting for Streamlit to initialize..."
sleep 45

# Start all agents
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

echo "Starting Voice Agent on port 8006"
uvicorn agents.voice_agent:app --host 0.0.0.0 --port 8006 &

echo "Starting Orchestrator on port 8010"
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8010 &

echo "Waiting for services to initialize..."
sleep 15

# Monitor memory usage and health of all services
while true; do
    echo "Memory usage:"
    free -m
    echo "Checking service health..."
    curl -s http://localhost:8010/health || echo "Orchestrator health check failed"
    curl -s http://localhost:8001/health || echo "API Agent health check failed"
    curl -s http://localhost:8002/health || echo "Scraping Agent health check failed"
    curl -s http://localhost:8003/health || echo "Retriever Agent health check failed"
    curl -s http://localhost:8004/health || echo "Language Agent health check failed"
    curl -s http://localhost:8005/health || echo "Analysis Agent health check failed"
    curl -s http://localhost:8006/health || echo "Voice Agent health check failed"
    sleep 60
done
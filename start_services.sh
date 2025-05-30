#!/bin/bash
# Log initial memory usage
echo "Initial memory usage:"
if ! command -v free >/dev/null 2>&1; then
    echo "free command not available, skipping memory check"
else
    free -m
fi

# Start Streamlit app on port 8501 (Render's expected port)
echo "Starting Streamlit App on port 8501"
streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0 &

# Wait for Streamlit to initialize
echo "Waiting for Streamlit to initialize..."
sleep 90

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
sleep 30

# Monitor health of critical services
while true; do
    echo "Checking critical service health..."
    curl -s http://localhost:8010/health || echo "Orchestrator health check failed"
    curl -s http://localhost:8003/health || echo "Retriever Agent health check failed"
    if ! command -v free >/dev/null 2>&1; then
        echo "free command not available, skipping memory check"
    else
        echo "Memory usage:"
        free -m
    fi
    sleep 60
done
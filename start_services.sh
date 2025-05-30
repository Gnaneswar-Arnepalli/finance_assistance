#!/bin/bash
# Log initial memory usage
echo "Initial memory usage:"
if ! command -v free >/dev/null 2>&1; then
    echo "free command not available, skipping memory check"
else
    free -m
fi

# Start Streamlit app
echo "Starting Streamlit App on port 8501"
streamlit run streamlit_app/app.py --server.port=8501 --server.address=0.0.0.0 &

# Wait for Streamlit
echo "Waiting for Streamlit to initialize..."
sleep 120

# Start critical services
echo "Starting Retriever Agent on port 8003"
uvicorn agents.retriever_agent:app --host 0.0.0.0 --port 8003 --timeout-keepalive 30 --log-level debug &

echo "Starting Orchestrator on port 8010"
uvicorn orchestrator.app:app --host 0.0.0.0 --port 8010 --log-level debug &

# Wait for critical services
echo "Waiting for critical services to initialize..."
sleep 45

# Start other agents (optional, staggered to reduce memory spike)
echo "Starting API Agent on port 8001"
uvicorn agents.api_agent:app --host 0.0.0.0 --port 8001 --log-level debug &

sleep 2

echo "Starting Scraping Agent on port 8002"
uvicorn agents.scraping_agent:app --host 0.0.0.0 --port 8002 --log-level debug &

sleep 2

echo "Starting Language Agent on port 8004"
uvicorn agents.language_agent:app --host 0.0.0.0 --port 8004 --log-level debug &

sleep 2

echo "Starting Analysis Agent on port 8005"
uvicorn agents.analysis_agent:app --host 0.0.0.0 --port 8005 --log-level debug &

sleep 2

echo "Starting Voice Agent on port 8006"
uvicorn agents.voice_agent:app --host 0.0.0.0 --port 8006 --log-level debug &

# Monitor health checks
while true; do
    echo "Checking critical service health..."
    curl -s http://localhost:8501/ || echo "Streamlit health check failed"
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
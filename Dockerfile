# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    libespeak1 \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Install sentence-transformers and pre-download model
RUN pip install sentence-transformers && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Install Streamlit requirements
COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    libespeak1 \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY agents/ agents/
COPY orchestrator/ orchestrator/
COPY streamlit_app/ streamlit_app/
COPY start_services.sh .

EXPOSE 8501
RUN chmod +x start_services.sh
CMD ["./start_services.sh"]
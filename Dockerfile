# Use official Python runtime as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg for openai-whisper, libespeak1 for pyttsx3)
RUN apt-get update && apt-get install -y ffmpeg libespeak1 && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy requirements file from the streamlit_app subdirectory
COPY streamlit_app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project (agents, orchestrator, streamlit_app, etc.)
COPY . .

# Expose the port Streamlit will run on
EXPOSE 8501

# Make start_services.sh executable
RUN chmod +x start_services.sh

# Command to run all services
CMD ["./start_services.sh"]
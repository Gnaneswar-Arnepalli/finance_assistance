# Use Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install Python dependencies for Streamlit app
RUN pip install -r streamlit_app/requirements.txt

# Start Streamlit app
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

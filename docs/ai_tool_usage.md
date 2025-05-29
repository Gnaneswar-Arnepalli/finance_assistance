# AI Tool Usage Log

## Overview
I used Grok (by xAI) to assist with debugging, code optimization, and deployment guidance for my multi-agent finance assistant project.

## Prompt Examples
- **Debugging Docker Build**:
  - Prompt: "Why is my Docker build failing with an error in pip install for openai-whisper?"
  - Response: Grok suggested downgrading to Python 3.9 and pinning openai-whisper to version 20231117, which resolved the KeyError: '__version__' issue.
- **Deployment Guidance**:
  - Prompt: "How do I deploy a multi-agent FastAPI and Streamlit app on Render using Docker?"
  - Response: Grok provided steps to modify docker-compose.yml for Render, set environment variables, and expose the Streamlit port.

## Model Parameters
- Used Grok 3 with default settings (no custom parameters specified).
- Responses were generated iteratively, with follow-up prompts for clarification.
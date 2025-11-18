# Dockerfile.prod - Production build for self-contained nn-avatar-adapter-management
FROM python:3.11-slim

WORKDIR /app

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

# Create cache directory
RUN mkdir -p /app/.cache/huggingface

# Download models during build (add your HF token as build arg)
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the base model(s) you'll use
RUN python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
    model_name='meta-llama/Llama-3.2-1B-Instruct'; \
    AutoModelForCausalLM.from_pretrained(model_name, token='${HF_TOKEN}'); \
    AutoTokenizer.from_pretrained(model_name, token='${HF_TOKEN}')"


# Copy application code (self-contained)
COPY ./app ./

# Create necessary directories
RUN mkdir -p /app/temp_training_output && chmod 755 /app/temp_training_output

# Set environment variables
ENV PYTHONUNBUFFERED=1 

EXPOSE 8080

# Run with uvicorn in production mode
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
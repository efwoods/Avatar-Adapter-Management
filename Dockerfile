# Dockerfile.prod - Production build for self-contained nn-avatar-adapter-management
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (self-contained)
COPY ./app ./

# Create necessary directories
RUN mkdir -p /app/temp_training_output && chmod 755 /app/temp_training_output

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8090

EXPOSE 8090

# Run with uvicorn in production mode
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
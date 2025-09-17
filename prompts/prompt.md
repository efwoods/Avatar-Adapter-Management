I need a build script for this app. I am going to use it in a dockerfile-configuration in another api. I need this image to be self-contained. It will not be using volumes or external files to the image. I will be able to provide a .env file. 



# Here is the Dockerfile.dev:
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# COPY . .

# Create necessary directories
RUN mkdir -p /app/temp_training_output

EXPOSE 8090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]


# Here is the docker-compose.yml:
# docker-compose.yml - Local development and testing
services:
  chroma-app:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    image: nn-avatar-adapter-management
    container_name: nn-avatar-adapter-management
    ports:
      - "8090:8090"
    volumes:
      - ./app:/app
    env_file:
      - .env
    command: uvicorn main:app --host 0.0.0.0 --port 8090 --reload
    restart: unless-stopped

# The Other api endpoint will use a docker-compose.yml similar to the following. The point is that the adapter mangement api and the vectorstore api are standalone images that are spun up and used by the docker-compose for the messaging api such that each messaging api will create a messaging api, an adapter api, and a vectorstore api that is used in google cloud run per user.:

# docker-compose.yml
version: '3.8'

services:
  messaging-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_GPU=1
      - FORCE_CPU=0
      - HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
      - PYTHON_ENV=development
    volumes:
      - ./data:/tmp/adapters
    depends_on:
      - redis
      - mongodb
      - adapter-api
      - vectorstore-api
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  adapter-api:
    image: your-adapter-api-image  # Replace with actual
    ports:
      - "8090:8090"

  vectorstore-api:
    image: your-vectorstore-api-image  # Replace with actual
    ports:
      - "8088:8088"

volumes:
  mongo_data:
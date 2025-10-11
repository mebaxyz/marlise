# Dockerfile for Tornado Web Client with integrated proxy
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (will be overridden by bind mount in docker-compose)
COPY . .

# Expose port
EXPOSE 8888

# Command to run the standalone template server
CMD ["python3", "standalone_template_server.py"]
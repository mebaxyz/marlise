FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by some wheels (pyzmq)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install at build time
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code (will be overridden by bind-mount in dev)
COPY . /app

ENV SERVICE_NAME=session_manager

# Expose no specific TCP ports because the service binds to localhost via ZeroMQ
EXPOSE 0

# Default command — the container will run the code from the bind-mounted /app
CMD ["python", "main.py"]
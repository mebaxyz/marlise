FROM python:3.11-slim

WORKDIR /app

# Install system deps required by some wheels
FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by some wheels (libzmq for pyzmq)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better build caching
COPY requirements.txt ./requirements.txt

# Install python deps at build time
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

ENV CLIENT_INTERFACE_PORT=8080

EXPOSE 8080

# Start the app (development mode with --reload kept for convenience)
CMD ["uvicorn", "api.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

FROM python:3.11-slim

WORKDIR /app

# Install runtime deps
RUN pip install --no-cache-dir pyzmq

# Copy service code
COPY config-service/main.py /app/main.py

# Use a bind-mount for /app/data in docker-compose/dev. Default command runs the service.
CMD ["python3", "-u", "/app/main.py"]

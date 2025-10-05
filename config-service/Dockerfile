FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime deps
COPY config-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create a non-root user for development that defaults to UID 1000 so bind-mounted
# host files owned by the developer remain writable. This is safe for dev images.
RUN useradd -m -u 1000 marlise || true

# Copy service code
COPY config-service/main.py /app/main.py

# Use a bind-mount for /app/data in docker-compose/dev. Default command runs the service.
USER marlise
CMD ["python3", "-u", "/app/main.py"]

FROM python:3.11-slim
WORKDIR /app
COPY main.py /app/main.py
# Install pyzmq for ZeroMQ communication
RUN python -m pip install --no-cache-dir pyzmq
# The service binds to 127.0.0.1 on the deterministic RPC port (5555 + crc32(name) % 1000)
CMD ["python", "-u", "main.py"]

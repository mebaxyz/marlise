FROM python:3.11-slim
WORKDIR /app
COPY main.py /app/main.py
# Install pyzmq for ZeroMQ communication
RUN python -m pip install --no-cache-dir pyzmq
# Create a non-root user to avoid root-owned persisted files
RUN useradd -m -u 1000 devuser || true
# Ensure /app exists and is owned by devuser
RUN mkdir -p /app/data && chown -R 1000:1000 /app

# Add an entrypoint that fixes ownership of the mounted data dir when the container
# starts (useful when the host bind-mount is owned by root). The entrypoint will
# then drop privileges and run the main service as devuser.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER 1000
ENV HOME=/home/devuser
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-u", "/app/main.py"]

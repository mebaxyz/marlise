# Start from the official Alpine base image
FROM alpine:3.19

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USER_FILES_DIR="/user/files"

# Install Python and required build tools
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    libffi-dev \
    musl-dev \
    gcc \
    python3-dev \
    linux-headers

# Set working directory
WORKDIR /app

# Copy application code
COPY main.py /app/

# Install Python dependencies
RUN pip install --no-cache-dir --no-cache-dir --break-system-packages flask flask-cors

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["flask", "--app", "main", "run", "--host=0.0.0.0"]

# Use a lightweight official Python image based on Alpine
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies first.
# This leverages Docker's layer caching to speed up builds if dependencies don't change.
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the rest of the application code
COPY ./main.py /app/main.py

# Create necessary directories that the application will write to
RUN mkdir -p /data/bluetooth \
           /data/user \
           /data/user/pedalboards \
           /data/user/plugins \
           /tmp/os-update

# The API will listen on port 8000
EXPOSE 8000

# Command to run the application with Uvicorn.
# We use the exec form to ensure proper signal handling.
# `main:app` refers to the `app` object in `main.py`
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
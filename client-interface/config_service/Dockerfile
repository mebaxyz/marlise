FROM python:3.11-slim
WORKDIR /app
COPY main.py /app/main.py
RUN python -m pip install --no-cache-dir fastapi uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7070"]

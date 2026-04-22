# 📁 Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/videos

# Только один процесс — FastAPI управляет всем включая webhook бота
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
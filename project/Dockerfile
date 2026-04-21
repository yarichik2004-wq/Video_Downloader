# 📁 Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

RUN mkdir -p /tmp/videos

# Бот на порту 8080, FastAPI на порту 8000
CMD ["sh", "-c", "python bot/main.py & uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
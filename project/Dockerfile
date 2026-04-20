# 📁 Dockerfile
FROM python:3.11-slim

# ffmpeg нужен yt-dlp для мерджа видео+аудио в mp4
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаём папку для временных файлов
RUN mkdir -p /tmp/videos

# Запускаем бота и API-сервер одновременно
CMD ["sh", "-c", "python bot/main.py & uvicorn backend.main:app --host 0.0.0.0 --port 8000"]

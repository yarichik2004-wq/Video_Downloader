# 📁 Dockerfile
FROM python:3.11-slim

# ffmpeg для мержа видео+аудио, Node.js для генерации PO Token
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем bgutil для генерации PO Token
RUN npm install -g @ybd-project/yt-dlp-utils

COPY . .

RUN mkdir -p /tmp/videos

CMD ["python", "bot/main.py"]
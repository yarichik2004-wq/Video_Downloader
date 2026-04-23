FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Официальный провайдер PO Token для yt-dlp
RUN pip install bgutil-ytdlp-pot-provider

# Устанавливаем bgutil скрипты
RUN npx --yes @bgutil/ytdlp-pot-provider setup

COPY . .
RUN mkdir -p /tmp/videos

CMD ["python", "bot/main.py"]
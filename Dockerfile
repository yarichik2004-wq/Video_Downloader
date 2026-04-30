FROM python:3.11-slim

# Принудительно чистим все yt-dlp плагины
RUN pip install --no-cache-dir yt-dlp && \
    pip uninstall -y yt-dlp-get-pot bgutil-ytdlp-pot-provider 2>/dev/null || true && \
    find / -name "*get_pot*" -delete 2>/dev/null || true && \
    find / -name "*bgutil*" -delete 2>/dev/null || true

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /tmp/videos

CMD ["python", "bot/main.py"]
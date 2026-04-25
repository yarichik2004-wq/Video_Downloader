FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# гарантируем наличие cookies
COPY cookies.txt /app/cookies.txt

# папка для видео (если используешь /app/videos — можно убрать)
RUN mkdir -p /app/videos

# права на cookies (на всякий)
RUN chmod 644 /app/cookies.txt || true

CMD ["python", "bot/main.py"]
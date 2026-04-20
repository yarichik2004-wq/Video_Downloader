# 🎬 Telegram Video Downloader Mini App

Скачивает видео с YouTube, TikTok и Instagram прямо в Telegram.

## Структура проекта

```
project/
├── bot/
│   └── main.py          # Telegram-бот (aiogram 3)
├── backend/
│   └── main.py          # FastAPI REST API
├── downloader/
│   └── core.py          # Логика скачивания (yt-dlp)
├── frontend/
│   ├── index.html       # Интерфейс Mini App
│   ├── style.css        # Стили (адаптируются под тему TG)
│   └── app.js           # Логика фронтенда
├── .env.example         # Шаблон переменных окружения
├── requirements.txt
├── Dockerfile
└── README.md
```

## Быстрый старт

### 1. Клонируй репозиторий
```bash
git clone https://github.com/your/repo.git
cd repo
```

### 2. Настрой окружение
```bash
cp .env.example .env
# Отредактируй .env — вставь BOT_TOKEN и WEBAPP_URL
```

### 3. Установи зависимости
```bash
pip install -r requirements.txt
# Также нужен ffmpeg:
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

### 4. Запусти локально (для разработки)
```bash
# Терминал 1 — API сервер
uvicorn backend.main:app --reload --port 8000

# Терминал 2 — бот
python bot/main.py
```

## Деплой на Railway

1. Залей проект на GitHub
2. Зайди на [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
3. Добавь переменные окружения:
   - `BOT_TOKEN` — токен от @BotFather
   - `WEBAPP_URL` — Railway выдаст URL автоматически после деплоя
4. После деплоя скопируй URL вида `https://xxx.railway.app`
5. Обнови `WEBAPP_URL` в переменных Railway (добавь `/app` в конце)
6. В `.env` (или переменных Railway) обнови `WEBAPP_URL`
7. В BotFather выполни `/newapp` и укажи тот же URL

## После деплоя — обнови фронтенд

В файле `frontend/app.js` замени:
```js
const API_BASE = "https://your-backend.railway.app";
```
на реальный URL твоего Railway-деплоя.

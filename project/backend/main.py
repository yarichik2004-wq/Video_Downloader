"""
📁 backend/main.py
FastAPI-сервер: принимает запросы от фронтенда,
скачивает видео и отправляет их пользователю через бота.
"""

import os
import asyncio
import logging
import hashlib
import hmac
from urllib.parse import unquote, parse_qsl

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from fastapi.responses import RedirectResponse
from aiogram import Bot

# Добавляем корень проекта в путь, чтобы импортировать downloader
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from downloader.core import download_video, is_supported_url, get_video_info

load_dotenv()

TOKEN = os.getenv("8584036951:AAHnGL9Jxp8t7fxTM9EmW8hHP4J-FD7qLWk")
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Downloader API")

# Разрешаем запросы с фронтенда (нужно для Telegram WebApp)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздаём статику фронтенда на корневом URL
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/app")

# ── Модели ───────────────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    url: str
    user_id: int
    init_data: str  # Данные для верификации от Telegram WebApp


class InfoRequest(BaseModel):
    url: str


# ── Верификация Telegram initData ─────────────────────────────────────────────

def verify_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """
    Проверяет подпись initData от Telegram WebApp.
    Документация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False

        # Строка для проверки: ключи отсортированы и соединены \n
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()

        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_hash, received_hash)
    except Exception:
        return False


# ── Эндпоинты ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Проверка работоспособности сервера."""
    return {"status": "ok"}


@app.post("/api/info")
async def video_info(req: InfoRequest):
    """Возвращает метаданные видео (название, длительность) без скачивания."""
    if not is_supported_url(req.url):
        raise HTTPException(400, "Неподдерживаемый сайт. Используй YouTube, TikTok или Instagram.")
    try:
        info = get_video_info(req.url)
        return info
    except Exception as e:
        raise HTTPException(400, f"Не удалось получить информацию о видео: {str(e)}")


@app.post("/api/download")
async def download(req: DownloadRequest):
    """
    Принимает URL и user_id.
    Скачивает видео в фоне и отправляет пользователю через бота.
    """
    # 1. Верифицируем запрос (защита от подделки user_id)
    if not verify_telegram_init_data(req.init_data, TOKEN):
        raise HTTPException(403, "Неверная подпись Telegram. Открой приложение из Telegram.")

    # 2. Проверяем URL
    if not is_supported_url(req.url):
        raise HTTPException(400, "Неподдерживаемый сайт.")

    # 3. Запускаем скачивание в фоне (не блокируем ответ)
    asyncio.create_task(_download_and_send(req.url, req.user_id))

    return {"status": "downloading", "message": "Видео скачивается, скоро придёт в чат!"}


async def _download_and_send(url: str, user_id: int):
    """Фоновая задача: скачать видео и отправить пользователю."""
    filepath = None
    bot = Bot(token=TOKEN)
    try:
        # Уведомляем пользователя что начали скачивать
        await bot.send_message(user_id, "⏳ Скачиваю видео, подождите...")

        # Скачиваем (это синхронная операция — запускаем в executor)
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video, url)

        # Отправляем видео
        with open(filepath, "rb") as video_file:
            await bot.send_video(
                chat_id=user_id,
                video=video_file,
                caption="✅ Готово!",
                supports_streaming=True,
            )

    except Exception as e:
        logger.error(f"Download failed for user {user_id}: {e}")
        await bot.send_message(
            user_id,
            f"❌ Не удалось скачать видео.\n\nПричина: {str(e)}\n\n"
            "Попробуй другую ссылку или убедись, что пост публичный."
        )
    finally:
        # Всегда удаляем файл с сервера
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        await bot.session.close()

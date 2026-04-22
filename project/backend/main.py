"""
📁 backend/main.py
"""

import os
import asyncio
import logging
import hashlib
import hmac
from contextlib import asynccontextmanager
from urllib.parse import parse_qsl

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from aiogram.types import Update

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from downloader.core import download_video, is_supported_url, get_video_info
from bot.main import bot, dp

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def keep_alive():
    while True:
        await asyncio.sleep(300)
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{WEBHOOK_HOST}/health")
            logger.info("Keep-alive ping sent")
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(keep_alive())
    logger.info(f"Webhook set: {WEBHOOK_URL}")
    yield
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Webhook deleted")


app = FastAPI(title="Video Downloader API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)


@app.get("/")
async def root():
    return RedirectResponse(url="/app")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


class DownloadRequest(BaseModel):
    url: str
    user_id: int
    init_data: str


class InfoRequest(BaseModel):
    url: str


def verify_telegram_init_data(init_data: str, bot_token: str) -> bool:
    try:
        if not init_data:
            return False
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False
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


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/check-webhook")
async def check_webhook():
    info = await bot.get_webhook_info()
    return {
        "url": info.url,
        "pending_updates": info.pending_update_count,
        "last_error": info.last_error_message,
    } 

@app.post("/api/info")
async def video_info(req: InfoRequest):
    if not is_supported_url(req.url):
        raise HTTPException(400, "Неподдерживаемый сайт.")
    try:
        return get_video_info(req.url)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/download")
async def download(req: DownloadRequest):
    if not verify_telegram_init_data(req.init_data, TOKEN):
        raise HTTPException(403, "Неверная подпись Telegram.")
    if not is_supported_url(req.url):
        raise HTTPException(400, "Неподдерживаемый сайт.")
    asyncio.create_task(_download_and_send(req.url, req.user_id))
    return {"status": "downloading"}


async def _download_and_send(url: str, user_id: int):
    filepath = None
    try:
        await bot.send_message(user_id, "⏳ Скачиваю видео, подождите...")
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video, url)
        with open(filepath, "rb") as f:
            await bot.send_video(
                chat_id=user_id,
                video=f,
                caption="✅ Готово!",
                supports_streaming=True,
            )
    except Exception as e:
        logger.error(f"Download failed for {user_id}: {e}")
        await bot.send_message(user_id, f"❌ Не удалось скачать.\n\n{str(e)}")
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")
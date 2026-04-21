"""
📁 bot/main.py
Telegram-бот на webhook — без конфликтов при деплое.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # https://videodownloader-production-7dbf.up.railway.app
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()



@dp.message(Command("start"))
async def cmd_start(message: Message):
    webapp_url = os.getenv("WEBAPP_URL")
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🎬 Скачать видео",
        web_app=WebAppInfo(url=webapp_url)
    )
    await message.answer(
        "👋 Привет! Я скачиваю видео с YouTube, TikTok и Instagram.\n\n"
        "Нажми кнопку ниже, вставь ссылку — и видео придёт сюда в чат.",
        reply_markup=kb.as_markup()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Как пользоваться:</b>\n\n"
        "1. Нажми /start\n"
        "2. Открой приложение\n"
        "3. Вставь ссылку на видео\n"
        "4. Нажми «Скачать»\n"
        "5. Видео придёт прямо в этот чат\n\n"
        "<b>Поддерживаемые сайты:</b>\n"
        "✅ YouTube\n"
        "✅ TikTok\n"
        "✅ Instagram (только публичные посты)",
        parse_mode="HTML"
    )


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set: {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
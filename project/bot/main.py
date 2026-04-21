"""
📁 bot/main.py
Telegram-бот: показывает кнопку открытия Mini App и принимает команды.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

# БЫЛО:


# СТАЛО — добавь печать для диагностики:
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    webapp_url = os.getenv("WEBAPP_URL")  # читаем здесь
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🎬 Скачать видео",
        web_app=WebAppInfo(url=webapp_url)
    )
    await message.answer(
        "👋 Привет! Нажми кнопку ниже чтобы открыть приложение.",
        reply_markup=kb.as_markup()
    )




@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🎬 Скачать видео",
        web_app=WebAppInfo(url=WEBAPP_URL)
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


async def main():
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

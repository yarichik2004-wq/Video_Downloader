"""
📁 bot/main.py
Только хендлеры — без запуска сервера.
Webhook регистрирует backend/main.py
"""

import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    webapp_url = os.getenv("WEBAPP_URL")
    user_id = message.from_user.id
    # Передаём user_id в URL как параметр
    url_with_id = f"{webapp_url}?uid={user_id}"
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Скачать видео", web_app=WebAppInfo(url=url_with_id))
    await message.answer(
        "👋 Привет! Нажми кнопку ниже, вставь ссылку — и видео придёт сюда в чат.",
        reply_markup=kb.as_markup()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Поддерживаемые сайты", callback_data="faq_sites")
    kb.button(text="⚠️ Видео не скачивается", callback_data="faq_error")
    kb.button(text="📏 Лимит размера", callback_data="faq_limit")
    kb.adjust(1)
    await message.answer("❓ Чем могу помочь?", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "faq_sites")
async def faq_sites(call: CallbackQuery):
    await call.message.edit_text(
        "✅ <b>Поддерживаемые сайты:</b>\n\n"
        "▶ YouTube — любые публичные видео\n"
        "♪ TikTok — публичные посты\n"
        "◈ Instagram — только публичные посты\n\n"
        "Приватные страницы и сторис не поддерживаются.",
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "faq_error")
async def faq_error(call: CallbackQuery):
    await call.message.edit_text(
        "⚠️ <b>Если видео не скачивается:</b>\n\n"
        "1. Убедись что ссылка на публичное видео\n"
        "2. Попробуй скопировать ссылку заново\n"
        "3. Instagram иногда недоступен — попробуй YouTube или TikTok\n"
        "4. Видео может быть больше 50 МБ — Telegram не пропустит",
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "faq_limit")
async def faq_limit(call: CallbackQuery):
    await call.message.edit_text(
        "📏 <b>Лимит размера — 50 МБ</b>\n\n"
        "Это ограничение Telegram Bot API.\n"
        "Большинство коротких видео до 5-7 минут укладываются в лимит.\n\n"
        "Длинные видео с YouTube могут не пройти.",
        parse_mode="HTML"
    )
    await call.answer()
"""
📁 bot/main.py
Простой бот — принимает ссылку, скачивает видео, отправляет пользователю.
Никакого бэкенда, никакого Mini App.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from downloader.core import download_video, is_supported_url

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

SUPPORTED = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]


# ── Команды ───────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я скачиваю видео с YouTube, TikTok и Instagram.\n\n"
        "Просто отправь мне ссылку на видео — и я пришлю его сюда.\n\n"
        "▶ YouTube\n"
        "♪ TikTok\n"
        "◈ Instagram (только публичные посты)"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Поддерживаемые сайты", callback_data="faq_sites")
    kb.button(text="⚠️ Видео не скачивается", callback_data="faq_error")
    kb.button(text="📏 Лимит размера", callback_data="faq_limit")
    kb.adjust(1)
    await message.answer("❓ Чем могу помочь?", reply_markup=kb.as_markup())


# ── FAQ callbacks ─────────────────────────────────────────────────────────────

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
        "Большинство коротких видео до 5-7 минут укладываются в лимит.\n"
        "Длинные видео с YouTube могут не пройти.",
        parse_mode="HTML"
    )
    await call.answer()


# ── Обработка ссылок ──────────────────────────────────────────────────────────

@dp.message(F.text)
async def handle_message(message: Message):
    text = message.text.strip()

    # Проверяем что это ссылка на поддерживаемый сайт
    if not any(d in text for d in SUPPORTED):
        await message.answer(
            "🔗 Отправь мне ссылку на видео с YouTube, TikTok или Instagram."
        )
        return

    status = await message.answer("⏳ Скачиваю видео, подождите...")

    try:
        # Скачиваем в отдельном потоке чтобы не блокировать бота
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video, text)

        # Отправляем видео
        with open(filepath, "rb") as f:
            await message.answer_video(
                video=f,
                caption="✅ Готово!",
                supports_streaming=True,
            )

    except Exception as e:
        logger.error(f"Download failed: {e}")
        await message.answer(
            f"❌ Не удалось скачать видео.\n\n"
            f"Причина: {str(e)}\n\n"
            "Убедись что видео публичное и попробуй ещё раз."
        )
    finally:
        # Удаляем сообщение "скачиваю..."
        await status.delete()
        # Удаляем файл с сервера
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass


# ── Запуск ────────────────────────────────────────────────────────────────────

async def main():
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
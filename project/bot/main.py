import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

load_dotenv()

# Читаем переменные
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://my-app.up.railway.app
WEBHOOK_PATH = "/webhook"

# Убираем возможный лишний слэш в конце хоста
if WEBHOOK_HOST and WEBHOOK_HOST.endswith("/"):
    WEBHOOK_HOST = WEBHOOK_HOST[:-1]

WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ХЕНДЛЕРЫ ---

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
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Поддерживаемые сайты", callback_data="faq_sites")
    kb.button(text="⚠️ Ошибки", callback_data="faq_error")
    kb.button(text="📏 Лимиты", callback_data="faq_limit")
    kb.adjust(1)
    
    help_text = (
        "📖 <b>Как пользоваться:</b>\n"
        "1. Нажми кнопку «Скачать видео»\n"
        "2. Вставь ссылку в приложении\n"
        "3. Жди видео в этом чате\n\n"
        "❓ Выбери раздел ниже для подробностей:"
    )
    await message.answer(help_text, reply_markup=kb.as_markup(), parse_mode="HTML")

# --- FAQ CALLBACKS ---

@dp.callback_query(F.data.startswith("faq_"))
async def faq_handlers(call: CallbackQuery):
    responses = {
        "faq_sites": "✅ <b>YouTube, TikTok, Instagram</b> (публичные посты).",
        "faq_error": "⚠️ Проверь, что ссылка рабочая и видео не приватное.",
        "faq_limit": "📏 Лимит Telegram — <b>50 МБ</b> на файл."
    }
    await call.message.edit_text(responses.get(call.data, "Нет данных"), parse_mode="HTML")
    await call.answer()

# --- ЖИЗНЕННЫЙ ЦИКЛ WEBHOOK ---

async def on_startup(app):
    # Принудительно удаляем старый и ставим новый вебхук
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"🚀 Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("🛑 Webhook deleted")

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Регистрируем обработчик вебхука
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)
    
    # Railway использует порт 8080 (или PORT из окружения)
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
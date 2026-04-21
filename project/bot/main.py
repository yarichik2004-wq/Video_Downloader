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

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"

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
    kb.button(text="🎬 Скачать видео", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer(
        "👋 Привет! Нажми кнопку ниже, чтобы открыть приложение.",
        reply_markup=kb.as_markup()
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Поддерживаемые сайты", callback_data="faq_sites")
    kb.button(text="⚠️ Ошибки", callback_data="faq_error")
    kb.adjust(1)
    await message.answer("❓ Помощь по боту:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("faq_"))
async def faq_handlers(call: CallbackQuery):
    responses = {
        "faq_sites": "✅ YouTube, TikTok, Instagram.",
        "faq_error": "⚠️ Проверь ссылку, она должна быть публичной."
    }
    await call.message.edit_text(responses.get(call.data, "Инфо отсутствует"), parse_mode="HTML")
    await call.answer()

# --- ЛОГИКА ЗАПУСКА ---

async def on_startup(bot: Bot):
    # 1. Удаляем вебхук и ОЧИЩАЕМ накопившиеся сообщения (drop_pending_updates)
    # Это критично, чтобы убрать ошибку Conflict
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 2. Ставим вебхук заново
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"🚀 Webhook set to: {WEBHOOK_URL}")

def main():
    # Мы не используем dp.start_polling() здесь!
    
    app = web.Application()

    # Настраиваем обработчик запросов от Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Привязываем startup/shutdown к приложению aiohttp
    # Важно: передаем bot в setup_application
    setup_application(app, dp, bot=bot)

    # Регистрируем функцию on_startup через диспетчер aiogram
    dp.startup.register(on_startup)

    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
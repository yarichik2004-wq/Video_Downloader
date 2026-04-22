import yt_dlp
import os
import uuid
import logging
from dotenv import load_dotenv

# Загружаем переменные (если ты решишь вставить токен вручную в .env)
load_dotenv()

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024
# Путь к кукам (важно для YouTube)
COOKIES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")

# Список поддерживаемых доменов
SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]

def is_supported_url(url: str) -> bool:
    """Проверяет, поддерживается ли ссылка ботом."""
    return any(domain in url.lower() for domain in SUPPORTED_DOMAINS)

def is_youtube(url: str) -> bool:
    """Проверяет, является ли ссылка YouTube ссылкой."""
    return "youtube.com" in url.lower() or "youtu.be" in url.lower()

def download_video(url: str) -> str:
    """Скачивает видео, используя установленный плагин get-pot."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    # Получаем токены из .env на случай, если автоматика не сработает
    env_po_token = os.getenv("YT_PO_TOKEN")
    env_visitor_data = os.getenv("YT_VISITOR_DATA")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE,
        "quiet": False,  # Поставим False, чтобы ты видел прогресс в консоли
        "no_warnings": False,
        "noplaylist": True,
        "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        
        # Настройка эмуляции
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        
        "extractor_args": {
            "youtube": {
                # 1. Пытаемся использовать плагин get-pot автоматически
                "player_client": ["ios", "web_safari"],
                # 2. Если в .env есть токен, подставляем его как запасной вариант
                "po_token": [f"web+{env_po_token}"] if env_po_token else None,
            }
        },
    }

    # Добавляем visitor_data если он есть
    if env_visitor_data:
        ydl_opts["headers"] = {"X-Goog-Visitor-Id": env_visitor_data}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Начинаю загрузку: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Проверка расширения (мердж в mp4)
            if not os.path.exists(filename):
                mp4_path = os.path.splitext(filename)[0] + ".mp4"
                if os.path.exists(mp4_path):
                    filename = mp4_path
            
            return filename
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        raise e
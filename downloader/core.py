import yt_dlp
import os
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_PATH = os.path.join(BASE_DIR, "cookies.txt")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "videos")


MAX_FILESIZE = 50 * 1024 * 1024

SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]


def is_supported_url(url: str) -> bool:
    return any(domain in url.lower() for domain in SUPPORTED_DOMAINS)


def is_youtube(url: str) -> bool:
    return "youtube.com" in url.lower() or "youtu.be" in url.lower()


def download_video(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
    }

    if is_youtube(url):
        ydl_opts.update({
            "cookiefile": COOKIE_PATH,
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            # Ограничиваем качество, чтобы почти всегда влезало в 50MB
            "format": "best[height<=720][ext=mp4]/best",
            "sleep_interval": 1,
            "max_sleep_interval": 3,
        })
    else:
        ydl_opts.update({
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "format": "best"
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # Проверка расширения после скачивания
    if not os.path.exists(filename):
        base_path = os.path.splitext(filename)[0]
        if os.path.exists(base_path + ".mp4"):
            filename = base_path + ".mp4"
        elif os.path.exists(base_path + ".mkv"):
            filename = base_path + ".mkv"
        else:
            raise FileNotFoundError(f"Файл не найден: {filename}")

    # Проверка размера (важно для Telegram)
    size = os.path.getsize(filename)
    if size > MAX_FILESIZE:
        os.remove(filename)
        raise ValueError("Видео слишком большое (>50MB)")

    logger.info(f"Downloaded: {filename} ({size} bytes)")
    return filename


def get_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    if is_youtube(url):
        ydl_opts.update({
            "cookiefile": COOKIE_PATH,
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "title": info.get("title", "Video"),
        "duration": info.get("duration", 0),
        "filesize": info.get("filesize") or info.get("filesize_approx", 0),
    }
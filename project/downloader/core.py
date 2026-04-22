import yt_dlp
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024  # 50 MB
# Путь к файлу внутри контейнера (если положил в корень проекта)
COOKIES_PATH = os.path.join(os.getcwd(), "cookies.txt")

SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
]

def is_supported_url(url: str) -> bool:
    return any(domain in url for domain in SUPPORTED_DOMAINS)

def get_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "filesize": info.get("filesize") or info.get("filesize_approx", 0),
        }

def download_video(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        # ДОБАВЛЕНО: использование куки
        "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        # ДОБАВЛЕНО: стандартный User-Agent для надежности
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        mp4_path = os.path.splitext(filename)[0] + ".mp4"
        if os.path.exists(mp4_path):
            filename = mp4_path
        else:
            raise FileNotFoundError(f"Файл не найден после скачивания: {filename}")

    logger.info(f"Downloaded: {filename} ({os.path.getsize(filename)} bytes)")
    return filename
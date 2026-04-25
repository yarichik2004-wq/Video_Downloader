"""
📁 downloader/core.py
"""

import yt_dlp
import os
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024
COOKIES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]

# Прокси из переменных окружения
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
# Webshare rotating proxy — один адрес, автоматически ротирует между всеми 10
PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@p.webshare.io:80" if PROXY_USER else None


def is_supported_url(url: str) -> bool:
    return any(domain in url.lower() for domain in SUPPORTED_DOMAINS)


def is_youtube(url: str) -> bool:
    return "youtube.com" in url.lower() or "youtu.be" in url.lower()


def is_instagram(url: str) -> bool:
    return "instagram.com" in url.lower()


def download_video(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
    }

    if is_youtube(url):
        ydl_opts.update({
            "proxy": PROXY_URL,
            "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
            "extractor_args": {
                "youtube": {"player_client": ["web"]}
            },
        })
        logger.info(f"YouTube download via proxy: {PROXY_URL is not None}")

    elif is_instagram(url):
        ydl_opts.update({
            "proxy": PROXY_URL,
            "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        })
        logger.info(f"Instagram download via proxy: {PROXY_URL is not None}")

    else:
        # TikTok — работает без прокси
        ydl_opts.update({
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        logger.info("TikTok download without proxy")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        mp4_path = os.path.splitext(filename)[0] + ".mp4"
        if os.path.exists(mp4_path):
            filename = mp4_path
        else:
            raise FileNotFoundError(f"Файл не найден: {filename}")

    size = os.path.getsize(filename)
    if size > MAX_FILESIZE:
        os.remove(filename)
        raise ValueError("Видео слишком большое (>50MB)")

    logger.info(f"Downloaded: {filename} ({size} bytes)")
    return filename


def get_video_info(url: str) -> dict:
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "filesize": info.get("filesize") or info.get("filesize_approx", 0),
        }
"""
📁 downloader/core.py
YouTube через PO Token (автоматическая генерация), TikTok/Instagram через yt-dlp.
"""

import yt_dlp
import os
import uuid
import logging
import subprocess
import json
import time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024
COOKIES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]

# Кэш токена — генерируем раз в час
_po_token_cache = {"token": None, "visitor_data": None, "expires": 0}


def get_po_token() -> tuple[str, str]:
    """
    Возвращает (po_token, visitor_data).
    Сначала пробует из .env, потом генерирует автоматически через bgutil.
    Кэширует на 1 час.
    """
    now = time.time()

    # Из переменных окружения (ручной токен)
    env_token = os.getenv("YT_PO_TOKEN")
    env_visitor = os.getenv("YT_VISITOR_DATA")
    if env_token and env_visitor:
        logger.info("Using PO Token from environment")
        return env_token, env_visitor

    # Из кэша
    if _po_token_cache["token"] and now < _po_token_cache["expires"]:
        logger.info("Using cached PO Token")
        return _po_token_cache["token"], _po_token_cache["visitor_data"]

    # Генерируем новый через bgutil
    logger.info("Generating new PO Token via bgutil...")
    try:
        result = subprocess.run(
            ["node", "-e", """
                const { BgUtils } = require('@ybd-project/yt-dlp-utils');
                BgUtils.generatePoToken().then(data => {
                    console.log(JSON.stringify(data));
                }).catch(e => {
                    console.error(e.message);
                    process.exit(1);
                });
            """],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise Exception(f"bgutil error: {result.stderr}")

        data = json.loads(result.stdout.strip())
        token = data.get("poToken") or data.get("po_token")
        visitor = data.get("visitorData") or data.get("visitor_data")

        if not token:
            raise Exception("bgutil вернул пустой токен")

        # Кэшируем на 1 час
        _po_token_cache["token"] = token
        _po_token_cache["visitor_data"] = visitor
        _po_token_cache["expires"] = now + 3600

        logger.info("PO Token generated successfully")
        return token, visitor

    except Exception as e:
        logger.warning(f"Failed to generate PO Token: {e}. Trying without token.")
        return None, None


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
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
    }

    # Для YouTube добавляем PO Token
    if is_youtube(url):
        po_token, visitor_data = get_po_token()
        if po_token:
            ydl_opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["web"],
                    "po_token": [f"web+{po_token}"],
                }
            }
            if visitor_data:
                ydl_opts["headers"] = {"X-Goog-Visitor-Id": visitor_data}
            logger.info("YouTube download with PO Token")
        else:
            # Fallback без токена
            ydl_opts["extractor_args"] = {
                "youtube": {"player_client": ["ios"]}
            }
            logger.info("YouTube download without PO Token (fallback)")
    else:
        # TikTok / Instagram
        ydl_opts["user_agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        mp4_path = os.path.splitext(filename)[0] + ".mp4"
        if os.path.exists(mp4_path):
            filename = mp4_path
        else:
            raise FileNotFoundError(f"Файл не найден: {filename}")

    logger.info(f"Downloaded: {filename} ({os.path.getsize(filename)} bytes)")
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
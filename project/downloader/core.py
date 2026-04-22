"""
📁 downloader/core.py
Скачивание через cobalt.tools API (YouTube) и yt-dlp (TikTok, Instagram).
"""

import yt_dlp
import os
import uuid
import logging
import requests

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024
COOKIES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")

SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]


def is_supported_url(url: str) -> bool:
    return any(domain in url for domain in SUPPORTED_DOMAINS)


def is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def download_via_cobalt(url: str) -> str:
    """Скачивает YouTube видео через cobalt.tools API."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    unique_id = uuid.uuid4().hex
    filepath = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp4")

    # Запрашиваем ссылку для скачивания
    res = requests.post(
        "https://api.cobalt.tools/",
        json={
            "url": url,
            "videoQuality": "720",
            "filenameStyle": "basic",
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    data = res.json()
    logger.info(f"Cobalt response: {data}")

    status = data.get("status")
    if status not in ["stream", "redirect", "tunnel"]:
        error = data.get("error", {})
        if isinstance(error, dict):
            raise Exception(f"Cobalt error: {error.get('code', 'unknown')}")
        raise Exception(f"Cobalt error: {error}")

    download_url = data.get("url")
    if not download_url:
        raise Exception("Cobalt не вернул ссылку для скачивания")

    # Скачиваем файл
    logger.info(f"Downloading from: {download_url}")
    response = requests.get(download_url, timeout=120, stream=True)
    response.raise_for_status()

    size = 0
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                size += len(chunk)
                if size > MAX_FILESIZE:
                    raise Exception("Видео слишком большое (больше 50 МБ)")
                f.write(chunk)

    logger.info(f"Downloaded via cobalt: {filepath} ({size} bytes)")
    return filepath


def download_via_ytdlp(url: str) -> str:
    """Скачивает TikTok/Instagram через yt-dlp."""
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
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        mp4_path = os.path.splitext(filename)[0] + ".mp4"
        if os.path.exists(mp4_path):
            filename = mp4_path
        else:
            raise FileNotFoundError(f"Файл не найден: {filename}")

    logger.info(f"Downloaded via yt-dlp: {filename} ({os.path.getsize(filename)} bytes)")
    return filename


def download_video(url: str) -> str:
    """Универсальная функция — выбирает метод в зависимости от платформы."""
    if is_youtube(url):
        return download_via_cobalt(url)
    else:
        return download_via_ytdlp(url)


def get_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "filesize": info.get("filesize") or info.get("filesize_approx", 0),
        }
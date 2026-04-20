"""
📁 downloader/core.py
Логика скачивания видео через yt-dlp.
"""

import yt_dlp
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/videos"
MAX_FILESIZE = 50 * 1024 * 1024  # 50 MB — лимит Telegram Bot API

# Поддерживаемые домены
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
]


def is_supported_url(url: str) -> bool:
    """Проверяет, что URL принадлежит поддерживаемому сайту."""
    return any(domain in url for domain in SUPPORTED_DOMAINS)


def get_video_info(url: str) -> dict:
    """Возвращает метаданные видео без скачивания."""
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


def download_video(url: str) -> str:
    """
    Скачивает видео по URL.
    Возвращает путь к скачанному файлу.
    Бросает исключение при ошибке.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Уникальное имя файла, чтобы не было коллизий при параллельных запросах
    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        # Выбираем лучшее качество с ограничением по размеру
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,       # Только одно видео, не весь плейлист
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # prepare_filename возвращает итоговый путь с правильным расширением
        filename = ydl.prepare_filename(info)

    # После merge_output_format расширение может поменяться на .mp4
    if not os.path.exists(filename):
        mp4_path = os.path.splitext(filename)[0] + ".mp4"
        if os.path.exists(mp4_path):
            filename = mp4_path
        else:
            raise FileNotFoundError(f"Файл не найден после скачивания: {filename}")

    logger.info(f"Downloaded: {filename} ({os.path.getsize(filename)} bytes)")
    return filename

"""
Instagram Reel downloader service using yt-dlp.
Public reels can be fetched without authentication.
"""

import uuid
from pathlib import Path

import yt_dlp

from config.settings import settings


class InstagramFetchError(Exception):
    def __init__(self, user_message: str, technical_detail: str = ""):
        self.user_message = user_message
        self.technical_detail = technical_detail
        super().__init__(technical_detail or user_message)


def download_instagram_reel(url: str, video_id: uuid.UUID) -> dict:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "mp4/best",
        "outtmpl": str(upload_dir / f"{video_id}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            saved_path = Path(ydl.prepare_filename(info))
            if not saved_path.exists():
                saved_path = saved_path.with_suffix(".mp4")
    except Exception as e:
        raise InstagramFetchError(
            user_message="We couldn't fetch this reel. Please upload the file directly instead.",
            technical_detail=str(e),
        )

    return {
        "storage_path": str(saved_path),
        "original_filename": info.get("title", "instagram_reel") + ".mp4",
        "file_size_bytes": saved_path.stat().st_size,
    }

"""
YouTube downloader service using yt-dlp.
Downloads a YouTube video to local storage, returning the same kind of
metadata our upload flow produces — so both paths feed the same pipeline.
Tries multiple player client identities in order — YouTube's bot detection
targets one client type at a time, so falling back to another often works.
"""

import uuid
from pathlib import Path

import yt_dlp

from config.settings import settings


def download_youtube_video(url: str, video_id: uuid.UUID) -> dict:
    """
    Downloads a YouTube video and returns its saved path, original title,
    and file size — mirroring what the upload endpoint captures manually.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(upload_dir / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "tv"],
            }
        },
    }

    if settings.PROXY_HOST and settings.PROXY_PORT:
        proxy_url = (
            f"socks5h://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}"
            f"@{settings.PROXY_HOST}:{settings.PROXY_PORT}"
        )
        ydl_opts["proxy"] = proxy_url

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        saved_path = ydl.prepare_filename(info)

        actual_path = Path(saved_path)
        if not actual_path.exists():
            actual_path = actual_path.with_suffix(".mp4")

    return {
        "storage_path": str(actual_path),
        "original_filename": info.get("title", "youtube_video") + ".mp4",
        "file_size_bytes": actual_path.stat().st_size,
    }
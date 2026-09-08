"""
YouTube downloader service with layered fallback strategy.
Tries direct fetch first, falls back to cookie-auth, then Invidious mirror.
Never surfaces raw yt-dlp errors to the caller — maps to a friendly result.
"""

import logging
import uuid
from pathlib import Path

import yt_dlp

from config.settings import settings

logger = logging.getLogger(__name__)

INVIDIOUS_INSTANCES = [
    "inv.nadeko.net",
    "yt.chocolatemoo53.com",
    "invidious.tiekoetter.com",
]


class YouTubeFetchError(Exception):
    """Raised when all fallback methods are exhausted. Carries a user-facing message."""
    def __init__(self, user_message: str, technical_detail: str = ""):
        self.user_message = user_message
        self.technical_detail = technical_detail
        super().__init__(technical_detail or user_message)


def _base_ydl_opts(video_id: uuid.UUID) -> dict:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return {
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "outtmpl": str(upload_dir / f"{video_id}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }


def _run_download(url: str, video_id: uuid.UUID, ydl_opts: dict) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        saved_path = Path(ydl.prepare_filename(info))
        if not saved_path.exists():
            saved_path = saved_path.with_suffix(".mp4")

    return {
        "storage_path": str(saved_path),
        "original_filename": info.get("title", "youtube_video") + ".mp4",
        "file_size_bytes": saved_path.stat().st_size,
    }


def _try_direct_android(url: str, video_id: uuid.UUID) -> dict:
    opts = _base_ydl_opts(video_id)
    opts["extractor_args"] = {
        "youtube": {
            "player_client": ["android"],
            "player_skip": ["webpage", "configs"],
        }
    }
    return _run_download(url, video_id, opts)


def _try_with_cookies(url: str, video_id: uuid.UUID) -> dict:
    if not settings.YOUTUBE_COOKIES_PATH or not Path(settings.YOUTUBE_COOKIES_PATH).exists():
        raise YouTubeFetchError("cookies not configured", "no cookiefile set")

    opts = _base_ydl_opts(video_id)
    opts["cookiefile"] = str(settings.YOUTUBE_COOKIES_PATH)
    opts["extractor_args"] = {
        "youtube": {"player_client": ["android"]}
    }
    return _run_download(url, video_id, opts)


def _try_invidious_mirror(url: str, video_id: uuid.UUID) -> dict:
    last_err = None
    for instance in INVIDIOUS_INSTANCES:
        mirrored_url = (
            url.replace("www.youtube.com", instance)
               .replace("youtube.com", instance)
               .replace("youtu.be", instance)
        )
        try:
            opts = _base_ydl_opts(video_id)
            return _run_download(mirrored_url, video_id, opts)
        except Exception as e:
            last_err = e
            continue
    raise last_err or YouTubeFetchError("all invidious instances failed")


def download_youtube_video(url: str, video_id: uuid.UUID) -> dict:
    """
    Attempts to fetch a YouTube video via layered fallback:
    1. Direct android-client fetch (fast, free)
    2. Cookie-authenticated fetch (if configured)
    3. Invidious mirror (last resort)

    Raises YouTubeFetchError with a friendly message if every method fails —
    callers should catch this and surface .user_message to the frontend,
    prompting the user to upload the file directly instead.
    """
    attempts = [
        ("direct_android", _try_direct_android),
        ("cookies", _try_with_cookies),
        ("invidious", _try_invidious_mirror),
    ]

    last_exception = None
    for name, fn in attempts:
        try:
            result = fn(url, video_id)
            logger.info(f"YouTube fetch succeeded via '{name}' for video_id={video_id}")
            return result
        except Exception as e:
            logger.warning(f"YouTube fetch method '{name}' failed for video_id={video_id}: {e}")
            last_exception = e
            continue

    raise YouTubeFetchError(
        user_message="We couldn't automatically fetch this video. Please upload the file directly instead.",
        technical_detail=str(last_exception),
    )
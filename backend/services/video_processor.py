"""
Video processing service — wraps FFmpeg commands.
Handles audio extraction, duration lookup, and clip cutting with
optional aspect ratio cropping and burned-in captions.
"""

import subprocess
from pathlib import Path

ASPECT_RATIO_FILTERS = {
    "16:9": "crop='min(iw,ih*16/9)':'min(ih,iw*9/16)'",
    "9:16": "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'",
    "1:1": "crop='min(iw,ih)':'min(iw,ih)'",
}


def extract_audio(video_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")


def get_video_duration_seconds(video_path: str) -> float:
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    return float(result.stdout.strip())


def cut_clip(
    source_video_path: str,
    output_path: str,
    start_seconds: float,
    end_seconds: float,
    aspect_ratio: str = "original",
    subtitle_path: str | None = None,
) -> None:
    """
    Cuts a segment out of a source video and saves it as its own file.
    Optionally crops to a target aspect ratio, and optionally burns in
    captions from a provided .srt file.
    """
    duration = end_seconds - start_seconds

    video_filters = []
    if aspect_ratio in ASPECT_RATIO_FILTERS:
        video_filters.append(ASPECT_RATIO_FILTERS[aspect_ratio])

    if subtitle_path:
        # Style: white bold text, black outline, positioned near the bottom.
        # FFmpeg's subtitles filter needs the path escaped carefully since
        # colons and backslashes have special meaning inside filter strings.
        escaped_path = subtitle_path.replace("\\", "\\\\").replace(":", "\\:")
        style = "FontSize=14,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2"
        video_filters.append(f"subtitles='{escaped_path}':force_style='{style}'")

    command = [
        "ffmpeg",
        "-i", source_video_path,
        "-ss", str(start_seconds),
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
    ]

    if video_filters:
        command.extend(["-vf", ",".join(video_filters)])

    command.extend(["-y", output_path])

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg clip cutting failed: {result.stderr}")
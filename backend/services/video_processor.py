"""
Video processing service — wraps FFmpeg commands.
Currently handles audio extraction; will grow to handle clip cutting,
reframing, and caption burning in later modules.
"""

import subprocess
from pathlib import Path


def extract_audio(video_path: str, output_path: str) -> None:
    """
    Extracts the audio track from a video file and saves it as a .wav file
    (the format Whisper expects).

    Uses FFmpeg via subprocess rather than a Python wrapper library —
    this keeps us in full control of exact FFmpeg flags and versions.
    """
    command = [
        "ffmpeg",
        "-i", video_path,       # input file
        "-vn",                   # strip video stream — audio only
        "-acodec", "pcm_s16le",  # standard uncompressed WAV format
        "-ar", "16000",          # 16kHz sample rate — what Whisper expects
        "-ac", "1",              # mono audio — smaller, and Whisper doesn't need stereo
        "-y",                    # overwrite output file if it already exists
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")


def get_video_duration_seconds(video_path: str) -> float:
    """
    Uses ffprobe (bundled with FFmpeg) to read a video's duration,
    without extracting anything. Used to fill in Video.duration_seconds.
    """
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

"""
Video compilation service.
Takes a list of (image, audio) pairs — one per scene — and stitches them
into a single video using FFmpeg, with a subtle pan/zoom effect on each
image so it doesn't look like a static slideshow.
"""

import subprocess
from pathlib import Path


def get_audio_duration_seconds(audio_path: str) -> float:
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def create_scene_clip(image_path: str, audio_path: str, output_path: str) -> None:
    """
    Creates a single video segment from one image + its narration audio,
    with a slow zoom-in effect ("Ken Burns") lasting exactly as long as
    the audio.
    """
    duration = get_audio_duration_seconds(audio_path)
    fps = 30
    total_frames = int(duration * fps)

    # zoompan: slowly zooms in over the image's full duration.
    # scale first to a large size so the zoom has room to work with
    # cleanly, matching 1920x1080 output.
    zoom_filter = (
        f"scale=3840:2160,"
        f"zoompan=z='min(zoom+0.0008,1.3)':d={total_frames}:s=1920x1080:fps={fps}"
    )

    command = [
        "ffmpeg",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-vf", zoom_filter,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-y",
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg scene clip creation failed: {result.stderr}")


def concatenate_clips(clip_paths: list[str], output_path: str) -> None:
    """
    Joins a list of video clips into one final video, in order.
    """
    concat_list_path = str(Path(output_path).with_suffix(".txt"))
    with open(concat_list_path, "w") as f:
        for path in clip_paths:
            f.write(f"file '{Path(path).resolve()}'\n")

    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        "-y",
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concatenation failed: {result.stderr}")
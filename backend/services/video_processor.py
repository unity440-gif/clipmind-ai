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

# How big a gap between spoken segments has to be (in seconds) before
# it's treated as "dead air" worth cutting, per intensity level.
SILENCE_GAP_THRESHOLDS = {
    "low": 1.5,
    "medium": 1.0,
    "high": 0.6,
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


def get_ranges_with_silence_removed(
    segments: list[dict],
    clip_start: float,
    clip_end: float,
    intensity: str = "medium",
) -> list[tuple[float, float]]:
    """
    Given the full video's transcript segments and a clip's start/end
    range, returns a list of (start, end) sub-ranges to KEEP — skipping
    gaps between segments that are longer than the intensity's threshold.
    """
    gap_threshold = SILENCE_GAP_THRESHOLDS.get(intensity, SILENCE_GAP_THRESHOLDS["medium"])

    relevant = [
        s for s in segments
        if s["end"] > clip_start and s["start"] < clip_end
    ]
    relevant.sort(key=lambda s: s["start"])

    if not relevant:
        return [(clip_start, clip_end)]

    ranges_to_keep = []
    current_start = max(clip_start, relevant[0]["start"])
    previous_end = current_start

    for segment in relevant:
        seg_start = max(segment["start"], clip_start)
        seg_end = min(segment["end"], clip_end)

        gap = seg_start - previous_end
        if gap > gap_threshold:
            ranges_to_keep.append((current_start, previous_end))
            current_start = seg_start

        previous_end = seg_end

    ranges_to_keep.append((current_start, previous_end))

    ranges_to_keep = [
        (s, min(e, clip_end)) for s, e in ranges_to_keep if s < clip_end
    ]

    return ranges_to_keep


def cut_clip_with_silence_removed(
    source_video_path: str,
    output_path: str,
    start_seconds: float,
    end_seconds: float,
    segments: list[dict],
    intensity: str = "medium",
    aspect_ratio: str = "original",
) -> None:
    """
    Like cut_clip, but first removes dead-air gaps between spoken
    segments before producing the final clip. Captions are not
    supported in this path yet.
    """
    from services.video_compiler_service import concatenate_clips

    ranges = get_ranges_with_silence_removed(segments, start_seconds, end_seconds, intensity)

    if len(ranges) == 1:
        cut_clip(source_video_path, output_path, ranges[0][0], ranges[0][1], aspect_ratio)
        return

    output_dir = Path(output_path).parent
    output_stem = Path(output_path).stem
    sub_clip_paths = []

    for i, (sub_start, sub_end) in enumerate(ranges):
        if sub_end - sub_start < 0.05:
            continue
        sub_path = output_dir / f"{output_stem}_part{i}.mp4"
        cut_clip(source_video_path, str(sub_path), sub_start, sub_end, aspect_ratio)
        sub_clip_paths.append(str(sub_path))

    try:
        concatenate_clips(sub_clip_paths, output_path)
    finally:
        for p in sub_clip_paths:
            if Path(p).exists():
                Path(p).unlink()
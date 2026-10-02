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


def create_scene_clip(image_path: str, audio_path: str, output_path: str) -> None:
    """
    Creates a single video segment from one image + its narration audio,
    with a slow zoom-in effect ("Ken Burns") lasting exactly as long as
    the audio.
    """
    duration = get_audio_duration_seconds(audio_path)
    fps = 30
    total_frames = int(duration * fps)

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
    Joins a list of video clips into one final video, in order, with a
    hard cut between each — fast (stream copy, no re-encoding) but no
    transition effect.
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


def concatenate_clips_with_transitions(
    clip_paths: list[str],
    output_path: str,
    transition: str = "fade",
    transition_duration: float = 0.5,
) -> None:
    """
    Joins clips with a crossfade-style transition between each pair,
    instead of a hard cut — gives the "rolling into the next clip" flow
    effect rather than a straight concatenation.

    Requires re-encoding (can't use stream copy like concatenate_clips),
    so this is slower but produces an actual blended transition.

    `transition` can be any FFmpeg xfade transition name — e.g. "fade",
    "wipeleft", "slideup", "circleopen", "dissolve". Full list is in
    FFmpeg's xfade filter docs.
    """
    if len(clip_paths) < 2:
        # Nothing to transition between — just copy the single clip through.
        concatenate_clips(clip_paths, output_path)
        return

    durations = [get_video_duration_seconds(p) for p in clip_paths]

    inputs = []
    for path in clip_paths:
        inputs += ["-i", path]

    # Chain xfade (video) and acrossfade (audio) across every adjacent
    # pair of clips. Each xfade's "offset" is where in the *running*
    # output timeline the transition should start — i.e. cumulative
    # duration so far, minus the overlaps already consumed.
    filter_parts = []
    running_duration = durations[0]
    prev_video_label = "0:v"
    prev_audio_label = "0:a"

    for i in range(1, len(clip_paths)):
        offset = running_duration - transition_duration
        video_label = f"v{i}"
        audio_label = f"a{i}"

        filter_parts.append(
            f"[{prev_video_label}][{i}:v]xfade=transition={transition}:"
            f"duration={transition_duration}:offset={offset}[{video_label}]"
        )
        filter_parts.append(
            f"[{prev_audio_label}][{i}:a]acrossfade=d={transition_duration}[{audio_label}]"
        )

        prev_video_label = video_label
        prev_audio_label = audio_label
        running_duration += durations[i] - transition_duration

    filter_complex = ";".join(filter_parts)

    command = [
        "ffmpeg",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev_video_label}]",
        "-map", f"[{prev_audio_label}]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y",
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg crossfade concatenation failed: {result.stderr}")
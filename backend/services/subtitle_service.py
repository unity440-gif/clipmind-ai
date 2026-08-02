"""
Subtitle generation service.
Takes Whisper's segment-level timing data and produces a standard .srt
subtitle file scoped to a single clip's time range, ready to be burned
into the video by FFmpeg. Also supports parsing/writing .srt files
directly, used by the caption-editing feature.
"""

import json
import re


def _format_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _parse_srt_timestamp(ts: str) -> float:
    """Converts 'HH:MM:SS,mmm' back into a float number of seconds."""
    hours, minutes, rest = ts.split(":")
    secs, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000


def generate_srt_for_clip(
    segments_path: str,
    clip_start: float,
    clip_end: float,
    output_srt_path: str,
) -> None:
    with open(segments_path, "r") as f:
        all_segments = json.load(f)

    relevant = [
        seg for seg in all_segments
        if seg["end"] > clip_start and seg["start"] < clip_end
    ]

    entries = []
    for seg in relevant:
        start = max(seg["start"], clip_start) - clip_start
        end = min(seg["end"], clip_end) - clip_start
        entries.append({"start": start, "end": end, "text": seg["text"]})

    write_srt_file(entries, output_srt_path)


def write_srt_file(entries: list[dict], output_path: str) -> None:
    """
    Writes a list of {"start": float, "end": float, "text": str} entries
    (an "index" key is ignored if present) as a standard .srt file.
    """
    lines = []
    for i, entry in enumerate(entries, start=1):
        lines.append(str(i))
        lines.append(
            f"{_format_srt_timestamp(entry['start'])} --> {_format_srt_timestamp(entry['end'])}"
        )
        lines.append(entry["text"])
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def parse_srt_file(path: str) -> list[dict]:
    """
    Reads a .srt file back into a list of editable entries:
    [{"index": int, "start": float, "end": float, "text": str}, ...]
    """
    with open(path, "r") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    entries = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        index = int(lines[0].strip())
        start_str, end_str = [t.strip() for t in lines[1].split("-->")]
        text = " ".join(lines[2:]).strip()

        entries.append({
            "index": index,
            "start": _parse_srt_timestamp(start_str),
            "end": _parse_srt_timestamp(end_str),
            "text": text,
        })

    return entries
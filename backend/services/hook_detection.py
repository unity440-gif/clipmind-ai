"""
AI hook-detection service.
Sends a video transcript to OpenRouter and asks it to identify the best
short-form clips, returning structured data matching our Clip model.
"""

import json

from services.openrouter_service import call_openrouter

HOOK_DETECTION_PROMPT_TEMPLATE = """You are an expert short-form video editor who has produced hundreds of viral TikTok, Instagram Reels, and YouTube Shorts clips. You have a deep understanding of what makes viewers stop scrolling in the first 2 seconds and watch to the end.

Analyze the following video transcript (with timestamps) and identify the {num_clips} best possible clips for short-form vertical video platforms.

RULES:
- Each clip must be between {min_duration} and {max_duration} seconds long.
- Each clip must work as a STANDALONE piece of content — it needs a strong hook in its first 3 seconds, a clear payoff, and should not require outside context to make sense.
- Prioritize moments with: strong emotion, a surprising claim, a clear before/after, a controversial or counter-intuitive statement, a concrete story with stakes, or a punchy one-line insight.
- Do not choose overlapping time ranges.
- Base start/end times strictly on the timestamps given — do not invent times outside the transcript's range.

TRANSCRIPT:
{transcript}

Respond with ONLY a valid JSON array (no markdown, no explanation, no code fences) where each object has exactly this shape:

[
  {{
    "start_time_seconds": <number>,
    "end_time_seconds": <number>,
    "title": "<short punchy title for this clip>",
    "hook": "<the exact opening line/moment that hooks viewers>",
    "summary": "<2-3 sentence summary of what happens in this clip>",
    "reason": "<why this clip will perform well, referencing specific psychological/attention principles>",
    "virality_score": <integer 1-100>,
    "confidence_score": <integer 1-100>,
    "tiktok_caption": "<caption with relevant emojis, TikTok style>",
    "instagram_caption": "<caption, Instagram Reels style>",
    "youtube_caption": "<caption, YouTube Shorts style>",
    "hashtags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"]
  }}
]"""


def build_hook_detection_prompt(
    transcript: str,
    num_clips: int = 5,
    min_duration: int = 60,
    max_duration: int = 120,
) -> str:
    return HOOK_DETECTION_PROMPT_TEMPLATE.format(
        transcript=transcript,
        num_clips=num_clips,
        min_duration=min_duration,
        max_duration=max_duration,
    )


def detect_hooks(
    transcript: str,
    num_clips: int = 5,
    min_duration: int = 60,
    max_duration: int = 120,
    model: str = "claude-sonnet",
) -> list[dict]:
    """
    Calls OpenRouter with the hook-detection prompt and parses the JSON response
    into a list of clip dictionaries, ready to save as Clip rows.
    """
    prompt = build_hook_detection_prompt(transcript, num_clips, min_duration, max_duration)
    raw_response = call_openrouter(prompt, model=model)

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        clips = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {e}\nRaw response: {raw_response}")

    return clips
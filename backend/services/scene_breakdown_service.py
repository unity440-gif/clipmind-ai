"""
Scene breakdown service.
Sends a user's script to OpenRouter and asks it to split it into scenes,
each with an image description (for image generation) and narration
text (for text-to-speech).
"""

import json

from services.openrouter_service import call_openrouter

SCENE_BREAKDOWN_PROMPT_TEMPLATE = """You are a professional storyboard artist and video director. Break the following script into a sequence of distinct visual scenes suitable for turning into a narrated slideshow-style video.

RULES:
- Each scene should represent one clear visual moment or beat in the story.
- Aim for scenes that are roughly 5-15 seconds of narration each.
- "description" should be a vivid, specific image-generation prompt describing exactly what should be shown — style, setting, characters, mood, lighting.
- "narration" should be the exact words to be spoken aloud for that scene, drawn from or adapted from the script.
- Keep character appearance descriptions CONSISTENT across scenes (same described hair color, clothing, etc.) if the same character appears in multiple scenes, since each image is generated independently.

SCRIPT:
{script}

Respond with ONLY a valid JSON array (no markdown, no explanation, no code fences) where each object has exactly this shape:

[
  {{
    "scene_number": <integer, starting at 1>,
    "description": "<vivid image-generation prompt for this scene>",
    "narration": "<exact narration text for this scene>"
  }}
]"""


def break_down_script(script: str) -> list[dict]:
    """
    Calls OpenRouter to break a script into a list of scene dictionaries.
    """
    prompt = SCENE_BREAKDOWN_PROMPT_TEMPLATE.format(script=script)
    raw_response = call_openrouter(prompt, model="claude-sonnet")

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        scenes = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {e}\nRaw response: {raw_response}")

    return scenes
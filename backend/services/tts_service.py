"""
Text-to-speech service using OpenRouter's dedicated Audio Speech API.
Uses Fish Audio's free-tier model, with a curated set of real public
voice IDs from Fish Audio's own voice library.
"""

import uuid
from pathlib import Path

import httpx

from config.settings import settings

OPENROUTER_SPEECH_URL = "https://openrouter.ai/api/v1/audio/speech"

TTS_MODEL = "fish-audio/s2.1-pro-free:free"

NARRATOR_VOICES = {
    "adrian": "bf322df2096a46f18c579d0baa36f41d",       # male
    "laura": "e3cd384158934cc9a01029cd7d278634",         # female
    "ethan": "536d3a5e000945adb7038665781a4aca",         # male
    "male-child": "d4708472472c406286f5ba27cc4ac1d7",
    "female-child": "0c0f9d7d87e44e2dabb53ebb092f5f53",
    "story-narrator": "85f74fd86bee4150a3696e691e773081",
}


def generate_speech(text: str, voice: str | None = None) -> dict:
    """
    Generates speech audio from text using one of the curated narrator voices.
    If no voice is specified (or an unknown one is given), the provider's
    own default voice is used instead.
    """
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": TTS_MODEL,
        "input": text,
        "response_format": "mp3",
    }

    voice_id = NARRATOR_VOICES.get(voice) if voice else None
    if voice_id:
        payload["voice"] = voice_id

    response = httpx.post(OPENROUTER_SPEECH_URL, headers=headers, json=payload, timeout=90.0)

    if response.status_code != 200:
        raise RuntimeError(f"TTS generation failed: {response.text}")

    audio_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / f"speech_{audio_id}.mp3"

    with open(output_path, "wb") as f:
        f.write(response.content)

    return {
        "storage_path": str(output_path),
        "filename": f"speech_{audio_id}.mp3",
    }
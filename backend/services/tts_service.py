"""
Text-to-speech service using OpenRouter's dedicated Audio Speech API.
Uses Fish Audio's free-tier model. Supports picking from a small set of
known public voice IDs, or the provider's default if none is specified.
"""

import uuid
from pathlib import Path

import httpx

from config.settings import settings

OPENROUTER_SPEECH_URL = "https://openrouter.ai/api/v1/audio/speech"

TTS_MODEL = "fish-audio/s2.1-pro-free:free"

# Known public voice reference IDs from Fish Audio's own voice library.
# "default" means: omit the voice parameter entirely, letting the
# provider pick its own default voice.
NARRATOR_VOICES = {
    "default": None,
    "narrator-2": "933563129e564b19a115bedd57b7406a",
}


def generate_speech(text: str, voice: str | None = None) -> dict:
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
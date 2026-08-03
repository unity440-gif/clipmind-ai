"""
Image generation service using OpenRouter's dedicated Image API.
Sends a text prompt, receives a base64-encoded image back, and saves
it to disk — completely separate from the video pipeline, but reusing
the same OpenRouter API key.
"""

import base64
import uuid
from pathlib import Path

import httpx

from config.settings import settings

OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"

# A few free/cheap image models available through OpenRouter.
# "flash" is Google's fast, low-cost option — good default.
IMAGE_MODELS = {
    "flash": "google/gemini-2.5-flash-image",
    "gpt-image": "openai/gpt-image-2",
}


def generate_image(prompt: str, model: str = "flash", aspect_ratio: str = "1:1") -> dict:
    """
    Generates an image from a text prompt and saves it to the uploads folder.
    Returns a dict with the saved file path and filename.
    """
    if model not in IMAGE_MODELS:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(IMAGE_MODELS.keys())}")

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": IMAGE_MODELS[model],
        "prompt": prompt,
        "image_config": {
            "aspect_ratio": aspect_ratio,
        },
    }

    response = httpx.post(OPENROUTER_IMAGES_URL, headers=headers, json=payload, timeout=90.0)
    response.raise_for_status()

    data = response.json()

    # OpenRouter returns images as base64-encoded data URLs
    # (format: "data:image/png;base64,<actual base64 data>")
    image_data_url = data["data"][0]["b64_json"] if "b64_json" in data.get("data", [{}])[0] else None
    if not image_data_url:
        # Some response shapes nest it under choices/message/images instead
        image_data_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
        image_data_url = image_data_url.split(",", 1)[1]  # strip the "data:image/png;base64," prefix
    else:
        image_data_url = image_data_url

    image_bytes = base64.b64decode(image_data_url)

    image_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / f"image_{image_id}.png"

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return {
        "storage_path": str(output_path),
        "filename": f"image_{image_id}.png",
    }
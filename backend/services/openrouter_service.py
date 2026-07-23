"""
OpenRouter service — the ONLY place in the codebase that talks to AI models.
Every AI feature (hook detection, caption generation, etc.) goes through this file.
Supports switching between GPT-5.5, Claude Sonnet, Claude Opus, Gemini, and DeepSeek
just by changing the `model` argument — OpenRouter normalizes the API across providers.
"""

import httpx

from config.settings import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Friendly names mapped to OpenRouter's actual model identifiers.
# Update these strings if OpenRouter changes a model's slug.
MODELS = {
    "gpt-5.5": "openai/gpt-5.5",
    "claude-sonnet": "anthropic/claude-sonnet-4.5",
    "claude-opus": "anthropic/claude-opus-4.5",
    "gemini": "google/gemini-2.5-pro",
    "deepseek": "deepseek/deepseek-chat",
}


def call_openrouter(prompt: str, model: str = "claude-sonnet") -> str:
    """
    Sends a single prompt to OpenRouter and returns the model's text response.
    Raises an exception if the request fails, so callers can handle/log errors.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODELS.keys())}")

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODELS[model],
        "messages": [{"role": "user", "content": prompt}],
    }

    response = httpx.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()  # raises an exception on 4xx/5xx responses

    data = response.json()
    return data["choices"][0]["message"]["content"]

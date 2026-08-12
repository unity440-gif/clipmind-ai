"""
Pydantic schemas for text-to-speech generation.
"""

from pydantic import BaseModel


class GenerateSpeechRequest(BaseModel):
    text: str
    voice: str | None = None


class GenerateSpeechResponse(BaseModel):
    filename: str
    url: str
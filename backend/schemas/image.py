"""
Pydantic schemas for image generation.
"""

from pydantic import BaseModel


class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"  # "1:1" | "16:9" | "9:16" | etc.


class GenerateImageResponse(BaseModel):
    filename: str
    url: str
"""
Pydantic schemas for the Clip resource, and for the hook-detection request body.
"""

import uuid

from pydantic import BaseModel

class CaptionEntry(BaseModel):
    index: int
    start: float
    end: float
    text: str


class UpdateCaptionsRequest(BaseModel):
    captions: list[CaptionEntry]

class HookDetectionRequest(BaseModel):
    min_duration: int = 60
    max_duration: int = 120
    aspect_ratio: str = "original"  # "original" | "16:9" | "9:16" | "1:1"
    num_clips: int = 5


class ClipResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    start_time_seconds: float
    end_time_seconds: float
    title: str | None
    hook: str | None
    summary: str | None
    reason: str | None
    virality_score: float | None
    confidence_score: float | None
    tiktok_caption: str | None
    instagram_caption: str | None
    youtube_caption: str | None
    hashtags: list[str] | None
    status: str

    class Config:
        from_attributes = True
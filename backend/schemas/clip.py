"""
Pydantic schemas for the Clip resource.
"""

import uuid

from pydantic import BaseModel


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
"""
Pydantic schemas for the Video resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    original_filename: str | None
    file_size_bytes: int | None
    created_at: datetime

    class Config:
        from_attributes = True

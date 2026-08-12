"""
Pydantic schemas for the Video resource, including chunked upload support.
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


class InitUploadRequest(BaseModel):
    filename: str
    total_size: int


class InitUploadResponse(BaseModel):
    upload_id: str


class CompleteUploadRequest(BaseModel):
    upload_id: str
    filename: str
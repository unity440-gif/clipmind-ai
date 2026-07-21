"""
Pydantic schemas for the Project resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreateRequest(BaseModel):
    title: str


class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

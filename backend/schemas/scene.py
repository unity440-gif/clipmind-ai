"""
Pydantic schemas for the script-to-scenes feature.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateScriptProjectRequest(BaseModel):
    title: str
    script_text: str


class SceneResponse(BaseModel):
    id: uuid.UUID
    scene_number: int
    description: str
    narration_text: str
    image_url: str | None
    audio_url: str | None
    status: str


class ScriptProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    compiled_video_url: str | None
    created_at: datetime
    scenes: list[SceneResponse] = []
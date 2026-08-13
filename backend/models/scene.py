"""
Scene model — one row per AI-generated scene within a ScriptProject,
each with its own image and narration audio.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_project_id = Column(UUID(as_uuid=True), ForeignKey("script_projects.id"), nullable=False, index=True)

    scene_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)   # what the image should show
    narration_text = Column(Text, nullable=False)  # what gets spoken aloud

    image_path = Column(String, nullable=True)   # R2 key
    audio_path = Column(String, nullable=True)    # R2 key

    status = Column(String, default="pending", nullable=False)  # pending -> generating -> completed -> failed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    script_project = relationship("ScriptProject", back_populates="scenes")
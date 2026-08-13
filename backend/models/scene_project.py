"""
ScriptProject model — represents one user-submitted script being broken
into AI-generated scenes (image + narration per scene), optionally
compiled into a single video.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class ScriptProject(Base):
    __tablename__ = "script_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    script_text = Column(Text, nullable=False)

    # pending -> breaking_down_script -> generating_scenes -> scenes_ready
    # -> compiling_video -> completed -> failed
    status = Column(String, default="pending", nullable=False)

    compiled_video_path = Column(String, nullable=True)  # R2 key, once compiled

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scenes = relationship("Scene", back_populates="script_project", cascade="all, delete-orphan")
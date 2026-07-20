"""
Project model — represents one row in the "projects" table.
A project is created when a user uploads a video or pastes a YouTube URL.
It's the container that holds the video and all clips generated from it.
"""

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links this project to the user who created it.
    # ForeignKey means: this value MUST match an existing id in the users table.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)

    # Tracks where this project is in the pipeline:
    # "pending" -> "downloading" -> "transcribing" -> "analyzing" -> "rendering" -> "completed" -> "failed"
    status = Column(String, default="pending", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")

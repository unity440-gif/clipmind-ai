"""
Video model — represents one row in the "videos" table.
This is the raw uploaded/downloaded source video that clips get cut from.
One project has exactly one source video.
"""
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)

    # Where the raw video lives in Cloudflare R2 (a URL/key, not the file itself)
    source_url = Column(String, nullable=True)          # set if uploaded from YouTube
    storage_path = Column(String, nullable=True)         # set once stored in R2

    original_filename = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)      # filled in after we inspect the video with FFmpeg
    file_size_bytes = Column(Integer, nullable=True)

    # Where the generated transcript text will be stored (as JSON with timestamps)
    transcript_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    project = relationship("Project", back_populates="videos")
    clips = relationship("Clip", back_populates="video", cascade="all, delete-orphan")

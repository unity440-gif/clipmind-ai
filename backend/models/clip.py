"""
Clip model — represents one row in the "clips" table.
Each row is a single AI-generated clip candidate from a video,
with all the metadata the AI hook-detection step produces.
"""
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Clip(Base):
    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True)

    # Timing within the source video
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)

    # AI-generated metadata (from the hook-detection prompt in your spec)
    title = Column(String, nullable=True)
    hook = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    virality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    tiktok_caption = Column(Text, nullable=True)
    instagram_caption = Column(Text, nullable=True)
    youtube_caption = Column(Text, nullable=True)
    hashtags = Column(ARRAY(String), nullable=True)

    # Where the actual rendered clip file lives once FFmpeg cuts it (Module: Clip Generation)
    storage_path = Column(String, nullable=True)
    aspect_ratio = Column(String, nullable=True)  # "16:9" | "9:16" | "1:1"

    status = Column(String, default="pending", nullable=False)  # pending -> rendering -> completed -> failed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    video = relationship("Video", back_populates="clips")

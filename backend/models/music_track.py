"""
MusicTrack model — represents one row in the "music_tracks" table.
Each row is one royalty-free background music file stored in R2,
tagged by mood so clips can be auto-matched to a fitting track.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class MusicTrack(Base):
    __tablename__ = "music_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)  # R2 key, e.g. "music/calm-1.mp3"
    mood = Column(String, nullable=False, index=True)  # "calm" | "dramatic" | "upbeat" | "neutral"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

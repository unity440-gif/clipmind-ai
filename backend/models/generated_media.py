"""
GeneratedMedia model — represents one row per AI-generated image or
speech clip a user has created, so they can browse their history later.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class GeneratedMedia(Base):
    __tablename__ = "generated_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    media_type = Column(String, nullable=False)  # "image" | "speech"
    prompt_or_text = Column(Text, nullable=False)  # the original prompt (image) or input text (speech)
    voice = Column(String, nullable=True)  # only set for speech generations
    storage_path = Column(String, nullable=False)  # R2 key

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
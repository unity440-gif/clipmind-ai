"""
User model — represents one row in the "users" table.
This is the account that owns projects, videos, clips, and a subscription.
"""
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class User(Base):
    __tablename__ = "users"

    # Primary key — a UUID instead of a plain incrementing number.
    # Reason: UUIDs can't be guessed/enumerated (e.g. someone trying /users/1, /users/2...),
    # which matters once this is a public product.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # nullable: Google-login users won't have one
    full_name = Column(String, nullable=True)

    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    verification_code = Column(String, nullable=True)
    verification_code_expires_at = Column(DateTime, nullable=True)

    # Credits system (Billing module) — how many clip-generation credits they have left
    credits_remaining = Column(Integer, default=10, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

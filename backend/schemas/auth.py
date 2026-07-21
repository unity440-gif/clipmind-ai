"""
Pydantic schemas for authentication requests/responses.
These define exactly what shape of JSON the API accepts and returns —
separate from our SQLAlchemy models, which define the database shape.
"""

import uuid

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    credits_remaining: int

    class Config:
        from_attributes = True  # allows converting a SQLAlchemy User object directly into this schema

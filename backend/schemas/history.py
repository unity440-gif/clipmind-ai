"""
Pydantic schema for generation history entries.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class HistoryEntryResponse(BaseModel):
    id: uuid.UUID
    media_type: str
    prompt_or_text: str
    voice: str | None
    url: str
    created_at: datetime
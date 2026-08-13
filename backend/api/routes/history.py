"""
Generation history routes.
Lets a logged-in user browse everything they've previously generated
(images and speech), newest first.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from models.generated_media import GeneratedMedia
from schemas.history import HistoryEntryResponse
from services.storage_service import get_public_url
from api.dependencies import get_current_user

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryEntryResponse])
def list_history(
    media_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current user's generation history, newest first.
    Optionally filter by media_type ("image" or "speech").
    """
    query = db.query(GeneratedMedia).filter(GeneratedMedia.user_id == current_user.id)
    if media_type:
        query = query.filter(GeneratedMedia.media_type == media_type)

    entries = query.order_by(GeneratedMedia.created_at.desc()).all()

    return [
        HistoryEntryResponse(
            id=entry.id,
            media_type=entry.media_type,
            prompt_or_text=entry.prompt_or_text,
            voice=entry.voice,
            url=get_public_url(entry.storage_path),
            created_at=entry.created_at,
        )
        for entry in entries
    ]
"""
Text-to-speech routes.
Lets a logged-in user generate speech audio from text using the provider's
default voice. Costs 1 credit per generation, only deducted on success.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from schemas.tts import GenerateSpeechRequest, GenerateSpeechResponse
from services.tts_service import generate_speech
from services.storage_service import upload_file, get_public_url
from api.dependencies import get_current_user

router = APIRouter(prefix="/tts", tags=["tts"])

TTS_COST = 1


@router.post("/generate", response_model=GenerateSpeechResponse, status_code=status.HTTP_201_CREATED)
def create_speech(
    payload: GenerateSpeechRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates speech audio from text using OpenRouter.
    Costs 1 credit, only deducted after a successful generation.
    """
    if current_user.credits_remaining < TTS_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Not enough credits. This costs {TTS_COST} credit(s), "
                   f"you have {current_user.credits_remaining}.",
        )

    try:
        result = generate_speech(payload.text, voice=payload.voice)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    r2_key = f"speech/{result['filename']}"
    upload_file(result["storage_path"], r2_key)
    os.remove(result["storage_path"])

    current_user.credits_remaining -= TTS_COST
    db.commit()

    return GenerateSpeechResponse(
        filename=result["filename"],
        url=get_public_url(r2_key),
    )
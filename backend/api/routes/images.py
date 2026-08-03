"""
Image generation routes.
Lets a logged-in user generate an AI image from a text prompt.
Costs 1 credit per generation, only deducted on success.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from schemas.image import GenerateImageRequest, GenerateImageResponse
from services.image_generation_service import generate_image
from api.dependencies import get_current_user

router = APIRouter(prefix="/images", tags=["images"])

IMAGE_GENERATION_COST = 1


@router.post("/generate", response_model=GenerateImageResponse, status_code=status.HTTP_201_CREATED)
def create_image(
    payload: GenerateImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates an image from a text prompt using OpenRouter.
    Costs 1 credit, only deducted after a successful generation.
    """
    if current_user.credits_remaining < IMAGE_GENERATION_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Not enough credits. This costs {IMAGE_GENERATION_COST} credit(s), "
                   f"you have {current_user.credits_remaining}.",
        )

    try:
        result = generate_image(payload.prompt, aspect_ratio=payload.aspect_ratio)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    current_user.credits_remaining -= IMAGE_GENERATION_COST
    db.commit()

    return GenerateImageResponse(
        filename=result["filename"],
        url=f"/uploads/{result['filename']}",
    )
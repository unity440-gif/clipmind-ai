"""
Quick video reformat route.
Lets a user upload a video and get back the whole thing reformatted to
a target aspect ratio, without going through the full project/AI pipeline.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from config.settings import settings
from database.session import get_db
from models.user import User
from services.video_processor import get_video_duration_seconds, cut_clip
from services.storage_service import upload_file, get_public_url
from api.dependencies import get_current_user

router = APIRouter(prefix="/reformat", tags=["reformat"])

LOCAL_SCRATCH_DIR = Path("uploads")


@router.post("/video")
async def reformat_video(
    aspect_ratio: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a video and returns it reformatted to the given aspect ratio
    ("16:9" | "9:16" | "1:1"), as a real R2-hosted file URL.
    """
    if aspect_ratio not in ("16:9", "9:16", "1:1"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="aspect_ratio must be one of: 16:9, 9:16, 1:1",
        )

    extension = Path(file.filename).suffix.lower()
    if extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}",
        )

    LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4()
    local_input_path = LOCAL_SCRATCH_DIR / f"reformat_in_{job_id}{extension}"
    local_output_path = LOCAL_SCRATCH_DIR / f"reformat_out_{job_id}.mp4"

    total_size = 0
    chunk_size = 1024 * 1024
    with open(local_input_path, "wb") as buffer:
        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                os.remove(local_input_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File exceeds the 5GB upload limit.",
                )
            buffer.write(chunk)

    try:
        duration = get_video_duration_seconds(str(local_input_path))

        cut_clip(
            source_video_path=str(local_input_path),
            output_path=str(local_output_path),
            start_seconds=0,
            end_seconds=duration,
            aspect_ratio=aspect_ratio,
        )

        r2_key = f"reformatted/{job_id}.mp4"
        upload_file(str(local_output_path), r2_key)

        return {"url": get_public_url(r2_key)}

    finally:
        for f in [local_input_path, local_output_path]:
            if f.exists():
                os.remove(f)
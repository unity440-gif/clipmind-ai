"""
Video upload routes.
Handles uploading a raw video file into an existing project.
Files are saved to a local uploads directory for now (swapped for
Cloudflare R2 in a later module, behind the same endpoint shape).
"""

import os
import uuid
from pathlib import Path
from workers.tasks import extract_audio_task

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from config.settings import settings
from database.session import get_db
from models.user import User
from models.project import Project
from models.video import Video
from schemas.video import VideoResponse
from api.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["videos"])


@router.post(
    "/{project_id}/videos",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_video(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a video file into a project the current user owns.
    Validates file extension and size before saving.
    """
    # 1. Make sure the project exists AND belongs to this user
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    # 2. Validate file extension
    original_extension = Path(file.filename).suffix.lower()
    if original_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}",
        )

    # 3. Build a safe, unique path to save the file (never trust the original filename directly)
    video_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{video_id}{original_extension}"

    # 4. Stream the file to disk in chunks, enforcing the size limit as we go
    #    (never load the whole file into memory at once — that would crash on large uploads)
    total_size = 0
    chunk_size = 1024 * 1024  # 1MB at a time

    with open(saved_path, "wb") as buffer:
        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                os.remove(saved_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File exceeds the 5GB upload limit.",
                )
            buffer.write(chunk)

    # 5. Save the video record in the database
    video = Video(
        id=video_id,
        project_id=project.id,
        original_filename=file.filename,
        storage_path=str(saved_path),
        file_size_bytes=total_size,
    )
    db.add(video)

    # Update the project's status now that a video is attached
    project.status = "uploaded"

    db.commit()
    db.refresh(video)

    # Kick off audio extraction in the background — this returns immediately,
    # the actual work happens in a separate Celery worker process.
    extract_audio_task.delay(str(video.id))

    return video
@router.post("/{project_id}/videos/{video_id}/set-test-transcript")
def set_test_transcript(
    project_id: uuid.UUID,
    video_id: uuid.UUID,
    transcript: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    TEMPORARY test-only endpoint: manually sets a transcript on a video.
    Whisper (a later module) will write here automatically instead.
    Safe to delete once real transcription is built.
    """
    video = (
        db.query(Video)
        .join(Project)
        .filter(Video.id == video_id, Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    # For this test-only endpoint, we store the transcript text directly
    # rather than a file path (the real Whisper module will use a file).
    video.transcript_path = transcript
    db.commit()

    return {"success": True}

@router.get("/{project_id}/videos", response_model=list[VideoResponse])
def list_project_videos(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all videos belonging to a project the current user owns."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    return db.query(Video).filter(Video.project_id == project.id).all()


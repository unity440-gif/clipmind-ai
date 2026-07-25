"""
Video routes.
Handles uploading a raw video file OR downloading one from a YouTube URL
into an existing project. Both paths feed the same downstream pipeline
(audio extraction, transcription, hook detection) since once a file exists
on disk, its origin doesn't matter to the rest of the app.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from config.settings import settings
from database.session import get_db
from models.user import User
from models.project import Project
from models.video import Video
from schemas.video import VideoResponse
from api.dependencies import get_current_user
from workers.tasks import extract_audio_task
from services.youtube_downloader import download_youtube_video

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

    original_extension = Path(file.filename).suffix.lower()
    if original_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}",
        )

    video_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{video_id}{original_extension}"

    total_size = 0
    chunk_size = 1024 * 1024

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

    video = Video(
        id=video_id,
        project_id=project.id,
        original_filename=file.filename,
        storage_path=str(saved_path),
        file_size_bytes=total_size,
    )
    db.add(video)
    project.status = "uploaded"
    db.commit()
    db.refresh(video)

    extract_audio_task.delay(str(video.id))

    return video


@router.post(
    "/{project_id}/videos/from-youtube",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_video_from_youtube(
    project_id: uuid.UUID,
    youtube_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Downloads a YouTube video into a project the current user owns,
    then feeds it into the exact same pipeline as a direct upload.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    video_id = uuid.uuid4()

    try:
        result = download_youtube_video(youtube_url, video_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download YouTube video: {e}",
        )

    video = Video(
        id=video_id,
        project_id=project.id,
        original_filename=result["original_filename"],
        storage_path=result["storage_path"],
        file_size_bytes=result["file_size_bytes"],
    )
    db.add(video)
    project.status = "uploaded"
    db.commit()
    db.refresh(video)

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
    Whisper writes here automatically in the real flow.
    Safe to delete once real transcription is fully relied upon.
    """
    video = (
        db.query(Video)
        .join(Project)
        .filter(Video.id == video_id, Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    transcript_file_path = str(Path(video.storage_path).with_suffix(".txt"))
    with open(transcript_file_path, "w") as f:
        f.write(transcript)

    video.transcript_path = transcript_file_path
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
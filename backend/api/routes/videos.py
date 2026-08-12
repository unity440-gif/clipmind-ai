"""
Video routes.
Handles uploading a raw video file OR downloading one from a YouTube URL
into an existing project. Large files use chunked upload to avoid
hitting Railway's ~5 minute hard HTTP timeout on a single request.
"""

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from config.settings import settings
from database.session import get_db
from models.user import User
from models.project import Project
from models.video import Video
from schemas.video import VideoResponse, InitUploadRequest, InitUploadResponse, CompleteUploadRequest
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
    Direct (non-chunked) upload — still used for smaller files.
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


@router.post("/{project_id}/videos/init-upload", response_model=InitUploadResponse)
def init_chunked_upload(
    project_id: uuid.UUID,
    payload: InitUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Starts a chunked upload session. Validates the file extension and size
    up front, creates a temporary folder to hold incoming chunks, and
    returns a unique upload_id the frontend will use for every chunk it sends.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    extension = Path(payload.filename).suffix.lower()
    if extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}",
        )

    if payload.total_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 5GB upload limit.",
        )

    upload_id = uuid.uuid4()
    chunk_dir = Path(settings.UPLOAD_DIR) / "chunks" / str(upload_id)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    return InitUploadResponse(upload_id=str(upload_id))


@router.post("/{project_id}/videos/upload-chunk")
async def upload_chunk(
    project_id: uuid.UUID,
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Receives a single chunk of a file and saves it to the upload session's
    temporary folder, named by its index so chunks can be reassembled in order.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    chunk_dir = Path(settings.UPLOAD_DIR) / "chunks" / upload_id
    if not chunk_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found.")

    chunk_path = chunk_dir / f"chunk_{chunk_index:06d}"
    with open(chunk_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"success": True, "chunk_index": chunk_index}


@router.post("/{project_id}/videos/complete-upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def complete_chunked_upload(
    project_id: uuid.UUID,
    payload: CompleteUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reassembles all uploaded chunks into the final video file, in order,
    then creates the Video row and kicks off the normal processing pipeline
    exactly like a direct upload would.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    chunk_dir = Path(settings.UPLOAD_DIR) / "chunks" / payload.upload_id
    if not chunk_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found.")

    chunk_files = sorted(chunk_dir.glob("chunk_*"))
    if not chunk_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chunks were uploaded.")

    video_id = uuid.uuid4()
    extension = Path(payload.filename).suffix.lower()
    final_path = Path(settings.UPLOAD_DIR) / f"{video_id}{extension}"

    total_size = 0
    with open(final_path, "wb") as final_file:
        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as cf:
                data = cf.read()
                total_size += len(data)
                final_file.write(data)

    shutil.rmtree(chunk_dir)

    video = Video(
        id=video_id,
        project_id=project.id,
        original_filename=payload.filename,
        storage_path=str(final_path),
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
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    return db.query(Video).filter(Video.project_id == project.id).all()
"""
Clip routes.
This is where AI hook-detection actually runs: given a video with a transcript,
ask OpenRouter to identify the best clips and save them as Clip rows.
Also triggers FFmpeg rendering of each clip in the background, and supports
editing/re-rendering captions. Files live in Cloudflare R2.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from models.project import Project
from models.video import Video
from models.clip import Clip
from schemas.clip import ClipResponse, HookDetectionRequest, UpdateCaptionsRequest
from services.hook_detection import detect_hooks
from services.subtitle_service import parse_srt_file, write_srt_file
from services.storage_service import upload_file, download_file, get_public_url
from api.dependencies import get_current_user
from workers.tasks import render_clip_task

router = APIRouter(prefix="/videos", tags=["clips"])

HOOK_DETECTION_COST = 1
LOCAL_SCRATCH_DIR = Path("uploads")


@router.post("/{video_id}/detect-hooks", response_model=list[ClipResponse])
def run_hook_detection(
    video_id: uuid.UUID,
    settings: HookDetectionRequest = HookDetectionRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Runs AI hook detection on a video's transcript and saves the results as Clips.
    Costs 1 credit, only deducted after a successful AI response.
    Then triggers background rendering of each clip into its own video file.
    """
    video = (
        db.query(Video)
        .join(Project)
        .filter(Video.id == video_id, Project.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    if not video.transcript_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This video has no transcript yet.",
        )

    if current_user.credits_remaining < HOOK_DETECTION_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Not enough credits. This action costs {HOOK_DETECTION_COST} credit(s), "
                   f"you have {current_user.credits_remaining}.",
        )

    LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    local_transcript_path = LOCAL_SCRATCH_DIR / f"{video_id}_transcript_read.txt"

    try:
        download_file(video.transcript_path, str(local_transcript_path))
        with open(local_transcript_path, "r") as f:
            transcript_text = f.read()
        os.remove(local_transcript_path)

        detected_clips = detect_hooks(
            transcript_text,
            num_clips=settings.num_clips,
            min_duration=settings.min_duration,
            max_duration=settings.max_duration,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    saved_clips = []
    for clip_data in detected_clips:
        clip = Clip(
            id=uuid.uuid4(),
            video_id=video.id,
            aspect_ratio=settings.aspect_ratio if settings.aspect_ratio != "original" else None,
            start_time_seconds=clip_data.get("start_time_seconds"),
            end_time_seconds=clip_data.get("end_time_seconds"),
            title=clip_data.get("title"),
            hook=clip_data.get("hook"),
            summary=clip_data.get("summary"),
            reason=clip_data.get("reason"),
            virality_score=clip_data.get("virality_score"),
            confidence_score=clip_data.get("confidence_score"),
            tiktok_caption=clip_data.get("tiktok_caption"),
            instagram_caption=clip_data.get("instagram_caption"),
            youtube_caption=clip_data.get("youtube_caption"),
            hashtags=clip_data.get("hashtags"),
            status="pending",
        )
        db.add(clip)
        saved_clips.append(clip)

    current_user.credits_remaining -= HOOK_DETECTION_COST
    db.commit()

    for clip in saved_clips:
        db.refresh(clip)
        render_clip_task.delay(str(clip.id))

    return saved_clips


@router.get("/{video_id}/clips", response_model=list[ClipResponse])
def list_clips(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .join(Project)
        .filter(Video.id == video_id, Project.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    return db.query(Clip).filter(Clip.video_id == video.id).order_by(Clip.virality_score.desc()).all()


def _get_owned_clip(clip_id: uuid.UUID, current_user: User, db: Session) -> Clip:
    clip = (
        db.query(Clip)
        .join(Video)
        .join(Project)
        .filter(Clip.id == clip_id, Project.user_id == current_user.id)
        .first()
    )
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found.")
    return clip


@router.get("/clip-url/{clip_id}")
def get_clip_video_url(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a temporary, secure direct URL to the rendered clip video in R2,
    so the browser can stream it without routing through the backend.
    """
    clip = _get_owned_clip(clip_id, current_user, db)
    if not clip.storage_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip video not rendered yet.")

    return {"url": get_public_url(clip.storage_path)}


@router.get("/clips/{clip_id}/captions")
def get_clip_captions(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a clip's captions as editable entries — from the custom edited
    version if one exists, otherwise from the original auto-generated .srt,
    both fetched from R2.
    """
    clip = _get_owned_clip(clip_id, current_user, db)

    r2_key = clip.custom_captions_path or f"clips/clip_{clip_id}.srt"

    LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    local_path = LOCAL_SCRATCH_DIR / f"{clip_id}_captions_read.srt"

    try:
        download_file(r2_key, str(local_path))
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No captions found for this clip yet.")

    captions = parse_srt_file(str(local_path))
    os.remove(local_path)

    return {"captions": captions}


@router.put("/clips/{clip_id}/captions")
def update_clip_captions(
    clip_id: uuid.UUID,
    payload: UpdateCaptionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Saves edited captions to R2 and triggers a re-render of the clip with
    the corrected text burned in.
    """
    clip = _get_owned_clip(clip_id, current_user, db)

    LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    local_path = LOCAL_SCRATCH_DIR / f"clip_{clip_id}_custom.srt"
    write_srt_file([entry.model_dump() for entry in payload.captions], str(local_path))

    r2_key = f"clips/clip_{clip_id}_custom.srt"
    upload_file(str(local_path), r2_key)
    os.remove(local_path)

    clip.custom_captions_path = r2_key
    clip.status = "rendering"
    db.commit()

    render_clip_task.delay(str(clip.id))

    return {"success": True, "message": "Captions updated, re-rendering clip."}
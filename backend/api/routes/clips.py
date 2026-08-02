"""
Clip routes.
This is where AI hook-detection actually runs: given a video with a transcript,
ask OpenRouter to identify the best clips and save them as Clip rows.
Also triggers FFmpeg rendering of each clip in the background, and supports
editing/re-rendering captions.
"""

import uuid

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
from api.dependencies import get_current_user
from workers.tasks import render_clip_task

router = APIRouter(prefix="/videos", tags=["clips"])

HOOK_DETECTION_COST = 1


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

    try:
        with open(video.transcript_path, "r") as f:
            transcript_text = f.read()
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
    """Returns all clips generated for a given video."""
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


@router.get("/clips/{clip_id}/captions")
def get_clip_captions(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a clip's captions as editable entries — from the custom edited
    version if one exists, otherwise from the original auto-generated .srt.
    """
    clip = _get_owned_clip(clip_id, current_user, db)

    path = clip.custom_captions_path or (
        str(clip_id) and None
    )
    # Fall back to the auto-generated file, which uses the same naming
    # convention as render_clip_task: uploads/clip_<id>.srt
    if not path:
        video = db.query(Video).filter(Video.id == clip.video_id).first()
        from pathlib import Path
        guessed_path = str(Path(video.storage_path).parent / f"clip_{clip.id}.srt")
        path = guessed_path

    if not path or not __import__("os").path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No captions found for this clip yet.")

    return {"captions": parse_srt_file(path)}


@router.put("/clips/{clip_id}/captions")
def update_clip_captions(
    clip_id: uuid.UUID,
    payload: UpdateCaptionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Saves edited captions and triggers a re-render of the clip with the
    corrected text burned in.
    """
    from pathlib import Path

    clip = _get_owned_clip(clip_id, current_user, db)
    video = db.query(Video).filter(Video.id == clip.video_id).first()

    custom_path = str(Path(video.storage_path).parent / f"clip_{clip.id}_custom.srt")
    write_srt_file(
        [entry.model_dump() for entry in payload.captions],
        custom_path,
    )

    clip.custom_captions_path = custom_path
    clip.status = "rendering"
    db.commit()

    render_clip_task.delay(str(clip.id))

    return {"success": True, "message": "Captions updated, re-rendering clip."}
"""
Clip routes.
This is where AI hook-detection actually runs: given a video with a transcript,
ask OpenRouter to identify the best clips and save them as Clip rows.
Also triggers FFmpeg rendering of each clip in the background.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from models.project import Project
from models.video import Video
from models.clip import Clip
from schemas.clip import ClipResponse
from services.hook_detection import detect_hooks
from api.dependencies import get_current_user
from workers.tasks import render_clip_task

router = APIRouter(prefix="/videos", tags=["clips"])


@router.post("/{video_id}/detect-hooks", response_model=list[ClipResponse])
def run_hook_detection(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Runs AI hook detection on a video's transcript and saves the results as Clips.
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

    try:
        with open(video.transcript_path, "r") as f:
            transcript_text = f.read()
        detected_clips = detect_hooks(transcript_text)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    saved_clips = []
    for clip_data in detected_clips:
        clip = Clip(
            id=uuid.uuid4(),
            video_id=video.id,
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
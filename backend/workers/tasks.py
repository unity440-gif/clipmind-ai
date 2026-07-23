"""
Celery background tasks.
Each function here runs asynchronously in a separate worker process,
completely independent from the FastAPI web server.
"""

from pathlib import Path

from workers.celery_app import celery_app
from database.session import SessionLocal
from models.video import Video
from models.project import Project
from services.video_processor import extract_audio, get_video_duration_seconds


@celery_app.task(name="extract_audio_task")
def extract_audio_task(video_id: str):
    """
    Background job: extracts audio from an uploaded video,
    updates its duration, and advances the project's status.

    Runs in a separate worker process — NOT inside the web server —
    so a slow/large video never blocks or times out an API request.
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return  # video was deleted or id was wrong; nothing to do

        project = db.query(Project).filter(Project.id == video.project_id).first()

        try:
            project.status = "extracting_audio"
            db.commit()

            # Read video duration (fills in metadata we didn't have at upload time)
            video.duration_seconds = get_video_duration_seconds(video.storage_path)

            # Extract audio to a .wav file next to the video
            audio_path = str(Path(video.storage_path).with_suffix(".wav"))
            extract_audio(video.storage_path, audio_path)

            video.transcript_path = None  # will be set once Whisper runs (Module 7)
            project.status = "audio_extracted"
            db.commit()

        except Exception as e:
            project.status = "failed"
            db.commit()
            raise e

    finally:
        db.close()

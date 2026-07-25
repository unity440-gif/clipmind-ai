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
from models.clip import Clip
from services.video_processor import extract_audio, get_video_duration_seconds, cut_clip
from services.whisper_service import transcribe_audio


@celery_app.task(name="extract_audio_task")
def extract_audio_task(video_id: str):
    """
    Background job: extracts audio from an uploaded video, transcribes it
    with Whisper, and advances the project's status at each stage.
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        project = db.query(Project).filter(Project.id == video.project_id).first()

        try:
            project.status = "extracting_audio"
            db.commit()

            video.duration_seconds = get_video_duration_seconds(video.storage_path)

            audio_path = str(Path(video.storage_path).with_suffix(".wav"))
            extract_audio(video.storage_path, audio_path)

            project.status = "transcribing"
            db.commit()

            transcript_text = transcribe_audio(audio_path)

            # Save the transcript as its own text file next to the video/audio,
            # and store the FILE PATH (not the raw text) — matching how a real
            # production system would handle potentially long transcripts.
            transcript_file_path = str(Path(video.storage_path).with_suffix(".txt"))
            with open(transcript_file_path, "w") as f:
                f.write(transcript_text)

            video.transcript_path = transcript_file_path
            project.status = "transcribed"
            db.commit()

        except Exception as e:
            project.status = "failed"
            db.commit()
            raise e

    finally:
        db.close()


@celery_app.task(name="render_clip_task")
def render_clip_task(clip_id: str):
    """
    Background job: cuts a single clip out of its source video using FFmpeg
    and saves the resulting file, updating the clip's status as it progresses.
    """
    db = SessionLocal()
    try:
        clip = db.query(Clip).filter(Clip.id == clip_id).first()
        if not clip:
            return

        video = db.query(Video).filter(Video.id == clip.video_id).first()

        try:
            clip.status = "rendering"
            db.commit()

            if clip.start_time_seconds >= video.duration_seconds:
                raise ValueError(
                    f"Clip start time ({clip.start_time_seconds}s) is beyond "
                    f"the video's actual duration ({video.duration_seconds}s)."
                )

            output_path = str(
                Path(video.storage_path).parent / f"clip_{clip.id}.mp4"
            )
            cut_clip(
                source_video_path=video.storage_path,
                output_path=output_path,
                start_seconds=clip.start_time_seconds,
                end_seconds=clip.end_time_seconds,
            )

            clip.storage_path = output_path
            clip.status = "completed"
            db.commit()

        except Exception as e:
            clip.status = "failed"
            db.commit()
            raise e

    finally:
        db.close()
"""
Celery background tasks.
Each function here runs asynchronously in a separate worker process,
completely independent from the FastAPI web server.
Files live in Cloudflare R2; tasks download what they need locally,
process it, then upload results back to R2.
"""

import json
import os
from pathlib import Path

from workers.celery_app import celery_app
from database.session import SessionLocal
from models.video import Video
from models.project import Project
from models.clip import Clip
from services.video_processor import extract_audio, get_video_duration_seconds, cut_clip
from services.whisper_service import transcribe_audio
from services.subtitle_service import generate_srt_for_clip
from services.storage_service import upload_file, download_file

LOCAL_SCRATCH_DIR = Path("uploads")


@celery_app.task(name="extract_audio_task")
def extract_audio_task(video_id: str):
    """
    Downloads the video from R2, extracts audio and transcribes it locally,
    then uploads the results (audio, transcript, segments) back to R2.
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        project = db.query(Project).filter(Project.id == video.project_id).first()

        LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        video_extension = Path(video.storage_path).suffix
        local_video_path = LOCAL_SCRATCH_DIR / f"{video_id}{video_extension}"

        try:
            project.status = "extracting_audio"
            db.commit()

            # Pull the video down from R2 to work on it locally
            download_file(video.storage_path, str(local_video_path))

            video.duration_seconds = get_video_duration_seconds(str(local_video_path))

            local_audio_path = local_video_path.with_suffix(".wav")
            extract_audio(str(local_video_path), str(local_audio_path))

            project.status = "transcribing"
            db.commit()

            transcription_result = transcribe_audio(str(local_audio_path))

            local_transcript_path = local_video_path.with_suffix(".txt")
            with open(local_transcript_path, "w") as f:
                f.write(transcription_result["text"])

            local_segments_path = LOCAL_SCRATCH_DIR / f"{video_id}.segments.json"
            with open(local_segments_path, "w") as f:
                json.dump(transcription_result["segments"], f)

            # Upload the results back to R2
            transcript_r2_key = f"transcripts/{video_id}.txt"
            segments_r2_key = f"transcripts/{video_id}.segments.json"
            upload_file(str(local_transcript_path), transcript_r2_key)
            upload_file(str(local_segments_path), segments_r2_key)

            video.transcript_path = transcript_r2_key
            video.segments_path = segments_r2_key
            project.status = "transcribed"
            db.commit()

        except Exception as e:
            project.status = "failed"
            db.commit()
            raise e

        finally:
            # Always clean up local scratch files, whether this succeeded or failed
            for f in [
                local_video_path,
                local_video_path.with_suffix(".wav"),
                local_video_path.with_suffix(".txt"),
                LOCAL_SCRATCH_DIR / f"{video_id}.segments.json",
            ]:
                if f.exists():
                    os.remove(f)

    finally:
        db.close()


@celery_app.task(name="render_clip_task")
def render_clip_task(clip_id: str):
    """
    Downloads the source video from R2, cuts the clip locally with FFmpeg
    (burning in captions if available), then uploads the rendered clip
    back to R2.
    """
    db = SessionLocal()
    try:
        clip = db.query(Clip).filter(Clip.id == clip_id).first()
        if not clip:
            return

        video = db.query(Video).filter(Video.id == clip.video_id).first()

        LOCAL_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        video_extension = Path(video.storage_path).suffix
        local_video_path = LOCAL_SCRATCH_DIR / f"src_{clip.video_id}{video_extension}"
        local_output_path = LOCAL_SCRATCH_DIR / f"clip_{clip.id}.mp4"
        local_subtitle_path = None

        try:
            clip.status = "rendering"
            db.commit()

            if clip.start_time_seconds >= video.duration_seconds:
                raise ValueError(
                    f"Clip start time ({clip.start_time_seconds}s) is beyond "
                    f"the video's actual duration ({video.duration_seconds}s)."
                )

            # Only re-download the source video if we don't already have it
            # locally from a previous clip render in this same batch
            if not local_video_path.exists():
                download_file(video.storage_path, str(local_video_path))

            if clip.custom_captions_path:
                local_subtitle_path = LOCAL_SCRATCH_DIR / f"clip_{clip.id}_custom.srt"
                download_file(clip.custom_captions_path, str(local_subtitle_path))
            elif video.segments_path:
                local_segments_path = LOCAL_SCRATCH_DIR / f"{video.id}.segments.json"
                if not local_segments_path.exists():
                    download_file(video.segments_path, str(local_segments_path))

                local_subtitle_path = LOCAL_SCRATCH_DIR / f"clip_{clip.id}.srt"
                generate_srt_for_clip(
                    segments_path=str(local_segments_path),
                    clip_start=clip.start_time_seconds,
                    clip_end=clip.end_time_seconds,
                    output_srt_path=str(local_subtitle_path),
                )

            cut_clip(
                source_video_path=str(local_video_path),
                output_path=str(local_output_path),
                start_seconds=clip.start_time_seconds,
                end_seconds=clip.end_time_seconds,
                aspect_ratio=clip.aspect_ratio or "original",
                subtitle_path=str(local_subtitle_path) if local_subtitle_path else None,
            )

            clip_r2_key = f"clips/clip_{clip.id}.mp4"
            upload_file(str(local_output_path), clip_r2_key)

            clip.storage_path = clip_r2_key
            clip.status = "completed"
            db.commit()

        except Exception as e:
            clip.status = "failed"
            db.commit()
            raise e

        finally:
            for f in [local_output_path, local_subtitle_path]:
                if f and Path(f).exists():
                    os.remove(f)
            # Note: we intentionally do NOT delete local_video_path here,
            # since multiple clips from the same video render in quick
            # succession and can reuse the same downloaded source file.

    finally:
        db.close()
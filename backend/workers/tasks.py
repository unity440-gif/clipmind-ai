"""
Celery background tasks.
Each function here runs asynchronously in a separate worker process,
completely independent from the FastAPI web server.
Files live in Cloudflare R2; tasks download what they need locally,
process it, then upload results back to R2.
"""

import json
import os
import uuid
from pathlib import Path

from workers.celery_app import celery_app
from database.session import SessionLocal
from models.video import Video
from models.project import Project
from models.clip import Clip
from models.scene_project import ScriptProject
from models.scene import Scene
from services.video_processor import extract_audio, get_video_duration_seconds, cut_clip
from services.whisper_service import transcribe_audio
from services.subtitle_service import generate_srt_for_clip
from services.storage_service import upload_file, download_file
from services.scene_breakdown_service import break_down_script
from services.image_generation_service import generate_image
from services.tts_service import generate_speech

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

    finally:
        db.close()


@celery_app.task(name="process_script_task")
def process_script_task(script_project_id: str):
    """
    Background job: breaks a script into scenes, then generates an image
    and narration audio for each scene.
    """
    db = SessionLocal()
    try:
        project = db.query(ScriptProject).filter(ScriptProject.id == script_project_id).first()
        if not project:
            return

        try:
            project.status = "breaking_down_script"
            db.commit()

            scene_data_list = break_down_script(project.script_text)

            scenes = []
            for scene_data in scene_data_list:
                scene = Scene(
                    id=uuid.uuid4(),
                    script_project_id=project.id,
                    scene_number=scene_data.get("scene_number"),
                    description=scene_data.get("description"),
                    narration_text=scene_data.get("narration"),
                    status="pending",
                )
                db.add(scene)
                scenes.append(scene)

            project.status = "generating_scenes"
            db.commit()
            for scene in scenes:
                db.refresh(scene)

            for scene in scenes:
                generate_scene_assets_task.delay(str(scene.id))

        except Exception as e:
            project.status = "failed"
            db.commit()
            raise e

    finally:
        db.close()


@celery_app.task(name="generate_scene_assets_task")
def generate_scene_assets_task(scene_id: str):
    """
    Background job: generates one scene's image and narration audio,
    uploads both to R2, and checks if the whole script project is
    now ready (all scenes completed).
    """
    db = SessionLocal()
    try:
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            return

        try:
            scene.status = "generating"
            db.commit()

            image_result = generate_image(scene.description, aspect_ratio="16:9")
            image_r2_key = f"scenes/{scene.id}_image.png"
            upload_file(image_result["storage_path"], image_r2_key)
            os.remove(image_result["storage_path"])

            speech_result = generate_speech(scene.narration_text)
            audio_r2_key = f"scenes/{scene.id}_audio.mp3"
            upload_file(speech_result["storage_path"], audio_r2_key)
            os.remove(speech_result["storage_path"])

            scene.image_path = image_r2_key
            scene.audio_path = audio_r2_key
            scene.status = "completed"
            db.commit()

        except Exception as e:
            scene.status = "failed"
            db.commit()
            raise e

        project = db.query(ScriptProject).filter(ScriptProject.id == scene.script_project_id).first()
        all_scenes = db.query(Scene).filter(Scene.script_project_id == project.id).all()
        if all(s.status in ("completed", "failed") for s in all_scenes):
            project.status = "scenes_ready"
            db.commit()

    finally:
        db.close()
"""
Script-to-scenes routes.
Lets a user submit a script, have it broken into AI-generated scenes
(image + narration each), and later compiled into a video.
Costs credits based on number of scenes generated (1 credit per scene).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from models.scene_project import ScriptProject
from models.scene import Scene
from schemas.scene import CreateScriptProjectRequest, ScriptProjectResponse, SceneResponse
from services.storage_service import get_public_url
from api.dependencies import get_current_user
from workers.tasks import process_script_task

router = APIRouter(prefix="/scripts", tags=["scenes"])


def _to_response(project: ScriptProject) -> ScriptProjectResponse:
    return ScriptProjectResponse(
        id=project.id,
        title=project.title,
        status=project.status,
        compiled_video_url=get_public_url(project.compiled_video_path) if project.compiled_video_path else None,
        created_at=project.created_at,
        scenes=[
            SceneResponse(
                id=s.id,
                scene_number=s.scene_number,
                description=s.description,
                narration_text=s.narration_text,
                image_url=get_public_url(s.image_path) if s.image_path else None,
                audio_url=get_public_url(s.audio_path) if s.audio_path else None,
                status=s.status,
            )
            for s in sorted(project.scenes, key=lambda s: s.scene_number)
        ],
    )


@router.post("", response_model=ScriptProjectResponse, status_code=status.HTTP_201_CREATED)
def create_script_project(
    payload: CreateScriptProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a script to be broken into AI-generated scenes.
    Processing happens entirely in the background.
    """
    project = ScriptProject(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=payload.title,
        script_text=payload.script_text,
        status="pending",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    process_script_task.delay(str(project.id))

    return _to_response(project)


@router.get("", response_model=list[ScriptProjectResponse])
def list_script_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(ScriptProject)
        .filter(ScriptProject.user_id == current_user.id)
        .order_by(ScriptProject.created_at.desc())
        .all()
    )
    return [_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ScriptProjectResponse)
def get_script_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(ScriptProject)
        .filter(ScriptProject.id == project_id, ScriptProject.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script project not found.")
    return _to_response(project)
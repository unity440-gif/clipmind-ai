"""
Project routes.
A Project is the container a user creates before uploading a video —
it's what ties together the video, transcript, and generated clips.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from models.project import Project
from schemas.project import ProjectCreateRequest, ProjectResponse
from api.dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new project owned by the logged-in user.
    """
    project = Project(
        user_id=current_user.id,
        title=payload.title,
        status="pending",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all projects belonging to the logged-in user.
    """
    return (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes a project, its videos, and its clips —
    including the actual files on disk, not just the database rows.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    for video in project.videos:
        for path in [video.storage_path, video.transcript_path]:
            if path and os.path.exists(path):
                os.remove(path)
        if video.storage_path:
            wav_path = str(Path(video.storage_path).with_suffix(".wav"))
            if os.path.exists(wav_path):
                os.remove(wav_path)
        for clip in video.clips:
            if clip.storage_path and os.path.exists(clip.storage_path):
                os.remove(clip.storage_path)

    db.delete(project)
    db.commit()
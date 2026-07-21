"""
Project routes.
A Project is the container a user creates before uploading a video —
it's what ties together the video, transcript, and generated clips.
"""

from fastapi import APIRouter, Depends, status
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
    This is the first step before uploading a video into it.
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
    Powers the dashboard's "recent clips/projects" and history page.
    """
    return (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

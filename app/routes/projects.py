# app/routes/projects.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.sample import Sample
from app.schemas import ProjectCreate, ProjectOut, SampleCreate, SampleOut

router = APIRouter(prefix="/projects", tags=["projects"])


def sample_to_dict(s: Sample) -> Dict[str, Any]:
    return {
        "id": s.id,
        "barcode": s.barcode,
        "sample_type": s.sample_type,
        "project_id": s.project_id,
        "metadata": s.metadata_dict,
        "created_at": s.created_at,
    }


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user),
):
    # resolve owner_email -> owner_id if provided
    owner_id: Optional[int] = None
    if getattr(payload, "owner_email", None):
        owner = db.query(User).filter(User.email == payload.owner_email).first()
        if not owner:
            raise HTTPException(status_code=400, detail="owner_email not found")
        owner_id = owner.id
    else:
        owner_id = current_user.id

    p = Project(name=payload.name, description=payload.description, owner_id=owner_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("", response_model=List[ProjectOut])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Security(get_current_user)):
    return db.query(Project).offset(skip).limit(limit).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Security(get_current_user)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return p


@router.get("/{project_id}/samples", response_model=List[SampleOut])
def get_project_samples(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    sample_type: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user),
):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    q = db.query(Sample).filter(Sample.project_id == project_id)
    if sample_type:
        q = q.filter(Sample.sample_type == sample_type)
    if barcode:
        q = q.filter(Sample.barcode.ilike(f"%{barcode}%"))

    qs = q.offset(skip).limit(limit).all()
    return [sample_to_dict(s) for s in qs]


@router.post("/{project_id}/samples", response_model=SampleOut, status_code=status.HTTP_201_CREATED)
def create_project_sample(
    project_id: int,
    payload: SampleCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(get_current_user),
):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    s = Sample(
        barcode=payload.barcode,
        sample_type=payload.sample_type,
        project_id=project_id,
        metadata_json=payload.metadata,
    )
    db.add(s)
    try:
        db.commit()
        db.refresh(s)
    except Exception:
        db.rollback()
        raise
    return sample_to_dict(s)

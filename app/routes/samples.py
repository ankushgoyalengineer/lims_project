# app/routes/samples.py
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.deps import get_db, get_current_user
from app.schemas import SampleCreate, SampleOut
from app.models.sample import Sample
from app.models.project import Project

router = APIRouter(prefix="/samples", tags=["samples"])


def sample_to_dict(s: Sample) -> Dict[str, Any]:
    return {
        "id": s.id,
        "barcode": s.barcode,
        "sample_type": s.sample_type,
        # <--- use the model helper property name
        "metadata": s.metadata_dict,
        "project_id": s.project_id,
        "created_at": s.created_at,
    }


@router.post("", response_model=SampleOut, status_code=status.HTTP_201_CREATED)
def create_sample(payload: SampleCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if payload.project_id is not None:
        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    s = Sample(
        barcode=payload.barcode,
        sample_type=payload.sample_type,
        project_id=payload.project_id,
        metadata_json=payload.metadata,
    )
    db.add(s)
    try:
        db.commit()
        db.refresh(s)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already exists")
    except Exception:
        db.rollback()
        raise
    return sample_to_dict(s)


@router.get("", response_model=List[SampleOut])
def list_samples(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    qs = db.query(Sample).offset(skip).limit(limit).all()
    return [sample_to_dict(s) for s in qs]


@router.get("/{sample_id}", response_model=SampleOut)
def get_sample(sample_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.get(Sample, sample_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return sample_to_dict(s)

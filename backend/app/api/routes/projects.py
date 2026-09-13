from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import JobModel
from app.models.schemas import JobResponse
from app.api.routes.jobs import build_job_response

router = APIRouter()

@router.get("/projects", response_model=List[JobResponse])
def list_projects(db: Session = Depends(get_db)):
    jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).all()
    return [build_job_response(j, db) for j in jobs]

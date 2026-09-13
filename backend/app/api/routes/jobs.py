import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.db_models import JobModel, ClipModel, CaptionModel
from app.models.schemas import CreateJobRequest, JobResponse, ClipResponse, CaptionSegmentSchema
from app.workers.job_processor import process_job

router = APIRouter()

def build_clip_response(clip: ClipModel, db: Session) -> ClipResponse:
    captions = db.query(CaptionModel).filter(CaptionModel.clip_id == clip.id).order_by(CaptionModel.start_time).all()
    cap_schemas = [
        CaptionSegmentSchema(
            id=c.id,
            start=c.start_time,
            end=c.end_time,
            text=c.text,
            words=json.loads(c.words_json) if c.words_json else []
        )
        for c in captions
    ]
    return ClipResponse(
        id=clip.id,
        job_id=clip.job_id,
        clip_index=clip.clip_index,
        start_time=clip.start_time,
        end_time=clip.end_time,
        duration=clip.duration,
        output_filename=clip.output_filename,
        thumbnail_filename=clip.thumbnail_filename,
        status=clip.status,
        error_message=clip.error_message,
        created_at=clip.created_at,
        captions=cap_schemas
    )

def build_job_response(job: JobModel, db: Session) -> JobResponse:
    clips = db.query(ClipModel).filter(ClipModel.job_id == job.id).order_by(ClipModel.clip_index).all()
    clip_schemas = [build_clip_response(c, db) for c in clips]
    return JobResponse(
        id=job.id,
        original_filename=job.original_filename,
        video_duration=job.video_duration,
        video_width=job.video_width,
        video_height=job.video_height,
        requested_duration=job.requested_duration,
        language=job.language,
        caption_style=job.caption_style,
        caption_position=job.caption_position,
        accuracy_mode=getattr(job, "accuracy_mode", "BALANCED") or "BALANCED",
        status=job.status,
        progress=job.progress,
        stage_message=job.stage_message,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        clips=clip_schemas
    )

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(req: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    file_path = settings.UPLOAD_DIR / req.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uploaded file '{req.filename}' not found on server."
        )

    job = JobModel(
        original_filename=req.filename,
        file_path=str(file_path),
        requested_duration=req.requested_duration,
        language=req.language,
        caption_style=req.caption_style,
        caption_position=req.caption_position,
        accuracy_mode=req.accuracy_mode or "BALANCED",
        status="UPLOADING",
        progress=5,
        stage_message="Job queued for processing..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_job, job.id)

    return {"job_id": job.id}

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return build_job_response(job, db)

@router.get("/jobs/{job_id}/results", response_model=JobResponse)
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return build_job_response(job, db)

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Delete video/thumbnail files on disk
    for clip in job.clips:
        if clip.output_path and Path(clip.output_path).exists():
            try:
                Path(clip.output_path).unlink()
            except Exception:
                pass
        if clip.thumbnail_path and Path(clip.thumbnail_path).exists():
            try:
                Path(clip.thumbnail_path).unlink()
            except Exception:
                pass

    if Path(job.file_path).exists():
        try:
            Path(job.file_path).unlink()
        except Exception:
            pass

    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully"}

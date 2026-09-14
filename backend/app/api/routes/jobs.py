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
    breakdown = None
    if getattr(clip, "score_breakdown_json", None):
        try:
            breakdown = json.loads(clip.score_breakdown_json)
        except Exception:
            pass

    return ClipResponse(
        id=clip.id,
        job_id=clip.job_id,
        clip_index=clip.clip_index,
        start_time=clip.start_time,
        end_time=clip.end_time,
        duration=clip.duration,
        score=getattr(clip, "score", 80),
        score_breakdown=breakdown,
        category=getattr(clip, "category", "Insight") or "Insight",
        hook=getattr(clip, "hook", None),
        reason=getattr(clip, "reason", None),
        transcript=getattr(clip, "transcript", None),
        is_selected=bool(getattr(clip, "is_selected", 1)),
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

import traceback

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(req: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print("\n==================================================")
    print(" PROCESSING JOB REQUEST RECEIVED ")
    print(f" Filename: {req.filename}")
    print(f" Target Duration: {req.requested_duration}s")
    print(f" Caption Language: {req.language}")
    print(f" Caption Style: {req.caption_style}")
    print(f" Caption Position: {req.caption_position}")
    print(f" Accuracy Mode: {req.accuracy_mode}")
    print("==================================================")

    file_path = settings.UPLOAD_DIR / req.filename
    if not file_path.exists():
        print(f"[-] ERROR: Uploaded file '{req.filename}' NOT FOUND at {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uploaded file '{req.filename}' not found on server at {file_path}."
        )

    print(f"[+] VIDEO FOUND: {file_path}")

    try:
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

        print(f"[+] JOB CREATED & DATABASE RECORD SAVED (ID: {job.id})")

        background_tasks.add_task(process_job, job.id)
        print(f"[+] PROCESSING QUEUED & WORKER STARTED for Job ID: {job.id}")

        return {"job_id": job.id}

    except Exception as e:
        print(f"[-] CRITICAL ERROR CREATING JOB:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error creating job: {str(e)}"
        )

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


from app.services.clip_analysis_service import clip_analysis_service
from app.services.clipping_service import assign_transcript_to_clip
from app.models.schemas import DiscoverClipsRequest, SelectClipsRequest

@router.post("/jobs/{job_id}/discover-clips")
def discover_clips_for_job(
    job_id: str,
    req: DiscoverClipsRequest,
    db: Session = Depends(get_db)
):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if not job.master_transcript_json:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job transcription not completed yet.")

    try:
        master_transcript = json.loads(job.master_transcript_json)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invalid transcript JSON: {e}")

    # Analyze transcript using ClipAnalysisProvider
    discovered = clip_analysis_service.analyze_transcript(
        master_transcript=master_transcript,
        target_duration=req.target_duration,
        max_clips=req.max_clips
    )

    if not discovered:
        # Fallback if no window matched target duration
        from app.services.clipping_service import FixedDurationClipStrategy
        fixed_strat = FixedDurationClipStrategy()
        discovered = fixed_strat.generate_clip_boundaries(job.video_duration, req.target_duration)

    # Delete existing pending clips for this job
    existing_clips = db.query(ClipModel).filter(ClipModel.job_id == job_id).all()
    for clip in existing_clips:
        db.delete(clip)
    db.commit()

    master_segments = master_transcript.get("segments", [])
    created_clips = []

    for idx, cand in enumerate(discovered, start=1):
        c_start = cand["start"]
        c_end = cand["end"]
        c_dur = cand["duration"]

        clip_record = ClipModel(
            job_id=job_id,
            clip_index=idx,
            start_time=c_start,
            end_time=c_end,
            duration=c_dur,
            score=cand.get("score", 80),
            score_breakdown_json=json.dumps(cand.get("score_breakdown", {})),
            category=cand.get("category", "Insight"),
            hook=cand.get("hook", ""),
            reason=cand.get("reason", ""),
            transcript=cand.get("transcript", ""),
            is_selected=1,
            status="PENDING"
        )
        db.add(clip_record)
        db.flush()

        clip_caps = assign_transcript_to_clip(master_segments, c_start, c_end)
        for cap in clip_caps:
            cap_record = CaptionModel(
                clip_id=clip_record.id,
                start_time=cap["start"],
                end_time=cap["end"],
                text=cap["text"],
                words_json=json.dumps(cap.get("words", []))
            )
            db.add(cap_record)

        created_clips.append(clip_record)

    db.commit()
    
    return {
        "job_id": job_id,
        "total_discovered": len(created_clips),
        "clips": [build_clip_response(c, db) for c in created_clips]
    }


@router.post("/jobs/{job_id}/select-clips")
def select_clips_for_job(
    job_id: str,
    req: SelectClipsRequest,
    db: Session = Depends(get_db)
):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    clips = db.query(ClipModel).filter(ClipModel.job_id == job_id).all()
    selected_set = set(req.selected_clip_ids)

    for clip in clips:
        clip.is_selected = 1 if clip.id in selected_set else 0

    db.commit()
    return {
        "job_id": job_id,
        "selected_count": len(selected_set),
        "clips": [build_clip_response(c, db) for c in clips]
    }


import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.db_models import ClipModel, CaptionModel, JobModel
from app.models.schemas import RenderClipRequest
from app.services.rendering_service import rendering_service
from app.services.ffmpeg_service import ffmpeg_service

router = APIRouter()

@router.post("/render/{clip_id}")
def re_render_clip(clip_id: str, req: RenderClipRequest = None, db: Session = Depends(get_db)):
    clip = db.query(ClipModel).filter(ClipModel.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    job = db.query(JobModel).filter(JobModel.id == clip.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent job not found")

    clip_style = (req.caption_style if req and req.caption_style else job.caption_style) or "KARAOKE"
    clip_position = (req.caption_position if req and req.caption_position else job.caption_position) or "BOTTOM"

    # Fetch latest updated captions from database
    db_caps = db.query(CaptionModel).filter(CaptionModel.clip_id == clip_id).order_by(CaptionModel.start_time).all()
    cap_dicts = [
        {
            "start": c.start_time,
            "end": c.end_time,
            "text": c.text,
            "words": json.loads(c.words_json) if c.words_json else []
        }
        for c in db_caps
    ]

    out_filename = f"short_{job.id}_{clip.clip_index}.mp4"
    thumb_filename = f"thumb_{job.id}_{clip.clip_index}.jpg"
    out_path = settings.OUTPUT_DIR / out_filename
    thumb_path = settings.OUTPUT_DIR / thumb_filename

    clip.status = "RENDERING"
    db.commit()

    render_ok = rendering_service.render_clip(
        source_video_path=job.file_path,
        start_time=clip.start_time,
        end_time=clip.end_time,
        output_mp4_path=str(out_path),
        captions=cap_dicts,
        caption_style=clip_style,
        caption_position=clip_position,
        in_width=job.video_width,
        in_height=job.video_height
    )

    mid_point = round((clip.start_time + clip.end_time) / 2.0, 2)
    ffmpeg_service.generate_thumbnail(job.file_path, mid_point, str(thumb_path))

    if render_ok:
        clip.output_path = str(out_path)
        clip.output_filename = out_filename
        clip.thumbnail_path = str(thumb_path)
        clip.thumbnail_filename = thumb_filename
        clip.status = "COMPLETED"
        clip.error_message = None
    else:
        clip.status = "FAILED"
        clip.error_message = "Re-rendering clip failed."

    db.commit()
    db.refresh(clip)

    return {
        "status": clip.status,
        "output_filename": clip.output_filename,
        "thumbnail_filename": clip.thumbnail_filename
    }

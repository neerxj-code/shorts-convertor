import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import ClipModel, CaptionModel
from app.models.schemas import CaptionSegmentSchema, UpdateCaptionsRequest

router = APIRouter()

@router.get("/captions/{clip_id}", response_model=List[CaptionSegmentSchema])
def get_clip_captions(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(ClipModel).filter(ClipModel.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    captions = db.query(CaptionModel).filter(CaptionModel.clip_id == clip_id).order_by(CaptionModel.start_time).all()
    return [
        CaptionSegmentSchema(
            id=c.id,
            start=c.start_time,
            end=c.end_time,
            text=c.text,
            words=json.loads(c.words_json) if c.words_json else []
        )
        for c in captions
    ]

@router.put("/captions/{clip_id}")
def update_clip_captions(clip_id: str, req: UpdateCaptionsRequest, db: Session = Depends(get_db)):
    clip = db.query(ClipModel).filter(ClipModel.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    # Delete old captions for this clip
    db.query(CaptionModel).filter(CaptionModel.clip_id == clip_id).delete()
    
    # Insert updated caption segments
    for cap_data in req.captions:
        cap_model = CaptionModel(
            clip_id=clip_id,
            start_time=cap_data.start,
            end_time=cap_data.end,
            text=cap_data.text,
            words_json=json.dumps([w.dict() for w in cap_data.words]) if cap_data.words else "[]"
        )
        db.add(cap_model)

    db.commit()
    return {"message": "Captions updated successfully"}

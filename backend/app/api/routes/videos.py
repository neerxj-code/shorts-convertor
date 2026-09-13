from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.core.config import settings

router = APIRouter()

@router.get("/videos/{filename}")
def get_video_file(filename: str):
    # Check outputs directory first, then uploads directory
    out_file = settings.OUTPUT_DIR / filename
    if out_file.exists():
        return FileResponse(path=str(out_file), media_type="video/mp4", filename=filename)

    up_file = settings.UPLOAD_DIR / filename
    if up_file.exists():
        return FileResponse(path=str(up_file), media_type="video/mp4", filename=filename)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

@router.get("/thumbnails/{filename}")
def get_thumbnail_file(filename: str):
    thumb_file = settings.OUTPUT_DIR / filename
    if thumb_file.exists():
        return FileResponse(path=str(thumb_file), media_type="image/jpeg", filename=filename)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

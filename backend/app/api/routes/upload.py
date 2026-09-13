import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.utils.file_utils import generate_safe_filename, is_allowed_video_file
from app.services.ffmpeg_service import ffmpeg_service
from app.models.schemas import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    if not file.filename or not is_allowed_video_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video file format. Supported formats: MP4, MOV, AVI, MKV, WEBM."
        )

    unique_id, safe_name = generate_safe_filename(file.filename)
    dest_path = settings.UPLOAD_DIR / safe_name

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size_mb = round(dest_path.stat().st_size / (1024 * 1024), 2)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            dest_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Probe metadata
        meta = ffmpeg_service.probe_video(str(dest_path))

        return UploadResponse(
            filename=safe_name,
            original_name=file.filename,
            size_mb=file_size_mb,
            duration_sec=round(meta["duration"], 2),
            width=meta["width"],
            height=meta["height"]
        )
    except HTTPException:
        raise
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process video upload: {str(e)}"
        )

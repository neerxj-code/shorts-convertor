import torch
from fastapi import APIRouter
from app.services.ffmpeg_service import ffmpeg_service
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "ffmpeg": ffmpeg_service.ffmpeg_path,
        "whisper_model": settings.WHISPER_MODEL,
        "cuda_available": cuda_available,
        "device": device_name
    }

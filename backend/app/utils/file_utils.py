import os
import uuid
import shutil
import time
from pathlib import Path
from typing import Tuple
from app.core.config import settings

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

def generate_safe_filename(original_filename: str) -> Tuple[str, str]:
    """Generates UUID filename preserving extension"""
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".mp4"
    unique_id = str(uuid.uuid4())
    safe_name = f"{unique_id}{ext}"
    return unique_id, safe_name

def is_allowed_video_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

def cleanup_temp_files(job_id: str = None):
    """Clean temporary audio/ASS/intermediate files"""
    try:
        if not settings.TEMP_DIR.exists():
            return
        
        current_time = time.time()
        max_age = settings.FILE_RETENTION_HOURS * 3600
        
        for item in settings.TEMP_DIR.iterdir():
            if item.is_file():
                if job_id and job_id in item.name:
                    try:
                        item.unlink()
                    except Exception:
                        pass
                elif current_time - item.stat().st_mtime > max_age:
                    try:
                        item.unlink()
                    except Exception:
                        pass
    except Exception as e:
        print(f"Error cleaning temp files: {e}")

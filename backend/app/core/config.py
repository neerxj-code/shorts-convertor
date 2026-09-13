import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = "Shortify API"
    
    # Upload & Storage
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/shortify.db")
    
    # Whisper & AI
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    ACCURACY_MODE: str = os.getenv("ACCURACY_MODE", "BALANCED")
    
    # FFmpeg paths
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "")
    
    # File Retention
    FILE_RETENTION_HOURS: int = int(os.getenv("FILE_RETENTION_HOURS", "24"))

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

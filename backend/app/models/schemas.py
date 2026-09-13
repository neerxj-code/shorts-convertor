from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class WordSchema(BaseModel):
    word: str
    text: Optional[str] = None
    start: float
    end: float

    def get_word(self) -> str:
        return self.word or self.text or ""

class CaptionSegmentSchema(BaseModel):
    id: Optional[str] = None
    start: float
    end: float
    text: str
    words: List[WordSchema] = []

class UpdateCaptionsRequest(BaseModel):
    captions: List[CaptionSegmentSchema]

class RenderClipRequest(BaseModel):
    caption_style: Optional[str] = None
    caption_position: Optional[str] = None
    font_color: Optional[str] = None
    highlight_color: Optional[str] = None

class CreateJobRequest(BaseModel):
    filename: str
    requested_duration: int = Field(default=30, ge=10, le=180)
    language: str = Field(default="AUTO")
    caption_style: str = Field(default="KARAOKE")
    caption_position: str = Field(default="BOTTOM")
    accuracy_mode: Optional[str] = Field(default="BALANCED")

class ClipResponse(BaseModel):
    id: str
    job_id: str
    clip_index: int
    start_time: float
    end_time: float
    duration: float
    output_filename: Optional[str] = None
    thumbnail_filename: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    captions: List[CaptionSegmentSchema] = []

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: str
    original_filename: str
    video_duration: float
    video_width: int
    video_height: int
    requested_duration: int
    language: str
    caption_style: str
    caption_position: str
    accuracy_mode: Optional[str] = "BALANCED"
    status: str
    progress: int
    stage_message: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    clips: List[ClipResponse] = []

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    filename: str
    original_name: str
    size_mb: float
    duration_sec: float
    width: int
    height: int

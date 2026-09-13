import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    video_duration = Column(Float, default=0.0)
    video_width = Column(Integer, default=0)
    video_height = Column(Integer, default=0)
    
    requested_duration = Column(Integer, default=30)
    language = Column(String, default="AUTO")
    caption_style = Column(String, default="KARAOKE")
    caption_position = Column(String, default="BOTTOM")
    accuracy_mode = Column(String, default="BALANCED")
    
    status = Column(String, default="UPLOADING")
    progress = Column(Integer, default=0)
    stage_message = Column(String, default="Job created")
    error_message = Column(Text, nullable=True)
    master_transcript_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clips = relationship("ClipModel", back_populates="job", cascade="all, delete-orphan", order_by="ClipModel.clip_index")


class ClipModel(Base):
    __tablename__ = "clips"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    clip_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    output_path = Column(String, nullable=True)
    output_filename = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    thumbnail_filename = Column(String, nullable=True)
    
    status = Column(String, default="PENDING")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("JobModel", back_populates="clips")
    captions = relationship("CaptionModel", back_populates="clip", cascade="all, delete-orphan", order_by="CaptionModel.start_time")


class CaptionModel(Base):
    __tablename__ = "captions"

    id = Column(String, primary_key=True, default=generate_uuid)
    clip_id = Column(String, ForeignKey("clips.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    words_json = Column(Text, nullable=False)  # JSON representation of word timestamps

    clip = relationship("ClipModel", back_populates="captions")

import os
import json
import traceback
from datetime import datetime
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db_models import JobModel, ClipModel, CaptionModel
from app.services.ffmpeg_service import ffmpeg_service
from app.services.transcription_service import transcription_service
from app.services.clipping_service import clipping_service, assign_transcript_to_clip
from app.services.rendering_service import rendering_service
from app.utils.file_utils import cleanup_temp_files

def process_job(job_id: str):
    """
    Background worker task to process long video into vertical shorts with animated captions.
    Runs asynchronously and updates database status & progress.
    """
    db = SessionLocal()
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        db.close()
        return

    wav_path = str(settings.TEMP_DIR / f"{job_id}_master.wav")

    try:
        # Stage 1: ANALYZING (10-20%)
        job.status = "ANALYZING"
        job.progress = 15
        job.stage_message = "Analyzing video metadata and aspect ratio..."
        db.commit()

        video_meta = ffmpeg_service.probe_video(job.file_path)
        job.video_duration = video_meta["duration"]
        job.video_width = video_meta["width"]
        job.video_height = video_meta["height"]
        db.commit()

        if job.video_duration <= 0:
            raise ValueError("Could not determine valid video duration or video file is corrupted.")

        # Stage 2: EXTRACTING AUDIO (20-35%)
        job.status = "EXTRACTING_AUDIO"
        job.progress = 25
        job.stage_message = "Extracting 16kHz mono audio stream for speech recognition..."
        db.commit()

        audio_success = ffmpeg_service.extract_audio(job.file_path, wav_path)
        if not audio_success or not os.path.exists(wav_path):
            raise RuntimeError("Failed to extract audio track from video file.")

        # Stage 3: TRANSCRIBING (35-60%)
        job.status = "TRANSCRIBING"
        job.progress = 40
        job.stage_message = "Running Whisper speech-to-text (English/Hindi/Hinglish)..."
        db.commit()

        transcript_result = transcription_service.transcribe(
            audio_path=wav_path,
            language_hint=job.language,
            accuracy_mode=job.accuracy_mode
        )
        job.master_transcript_json = json.dumps(transcript_result)
        job.progress = 60
        db.commit()

        # Stage 4: GENERATING CAPTIONS & CLIPS (60-75%)
        job.status = "GENERATING_CAPTIONS"
        job.progress = 65
        job.stage_message = "Calculating clip boundaries and word timestamps..."
        db.commit()

        boundaries = clipping_service.generate_clip_boundaries(
            total_duration=job.video_duration,
            requested_duration=job.requested_duration
        )

        master_segments = transcript_result.get("segments", [])
        created_clips = []

        for idx, (c_start, c_end) in enumerate(boundaries, start=1):
            clip_dur = round(c_end - c_start, 2)
            clip_record = ClipModel(
                job_id=job_id,
                clip_index=idx,
                start_time=c_start,
                end_time=c_end,
                duration=clip_dur,
                status="PENDING"
            )
            db.add(clip_record)
            db.flush()

            # Assign transcript segments for this clip
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
        job.progress = 75
        db.commit()

        # Stage 5: RENDERING EACH CLIP (75-95%)
        job.status = "RENDERING"
        total_clips = len(created_clips)

        for i, clip in enumerate(created_clips, start=1):
            current_progress = 75 + int((i / max(1, total_clips)) * 20)
            job.progress = current_progress
            job.stage_message = f"Rendering clip {i} of {total_clips} (9:16 vertical + animated captions)..."
            db.commit()

            clip.status = "RENDERING"
            db.commit()

            out_filename = f"short_{job_id}_{clip.clip_index}.mp4"
            thumb_filename = f"thumb_{job_id}_{clip.clip_index}.jpg"
            out_path = settings.OUTPUT_DIR / out_filename
            thumb_path = settings.OUTPUT_DIR / thumb_filename

            # Get clip captions from DB
            db_caps = db.query(CaptionModel).filter(CaptionModel.clip_id == clip.id).all()
            cap_dicts = [
                {
                    "start": cap.start_time,
                    "end": cap.end_time,
                    "text": cap.text,
                    "words": json.loads(cap.words_json) if cap.words_json else []
                }
                for cap in db_caps
            ]

            render_ok = rendering_service.render_clip(
                source_video_path=job.file_path,
                start_time=clip.start_time,
                end_time=clip.end_time,
                output_mp4_path=str(out_path),
                captions=cap_dicts,
                caption_style=job.caption_style,
                caption_position=job.caption_position,
                in_width=job.video_width,
                in_height=job.video_height
            )

            # Generate thumbnail
            mid_point = round((clip.start_time + clip.end_time) / 2.0, 2)
            ffmpeg_service.generate_thumbnail(job.file_path, mid_point, str(thumb_path))

            if render_ok:
                clip.output_path = str(out_path)
                clip.output_filename = out_filename
                clip.thumbnail_path = str(thumb_path)
                clip.thumbnail_filename = thumb_filename
                clip.status = "COMPLETED"
            else:
                clip.status = "FAILED"
                clip.error_message = "FFmpeg clip rendering failed."

            db.commit()

        # Stage 6: COMPLETED (100%)
        job.status = "COMPLETED"
        job.progress = 100
        job.stage_message = "Shortify video conversion completed successfully!"
        job.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        err_msg = str(e)
        print(f"[JobProcessor] Error processing job {job_id}: {err_msg}")
        traceback.print_exc()
        job.status = "FAILED"
        job.error_message = err_msg
        job.stage_message = f"Processing failed: {err_msg[:100]}"
        db.commit()

    finally:
        # Cleanup temporary audio WAV file
        if os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except Exception:
                pass
        cleanup_temp_files(job_id)
        db.close()

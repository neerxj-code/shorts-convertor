import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from app.services.ffmpeg_service import ffmpeg_service
from app.services.cropping_service import cropping_service
from app.services.caption_service import caption_service

class RenderingService:
    def __init__(self):
        pass

    def render_clip(
        self,
        source_video_path: str,
        start_time: float,
        end_time: float,
        output_mp4_path: str,
        captions: list,
        caption_style: str = "KARAOKE",
        caption_position: str = "BOTTOM",
        in_width: int = 1920,
        in_height: int = 1080
    ) -> bool:
        """
        Renders a single vertical 9:16 short clip with burned-in animated captions using FFmpeg.
        """
        source_video_path = str(source_video_path)
        output_mp4_path = str(output_mp4_path)
        os.makedirs(os.path.dirname(output_mp4_path), exist_ok=True)
        
        duration = max(1.0, end_time - start_time)
        
        # 1. Generate ASS subtitle file if captions exist
        ass_path = output_mp4_path + ".ass"
        has_subtitles = False
        
        if captions:
            has_subtitles = caption_service.generate_ass_subtitle_file(
                captions=captions,
                output_ass_path=ass_path,
                style_preset=caption_style,
                position=caption_position,
                video_width=1080,
                video_height=1920
            )

        # 2. Build 9:16 crop filter
        crop_filter = cropping_service.calculate_crop_filter(in_width, in_height, target_w=1080, target_h=1920)

        # 3. Combine filter chain
        if has_subtitles and os.path.exists(ass_path):
            # Escape windows paths for FFmpeg subtitle filter: replace \ with / and escape : as \:
            clean_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
            vf_chain = f"{crop_filter},subtitles='{clean_ass_path}'"
        else:
            vf_chain = crop_filter

        # Check if source video has audio track
        meta = ffmpeg_service.probe_video(source_video_path)
        has_audio = meta.get("has_audio", True)

        audio_flags = ["-c:a", "aac", "-b:a", "128k"] if has_audio else ["-an"]

        # 4. Construct FFmpeg command
        cmd = [
            ffmpeg_service.ffmpeg_path, "-y",
            "-ss", str(start_time),
            "-i", source_video_path,
            "-t", str(duration),
            "-vf", vf_chain,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            *audio_flags,
            "-movflags", "+faststart",
            output_mp4_path
        ]

        print(f"[RenderingService] Executing FFmpeg clip render: {' '.join(cmd[:10])}...")
        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode != 0:
            print(f"[RenderingService] FFmpeg render error (stderr): {res.stderr[-500:]}")
            # Fallback render without subtitles if subtitle filter failed
            if has_subtitles:
                print("[RenderingService] Retrying render without subtitle overlay filter...")
                cmd_fallback = [
                    ffmpeg_service.ffmpeg_path, "-y",
                    "-ss", str(start_time),
                    "-i", source_video_path,
                    "-t", str(duration),
                    "-vf", crop_filter,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    output_mp4_path
                ]
                res = subprocess.run(cmd_fallback, capture_output=True, text=True)

        # Clean up temporary ASS file after render
        if os.path.exists(ass_path):
            try:
                os.unlink(ass_path)
            except Exception:
                pass

        return res.returncode == 0 and os.path.exists(output_mp4_path) and os.path.getsize(output_mp4_path) > 0

rendering_service = RenderingService()

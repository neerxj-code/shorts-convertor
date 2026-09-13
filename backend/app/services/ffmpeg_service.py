import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings

class FFmpegService:
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        self._ensure_ffmpeg_in_path()
        print(f"[FFmpegService] Using FFmpeg: {self.ffmpeg_path}")
        print(f"[FFmpegService] Using FFprobe: {self.ffprobe_path}")

    def _find_ffmpeg(self) -> str:
        # 1. Configured path
        if settings.FFMPEG_PATH and os.path.exists(settings.FFMPEG_PATH):
            return settings.FFMPEG_PATH
        
        # 2. Try imageio_ffmpeg
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

        # 3. System PATH fallback
        return "ffmpeg"

    def _find_ffprobe(self) -> str:
        # 1. Configured path
        if settings.FFPROBE_PATH and os.path.exists(settings.FFPROBE_PATH):
            return settings.FFPROBE_PATH
        
        # 2. Check if ffprobe exists alongside ffmpeg
        ffmpeg_exe = self.ffmpeg_path
        if ffmpeg_exe and os.path.isabs(ffmpeg_exe):
            parent = Path(ffmpeg_exe).parent
            name = Path(ffmpeg_exe).name.replace("ffmpeg", "ffprobe")
            probe_candidate = parent / name
            if probe_candidate.exists():
                return str(probe_candidate)
            # Try ffprobe.exe
            ffprobe_alias = parent / "ffprobe.exe"
            if ffprobe_alias.exists():
                return str(ffprobe_alias)

        # 3. System PATH fallback
        return shutil.which("ffprobe") or "ffprobe"

    def _ensure_ffmpeg_in_path(self):
        """Ensures directory containing ffmpeg.exe is in os.environ['PATH'] so Whisper subprocess calls work."""
        if self.ffmpeg_path and os.path.isabs(self.ffmpeg_path):
            ffmpeg_bin_dir = Path(self.ffmpeg_path).parent
            
            # Ensure executables named 'ffmpeg.exe' and 'ffprobe.exe' exist in the directory
            ffmpeg_alias = ffmpeg_bin_dir / "ffmpeg.exe"
            if not ffmpeg_alias.exists() and Path(self.ffmpeg_path).exists():
                try:
                    shutil.copy2(self.ffmpeg_path, ffmpeg_alias)
                except Exception as e:
                    print(f"[FFmpegService] Could not alias ffmpeg.exe: {e}")

            ffprobe_alias = ffmpeg_bin_dir / "ffprobe.exe"
            if not ffprobe_alias.exists() and Path(self.ffmpeg_path).exists():
                try:
                    shutil.copy2(self.ffmpeg_path, ffprobe_alias)
                except Exception:
                    pass
            
            dir_str = str(ffmpeg_bin_dir)
            path_env = os.environ.get("PATH", "")
            if dir_str not in path_env:
                os.environ["PATH"] = dir_str + os.pathsep + path_env

    def probe_video(self, video_path: str) -> Dict[str, Any]:
        """Probes video file and returns metadata dictionary"""
        video_path = str(video_path)
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            
            width = 0
            height = 0
            fps = 30.0
            has_audio = False

            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type")
                if codec_type == "video" and width == 0:
                    width = int(stream.get("width", 0))
                    height = int(stream.get("height", 0))
                    r_fps = stream.get("r_frame_rate", "30/1")
                    try:
                        num, den = map(float, r_fps.split("/"))
                        fps = num / den if den > 0 else 30.0
                    except Exception:
                        fps = 30.0
                elif codec_type == "audio":
                    has_audio = True

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "has_audio": has_audio,
                "size_bytes": int(format_info.get("size", 0))
            }
        except Exception:
            # Fallback estimation using ffmpeg if ffprobe is absent or fails
            return self._probe_fallback(video_path)

    def _probe_fallback(self, video_path: str) -> Dict[str, Any]:
        """Fallback video duration/resolution probe using ffmpeg -i"""
        cmd = [self.ffmpeg_path, "-i", video_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        stderr = res.stderr
        
        duration = 10.0
        width, height = 1280, 720
        
        for line in stderr.splitlines():
            if "Duration:" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    duration = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
            if "Video:" in line:
                try:
                    # Look for resolution e.g. 1920x1080
                    for token in line.split(","):
                        if "x" in token and any(c.isdigit() for c in token):
                            dims = token.strip().split(" ")[0].split("x")
                            if len(dims) == 2 and dims[0].isdigit() and dims[1].isdigit():
                                width = int(dims[0])
                                height = int(dims[1])
                except Exception:
                    pass

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": 30.0,
            "has_audio": True,
            "size_bytes": os.path.getsize(video_path) if os.path.exists(video_path) else 0
        }

    def extract_audio(self, video_path: str, output_wav_path: str) -> bool:
        """Extracts video audio stream to normalized 16kHz mono WAV format for Whisper ASR"""
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vn",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(output_wav_path):
            # Fallback without loudnorm filter if loudnorm fails
            cmd_fallback = [
                self.ffmpeg_path, "-y",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(output_wav_path)
            ]
            res = subprocess.run(cmd_fallback, capture_output=True, text=True)

        return res.returncode == 0 and os.path.exists(output_wav_path)

    def generate_thumbnail(self, video_path: str, time_sec: float, output_jpg_path: str) -> bool:
        """Generates thumbnail frame at given timestamp"""
        cmd = [
            self.ffmpeg_path, "-y",
            "-ss", str(time_sec),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_jpg_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0 and os.path.exists(output_jpg_path)

ffmpeg_service = FFmpegService()

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional

class CropStrategy:
    def calculate_crop_filter(
        self,
        in_width: int,
        in_height: int,
        target_w: int = 1080,
        target_h: int = 1920,
        video_path: Optional[str] = None,
        start_time: float = 0.0,
        end_time: float = 0.0
    ) -> str:
        raise NotImplementedError

class CenterCropStrategy(CropStrategy):
    def calculate_crop_filter(
        self,
        in_width: int,
        in_height: int,
        target_w: int = 1080,
        target_h: int = 1920,
        video_path: Optional[str] = None,
        start_time: float = 0.0,
        end_time: float = 0.0
    ) -> str:
        """
        Calculates FFmpeg video filter for 9:16 vertical center crop without aspect distortion.
        Outputs video scaled to target dimensions (1080x1920).
        """
        if in_width <= 0 or in_height <= 0:
            return f"scale={target_w}:{target_h}"
            
        target_aspect = target_w / target_h  # 9/16 = 0.5625
        in_aspect = in_width / in_height
        
        if in_aspect > target_aspect:
            # Video is wider than 9:16 (e.g. 16:9 landscape 1920x1080)
            crop_w = f"ih*{target_w}/{target_h}"
            crop_h = "ih"
            x_offset = f"(iw-{crop_w})/2"
            y_offset = "0"
        else:
            # Video is taller than 9:16
            crop_w = "iw"
            crop_h = f"iw*{target_h}/{target_w}"
            x_offset = "0"
            y_offset = f"(ih-{crop_h})/2"

        return f"crop={crop_w}:{crop_h}:{x_offset}:{y_offset},scale={target_w}:{target_h}:flags=bicubic"


class FaceTrackingCropStrategy(CropStrategy):
    """
    Phase 7: Smart 9:16 Reframing with face tracking & active speaker positioning.
    Detects face coordinates across video frames and centers 9:16 viewport dynamically.
    """

    def __init__(self):
        self.center_fallback = CenterCropStrategy()
        # OpenCV Haar Cascade face detector
        self.cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path) if os.path.exists(self.cascade_path) else None

    def calculate_crop_filter(
        self,
        in_width: int,
        in_height: int,
        target_w: int = 1080,
        target_h: int = 1920,
        video_path: Optional[str] = None,
        start_time: float = 0.0,
        end_time: float = 0.0
    ) -> str:
        if not video_path or not os.path.exists(video_path) or not self.face_cascade or in_width <= 0 or in_height <= 0:
            return self.center_fallback.calculate_crop_filter(in_width, in_height, target_w, target_h)

        target_aspect = target_w / target_h
        in_aspect = in_width / in_height

        if in_aspect <= target_aspect:
            return self.center_fallback.calculate_crop_filter(in_width, in_height, target_w, target_h)

        crop_w_px = int(round(in_height * target_aspect))
        crop_h_px = in_height

        # Sample up to 5 frames across the clip duration to locate active speaker
        detected_x_centers = []
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            clip_dur = max(1.0, end_time - start_time)
            sample_timestamps = [start_time + (i * clip_dur / 5.0) for i in range(1, 5)]

            for ts in sample_timestamps:
                frame_idx = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
                for (x, y, w, h) in faces:
                    face_center_x = x + (w / 2.0)
                    detected_x_centers.append(face_center_x)

            cap.release()
        except Exception as e:
            print(f"[FaceTrackingCropStrategy] Face detection probe error ({e}), using center crop.")

        if not detected_x_centers:
            print("[FaceTrackingCropStrategy] No faces detected in sample frames. Falling back to center crop.")
            return self.center_fallback.calculate_crop_filter(in_width, in_height, target_w, target_h)

        # Compute median face center X coordinate
        target_face_x = float(np.median(detected_x_centers))
        
        # Calculate optimal crop X offset centered around speaker
        optimal_x = target_face_x - (crop_w_px / 2.0)
        max_x = max(0, in_width - crop_w_px)
        clamped_x = int(round(max(0, min(optimal_x, max_x))))

        print(f"[FaceTrackingCropStrategy] Reframed 9:16 crop box around active speaker face at X={clamped_x}px (in_width={in_width}px, crop_w={crop_w_px}px)")
        return f"crop={crop_w_px}:{crop_h_px}:{clamped_x}:0,scale={target_w}:{target_h}:flags=bicubic"


cropping_service = FaceTrackingCropStrategy()


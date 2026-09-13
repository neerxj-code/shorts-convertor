from typing import Dict, Any

class CropStrategy:
    def calculate_crop_filter(self, in_width: int, in_height: int, target_w: int = 1080, target_h: int = 1920) -> str:
        raise NotImplementedError

class CenterCropStrategy(CropStrategy):
    def calculate_crop_filter(self, in_width: int, in_height: int, target_w: int = 1080, target_h: int = 1920) -> str:
        """
        Calculates FFmpeg video filter for 9:16 vertical center crop without aspect distortion.
        Outputs video scaled to 1080x1920 (or target dimensions).
        """
        if in_width <= 0 or in_height <= 0:
            return f"scale={target_w}:{target_h}"
            
        target_aspect = target_w / target_h  # 9/16 = 0.5625
        in_aspect = in_width / in_height
        
        if in_aspect > target_aspect:
            # Video is wider than 9:16 (e.g. 16:9 landscape 1920x1080)
            # Crop width = height * (9/16)
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

cropping_service = CenterCropStrategy()

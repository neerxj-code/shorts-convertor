import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.cropping_service import FaceTrackingCropStrategy, CenterCropStrategy

def test_phase7():
    print("==================================================")
    print(" TESTING PHASE 7: SMART 9:16 REFRAMING & CROP STRATEGY ")
    print("==================================================")

    # 1. Test Center Crop Strategy fallback
    center_strat = CenterCropStrategy()
    filter_center = center_strat.calculate_crop_filter(in_width=1920, in_height=1080, target_w=1080, target_h=1920)
    print(f"[+] Center Crop Filter output: {filter_center}")
    assert "crop=" in filter_center and "scale=1080:1920" in filter_center, "Invalid center crop filter format"

    # 2. Test Face Tracking Crop Strategy
    face_strat = FaceTrackingCropStrategy()
    test_video = Path(__file__).parent / "test_video.mp4"
    
    filter_face = face_strat.calculate_crop_filter(
        in_width=1920,
        in_height=1080,
        target_w=1080,
        target_h=1920,
        video_path=str(test_video) if test_video.exists() else None,
        start_time=0.0,
        end_time=5.0
    )
    print(f"[+] Face Tracking Crop Filter output: {filter_face}")
    assert "crop=" in filter_face and "scale=1080:1920" in filter_face, "Invalid face crop filter format"

    print("\n[+] PHASE 7 SMART 9:16 REFRAMING TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase7()

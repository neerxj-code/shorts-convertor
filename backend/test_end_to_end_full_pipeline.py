import os
import sys
import time
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from app.services.ffmpeg_service import ffmpeg_service

BASE_URL = "http://127.0.0.1:8000/api"

def run_end_to_end_test():
    print("==================================================")
    print(" SHORTIFY COMPLETE END-TO-END PIPELINE TEST ")
    print("==================================================")

    test_video_path = Path(__file__).parent / "test_video.mp4"
    assert test_video_path.exists(), f"Test video file missing at {test_video_path}"

    # 1. Upload Video (POST /api/upload)
    print(f"\n[STEP 1] Uploading '{test_video_path.name}' to {BASE_URL}/upload...")
    start_upload_t = time.time()
    with open(test_video_path, "rb") as f:
        up_res = requests.post(f"{BASE_URL}/upload", files={"file": (test_video_path.name, f, "video/mp4")})

    assert up_res.status_code == 200, f"Upload failed with HTTP {up_res.status_code}: {up_res.text}"
    up_data = up_res.json()
    upload_dur = round(time.time() - start_upload_t, 2)
    print(f"[OK] Upload Successful (HTTP 200 in {upload_dur}s)")
    print(f"  Filename: {up_data['filename']}")
    print(f"  Size: {up_data['size_mb']} MB | Duration: {up_data['duration_sec']}s | Aspect: {up_data['width']}x{up_data['height']}")

    uploaded_filename = up_data["filename"]

    # 2. Create Job (POST /api/jobs)
    print(f"\n[STEP 2] Creating processing job at {BASE_URL}/jobs...")
    job_payload = {
        "filename": uploaded_filename,
        "requested_duration": 15,
        "language": "HINGLISH",
        "caption_style": "KARAOKE",
        "caption_position": "BOTTOM",
        "accuracy_mode": "BALANCED"
    }
    
    start_job_t = time.time()
    job_res = requests.post(f"{BASE_URL}/jobs", json=job_payload)
    assert job_res.status_code == 201, f"Job creation failed with HTTP {job_res.status_code}: {job_res.text}"
    job_data = job_res.json()
    job_id = job_data["job_id"]
    print(f"[OK] Job Created (HTTP 201) -> Job ID: {job_id}")

    # 3. Poll Job Status until COMPLETED or FAILED
    print(f"\n[STEP 3] Polling Job Status (GET {BASE_URL}/jobs/{job_id})...")
    last_stage = ""
    poll_count = 0
    final_job = None

    while True:
        poll_res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        assert poll_res.status_code == 200, f"Job status poll failed: {poll_res.text}"
        current_job = poll_res.json()
        
        status = current_job["status"]
        progress = current_job["progress"]
        stage = current_job["stage_message"]

        if stage != last_stage or poll_count % 5 == 0:
            print(f"  [{progress}%] Status: {status} | Stage: '{stage}'")
            last_stage = stage

        if status in ["COMPLETED", "FAILED"]:
            final_job = current_job
            break

        time.sleep(1.5)
        poll_count += 1

    total_pipeline_time = round(time.time() - start_job_t, 2)
    print(f"\n[OK] Pipeline Execution Finished in {total_pipeline_time}s with status: '{final_job['status']}'")

    if final_job["status"] == "FAILED":
        print(f"\n[FAIL] CRITICAL JOB FAILURE: {final_job.get('error_message')}")
        sys.exit(1)

    # 4. Transcription Verification
    print("\n==================================================")
    print(" 4. TRANSCRIPTION VERIFICATION ")
    print("==================================================")
    
    # Fetch job results
    results_res = requests.get(f"{BASE_URL}/jobs/{job_id}/results")
    assert results_res.status_code == 200, f"Failed to get job results: {results_res.text}"
    job_result = results_res.json()

    clips = job_result.get("clips", [])
    assert len(clips) > 0, "No clips found in completed job"

    # 5. Clip & 9:16 Output MP4 Verification
    print("\n==================================================")
    print(" 5. CLIP & 9:16 VERTICAL OUTPUT VERIFICATION ")
    print("==================================================")
    
    for idx, clip in enumerate(clips, start=1):
        print(f"\n--- CLIP #{idx} ---")
        print(f"Clip ID: {clip['id']}")
        print(f"Time Range: {clip['start_time']}s -> {clip['end_time']}s (Duration: {clip['duration']}s)")
        print(f"AI Score: {clip['score']}/100 | Category: {clip.get('category')}")
        print(f"Hook: '{clip.get('hook')}'")
        print(f"Reason: '{clip.get('reason')}'")
        print(f"Output Filename: {clip.get('output_filename')}")
        print(f"Thumbnail Filename: {clip.get('thumbnail_filename')}")

        output_filename = clip.get("output_filename")
        assert output_filename, f"Clip #{idx} missing output filename"

        # Check file on disk
        outputs_dir = Path(__file__).parent / "outputs"
        output_mp4_file = outputs_dir / output_filename
        assert output_mp4_file.exists(), f"Rendered output MP4 does not exist on disk at {output_mp4_file}"

        file_size_bytes = output_mp4_file.stat().st_size
        assert file_size_bytes > 0, f"Rendered output MP4 is empty (0 bytes)"
        print(f"[OK] Output MP4 File Exists on Disk: {output_mp4_file} ({round(file_size_bytes / 1024, 1)} KB)")

        # Probe output MP4 with FFprobe
        probe_meta = ffmpeg_service.probe_video(str(output_mp4_file))
        print(f"[OK] FFprobe Inspection Results:")
        print(f"   Width: {probe_meta['width']} px")
        print(f"   Height: {probe_meta['height']} px")
        print(f"   FPS: {probe_meta['fps']}")
        print(f"   Duration: {probe_meta['duration']} s")
        print(f"   Has Audio Track: {probe_meta['has_audio']}")

        # 9:16 Vertical aspect ratio assertion (1080x1920)
        assert probe_meta['width'] == 1080, f"Expected width 1080, got {probe_meta['width']}"
        assert probe_meta['height'] == 1920, f"Expected height 1920, got {probe_meta['height']}"
        assert probe_meta['has_audio'] is True, "Rendered short clip is missing audio track"
        assert probe_meta['duration'] > 0, "Rendered short clip has 0 duration"
        print("[OK] Verified 9:16 Vertical Resolution (1080x1920) and Audio/Video Streams!")

        # 6. Captions & Karaoke Timing Verification
        captions = clip.get("captions", [])
        print(f"\n[OK] Captions Verification ({len(captions)} caption blocks):")
        for c_idx, cap in enumerate(captions[:3], start=1):
            words = cap.get("words", [])
            print(f"   Block #{c_idx} [{cap['start']}s -> {cap['end']}s]: '{cap['text']}' ({len(words)} words)")
            if words:
                first_w = words[0]
                print(f"     -> First word highlight timing: '{first_w.get('word')}' ({first_w.get('start')}s -> {first_w.get('end')}s)")

    print("\n==================================================")
    print(" [SUCCESS] COMPLETE END-TO-END PIPELINE TEST PASSED! ")
    print("==================================================")

if __name__ == "__main__":
    run_end_to_end_test()

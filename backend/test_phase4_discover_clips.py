import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.clip_analysis_service import clip_analysis_service, LocalHeuristicClipAnalyzer, ClipAnalysisProvider
from app.services.transcription_service import LocalWhisperProvider
from app.services.ffmpeg_service import ffmpeg_service

def test_discovery():
    print("==================================================")
    print(" TESTING REAL AI SHORT CLIP DISCOVERY & SCORING ")
    print("==================================================")

    # 1. Verify Abstraction
    analyzer = LocalHeuristicClipAnalyzer()
    assert isinstance(analyzer, ClipAnalysisProvider), "LocalHeuristicClipAnalyzer must inherit from ClipAnalysisProvider ABC"
    print("[+] Interface abstraction test passed (isinstance ClipAnalysisProvider)")

    test_video = Path(__file__).parent / "test_video.mp4"
    temp_wav = Path(__file__).parent / "temp" / "test_discovery_audio.wav"
    temp_wav.parent.mkdir(parents=True, exist_ok=True)

    if test_video.exists():
        print(f"[*] Extracting audio from {test_video.name}...")
        ffmpeg_service.extract_audio(str(test_video), str(temp_wav))
        
        print("[*] Running transcription...")
        provider = LocalWhisperProvider()
        transcript = provider.transcribe(str(temp_wav), language_hint="HINGLISH", accuracy_mode="BALANCED")
    else:
        print("[*] Using mock long video transcript...")
        transcript = {
            "segments": [
                {"start": 0.0, "end": 4.0, "text": "Welcome everyone to our deep dive session today."},
                {"start": 4.5, "end": 12.0, "text": "What is the biggest mistake creators make when building short videos?"},
                {"start": 12.5, "end": 22.0, "text": "The secret reason is they focus only on cutting instead of storytelling and hook density."},
                {"start": 22.5, "end": 32.0, "text": "Basically, if your first three seconds don't grab attention, viewers scroll away immediately."},
                {"start": 32.5, "end": 42.0, "text": "Aaj hum issi concept ko practical example se dekhenge."},
                {"start": 42.5, "end": 52.0, "text": "This amazing insight completely changed how our short video converter works."},
                {"start": 52.5, "end": 62.0, "text": "So always optimize your caption timing and active speaker framing."}
            ]
        }

    # 2. Test Discovery for 30s target
    print("\n--- DISCOVERING CANDIDATES (Target Duration: 30s) ---")
    candidates_30s = analyzer.analyze_transcript(transcript, target_duration=30, max_clips=5)
    
    for idx, cand in enumerate(candidates_30s, start=1):
        print(f"\n[SHORT #{idx}]")
        print(f"  Start: {cand['start']}s | End: {cand['end']}s | Duration: {cand['duration']}s")
        print(f"  Total Score: {cand['score']}/100 | Category: {cand['category']}")
        print(f"  Score Breakdown: {cand['score_breakdown']}")
        print(f"  Hook: \"{cand['hook']}\"")
        print(f"  Reason: {cand['reason']}")
        print(f"  Transcript: \"{cand['transcript'][:90]}...\"")

        assert "score" in cand and "score_breakdown" in cand, "Candidate missing score breakdown"
        assert "hook" in cand and "category" in cand, "Candidate missing hook or category"

    # 3. Test Discovery for 60s target
    print("\n--- DISCOVERING CANDIDATES (Target Duration: 60s) ---")
    candidates_60s = analyzer.analyze_transcript(transcript, target_duration=60, max_clips=5)
    for idx, cand in enumerate(candidates_60s, start=1):
        print(f"[SHORT #{idx}] Duration: {cand['duration']}s | Score: {cand['score']} | Category: {cand['category']} | Hook: \"{cand['hook']}\"")

    print("\n[+] REAL AI SHORT CLIP DISCOVERY TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_discovery()

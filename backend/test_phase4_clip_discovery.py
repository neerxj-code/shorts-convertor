import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.clipping_service import AIClipDiscoveryStrategy

def test_phase4():
    print("==================================================")
    print(" TESTING PHASE 4 & 5 & 6: AI CLIP DISCOVERY ")
    print("==================================================")

    strategy = AIClipDiscoveryStrategy()

    # Mock master transcript with multiple segments containing hooks, questions, and insights
    mock_transcript = {
        "segments": [
            {"start": 0.0, "end": 4.2, "text": "Welcome back everyone to today's video."},
            {"start": 4.5, "end": 12.0, "text": "What is the biggest mistake creators make when building short videos?"},
            {"start": 12.5, "end": 22.0, "text": "The secret reason is they focus only on cutting instead of storytelling and hook density."},
            {"start": 22.5, "end": 32.0, "text": "Basically, if your first three seconds don't grab attention, viewers scroll away immediately."},
            {"start": 32.5, "end": 42.0, "text": "Aaj hum issi concept ko practical example se dekhenge."},
            {"start": 42.5, "end": 52.0, "text": "This amazing insight completely changed how our short video converter works."},
            {"start": 52.5, "end": 62.0, "text": "So always optimize your caption timing and active speaker framing."}
        ]
    }

    total_duration = 65.0
    requested_duration = 30  # Target 30 seconds

    candidates = strategy.generate_clip_boundaries(
        total_duration=total_duration,
        requested_duration=requested_duration,
        master_transcript=mock_transcript
    )

    assert len(candidates) > 0, "No candidate clips generated"
    print(f"[+] Successfully discovered {len(candidates)} high-value short candidates:\n")

    for idx, cand in enumerate(candidates, start=1):
        print(f"--- CANDIDATE #{idx} ---")
        print(f"Time Range: {cand['start']}s -> {cand['end']}s (Duration: {cand['duration']}s)")
        print(f"AI Score: {cand['score']}/100")
        print(f"Hook: '{cand['hook']}'")
        print(f"Reason: {cand['reason']}")
        print(f"Snippet: '{cand['transcript'][:80]}...'")
        print()

        assert "start" in cand and "end" in cand and "score" in cand, "Candidate missing required keys"
        assert cand["score"] >= 30, "Invalid candidate score below minimum"
        assert cand["duration"] >= 15.0, "Candidate duration too short"

    print("[+] PHASE 4 & 5 & 6 AI CLIP DISCOVERY TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase4()

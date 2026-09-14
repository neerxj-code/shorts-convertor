import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.caption_service import caption_service

def test_phase2():
    print("==================================================")
    print(" TESTING PHASE 2: WORD ALIGNMENT & NORMALIZATION ")
    print("==================================================")

    dummy_segments = [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "Hello guys welcome to Shortify",
            "words": [
                {"word": "Hello", "start": 0.1, "end": 0.5, "confidence": 0.98},
                {"word": "guys", "start": 0.55, "end": 0.9, "confidence": 0.95},
                {"word": "welcome", "start": 0.95, "end": 1.4, "confidence": 0.92},
                {"word": "to", "start": 1.45, "end": 1.7, "confidence": 0.99},
                {"word": "Shortify", "start": 1.75, "end": 2.4, "confidence": 0.96}
            ]
        },
        {
            "start": 2.8,
            "end": 4.5,
            "text": "Aaj hum basic clip discovery discuss karenge",
            "words": [
                {"word": "Aaj", "start": 2.85, "end": 3.1, "confidence": 0.94},
                {"word": "hum", "start": 3.15, "end": 3.4, "confidence": 0.93},
                {"word": "basic", "start": 3.45, "end": 3.8, "confidence": 0.97},
                {"word": "clip", "start": 3.85, "end": 4.0, "confidence": 0.99},
                {"word": "discovery", "start": 4.05, "end": 4.5, "confidence": 0.91}
            ]
        }
    ]

    # Test word timeline normalization
    normalized_words = caption_service.normalize_word_timeline(dummy_segments)
    
    assert len(normalized_words) == 10, f"Expected 10 normalized words, got {len(normalized_words)}"
    
    for w in normalized_words:
        assert "text" in w and "word" in w and "start" in w and "end" in w and "confidence" in w, \
            f"Normalized word dict missing keys: {w}"
        assert w["end"] >= w["start"], f"Invalid timestamp order for word {w}"
        assert 0.0 <= w["confidence"] <= 1.0, f"Invalid confidence range for word {w}"

    print(f"[+] Successfully normalized {len(normalized_words)} word timeline items:")
    for w in normalized_words[:3]:
        print(f"    - '{w['text']}' [{w['start']}s -> {w['end']}s] (conf: {w['confidence']})")

    # Test chunking with normalized word alignment
    chunked = caption_service.chunk_captions(dummy_segments, max_words_per_line=3)
    assert len(chunked) > 0, "Chunked captions empty"
    print(f"[+] Generated {len(chunked)} short caption blocks:")
    for c in chunked:
        print(f"    - [{c['start']}s - {c['end']}s]: '{c['text']}' (words count: {len(c['words'])})")

    print("\n[+] PHASE 2 WORD ALIGNMENT TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase2()

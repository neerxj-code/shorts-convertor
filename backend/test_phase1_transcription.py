import os
import sys
import json
from pathlib import Path

# Ensure app package is in path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.transcription_service import LocalWhisperProvider, TranscriptionProvider
from app.services.ffmpeg_service import ffmpeg_service

def test_phase1():
    print("==================================================")
    print(" TESTING PHASE 1: HIGH ACCURACY TRANSCRIPTION ")
    print("==================================================")

    # 1. Verify Abstraction Inheritance
    provider = LocalWhisperProvider()
    assert isinstance(provider, TranscriptionProvider), "LocalWhisperProvider must inherit from TranscriptionProvider ABC"
    print("[+] Provider abstraction test passed (isinstance TranscriptionProvider)")

    test_video = Path(__file__).parent / "test_video.mp4"
    temp_wav = Path(__file__).parent / "temp" / "test_phase1_audio.wav"
    temp_wav.parent.mkdir(parents=True, exist_ok=True)

    if not test_video.exists():
        print(f"[-] Warning: Test video {test_video} does not exist. Skipping audio transcription execution test.")
        return

    print(f"[*] Extracting 16kHz mono audio from {test_video.name}...")
    success = ffmpeg_service.extract_audio(str(test_video), str(temp_wav))
    assert success and temp_wav.exists(), "Audio extraction failed"
    print(f"[+] Audio extracted to {temp_wav}")

    # 2. Test Transcription with 'small' / 'base' / 'large-v3'
    print("[*] Transcribing audio with LocalWhisperProvider (Mode: BALANCED, Language: HINGLISH)...")
    res = provider.transcribe(
        audio_path=str(temp_wav),
        language_hint="HINGLISH",
        accuracy_mode="BALANCED"
    )

    print("\n--- TRANSCRIPTION RESULT SUMMARY ---")
    print(f"Model used: {res.get('whisper_model_used')}")
    print(f"Language: {res.get('language')}")
    print(f"Total Segments: {res.get('total_segments')}")
    print(f"Total Words: {res.get('total_words')}")
    print(f"Suspicious Filtered: {res.get('suspicious_filtered_count')}")
    print(f"Full Text: {res.get('text')}")

    # 3. Verify Output Specifications
    assert "segments" in res, "Missing 'segments' in result"
    assert "language" in res, "Missing 'language' in result"
    assert "text" in res, "Missing 'text' in result"

    segments = res["segments"]
    if segments:
        first_seg = segments[0]
        assert "start" in first_seg and "end" in first_seg and "text" in first_seg, "Segment metadata missing start/end/text"
        assert "words" in first_seg, "Segment missing word-level timestamps"
        if first_seg["words"]:
            first_word = first_seg["words"][0]
            assert "word" in first_word and "start" in first_word and "end" in first_word and "confidence" in first_word, \
                "Word metadata missing required keys (word, start, end, confidence)"
            print(f"[+] First word structure verified: {first_word}")

    print("\n[+] PHASE 1 TRANSCRIPTION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase1()

import os
import sys
import time
import json
import torch
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ffmpeg_service import ffmpeg_service
from app.services.transcription_service import LocalWhisperProvider, _safe_str

def run_whisper_benchmark():
    print("==================================================")
    print(" SHORTIFY HINGLISH TRANSCRIPTION BENCHMARK ")
    print(" BASE vs SMALL vs LARGE-V3 COMPARISON TEST ")
    print("==================================================")

    # 1. Locate test video
    backend_dir = Path(__file__).parent
    test_video_path = backend_dir / "test_video.mp4"
    assert test_video_path.exists(), f"No test video found at {test_video_path}"

    print(f"\n[BENCHMARK SOURCE] File: '{test_video_path.name}' ({round(test_video_path.stat().st_size / (1024*1024), 2)} MB)")
    
    # 2. Extract 30-Second Audio WAV for Benchmarking
    wav_path = backend_dir / "temp" / f"benchmark_{test_video_path.stem}.wav"
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[AUDIO EXTRACTION] Extracting 30s 16kHz mono WAV clip to {wav_path}...")
    # Extract audio using FFmpeg with max duration 30 seconds
    cmd = [
        ffmpeg_service.ffmpeg_path, "-y",
        "-ss", "0", "-i", str(test_video_path),
        "-t", "30",
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(wav_path)
    ]
    import subprocess
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    assert wav_path.exists() and wav_path.stat().st_size > 0, "Audio extraction failed!"

    audio_duration = 30.0
    print(f"[AUDIO METADATA] Duration: {audio_duration:.2f} seconds | Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

    # 3. Models to benchmark
    models_to_test = [
        ("FAST", "base"),
        ("BALANCED", "small"),
        ("ACCURATE", "large-v3")
    ]

    provider = LocalWhisperProvider()
    results = {}

    for mode, model_name in models_to_test:
        print(f"\n" + "="*50)
        print(f" RUNNING MODEL TEST: Accuracy Mode='{mode}' -> Requested='{model_name}'")
        print("="*50)

        t_start = time.time()
        try:
            res = provider.transcribe(
                audio_path=str(wav_path),
                language_hint="HINGLISH",
                accuracy_mode=mode,
                model_size=model_name
            )
            dur = round(time.time() - t_start, 2)
            speed_ratio = round(audio_duration / max(0.1, dur), 2)
            
            res["benchmark_proc_time_sec"] = dur
            res["benchmark_speed_ratio"] = speed_ratio
            results[model_name] = res

            print(f"[RESULT OK] Mode: {mode} | Requested: {model_name} | Actual: {res['whisper_model_used']}")
            print(f"  Processing Time: {dur}s ({speed_ratio}x real-time)")
            print(f"  Detected Language: {res['language']}")
            print(f"  Total Words: {res['total_words']} | Total Segments: {res['total_segments']}")
            print(f"  Hallucinations Suppressed: {res['suspicious_filtered_count']}")
            print(f"  Full Transcript: '{_safe_str(res['text'])}'")
            
            print(f"\n  Word Timestamps Sample (First 8 words):")
            sample_words = []
            for seg in res.get("segments", []):
                for w in seg.get("words", []):
                    sample_words.append(w)
                    if len(sample_words) >= 8:
                        break
                if len(sample_words) >= 8:
                    break
            
            for sw in sample_words:
                print(f"    - Word: '{_safe_str(sw['word'])}' | Start: {sw['start']}s | End: {sw['end']}s | Conf: {sw.get('confidence', 1.0)}")

        except Exception as e:
            dur = round(time.time() - t_start, 2)
            print(f"[RESULT FAILED] Model '{model_name}' failed after {dur}s: {e}")
            results[model_name] = {
                "error": str(e),
                "whisper_model_used": "FAILED",
                "benchmark_proc_time_sec": dur
            }

    # 4. Comparative Benchmark Summary Table
    print("\n" + "="*70)
    print(" HINGLISH WHISPER ACCURACY & PERFORMANCE COMPARISON SUMMARY ")
    print("="*70)
    print(f"{'ACCURACY MODE':<15} | {'MODEL':<10} | {'ACTUAL LOADED':<12} | {'TIME(s)':<8} | {'SPEED':<8} | {'WORDS':<6} | {'LANG':<5}")
    print("-" * 75)

    for mode, model_name in models_to_test:
        r = results.get(model_name, {})
        if "error" in r:
            print(f"{mode:<15} | {model_name:<10} | {'FAILED':<12} | {r.get('benchmark_proc_time_sec', 0):<8} | {'N/A':<8} | {'0':<6} | {'N/A':<5}")
        else:
            actual = r.get("whisper_model_used", "N/A")
            proc_t = r.get("benchmark_proc_time_sec", 0)
            spd = f"{r.get('benchmark_speed_ratio', 0)}x"
            w_cnt = r.get("total_words", 0)
            lang = r.get("language", "N/A")
            print(f"{mode:<15} | {model_name:<10} | {actual:<12} | {proc_t:<8} | {spd:<8} | {w_cnt:<6} | {lang:<5}")

    print("="*70)

    # Cleanup temp wav
    if wav_path.exists():
        os.unlink(wav_path)

if __name__ == "__main__":
    run_whisper_benchmark()

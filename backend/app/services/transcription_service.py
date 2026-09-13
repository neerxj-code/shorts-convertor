import os
import sys
import torch
from typing import Dict, Any, List
from app.core.config import settings

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def _safe_str(text: str) -> str:
    """Safe string encoding for Windows console print logging."""
    if not isinstance(text, str):
        return str(text)
    return text.encode("ascii", errors="backslashreplace").decode("ascii")

class TranscriptionProvider:
    def transcribe(
        self,
        audio_path: str,
        language_hint: str = "AUTO",
        accuracy_mode: str = "BALANCED"
    ) -> Dict[str, Any]:
        raise NotImplementedError

class WhisperProvider(TranscriptionProvider):
    _models = {}

    def __init__(self, default_model: str = None):
        self.default_model = default_model or settings.WHISPER_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[WhisperProvider] Initialized Whisper Engine (Default: {self.default_model}, Device: {self.device})")

    def _select_model_name(self, accuracy_mode: str) -> str:
        acc = (accuracy_mode or "BALANCED").upper()
        if acc == "FAST":
            return "base"
        elif acc == "ACCURATE":
            return "large-v3" if torch.cuda.is_available() else "medium"
        else:
            return settings.WHISPER_MODEL or "small"

    def _get_model(self, model_name: str):
        if model_name not in WhisperProvider._models:
            import whisper
            print(f"[WhisperProvider] Loading Whisper model '{model_name}' on device '{self.device}'...")
            try:
                WhisperProvider._models[model_name] = whisper.load_model(model_name, device=self.device)
            except Exception as e:
                print(f"[WhisperProvider] Failed to load requested model '{model_name}' ({e}), falling back to 'base'...")
                if "base" not in WhisperProvider._models:
                    WhisperProvider._models["base"] = whisper.load_model("base", device=self.device)
                return WhisperProvider._models["base"]

        return WhisperProvider._models[model_name]

    def transcribe(
        self,
        audio_path: str,
        language_hint: str = "AUTO",
        accuracy_mode: str = "BALANCED"
    ) -> Dict[str, Any]:
        model_name = self._select_model_name(accuracy_mode)
        model = self._get_model(model_name)
        
        # Prepare options based on language hint
        lang_arg = None
        if language_hint and language_hint.upper() not in ["AUTO", "HINGLISH"]:
            if language_hint.upper() == "ENGLISH":
                lang_arg = "en"
            elif language_hint.upper() == "HINDI":
                lang_arg = "hi"
            else:
                lang_arg = language_hint.lower()

        # Hinglish code-switching initial prompt context
        prompt_text = (
            "A natural conversation in Hinglish containing a mix of Hindi and English words like: "
            "aaj, hum, guys, basically, simple, understand, topic, kaafi, consistent, video, shorts, concept."
            if language_hint and language_hint.upper() in ["HINGLISH", "AUTO"] else None
        )

        print(f"[WhisperProvider] Transcribing '{audio_path}' (Model: {model_name}, Mode: {accuracy_mode}, Language: {language_hint})...")
        
        # Base Whisper execution options
        kwargs = {
            "word_timestamps": True,
            "task": "transcribe",  # Never translate
            "condition_on_previous_text": False, # Reduce hallucination repetition loops
            "no_speech_threshold": 0.6,
            "logprob_threshold": -1.0,
            "compression_ratio_threshold": 2.4
        }
        if lang_arg:
            kwargs["language"] = lang_arg
        if prompt_text:
            kwargs["initial_prompt"] = prompt_text

        try:
            result = model.transcribe(audio_path, **kwargs)
        except Exception as e:
            print(f"[WhisperProvider] Warning: word_timestamps / advanced kwargs failed ({e}), retrying basic transcribe...")
            kwargs_basic = {"task": "transcribe"}
            if lang_arg:
                kwargs_basic["language"] = lang_arg
            result = model.transcribe(audio_path, **kwargs_basic)

        detected_lang = result.get("language", "en")
        raw_segments = result.get("segments", [])
        
        processed_segments = []
        suspicious_filtered_count = 0
        total_words_count = 0

        # Known hallucinated phantom phrases during silence
        HALLUCINATED_PHRASES = {
            "thank you for watching", "thanks for watching", "subscribe to my channel",
            "subtitles by", "amara.org", "like and subscribe", "bye bye", "see you next time"
        }

        for seg in raw_segments:
            seg_start = float(seg.get("start", 0.0))
            seg_end = float(seg.get("end", 0.0))
            seg_text = seg.get("text", "").strip()

            no_speech_prob = float(seg.get("no_speech_prob", 0.0))
            avg_logprob = float(seg.get("avg_logprob", 0.0))
            comp_ratio = float(seg.get("compression_ratio", 1.0))

            # VAD & Hallucination Suppression Check
            if no_speech_prob > 0.65 or avg_logprob < -1.2 or comp_ratio > 2.6:
                print(f"[WhisperProvider] Suppressed suspicious/no-speech segment: '{_safe_str(seg_text)}' (no_speech_prob={no_speech_prob:.2f}, logprob={avg_logprob:.2f})")
                suspicious_filtered_count += 1
                continue

            if seg_text.lower() in HALLUCINATED_PHRASES:
                print(f"[WhisperProvider] Suppressed phantom subtitle phrase: '{_safe_str(seg_text)}'")
                suspicious_filtered_count += 1
                continue
            
            raw_words = seg.get("words", [])
            words_list = []
            
            if raw_words:
                for w in raw_words:
                    word_text = w.get("word", "").strip()
                    if not word_text:
                        continue
                    w_start = float(w.get("start", seg_start))
                    w_end = float(w.get("end", seg_end))
                    words_list.append({
                        "word": word_text,
                        "text": word_text,
                        "start": round(w_start, 2),
                        "end": round(w_end, 2)
                    })
                    total_words_count += 1
            
            # Fallback word timing estimation if word timestamps missing
            if not words_list and seg_text:
                tokens = seg_text.split()
                if tokens:
                    total_dur = max(0.1, seg_end - seg_start)
                    dur_per_token = total_dur / len(tokens)
                    curr = seg_start
                    for tok in tokens:
                        words_list.append({
                            "word": tok,
                            "text": tok,
                            "start": round(curr, 2),
                            "end": round(curr + dur_per_token, 2)
                        })
                        curr += dur_per_token
                        total_words_count += 1

            processed_segments.append({
                "start": round(seg_start, 2),
                "end": round(seg_end, 2),
                "text": seg_text,
                "words": words_list
            })

        return {
            "language": detected_lang,
            "text": result.get("text", "").strip(),
            "segments": processed_segments,
            "whisper_model_used": model_name,
            "accuracy_mode": accuracy_mode,
            "total_segments": len(processed_segments),
            "total_words": total_words_count,
            "suspicious_filtered_count": suspicious_filtered_count
        }

# Global instance initialization
transcription_service = WhisperProvider()

import os
import sys
import abc
import torch
from typing import Dict, Any, List, Optional
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


class TranscriptionProvider(abc.ABC):
    """
    Abstract Base Class for ASR (Automatic Speech Recognition) Providers.
    Ensures modularity allowing LocalWhisperProvider or future Cloud ASR providers (e.g. Deepgram, AssemblyAI).
    """

    @abc.abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language_hint: str = "AUTO",
        accuracy_mode: str = "BALANCED",
        model_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribes audio file and returns standardized transcript result.
        
        Must return a dict containing:
        - language: str (e.g. 'en', 'hi')
        - text: str (complete transcript text)
        - segments: List[Dict] with start, end, text, words, confidence metadata
        - whisper_model_used: str
        - total_segments: int
        - total_words: int
        - suspicious_filtered_count: int
        """
        pass


class LocalWhisperProvider(TranscriptionProvider):
    """
    Local Whisper ASR Provider supporting models: base, small, medium, large-v3.
    Recommends 'large-v3' for highest accuracy with automatic fallback.
    """
    _models: Dict[str, Any] = {}

    SUPPORTED_MODELS = ["base", "small", "medium", "large-v3"]

    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or settings.WHISPER_MODEL or "small"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[LocalWhisperProvider] Initialized Engine (Default: {self.default_model}, Device: {self.device})")

    def _select_model_name(self, accuracy_mode: str, requested_model: Optional[str] = None) -> str:
        if requested_model and requested_model.lower() in self.SUPPORTED_MODELS:
            return requested_model.lower()

        acc = (accuracy_mode or "BALANCED").upper()
        if acc in ["ACCURATE", "HIGH", "LARGE"]:
            return "large-v3"
        elif acc == "FAST":
            return "base"
        elif acc == "MEDIUM":
            return "medium"
        else:
            # BALANCED
            return "small"

    def _get_model(self, model_name: str):
        if model_name not in LocalWhisperProvider._models:
            import whisper
            print(f"[LocalWhisperProvider] Loading Whisper model '{model_name}' on device '{self.device}'...")
            
            fallback_sequence = [model_name]
            for fb in ["large-v3", "medium", "small", "base"]:
                if fb not in fallback_sequence:
                    fallback_sequence.append(fb)

            loaded_model = None
            loaded_name = model_name
            failure_reasons = {}

            for candidate in fallback_sequence:
                try:
                    print(f"[LocalWhisperProvider] Attempting to load Whisper model '{candidate}' on {self.device}...")
                    loaded_model = whisper.load_model(candidate, device=self.device)
                    loaded_name = candidate
                    break
                except Exception as e:
                    reason_msg = f"Failed on {self.device}: {str(e)}"
                    print(f"[LocalWhisperProvider] Warning: {reason_msg}")
                    failure_reasons[candidate] = reason_msg
                    
                    if self.device == "cuda":
                        try:
                            print(f"[LocalWhisperProvider] Retrying '{candidate}' on CPU fallback...")
                            loaded_model = whisper.load_model(candidate, device="cpu")
                            loaded_name = candidate
                            break
                        except Exception as e_cpu:
                            reason_cpu = f"Failed on CPU: {str(e_cpu)}"
                            print(f"[LocalWhisperProvider] Warning: {reason_cpu}")
                            failure_reasons[f"{candidate}_cpu"] = reason_cpu

            if not loaded_model:
                raise RuntimeError(
                    f"Failed to load Whisper model '{model_name}'. Diagnostic log:\n"
                    + "\n".join(f" - {k}: {v}" for k, v in failure_reasons.items())
                )

            if loaded_name != model_name:
                print(
                    f"\n[LocalWhisperProvider] FALLBACK NOTICE:\n"
                    f"  REQUESTED MODEL: {model_name}\n"
                    f"  ACTUAL MODEL   : {loaded_name}\n"
                    f"  REASON         : Requested model '{model_name}' failed to load ({failure_reasons.get(model_name, 'Resource constraints')})\n"
                )

            LocalWhisperProvider._models[loaded_name] = loaded_model
            return loaded_name, loaded_model

        return model_name, LocalWhisperProvider._models[model_name]

    def transcribe(
        self,
        audio_path: str,
        language_hint: str = "AUTO",
        accuracy_mode: str = "BALANCED",
        model_size: Optional[str] = None
    ) -> Dict[str, Any]:
        target_model_name = self._select_model_name(accuracy_mode, model_size)
        actual_model_name, model = self._get_model(target_model_name)
        
        # Log exact requested vs actual model
        print(f"\n[LocalWhisperProvider] Accuracy Mode: {accuracy_mode.upper()}")
        print(f"[LocalWhisperProvider] Requested Model: {target_model_name}")
        print(f"[LocalWhisperProvider] Actual Loaded Model: {actual_model_name}")
        print(f"[LocalWhisperProvider] Speech Language Mode: {language_hint.upper()}\n")

        # Prepare options based on language hint
        lang_arg = None
        lang_upper = (language_hint or "AUTO").upper()
        
        if lang_upper not in ["AUTO", "HINGLISH"]:
            if lang_upper == "ENGLISH":
                lang_arg = "en"
            elif lang_upper == "HINDI":
                lang_arg = "hi"
            else:
                lang_arg = language_hint.lower()

        # Hinglish code-switching initial prompt context
        prompt_text = None
        if lang_upper in ["HINGLISH", "AUTO"]:
            prompt_text = (
                "Yeh ek natural Hinglish conversation hai featuring mixed Hindi and English speech like: "
                "guys, video, topic, aaj, hum, simple, basically, important, consistency, bohot, acha, "
                "experience, workflow, output, quality, concept, strategy, results."
            )

        print(f"[LocalWhisperProvider] Transcribing audio '{audio_path}'...")
        
        # Base Whisper execution options - ALWAYS enforce task='transcribe' (NEVER translate)
        kwargs = {
            "word_timestamps": True,
            "task": "transcribe",
            "condition_on_previous_text": False,  # Prevents hallucination loops during pauses
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
            print(f"[LocalWhisperProvider] Advanced word_timestamps kwargs failed ({e}), falling back to basic transcribe...")
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
            "subtitles by", "amara.org", "like and subscribe", "bye bye", "see you next time",
            "thank you", "thanks", "subscribe"
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
                print(f"[LocalWhisperProvider] Suppressed suspicious/no-speech segment: '{_safe_str(seg_text)}' (no_speech_prob={no_speech_prob:.2f}, logprob={avg_logprob:.2f})")
                suspicious_filtered_count += 1
                continue

            if seg_text.lower().strip(".!?,") in HALLUCINATED_PHRASES:
                print(f"[LocalWhisperProvider] Suppressed phantom subtitle phrase: '{_safe_str(seg_text)}'")
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
                    w_conf = float(w.get("probability", 1.0 - no_speech_prob))
                    words_list.append({
                        "word": word_text,
                        "text": word_text,
                        "start": round(w_start, 2),
                        "end": round(w_end, 2),
                        "confidence": round(w_conf, 2)
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
                            "end": round(curr + dur_per_token, 2),
                            "confidence": 0.70
                        })
                        curr += dur_per_token
                        total_words_count += 1

            processed_segments.append({
                "start": round(seg_start, 2),
                "end": round(seg_end, 2),
                "text": seg_text,
                "words": words_list,
                "no_speech_prob": round(no_speech_prob, 3),
                "avg_logprob": round(avg_logprob, 3),
                "compression_ratio": round(comp_ratio, 3)
            })

        return {
            "language": detected_lang,
            "text": result.get("text", "").strip(),
            "segments": processed_segments,
            "whisper_model_used": actual_model_name,
            "requested_model": target_model_name,
            "accuracy_mode": accuracy_mode,
            "language_hint": language_hint,
            "total_segments": len(processed_segments),
            "total_words": total_words_count,
            "suspicious_filtered_count": suspicious_filtered_count
        }


# Backward compatibility alias
WhisperProvider = LocalWhisperProvider

# Global instance initialization
transcription_service = LocalWhisperProvider()


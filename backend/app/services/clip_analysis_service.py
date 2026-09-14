import re
import abc
import json
from typing import List, Dict, Any, Tuple, Optional

class ClipAnalysisProvider(abc.ABC):
    """
    Abstract Base Class for AI Short Clip Discovery & Scoring.
    Allows local heuristic analyzers or future LLM-based analyzers (OpenAI, Gemini, Local LLM)
    without rewriting the application or requiring API keys.
    """

    @abc.abstractmethod
    def analyze_transcript(
        self,
        master_transcript: Dict[str, Any],
        target_duration: int = 60,
        max_clips: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyzes master transcript and returns ranked candidate moments.
        
        Must return list of dicts containing:
        - start: float
        - end: float
        - duration: float
        - score: int (0-100)
        - hook_score: int (0-20)
        - value_score: int (0-20)
        - emotion_score: int (0-20)
        - completeness_score: int (0-20)
        - ending_score: int (0-20)
        - silence_penalty: int (0 to -20)
        - category: str (Educational, Story, Insight, Humor, Opinion, Advice)
        - hook: str
        - reason: str
        - transcript: str
        """
        pass


class LocalHeuristicClipAnalyzer(ClipAnalysisProvider):
    """
    Rule-based & heuristic transcript analyzer for finding high-value Shorts.
    Processes English, Hindi, and Hinglish transcripts natively without translation or API keys.
    """

    HOOK_KEYWORDS = [
        "biggest", "mistake", "secret", "never", "always", "why", "how", "what",
        "stop", "start", "don't", "kya", "kaise", "kyun", "galti", "sabse", "secret",
        "reason", "truth", "magic", "power", "rule", "lesson", "tips", "hacks",
        "remember", "important", "nobody", "everyone", "failed", "success"
    ]

    EMOTIONAL_KEYWORDS = [
        "amazing", "crazy", "wrong", "dangerous", "unbelievable", "important",
        "shocking", "bohot", "jaruri", "fail", "win", "money", "growth", "viral",
        "terrible", "incredible", "mindblowing", "scary", "hardest", "best"
    ]

    VALUE_KEYWORDS = [
        "because", "therefore", "step", "first", "second", "third", "example",
        "solution", "strategy", "method", "result", "system", "process", "tarika",
        "upay", "samjho", "soch", "concept", "technique", "formula"
    ]

    AMBIGUOUS_PRONOUNS_START = [
        "he did", "she did", "they did", "it is because", "that is why", "and then he",
        "usne kiya", "unhone kaha", "iss vajah se", "woh bola"
    ]

    CATEGORIES = {
        "Educational": ["how", "why", "step", "method", "strategy", "concept", "samjho", "learn"],
        "Story": ["failed", "remember", "when i", "first time", "story", "ek baar", "experience"],
        "Insight": ["secret", "truth", "nobody", "biggest", "rule", "realize", "actually"],
        "Advice": ["mistake", "never", "always", "stop", "should", "galti", "mat karo", "tips"],
        "Opinion": ["believe", "think", "wrong", "agree", "disagree", "sochta hun", "view"]
    }

    def _determine_category(self, text: str) -> str:
        lower_text = text.lower()
        cat_scores = {cat: 0 for cat in self.CATEGORIES}
        for cat, kws in self.CATEGORIES.items():
            for kw in kws:
                if kw in lower_text:
                    cat_scores[cat] += 1
        best_cat = max(cat_scores, key=cat_scores.get)
        return best_cat if cat_scores[best_cat] > 0 else "Insight"

    def _score_candidate_window(
        self,
        start_time: float,
        end_time: float,
        segments_in_range: List[Dict[str, Any]],
        target_duration: int
    ) -> Tuple[int, Dict[str, int], str, str, str, str]:
        duration = end_time - start_time
        if duration <= 0 or not segments_in_range:
            return 0, {}, "", "Empty transcript", "Insight", ""

        text_list = [s.get("text", "").strip() for s in segments_in_range if s.get("text", "").strip()]
        full_transcript = " ".join(text_list)
        if not full_transcript:
            return 0, {}, "", "No speech text", "Insight", ""

        opening_text = text_list[0].lower() if text_list else ""
        closing_text = text_list[-1].lower() if text_list else ""

        # 1. Hook Score (0 - 20)
        hook_score = 8
        if any(kw in opening_text for kw in self.HOOK_KEYWORDS):
            hook_score += 8
        if opening_text.endswith("?") or "?" in opening_text:
            hook_score += 4
        hook_score = min(20, hook_score)

        # 2. Value Score (0 - 20)
        value_count = sum(1 for kw in self.VALUE_KEYWORDS if kw in full_transcript.lower())
        value_score = min(20, 6 + value_count * 3)

        # 3. Emotion Score (0 - 20)
        emotion_count = sum(1 for kw in self.EMOTIONAL_KEYWORDS if kw in full_transcript.lower())
        emotion_score = min(20, 5 + emotion_count * 4)

        # 4. Context Completeness Score (0 - 20)
        completeness_score = 15
        if any(opening_text.startswith(pr) for pr in self.AMBIGUOUS_PRONOUNS_START):
            completeness_score -= 7  # Penalize ambiguous starting context
        if re.search(r"^[A-Z0-9]", text_list[0]):
            completeness_score += 3
        completeness_score = max(0, min(20, completeness_score))

        # 5. Ending Quality Score (0 - 20)
        ending_score = 10
        if re.search(r"[.!?]$", text_list[-1]):
            ending_score += 10
        elif closing_text and not closing_text.endswith((",", "-", "...")):
            ending_score += 5
        ending_score = min(20, ending_score)

        # 6. Silence & Speech Density Penalty (0 to -20)
        spoken_dur = sum(max(0.1, float(s.get("end", 0)) - float(s.get("start", 0))) for s in segments_in_range)
        density_ratio = spoken_dur / max(1.0, duration)
        
        silence_penalty = 0
        if density_ratio < 0.65:
            silence_penalty = -15
        elif density_ratio < 0.75:
            silence_penalty = -8

        # 7. Duration Target Penalty/Bonus
        dur_diff = abs(duration - target_duration)
        dur_penalty = 0
        if dur_diff > 10.0:
            dur_penalty = -int(dur_diff - 10.0)

        # Calculate Total Score (0 - 100)
        raw_total = (
            hook_score + value_score + emotion_score +
            completeness_score + ending_score + silence_penalty + dur_penalty
        )
        total_score = min(99, max(25, raw_total))

        score_breakdown = {
            "hook_score": hook_score,
            "value_score": value_score,
            "emotion_score": emotion_score,
            "completeness_score": completeness_score,
            "ending_score": ending_score,
            "silence_penalty": silence_penalty
        }

        # Human-Readable Hook & Reason & Category
        hook_text = text_list[0][:70] + ("..." if len(text_list[0]) > 70 else "")
        category = self._determine_category(full_transcript)

        reasons = []
        if hook_score >= 15:
            reasons.append("Strong hook opening")
        if value_score >= 14:
            reasons.append("High educational & practical value")
        if emotion_score >= 14:
            reasons.append("Strong emotional resonance")
        if ending_score >= 15:
            reasons.append("Clean complete takeaway ending")
        if not reasons:
            reasons.append("Balanced speech density and duration match")

        reason_str = ". ".join(reasons) + "."
        return total_score, score_breakdown, hook_text, reason_str, category, full_transcript

    def analyze_transcript(
        self,
        master_transcript: Dict[str, Any],
        target_duration: int = 60,
        max_clips: int = 5
    ) -> List[Dict[str, Any]]:
        segments = master_transcript.get("segments", []) if master_transcript else []
        if not segments:
            return []

        min_dur = max(15.0, target_duration * 0.75)
        max_dur = min(95.0, target_duration * 1.25)

        n_segs = len(segments)
        raw_candidates = []

        # Sliding window over master transcript segments
        for i in range(n_segs):
            seg_i_start = float(segments[i].get("start", 0.0))

            accumulated_segs = []
            for j in range(i, n_segs):
                seg_j_end = float(segments[j].get("end", 0.0))
                dur = seg_j_end - seg_i_start
                accumulated_segs.append(segments[j])

                if dur >= min_dur:
                    if dur <= max_dur:
                        score, breakdown, hook, reason, category, text_snippet = self._score_candidate_window(
                            seg_i_start, seg_j_end, accumulated_segs, target_duration
                        )
                        raw_candidates.append({
                            "start": round(seg_i_start, 2),
                            "end": round(seg_j_end, 2),
                            "duration": round(dur, 2),
                            "score": score,
                            "score_breakdown": breakdown,
                            "hook": hook,
                            "reason": reason,
                            "category": category,
                            "transcript": text_snippet
                        })
                    else:
                        break

        if not raw_candidates:
            return []

        # Sort candidates by total score descending
        raw_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Deduplication using Non-Maximum Suppression (Max 30% overlap allowed)
        selected_candidates = []
        for cand in raw_candidates:
            c_start = cand["start"]
            c_end = cand["end"]

            overlaps = False
            for sel in selected_candidates:
                s_start = sel["start"]
                s_end = sel["end"]
                intersection = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                min_len = min(cand["duration"], sel["duration"])
                if (intersection / max(1.0, min_len)) > 0.30:
                    overlaps = True
                    break

            if not overlaps:
                selected_candidates.append(cand)
                if len(selected_candidates) >= max_clips:
                    break

        # Sort selected candidates chronologically
        selected_candidates.sort(key=lambda x: x["start"])
        return selected_candidates


# Default analyzer instance
clip_analysis_service = LocalHeuristicClipAnalyzer()

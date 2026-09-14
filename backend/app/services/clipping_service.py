import re
from typing import List, Tuple, Dict, Any, Optional

class ClipStrategy:
    def generate_clip_boundaries(
        self,
        total_duration: float,
        requested_duration: int,
        master_transcript: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

class FixedDurationClipStrategy(ClipStrategy):
    def generate_clip_boundaries(
        self,
        total_duration: float,
        requested_duration: int,
        master_transcript: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        candidates = []
        if total_duration <= 0:
            return candidates
        
        if total_duration <= requested_duration + 2.0:
            return [{
                "start": 0.0,
                "end": round(total_duration, 2),
                "duration": round(total_duration, 2),
                "score": 75,
                "hook": "Full Video Clip",
                "reason": "Video is shorter than requested duration target.",
                "transcript": ""
            }]
        
        curr_start = 0.0
        step = float(requested_duration)
        
        while curr_start < total_duration:
            curr_end = min(curr_start + step, total_duration)
            if (curr_end - curr_start) < 5.0 and len(candidates) > 0:
                break
                
            dur = round(curr_end - curr_start, 2)
            candidates.append({
                "start": round(curr_start, 2),
                "end": round(curr_end, 2),
                "duration": dur,
                "score": 70,
                "hook": f"Clip starting at {round(curr_start, 1)}s",
                "reason": "Fixed duration window cut",
                "transcript": ""
            })
            curr_start += step
            
        return candidates


from app.services.clip_analysis_service import clip_analysis_service

class AIClipDiscoveryStrategy(ClipStrategy):
    """
    Phase 4, Phase 5 & Phase 6: AI-driven short discovery engine.
    Analyzes master transcript to find high-scoring moments near requested target duration
    with smart sentence boundaries, hook detection, and speech density checks.
    """

    def generate_clip_boundaries(
        self,
        total_duration: float,
        requested_duration: int,
        master_transcript: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if total_duration <= 0:
            return []

        if not master_transcript or not master_transcript.get("segments"):
            fixed_strat = FixedDurationClipStrategy()
            return fixed_strat.generate_clip_boundaries(total_duration, requested_duration)

        # Delegate to modular clip analysis service
        candidates = clip_analysis_service.analyze_transcript(
            master_transcript=master_transcript,
            target_duration=requested_duration,
            max_clips=8
        )

        if not candidates:
            fixed_strat = FixedDurationClipStrategy()
            return fixed_strat.generate_clip_boundaries(total_duration, requested_duration)

        return candidates


def assign_transcript_to_clip(
    master_segments: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float
) -> List[Dict[str, Any]]:
    """
    Maps master transcript segments and words into relative timestamps [0.0, clip_duration]
    for a specific clip boundary [clip_start, clip_end].
    """
    clip_captions = []
    
    for seg in master_segments:
        seg_start = float(seg.get("start", 0.0))
        seg_end = float(seg.get("end", 0.0))
        
        # Check if segment overlaps with [clip_start, clip_end]
        if seg_end <= clip_start or seg_start >= clip_end:
            continue
        
        rel_seg_start = max(0.0, seg_start - clip_start)
        rel_seg_end = min(clip_end - clip_start, seg_end - clip_start)
        
        # Filter and map words
        rel_words = []
        for w in seg.get("words", []):
            w_start = float(w.get("start", seg_start))
            w_end = float(w.get("end", seg_end))
            w_conf = float(w.get("confidence", 0.90))
            
            if w_end <= clip_start or w_start >= clip_end:
                continue
            
            rel_words.append({
                "word": w.get("word", ""),
                "text": w.get("text", w.get("word", "")),
                "start": round(max(0.0, w_start - clip_start), 2),
                "end": round(min(clip_end - clip_start, w_end - clip_start), 2),
                "confidence": round(w_conf, 2)
            })
            
        if rel_words or seg.get("text", "").strip():
            clip_captions.append({
                "start": round(rel_seg_start, 2),
                "end": round(rel_seg_end, 2),
                "text": seg.get("text", "").strip(),
                "words": rel_words
            })
            
    return clip_captions

clipping_service = AIClipDiscoveryStrategy()


from typing import List, Tuple, Dict, Any

class ClipStrategy:
    def generate_clip_boundaries(self, total_duration: float, requested_duration: int) -> List[Tuple[float, float]]:
        raise NotImplementedError

class FixedDurationClipStrategy(ClipStrategy):
    def generate_clip_boundaries(self, total_duration: float, requested_duration: int) -> List[Tuple[float, float]]:
        boundaries = []
        if total_duration <= 0:
            return boundaries
        
        # If video is shorter than or equal to requested duration
        if total_duration <= requested_duration + 2.0:  # small grace margin
            return [(0.0, round(total_duration, 2))]
        
        curr_start = 0.0
        step = float(requested_duration)
        
        while curr_start < total_duration:
            curr_end = min(curr_start + step, total_duration)
            
            # Skip trailing tiny fragment under 5 seconds unless it's the only clip
            if (curr_end - curr_start) < 5.0 and len(boundaries) > 0:
                break
                
            boundaries.append((round(curr_start, 2), round(curr_end, 2)))
            curr_start += step
            
        return boundaries


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
            
            if w_end <= clip_start or w_start >= clip_end:
                continue
            
            rel_words.append({
                "word": w.get("word", ""),
                "text": w.get("text", w.get("word", "")),
                "start": round(max(0.0, w_start - clip_start), 2),
                "end": round(min(clip_end - clip_start, w_end - clip_start), 2)
            })
            
        if rel_words or seg.get("text", "").strip():
            clip_captions.append({
                "start": round(rel_seg_start, 2),
                "end": round(rel_seg_end, 2),
                "text": seg.get("text", "").strip(),
                "words": rel_words
            })
            
    return clip_captions

clipping_service = FixedDurationClipStrategy()

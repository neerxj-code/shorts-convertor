import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

class CaptionService:
    def __init__(self):
        pass

    def chunk_captions(self, captions_data: List[Dict[str, Any]], max_words_per_line: int = 4) -> List[Dict[str, Any]]:
        """
        Chunks transcript segments into short, punchy 2-5 word social media caption blocks
        with word-level timestamp alignment.
        """
        chunked = []
        for cap in captions_data:
            words = cap.get("words", [])
            if not words:
                text = cap.get("text", "").strip()
                if text:
                    tokens = text.split()
                    seg_start = float(cap.get("start", 0.0))
                    seg_end = float(cap.get("end", 0.0))
                    dur = max(0.1, seg_end - seg_start) / max(1, len(tokens))
                    curr = seg_start
                    for i in range(0, len(tokens), max_words_per_line):
                        group = tokens[i:i + max_words_per_line]
                        c_start = curr
                        c_end = min(seg_end, curr + len(group) * dur)
                        w_list = [{"word": t, "text": t, "start": round(c_start + j*dur, 2), "end": round(c_start + (j+1)*dur, 2)} for j, t in enumerate(group)]
                        chunked.append({
                            "start": round(c_start, 2),
                            "end": round(c_end, 2),
                            "text": " ".join(group),
                            "words": w_list
                        })
                        curr = c_end
                continue

            # We have word timestamps
            for i in range(0, len(words), max_words_per_line):
                group = words[i:i + max_words_per_line]
                c_start = group[0]["start"]
                c_end = group[-1]["end"]
                group_text = " ".join([w.get("word") or w.get("text", "") for w in group])
                chunked.append({
                    "start": round(c_start, 2),
                    "end": round(c_end, 2),
                    "text": group_text,
                    "words": group
                })

        return chunked

    def _sanitize_ass_text(self, text: str) -> str:
        """Escapes ASS special characters to prevent subtitle formatting syntax errors"""
        if not text:
            return ""
        return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

    def generate_ass_subtitle_file(
        self,
        captions: List[Dict[str, Any]],
        output_ass_path: str,
        style_preset: str = "KARAOKE",
        position: str = "BOTTOM",
        video_width: int = 1080,
        video_height: int = 1920
    ) -> bool:
        """
        Generates an Advanced SubStation Alpha (.ass) subtitle file supporting animated word highlights,
        positioning (Top, Center, Bottom), and custom typography.
        """
        style_preset = (style_preset or "KARAOKE").upper()
        position = (position or "BOTTOM").upper()

        # ASS alignment: 2 = bottom-center, 5 = center, 8 = top-center
        alignment = 2
        margin_v = 140
        if position == "TOP":
            alignment = 8
            margin_v = 160
        elif position == "CENTER":
            alignment = 5
            margin_v = 0

        # Colors in ASS format (&HBBGGRR& or &HAABBGGRR&)
        # Default: Primary White (&H00FFFFFF), Outline Black (&H00000000), Highlight Yellow (&H0000FFFF)
        primary_color = "&H00FFFFFF"
        secondary_color = "&H0000FFFF"  # Highlight color (yellow)
        outline_color = "&H00000000"
        back_color = "&H80000000"
        font_name = "Arial"
        font_size = 64
        bold = 1
        outline = 3
        shadow = 2

        if style_preset == "CLASSIC":
            font_size = 56
            bold = 0
            shadow = 2
            secondary_color = "&H00FFFFFF"
        elif style_preset == "POP":
            font_size = 72
            secondary_color = "&H0000E6FF" # Bright orange/gold
            outline = 4
        elif style_preset == "KARAOKE":
            font_size = 68
            primary_color = "&H00D0D0D0" # Dim white/grey for unread words
            secondary_color = "&H0000FFFF" # Cyan/Yellow for active word
            outline = 4
        elif style_preset == "BOUNCE":
            font_size = 66
            secondary_color = "&H0000FF7F" # Spring green
            outline = 4
        elif style_preset == "MINIMAL":
            font_size = 48
            bold = 0
            outline = 2
            shadow = 0
            primary_color = "&H00F0F0F0"
        elif style_preset == "BOLD":
            font_size = 76
            bold = 1
            outline = 5
            shadow = 4
            primary_color = "&H00FFFFFF"
            secondary_color = "&H0000A5FF" # Vibrant orange

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortifyDefault,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{back_color},{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        
        # Format time to ASS format: H:MM:SS.cs
        def format_ass_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            cs = int(round((seconds - int(seconds)) * 100))
            if cs >= 100:
                cs = 99
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        chunked_caps = self.chunk_captions(captions, max_words_per_line=4)

        for cap in chunked_caps:
            start_str = format_ass_time(cap["start"])
            end_str = format_ass_time(cap["end"])
            words = cap.get("words", [])

            if style_preset in ["KARAOKE", "POP", "BOUNCE"] and words:
                # Word-level karaoke effect using ASS \k or \kf tags
                line_text = ""
                for w in words:
                    raw_w = w.get("word") or w.get("text", "")
                    clean_w = self._sanitize_ass_text(raw_w)
                    w_dur_cs = max(5, int(round((w["end"] - w["start"]) * 100)))
                    if style_preset == "KARAOKE":
                        # \k<duration_cs> highlights text progressively
                        line_text += f"{{\\k{w_dur_cs}}}{clean_w} "
                    else:
                        line_text += f"{clean_w} "
                line_text = line_text.strip()
            else:
                line_text = self._sanitize_ass_text(cap.get("text", "").strip())

            if line_text:
                events.append(f"Dialogue: 0,{start_str},{end_str},ShortifyDefault,,0,0,0,,{line_text}")

        content = header + "\n".join(events) + "\n"
        
        os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(content)

        return os.path.exists(output_ass_path)

caption_service = CaptionService()

"""Shared helpers: transcript loading and the DaVinci Resolve connection."""
import json
import os
import re
import sys
from pathlib import Path

TRANSCRIPT_EXTS = (".srt", ".json")


# --- transcripts ------------------------------------------------------------------------------

def _srt_time(ts):
    h, m, rest = ts.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def parse_srt(text):
    segments = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if "-->" in line:
                start, end = line.split("-->")
                body = " ".join(lines[i + 1:]).strip()
                if body:
                    segments.append((_srt_time(start), _srt_time(end.split()[0]), body))
                break
    return segments


def parse_whisper_json(text):
    data = json.loads(text)
    return [(s["start"], s["end"], s["text"].strip()) for s in data["segments"] if s["text"].strip()]


def load_transcript(path):
    path = str(path)
    text = Path(path).read_text(encoding="utf-8")
    return parse_whisper_json(text) if path.lower().endswith(".json") else parse_srt(text)


def find_transcript(media):
    """The transcript is expected next to the video with the same name: day1.mp4 -> day1.srt."""
    for ext in TRANSCRIPT_EXTS:
        candidate = Path(media).with_suffix(ext)
        if candidate.exists():
            return candidate
    return None


def hms(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


# --- DaVinci Resolve --------------------------------------------------------------------------

# Default macOS locations of Resolve's scripting module and library.
MAC_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
MAC_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"


def connect_resolve():
    os.environ.setdefault("RESOLVE_SCRIPT_API", MAC_API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", MAC_LIB)
    sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        sys.exit("Couldn't import DaVinciResolveScript. Check RESOLVE_SCRIPT_API (see README).")
    resolve = dvr.scriptapp("Resolve")
    if resolve is None:
        sys.exit("Couldn't reach Resolve. Is Resolve Studio open, with Preferences > System > "
                 "General > External scripting using set to Local?")
    return resolve

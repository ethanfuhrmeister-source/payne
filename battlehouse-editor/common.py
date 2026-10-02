"""Shared helpers: transcript loading and the DaVinci Resolve connection."""
import json
import os
import re
import sys
from pathlib import Path

TRANSCRIPT_EXTS = (".srt", ".json")
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"


# --- shared Google Drive folder ---------------------------------------------------------------
# Every editor's Mac mounts the shared Drive at a different path, so story.json stores footage
# paths *relative to the Drive folder* and each Mac resolves them with its own config.json.

def drive_folder():
    if CONFIG.exists():
        folder = json.loads(CONFIG.read_text()).get("drive_folder")
        if folder and Path(folder).expanduser().is_dir():
            return Path(folder).expanduser()
    return None


def bible_path():
    """The shared bible in Drive wins, so every editor works from the same cast/storylines."""
    drive = drive_folder()
    if drive and (drive / "bible.md").exists():
        return drive / "bible.md"
    return HERE / "story" / "bible.md"


def to_portable(path):
    drive = drive_folder()
    path = Path(path).resolve()
    if drive:
        try:
            return str(path.relative_to(drive.resolve()))
        except ValueError:
            pass
    return str(path)


def find_media(stored):
    """Turn a stored footage path back into a real file on this Mac."""
    p = Path(stored).expanduser()
    if p.is_absolute() and p.exists():
        return str(p)
    drive = drive_folder()
    if drive:
        if (drive / stored).exists():
            return str(drive / stored)
        footage = drive / "Footage" if (drive / "Footage").is_dir() else drive
        for root, _, files in os.walk(footage):  # fallback: same file name anywhere in Footage
            if p.name in files:
                return os.path.join(root, p.name)
    return str(p)


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


def config_value(key, default=None):
    if CONFIG.exists():
        return json.loads(CONFIG.read_text()).get(key, default)
    return default


def connect_resolve(quiet=False):
    """quiet=True (background mode): return None instead of exiting when Resolve isn't open."""
    # Launched from Resolve's Workspace > Scripts menu: Resolve hands us the app directly.
    import __main__
    for name in ("resolve", "bmd"):
        app = getattr(__main__, name, None)
        if app is not None:
            return app if name == "resolve" else app.scriptapp("Resolve")
    os.environ.setdefault("RESOLVE_SCRIPT_API", MAC_API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", MAC_LIB)
    sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        sys.exit("Couldn't import DaVinciResolveScript. Check RESOLVE_SCRIPT_API (see README).")
    resolve = dvr.scriptapp("Resolve")
    if resolve is None and quiet:
        return None
    if resolve is None:
        sys.exit("Couldn't reach Resolve. Is Resolve Studio open, with Preferences > System > "
                 "General > External scripting using set to Local?")
    return resolve

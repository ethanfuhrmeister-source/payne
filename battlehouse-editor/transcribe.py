#!/usr/bin/env python3
"""Transcribe every video in an episode folder that doesn't have a transcript yet.

Writes day3_main.srt next to day3_main.mp4, which is what paper_edit.py expects. Runs locally
with Whisper: mlx-whisper on Apple Silicon Macs (fast), openai-whisper elsewhere. Cast names
from the story bible are given to Whisper so handles like "Tommy2Coats" are spelled right.

    python3 transcribe.py "<Drive>/Footage/Episode 3"
"""
import argparse
import re
import sys
import time
from pathlib import Path

from common import bible_path, find_transcript, hms

VIDEO_EXTS = {".mp4", ".mov", ".mxf", ".mkv", ".m4v"}
MLX_MODEL = "mlx-community/whisper-large-v3-turbo"
OPENAI_MODEL = "turbo"


def cast_prompt():
    """'Brandon Gomes, Coach K, Tommy2Coats, ...' - names Whisper should expect to hear."""
    path = bible_path()
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    names = re.findall(r"^- \*\*(.+?)\*\*", text, flags=re.M)  # hosts
    for row in re.findall(r"^\| ([^|]+?) \|", text, flags=re.M):
        if row.strip() and not row.startswith(("Name", "Storyline", "-")):
            names.append(row.strip())
    names = list(dict.fromkeys(n for n in names if n))
    return ("BattleHouse Live. " + ", ".join(names) + ".") if names else None


def load_engine():
    try:
        import mlx_whisper
        return "mlx-whisper", lambda path, prompt: mlx_whisper.transcribe(
            str(path), path_or_hf_repo=MLX_MODEL, initial_prompt=prompt, language="en")
    except ImportError:
        pass
    try:
        import whisper
    except ImportError:
        sys.exit("No Whisper installed. Run install.command again (it installs mlx-whisper).")
    model = whisper.load_model(OPENAI_MODEL)
    return "openai-whisper", lambda path, prompt: model.transcribe(
        str(path), initial_prompt=prompt, language="en")


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def to_srt(segments):
    blocks = []
    for i, seg in enumerate((s for s in segments if s["text"].strip()), 1):
        blocks.append(f"{i}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n{seg['text'].strip()}\n")
    return "\n".join(blocks)


def videos_needing_transcripts(paths):
    found = []
    for p in map(lambda x: Path(x).expanduser(), paths):
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() in VIDEO_EXTS) if p.is_dir() else [p]
        found += [f for f in files if not find_transcript(f)]
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="episode folders or video files")
    args = ap.parse_args()

    todo = videos_needing_transcripts(args.paths)
    if not todo:
        print("All videos already have transcripts.")
        return
    name, transcribe = load_engine()
    prompt = cast_prompt()
    print(f"Transcribing {len(todo)} video(s) with {name}. Long streams take a while - "
          "leave this window open.")
    for n, video in enumerate(todo, 1):
        print(f"  [{n}/{len(todo)}] {video.name} ...", flush=True)
        started = time.time()
        try:
            result = transcribe(video, prompt)
        except Exception as e:  # one bad file shouldn't stop the rest
            print(f"      failed: {e}")
            continue
        srt = video.with_suffix(".srt")
        tmp = srt.with_suffix(".srt.part")  # never leave a half-written transcript behind
        tmp.write_text(to_srt(result["segments"]), encoding="utf-8")
        tmp.rename(srt)
        length = result["segments"][-1]["end"] if result["segments"] else 0
        print(f"      done: {hms(length)} of audio in {hms(time.time() - started)} -> {srt.name}")


if __name__ == "__main__":
    main()

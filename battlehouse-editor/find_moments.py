#!/usr/bin/env python3
"""Find the best clip-worthy moments in a BattleHouse Live stream transcript.

Reads a timestamped transcript (.srt from Resolve/Whisper, or Whisper .json), asks Claude to
pick clips using the style guide in skill/SKILL.md, and writes clips.json for
build_timelines.py.

    python3 find_moments.py stream.srt --media "/Volumes/Footage/stream.mp4" -o clips.json

No API key? Use --prompt-only to write a prompt you can paste into the Claude app, then save
Claude's JSON reply as clips.json.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STYLE_GUIDE = HERE / "skill" / "SKILL.md"
MODEL = "claude-opus-5-5"


# --- transcript parsing -----------------------------------------------------------------------

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
    text = Path(path).read_text(encoding="utf-8")
    segments = parse_whisper_json(text) if path.lower().endswith(".json") else parse_srt(text)
    if not segments:
        sys.exit(f"No transcript segments found in {path}")
    return segments


def hms(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def format_transcript(segments):
    # Second-level timestamps on every line keep the prompt compact but let Claude cite times.
    return "\n".join(f"[{hms(s)} | {s:.1f}s] {t}" for s, _, t in segments)


# --- prompt -----------------------------------------------------------------------------------

INSTRUCTIONS = """You are a short-form editor for BattleHouse Live. Using the style guide above,
pick the {count} best clips from the stream transcript below.

Rules:
- start_seconds / end_seconds are absolute times in the source video, taken from the
  transcript's [.. | N.Ns] stamps. Respect the clip length and "start late / end on the
  reaction" rules from the style guide.
- Clips must not overlap. Order them best first; score is 1-10 for how well it will perform.
- notes[].at_seconds are absolute source times inside the clip, for edit instructions
  (punch-in, SFX, bleep, cold-open, music drop).
- Only use names that appear in the transcript. If a speaker is unknown, describe them.
- If the transcript has fewer than {count} genuinely good moments, return fewer.
"""

JSON_SHAPE = """Reply with JSON only, in this shape:
{"clips": [{"title": "", "start_seconds": 0.0, "end_seconds": 0.0, "score": 0, "why": "",
  "hook_text": "", "post_title": "", "post_caption": "", "hashtags": [""],
  "notes": [{"at_seconds": 0.0, "text": ""}]}]}"""


def build_prompt(segments, count):
    return (INSTRUCTIONS.format(count=count)
            + "\n<transcript>\n" + format_transcript(segments) + "\n</transcript>")


# --- Claude call ------------------------------------------------------------------------------

def ask_claude(style_guide, prompt):
    from typing import List

    import anthropic
    from pydantic import BaseModel

    class Note(BaseModel):
        at_seconds: float
        text: str

    class Clip(BaseModel):
        title: str
        start_seconds: float
        end_seconds: float
        score: int
        why: str
        hook_text: str
        post_title: str
        post_caption: str
        hashtags: List[str]
        notes: List[Note]

    class ClipPlan(BaseModel):
        clips: List[Clip]

    client = anthropic.Anthropic()
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        # Re-runs on another model automatically if the request is declined.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=style_guide,
        messages=[{"role": "user", "content": prompt}],
        output_format=ClipPlan,
    )
    if response.stop_reason == "refusal":
        sys.exit("Claude declined this transcript; try --prompt-only and review it manually.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        sys.exit("Claude's reply was cut off; try a smaller --count.")
    return response.parsed_output.model_dump()["clips"]


# --- validation -------------------------------------------------------------------------------

def clean_clips(clips, duration):
    """Drop impossible clips, clamp to the video, remove overlaps (keeping the higher-ranked)."""
    kept = []
    for c in clips:
        c["start_seconds"] = max(0.0, float(c["start_seconds"]))
        c["end_seconds"] = min(duration, float(c["end_seconds"]))
        length = c["end_seconds"] - c["start_seconds"]
        if length < 5:
            print(f"  skipping '{c['title']}': only {length:.1f}s long", file=sys.stderr)
            continue
        if any(c["start_seconds"] < k["end_seconds"] and k["start_seconds"] < c["end_seconds"] for k in kept):
            print(f"  skipping '{c['title']}': overlaps a better clip", file=sys.stderr)
            continue
        c["notes"] = [n for n in c.get("notes", [])
                      if c["start_seconds"] <= n["at_seconds"] <= c["end_seconds"]]
        kept.append(c)
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", help=".srt or Whisper .json transcript of the stream")
    ap.add_argument("--media", help="path to the stream video on your Mac (stored in clips.json)")
    ap.add_argument("--count", type=int, default=10, help="how many clips to ask for (default 10)")
    ap.add_argument("-o", "--out", default="clips.json")
    ap.add_argument("--prompt-only", action="store_true",
                    help="write prompt.txt to paste into the Claude app instead of calling the API")
    args = ap.parse_args()

    segments = load_transcript(args.transcript)
    style_guide = STYLE_GUIDE.read_text(encoding="utf-8")
    prompt = build_prompt(segments, args.count)

    if args.prompt_only:
        out = Path("prompt.txt")
        out.write_text(style_guide + "\n\n" + prompt + "\n\n" + JSON_SHAPE + "\n", encoding="utf-8")
        print(f"Wrote {out}. Paste it into Claude and save the JSON reply as {args.out}.")
        print('Then add "source_media": "/path/to/stream.mp4" to that file (or pass --media to build_timelines.py).')
        return

    print(f"Sending {len(segments)} transcript lines to Claude...")
    clips = clean_clips(ask_claude(style_guide, prompt), duration=segments[-1][1])
    plan = {"source_media": args.media, "transcript": str(Path(args.transcript).resolve()), "clips": clips}
    Path(args.out).write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWrote {len(clips)} clips to {args.out}:")
    for i, c in enumerate(clips, 1):
        print(f"  {i:2d}. [{hms(c['start_seconds'])}-{hms(c['end_seconds'])}] "
              f"({c['score']}/10) {c['hook_text']}")


if __name__ == "__main__":
    main()

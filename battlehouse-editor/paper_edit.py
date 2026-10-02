#!/usr/bin/env python3
"""Build a story paper edit for a BattleHouse Live episode from footage transcripts.

Give it the video files; each needs a transcript next to it with the same name
(day3_main.mp4 -> day3_main.srt). Claude reads all of it plus the story bible, finds the
storylines, and writes:

  story.json        – acts > beats > shots with source timecodes (for assemble.py)
  story.md          – the same paper edit, readable, to review with producers
  bible_updates.md  – suggested updates for story/bible.md

    python3 paper_edit.py /Volumes/Footage/day3/*.mp4 --brief "Episode 3: the first elimination" --minutes 20

No API key? --prompt-only writes prompt.txt to paste into the Claude app; then
--import-reply reply.json turns Claude's answer into the same three files.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Literal

from common import bible_path, config_value, drive_folder, find_transcript, hms, load_transcript, to_portable

HERE = Path(__file__).resolve().parent
STYLE_GUIDE = HERE / "skill" / "SKILL.md"
MODEL = config_value("model", "claude-opus-5-5")  # override per Mac in config.json


# --- footage ----------------------------------------------------------------------------------

VIDEO_EXTS = {".mp4", ".mov", ".mxf", ".mkv", ".m4v"}


def expand_media(paths):
    """Accept video files or whole folders (every video in the folder that has a transcript)."""
    files = []
    for p in map(lambda x: Path(x).expanduser(), paths):
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.suffix.lower() in VIDEO_EXTS and find_transcript(f))
        else:
            files.append(p)
    if not files:
        sys.exit("No videos with matching transcripts found.")
    return files


def load_sources(media_files):
    sources = {}
    for media in expand_media(media_files):
        media = Path(media).expanduser().resolve()
        transcript = find_transcript(media)
        if not transcript:
            sys.exit(f"No transcript for {media.name}: expected {media.with_suffix('.srt').name}")
        segments = load_transcript(transcript)
        if not segments:
            sys.exit(f"Transcript {transcript.name} is empty")
        sid = media.stem
        if sid in sources:
            sys.exit(f"Two files are named {sid}; rename one so every source is unique.")
        sources[sid] = {"media": str(media), "segments": segments, "duration": segments[-1][1]}
    return sources


def format_footage(sources):
    parts = []
    for sid, src in sources.items():
        lines = "\n".join(f"[{hms(s)} | {s:.1f}s] {t}" for s, _, t in src["segments"])
        parts.append(f'<source id="{sid}" length="{hms(src["duration"])}">\n{lines}\n</source>')
    return "\n\n".join(parts)


# --- prompt -----------------------------------------------------------------------------------

INSTRUCTIONS = """Build the paper edit for this BattleHouse Live episode, following the story
editing guide in the system prompt and staying consistent with the story bible.

Brief from the editor: {brief}
Target running time: about {minutes} minutes.

Rules:
- Every shot references a source id below and absolute start/end seconds from that source's
  [.. | N.Ns] stamps. Trim to the line you want; don't include dead air.
- quote = the exact words spoken in the shot (empty for b-roll / reaction-only shots).
- The total of all shots should land near the target running time.
- Shots can be out of chronological order for story (cold open, flash-forwards), but never
  change what someone meant. If a trim changes meaning, don't use it.
- Use a name only if it's in the bible or clearly identified in the footage; otherwise
  describe the person ("guy in the red hoodie") and add it to coverage_gaps.

<story_bible>
{bible}
</story_bible>

<footage>
{footage}
</footage>
"""

JSON_SHAPE = """Reply with JSON only, in this shape:
{"title": "", "logline": "", "storylines": [{"label": "A", "name": "", "summary": ""}],
 "acts": [{"name": "Cold Open", "beats": [{"name": "", "storyline": "A", "purpose": "",
   "music": "", "shots": [{"source": "", "start_seconds": 0.0, "end_seconds": 0.0,
   "kind": "dialogue", "speaker": "", "quote": "", "note": ""}]}]}],
 "coverage_gaps": [""], "bible_updates": ""}
kind is one of: dialogue, confessional, host, reaction, broll, action"""


def build_prompt(sources, brief, minutes):
    bible = bible_path().read_text(encoding="utf-8") if bible_path().exists() else "(no bible yet)"
    return INSTRUCTIONS.format(brief=brief or "(none - find the strongest story)", minutes=minutes,
                               bible=bible, footage=format_footage(sources))


# --- Claude call ------------------------------------------------------------------------------

def ask_claude(style_guide, prompt):
    import anthropic
    from pydantic import BaseModel

    class Shot(BaseModel):
        source: str
        start_seconds: float
        end_seconds: float
        kind: Literal["dialogue", "confessional", "host", "reaction", "broll", "action"]
        speaker: str
        quote: str
        note: str

    class Beat(BaseModel):
        name: str
        storyline: str
        purpose: str
        music: str
        shots: List[Shot]

    class Act(BaseModel):
        name: str
        beats: List[Beat]

    class Storyline(BaseModel):
        label: str
        name: str
        summary: str

    class Story(BaseModel):
        title: str
        logline: str
        storylines: List[Storyline]
        acts: List[Act]
        coverage_gaps: List[str]
        bible_updates: str

    client = anthropic.Anthropic()
    # Streaming: hours of footage in and a long paper edit out can take several minutes.
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        # Re-runs on another model automatically if the request is declined.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=style_guide,
        messages=[{"role": "user", "content": prompt}],
        output_format=Story,
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "refusal":
        sys.exit("Claude declined this footage; try --prompt-only and review it manually.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        sys.exit("Claude's reply was cut off; try fewer files or a shorter target.")
    return response.parsed_output.model_dump()


# --- validation & output ----------------------------------------------------------------------

def clean_story(story, sources):
    """Drop shots that point at unknown sources or impossible times; clamp the rest."""
    for act in story["acts"]:
        for beat in act["beats"]:
            kept = []
            for shot in beat["shots"]:
                src = sources.get(shot["source"])
                if not src:
                    print(f"  dropping shot from unknown source '{shot['source']}'", file=sys.stderr)
                    continue
                shot["start_seconds"] = max(0.0, float(shot["start_seconds"]))
                shot["end_seconds"] = min(src["duration"], float(shot["end_seconds"]))
                if shot["end_seconds"] - shot["start_seconds"] < 0.5:
                    print(f"  dropping too-short shot in '{beat['name']}'", file=sys.stderr)
                    continue
                kept.append(shot)
            beat["shots"] = kept
        act["beats"] = [b for b in act["beats"] if b["shots"]]
    story["acts"] = [a for a in story["acts"] if a["beats"]]
    story["sources"] = {sid: to_portable(src["media"]) for sid, src in sources.items()}
    return story


def runtime(items):
    return sum(s["end_seconds"] - s["start_seconds"] for s in items)


def write_markdown(story, path):
    shots = lambda a: [s for b in a["beats"] for s in b["shots"]]
    total = sum(runtime(shots(a)) for a in story["acts"])
    out = [f"# {story['title']}", "", f"_{story['logline']}_", "",
           f"**Rough running time:** {hms(total)}", "", "## Storylines", ""]
    out += [f"- **{s['label']}** – {s['name']}: {s['summary']}" for s in story["storylines"]]
    for act in story["acts"]:
        out += ["", f"## {act['name']}  ({hms(runtime(shots(act)))})"]
        for beat in act["beats"]:
            out += ["", f"### {beat['name']}  [{beat['storyline']}]", f"_{beat['purpose']}_"]
            if beat["music"]:
                out.append(f"Music: {beat['music']}")
            out += ["", "| Source | In | Out | Kind | Who | Line / note |", "|---|---|---|---|---|---|"]
            for s in beat["shots"]:
                line = f"\"{s['quote']}\"" if s["quote"] else ""
                if s["note"]:
                    line += f" _({s['note']})_"
                out.append(f"| {s['source']} | {hms(s['start_seconds'])} | {hms(s['end_seconds'])} "
                           f"| {s['kind']} | {s['speaker']} | {line.replace('|', '/')} |")
    out += ["", "## Coverage gaps", ""] + [f"- {g}" for g in story["coverage_gaps"] or ["(none)"]]
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("media", nargs="+",
                    help="video files or folders; each video needs a matching .srt/.json transcript")
    ap.add_argument("--brief", default="", help="what this episode is / what to focus on")
    ap.add_argument("--minutes", type=int, default=20, help="target running time (default 20)")
    ap.add_argument("--out", help="folder for story.json / story.md "
                                  "(default: <Drive>/Paper Edits/<footage folder name>)")
    ap.add_argument("--prompt-only", action="store_true",
                    help="write prompt.txt to paste into the Claude app instead of calling the API")
    ap.add_argument("--import-reply", metavar="FILE",
                    help="use Claude's pasted JSON reply (from --prompt-only) instead of calling the API")
    args = ap.parse_args()

    sources = load_sources(args.media)
    style_guide = STYLE_GUIDE.read_text(encoding="utf-8")
    prompt = build_prompt(sources, args.brief, args.minutes)
    if args.out:
        out = Path(args.out).expanduser()
    else:
        first = Path(args.media[0]).expanduser()
        episode = (first if first.is_dir() else first.parent).name
        drive = drive_folder()
        out = (drive / "Paper Edits" / episode) if drive else Path(episode)
    out.mkdir(parents=True, exist_ok=True)

    if args.prompt_only:
        (out / "prompt.txt").write_text(style_guide + "\n\n" + prompt + "\n" + JSON_SHAPE + "\n",
                                        encoding="utf-8")
        print(f"Wrote {out / 'prompt.txt'}. Paste it into Claude, save the JSON reply as reply.json, "
              f"then re-run this command with --import-reply reply.json instead of --prompt-only.")
        return

    if args.import_reply:
        story = clean_story(json.loads(Path(args.import_reply).read_text(encoding="utf-8")), sources)
    else:
        words = sum(len(t.split()) for src in sources.values() for _, _, t in src["segments"])
        print(f"Sending {len(sources)} sources (~{words:,} words of transcript) to Claude. "
              "This can take a few minutes...")
        story = clean_story(ask_claude(style_guide, prompt), sources)

    (out / "story.json").write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
    total = write_markdown(story, out / "story.md")
    (out / "bible_updates.md").write_text(story.get("bible_updates", "") + "\n", encoding="utf-8")
    beats = sum(len(a["beats"]) for a in story["acts"])
    print(f"\n{story['title']}: {len(story['acts'])} acts, {beats} beats, ~{hms(total)} rough cut")
    print(f"Review {out / 'story.md'}, then run: python3 assemble.py {out / 'story.json'}")


if __name__ == "__main__":
    main()

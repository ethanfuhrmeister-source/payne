#!/usr/bin/env python3
"""Make a BattleHouse story from the media already in your open DaVinci Resolve project.

Standalone: needs only Resolve Studio (Preferences > System > General > External scripting
using: Local) and mlx-whisper (pip3 install mlx-whisper).

  python3 bh_resolve.py export
      Transcribes every clip in the open project's media pool (reusing any .srt already next
      to a file) and writes ~/Downloads/bh_media_transcripts.txt - send that file to Claude.

  python3 bh_resolve.py build story.json
      Builds Claude's paper edit as a new timeline in the open project, with act/beat,
      confessional, host and note markers. Never overwrites an existing timeline.
"""
import json
import os
import re
import sys
from pathlib import Path

OUT = Path.home() / "Downloads" / "bh_media_transcripts.txt"
FALLBACK_SRT_DIR = Path.home() / "Downloads" / "bh_transcripts"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
NAMES = ("BattleHouse Live. Brandon Gomes, Coach K, Amanda Frances, Ashwitdafin, Bethany Mals, "
         "Big Tim, Caleb_runkle, Charity, Cybertt2077, Drewfilmedit, Dreybaby, Gordo Loco, "
         "Gus Smyrnios, Im_loving_cj, JaeArsenal, Jay Borbon, Jessicadimon, John Conner, "
         "Kayceewins, King Quran, Luckless Holly, Madi Jo, Mikie, Monica Baez, Nigerian_nupe, "
         "Queen Cheryl, StillAngiie, Thecountryascornbread, Thedrezshow, Tommy2Coats, Wuanof1, "
         "Whitneywren1, Young_rum.")
MEDIA_EXTS = {".mp4", ".mov", ".mxf", ".mkv", ".m4v", ".m4a", ".wav", ".mp3", ".aac"}


# --- Resolve ----------------------------------------------------------------------------------

def connect():
    import __main__
    if getattr(__main__, "resolve", None):
        return __main__.resolve
    api = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    os.environ.setdefault("RESOLVE_SCRIPT_API", api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", "/Applications/DaVinci Resolve/DaVinci Resolve.app"
                          "/Contents/Libraries/Fusion/fusionscript.so")
    sys.path.append(os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules"))
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        sys.exit("Couldn't load Resolve's scripting module. Is DaVinci Resolve Studio installed?")
    resolve = dvr.scriptapp("Resolve")
    if not resolve:
        sys.exit("Couldn't reach Resolve. Open Resolve Studio and set Preferences > System > "
                 "General > External scripting using: Local, then try again.")
    return resolve


def current_project(resolve):
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        sys.exit("Open your project in Resolve first.")
    return project


def media_items(pool):
    """Every media pool clip that is a real audio/video file, in bin order."""
    found, seen = [], set()

    def walk(folder):
        for item in folder.GetClipList() or []:
            path = item.GetClipProperty("File Path") or ""
            if path and Path(path).suffix.lower() in MEDIA_EXTS and path not in seen:
                seen.add(path)
                found.append(item)
        for sub in folder.GetSubFolderList() or []:
            walk(sub)

    walk(pool.GetRootFolder())
    return found


# --- export -----------------------------------------------------------------------------------

def srt_time(sec):
    ms = int(round(sec * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def hms(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def parse_srt(text):
    segs = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if "-->" in line:
                a, b = line.split("-->")
                to_s = lambda t: (lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s))(
                    *t.strip().split()[0].replace(",", ".").split(":"))
                body = " ".join(lines[i + 1:]).strip()
                if body:
                    segs.append((to_s(a), to_s(b), body))
                break
    return segs


def transcript_for(path, whisper):
    """Reuse <file>.srt (next to the media or in ~/Downloads/bh_transcripts), else transcribe."""
    p = Path(path)
    candidates = [p.with_suffix(".srt"), FALLBACK_SRT_DIR / (p.stem + ".srt")]
    for c in candidates:
        if c.exists():
            return parse_srt(c.read_text(encoding="utf-8")), "existing"
    result = whisper(path)
    segs = [(s["start"], s["end"], s["text"].strip()) for s in result["segments"] if s["text"].strip()]
    srt = "\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n" for i, (a, b, t) in enumerate(segs, 1))
    for target in candidates:  # next to the media if that folder is writable
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(srt, encoding="utf-8")
            break
        except OSError:
            continue
    return segs, "transcribed"


def export(resolve):
    project = current_project(resolve)
    items = media_items(project.GetMediaPool())
    if not items:
        sys.exit("No audio/video files found in this project's media pool.")
    print(f"Project '{project.GetName()}': {len(items)} media file(s)")

    whisper_fn = None

    def whisper(path):
        nonlocal whisper_fn
        if whisper_fn is None:
            try:
                import mlx_whisper
            except ImportError:
                sys.exit("Whisper isn't installed. Run: pip3 install mlx-whisper")
            whisper_fn = lambda p: mlx_whisper.transcribe(p, path_or_hf_repo=WHISPER_MODEL,
                                                          language="en", initial_prompt=NAMES)
        return whisper_fn(path)

    sections, ids = [], set()
    for n, item in enumerate(items, 1):
        path = item.GetClipProperty("File Path")
        sid = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(path).stem)[:40] or "clip"
        base, k = sid, 2
        while sid in ids:
            sid, k = f"{base}_{k}", k + 1
        ids.add(sid)
        print(f"  [{n}/{len(items)}] {Path(path).name} ...", flush=True)
        try:
            segs, how = transcript_for(path, whisper)
        except Exception as e:
            print(f"      skipped: {e}")
            continue
        length = segs[-1][1] if segs else 0
        print(f"      {how}: {len(segs)} lines, {hms(length)}")
        lines = "\n".join(f"[{hms(a)} | {a:.1f}s] {t}" for a, _, t in segs) or "(no speech)"
        sections.append(f'<source id="{sid}" file="{path}" length="{hms(length)}" '
                        f'type="{item.GetClipProperty("Type")}">\n{lines}\n</source>')

    OUT.write_text(f"Resolve project: {project.GetName()}\n\n" + "\n\n".join(sections) + "\n",
                   encoding="utf-8")
    print(f"\nDone. Send this file to Claude:\n  {OUT}")


# --- build ------------------------------------------------------------------------------------

ACT_COLORS = ["Red", "Blue", "Cyan", "Pink", "Lavender", "Sand", "Mint", "Rose"]
KIND_MARKERS = {"confessional": ("Purple", "CONF"), "host": ("Green", "HOST"), "broll": ("Cream", "B-ROLL")}


def build(resolve, story_path):
    story = json.loads(Path(story_path).expanduser().read_text(encoding="utf-8"))
    project = current_project(resolve)
    pool = project.GetMediaPool()
    by_path = {i.GetClipProperty("File Path"): i for i in media_items(pool)}
    by_name = {Path(p).name: i for p, i in by_path.items()}

    items = {}
    for sid, path in story["sources"].items():
        item = by_path.get(path) or by_name.get(Path(path).name)
        if not item:
            sys.exit(f"'{Path(path).name}' isn't in this project's media pool any more.")
        items[sid] = item
    fps_of = {sid: float(i.GetClipProperty("FPS") or 30) for sid, i in items.items()}

    names = {project.GetTimelineByIndex(i).GetName() for i in range(1, project.GetTimelineCount() + 1)}
    base, n = f"BH Story - {story['title']}"[:60], 1
    while f"{base} v{n}" in names:
        n += 1
    tl = pool.CreateEmptyTimeline(f"{base} v{n}")
    if not tl:
        sys.exit("Resolve couldn't create the timeline.")
    project.SetCurrentTimeline(tl)
    tl_fps = float(tl.GetSetting("timelineFrameRate") or next(iter(fps_of.values())))
    tl_start = tl.GetStartFrame()
    print(f"Building '{tl.GetName()}' at {tl_fps:g} fps")

    used, placed, failed, position = set(), 0, 0, 0

    def marker(frame, color, name, note):
        while frame in used:
            frame += 1
        if tl.AddMarker(frame, color, name, note or "", 1):
            used.add(frame)

    for ai, act in enumerate(story["acts"]):
        color = ACT_COLORS[ai % len(ACT_COLORS)]
        for bi, beat in enumerate(act["beats"]):
            for si, shot in enumerate(beat["shots"]):
                sid = shot["source"]
                if sid not in items:
                    failed += 1
                    continue
                fps = fps_of[sid]
                a, b = round(shot["start_seconds"] * fps), round(shot["end_seconds"] * fps)
                appended = pool.AppendToTimeline([{"mediaPoolItem": items[sid], "startFrame": a, "endFrame": b - 1}])
                if not appended:
                    print(f"  ! couldn't place {sid} at {hms(shot['start_seconds'])}")
                    failed += 1
                    continue
                placed += 1
                try:
                    at = appended[0].GetStart() - tl_start
                except Exception:
                    at = position
                position = at + round((shot["end_seconds"] - shot["start_seconds"]) * tl_fps)
                if bi == 0 and si == 0:
                    marker(at, color, f"ACT: {act['name']}", "")
                if si == 0:
                    marker(at, color, beat["name"], "\n".join(filter(None, [
                        f"[{beat.get('storyline', '')}] {beat.get('purpose', '')}",
                        beat.get("music") and f"Music: {beat['music']}"])))
                if shot.get("kind") in KIND_MARKERS:
                    c, label = KIND_MARKERS[shot["kind"]]
                    marker(at, c, f"{label}: {shot.get('speaker', '')}".rstrip(": "), shot.get("quote", ""))
                if shot.get("note"):
                    marker(at, "Yellow", "NOTE", shot["note"])

    resolve.OpenPage("edit")
    print(f"Done: {placed} shots, {hms(position / tl_fps)}" + (f" ({failed} couldn't be placed)" if failed else ""))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "export":
        export(connect())
    elif len(sys.argv) >= 3 and sys.argv[1] == "build":
        build(connect(), sys.argv[2])
    else:
        sys.exit(__doc__)

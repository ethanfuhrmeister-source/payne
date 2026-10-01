#!/usr/bin/env python3
"""Build vertical BattleHouse clip timelines in DaVinci Resolve Studio from clips.json.

Run with Resolve Studio open and a project loaded:

    python3 build_timelines.py clips.json                 # build timelines + markers
    python3 build_timelines.py clips.json --queue "BH Vertical" --out ~/Renders/BattleHouse
                                                          # after editing: queue renders

Re-running is safe: timelines that already exist are left alone (your edits are kept).
--dry-run prints the plan without touching Resolve.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

BIN_NAME = "BattleHouse Clips"
WIDTH, HEIGHT = 1080, 1920

# Default macOS locations of Resolve's scripting module and library.
MAC_API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
MAC_LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"


def connect():
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


def slug(text, n=28):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:n] or "clip"


def timeline_name(i, clip):
    return f"BH_{i:02d}_{slug(clip['title'])}"


def load_plan(path, media_override):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    media = media_override or plan.get("source_media")
    if not media:
        sys.exit("No source video: pass --media or add \"source_media\" to clips.json.")
    clips = [c for c in plan["clips"] if float(c["end_seconds"]) > float(c["start_seconds"])]
    return os.path.expanduser(media), clips


# --- Resolve helpers --------------------------------------------------------------------------

def find_or_import(pool, media):
    def walk(folder):
        for item in folder.GetClipList() or []:
            if item.GetClipProperty("File Path") == media:
                return item
        for sub in folder.GetSubFolderList() or []:
            found = walk(sub)
            if found:
                return found
        return None

    item = walk(pool.GetRootFolder())
    if item:
        return item
    if not os.path.exists(media):
        sys.exit(f"Video not found: {media}")
    imported = pool.ImportMedia([media])
    if not imported:
        sys.exit(f"Resolve couldn't import {media}")
    return imported[0]


def existing_timelines(project):
    found = {}
    for i in range(1, project.GetTimelineCount() + 1):
        tl = project.GetTimelineByIndex(i)
        found[tl.GetName()] = tl
    return found


def get_bin(pool):
    root = pool.GetRootFolder()
    for sub in root.GetSubFolderList() or []:
        if sub.GetName() == BIN_NAME:
            return sub
    return pool.AddSubFolder(root, BIN_NAME)


def try_step(label, fn):
    """Run an optional step; Resolve API calls return False/None instead of raising."""
    try:
        ok = fn()
    except Exception as e:  # API surface varies slightly between Resolve versions
        ok, label = False, f"{label} ({e})"
    if not ok:
        print(f"    - couldn't {label}; do it by hand")
    return ok


def add_hook_title(tl, hook):
    tl.SetCurrentTimecode(tl.GetStartTimecode())
    title = tl.InsertFusionTitleIntoTimeline("Text+")
    if not title:
        return False
    tool = title.GetFusionCompByIndex(1).FindTool("Template")
    return bool(tool) and tool.SetInput("StyledText", hook) is not False


def build_clip(project, pool, media_item, fps, name, clip, args):
    tl = pool.CreateEmptyTimeline(name)
    if not tl:
        print(f"  ! couldn't create timeline {name}")
        return None
    project.SetCurrentTimeline(tl)

    # Vertical 9:16 timeline; a 16:9 stream gets centre-cropped to fill it.
    tl.SetSetting("useCustomSettings", "1")
    tl.SetSetting("timelineResolutionWidth", str(WIDTH))
    tl.SetSetting("timelineResolutionHeight", str(HEIGHT))
    tl.SetSetting("timelineInputResMismatchBehavior", "scaleToCrop")

    start = round(float(clip["start_seconds"]) * fps)
    end = round(float(clip["end_seconds"]) * fps)
    if not pool.AppendToTimeline([{"mediaPoolItem": media_item, "startFrame": start, "endFrame": end - 1}]):
        print(f"  ! couldn't place footage in {name}")
        return tl

    # Markers: hook + post copy at the top, the editor's notes where they happen.
    tl.AddMarker(0, "Red", "HOOK", clip.get("hook_text", ""), 1)
    post = "\n".join(filter(None, [clip.get("post_title"), clip.get("post_caption"),
                                   " ".join(clip.get("hashtags", [])), "Why: " + clip.get("why", "")]))
    tl.AddMarker(1, "Blue", "POST", post, 1)
    used = {0, 1}
    for note in clip.get("notes", []):
        frame = round((float(note["at_seconds"]) - float(clip["start_seconds"])) * fps)
        while frame in used:  # Resolve allows one marker per frame
            frame += 1
        if 0 <= frame < end - start:
            tl.AddMarker(frame, "Yellow", "EDIT", note["text"], 1)
            used.add(frame)

    if args.hook_titles and clip.get("hook_text"):
        try_step("add the hook Text+ title", lambda: add_hook_title(tl, clip["hook_text"]))
    if args.subtitles:
        try_step("auto-create subtitles", lambda: tl.CreateSubtitlesFromAudio({}))
    return tl


def queue_render(project, tl, name, args):
    project.SetCurrentTimeline(tl)
    if not project.LoadRenderPreset(args.queue):
        sys.exit(f"Render preset '{args.queue}' not found. Save it on the Deliver page first.")
    project.SetRenderSettings({"SelectAllFrames": True, "TargetDir": os.path.expanduser(args.out),
                               "CustomName": name})
    return project.AddRenderJob()


# --- main -------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="clips.json from find_moments.py")
    ap.add_argument("--media", help="stream video path (overrides source_media in clips.json)")
    ap.add_argument("--no-hook-titles", dest="hook_titles", action="store_false",
                    help="don't add a Text+ title with the hook at the start of each clip")
    ap.add_argument("--subtitles", action="store_true",
                    help="auto-create subtitles from audio on each new timeline")
    ap.add_argument("--queue", metavar="PRESET",
                    help="add a render job per clip using this saved Deliver-page preset")
    ap.add_argument("--out", default="~/Movies/BattleHouse Renders", help="render folder (with --queue)")
    ap.add_argument("--start-render", action="store_true", help="start rendering after queueing")
    ap.add_argument("--dry-run", action="store_true", help="print the plan; don't touch Resolve")
    ap.add_argument("--fps", type=float, default=30.0, help="frame rate for --dry-run only")
    args = ap.parse_args()

    media, clips = load_plan(args.plan, args.media)

    if args.dry_run:
        print(f"Source: {media}  ({len(clips)} clips @ {args.fps} fps, {WIDTH}x{HEIGHT})")
        for i, c in enumerate(clips, 1):
            s, e = float(c["start_seconds"]), float(c["end_seconds"])
            print(f"  {timeline_name(i, c)}: frames {round(s * args.fps)}-{round(e * args.fps) - 1} "
                  f"({e - s:.0f}s) hook={c.get('hook_text', '')!r} notes={len(c.get('notes', []))}")
        return

    resolve = connect()
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        sys.exit("Open a project in Resolve first.")
    pool = project.GetMediaPool()
    media_item = find_or_import(pool, media)
    fps = float(media_item.GetClipProperty("FPS"))
    pool.SetCurrentFolder(get_bin(pool))
    existing = existing_timelines(project)

    print(f"Project '{project.GetName()}', source at {fps} fps")
    timelines = []
    for i, clip in enumerate(clips, 1):
        name = timeline_name(i, clip)
        if name in existing:
            print(f"  = {name} (exists, keeping your edits)")
            timelines.append((name, existing[name]))
            continue
        print(f"  + {name}")
        tl = build_clip(project, pool, media_item, fps, name, clip, args)
        if tl:
            timelines.append((name, tl))

    if args.queue:
        queued = sum(bool(queue_render(project, tl, name, args)) for name, tl in timelines)
        print(f"Queued {queued} render jobs to {args.out}")
        if args.start_render and queued:
            project.StartRendering()
            print("Rendering started.")

    resolve.OpenPage("edit")
    print("Done.")


if __name__ == "__main__":
    main()

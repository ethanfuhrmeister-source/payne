#!/usr/bin/env python3
"""Assemble a paper edit (story.json) into a rough-cut timeline in DaVinci Resolve Studio.

Run with Resolve Studio open and your project loaded:

    python3 assemble.py story.json

Builds one timeline with every shot in story order, plus markers:
  act/beat markers (beat purpose + music), purple = confessional, green = host,
  yellow = editor note. Each run makes a new timeline (v1, v2...), so nothing you've
  edited gets overwritten. --dry-run prints the cut list without touching Resolve.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from color import apply_looks
from common import config_value, connect_resolve, drive_folder, find_media, hms

# Per-Mac record of which paper edits the background job has already built.
STATE = Path.home() / "Library" / "Application Support" / "BattleHouse" / "assembled.json"

BIN_NAME = "BattleHouse Story"
ACT_COLORS = ["Red", "Blue", "Cyan", "Pink", "Lavender", "Sand", "Mint", "Rose"]
KIND_MARKERS = {"confessional": ("Purple", "CONF"), "host": ("Green", "HOST"), "broll": ("Cream", "B-ROLL")}


def load_story(path):
    path = Path(path)
    story = json.loads(path.read_text(encoding="utf-8"))
    sources = story.get("sources")
    if not sources:
        sys.exit("story.json has no source video paths; create it with paper_edit.py.")
    return story, {k: find_media(v) for k, v in sources.items()}


def latest_story():
    """Newest story.json in the shared Drive's Paper Edits folder."""
    drive = drive_folder()
    if not drive:
        sys.exit("No Drive folder set up. Run install.command first, or pass a story.json path.")
    stories = sorted((drive / "Paper Edits").glob("**/story.json"), key=lambda p: p.stat().st_mtime)
    if not stories:
        sys.exit(f"No story.json found in {drive / 'Paper Edits'}")
    return stories[-1]


def shot_list(story):
    """Flatten acts > beats > shots, remembering where each act and beat starts."""
    for ai, act in enumerate(story["acts"]):
        for bi, beat in enumerate(act["beats"]):
            for si, shot in enumerate(beat["shots"]):
                yield ai, act, (bi == 0 and si == 0), beat, si == 0, shot


# --- Resolve ----------------------------------------------------------------------------------

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


def get_bin(pool):
    root = pool.GetRootFolder()
    for sub in root.GetSubFolderList() or []:
        if sub.GetName() == BIN_NAME:
            return sub
    return pool.AddSubFolder(root, BIN_NAME)


def unique_name(project, base):
    names = {project.GetTimelineByIndex(i).GetName() for i in range(1, project.GetTimelineCount() + 1)}
    n = 1
    while f"{base} v{n}" in names:
        n += 1
    return f"{base} v{n}"


class Markers:
    """Resolve allows one marker per frame; nudge collisions forward."""

    def __init__(self, tl):
        self.tl, self.used = tl, set()

    def add(self, frame, color, name, note):
        while frame in self.used:
            frame += 1
        if self.tl.AddMarker(frame, color, name, note, 1):
            self.used.add(frame)


def assemble(resolve, story, sources, args, background=False):
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        sys.exit("Open a project in Resolve first.")
    pool = project.GetMediaPool()
    # Remember where the editor was so a background build doesn't pull them away.
    previous_tl, previous_folder = project.GetCurrentTimeline(), pool.GetCurrentFolder()
    items = {sid: find_or_import(pool, media) for sid, media in sources.items()}
    fps_of = {sid: float(item.GetClipProperty("FPS") or 30) for sid, item in items.items()}

    pool.SetCurrentFolder(get_bin(pool))
    name = unique_name(project, f"BH Story - {story['title']}"[:60])
    tl = pool.CreateEmptyTimeline(name)
    if not tl:
        sys.exit("Couldn't create the timeline.")
    project.SetCurrentTimeline(tl)
    if args.vertical:
        tl.SetSetting("useCustomSettings", "1")
        tl.SetSetting("timelineResolutionWidth", "1080")
        tl.SetSetting("timelineResolutionHeight", "1920")
        tl.SetSetting("timelineInputResMismatchBehavior", "scaleToCrop")
    tl_fps = float(tl.GetSetting("timelineFrameRate") or next(iter(fps_of.values())))
    tl_start = tl.GetStartFrame()

    markers, position, placed, failed = Markers(tl), 0, 0, 0
    placed_items = {}  # source id -> timeline clips, for colour
    print(f"Building '{name}' at {tl_fps:g} fps")
    for ai, act, act_start, beat, beat_start, shot in shot_list(story):
        sid = shot["source"]
        if sid not in items:
            print(f"  ! unknown source {sid}, skipping shot")
            failed += 1
            continue
        fps = fps_of[sid]
        start, end = round(shot["start_seconds"] * fps), round(shot["end_seconds"] * fps)
        appended = pool.AppendToTimeline([{"mediaPoolItem": items[sid], "startFrame": start, "endFrame": end - 1}])
        if not appended:
            print(f"  ! couldn't place {sid} {hms(shot['start_seconds'])}")
            failed += 1
            continue
        placed += 1
        placed_items.setdefault(sid, []).append(appended[0])
        try:
            at = appended[0].GetStart() - tl_start
        except Exception:
            at = position
        position = at + round((shot["end_seconds"] - shot["start_seconds"]) * tl_fps)

        color = ACT_COLORS[ai % len(ACT_COLORS)]
        if act_start:
            markers.add(at, color, f"ACT: {act['name']}", "")
        if beat_start:
            note = "\n".join(filter(None, [f"[{beat['storyline']}] {beat['purpose']}",
                                           beat.get("music") and f"Music: {beat['music']}"]))
            markers.add(at, color, beat["name"], note)
        if shot["kind"] in KIND_MARKERS:
            c, label = KIND_MARKERS[shot["kind"]]
            markers.add(at, c, f"{label}: {shot.get('speaker', '')}".rstrip(": "), shot.get("quote", ""))
        if shot.get("note"):
            markers.add(at, "Yellow", "NOTE", shot["note"])

    summary = f"Placed {placed} shots ({hms(position / tl_fps)})" + (f", {failed} failed" if failed else "")
    drive = drive_folder()
    if drive and not args.no_color:
        color = apply_looks(project, tl, placed_items, drive / "Looks")
        if color:
            summary += f"; {color}"
    print(summary)
    if background:
        if previous_tl:
            project.SetCurrentTimeline(previous_tl)
        if previous_folder:
            pool.SetCurrentFolder(previous_folder)
    else:
        resolve.OpenPage("edit")
    return name, summary


# --- background mode --------------------------------------------------------------------------

def notify(title, message):
    script = f'display notification {json.dumps(message)} with title {json.dumps(title)}'
    try:
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    except FileNotFoundError:  # not on a Mac
        pass


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, ValueError):
        return None


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))


def watch(args):
    """One pass: build every paper edit that's new or changed since last time. Run by launchd."""
    drive = drive_folder()
    if not drive:
        return
    stories = {str(p.relative_to(drive)): p.stat().st_mtime
               for p in (drive / "Paper Edits").glob("**/story.json")}
    state = load_state()
    if state is None:  # first run on this Mac: only build paper edits made from now on
        save_state(stories)
        print(f"Watching {drive / 'Paper Edits'} ({len(stories)} existing paper edits skipped)")
        return
    todo = [rel for rel, mtime in sorted(stories.items(), key=lambda kv: kv[1]) if state.get(rel) != mtime]
    todo = [rel for rel in todo if time.time() - stories[rel] >= 30]  # let Drive finish syncing
    if not todo:
        return

    resolve = connect_resolve(quiet=True)
    if resolve is None:
        return  # Resolve isn't open; try again later
    project = resolve.GetProjectManager().GetCurrentProject()
    wanted = config_value("resolve_project")
    if not project or (wanted and project.GetName() != wanted):
        return  # wait until the editor has the BattleHouse project open

    for rel in todo:
        try:
            story, sources = load_story(drive / rel)
            name, summary = assemble(resolve, story, sources, args, background=True)
        except (ValueError, KeyError) as e:  # half-synced or malformed file
            print(f"Skipping {rel} for now: {e}")
            continue
        except SystemExit as e:
            if str(e.code).startswith("Video not found"):
                # Footage hasn't synced to this Mac yet: tell the editor once, keep retrying.
                flag = f"{rel}#waiting"
                if not state.get(flag):
                    notify("BattleHouse: waiting for footage", f"{e.code} - make the Drive folder available offline")
                    state[flag] = True
                    save_state(state)
                continue
            notify("BattleHouse: couldn't build rough cut", f"{rel}: {e.code}")
            name = None
        state[rel] = stories[rel]
        save_state(state)
        if name:
            notify("BattleHouse rough cut ready", f"{name} - {summary}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", nargs="?", help="story.json from paper_edit.py (default: newest in Drive)")
    ap.add_argument("--vertical", action="store_true", help="1080x1920 timeline instead of the project default")
    ap.add_argument("--dry-run", action="store_true", help="print the cut list; don't touch Resolve")
    ap.add_argument("--no-color", action="store_true", help="don't apply the Looks from Drive")
    ap.add_argument("--watch", action="store_true",
                    help="background mode: build any new paper edits from Drive (run by launchd)")
    args = ap.parse_args()

    if args.watch:
        args.vertical = args.vertical or bool(config_value("vertical"))
        watch(args)
        return

    story_file = args.story or latest_story()
    print(f"Paper edit: {story_file}")
    story, sources = load_story(story_file)
    if args.dry_run:
        total = 0
        for ai, act, act_start, beat, beat_start, shot in shot_list(story):
            if act_start:
                print(f"\n== {act['name']}")
            if beat_start:
                print(f"  -- {beat['name']} [{beat['storyline']}]")
            length = shot["end_seconds"] - shot["start_seconds"]
            total += length
            print(f"     {shot['source']} {hms(shot['start_seconds'])}-{hms(shot['end_seconds'])} "
                  f"{shot['kind']:<12} {shot.get('quote', '')[:60]}")
        print(f"\nTotal ~{hms(total)}; sources: {', '.join(sources)}")
        return

    assemble(connect_resolve(), story, sources, args)


if __name__ == "__main__":
    main()

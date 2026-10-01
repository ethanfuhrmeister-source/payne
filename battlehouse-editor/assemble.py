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
import sys
from pathlib import Path

from common import connect_resolve, hms

BIN_NAME = "BattleHouse Story"
ACT_COLORS = ["Red", "Blue", "Cyan", "Pink", "Lavender", "Sand", "Mint", "Rose"]
KIND_MARKERS = {"confessional": ("Purple", "CONF"), "host": ("Green", "HOST"), "broll": ("Cream", "B-ROLL")}


def load_story(path):
    path = Path(path)
    story = json.loads(path.read_text(encoding="utf-8"))
    sources = story.get("sources")
    if not sources:
        sys.exit("story.json has no source video paths; create it with paper_edit.py.")
    return story, {k: os.path.expanduser(v) for k, v in sources.items()}


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


def assemble(resolve, story, sources, args):
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        sys.exit("Open a project in Resolve first.")
    pool = project.GetMediaPool()
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

    resolve.OpenPage("edit")
    print(f"Placed {placed} shots ({hms(position / tl_fps)})" + (f", {failed} failed" if failed else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", help="story.json from paper_edit.py")
    ap.add_argument("--vertical", action="store_true", help="1080x1920 timeline instead of the project default")
    ap.add_argument("--dry-run", action="store_true", help="print the cut list; don't touch Resolve")
    args = ap.parse_args()

    story, sources = load_story(args.story)
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

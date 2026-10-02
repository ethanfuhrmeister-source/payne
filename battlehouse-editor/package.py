#!/usr/bin/env python3
"""Build the two files to hand to someone setting this up on another computer.

    python3 package.py [output folder]

  BattleHouse-Editor.zip      – the whole toolkit for a Mac (unzip, double-click install.command)
  battlehouse-story-skill.zip – the story-producer style guide + cast bible as a Claude skill,
                                to upload in the Claude app (Settings > Capabilities > Skills)

Per-machine files (config.json, api_key.txt) are never included.
"""
import sys
import zipfile
from pathlib import Path

from common import bible_path

HERE = Path(__file__).resolve().parent
NEVER = {"config.json", "api_key.txt", "prompt.txt", ".DS_Store"}


def build(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)

    toolkit = out_dir / "BattleHouse-Editor.zip"
    with zipfile.ZipFile(toolkit, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(HERE.rglob("*")):
            rel = f.relative_to(HERE)
            if f.is_dir() or f.name in NEVER or "__pycache__" in rel.parts or f.suffix == ".zip":
                continue
            info = zipfile.ZipInfo.from_file(f, f"battlehouse-editor/{rel}")
            if f.suffix in (".command", ".py"):
                info.external_attr = 0o755 << 16  # stay double-clickable after unzipping
            z.writestr(info, f.read_bytes(), zipfile.ZIP_DEFLATED)

    skill = out_dir / "battlehouse-story-skill.zip"
    with zipfile.ZipFile(skill, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "skill" / "SKILL.md", "battlehouse-story/SKILL.md")
        z.write(bible_path(), "battlehouse-story/bible.md")  # the shared Drive bible if set up
    return toolkit, skill


if __name__ == "__main__":
    for path in build(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "dist"):
        print(f"Wrote {path}")

#!/bin/bash
# One-time setup for each editor's Mac. Double-click this file in Finder.
cd "$(dirname "$0")"
TOOLKIT="$(pwd)"
echo "=== BattleHouse story editor setup ==="
echo
echo "Drag the shared BattleHouse Google Drive folder into this window, then press Return:"
read -r DRIVE
DRIVE="${DRIVE%/}"; DRIVE="${DRIVE//\\/}"; DRIVE="$(echo "$DRIVE" | sed "s/^'//; s/'$//")"
if [ ! -d "$DRIVE" ]; then echo "That folder doesn't exist: $DRIVE"; read -r; exit 1; fi
echo
echo "Name of the Resolve project rough cuts should go into (e.g. BattleHouse S1)."
echo "Leave blank to use whichever project is open:"
read -r PROJECT
python3 - "$DRIVE" "$PROJECT" <<'PYCFG'
import json, sys
cfg = {"drive_folder": sys.argv[1]}
if sys.argv[2].strip():
    cfg["resolve_project"] = sys.argv[2].strip()
json.dump(cfg, open("config.json", "w"), indent=1)
PYCFG
mkdir -p "$DRIVE/Footage" "$DRIVE/Paper Edits"
[ -f "$DRIVE/bible.md" ] || cp story/bible.md "$DRIVE/bible.md"

python3 -m pip install --quiet --user -r requirements.txt || echo "(pip install failed - only needed for making paper edits)"

# Transcription (only needed on the Mac that makes paper edits): Whisper needs ffmpeg.
if [ "$(uname -m)" = "arm64" ]; then WHISPER=mlx-whisper; else WHISPER=openai-whisper; fi
python3 -m pip install --quiet --user "$WHISPER" || echo "(couldn't install $WHISPER)"
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg
  else echo "NOTE: install ffmpeg for transcription: https://brew.sh then 'brew install ffmpeg'"; fi
fi

SCRIPTS="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit"
mkdir -p "$SCRIPTS"
cat > "$SCRIPTS/BattleHouse Assemble.py" <<PY
# Builds the newest paper edit from the shared Drive as a rough-cut timeline.
import sys
sys.path.insert(0, "$TOOLKIT")
import assemble
sys.argv = ["assemble"]
try:
    assemble.main()
except SystemExit as e:
    if e.code:
        print(e.code)
PY
# Background job: every 2 minutes, build any new paper edit into Resolve (if Resolve is open).
PY3="$(command -v python3)"
AGENT="$HOME/Library/LaunchAgents/com.battlehouse.assemble.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat > "$AGENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.battlehouse.assemble</string>
  <key>ProgramArguments</key><array>
    <string>$PY3</string><string>$TOOLKIT/assemble.py</string><string>--watch</string>
  </array>
  <key>StartInterval</key><integer>120</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/BattleHouse.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/BattleHouse.log</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)" "$AGENT" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$AGENT" && AUTO=on || AUTO="off (couldn't start background job)"

echo
echo "Done."
echo " - Automatic rough cuts: $AUTO - new paper edits appear in Resolve within ~2 minutes"
echo "   while Resolve is open. Log: ~/Library/Logs/BattleHouse.log"
echo "   (If macOS asks whether python3 may access Google Drive, click Allow.)"
echo " - Drive folder: $DRIVE"
echo " - In Resolve: Workspace > Scripts > Edit > BattleHouse Assemble"
echo "   (Resolve: Preferences > System > General > External scripting using: Local)"
echo "Press Return to close."
read -r

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
printf '{"drive_folder": "%s"}\n' "$DRIVE" > config.json
mkdir -p "$DRIVE/Footage" "$DRIVE/Paper Edits"
[ -f "$DRIVE/bible.md" ] || cp story/bible.md "$DRIVE/bible.md"

python3 -m pip install --quiet --user -r requirements.txt || echo "(pip install failed - only needed for making paper edits)"

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
echo
echo "Done."
echo " - Drive folder: $DRIVE"
echo " - In Resolve: Workspace > Scripts > Edit > BattleHouse Assemble"
echo "   (Resolve: Preferences > System > General > External scripting using: Local)"
echo "Press Return to close."
read -r

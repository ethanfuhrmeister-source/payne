#!/bin/bash
# For whoever builds the paper edits. Double-click this file in Finder.
cd "$(dirname "$0")"
DRIVE="$(python3 -c 'import json;print(json.load(open("config.json"))["drive_folder"])' 2>/dev/null)"
if [ -z "$DRIVE" ]; then echo "Run install.command first."; read -r; exit 1; fi
if [ -z "$ANTHROPIC_API_KEY" ] && [ -f api_key.txt ]; then export ANTHROPIC_API_KEY="$(cat api_key.txt)"; fi
if [ -z "$ANTHROPIC_API_KEY" ]; then echo "Put your Claude API key in api_key.txt next to this file."; read -r; exit 1; fi
echo "Episode folders in $DRIVE/Footage:"
ls -1 "$DRIVE/Footage"
echo
read -r -p "Episode folder name: " EP
read -r -p "Brief (what's the story / what to focus on, or leave blank): " BRIEF
read -r -p "Target minutes [20]: " MIN
echo
echo "Step 1/2: transcribing any videos that don't have a transcript yet..."
python3 transcribe.py "$DRIVE/Footage/$EP" || { echo "Transcription failed."; read -r; exit 1; }
echo
echo "Step 2/2: building the paper edit with Claude..."
python3 paper_edit.py "$DRIVE/Footage/$EP" --brief "$BRIEF" --minutes "${MIN:-20}" \
  && open "$DRIVE/Paper Edits/$EP/story.md"
echo "Press Return to close."
read -r

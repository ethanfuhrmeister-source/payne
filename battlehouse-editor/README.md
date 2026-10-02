# BattleHouse Live story editor

**Goal:** give editors their time back. Claude does the slow first pass of a reality story edit
(watching hours of transcripts, finding the storylines, pulling soundbites, laying out a
rough cut), so editors start from a structured assembly instead of a blank timeline.

## How it works

```
Shared Google Drive                          Editor's Mac (DaVinci Resolve Studio 21)
├─ Footage/Episode 3/  (.mp4 + .srt)
├─ bible.md            (cast + storylines)
└─ Paper Edits/Episode 3/  ◄── Claude ──     Workspace > Scripts > BattleHouse Assemble
     story.md   (read & approve)                → rough-cut timeline, ready to edit
     story.json (used by Resolve)
```

1. **Footage goes in Drive** under `Footage/<episode>/`.
2. **One person makes the paper edit:** double-click `make_paper_edit.command`, pick the
   episode, type a one-line brief. It **transcribes any new footage automatically** (on the
   Mac, with Whisper), then Claude writes `story.md` into `Paper Edits/<episode>/`.
3. **Producer/lead reads `story.md`** (storylines, acts, every soundbite with timecodes,
   coverage gaps) and approves it, or re-runs with a sharper brief.
4. **Editor opens Resolve** → *Workspace → Scripts → Edit → BattleHouse Assemble*. The newest
   paper edit is built as a new timeline in a `BattleHouse Story` bin: every shot in story
   order, with colour markers for acts/beats (with each beat's purpose and music idea),
   confessionals, host lines, b-roll and notes. Nothing existing is ever overwritten.
5. **Editor cuts from there:** lays b-roll and reactions over dialogue, tightens, adds music
   and graphics.

## Setup

### The shared Drive (once)
Create a `BattleHouse` folder in Google Drive and share it with the editors. The installer
creates `Footage/`, `Paper Edits/` and `bible.md` inside it. **Fill in `bible.md`** (cast
look/voice notes) – it's how Claude knows who's talking.

### Each editor's Mac (once, ~2 minutes)
1. Install **Google Drive for desktop** and make the `BattleHouse` folder **available offline**
   (right-click → *Available offline*). Resolve needs the footage on the disk, not streaming.
2. Get this `battlehouse-editor` folder onto the Mac (e.g. put a copy in the Drive folder).
3. Double-click **`install.command`** and drag the shared `BattleHouse` Drive folder into the
   window when asked. (If macOS blocks it: right-click → *Open*.)
4. In Resolve: *Preferences → System → General → External scripting using: **Local***.

### The person making paper edits (once)
Get a Claude API key at console.anthropic.com and save it in a file called `api_key.txt`
next to `make_paper_edit.command`. Editors who only assemble don't need a key.

## Transcripts
`make_paper_edit.command` transcribes automatically: every video in the episode folder
without a transcript gets a `.srt` saved next to it (`day3_main.mp4` → `day3_main.srt`),
so it only happens once per file and everyone on the Drive can reuse it.
- Runs locally with **Whisper** (mlx-whisper on Apple Silicon Macs – roughly a few minutes
  per hour of footage on an M-series Mac; much slower on Intel). Nothing is uploaded.
- Cast names from `bible.md` are given to Whisper so handles like *Tommy2Coats* are spelled
  right. Keep the bible's cast list current.
- Needs `ffmpeg` (the installer adds it via Homebrew if Homebrew is installed).
- Already have transcripts (e.g. from Resolve's *Create Subtitles from Audio* → *Export
  Subtitle*)? Drop the `.srt` next to the video with the same name and it's skipped.

## Files

| File | What it is |
|---|---|
| `install.command` | One-time setup per Mac: links the Drive folder and adds the Resolve menu item. |
| `make_paper_edit.command` | Double-click to build a paper edit for an episode. |
| `transcribe.py` | Step 1 of that: transcribes videos that have no `.srt` yet. `python3 transcribe.py "<Drive>/Footage/Episode 3"` |
| `paper_edit.py` | Step 2 of that. Command line: `python3 paper_edit.py "<Drive>/Footage/Episode 3" --brief "..." --minutes 20` (`--prompt-only` / `--import-reply` to use the Claude app instead of an API key). |
| `assemble.py` | What the Resolve menu item runs. Command line: `python3 assemble.py [story.json] [--vertical] [--dry-run]`. |
| `skill/SKILL.md` | How Claude builds a BattleHouse story (A/B/C stories, cold open, act-outs, soundbite rules). Starter – lock in `[VERIFY]` lines with the showrunner. |
| `story/bible.md` | Template for the shared `bible.md` in Drive. |

## Good to know
- Claude works from **what's said**, not the picture. Silent moments (looks, action) only
  make it in if the transcript or the brief mentions them.
- Footage paths are stored relative to the Drive folder, so a paper edit made on one Mac
  assembles on any editor's Mac.
- Rule baked into the style guide: never cut someone's words to change what they meant.

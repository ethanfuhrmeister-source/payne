# BattleHouse Live story editor

**Goal:** give editors their time back. Claude does the slow first pass of a reality story edit
(watching hours of transcripts, finding the storylines, pulling soundbites, laying out a
rough cut), so editors start from a structured assembly instead of a blank timeline.

## How it works

```
Shared Google Drive                          Editor's Mac (DaVinci Resolve Studio 21)
├─ Footage/Episode 3/  (.mp4 + .srt)
├─ Looks/              (show look .drx)
├─ bible.md            (cast + storylines)
└─ Paper Edits/Episode 3/  ◄── Claude ──     Workspace > Scripts > BattleHouse Assemble
     story.md   (for reference)                 → rough-cut timeline, built automatically
     story.json (used by Resolve)
```

1. **Footage goes in Drive** under `Footage/<episode>/`.
2. **One person makes the paper edit:** double-click `make_paper_edit.command`, pick the
   episode, type a one-line brief. It **transcribes any new footage automatically** (on the
   Mac, with Whisper), then Claude writes `story.md` into `Paper Edits/<episode>/`.
3. **Producer/lead can read `story.md`** (storylines, acts, every soundbite with timecodes,
   coverage gaps) while the rough cut builds, and re-run with a sharper brief if needed.
4. **The rough cut builds itself.** On every editor's Mac a background job checks Drive every
   2 minutes. When a new paper edit appears and Resolve is open (in the BattleHouse project),
   it builds a new timeline in a `BattleHouse Story` bin and pops up a Mac notification
   *"BattleHouse rough cut ready"*. Every shot is in story order, with colour markers for
   acts/beats (purpose + music idea), confessionals, host lines, b-roll and notes. The editor
   stays on whatever timeline they were working in, and nothing existing is overwritten.
   Re-running a paper edit (new brief) produces a new version (`v2`, `v3`…).
   *(Manual option: Workspace → Scripts → Edit → BattleHouse Assemble.)*
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
3. Double-click **`install.command`**, drag the shared `BattleHouse` Drive folder into the
   window, and type the Resolve project name rough cuts should go into (e.g. `BattleHouse S1`).
   (If macOS blocks it: right-click → *Open*. If it asks whether python3 may access Google
   Drive, click *Allow*.) This also turns on automatic rough cuts –
   `uninstall_auto.command` turns them off again.
4. In Resolve: *Preferences → System → General → External scripting using: **Local***.

### The person making paper edits (once)
Get a Claude API key at console.anthropic.com and save it in a file called `api_key.txt`
next to `make_paper_edit.command`. Editors who only assemble don't need a key.

## Colour
Rough cuts come out **already graded with the show's look**. Set it up once:
1. A colorist (or one editor) grades a representative shot from each camera/setup on the Color
   page, grabs a still, then right-click the still → *Export* → `.drx`.
2. Save it in the Drive's `Looks/` folder as **`BattleHouse.drx`**. That alone grades every clip.
3. Different cameras need different looks? Add more `.drx` (or `.cube` LUT) files and a
   `Looks/looks.json` that matches footage file names to looks (first match wins):
   ```json
   {"default": "BattleHouse.drx",
    "sources": {"*confessional*": "Confessional.drx", "*poolcam*": "Pool.cube"}}
   ```

Every automatic rough cut then applies the matching look to each clip and puts the clips in a
colour group per look (`BH Look - Confessional`, …), so a colorist can adjust a whole look at
once on the Color page. The notification says how many clips were graded. Swapping a `.drx` in
Drive changes the look for every rough cut built after that. No `Looks` files = footage is left
ungraded. This applies a consistent look; it doesn't balance shots individually, so final
shot-matching is still a colourist's pass.

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
| `color.py` | Applies the Drive `Looks/` to each new rough cut (`assemble.py --no-color` skips it). |
| `package.py` | Builds the zips for moving to another computer (see below). |
| `CLAUDE.md` | How it all works, for whichever Claude picks this up next. |
| `uninstall_auto.command` | Turns off automatic rough cuts on that Mac. |
| `assemble.py` | Builds the timeline. `--watch` is the background job (log: `~/Library/Logs/BattleHouse.log`); the Resolve menu item runs it manually. Command line: `python3 assemble.py [story.json] [--vertical] [--dry-run]`. |
| `skill/SKILL.md` | How Claude builds a BattleHouse story (A/B/C stories, cold open, act-outs, soundbite rules). Starter – lock in `[VERIFY]` lines with the showrunner. |
| `story/bible.md` | Template for the shared `bible.md` in Drive. |

## Moving to another computer / another Claude account
Nothing in the toolkit is tied to one Mac or one Claude account – the Drive path, API key and
Resolve project are set per Mac by `install.command` and never shipped.
1. On a set-up Mac run `python3 package.py` → `dist/BattleHouse-Editor.zip` and
   `dist/battlehouse-story-skill.zip`.
2. On the new Mac: unzip `BattleHouse-Editor.zip`, double-click `install.command`, and (if this
   Mac makes paper edits) put **their own** Claude API key in `api_key.txt`.
3. Optional: in their Claude app, upload `battlehouse-story-skill.zip` (Settings → Capabilities →
   Skills). Their Claude then knows the BattleHouse story style and cast even in chat – e.g.
   paste a transcript and ask for a paper edit.
4. If they use Claude Code, opening this folder loads `CLAUDE.md`, which explains how the
   toolkit works so their Claude can run, fix or extend it.

No API key? `paper_edit.py --prompt-only` / `--import-reply` work with any Claude chat.
If the toolkit folder is moved, run `install.command` again (it re-points the background job).
Optional per-Mac `config.json` keys: `model` (default `claude-opus-5-5`), `vertical`.

## Good to know
- Automatic builds only happen while Resolve is open with the BattleHouse project, and only for
  paper edits made after the installer ran. If footage hasn't finished syncing, the editor gets
  one *"waiting for footage"* notice and it retries until the files are there.
- Claude works from **what's said**, not the picture. Silent moments (looks, action) only
  make it in if the transcript or the brief mentions them.
- Footage paths are stored relative to the Drive folder, so a paper edit made on one Mac
  assembles on any editor's Mac.
- Rule baked into the style guide: never cut someone's words to change what they meant.

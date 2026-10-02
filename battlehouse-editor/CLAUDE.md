# BattleHouse story editor – notes for Claude

You're picking up a working toolkit. Read `README.md` for the user-facing workflow; this file is
how it works inside, so you can run, debug or extend it on this Mac.

## What it does
Automates the first pass of story editing for **BattleHouse Live** (live-streamed reality
competition: 30 creators, one mansion, $100K, hosts Brandon Gomes and Coach K, Season 1 from
Oct 4 2026). Short-form clips are done by separate clippers – this is only the story edit.

Pipeline (Mac + DaVinci Resolve Studio 21 + a shared Google Drive folder):
1. `transcribe.py` – Whisper (mlx-whisper on Apple Silicon) writes `<video>.srt` next to each
   video in `Drive/Footage/<episode>/` that lacks one. Cast names from the bible are passed as
   Whisper's `initial_prompt` so handles are spelled right.
2. `paper_edit.py` – sends all transcripts + `skill/SKILL.md` (system prompt) + the shared
   `Drive/bible.md` to the Claude API with structured output (acts > beats > shots with source
   + seconds). Writes `story.json`, `story.md`, `bible_updates.md` to
   `Drive/Paper Edits/<episode>/`. Shots are validated against real sources/durations.
3. `assemble.py --watch` – launchd job (every 120 s) on each editor's Mac. When a new or changed
   `story.json` appears and Resolve is open on the configured project, it builds a timeline via
   the Resolve scripting API (`AppendToTimeline`, markers per act/beat/kind), restores the
   editor's previous timeline, and posts a macOS notification. State per Mac:
   `~/Library/Application Support/BattleHouse/assembled.json`. Log: `~/Library/Logs/BattleHouse.log`.
4. `color.py` – after assembly, applies `Drive/Looks/*.drx` (or `.cube`) per source using
   `Looks/looks.json` patterns, and assigns clips to a colour group per look.

`make_paper_edit.command` runs 1+2. `install.command` sets up a Mac (config, pip, Whisper,
ffmpeg, Resolve menu script, launchd agent). No approval step: rough cuts build automatically.

## Per-machine settings (never commit these)
- `config.json` – `drive_folder` (required), `resolve_project` (optional),
  `model` (optional, default `claude-opus-5-5`), `vertical` (optional).
- `api_key.txt` – Claude API key for whoever runs paper edits (or `ANTHROPIC_API_KEY`).
- Footage paths inside `story.json` are **relative to the Drive folder**, so any Mac works.

## Testing without a Mac / Resolve
`python3 assemble.py <story.json> --dry-run` prints the cut list. For logic changes, mock the
Resolve objects (timeline, media pool, timeline items) – Resolve API calls return None/False
on failure rather than raising, so check return values. `example/*.srt` are tiny sample
transcripts.

## Things that are deliberately the way they are
- Never overwrite an existing timeline: always create `… vN`.
- Background builds must not leave the editor on a different timeline.
- Never cut words to change what someone meant (rule in `skill/SKILL.md`).
- Claude only sees transcripts, not pictures; the brief is how visual moments get in.

## Open items
- `[VERIFY]` lines in `skill/SKILL.md` (episode length, act count) need the showrunner's answer.
- Bible "How to recognise them" column is empty; "Sounds like" values are guesses.
- Not yet run on real hardware: confirm Resolve 21 accepts `ApplyGradeFromDRX` / colour-group
  calls and that launchd can read the Google Drive folder (macOS may ask to allow access).

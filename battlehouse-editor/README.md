# BattleHouse Live story editor

Claude acts as **story producer** for BattleHouse Live episodes: it reads the transcripts of all
the footage, finds the storylines, writes a **paper edit** (acts → beats → soundbites with
timecodes), then builds that as a **rough-cut timeline in DaVinci Resolve Studio 21 (Mac)**.
The editor takes it from there. Short-form clips are handled by the clippers, not this tool.

```
footage (.mp4 + matching .srt) ──► paper_edit.py ──► story.md  (review with producers)
         + story/bible.md                         └► story.json ──► assemble.py ──► Resolve rough cut
```

| File | What it is |
|---|---|
| `skill/SKILL.md` | How to build a BattleHouse story: A/B/C stories, cold open, act-outs, soundbite rules. **Starter** – lock in house style after the premiere (`[VERIFY]` lines). |
| `story/bible.md` | Cast and running storylines. Claude reads it every episode so stories stay consistent across the season. **Fill in the cast before episode 1.** |
| `paper_edit.py` | Footage transcripts + bible + your brief → `story.json`, `story.md`, `bible_updates.md`. |
| `assemble.py` | `story.json` → a new timeline in Resolve with every shot in story order and markers. |

## One-time setup (Mac)

1. `cd battlehouse-editor && python3 -m pip install -r requirements.txt`
2. **Claude API key** – create one at console.anthropic.com, then add
   `export ANTHROPIC_API_KEY=...` to `~/.zshrc`. (No key? See *Without an API key* below.)
3. **Resolve scripting** – *DaVinci Resolve → Preferences → System → General →
   External scripting using: **Local***. The default Mac paths are built in; if Resolve is
   installed elsewhere, set `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB` as described in
   *Help → Documentation → Developer → Scripting/README.txt*.
4. **Fill in `story/bible.md`** – cast names, handles, and a "how to recognise them" note.
   Transcripts don't always say who's talking; this is how Claude tells people apart.

## Each episode

1. **Transcribe every source** and save the transcript next to the video with the same name
   (`day3_main.mp4` → `day3_main.srt`):
   - In Resolve: put the clip on a timeline → *Timeline → Create Subtitles from Audio* →
     *File → Export → Subtitle…* (speaker labels help a lot if your version adds them), or
   - Whisper: `whisper day3_main.mp4 --model small --language en --output_format srt`
2. **Build the paper edit**
   ```bash
   python3 paper_edit.py /Volumes/Footage/day3/*.mp4 \
       --brief "Episode 3. Marcus gets voted out; set up the Jess/Dre alliance" \
       --minutes 20 --out ~/BattleHouse/ep3
   ```
   The brief is where you steer the story. Leave it out and Claude picks the strongest one.
3. **Review `story.md`** (storylines, act/beat outline, every soundbite with timecodes,
   coverage gaps). Re-run with a sharper brief, or edit `story.json` directly, until the
   story's right. Copy anything useful from `bible_updates.md` into `story/bible.md`.
4. **Assemble in Resolve** – open your project, then:
   ```bash
   python3 assemble.py ~/BattleHouse/ep3/story.json
   ```
   You get a `BattleHouse Story` bin with a new timeline (`… v1`, `v2` on re-runs – nothing
   gets overwritten), every shot in story order, and markers:
   - act / beat markers (colour per act) with each beat's purpose and music idea
   - 🟣 confessional · 🟢 host · cream b-roll · 🟡 editor notes ("cut before the name", "punch-in")
5. **Cut it.** The assembly is a string-out: lay b-roll and reactions over dialogue, tighten, add
   music, graphics and SFX.

### Options
- `assemble.py --dry-run` – print the cut list without touching Resolve.
- `assemble.py --vertical` – 1080×1920 timeline instead of the project's resolution.

### Without an API key
```bash
python3 paper_edit.py day3/*.mp4 --brief "..." --prompt-only --out ~/BattleHouse/ep3
# paste ~/BattleHouse/ep3/prompt.txt into Claude, save its JSON answer as reply.json, then:
python3 paper_edit.py day3/*.mp4 --brief "..." --import-reply reply.json --out ~/BattleHouse/ep3
```
Long days of footage can be too big to paste. The API handles about 1M tokens, roughly
100+ hours of talking at a time.

## Good to know
- Claude works from **what's said**, not the picture. Silent moments (looks, reactions, action)
  only show up if the transcript or your brief mentions them, so call out key visual moments in
  the brief ("Jess's face when the name is read, ~05:14 in day3_main").
- Every shot is checked against the real files: unknown sources and out-of-range times are
  dropped or clamped before anything reaches Resolve.
- Rule baked into the style guide: never cut someone's words to change what they meant.

# BattleHouse Live clip editor

Turns a BattleHouse Live stream VOD into ready-to-finish vertical clips in
**DaVinci Resolve Studio 21 on Mac**.

```
stream.mp4 ──► transcript (.srt) ──► find_moments.py ──► clips.json ──► build_timelines.py ──► Resolve
                                       (Claude picks clips,               (9:16 timelines, hook +
                                        hooks, captions)                   post markers, renders)
```

| File | What it does |
|---|---|
| `skill/SKILL.md` | The BattleHouse style guide Claude follows. **Starter version** – update it after the Oct 4 premiere (see the bottom of the file). |
| `find_moments.py` | Sends the transcript + style guide to Claude, writes `clips.json` (in/out times, score, hook, title, caption, hashtags, edit notes). |
| `build_timelines.py` | Builds one 1080×1920 timeline per clip in Resolve, with markers, an optional hook title, and render jobs. |

## One-time setup (Mac)

1. **Python packages**
   ```bash
   cd battlehouse-editor
   python3 -m pip install -r requirements.txt
   ```
2. **Claude API key** (for `find_moments.py`) – create one at console.anthropic.com, then
   `export ANTHROPIC_API_KEY=...` (add it to `~/.zshrc`). No key? Use `--prompt-only` (below).
3. **Resolve scripting** – in Resolve: *DaVinci Resolve → Preferences → System → General →
   External scripting using: **Local***. The script already knows the default Mac paths; if you
   installed Resolve elsewhere, set `RESOLVE_SCRIPT_API` and `RESOLVE_SCRIPT_LIB` as described in
   *Help → Documentation → Developer → Scripting/README.txt*.
4. **Render preset** – on the Deliver page, set up your vertical export (e.g. H.264, 1080×1920,
   your bitrate) and *Save as New Preset*, e.g. `BH Vertical`.

## Each stream

1. **Get a transcript** (either way works):
   - In Resolve: put the VOD on a timeline → *Timeline → Create Subtitles from Audio* →
     *File → Export → Subtitle…* → `stream.srt`
   - Or Whisper: `pip install openai-whisper` then
     `whisper stream.mp4 --model small --language en --output_format srt`
2. **Find the clips**
   ```bash
   python3 find_moments.py stream.srt --media "/Volumes/Footage/stream.mp4" --count 10
   ```
   Check `clips.json`: delete clips you don't want and adjust times if needed.
3. **Build the timelines** – open your Resolve project, then:
   ```bash
   python3 build_timelines.py clips.json
   ```
   You get a `BattleHouse Clips` bin with `BH_01_…`, `BH_02_…` timelines. Each has:
   - 🔴 **HOOK** marker (and a Text+ title with the hook text at the start)
   - 🔵 **POST** marker with the title, caption, hashtags and why the clip was picked
   - 🟡 **EDIT** markers where Claude suggests a punch-in, SFX, bleep or music drop
4. **Finish in Resolve**: Smart Reframe on the clip (Inspector) to keep faces centred, captions,
   SFX, music. Your caption look can be saved as a Text+ preset to reuse.
5. **Render**
   ```bash
   python3 build_timelines.py clips.json --queue "BH Vertical" --out ~/Movies/BattleHouse --start-render
   ```
   Re-running never overwrites a timeline that already exists, so your edits are safe.

### Options
- `find_moments.py --prompt-only` – writes `prompt.txt` to paste into the Claude app instead of
  using the API. Save Claude's JSON reply as `clips.json` and add
  `"source_media": "/path/to/stream.mp4"` to it.
- `build_timelines.py --subtitles` – also auto-create subtitles on each new timeline.
- `build_timelines.py --no-hook-titles` – markers only, no Text+ hook title.
- `build_timelines.py --dry-run` – show what would be built without touching Resolve.

If a step prints *"couldn't …; do it by hand"*, that feature isn't available through Resolve's
scripting in your version – everything else still gets built.

## Improving the style
The clips are only as good as `skill/SKILL.md`. After the premiere, study 10–20 official
BattleHouse clips, replace the `[VERIFY]` lines with what the show really does, and add real
examples. You can also copy the `skill` folder to `~/.claude/skills/battlehouse-clipper/` to use
the same style guide when chatting with Claude Code.

## Rights
Only post clips you're allowed to – as part of the show, or with permission / an official
clipper program. Use licensed music.

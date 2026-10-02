"""Apply the show's looks to a freshly assembled rough cut.

A colorist grades one shot per camera/setup once, exports it to the shared Drive's Looks folder
(Gallery still -> right-click -> Export -> .drx, or a .cube LUT), and every rough cut after that
gets graded automatically:

    Looks/
      BattleHouse.drx        <- default look for every clip
      Confessional.drx       <- optional extra looks...
      looks.json             <- ...and which sources use them (optional)

looks.json matches source file names (wildcards allowed) to looks; first match wins:
    {"default": "BattleHouse.drx",
     "sources": {"*confessional*": "Confessional.drx", "*pool_cam*": "Pool.cube"}}

Clips are also put in a colour group per look ("BH Look - Confessional"), so the colorist can
adjust a whole look at once on the Color page instead of shot by shot.
"""
import fnmatch
import json
from pathlib import Path

LOOK_EXTS = (".drx", ".cube")
GRADE_MODE_NO_KEYFRAMES = 0


def load_rules(looks_dir):
    """-> (default look path or None, [(pattern, look path)])"""
    looks_dir = Path(looks_dir)
    if not looks_dir.is_dir():
        return None, []
    cfg_file = looks_dir / "looks.json"
    cfg = json.loads(cfg_file.read_text()) if cfg_file.exists() else {}
    default = cfg.get("default")
    if not default:  # no config: a single look file in the folder is the default
        files = sorted(p.name for p in looks_dir.iterdir() if p.suffix.lower() in LOOK_EXTS)
        default = files[0] if len(files) == 1 else ("BattleHouse.drx" if "BattleHouse.drx" in files else None)
    rules = [(pat, looks_dir / look) for pat, look in cfg.get("sources", {}).items()]
    return (looks_dir / default if default else None), rules


def look_for(source_id, default, rules):
    for pattern, look in rules:
        if fnmatch.fnmatch(source_id.lower(), pattern.lower()):
            return look
    return default


def _color_group(project, name, cache):
    if name in cache:
        return cache[name]
    group = None
    try:
        group = next((g for g in project.GetColorGroupsList() or [] if g.GetName() == name), None)
        group = group or project.AddColorGroup(name)
    except Exception:  # older Resolve without colour-group scripting
        pass
    cache[name] = group
    return group


def _apply(tl, look, items):
    if look.suffix.lower() == ".cube":
        return sum(bool(item.SetLUT(1, str(look))) for item in items)
    try:
        ok = tl.ApplyGradeFromDRX(str(look), GRADE_MODE_NO_KEYFRAMES, items)
    except TypeError:  # some versions take the clips as separate arguments
        ok = tl.ApplyGradeFromDRX(str(look), GRADE_MODE_NO_KEYFRAMES, *items)
    return len(items) if ok else 0


def apply_looks(project, tl, items_by_source, looks_dir):
    """items_by_source: {source_id: [TimelineItem, ...]}. Returns a one-line summary or None."""
    default, rules = load_rules(looks_dir)
    if not default and not rules:
        return None  # no Looks set up yet: leave the footage ungraded

    by_look, ungraded, missing = {}, 0, set()
    for sid, items in items_by_source.items():
        look = look_for(sid, default, rules)
        if look is None:
            ungraded += len(items)
        elif not look.exists():
            missing.add(look.name)
            ungraded += len(items)
        else:
            by_look.setdefault(look, []).extend(items)

    graded, groups = 0, {}
    for look, items in by_look.items():
        try:
            done = _apply(tl, look, items)
        except Exception:
            done = 0
        graded += done
        group = _color_group(project, f"BH Look - {look.stem}", groups)
        if group:
            for item in items:
                try:
                    item.AssignToColorGroup(group)
                except Exception:
                    break

    total = sum(len(v) for v in items_by_source.values())
    parts = [f"graded {graded}/{total} clips with {', '.join(l.stem for l in by_look)}"]
    if missing:
        parts.append(f"missing look file(s): {', '.join(sorted(missing))}")
    if ungraded and not missing:
        parts.append(f"{ungraded} clips have no look")
    return "; ".join(parts)

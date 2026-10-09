#!/usr/bin/env python3
"""Scan a website's source for the 15 tell-tale AI design patterns.

Usage: python3 scan.py [path ...]   (defaults to the current directory)

FAIL  = a banned pattern; fix it unless the user explicitly asked for it.
REVIEW = a likely tell; check it by eye.
Add the text `ai-tells-ok` on a line to silence it when a pattern was requested.
Exits 1 when any FAIL is found.
"""
import colorsys
import os
import re
import sys
from html.parser import HTMLParser

EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx",
        ".ts", ".tsx", ".vue", ".svelte", ".astro", ".md", ".mdx", ".php",
        ".liquid", ".njk", ".hbs", ".erb"}
STYLE_EXTS = {".css", ".scss", ".sass", ".less"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".nuxt",
             ".svelte-kit", ".output", "vendor", ".claude", "coverage", ".cache"}
SUPPRESS = "ai-tells-ok"
# Project docs, not site copy.
DOC_FILES = re.compile(r"^(readme|changelog|contributing|license|claude|agents|.*notes?)\b.*\.(md|mdx|txt)$", re.IGNORECASE)

RULES = {
    1: "purple-blue gradient", 2: "Inter on everything", 3: "gradient text",
    4: '"introducing" badge', 5: "glowing halo", 6: "frosted glass",
    7: "icon tiles", 8: "three identical feature cards", 9: "cards inside cards",
    10: "side-stripe cards", 11: 'giant "10M+" stat', 12: "01/02/03 labels",
    13: "pulsing status dot", 14: "buzzword copy / em dashes",
    15: "beige + fancy italic serif",
}

I = re.IGNORECASE
# (rule, severity, regex, applies_to) — applies_to: "all", "style", "markup"
PATTERNS = [
    (1, "FAIL", re.compile(r"\b(from|via|to)-(purple|violet|indigo|fuchsia)-\d{2,3}\b"), "all"),
    (2, "FAIL", re.compile(r"""(font-family\s*:[^;]*['"]?\bInter\b|family=Inter\b|\bfont-inter\b|import\s*\{[^}]*\bInter\b[^}]*\}\s*from\s*['"]next/font|@fontsource(-variable)?/inter\b|['"]Inter( var| Variable)?['"])"""), "all"),
    (3, "FAIL", re.compile(r"(background-clip\s*:\s*text|-webkit-text-fill-color\s*:\s*transparent|\bbg-clip-text\b)", I), "all"),
    (4, "FAIL", re.compile(r">\s*(✨\s*)?(introducing\b|announcing\b|now in beta\b|new\s*[:!—–-])", I), "markup"),
    (5, "FAIL", re.compile(r"(filter\s*:\s*blur\(\s*([4-9]\d|\d{3,})px|\bblur-(2xl|3xl|\[\d{2,}px\])\b)", I), "all"),
    (5, "REVIEW", re.compile(r"(box|text)-shadow\s*:[^;]*\b0\s+0\s+([3-9]\d|\d{3,})px", I), "all"),
    (6, "FAIL", re.compile(r"(backdrop-filter\s*:|\bbackdrop-blur(-\w+)?\b)", I), "all"),
    (7, "REVIEW", re.compile(r"(\b[\w-]*(icon[-_]?(wrap|wrapper|box|tile|container|bg|badge|square|circle)|feature[-_]?icon)[\w-]*\b|\b[wh]-1[0-4]\b[^\"'\n]*\brounded-(lg|xl|2xl)\b[^\"'\n]*\bjustify-center\b)", I), "all"),
    (8, "REVIEW", re.compile(r"(\b(sm:|md:|lg:)?grid-cols-3\b|grid-template-columns\s*:\s*repeat\(\s*3\s*,)", I), "all"),
    (10, "FAIL", re.compile(r"(border-(left|inline-start)\s*:\s*[2-9]px\s+solid|border-(left|inline-start)-width\s*:\s*[2-9]px|\bborder-l-(2|4|8|\[\d+px\])\b)", I), "all"),
    (11, "FAIL", re.compile(r">\s*\$?\d[\d.,]*\s*[KMBkmb]\+?\s*<|>\s*\$?\d[\d.,]*\+\s*<|>\s*\d{2}(\.\d+)?%\s*<|>\s*\d+x\s*<|>\s*24/7\s*<"), "markup"),
    (12, "FAIL", re.compile(r"(>\s*0[1-9]\s*(<|[/.—–-]|&mdash;)|decimal-leading-zero|content\s*:\s*['\"]0[1-9])", I), "all"),
    (13, "FAIL", re.compile(r"(\banimate-(ping|pulse)\b|@keyframes\s+(pulse|ping|blink|glow)\b|systems?\s+(are\s+)?operational)", I), "all"),
    (14, "FAIL", re.compile(r"\b(supercharge[sd]?|turbocharge[sd]?|unlock(s|ing)? (your|the|new)|unleash|seamless(ly)?|effortless(ly)?|elevate[sd]?|empower(s|ing)?|revolutioni[sz]e|reimagine[sd]?|game[- ]?changer|next[- ]level|cutting[- ]edge|world[- ]class|all[- ]in[- ]one|blazing(ly)? fast|harness the power|fast-paced world|built for the future|transform your)\b", I), "markup"),
    (14, "FAIL", re.compile(r"(—|&mdash;|&#8212;|&#x2014;|\\u2014)"), "markup"),
    (15, "REVIEW", re.compile(r"(Instrument Serif|Playfair Display|Cormorant|Fraunces|DM Serif|Newsreader|Gloock|Bodoni Moda|font-serif[^\"'\n]*\bitalic\b)", I), "all"),
]

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB = re.compile(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)")
GRADIENT = re.compile(r"(linear|radial|conic)-gradient\(", I)
BG_DECL = re.compile(r"(background(-color)?|--[\w-]*(bg|background|paper|surface|cream|base)[\w-]*)\s*:", I)
COMMENT_LINE = re.compile(r"^\s*(//|/\*|\*|<!--|#(?!\w*[0-9a-fA-F]{3}))")


def colors(text):
    out = []
    for m in HEX.finditer(text):
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        out.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    for m in RGB.finditer(text):
        out.append(tuple(min(int(v), 255) for v in m.groups()))
    return out


def hls(rgb):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return h * 360, l, s


def is_purple(rgb):
    h, l, s = hls(rgb)
    return 255 <= h <= 300 and s > 0.35 and 0.2 < l < 0.85


def is_blue(rgb):
    h, l, s = hls(rgb)
    return 195 <= h < 255 and s > 0.35 and 0.2 < l < 0.85


def is_beige(rgb):
    h, l, s = hls(rgb)
    return 20 <= h <= 55 and l >= 0.86 and 0.08 <= s <= 0.75


class CardNesting(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack, self.hits = [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        cls = dict(attrs).get("class") or ""
        is_card = bool(re.search(r"\b[\w-]*card\b", cls, I)) and not re.search(r"card-(title|body|text|img|header|footer)", cls, I)
        depth = sum(1 for _, c in self.stack if c) + (1 if is_card else 0)
        if is_card and depth >= 2:
            self.hits.append((self.getpos()[0], f'<{tag} class="{cls}"> is card #{depth} deep'))
        self.stack.append((tag, is_card))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def scan_file(path):
    ext = os.path.splitext(path)[1].lower()
    is_style = ext in STYLE_EXTS
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    found = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if SUPPRESS in line:
            continue
        comment = bool(COMMENT_LINE.match(line))
        for rule, sev, rx, where in PATTERNS:
            if where == "markup" and (is_style or comment):
                continue
            if where == "style" and not is_style:
                continue
            if rx.search(line):
                found.append((rule, sev, n, line.strip()))
        if GRADIENT.search(line):
            cs = colors(line)
            if any(map(is_purple, cs)) and any(map(is_blue, cs)):
                found.append((1, "FAIL", n, line.strip()))
        if BG_DECL.search(line) and any(map(is_beige, colors(line))):
            found.append((15, "REVIEW", n, line.strip()))
    if ext in {".html", ".htm"}:
        p = CardNesting()
        try:
            p.feed(text)
        except Exception:
            pass
        for n, msg in p.hits:
            if SUPPRESS not in (lines[n - 1] if n <= len(lines) else ""):
                found.append((9, "REVIEW", n, msg))
    return found


def walk(paths):
    for root in paths:
        if os.path.isfile(root):
            yield root
            continue
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in files:
                if (os.path.splitext(f)[1].lower() in EXTS and not f.endswith((".min.js", ".min.css"))
                        and not DOC_FILES.match(f)):
                    yield os.path.join(d, f)


def main():
    paths = sys.argv[1:] or ["."]
    results = []
    for f in walk(paths):
        for rule, sev, n, snippet in scan_file(f):
            results.append((rule, sev, f, n, snippet))
    seen, uniq = set(), []
    for r in results:
        key = (r[0], r[2], r[3])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    fails = sum(1 for r in uniq if r[1] == "FAIL")
    reviews = len(uniq) - fails
    for rule in sorted({r[0] for r in uniq}):
        print(f"\n[{rule:>2}] {RULES[rule]}")
        for _, sev, f, n, snippet in sorted((r for r in uniq if r[0] == rule), key=lambda r: (r[1], r[2], r[3])):
            print(f"  {sev:<6} {f}:{n}  {snippet[:110]}")
    print(f"\n{fails} FAIL, {reviews} REVIEW across {len({r[2] for r in uniq})} file(s).")
    if not uniq:
        print("Clean: none of the 15 AI tells detected. Still eyeball the layout (rules 8, 9, 11).")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

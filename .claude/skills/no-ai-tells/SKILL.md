---
name: no-ai-tells
description: Keeps websites from looking AI-generated. Use whenever building, redesigning, restyling or reviewing any website, landing page, HTML/CSS, React/Vue/Svelte UI, or marketing copy. Bans the 15 tell-tale AI patterns (purple-blue gradients, Inter everywhere, gradient headline text, "introducing" pill badges, glowing hero halos, frosted glass, icon tiles, three identical feature cards, nested cards, side-stripe cards, giant "10M+" stats, 01/02/03 labels, pulsing status dots, "supercharge your workflow" copy and em dashes, beige + fancy italic serif) and runs a scanner before the work is called done.
---

# No AI Tells

Fifteen patterns make a site look like an AI default. None of them are
wrong on their own, but together they read as "nobody made a decision here."
This skill bans all fifteen by default and replaces each with a decision
that comes from the actual brand, content and audience.

**The user's explicit request always wins.** If they ask for a gradient,
frosted glass or Inter, build it. These rules cover what *you* reach for when
nobody specified anything.

**Don't swap one template for another.** Avoiding these 15 by falling back on
a different stock look (all-black brutalism, everything monospace) misses the
point. Every visual choice should be traceable to something specific: the
client's logo, their materials, their industry, their photos, their voice.

## Workflow

1. **Before writing code**, pick and note in one line each:
   - **Palette**, taken from the brand: logo, product photos, storefront,
     existing materials. Name where each color came from.
   - **Type**: a display face and a text face picked for this brand, not Inter.
   - **Layout rhythm**: how sections differ from one another (see rules 7–12).
2. **While building**, follow the 15 rules below.
3. **Before calling it done**, run the scanner and fix every `FAIL`:
   ```bash
   python3 .claude/skills/no-ai-tells/scripts/scan.py <site-dir>
   ```
   (When this skill is installed somewhere else, use the `scripts/scan.py`
   next to this file.) Read each `REVIEW` hit and either fix it or be able
   to say why it's right for this site. If a pattern was explicitly
   requested, add the comment `ai-tells-ok` on that line to silence it.
4. **Look at it.** A regex can't see layout. Screenshot the page (Playwright
   or a browser) at desktop and phone width and check the page against the list
   again, especially rules 8, 9 and 11.

## The 15 rules

### Color & type

**1. No purple-to-blue gradients.**
Banned: `linear-gradient(#7c3aed, #3b82f6)`, Tailwind `from-purple-500 to-blue-500`,
`from-indigo-* via-purple-*`, violet/indigo glows on dark navy.
Instead: flat brand colors. If a gradient is genuinely called for, keep it
subtle and within one hue family taken from the brand (e.g. two greens from the
product photo), never a purple-blue sweep.

**2. No Inter on everything.**
Banned: Inter (or Inter-alikes used as a default: Geist, SF/system-ui for
everything) as the only typeface on the page.
Instead: choose type for the brand. A display face with character for
headings plus a readable text face. Ideas: a grotesk with personality
(Space Grotesk, Familjen Grotesk, Schibsted Grotesk), a humanist sans
(Source Sans 3, Figtree, Atkinson Hyperlegible), a slab (Roboto Slab, Zilla
Slab, Bitter), a condensed display (Oswald, Barlow Condensed, Bebas Neue) or
a classic serif (Source Serif, Libre Baskerville). Match the business: a
hardware store and a nail salon should not share a typeface.

**3. No gradient text.**
Banned: `background-clip: text` + `-webkit-text-fill-color: transparent`,
Tailwind `bg-clip-text text-transparent`.
Instead: solid-color headlines. Emphasis comes from size, weight, a
contrasting typeface, an underline, or one word in the brand's accent color.

**15. No beige + fancy italic serif (the 2025 default).**
Banned: cream/oat/sand backgrounds (`#F5F1EA`, `#FAF7F2`, `#EFE9DF`…)
paired with an italic display serif (Instrument Serif, Playfair Display,
Cormorant, Fraunces, DM Serif, Newsreader italic) as the "tasteful" fallback.
Instead: if the brand really is warm and editorial, take the neutrals from its
real materials and photography and use the serif upright. Don't make
"quiet luxury beige" the default.

### Hero & decoration

**4. No "introducing" pill badge.**
Banned: a small rounded pill above the H1 saying "Introducing…", "✨ New",
"Now in beta", "Announcing…", often with an arrow.
Instead: start with the headline. If there's real news, put it in a
plain dated line or a notice bar that links to it.

**5. No glowing halo behind the hero.**
Banned: big blurred color blobs (`filter: blur(80px)`, `blur-3xl`),
radial glow orbs, `box-shadow: 0 0 120px <color>` behind headlines or product
shots.
Instead: real imagery (photos of the actual product, place or people), a
solid color block, or plain whitespace.

**6. No frosted glass.**
Banned: `backdrop-filter: blur()`, Tailwind `backdrop-blur-*`, translucent
white cards over gradients.
Instead: opaque surfaces with a clear border or a solid color difference.
A sticky header can be solid.

**13. No pulsing "all systems operational" dot.**
Banned: green pinging dots, `animate-ping`/`animate-pulse` status
indicators, "All systems operational" or "Live" badges on a site with no real
status feed.
Instead: leave it out. Add a status indicator only when it's wired to a
real status source.

### Layout & components

**7. No icon in a rounded square above every heading.**
Banned: a 40–56px rounded tile with a tinted background and a line icon,
repeated above each feature heading (`.feature-icon`, `.icon-wrapper`,
`w-12 h-12 rounded-xl flex items-center justify-center`).
Instead: use real photos, numbers with meaning, or nothing. If icons
help, put them inline with the text, unboxed, and only where they add
information.

**8. No three identical feature cards.**
Banned: a row of exactly three equal cards (icon, title, two lines of text)
as the default "features" section (`grid-cols-3`, `repeat(3, 1fr)`).
Instead: let the content decide the layout. Lead with the most important
item and size it larger, use a list, a table, alternating image/text rows, a
before/after, or a single strong paragraph. Two or five items is fine if the
content has two or five.

**9. No cards inside cards inside cards.**
Banned: bordered/rounded/shadowed boxes nested in each other more than one
level deep.
Instead: one level of container at most. Group with spacing, headings
and dividers, not more boxes.

**10. No colored stripe down the side of every card.**
Banned: `border-left: 4px solid <accent>`, Tailwind `border-l-4`, on cards,
alerts, quotes, or callouts used as decoration.
Instead: a full border, a background tint, a heading, or an icon that
carries meaning. Keep a side rule only for real blockquotes, and even then
think twice.

**11. No giant "10M+" with a tiny label.**
Banned: stat bands of huge numbers ("10M+", "99.9%", "500K+", "24/7",
"10x") over small grey captions, especially invented ones.
Instead: **never invent numbers.** If there's a real, verifiable figure,
put it in a sentence with context ("Booked 1,200 appointments since 2021").
Use testimonials, photos or specifics instead of a stat strip.

**12. No tiny 01, 02, 03 section labels.**
Banned: small zero-padded numbers or eyebrow labels ("01 / Features",
"02 — Process") above each section, `decimal-leading-zero` counters used as
decoration.
Instead: plain, descriptive headings. Number only real ordered steps, and
write them as 1, 2, 3.

### Copy

**14. No "supercharge your workflow" copy and no em dashes.**
Banned words/phrases in visible copy: supercharge, turbocharge, unlock,
unleash, seamless(ly), effortless(ly), elevate, empower, revolutionize,
reimagine, game-changer, next-level, cutting-edge, world-class, all-in-one,
blazing fast, harness the power, take X to the next level, in today's
fast-paced world, built for the future, transform your…
Banned punctuation in visible copy: em dashes (`—`, `&mdash;`, `&#8212;`).
Use a period, comma, colon or parentheses instead.
Instead: write like the business owner talks. Concrete nouns, real
prices, real places, real names, short sentences. "Gel manicure, $45, about
an hour" beats "Elevate your self-care experience."

## Quick self-check before handing off

- [ ] Palette comes from the brand, no purple-blue anywhere
- [ ] Not Inter; type chosen for this business
- [ ] No gradient, glow, blur or glass effects
- [ ] Headline is first: no pill badge, no eyebrow numbers
- [ ] Sections have different shapes; no row of three clone cards
- [ ] Max one level of card nesting; no side stripes
- [ ] No invented stats; no status dots
- [ ] Copy has no buzzwords and no em dashes
- [ ] Not defaulting to beige + italic serif
- [ ] `scan.py` shows zero FAIL

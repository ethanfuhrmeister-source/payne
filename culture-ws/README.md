# Culture — culturews.com

Static site for **Culture**, an artist studio building and gallery on the ninth
floor of Liberty Plaza, 102 W. 3rd St., Winston-Salem NC 27101.

Built from the *Culture WS design deck* (Ethan Entermedia, LLC), which pulled the
visual direction and content out of the [@culturews](https://www.instagram.com/culturews/)
Instagram feed.

No build step, no framework, no dependencies. Plain HTML, one stylesheet, two
scripts. Open `index.html` in a browser and it works.

---

## Pages

| File | Page | Job |
|---|---|---|
| `index.html` | Home | What's on next, one photo of the building, two buttons |
| `events.html` | Events | Running calendar, filterable; past events roll into the bottom |
| `studios.html` | Studios | Sizes, what's included, photos, inquiry form — *the page that pays for the building* |
| `classes.html` | Classes & camp | Drawing nights + summer camp (camp has its own `#camp` anchor) |
| `comedy.html` | Comedy | The weekly show, Camel-Gate, how to get on a lineup |
| `gallery.html` | Gallery | Current and past shows, open calls |
| `visit.html` | Visit | Ninth floor, elevator, parking, map, email, phone |

Every page ends with the address, the ninth-floor note, and an email link.

---

## Design system

Everything lives in `css/style.css` as custom properties at the top.

**Color** — cobalt leads; tomato and gold do the shouting; teal is the quiet third.

| Token | Hex | Use |
|---|---|---|
| `--ink` | `#14110F` | All body text, every border. Never pure black. |
| `--newsprint` | `#E6E0D2` | Default page |
| `--cobalt` | `#101684` | Primary — buttons, links, offset shadows, full-bleed panels |
| `--tomato` | `#C24A26` | Event dates, prices, anything with a deadline |
| `--gold` | `#DCAA2D` | Tape strips, highlights, comedy |
| `--teal` | `#7FB3AE` | Photo tints and large calm areas. Use least. |
| `--rust` | `#6F1F1B` | Dark photo overlays only |

Cobalt and tomato never touch without ink or newsprint between them. Color is
flat — no gradients.

**Type** — two families, no more. Archivo Black for headlines (uppercase, tight,
stacked short). Archivo regular for anything a person has to read. Archivo Narrow
bold for dates, prices, and labels. Headline sizes jump hard; there is no gentle
middle step. Body copy stays under ~65 characters a line.

**Texture** — cut, tilt, stick down:

- Hard offset shadows in flat color, 7px, no blur — `.paper--cobalt`, `--tomato`, `--gold`
- Rotations of 1–3° — `.tilt-l1`, `.tilt-l2`, `.tilt-r1`, `.tilt-r2`, `.tilt-r3`
- 5px halftone dot screen over dark photos — `.halftone`
- 2.5px ink borders on anything that is "a piece of paper" — `.paper`
- Torn edges where two color fields meet — `.torn`, `.torn--up`
- Tape strips — `.tape`

Not used anywhere: soft gray shadows, corners over 4px, gradient washes, stock
photos, fade-up-on-scroll. Motion happens when someone clicks and not otherwise
(`.btn:active` presses into its own shadow).

---

## The calendar

`js/events.js` holds the programming. It has two parts:

**`RECURRING`** — the standing programming, as *rules* rather than dates.
Comedy every Thursday, Collage Night the first Thursday of the month, drawing
nights every Monday. Dates are generated from these rules in the browser, so the
Events page is never empty and never goes stale. Change the rule once and every
future date follows.

**`ONE_OFFS`** — dated one-offs: gallery openings, artist talks, camp weeks. Add
objects with a `"YYYY-MM-DD"` date and they merge into the same calendar, sorted.
The array ships empty with a commented example showing the shape.

Anything in the past automatically drops into the "already happened" section at
the bottom of the Events page.

### Before this goes live

The deck sampled prices and times from posted flyers. **Confirm with the studio
before publishing**, in particular:

- Which Thursday of the month Collage Night actually falls on (the site currently
  assumes the first — change `cadence: "monthly-first"` in `js/events.js` if not)
- Current studio rates — the Studios table says "Ask" rather than guessing a number
- This summer's camp weeks and whether the waitlist is open
- Whether comedy is genuinely every Thursday or some Thursdays

---

## Photos

The site ships with no photography. Every image slot renders as a flat color
panel with a halftone screen and a label naming what belongs there — so the
layout reads as finished while being honest that the photo is missing.

See **`img/README.md`** for the shot list and how to swap a real photo in.

---

## Forms

There is no backend. The three forms (studio inquiry, class/camp registration,
comedy lineup) compose a `mailto:` to `libertyplazaws@gmail.com` with the fields
filled in, so nothing is silently dropped into a void that nobody checks.

If you'd rather have real form submissions later, the markup is standard — point
`action` at Formspree, Netlify Forms, or similar and delete the
`data-mailto` attribute.

---

## Deploying

It is static files. Any host works.

**GitHub Pages** — push to `main`, then Settings → Pages → Source: *Deploy from a
branch*, branch `main`, folder `/ (root)`.

**Netlify / Cloudflare Pages** — connect the repo, leave the build command empty,
publish directory `/`.

After the domain is set, update the two `https://culturews.com` URLs in
`sitemap.xml` and `robots.txt`.

---

## Contact

102 W. 3rd St., 9th floor · Liberty Plaza · Winston-Salem, NC 27101
libertyplazaws@gmail.com · 336-692-3581 · [@culturews](https://www.instagram.com/culturews/)

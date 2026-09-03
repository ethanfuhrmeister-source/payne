# Beauty By Payne — spec site notes

Three files. `index.html`, `events.html`, `style.css`. No build step, no CMS, no framework, no accounts.

## Why it's built this way

She just lost a platform that held her booking, payments, client records and forms. The wrong response is to hand her another subscription that can do the same thing to her next year.

This site depends on nothing she has to keep paying for:

- Static HTML and CSS — hosts free on GitHub Pages or anywhere else
- Her existing JotForms carry the enquiry flow, and JotForm's free tier covers her volume
- No booking platform, no payment processor, no CMS login
- The only external calls are Google Fonts (which degrades gracefully) and the JotForm embeds

If she later wants a real calendar, that can be added without rebuilding anything.

## The tradeoff, stated plainly

**A form captures requests. It does not hold a calendar.** She reads them and confirms times manually.

For a solo operator that is usually fine, and it is how she is already handling event bookings. Say it out loud in the pitch rather than letting her discover it — it is the one honest weakness of a static build, and naming it first is what makes the rest credible.

What she loses versus a booking platform: automatic reminders, self-serve rescheduling, saved cards, and deposit collection. What she gains: no monthly bill, nothing that can lapse, and no platform holding her client list.

## Open with the broken link

`beautybypayne.glossgenius.com` currently 302-redirects to `glossgenius.com` — the vendor's own marketing homepage. Anyone tapping "Booking Website" from her Instagram bio lands there.

**Verify on your own phone before saying it.** If it holds, that is the opening, and it costs nothing to be the person who noticed.

## Before anything else: her data

If GlossGenius is lapsing, her client list, appointment history and service notes are inside it. **That needs exporting now.** It is time-boxed, it is worth more than the website, and telling her makes you the person protecting her business rather than the person selling to her.

Do this before you pitch, not after.

## Instagram recon — read this before you walk in

Pulled from the public grid at `instagram.com/beauty.by.payne` on 3 September 2026 (341 followers).

**She is on maternity leave and closed to new appointments.** A post dated 9 July 2026 states that from **1 August** she is no longer accepting new appointment requests while she prepares for leave, and refers her clients to other nail techs in the meantime. This is the single most important fact for timing the pitch — the site's primary CTA is "Request an appointment", for a business that is not currently taking them.

**Her most recent post, 29 August 2026, is a "COMING SOON" flyer with tear-off tabs taped beside a freshly painted studio door.** The flyer's body text is too low-resolution to read from the grid image, so treat the details as unknown — but a new space appears to be opening. Worth reading properly before you walk in; it changes whether this is a "welcome back" site or a "new studio launch" site, and the launch framing is the stronger sell.

**Practical read:** she is not buying a website this week. But a site that is finished and waiting when she reopens is a much easier yes than one she has to think about while managing a newborn and a new space. Pitch it as ready-for-reopening, not as something she needs to act on now.

**Other facts worth having:**

- Trading name is **Beauty By Payne LLC**; she posts as **Charley Payne** (she/her).
- Bio still links `beautybypayne.glossgenius.com` — check the redirect claim above on your own phone, it is the opening.
- Instagram highlights already exist for Reviews, Prices, News, Policies and Press Ons. **The Reviews highlight is where the testimonials come from** — item 5 below may already be solved without asking her.
- Pricing signals from her own posts: nail art add-ons run **$5 for simple touches up to $75 for full custom**, and she has advertised discounted **$45 portfolio-model sets**. Useful for sizing what $1,800 means against her ticket.
- Her posts show a printed price list on the table in most shots. If you can get a clean photo of it, that is the services copy in item 3 written for you.

**On the photos:** the four gallery images are her own work, downsampled from Instagram's 640px grid renders and cropped to 4:5. They are good enough to pitch with and not good enough to ship. If she engages, get the originals off her phone.

## What she needs to supply

Ordered by impact.

1. **An appointment request form.** `index.html` has a placeholder iframe at `REPLACE-WITH-YOUR-APPOINTMENT-FORM`. She builds it in JotForm — service wanted, preferred days, name, contact. Fifteen minutes of her time. The site cannot go live without it.
2. **Travel radius.** City is now set to Winston-Salem across the hero, footers and both schema blocks. The travel radius for events is still open (`class="fill"` on the events page).
3. **Her nail services and what a typical appointment involves.** The whole Nails card on the home page is placeholder text.
4. **Photos — four still needed, all permanent jewelry.** The home page gallery is now filled with four real nail sets pulled from her public Instagram grid (see *Instagram recon* below). Still missing, and she is the only source: chains on the tray, a weld close up, a group showing wrists, the event setup. The entire events page still has no imagery, and **there is not a single permanent-jewelry photo on her Instagram grid** — the service the site leads with has no visual proof anywhere. Phone photos are fine and better than stock.
5. **Testimonials with first names.** There is no testimonial section on either page because I will not invent one. Once she supplies three to five, that is the largest conversion gain available.
6. **Studio location and how to find it**, plus **how she takes payment**. Both are FAQ placeholders.
7. **Time per guest and guests per hour**, and her **busy season** — event page planning questions.
8. **A domain.** Replaces `REPLACE-WITH-DOMAIN` in both canonical tags and both schema blocks. A github.io address is a real handicap for local search.

Every unknown is marked on the page with a gold dashed highlight. Search for `class="fill"` to find them all.

## What I deliberately did not do

- **No invented testimonials.** No section at all rather than filler.
- **No invented prices.** Both pages route pricing to an enquiry, which is how she already works.
- **No invented photos.** Her own Instagram photos in the nail gallery; labelled slots everywhere else, rather than AI-generated jewelry that would misrepresent her work.
- **No invented location.** Marked, not guessed.

## Technical notes

- `HealthAndBeautyBusiness` schema on both pages, with an offer catalog on the home page and both event packages on the events page.
- One `<h1>` per page, clean heading order, semantic sections.
- Sticky action bar on mobile only — the highest-value pattern here, since people decide after scrolling rather than at the top.
- Reduced motion respected. The chain animation runs once on load and is disabled for anyone who has set that preference.
- Visible keyboard focus throughout.
- Two pages rather than one long scroll, so the events page can rank on its own for event-related searches.

## Design reasoning, if she asks

Almost every nail and beauty site defaults to pale pink and cream. This goes dark and warm instead, because her events happen in the evening and gold reads properly against dark. The one bold moment is the chain drawing across the hero and the weld sparking at the join — that is the product, so that is where the boldness goes. Everything else stays quiet.

One typeface for headings, one for body. Single grid. Subtle dividers.

## Pricing

**$1,800 Business Website tier**, quoted as one number covering copy, build, SEO setup and going live.

The reason she can justify it now and could not last month: she has to replace her platform regardless. This is not a new expense being proposed, it is a cheaper answer to a bill she already has. **Find out what she was paying GlossGenius** — that number is the anchor for the whole conversation.

Offer the $75/mo care plan. Do not push it.

The real value of this deal is not the fee. It is a finished result in the beauty vertical, with photos and a testimonial, that opens salons, med spas, brow and lash studios and event vendors — where the tickets are meaningfully larger.

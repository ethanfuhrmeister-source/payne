/* ==========================================================================
   CULTURE WS — programming data
   --------------------------------------------------------------------------
   Two sources feed the calendar:

   1. RECURRING — the standing weekly/monthly programming. Dates are generated
      from these rules, so the Events page never goes stale and never empties.
      Edit the rule once and every future date follows.

   2. ONE_OFFS — gallery openings, artist talks, camp sessions, anything with
      a specific date. Add objects here; they merge into the same calendar.

   Dates in ONE_OFFS are "YYYY-MM-DD". Keep prices and times literal.
   ========================================================================== */

const DOW = { SUN:0, MON:1, TUE:2, WED:3, THU:4, FRI:5, SAT:6 };

const RECURRING = [
  {
    id: "comedy",
    title: "New | Experimental | Comedy",
    weekday: DOW.THU,
    cadence: "weekly",
    time: "9pm",
    price: "$5",
    priceNote: "roughly $5 at the door",
    category: "comedy",
    blurb: "Untested material in front of a real room. Hosted by Nevin Sharma with Camel-Gate Comedy.",
    link: "comedy.html"
  },
  {
    id: "collage",
    title: "Collage Night",
    weekday: DOW.THU,
    cadence: "monthly-first",     // first Thursday of the month
    time: "6–10pm",
    price: "Free",
    priceNote: "free, materials provided",
    category: "open studio",
    blurb: "Materials provided. Bring scissors if you have a pair you like. The easiest first visit.",
    link: "events.html"
  },
  {
    id: "drawing",
    title: "Evening Art Hour & Figure Drawing",
    weekday: DOW.MON,
    cadence: "weekly",
    time: "7–9pm",
    price: "$25",
    priceNote: "$25 per person",
    category: "class",
    blurb: "Short and long poses with a figure model. Register ahead. Bring your own supplies.",
    link: "classes.html"
  }
];

/* Add dated one-offs here. Example shape left in place, commented, on purpose.
   {
     date: "2026-10-17",
     title: "Opening: <show name>",
     time: "6–9pm",
     price: "Free",
     category: "gallery",
     blurb: "One line. What it is, not how great it is.",
     link: "gallery.html"
   }
*/
const ONE_OFFS = [];

/* ------------------------------------------------------------------ util --- */

function ymd(d){
  return d.getFullYear() + "-" +
    String(d.getMonth() + 1).padStart(2, "0") + "-" +
    String(d.getDate()).padStart(2, "0");
}

function parseYMD(s){
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/* nth (1-indexed) given weekday of a month */
function nthWeekday(year, month, weekday, nth){
  const first = new Date(year, month, 1);
  const shift = (weekday - first.getDay() + 7) % 7;
  return new Date(year, month, 1 + shift + (nth - 1) * 7);
}

/* Expand one recurring rule across a window of months around today. */
function expand(rule, monthsBack, monthsForward){
  const out = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (rule.cadence === "monthly-first"){
    for (let i = -monthsBack; i <= monthsForward; i++){
      const ref = new Date(today.getFullYear(), today.getMonth() + i, 1);
      out.push(nthWeekday(ref.getFullYear(), ref.getMonth(), rule.weekday, 1));
    }
  } else { /* weekly */
    const start = new Date(today);
    start.setDate(start.getDate() - monthsBack * 30);
    // walk forward to the first matching weekday
    while (start.getDay() !== rule.weekday) start.setDate(start.getDate() + 1);
    const end = new Date(today);
    end.setDate(end.getDate() + monthsForward * 30);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 7)){
      out.push(new Date(d));
    }
  }

  return out.map(function(d){
    return {
      date: ymd(d),
      dateObj: d,
      title: rule.title,
      time: rule.time,
      price: rule.price,
      priceNote: rule.priceNote,
      category: rule.category,
      blurb: rule.blurb,
      link: rule.link,
      recurring: true
    };
  });
}

/* Full calendar: recurring occurrences + one-offs, sorted by date. */
function buildCalendar(monthsBack, monthsForward){
  let all = [];
  RECURRING.forEach(function(rule){
    all = all.concat(expand(rule, monthsBack || 3, monthsForward || 3));
  });
  ONE_OFFS.forEach(function(e){
    all.push(Object.assign({}, e, { dateObj: parseYMD(e.date), recurring: false }));
  });
  all.sort(function(a, b){ return a.dateObj - b.dateObj; });
  return all;
}

/* Split into what's coming and what already happened. */
function splitCalendar(monthsBack, monthsForward){
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const all = buildCalendar(monthsBack, monthsForward);
  return {
    upcoming: all.filter(function(e){ return e.dateObj >= today; }),
    past: all.filter(function(e){ return e.dateObj < today; }).reverse()
  };
}

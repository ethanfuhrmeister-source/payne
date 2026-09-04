/* Beauty By Payne — appointment request scheduler
 *
 * This site is static. There is no server, no database and no shared
 * state, so this CANNOT hold a calendar or reserve a slot: two people
 * can request the same time and neither is booked until Payne replies.
 * It collects a structured request and hands it to her. Every label in
 * the UI says "request" for that reason — do not reword them to imply
 * a confirmed booking.
 */
(function () {
  "use strict";

  /* ── Configuration — Payne still has to confirm all of this ──────── */

  // Days and hours she takes appointments. 0 = Sunday.
  // PLACEHOLDER HOURS. Replace with her real availability before launch.
  var AVAILABILITY = {
    1: { open: "10:00", close: "18:00" },
    2: { open: "10:00", close: "18:00" },
    3: { open: "10:00", close: "18:00" },
    4: { open: "10:00", close: "19:00" },
    5: { open: "10:00", close: "17:00" },
    6: { open: "10:00", close: "15:00" }
  };

  var SLOT_MINUTES = 30;   // request granularity, not appointment length
  var LEAD_DAYS    = 1;    // earliest request is tomorrow
  var HORIZON_DAYS = 90;   // how far ahead the calendar opens
  var MAX_PICKS    = 3;    // she can be offered a few options at once

  // Where the finished request goes. Fill any one of these in and the
  // matching button appears; with none set, the copy-and-paste path and
  // the form below are the fallback.
  var CONTACT = { sms: "", email: "", formUrl: "" };

  var SERVICES = [
    "Acrylic full set",
    "Fill",
    "Manicure",
    "Press-on set",
    "Permanent jewelry",
    "Not sure yet"
  ];

  var TIERS = [
    { main: "No art",      note: "",         value: "" },
    { main: "Simple Touch",   note: "$5–$10",  value: "Tier One — Simple Touch ($5–$10)" },
    { main: "Mini Designs",   note: "$10–$20", value: "Tier Two — Mini Designs ($10–$20)" },
    { main: "Mixed Art Set",  note: "$20–$35", value: "Tier Three — Mixed Art Set ($20–$35)" },
    { main: "Detailed Design",note: "$35–$50", value: "Tier Four — Detailed Design ($35–$50)" },
    { main: "Full Custom Art",note: "$50–$75", value: "Tier Five — Full Custom Art ($50–$75)" },
    { main: "Not sure yet",   note: "I'll send pics", value: "Not sure yet, will send inspiration pictures" }
  ];

  var DAY_NAMES   = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  var MONTH_NAMES = ["January","February","March","April","May","June",
                     "July","August","September","October","November","December"];

  /* ── Date helpers — all local time. toISOString() would shift the
        day across the UTC boundary and mis-label the request. ──────── */

  function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function addDays(d, n) { return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }
  function key(d) {
    return d.getFullYear() + "-" +
           String(d.getMonth() + 1).padStart(2, "0") + "-" +
           String(d.getDate()).padStart(2, "0");
  }
  function longDate(d) {
    return DAY_NAMES[d.getDay()] + " " + d.getDate() + " " +
           MONTH_NAMES[d.getMonth()] + " " + d.getFullYear();
  }
  function prettyTime(hhmm) {
    var p = hhmm.split(":"), h = +p[0], m = p[1];
    var suffix = h >= 12 ? "PM" : "AM";
    var h12 = h % 12 === 0 ? 12 : h % 12;
    return h12 + ":" + m + " " + suffix;
  }
  function minutes(hhmm) { var p = hhmm.split(":"); return +p[0] * 60 + +p[1]; }
  function hhmm(mins) {
    return String(Math.floor(mins / 60)).padStart(2, "0") + ":" +
           String(mins % 60).padStart(2, "0");
  }

  var today    = startOfDay(new Date());
  var earliest = addDays(today, LEAD_DAYS);
  var latest   = addDays(today, HORIZON_DAYS);

  function isOpen(d) { return !!AVAILABILITY[d.getDay()]; }
  function selectable(d) { return isOpen(d) && d >= earliest && d <= latest; }

  function slotsFor(d) {
    var rule = AVAILABILITY[d.getDay()];
    if (!rule) return [];
    var out = [];
    for (var t = minutes(rule.open); t + SLOT_MINUTES <= minutes(rule.close); t += SLOT_MINUTES) {
      out.push(hhmm(t));
    }
    return out;
  }

  /* ── State ───────────────────────────────────────────────────────── */

  var view   = new Date(earliest.getFullYear(), earliest.getMonth(), 1);
  var focus  = new Date(earliest);
  var active = null;   // day whose slots are open
  var picks  = [];     // [{dateKey, date, time}]

  var root = document.getElementById("scheduler");
  if (!root) return;

  var els = {
    service:  root.querySelector("#sch-service"),
    tier:     root.querySelector("#sch-tier"),
    monthLbl: root.querySelector("#sch-month"),
    prev:     root.querySelector("#sch-prev"),
    next:     root.querySelector("#sch-next"),
    grid:     root.querySelector("#sch-grid"),
    slotWrap: root.querySelector("#sch-slots"),
    slotHead: root.querySelector("#sch-slots-head"),
    picks:    root.querySelector("#sch-picks"),
    name:     root.querySelector("#sch-name"),
    contact:  root.querySelector("#sch-contact"),
    notes:    root.querySelector("#sch-notes"),
    summary:  root.querySelector("#sch-summary"),
    card:     root.querySelector("#sch-card"),
    cardWrap: root.querySelector("#sch-card-wrap"),
    cardEmpty:root.querySelector("#sch-card-empty"),
    actions:  root.querySelector("#sch-actions"),
    copy:     root.querySelector("#sch-copy"),
    status:   root.querySelector("#sch-status")
  };

  /* ── Build the static bits ───────────────────────────────────────── */

  // Native radios behind styled labels: real keyboard and screen-reader
  // semantics for free, rather than a hand-rolled radiogroup.
  function buildChips(host, name, items, checkedIndex) {
    items.forEach(function (item, i) {
      var id = name + "-" + i;
      var input = document.createElement("input");
      input.type = "radio"; input.name = name; input.id = id;
      input.className = "chip-input"; input.value = item.value;
      if (i === checkedIndex) input.checked = true;
      var label = document.createElement("label");
      label.className = "chip"; label.setAttribute("for", id);
      if (item.note) {
        var strong = document.createElement("span");
        strong.className = "chip-main"; strong.textContent = item.main;
        var note = document.createElement("span");
        note.className = "chip-note"; note.textContent = item.note;
        label.appendChild(strong); label.appendChild(note);
      } else {
        label.textContent = item.main;
      }
      host.appendChild(input); host.appendChild(label);
      input.addEventListener("change", render);
    });
  }

  buildChips(els.service, "service",
    SERVICES.map(function (s) { return { main: s, value: s }; }), -1);
  buildChips(els.tier, "tier", TIERS.map(function (t) {
    return { main: t.main, note: t.note, value: t.value };
  }), 0);

  function chosen(name) {
    var el = root.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : "";
  }

  /* ── Calendar ────────────────────────────────────────────────────── */

  function renderMonth() {
    els.monthLbl.textContent = MONTH_NAMES[view.getMonth()] + " " + view.getFullYear();
    els.grid.innerHTML = "";

    ["Su","Mo","Tu","We","Th","Fr","Sa"].forEach(function (d) {
      var h = document.createElement("div");
      h.className = "cal-head"; h.setAttribute("role", "columnheader");
      h.setAttribute("aria-label", DAY_NAMES[["Su","Mo","Tu","We","Th","Fr","Sa"].indexOf(d)]);
      h.textContent = d;
      els.grid.appendChild(h);
    });

    var first = new Date(view.getFullYear(), view.getMonth(), 1);
    for (var b = 0; b < first.getDay(); b++) {
      var pad = document.createElement("div");
      pad.className = "cal-pad"; pad.setAttribute("aria-hidden", "true");
      els.grid.appendChild(pad);
    }

    var days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
    for (var i = 1; i <= days; i++) {
      var d = new Date(view.getFullYear(), view.getMonth(), i);
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cal-day";
      btn.textContent = i;
      btn.dataset.key = key(d);

      var ok = selectable(d);
      btn.disabled = !ok;
      if (!ok) {
        btn.className += " is-off";
        btn.setAttribute("aria-label", longDate(d) + " — not available");
      } else {
        btn.setAttribute("aria-label", longDate(d));
      }
      if (key(d) === key(today)) btn.className += " is-today";
      if (active && key(d) === key(active)) btn.className += " is-active";
      if (picks.some(function (p) { return p.dateKey === key(d); })) btn.className += " has-pick";
      btn.tabIndex = key(d) === key(focus) ? 0 : -1;

      els.grid.appendChild(btn);
    }
  }

  function openDay(d) {
    active = d;
    renderMonth();
    var list = slotsFor(d);
    els.slotHead.textContent = longDate(d);
    els.slotWrap.innerHTML = "";
    if (!list.length) {
      els.slotWrap.innerHTML = '<p class="sch-empty">No times on this day.</p>';
      return;
    }
    var groups = [
      { name: "Morning",   from: 0,        to: 12 * 60 },
      { name: "Afternoon", from: 12 * 60,  to: 17 * 60 },
      { name: "Evening",   from: 17 * 60,  to: 24 * 60 }
    ];
    groups.forEach(function (g) {
      var inGroup = list.filter(function (t) {
        var m = minutes(t); return m >= g.from && m < g.to;
      });
      if (!inGroup.length) return;
      var head = document.createElement("p");
      head.className = "slot-group"; head.textContent = g.name;
      els.slotWrap.appendChild(head);
      var row = document.createElement("div");
      row.className = "slot-row";
      inGroup.forEach(function (t) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "slot";
        b.textContent = prettyTime(t);
        var isPicked = picks.some(function (p) { return p.dateKey === key(d) && p.time === t; });
        if (isPicked) b.className += " is-picked";
        b.setAttribute("aria-pressed", isPicked ? "true" : "false");
        b.addEventListener("click", function () { togglePick(d, t); });
        row.appendChild(b);
      });
      els.slotWrap.appendChild(row);
    });
    els.slotWrap.parentElement.hidden = false;
  }

  function togglePick(d, t) {
    var k = key(d);
    var at = picks.findIndex(function (p) { return p.dateKey === k && p.time === t; });
    if (at > -1) {
      picks.splice(at, 1);
    } else {
      if (picks.length >= MAX_PICKS) {
        say("You can offer up to " + MAX_PICKS + " times. Remove one to add another.");
        return;
      }
      picks.push({ dateKey: k, date: new Date(d), time: t });
      picks.sort(function (a, b) {
        return a.dateKey === b.dateKey ? a.time.localeCompare(b.time)
                                       : a.dateKey.localeCompare(b.dateKey);
      });
    }
    openDay(d);
    renderPicks();
    render();
  }

  function renderPicks() {
    els.picks.innerHTML = "";
    if (!picks.length) {
      els.picks.innerHTML = '<li class="sch-empty">No times chosen yet.</li>';
      return;
    }
    picks.forEach(function (p, i) {
      var li = document.createElement("li");
      li.className = "pick";
      var span = document.createElement("span");
      span.textContent = longDate(p.date) + " at " + prettyTime(p.time);
      var x = document.createElement("button");
      x.type = "button"; x.className = "pick-x";
      x.setAttribute("aria-label", "Remove " + span.textContent);
      x.textContent = "×";
      x.addEventListener("click", function () {
        picks.splice(i, 1);
        if (active) openDay(active);
        renderMonth(); renderPicks(); render();
      });
      li.appendChild(span); li.appendChild(x);
      els.picks.appendChild(li);
    });
  }

  /* ── Summary ─────────────────────────────────────────────────────── */

  function buildText() {
    var lines = ["Appointment request — Beauty By Payne", ""];
    lines.push("Service: " + (chosen("service") || "not specified"));
    if (chosen("tier")) lines.push("Nail art: " + chosen("tier"));
    lines.push("");
    lines.push(picks.length === 1 ? "Preferred time:" : "Preferred times (any of these):");
    picks.forEach(function (p) {
      lines.push("  • " + longDate(p.date) + " at " + prettyTime(p.time));
    });
    lines.push("");
    lines.push("Name: " + (els.name.value.trim() || "—"));
    lines.push("Contact: " + (els.contact.value.trim() || "—"));
    if (els.notes.value.trim()) lines.push("Notes: " + els.notes.value.trim());
    lines.push("");
    lines.push("(Times are requested, not booked — please confirm.)");
    return lines.join("\n");
  }

  function ready() {
    return picks.length > 0 && els.name.value.trim() && els.contact.value.trim();
  }

  function renderCard() {
    var rows = [];
    rows.push(["Service", chosen("service") || "Not chosen yet"]);
    if (chosen("tier")) rows.push(["Nail art", chosen("tier")]);
    rows.push(["Times", picks.map(function (p) {
      return longDate(p.date) + " at " + prettyTime(p.time);
    })]);
    if (els.name.value.trim())    rows.push(["Name", els.name.value.trim()]);
    if (els.contact.value.trim()) rows.push(["Contact", els.contact.value.trim()]);
    if (els.notes.value.trim())   rows.push(["Notes", els.notes.value.trim()]);

    els.card.innerHTML = "";
    rows.forEach(function (r) {
      var dt = document.createElement("dt"); dt.textContent = r[0];
      var dd = document.createElement("dd");
      if (Array.isArray(r[1])) {
        var ul = document.createElement("ul"); ul.className = "card-times";
        r[1].forEach(function (t) {
          var li = document.createElement("li"); li.textContent = t; ul.appendChild(li);
        });
        dd.appendChild(ul);
      } else { dd.textContent = r[1]; }
      els.card.appendChild(dt); els.card.appendChild(dd);
    });
  }

  function render() {
    var empty = !picks.length;
    els.cardWrap.hidden = empty;
    els.cardEmpty.hidden = !empty;
    els.summary.value = empty ? "" : buildText();
    if (!empty) renderCard();
    var on = ready();
    els.actions.querySelectorAll("[data-needs-ready]").forEach(function (b) {
      b.disabled = !on;
      b.setAttribute("aria-disabled", on ? "false" : "true");
    });
  }

  var sayTimer;
  function say(msg) {
    els.status.textContent = msg;
    clearTimeout(sayTimer);
    sayTimer = setTimeout(function () { els.status.textContent = ""; }, 4000);
  }

  /* ── Handoff ─────────────────────────────────────────────────────── */

  function buildActions() {
    els.actions.innerHTML = "";
    var made = false;

    if (CONTACT.sms) {
      made = true;
      var a = document.createElement("a");
      a.className = "btn"; a.dataset.needsReady = "1";
      a.textContent = "Text this request";
      a.addEventListener("click", function (e) {
        if (!ready()) { e.preventDefault(); say("Add your name and a contact first."); return; }
        a.href = "sms:" + CONTACT.sms + "?&body=" + encodeURIComponent(buildText());
      });
      els.actions.appendChild(a);
    }
    if (CONTACT.email) {
      made = true;
      var m = document.createElement("a");
      m.className = made ? "btn-line" : "btn"; m.dataset.needsReady = "1";
      m.textContent = "Email this request";
      m.addEventListener("click", function (e) {
        if (!ready()) { e.preventDefault(); say("Add your name and a contact first."); return; }
        m.href = "mailto:" + CONTACT.email +
                 "?subject=" + encodeURIComponent("Appointment request") +
                 "&body=" + encodeURIComponent(buildText());
      });
      els.actions.appendChild(m);
    }
    if (!made) {
      var note = document.createElement("p");
      note.className = "sch-handoff";
      note.innerHTML = "Copy your request below, then paste it into the form " +
                       "underneath so Payne gets it.";
      els.actions.appendChild(note);
    }
  }

  els.copy.addEventListener("click", function () {
    if (!picks.length) { say("Pick a time first."); return; }
    var text = buildText();
    function done() { say("Request copied. Paste it into the form below."); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else { fallback(); }
    function fallback() {
      els.summary.removeAttribute("readonly");
      els.summary.select();
      try { document.execCommand("copy"); done(); }
      catch (e) { say("Select the text above and copy it."); }
      els.summary.setAttribute("readonly", "");
    }
  });

  /* ── Wiring ──────────────────────────────────────────────────────── */

  els.grid.addEventListener("click", function (e) {
    var b = e.target.closest(".cal-day");
    if (!b || b.disabled) return;
    var p = b.dataset.key.split("-");
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    focus = d;
    openDay(d);
  });

  els.grid.addEventListener("keydown", function (e) {
    var step = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
    if (!step) return;
    e.preventDefault();
    var next = addDays(focus, step);
    if (next < earliest || next > latest) return;
    focus = next;
    if (next.getMonth() !== view.getMonth() || next.getFullYear() !== view.getFullYear()) {
      view = new Date(next.getFullYear(), next.getMonth(), 1);
    }
    renderMonth();
    syncNav();
    var target = els.grid.querySelector('[data-key="' + key(focus) + '"]');
    if (target) target.focus();
  });

  els.prev.addEventListener("click", function () {
    view = new Date(view.getFullYear(), view.getMonth() - 1, 1);
    renderMonth(); syncNav();
  });
  els.next.addEventListener("click", function () {
    view = new Date(view.getFullYear(), view.getMonth() + 1, 1);
    renderMonth(); syncNav();
  });

  function syncNav() {
    // Gate on the month you would land in, not the one you are looking
    // at — otherwise you can page back into a month with no open days.
    var prevLast  = new Date(view.getFullYear(), view.getMonth(), 0);
    var nextFirst = new Date(view.getFullYear(), view.getMonth() + 1, 1);
    els.prev.disabled = prevLast < earliest;
    els.next.disabled = nextFirst > latest;
  }

  [els.name, els.contact, els.notes].forEach(function (el) {
    el.addEventListener("input", render);
    el.addEventListener("change", render);
  });

  renderMonth();
  syncNav();
  renderPicks();
  buildActions();
  render();
  root.hidden = false;
  var fb = document.getElementById("scheduler-fallback");
  if (fb) fb.hidden = true;
})();

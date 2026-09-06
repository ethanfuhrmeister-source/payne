/* ==========================================================================
   CULTURE WS — behaviour
   Motion only when someone clicks. No scroll-triggered fades.
   ========================================================================== */

(function(){
  "use strict";

  /* ------------------------------------------------------------- nav --- */

  const btn = document.querySelector(".menu-btn");
  const nav = document.getElementById("nav");

  if (btn && nav){
    btn.addEventListener("click", function(){
      const open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!open));
      nav.hidden = open;
      btn.textContent = open ? "Menu" : "Close";
    });

    // Reset when we cross back to desktop width.
    const mq = window.matchMedia("(min-width:901px)");
    const sync = function(){
      if (mq.matches){
        nav.hidden = false;
        btn.setAttribute("aria-expanded", "false");
        btn.textContent = "Menu";
      } else if (btn.getAttribute("aria-expanded") !== "true"){
        nav.hidden = true;
      }
    };
    mq.addEventListener ? mq.addEventListener("change", sync) : mq.addListener(sync);
    sync();
  }

  /* --------------------------------------------------- mark current page --- */

  const here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  document.querySelectorAll("#nav a").forEach(function(a){
    const target = (a.getAttribute("href") || "").split("#")[0].toLowerCase();
    if (target === here) a.setAttribute("aria-current", "page");
  });

  /* ------------------------------------------------------------ dates --- */

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const DAYS   = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

  function dateBlock(d){
    return '<div class="event__date">' +
             '<span class="dow">' + DAYS[d.getDay()] + '</span>' +
             '<span class="day">' + d.getDate() + '</span>' +
             '<span class="mon">' + MONTHS[d.getMonth()] + '</span>' +
           '</div>';
  }

  function esc(s){
    return String(s).replace(/[&<>"]/g, function(c){
      return { "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;" }[c];
    });
  }

  function eventRow(e, isPast){
    return '<article class="event' + (isPast ? " event--past" : "") + '">' +
      dateBlock(e.dateObj) +
      '<div class="event__body">' +
        '<h3>' + esc(e.title) + '</h3>' +
        '<p>' + esc(e.blurb) + '</p>' +
        '<div class="event__meta">' +
          '<span class="pill pill--cobalt">' + esc(e.time) + '</span>' +
          '<span class="pill pill--teal">' + esc(e.category) + '</span>' +
          '<span class="pill">9th floor</span>' +
        '</div>' +
      '</div>' +
      '<div class="event__price">' + esc(e.price) + '</div>' +
    '</article>';
  }

  /* ------------------------------------------------- home: what's next --- */

  const nextMount = document.getElementById("whats-next");
  if (nextMount && typeof splitCalendar === "function"){
    const cal = splitCalendar(0, 2);
    const soon = cal.upcoming.slice(0, Number(nextMount.dataset.count || 4));
    nextMount.innerHTML = soon.length
      ? soon.map(function(e){ return eventRow(e, false); }).join("")
      : '<p class="paper">Nothing on the public calendar right now. Email ' +
        '<a href="mailto:libertyplazaws@gmail.com">libertyplazaws@gmail.com</a> ' +
        'and we will tell you what is open.</p>';
  }

  /* ------------------------------------------- events page: full list --- */

  const upMount   = document.getElementById("upcoming");
  const pastMount = document.getElementById("past");

  if (upMount && typeof splitCalendar === "function"){
    const cal = splitCalendar(3, 3);

    function render(filter){
      const list = filter === "all"
        ? cal.upcoming
        : cal.upcoming.filter(function(e){ return e.category === filter; });

      upMount.innerHTML = list.length
        ? list.map(function(e){ return eventRow(e, false); }).join("")
        : '<p class="paper">Nothing in that category yet. Try “everything”.</p>';

      if (pastMount){
        const pastList = filter === "all"
          ? cal.past
          : cal.past.filter(function(e){ return e.category === filter; });
        pastMount.innerHTML = pastList.slice(0, 12)
          .map(function(e){ return eventRow(e, true); }).join("");
      }
    }

    render("all");

    // Filters. Motion on click only.
    document.querySelectorAll("[data-filter]").forEach(function(b){
      b.addEventListener("click", function(){
        document.querySelectorAll("[data-filter]").forEach(function(o){
          o.classList.remove("btn--tomato");
          o.classList.add("btn--plain");
          o.setAttribute("aria-pressed", "false");
        });
        b.classList.remove("btn--plain");
        b.classList.add("btn--tomato");
        b.setAttribute("aria-pressed", "true");
        render(b.dataset.filter);
      });
    });
  }

  /* -------------------------------------------------------- year stamp --- */

  document.querySelectorAll("[data-year]").forEach(function(el){
    el.textContent = new Date().getFullYear();
  });

  /* --------------------------------------------------------- mailto forms --- */
  /* No backend. Forms compose an email so nothing is silently dropped. */

  document.querySelectorAll("form[data-mailto]").forEach(function(form){
    form.addEventListener("submit", function(ev){
      ev.preventDefault();
      const data = new FormData(form);
      const lines = [];
      data.forEach(function(value, key){
        if (String(value).trim()) lines.push(key + ": " + value);
      });
      const subject = form.dataset.subject || "Message from the Culture site";
      const href = "mailto:" + form.dataset.mailto +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(lines.join("\n"));
      const status = form.querySelector("[data-status]");
      if (status){
        status.textContent = "Opening your email app. If nothing happens, email libertyplazaws@gmail.com directly.";
        status.classList.remove("hidden");
      }
      window.location.href = href;
    });
  });

})();

/* XC Core website: small extras on top of a site that works fully without
   JavaScript. No cookies, no tracking; localStorage only remembers that
   the Arabic suggestion was dismissed. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Carousels: arrows, live dots, autoplay that pauses ---------- */
  function carousel(root) {
    var track = root.querySelector(".track");
    var slides = Array.prototype.slice.call(track.querySelectorAll(".slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll(".dots a"));
    var prev = root.querySelector(".arrow.prev");
    var next = root.querySelector(".arrow.next");
    var pause = root.querySelector(".pause");
    if (!slides.length) return;
    var current = 0, timer = null, stopped = reduce;

    function go(i) {
      current = (i + slides.length) % slides.length;
      var s = slides[current];
      // Scroll the track only (not the page), in either direction (RTL too).
      var tr = track.getBoundingClientRect(), sr = s.getBoundingClientRect();
      var centre = window.innerWidth < 900;
      var delta = centre ? (sr.left + sr.width / 2) - (tr.left + tr.width / 2)
        : (document.dir === "rtl" ? sr.right - tr.right + 56 : sr.left - tr.left - 56);
      track.scrollBy({ left: delta, behavior: reduce ? "auto" : "smooth" });
      mark(current);
    }
    function mark(i) {
      dots.forEach(function (d, k) {
        if (k === i) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current");
      });
    }
    // Keep the dots in step with swipes.
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting && e.intersectionRatio > 0.6) {
            current = slides.indexOf(e.target);
            mark(current);
          }
        });
      }, { root: track, threshold: [0.6] });
      slides.forEach(function (s) { io.observe(s); });
    }
    dots.forEach(function (d, k) {
      d.addEventListener("click", function (ev) { ev.preventDefault(); stop(); go(k); });
    });
    prev.hidden = next.hidden = false;
    prev.addEventListener("click", function () { stop(); go(current - 1); });
    next.addEventListener("click", function () { stop(); go(current + 1); });

    function tick() { go(current + 1); }
    function start() {
      if (stopped || timer) return;
      timer = window.setInterval(tick, 5000);
    }
    function halt() { if (timer) { window.clearInterval(timer); timer = null; } }
    function stop() {
      stopped = true; halt();
      if (pause) pause.textContent = pause.getAttribute("data-play");
    }
    if (!reduce && pause) {
      pause.hidden = false;
      pause.addEventListener("click", function () {
        if (stopped) {
          stopped = false; pause.textContent = pause.getAttribute("data-pause"); start();
        } else {
          stop();
        }
      });
      // A touch, the pointer or keyboard focus inside pauses it for good.
      ["touchstart", "pointerdown", "wheel"].forEach(function (t) {
        track.addEventListener(t, stop, { passive: true });
      });
      root.addEventListener("mouseenter", halt);
      root.addEventListener("mouseleave", start);
      root.addEventListener("focusin", halt);
      // Only run while the carousel is on screen.
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (e) {
          if (e[0].isIntersecting) start(); else halt();
        }, { threshold: 0.3 }).observe(root);
      } else {
        start();
      }
    }
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-carousel]"), carousel);

  /* ---------- The video: silent teaser loop, full video with sound ---------- */
  var v = document.getElementById("promo");
  var soundBtn = document.querySelector("[data-sound]");
  if (v && soundBtn) {
    var full = false;
    function sources(mp4, webm) {
      Array.prototype.slice.call(v.querySelectorAll("source")).forEach(function (s) { v.removeChild(s); });
      var track = v.querySelector("track");
      [[webm, "video/webm"], [mp4, "video/mp4"]].forEach(function (p) {
        var s = document.createElement("source");
        s.src = p[0]; s.type = p[1];
        v.insertBefore(s, track);
      });
    }
    if (!reduce) {
      // Start as the muted teaser, looping, once it scrolls into view.
      sources(v.dataset.teaserMp4, v.dataset.teaserWebm);
      v.muted = true; v.loop = true; v.preload = "metadata";
      v.load();
      var played = false;
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (e) {
          if (full) return;
          if (e[0].isIntersecting) { v.play().catch(function () {}); played = true; }
          else if (played) v.pause();
        }, { threshold: 0.4 }).observe(v);
      }
    }
    soundBtn.hidden = false;
    soundBtn.addEventListener("click", function () {
      if (!full) {
        full = true;
        sources(v.dataset.fullMp4, v.dataset.fullWebm);
        v.poster = v.dataset.fullPoster;
        v.loop = false;
        v.load();
      }
      v.muted = false;
      v.currentTime = 0;
      v.play().catch(function () {});
      soundBtn.hidden = true;
    });
  }

  /* ---------- A one-time suggestion of the Arabic site ---------- */
  var hint = document.getElementById("lang-hint");
  if (hint) {
    var key = "xccore-lang-hint";
    var seen = null;
    try { seen = window.localStorage.getItem(key); } catch (e) { seen = "?"; }
    var langs = navigator.languages || [navigator.language || ""];
    var prefersArabic = String(langs[0] || "").toLowerCase().indexOf("ar") === 0;
    if (prefersArabic && !seen) {
      hint.hidden = false;
      var remember = function () { try { window.localStorage.setItem(key, "1"); } catch (e) {} };
      hint.querySelector("[data-dismiss]").addEventListener("click", function () {
        remember(); hint.hidden = true;
      });
      hint.querySelector("a").addEventListener("click", remember);
      remember(); // Shown once: not again on the next page.
    }
  }
})();

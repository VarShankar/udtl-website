/* Shared behaviour: mobile menu, theme toggle, publication filters,
   grant progress bars, scroll reveal, and the lab hero "RBF stencil" canvas. */
(function () {
  "use strict";
  var doc = document.documentElement;

  /* ---- theme toggle (persisted per viewer) ---- */
  var themeBtn = document.querySelector("[data-theme-toggle]");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var dark = doc.getAttribute("data-theme") === "dark" ||
      (!doc.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    doc.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
    window.dispatchEvent(new Event("themechange"));
  });

  /* ---- mobile drawer ---- */
  var menuBtn = document.querySelector("[data-menu]");
  var drawer = document.getElementById("drawer");
  if (menuBtn && drawer) menuBtn.addEventListener("click", function () {
    var open = drawer.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", String(open));
  });

  /* ---- reveal on scroll ---- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else reveals.forEach(function (el) { el.classList.add("in"); });

  /* ---- grant progress (computed at view time so it never goes stale) ---- */
  var now = new Date(), yr = now.getFullYear() + now.getMonth() / 12;
  document.querySelectorAll("[data-start][data-end]").forEach(function (el) {
    var s = +el.dataset.start + (+el.dataset.startMonth || 0) / 12;
    var e = +el.dataset.end + (+el.dataset.endMonth || 0) / 12;
    var p = Math.max(0, Math.min(1, (yr - s) / Math.max(e - s, .1)));
    el.style.setProperty("--p", (p * 100).toFixed(1) + "%");
  });

  /* ---- publications filter ---- */
  var list = document.querySelector("[data-pubs]");
  if (list) {
    var items = Array.prototype.slice.call(list.querySelectorAll(".pub"));
    var years = Array.prototype.slice.call(list.querySelectorAll(".pub-year"));
    var chips = document.querySelectorAll("[data-tag]");
    var q = document.getElementById("pub-q");
    var count = document.getElementById("pub-count");
    var tag = "all";
    function apply() {
      var term = (q && q.value || "").trim().toLowerCase(), shown = 0;
      items.forEach(function (li) {
        var ok = (tag === "all" || (" " + li.dataset.tags + " ").indexOf(" " + tag + " ") > -1) &&
                 (!term || li.textContent.toLowerCase().indexOf(term) > -1);
        li.hidden = !ok; if (ok) shown++;
      });
      years.forEach(function (h) {
        var any = list.querySelector('.pub[data-year="' + h.dataset.year + '"]:not([hidden])');
        h.hidden = !any;
      });
      if (count) count.textContent = shown + " of " + items.length;
    }
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        tag = c.dataset.tag;
        chips.forEach(function (o) { o.setAttribute("aria-pressed", String(o === c)); });
        apply();
      });
    });
    if (q) q.addEventListener("input", apply);
    var h = location.hash.replace("#", "");
    var pre = h && document.querySelector('[data-tag="' + h + '"]');
    if (pre) pre.click(); else apply();
  }

  /* ---- lab hero: scattered nodes + nearest-neighbour stencils (an RBF-FD nod) ---- */
  var cv = document.getElementById("hero-canvas");
  if (cv && cv.getContext) {
    var ctx = cv.getContext("2d"), W, H, dpr, pts = [], K = 5, raf, reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    function col(v) { return getComputedStyle(doc).getPropertyValue(v).trim(); }
    var cAcc, cLine, cInk;
    function colors() { cAcc = col("--accent"); cLine = col("--line"); cInk = col("--muted"); }
    function seed() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = cv.clientWidth; H = cv.clientHeight;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.round(Math.min(180, W * H / 6500)); pts = [];
      // Halton (2,3) quasi-random nodes: well-spaced like a meshless node set
      function halton(i, b) { var f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; }
      for (var i = 1; i <= n; i++) {
        var x = halton(i, 2), y = halton(i, 3);
        pts.push({ x0: x * W, y0: y * H, x: x * W, y: y * H, ph: Math.random() * 6.283, a: 6 + Math.random() * 10 });
      }
    }
    var t0 = performance.now(), focus = 0, nextSwitch = 0;
    function frame(t) {
      var s = (t - t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      // gentle "flow" displacement: a smooth divergence-free-ish swirl
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        p.x = p.x0 + p.a * Math.sin(s * .35 + p.ph + p.y0 / 160);
        p.y = p.y0 + p.a * Math.cos(s * .3 + p.ph + p.x0 / 190);
      }
      if (s > nextSwitch) { focus = (Math.random() * pts.length) | 0; nextSwitch = s + 2.4; }
      // stencils for a handful of centres
      ctx.lineWidth = 1;
      for (var c = 0; c < pts.length; c += 7) {
        var pc = pts[c], nb = knn(pc, K);
        ctx.strokeStyle = cLine; ctx.globalAlpha = .9;
        for (var j = 0; j < nb.length; j++) { line(pc, nb[j]); }
      }
      // highlighted stencil
      var pf = pts[focus], nbf = knn(pf, 9), pulse = .5 + .5 * Math.sin(s * 2.6);
      ctx.strokeStyle = cAcc; ctx.globalAlpha = .55 + .35 * pulse; ctx.lineWidth = 1.4;
      for (var k = 0; k < nbf.length; k++) line(pf, nbf[k]);
      ctx.globalAlpha = 1;
      for (var m = 0; m < pts.length; m++) dot(pts[m], 1.8, cInk, .55);
      for (k = 0; k < nbf.length; k++) dot(nbf[k], 2.6, cAcc, .9);
      dot(pf, 5 + 2 * pulse, cAcc, 1);
      ctx.globalAlpha = .18; dot(pf, 16 + 8 * pulse, cAcc, .18); ctx.globalAlpha = 1;
      if (!reduce) raf = requestAnimationFrame(frame);
    }
    function knn(p, k) {
      var best = [];
      for (var i = 0; i < pts.length; i++) {
        var q = pts[i]; if (q === p) continue;
        var d = (q.x - p.x) * (q.x - p.x) + (q.y - p.y) * (q.y - p.y);
        if (best.length < k || d < best[best.length - 1].d) {
          best.push({ q: q, d: d }); best.sort(function (a, b) { return a.d - b.d; }); if (best.length > k) best.pop();
        }
      }
      return best.map(function (b) { return b.q; });
    }
    function line(a, b) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
    function dot(p, r, c, a) { ctx.globalAlpha = a; ctx.fillStyle = c; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 6.2832); ctx.fill(); ctx.globalAlpha = 1; }
    function start() { cancelAnimationFrame(raf); colors(); seed(); raf = requestAnimationFrame(frame); }
    var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(start, 150); });
    window.addEventListener("themechange", function () { colors(); if (reduce) frame(performance.now()); });
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () { colors(); });
    document.addEventListener("visibilitychange", function () { if (document.hidden) cancelAnimationFrame(raf); else if (!reduce) raf = requestAnimationFrame(frame); });
    start();
  }
})();

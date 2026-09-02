(function () {
  'use strict';
  document.documentElement.classList.add('js');

  /* ── mobile drawer ── */
  var drawer = document.getElementById('drawer');
  var burger = document.getElementById('burger');
  var drawerClose = document.getElementById('drawerClose');
  var lastFocus = null;

  function openDrawer() {
    lastFocus = document.activeElement;
    drawer.classList.add('open');
    document.body.classList.add('nav-open');
    burger.setAttribute('aria-expanded', 'true');
    drawerClose.focus();
  }
  function closeDrawer() {
    if (!drawer || !drawer.classList.contains('open')) return;
    drawer.classList.remove('open');
    document.body.classList.remove('nav-open');
    burger.setAttribute('aria-expanded', 'false');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if (burger) burger.addEventListener('click', openDrawer);
  if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
  if (drawer) {
    drawer.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeDrawer);
    });
    drawer.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var items = drawer.querySelectorAll('a[href], button:not([disabled])');
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  /* ── language dropdown ── */
  var lang = document.getElementById('lang');
  var langBtn = document.getElementById('langBtn');
  function closeLang() {
    if (!lang) return;
    lang.classList.remove('open');
    langBtn.setAttribute('aria-expanded', 'false');
  }
  if (langBtn) {
    langBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = lang.classList.toggle('open');
      langBtn.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', function (e) {
      if (lang && !lang.contains(e.target)) closeLang();
    });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); closeLang(); }
  });

  /* ── scroll state ── */
  var nav = document.getElementById('nav');
  var backTop = document.getElementById('back-top');
  var docEl = document.documentElement;
  var ticking = false;

  /* Each in-page nav link paired with the section it points at. Resolved once:
     the scroll handler used to run a querySelector per link per frame. */
  var navAnchors = [];
  Array.prototype.forEach.call(
    document.querySelectorAll('.nav-links a[href^="#"]'), function (a) {
      var sec = document.querySelector(a.getAttribute('href'));
      if (sec) navAnchors.push({ a: a, sec: sec, top: 0 });
    });

  /* Reading offsetTop or scrollHeight forces the browser to lay the page out.
     Neither changes while the page merely scrolls, so both are taken here and
     not in the frame. */
  var run = 0;
  function measure() {
    run = docEl.scrollHeight - window.innerHeight;
    navAnchors.forEach(function (n) { n.top = n.sec.offsetTop; });
  }

  function onScroll() {
    var y = window.scrollY;
    if (nav) nav.classList.toggle('scrolled', y > 8);
    /* how far down the page we are, 0 to 1 — the nav's bottom edge is scaled
       by this, so the bar doubles as the progress indicator */
    docEl.style.setProperty('--scroll', run > 0 ? (y / run).toFixed(4) : '0');
    if (backTop) backTop.classList.toggle('visible', y > 600);
    var current = null;
    navAnchors.forEach(function (n) { if (y >= n.top - 140) current = n; });
    navAnchors.forEach(function (n) { n.a.classList.toggle('active', n === current); });
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  /* The page grows as the fonts land and images settle, so the measurement is
     taken again on resize and once the load is done. */
  window.addEventListener('resize', function () { measure(); onScroll(); });
  window.addEventListener('load', function () { measure(); onScroll(); });
  measure();
  onScroll();
  if (backTop) backTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── pointer spotlight on the tiled cards ──
     The pool of colour under the cursor is a CSS gradient centred on --mx/--my;
     all this does is keep those two numbers current. One listener per grid,
     coalesced into a frame, and only where there is a real pointer to follow. */
  if (!reduced && window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.line-grid').forEach(function (grid) {
      var frame = null;
      grid.addEventListener('pointermove', function (e) {
        if (frame) return;
        var card = e.target.closest ? e.target.closest('.line') : null;
        if (!card) return;
        var x = e.clientX, y = e.clientY;
        frame = requestAnimationFrame(function () {
          frame = null;
          var r = card.getBoundingClientRect();
          card.style.setProperty('--mx', ((x - r.left) / r.width * 100).toFixed(1) + '%');
          card.style.setProperty('--my', ((y - r.top) / r.height * 100).toFixed(1) + '%');
        });
      }, { passive: true });
    });
  }

  /* ── the build panels turn toward the pointer ──
     A panel tips away from wherever the pointer is on it: across the panel
     turns it about its vertical axis, down the panel about its horizontal
     one. Both are folded into the single axis-and-angle the CSS `rotate`
     property takes — at these angles the difference between that and two
     stacked rotations is not visible, and one property is one thing to
     transition. The turn is offered only where there is a pointer to
     follow and motion is welcome — a touch screen gets nothing. The
     capability wall is the same panel in another row, so it turns too. */
  var panels = document.querySelectorAll('.build, .svc');
  var canTurn = !reduced && window.matchMedia('(hover: hover)').matches;

  panels.forEach(function (card) {
    var frame = null;

    if (canTurn) {
      card.addEventListener('pointermove', function (e) {
        if (frame) return;
        var x = e.clientX, y = e.clientY;
        frame = requestAnimationFrame(function () {
          frame = null;
          var r = card.getBoundingClientRect();
          var ax = -((y - r.top) / r.height - 0.5) * 3;    /* rotation about x */
          var ay = ((x - r.left) / r.width - 0.5) * 4.5;  /* rotation about y */
          var ang = Math.sqrt(ax * ax + ay * ay);
          if (ang < 0.01) return;
          card.style.setProperty('--ax', ax.toFixed(3));
          card.style.setProperty('--ay', ay.toFixed(3));
          card.style.setProperty('--ang', ang.toFixed(2) + 'deg');
        });
      }, { passive: true });

      /* it settles back flat rather than snapping from wherever it was */
      card.addEventListener('pointerleave', function () {
        if (frame) { cancelAnimationFrame(frame); frame = null; }
        card.style.setProperty('--ang', '0deg');
      }, { passive: true });
    }

  });

  /* ── analytics, and the consent it waits for ──
     Nothing is loaded from Google until someone says yes: no tag, no cookie,
     no request carrying an IP address. The answer is kept per browser, the
     banner is only built for a visitor who has not given one, and the footer
     link reopens it so a yes can be taken back. */
  var CONSENT_KEY = 'gd-consent';
  var GA_ID = document.documentElement.getAttribute('data-ga');

  function remember(value) {
    try { localStorage.setItem(CONSENT_KEY, value); } catch (err) { /* private mode */ }
  }
  function recall() {
    try { return localStorage.getItem(CONSENT_KEY); } catch (err) { return null; }
  }

  var loaded = false;
  function loadAnalytics() {
    if (loaded || !GA_ID) return;
    loaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    gtag('js', new Date());
    gtag('config', GA_ID, { anonymize_ip: true });
  }

  var banner = document.getElementById('consent');
  var reopener = null;

  /* Focus moves only when the notice was asked for. On first load it appears
     without taking the caret: it is a region, not a modal, and a page that
     grabs focus as it opens is a page a keyboard has to climb back out of. */
  function showBanner(from) {
    if (!banner) return;
    reopener = from || null;
    banner.hidden = false;
    if (from) document.getElementById('consentAccept').focus();
  }
  function answer(value) {
    remember(value);
    if (banner) banner.hidden = true;
    if (value === 'granted') loadAnalytics();
    /* hand the caret back to whatever opened this, rather than to the top */
    if (reopener && reopener.focus) reopener.focus();
    reopener = null;
  }

  if (banner) {
    document.getElementById('consentAccept')
      .addEventListener('click', function () { answer('granted'); });
    document.getElementById('consentDecline')
      .addEventListener('click', function () { answer('denied'); });
  }
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-consent-reopen]'), function (b) {
      b.addEventListener('click', function (e) { e.preventDefault(); showBanner(b); });
    });

  var answered = recall();
  if (answered === 'granted') loadAnalytics();
  else if (answered !== 'denied') showBanner();
})();

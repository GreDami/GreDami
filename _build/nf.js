(function () {
  'use strict';

  /* ── the address that failed ──
     GitHub Pages hands 404.html back for /nonsense, /fr/nonsense and
     /a/b/c/nonsense alike without changing the address in the bar, so the page
     can read what was asked for and answer it. Two things are done with it:
     the address is set out with the part this site has no page for underlined,
     and it is measured against every real page so the nearest one can be
     offered. Both are written into the page here rather than served in it —
     the file is one static page answering forty thousand possible addresses,
     and only the browser knows which one it is answering. */

  var addr = document.getElementById('nf-addr');
  if (!addr) return;

  /* Every page on the site, in every language, as the site addresses them. */
  var PAGES = __PAGES__;
  var LANGS = __LANGS__;

  /* Opened from disk there is no address to report, and the readout stays
     away rather than showing a file path from someone's downloads folder. */
  if (location.protocol.indexOf('http') !== 0) return;

  var raw;
  try { raw = decodeURIComponent(location.pathname); }
  catch (err) { raw = location.pathname; }

  /* the form the site links in: no trailing slash, no .html, no index */
  function tidy(p) {
    p = p.replace(/\/+/g, '/');
    if (p.slice(-11) === '/index.html') p = p.slice(0, -10);
    else if (p.slice(-5) === '.html') p = p.slice(0, -5);
    if (p.length > 1 && p.slice(-1) === '/') p = p.slice(0, -1);
    return p;
  }

  var path = tidy(raw);
  var low = path.toLowerCase();

  /* /404 reached on purpose, or the home page somehow — there is no wrong
     address to point at, so the card is left out entirely. The comparison
     against the real pages is case-sensitive on purpose: /Services is a miss
     on GitHub Pages, and answering it with the page it so nearly is is exactly
     the job here. */
  if (low === '' || low === '/' || low === '/404') return;
  for (var i = 0; i < PAGES.length; i++) if (tidy(PAGES[i].p) === path) return;

  var segs = path.split('/').filter(Boolean);
  if (!segs.length) return;

  /* What of the address the site does recognise is left unmarked, and only the
     part it cannot place carries the underline. A language folder counts; so
     does a whole page the address then goes on past — /methodology/step-1 is a
     deep link into a page that exists, and the page is the answer to it. */
  var lang = LANGS.indexOf(segs[0].toLowerCase()) > -1 ? segs[0].toLowerCase() : null;
  var kept = lang ? 1 : 0;
  var known = null;
  for (i = 0; i < PAGES.length; i++) {
    var pp = tidy(PAGES[i].p);
    if (pp.length < 2 || low.indexOf(pp.toLowerCase() + '/') !== 0) continue;
    var depth = pp.split('/').length - 1;
    if (depth > kept) { kept = depth; known = PAGES[i]; }
  }

  /* Built as text nodes, never as markup: this string comes from the address
     bar and anyone can put anything in it. */
  var url = document.getElementById('nf-url');
  function part(text, cls) {
    var s = document.createElement('span');
    if (cls) s.className = cls;
    s.textContent = text;
    url.appendChild(s);
  }
  var head = segs.slice(0, kept).map(function (s) { return '/' + s; }).join('');
  var tail = segs.slice(kept).map(function (s) { return '/' + s; }).join('');
  /* nothing but a language folder in an unknown case — there is no segment to
     underline, and a card pointing at nothing in particular is worse than none */
  if (!tail) return;
  if (tail.length > 90) tail = tail.slice(0, 90) + '…';
  part('gredami.com' + head, null);
  part(tail, 'nf-bad');
  addr.hidden = false;

  /* ── the nearest real page ──
     Edit distance over the part that failed. A typo, a plural, a word in the
     wrong language and a stale link to a page that has since been renamed all
     land close to the page that was meant; a genuinely unrelated address lands
     nowhere near one and is left without a suggestion rather than being sent
     somewhere arbitrary. */
  function lev(a, b) {
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i;
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1,
                          prev[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
      }
      for (j = 0; j <= b.length; j++) prev[j] = cur[j];
    }
    return prev[b.length];
  }
  function sim(a, b) {
    if (!a.length || !b.length) return 0;
    if (a === b) return 1;
    var m = Math.max(a.length, b.length);
    var s = 1 - lev(a, b) / m;
    /* One name inside the other — /our-services, /services-2024. The five
       characters are the whole of this rule: without them every address with
       an "ios" or an "app" buried in it matched a page it had nothing to do
       with, and /es/precios was answered with the apps. */
    if (Math.min(a.length, b.length) >= 5 && (a.indexOf(b) > -1 || b.indexOf(a) > -1)) {
      s = Math.max(s, 0.72);
    }
    return s;
  }

  function slug(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, ''); }

  var asked = slug(segs[segs.length - 1]);
  var best = known, bestScore = known ? 1 : 0;
  for (i = 0; !known && i < PAGES.length; i++) {
    var page = PAGES[i];
    var score = sim(asked, slug(page.p.split('/').pop()));
    /* The names a page is not called but is looked for under — /contact for
       the page that is filed as /start, /portfolio for the work. A link
       someone typed from memory is as much a miss as a typo, and it lands on
       the same suggestion. */
    for (var k = 0; k < page.k.length; k++) score = Math.max(score, sim(asked, page.k[k]));
    /* a page in the language the address was already in wins a tie */
    if (lang && page.g === lang) score += 0.06;
    else if (!lang && page.g === 'en') score += 0.06;
    if (score > bestScore) { bestScore = score; best = page; }
  }

  /* High enough that a word two edits away from a four-letter page name is not
     a match: /ru/o-nas is not the SaaS page, however close "onas" and "saas"
     look to an edit distance. Below the line nothing is offered, which is the
     honest answer to an address that means nothing here. */
  if (best && bestScore >= 0.58) {
    var link = document.getElementById('nf-guess-link');
    link.href = best.p;
    document.getElementById('nf-guess-label').textContent = best.l;
    document.getElementById('nf-guess').hidden = false;
  }
})();

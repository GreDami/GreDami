#!/usr/bin/env python3
"""
GreDami static site generator.

All copy lives in _build/site.json. Edit that file, then run:

    python3 _build/build.py

Sources in _build/ : site.json (all copy), site.css, site.js, contact.js
Writes: index.html, services.html, websites.html, apps.html, saas.html,
        methodology.html, start.html, the same seven under {fr,ru,es}/,
        sitemap.xml, robots.txt

Every generated page is self-contained — CSS, JS and the product icons are
inlined — so a page renders correctly when opened straight from disk. Safari
blocks file:// pages from loading local subresources; there are none to block.
"""
import json
import pathlib
import re
import html

import base64

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "_build" / "site.json").read_text(encoding="utf-8"))


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def data_uri(rel, mime):
    b64 = base64.b64encode((ROOT / rel).read_bytes()).decode("ascii")
    return "url(\"data:%s;base64,%s\")" % (mime, b64)


# Everything is inlined so a page works when opened straight from disk.
# Safari blocks a file:// page from loading local subresources; a self-contained
# page has none to block.
CSS = (":root{\n  --ic-gobag: " + data_uri("gobag-icon.webp", "image/webp") + ";\n"
       "  --ic-fw: " + data_uri("FW.webp", "image/webp") + ";\n"
       "  --ic-mark: " + data_uri("halo-mark.svg", "image/svg+xml") + ";\n}\n\n"
       + read("_build/site.css"))
# The hero photograph is heavy, and only the home page has a hero — it is
# inlined on that page alone rather than in the shared block.
HERO_CSS = ":root{\n  --img-hero: " + data_uri("halo-hero.webp", "image/webp") + ";\n}\n"
SITE_JS = read("_build/site.js")
CONTACT_JS = read("_build/contact.js")


# The favicon is the company mark itself, so the two can never drift apart:
# the same bird on a square field with a little air around it, and lighter
# blues under a dark tab strip, where the deep gradient sinks into the chrome.
def favicon_svg():
    # square off the mark's own box and leave a margin, so the bird never
    # touches the edge of a tab whatever the drawing grows into
    s = read("halo-mark.svg")
    m = re.search(r'viewBox="([-\d. ]+)"', s)
    x, y, w, h = (float(v) for v in m.group(1).split())
    side = max(w, h) + 2.4
    box = 'viewBox="%.2f %.2f %.2f %.2f"' % (
        x + w / 2 - side / 2, y + h / 2 - side / 2, side, side)
    s = s.replace(m.group(0), box, 1)
    return s.replace("<defs>", """<style>
    @media (prefers-color-scheme: dark) {
      .s0 { stop-color: #7DA0FF; }
      .s1 { stop-color: #8C86F2; }
      .s2 { stop-color: #A98BFA; }
      .s3 { fill: #A78BFA; stroke: #A78BFA; }
    }
  </style>
  <defs>""", 1)


FAVICON_SVG = favicon_svg()
FAVICON = "data:image/svg+xml;base64," + base64.b64encode(
    FAVICON_SVG.encode("utf-8")).decode("ascii")

LANGS = ["en", "fr", "ru", "es"]
# the pages that are not the home page, by file name
CONTACT = "start.html"
SERVICES = "services.html"
METHOD = "methodology.html"
# The work is not one shelf but three, because websites, apps and SaaS are
# three different things to commission: each kind gets its own page, reached
# from the card on the home page that offers to build that kind of thing.
CAT_PAGE = {"sites": "websites.html", "apps": "apps.html", "saas": "saas.html"}
CATS = ["sites", "apps", "saas"]
SITE = "https://gredami.com"
EMAIL = "contact@gredami.com"
LOCALE = {"en": "en_US", "fr": "fr_FR", "ru": "ru_RU", "es": "es_ES"}


def base(lang):
    """URL prefix for a language. English is the site root."""
    return "/" if lang == "en" else "/" + lang + "/"


def e(s):
    return html.escape(str(s), quote=True)


def url(lang, page):
    """Absolute URL — for canonical, hreflang and the sitemap only."""
    return SITE + base(lang).rstrip("/") + ("/" + page if page else "/")


def up(lang):
    """How far to climb to reach the site root from a page in this language."""
    return "" if lang == "en" else "../"


def href(from_lang, to_lang, page="index.html"):
    """Relative link between two pages. Works on file://, in subdirectories
    and when deployed, which a leading-slash path does not."""
    dir_part = up(from_lang) + ("" if to_lang == "en" else to_lang + "/")
    if page == "index.html":
        # Link to the directory, not the literal file, so the address bar
        # doesn't pick up a visible /index.html when the link is followed.
        return dir_part or "./"
    return dir_part + page


def asset(lang, path):
    return up(lang) + path.lstrip("/")


def alternates(page):
    rows = []
    for l in LANGS:
        rows.append('  <link rel="alternate" hreflang="' + l + '" href="' + url(l, page) + '" />')
    rows.append('  <link rel="alternate" hreflang="x-default" href="' + url("en", page) + '" />')
    return "\n".join(rows)


def lang_links(lang, page, indent):
    rows = []
    for l in LANGS:
        cur = ' aria-current="true"' if l == lang else ""
        rows.append(
            indent + '<a href="' + href(lang, l, page or "index.html") + '" hreflang="' + l
            + '" lang="' + l + '"' + cur + ">" + e(T[l]["lang.name"]) + "</a>"
        )
    return "\n".join(rows)


# ── head ────────────────────────────────────────────────────────────────
def head(lang, page, title, desc, extra=""):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)}</title>

  <script async src="https://www.googletagmanager.com/gtag/js?id=G-HCXQ2KD3SZ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-HCXQ2KD3SZ');
  </script>

  <link rel="icon" type="image/svg+xml" href="{FAVICON}">
  <link rel="mask-icon" href="{FAVICON}" color="#5B21B6">
  <meta name="theme-color" content="#FAFAF8">

  <meta name="description" content="{e(desc)}" />
  <meta name="author" content="GreDami" />
  <meta name="robots" content="{"noindex, follow" if page == CONTACT else "index, follow"}" />
  <link rel="canonical" href="{url(lang, page)}" />
{alternates(page)}

  <meta property="og:type" content="website" />
  <meta property="og:url" content="{url(lang, page)}" />
  <meta property="og:site_name" content="GreDami" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:image" content="{SITE}/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:locale" content="{LOCALE[lang]}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(title)}" />
  <meta name="twitter:description" content="{e(desc)}" />
  <meta name="twitter:image" content="{SITE}/og-image.png" />
  <meta name="google" content="notranslate" />
{extra}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,500;0,600;0,700;0,800;1,500;1,600&display=swap" rel="stylesheet">
  <style>\n{HERO_CSS if page == '' else ''}{CSS}\n  </style>
  <script>document.documentElement.classList.add('js');</script>
</head>

<body>
"""


# ── nav + drawer ────────────────────────────────────────────────────────
def nav(lang, page, t):
    home = href(lang, lang, "index.html")
    anchor = (lambda a: "#" + a) if page == "" else (lambda a: home + "#" + a)
    # Home leads the menu: an in-page jump on the home page, a link back to it
    # from anywhere else. Work and the methodology keep pages of their own, but
    # they are reached from the about section and the footer, not from the menu.
    items = [
        ("#hero" if page == "" else home, "nav.home", False),
        (anchor("build"), "nav.build", False),
        (href(lang, lang, SERVICES), "nav.services", page == SERVICES),
        (anchor("about"), "nav.about", False),
    ]

    def links(indent):
        return "\n".join(
            indent + '<li><a href="' + h + '"' + (' aria-current="page"' if cur else "")
            + ">" + e(t[k]) + "</a></li>" for h, k, cur in items)

    navlinks = links("        ")
    drawerlinks = links("      ")

    return f"""  <a class="skip" href="#main">{e(t["a11y.skip"])}</a>

  <nav id="nav">
    <div class="nav-in">
      <a href="{home}" class="nav-logo"><span class="nav-mark" aria-hidden="true"></span><span>Gre<em>Dami</em></span></a>

      <ul class="nav-links">
{navlinks}
      </ul>

      <div class="nav-tools">
        <a href="{href(lang, lang, CONTACT)}" class="nav-cta">{e(t["cta.getStarted"])} <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></a>

        <div class="lang" id="lang">
          <button class="lang-btn" id="langBtn" aria-haspopup="true" aria-expanded="false" aria-label="{e(t["a11y.lang"])}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 8l6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>
            <span>{e(t["lang.code"])}</span>
          </button>
          <div class="lang-menu" id="langMenu">
{lang_links(lang, page, "            ")}
          </div>
        </div>

        <button class="icon-btn burger" id="burger" aria-expanded="false" aria-controls="drawer" aria-label="{e(t["a11y.menu"])}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
        </button>
      </div>
    </div>
  </nav>
  <div class="nav-spacer"></div>

  <div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="{e(t["a11y.menu"])}">
    <div class="drawer-top">
      <span class="nav-logo"><span class="nav-mark" aria-hidden="true"></span><span>Gre<em>Dami</em></span></span>
      <button class="icon-btn" id="drawerClose" aria-label="{e(t["a11y.close"])}">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <ul class="drawer-links">
{drawerlinks}
    </ul>
    <a href="{href(lang, lang, "start.html")}" class="drawer-cta">{e(t["cta.start"])}</a>
    <a href="{href(lang, lang, CONTACT)}" class="drawer-cta ghost">{e(t["cta.getStarted"])}</a>
    <div class="drawer-langs">
{lang_links(lang, page, "      ")}
    </div>
  </div>
"""


# ── footer ──────────────────────────────────────────────────────────────
YOUTUBE = '<svg width="17" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>'
INSTAGRAM = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>'


def footer(lang, t, extra_js=""):
    home = href(lang, lang, "index.html")
    svc = href(lang, lang, SERVICES)
    cat_links = "\n".join(
        '        <a href="' + href(lang, lang, CAT_PAGE[k]) + '">'
        + e(t["proj.cat." + k]) + "</a>" for k in CATS)
    return f"""  <footer>
    <div class="footer-in">
      <div>
        <span class="footer-logo">Gre<em>Dami</em></span>
        <p class="footer-tagline">{e(t["footer.tagline"])}</p>
        <div class="footer-social">
          <a href="https://www.youtube.com/@GreDami" aria-label="GreDami · YouTube" target="_blank" rel="noopener">{YOUTUBE}</a>
          <a href="https://www.instagram.com/gredami/" aria-label="GreDami · Instagram" target="_blank" rel="noopener">{INSTAGRAM}</a>
        </div>
      </div>

      <div class="footer-col">
        <p class="footer-col-lbl">{e(t["footer.servicesLabel"])}</p>
        <a href="{svc}">{e(t["sp.3.name"])}</a>
        <a href="{svc}">{e(t["sp.2.name"])}</a>
        <a href="{svc}">{e(t["sp.4.name"])}</a>
        <a href="{svc}">{e(t["sp.1.name"])}</a>
        <a href="{svc}">{e(t["sp.5.name"])}</a>
      </div>

      <div class="footer-col">
        <p class="footer-col-lbl">{e(t["footer.workLabel"])}</p>
{cat_links}
        <a href="https://apps.apple.com/app/id6760232332" target="_blank" rel="noopener">GoBag+</a>
        <a href="https://apps.apple.com/app/id6767314346" target="_blank" rel="noopener">FinWall</a>
        <a href="https://lokalshot.com" target="_blank" rel="noopener">LokalShot</a>
      </div>

      <div class="footer-col">
        <p class="footer-col-lbl">{e(t["footer.companyLabel"])}</p>
        <a href="{home}#about">{e(t["nav.about"])}</a>
        <a href="{href(lang, lang, METHOD)}">{e(t["nav.process"])}</a>
        <a href="{href(lang, lang, "start.html")}">{e(t["cta.start"])}</a>
      </div>
    </div>

    <div class="footer-bottom">
      <span>{e(t["footer.copy"])}</span>
      <span class="footer-tag">{e(t["footer.tag"])}</span>
    </div>
  </footer>

  <button id="back-top" aria-label="{e(t["a11y.backTop"])}">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 12.5V4M3.5 8.5 8 4l4.5 4.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>

  <script>\n{SITE_JS}\n  </script>{extra_js}
</body>
</html>
"""


ARROW = '<svg width="15" height="15" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ARROW_SM = '<svg width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
EXT = '<svg width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M3 11 11 3M5 3h6v6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
LOKALSHOT_SVG = """<svg class="proj-icon" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LokalShot">
                    <defs><linearGradient id="ls" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
                    <rect width="64" height="64" fill="url(#ls)"/>
                    <rect x="18" y="10" width="12" height="44" rx="6" fill="white"/>
                    <rect x="18" y="42" width="32" height="12" rx="6" fill="white"/>
                  </svg>"""


SLUG = {"gobag-icon": "gobag", "FW": "fw"}


def icon(stem, alt, cls="work-icon", size=78, lang="en"):
    """Product mark drawn from an embedded data URI, so nothing is fetched."""
    classes = (cls + " " if cls else "") + "pic pic-" + SLUG[stem]
    label = f' role="img" aria-label="{e(alt)}"' if alt else ' aria-hidden="true"'
    return f'<span class="{classes.strip()}"{label}></span>' 


# ── the shelf, in three kinds ───────────────────────────────────────────
# Websites, apps and SaaS are three different things to commission, so they are
# three different things on the page: a site is shown inside a browser frame,
# because a site is a thing you look at; an app or a platform gets a fact
# sheet, because those are things you check the specifications of. Each kind
# numbers its own entries from one.

SITES_DATA = [
    # slug, address-bar markup (the bold run is the name), url, mark, chips
    ("gobag", "<b>gobag</b>.gredami.com", "https://gobag.gredami.com",
     "gobag-icon", ["chip.responsive", "SEO", "chip.ownDomain"]),
    ("finwall", "gredami.github.io/<b>FinWall</b>", "https://gredami.github.io/FinWall",
     "FW", ["chip.responsive", "SEO", "chip.staticHost"]),
]

# slug, name, platform chips, links, mark, the site on this page that is its own
APPS_DATA = [
    ("gobag", "GoBag+", ["iOS", "macOS", "Web"],
     [("link.appStore", "https://apps.apple.com/app/id6760232332")], "gobag-icon", "gobag"),
    ("finwall", "FinWall", ["iOS", "Web"],
     [("link.appStore", "https://apps.apple.com/app/id6767314346")], "FW", "finwall"),
]

SAAS_DATA = [
    ("lokalshot", "LokalShot", ["Web", "chip.cloudSync"],
     [("link.tool", "https://lokalshot.com")], None, None),
]


def chip_text(t, c):
    """Most chips are platform names, which do not translate. The few that are
    words rather than names arrive as a copy key instead."""
    return e(t[c]) if c in t else e(c)


def chips_html(t, chips):
    return "".join('<span class="chip">' + chip_text(t, c) + "</span>" for c in chips)


def site_card(lang, t, slug, urlbar, site_url, mark, chips):
    """A website, shown the way you meet one: a window with the real address in
    the bar and a drawing of the page behind it. Drawn, not screenshotted — it
    is a diagram of the layout and never pretends to be a photograph of one."""
    k = "site." + slug + "."
    return f"""              <article class="site reveal" id="site-{slug}">
                <div class="site-frame">
                  <div class="chrome">
                    <div class="chrome-bar">
                      <div class="chrome-dots" aria-hidden="true"><i></i><i></i><i></i></div>
                      <span class="chrome-url">{urlbar}</span>
                    </div>
                    <div class="mini" aria-hidden="true">
                      <div class="mini-nav">
                        {icon(mark, None, cls="mini-mark", lang=lang)}
                        <span class="mini-links"><i></i><i></i><i></i></span>
                      </div>
                      <div class="mini-hero">
                        <span class="mini-h">{e(t[k + "mini"])}</span>
                        <div class="mini-lines"><span></span><span></span></div>
                        <span class="mini-btn"></span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="site-body">
                  <div class="site-top">
                    <h3 class="site-name">{e(t[k + "name"])}</h3>
                    <span class="badge">{e(t["badge.live"])}</span>
                  </div>
                  <p class="site-desc">{e(t[k + "desc"])}</p>
                  <div class="site-job">
                    <b>{e(t["site.jobLabel"])}</b>
                    {e(t[k + "job"])}
                  </div>
                  <div class="site-foot">
                    <div class="site-chips">{chips_html(t, chips)}</div>
                    <a class="work-link" href="{site_url}" target="_blank" rel="noopener"><span>{e(t["link.visit"])}</span> {EXT}</a>
                  </div>
                </div>
              </article>"""


def proj_card(lang, t, n, slug, name, chips, links, mark, site_slug):
    """One product, told in full: a header strip carrying its number, category
    and status, then the story on the left and the facts on the right."""
    k = "proj." + slug + "."
    ic = LOKALSHOT_SVG if mark is None else icon(mark, name, cls="proj-icon", lang=lang)
    points = "\n".join(
        '                      <li>' + e(t[k + p]) + "</li>" for p in ["p1", "p2", "p3"])
    link_html = "\n".join(
        '                      <a class="work-link" href="' + h + '" target="_blank" rel="noopener">'
        + "<span>" + e(t[key]) + "</span> " + EXT + "</a>" for key, h in links)
    # a product whose website is also ours says so, and takes you to it on the
    # websites page — the two kinds no longer share one page to scroll within
    if site_slug:
        link_html += ("\n                      <a class=\"proj-xref\" href=\""
                      + href(lang, lang, CAT_PAGE["sites"]) + "#site-" + site_slug
                      + "\">" + ARROW_SM + " <span>"
                      + e(t["proj.xref.site"]) + "</span></a>")
    return f"""              <article class="proj reveal" id="{slug}">
                <div class="proj-bar">
                  <span class="proj-n">{n:02d}</span>
                  <span class="proj-cat">{e(t[k + "cat"])}</span>
                  <span class="badge">{e(t["badge.released"])}</span>
                </div>

                <div class="proj-body">
                  <div class="proj-main">
                    <div class="proj-id">
                      {ic}
                      <div>
                        <h3 class="proj-name">{name}</h3>
                        <p class="proj-tagline">{e(t["work." + slug + ".tagline"])}</p>
                      </div>
                    </div>
                    <p class="proj-desc">{e(t["work." + slug + ".desc"])}</p>
                    <ul class="proj-points">
{points}
                    </ul>
                  </div>

                  <aside class="proj-aside">
                    <div class="proj-fact">
                      <p class="proj-fact-lbl">{e(t["work.outcomeLabel"])}</p>
                      <p class="proj-fact-val">{e(t["work." + slug + ".outcome"])}</p>
                    </div>
                    <div class="proj-fact">
                      <p class="proj-fact-lbl">{e(t["proj.roleLabel"])}</p>
                      <p class="proj-fact-val">{e(t["proj.role"])}</p>
                    </div>
                    <div class="proj-fact">
                      <p class="proj-fact-lbl">{e(t["proj.platformsLabel"])}</p>
                      <div class="proj-chips">{chips_html(t, chips)}</div>
                    </div>
                    <div class="work-links">
{link_html}
                    </div>
                  </aside>
                </div>
              </article>"""


# key -> the "what we build" card that offers this kind of work, so the shelf
# and the offer to build another one are always worded the same way
BUILD_OF = {"sites": "web", "apps": "app", "saas": "saas"}
CAT_WRAP = {"sites": "site-grid", "apps": "proj-list", "saas": "proj-list"}


def cat_cards(lang, t, key):
    """The shelf for one kind, numbered from one — each page counts its own."""
    if key == "sites":
        return "\n\n".join(site_card(lang, t, *c) for c in SITES_DATA)
    data = APPS_DATA if key == "apps" else SAAS_DATA
    return "\n\n".join(
        proj_card(lang, t, i + 1, *c) for i, c in enumerate(data))


def cat_more(lang, t, key):
    """The two shelves this page is not. Someone weighing a site against an app
    is choosing between the three kinds, so the crossing is offered here rather
    than sending them back to the home page to find it."""
    links = "\n".join(
        '            <a class="build-link" href="' + href(lang, lang, CAT_PAGE[k])
        + '">\n              <span>' + e(t["build." + BUILD_OF[k] + ".cta"])
        + "</span> " + ARROW_SM + "\n            </a>"
        for k in CATS if k != key)
    return f"""        <div class="group-head reveal" style="margin-top:clamp(56px,7vw,92px);">
          <div class="group-kind">
            <h2 class="group-title">{e(t["cat.more"])}</h2>
          </div>
          <div class="sp-actions" style="margin-top:0;gap:28px;">
{links}
          </div>
        </div>"""


def steps_html(t):
    steps = ""
    for n in ["1", "2", "3", "4", "5"]:
        steps += f"""          <article class="step reveal">
            <p class="step-n">0{n}</p>
            <h3>{e(t["proc." + n + ".title"])}</h3>
            <p>{e(t["proc." + n + ".desc"])}</p>
          </article>

"""
    return steps


def final_cta(lang, t, sec_href, sec_key):
    """Closing call to action — the same block on the home page and on the
    pages that carry the work and the methodology."""
    return f"""    <section id="contact">
      <div class="shell">
        <div class="final-cta reveal">
          <span class="eyebrow">{e(t["contact.label"])}</span>
          <h2 class="final-title">{e(t["contact.title"])}</h2>
          <p class="final-sub">{e(t["contact.sub"])}</p>
          <p class="final-body">{e(t["contact.body"])}</p>
          <div class="final-actions">
            <a href="{href(lang, lang, CONTACT)}" class="btn btn-primary">
              <span>{e(t["cta.start"])}</span> {ARROW}
            </a>
            <a href="{sec_href}" class="btn btn-ghost">{e(t[sec_key])}</a>
          </div>
          <p class="final-note">{e(t["contact.note"])}</p>
        </div>
      </div>
    </section>

"""


def sub_page(lang, page, keys, inner, sec_page, sec_key):
    """A section that used to live on the home page, given a page of its own:
    lead-in, the section itself, then the same closing call to action."""
    t = T[lang]
    label, title, desc, meta_title, meta_desc = keys
    body = f"""
  <main id="main">

    <section>
      <div class="shell">
        <div class="page-head">
          <span class="eyebrow" style="display:block;margin-bottom:16px;">{e(t[label])}</span>
          <h1 class="page-title">{e(t[title])}</h1>
          <p class="page-sub">{e(t[desc])}</p>
        </div>

{inner}
      </div>
    </section>

{final_cta(lang, t, href(lang, lang, sec_page), sec_key)}  </main>

"""
    return (head(lang, page, t[meta_title], t[meta_desc])
            + nav(lang, page, t) + body + footer(lang, t))


def services_page(lang):
    """The services page: the six lines of work as a card wall, then the five
    stages of a project laid out vertically, then the usual closing CTA."""
    t = T[lang]
    nums = ["1", "2", "3", "4", "5", "6"]

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "OfferCatalog",
        "name": t["sp.title"],
        "url": url(lang, SERVICES),
        "description": t["sp.desc"],
        "provider": {"@type": "ProfessionalService", "name": "GreDami",
                     "url": url(lang, ""), "email": EMAIL},
        "itemListElement": [
            {"@type": "Offer", "position": int(n),
             "itemOffered": {"@type": "Service",
                             "name": t["sp." + n + ".name"],
                             "category": t["sp." + n + ".cat"],
                             "description": t["sp." + n + ".desc"]}}
            for n in nums],
    }, ensure_ascii=False, indent=2)

    svc_cards = ""
    for n in nums:
        k = "sp." + n + "."
        items = "\n".join(
            "              <li>" + e(i) + "</li>" for i in t[k + "items"])
        svc_cards += f"""          <article class="line reveal">
            <p class="line-cat">{e(t[k + "cat"])}</p>
            <h3>{e(t[k + "name"])}</h3>
            <p class="line-desc">{e(t[k + "desc"])}</p>
            <ul class="line-list">
{items}
            </ul>
            <a class="line-link" href="{href(lang, lang, CONTACT)}">
              <span>{e(t["sp.learn"])}</span> {ARROW_SM}
            </a>
          </article>

"""

    stages = ""
    for n in ["1", "2", "3", "4", "5"]:
        stages += f"""          <article class="stage reveal">
            <p class="stage-n">0{n}</p>
            <div>
              <h3>{e(t["proc." + n + ".title"])}</h3>
              <p>{e(t["proc." + n + ".desc"])}</p>
            </div>
          </article>

"""

    body = f"""
  <main id="main">

    <section>
      <div class="shell">
        <div class="page-head">
          <span class="eyebrow" style="display:block;margin-bottom:16px;">{e(t["sp.label"])}</span>
          <h1 class="page-title">{e(t["sp.title"])}</h1>
          <p class="sp-sub">{e(t["sp.sub"])}</p>
          <p class="page-sub">{e(t["sp.desc"])}</p>
          <div class="sp-actions">
            <a href="{href(lang, lang, CONTACT)}" class="btn btn-primary">
              <span>{e(t["cta.start"])}</span> {ARROW}
            </a>
            <a href="{href(lang, lang, METHOD)}" class="btn btn-ghost">{e(t["cta.methodology"])}</a>
          </div>
        </div>

        <div class="line-grid">
{svc_cards.rstrip()}
        </div>
      </div>
    </section>

    <section id="blueprint">
      <div class="shell">
        <div class="sec-head">
          <span class="eyebrow">{e(t["sp.blue.label"])}</span>
          <h2 class="sec-title">{e(t["sp.blue.title"])}</h2>
          <p class="sec-desc">{e(t["sp.blue.desc"])}</p>
        </div>

        <div class="stages">
{stages.rstrip()}
        </div>

        <div class="stages-note">
          <a class="build-link" href="{href(lang, lang, METHOD)}">
            <span>{e(t["sp.blue.cta"])}</span> {ARROW_SM}
          </a>
        </div>
      </div>
    </section>

{final_cta(lang, t, href(lang, lang, METHOD), "cta.methodology")}  </main>

"""
    extra = '\n  <script type="application/ld+json">\n' + ld + "\n  </script>\n"
    return (head(lang, SERVICES, t["sp.meta.title"], t["sp.meta.desc"], extra)
            + nav(lang, SERVICES, t) + body + footer(lang, t))


SVC_ICONS = [
    '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 14.9 9l6.5.6-4.9 4.3 1.5 6.4L12 16.9 6 20.3l1.5-6.4L2.6 9.6 9.1 9z"/></svg>',
    '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18.5h2"/></svg>',
    '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.2"/><path d="M2.8 12h18.4M12 2.8a14.5 14.5 0 0 1 0 18.4M12 2.8a14.5 14.5 0 0 0 0 18.4"/></svg>',
    '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17.5 9 11l4 4 7.5-7.5"/><path d="M15 7.5h5.5V13"/></svg>',
]

# key, the chips under it — technical names, so they stay in English everywhere
SVC_DATA = [
    ("design", ["UI systems", "App icons", "Screenshots", "Accessibility"]),
    ("ios",    ["SwiftUI", "iCloud", "StoreKit", "App Store"]),
    ("web",    ["Product sites", "Web apps", "Auth &amp; billing", "Analytics"]),
    ("growth", ["ASO", "SEO", "Localization", "Analytics"]),
]

# ── home page ───────────────────────────────────────────────────────────
def home(lang):
    t = T[lang]

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": "GreDami",
        "url": url(lang, ""),
        "logo": SITE + "/favicon.svg",
        "image": SITE + "/og-image.png",
        "description": t["footer.tagline"],
        "email": EMAIL,
        "knowsAbout": ["iOS Development", "SwiftUI", "Web Development", "SaaS",
                       "Product Design", "App Store Optimization", "Localization"],
        "availableLanguage": LANGS,
    }, ensure_ascii=False, indent=2)

    build_cards = ""
    for i, cat in enumerate(CATS):
        k = BUILD_OF[cat]
        build_cards += f"""          <article class="build reveal">
            <p class="build-n">0{i + 1}</p>
            <h3>{e(t["build." + k + ".name"])}</h3>
            <p>{e(t["build." + k + ".desc"])}</p>
            <a class="build-link" href="{href(lang, lang, CAT_PAGE[cat])}">
              <span>{e(t["build." + k + ".cta"])}</span> {ARROW_SM}
            </a>
          </article>

"""

    svc_cards = ""
    for i, (k, chips) in enumerate(SVC_DATA):
        chip_html = "".join('<span class="chip">' + c + "</span>" for c in chips)
        svc_cards += f"""          <article class="svc reveal">
            <div class="svc-icon">
              {SVC_ICONS[i]}
            </div>
            <h3>{e(t["svc." + k + ".name"])}</h3>
            <p>{e(t["svc." + k + ".desc"])}</p>
            <div class="svc-chips">{chip_html}</div>
          </article>

"""

    body = f"""
  <main id="main">

    <section id="hero">
      <span class="hero-glow" aria-hidden="true"></span>
      <div class="shell">
        <div class="hero-inner">
        <h1 class="hero-title">{t["hero.title"]}</h1>

        <div class="hero-body">
          <p class="hero-sub">{e(t["hero.sub"])}</p>
          <div class="hero-cta">
            <a href="{href(lang, lang, CONTACT)}" class="btn btn-primary">
              <span>{e(t["cta.explore"])}</span> {ARROW}
            </a>
            <a href="{href(lang, lang, METHOD)}" class="btn btn-ghost">{e(t["cta.methodology"])}</a>
          </div>
        </div>
        </div>

        <div class="hero-proof">
          <span>{e(t["hero.proof1"])}</span>
          <span>{e(t["hero.proof2"])}</span>
        </div>
      </div>
    </section>

    <section id="build">
      <div class="shell">
        <div class="sec-head">
          <span class="eyebrow">{e(t["build.label"])}</span>
          <h2 class="sec-title">{e(t["build.title"])}</h2>
          <p class="sec-desc">{e(t["build.desc"])}</p>
        </div>
        <div class="build-grid">
{build_cards.rstrip()}
        </div>
      </div>
    </section>

    <div class="shell"><div class="rule"></div></div>

    <section id="services">
      <div class="shell">
        <div class="sec-head">
          <span class="eyebrow">{e(t["svc.label"])}</span>
          <h2 class="sec-title">{e(t["svc.title"])}</h2>
          <p class="sec-desc">{e(t["svc.desc"])}</p>
        </div>
        <div class="svc-grid">
{svc_cards.rstrip()}
        </div>
        <div class="stages-note">
          <a class="build-link" href="{href(lang, lang, SERVICES)}">
            <span>{e(t["cta.allServices"])}</span> {ARROW_SM}
          </a>
        </div>
      </div>
    </section>

    <div class="shell"><div class="rule"></div></div>

    <section id="about">
      <div class="shell">
        <div class="reveal">
          <span class="eyebrow" style="display:block;margin-bottom:14px;">{e(t["about.label"])}</span>
          <h2 class="about-title">{t["about.title"]}</h2>
          <p class="about-desc">{e(t["about.desc"])}</p>
        </div>
      </div>
    </section>

{final_cta(lang, t, href(lang, lang, METHOD), "cta.methodology")}  </main>

"""
    extra = '\n  <script type="application/ld+json">\n' + ld + "\n  </script>\n"
    return (head(lang, "", t["meta.title"], t["footer.tagline"], extra)
            + nav(lang, "", t) + body + footer(lang, t))


def cat_ld(lang, key, page, t):
    """Structured data for one shelf: a site is a WebSite, an app or a platform
    is a SoftwareApplication, and each page lists only its own kind."""
    items = []
    if key == "sites":
        for c in SITES_DATA:
            items.append({"@type": "WebSite",
                          "name": t["site." + c[0] + ".name"],
                          "url": c[2],
                          "description": t["site." + c[0] + ".desc"]})
    else:
        for c in (APPS_DATA if key == "apps" else SAAS_DATA):
            items.append({"@type": "SoftwareApplication",
                          "name": c[1],
                          "applicationCategory": t["proj." + c[0] + ".cat"],
                          "operatingSystem": ", ".join(
                              chip_text(t, ch) for ch in c[2]),
                          "description": t["work." + c[0] + ".desc"],
                          "url": c[3][0][1]})
    author = {"@type": "Organization", "name": "GreDami", "url": url(lang, "")}
    listed = [{"@type": "ListItem", "position": n + 1,
               "item": dict(it, author=author)} for n, it in enumerate(items)]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": t["cat." + key + ".title"],
        "url": url(lang, page),
        "description": t["proj.g." + key + ".desc"],
        "mainEntity": {"@type": "ItemList", "itemListElement": listed},
    }, ensure_ascii=False, indent=2)


def cat_page(lang, key):
    """One kind of work, on a page of its own: the lead with the tally on it,
    the shelf, then the crossing to the other two kinds and the closing call."""
    t = T[lang]
    page = CAT_PAGE[key]
    k = "cat." + key + "."
    n = len(SITES_DATA if key == "sites" else
            APPS_DATA if key == "apps" else SAAS_DATA)
    count = t["proj.g." + key + ".count"].replace("{n}", str(n))

    body = f"""
  <main id="main">

    <section>
      <div class="shell">
        <div class="page-head">
          <div class="group-kind" style="margin-bottom:16px;">
            <span class="eyebrow">{e(t[k + "label"])}</span>
            <span class="group-count">{e(count)}</span>
          </div>
          <h1 class="page-title">{e(t[k + "title"])}</h1>
          <p class="sp-sub">{e(t[k + "sub"])}</p>
          <p class="page-sub">{e(t["proj.g." + key + ".desc"])}</p>

          <div class="sp-actions">
            <a href="{href(lang, lang, CONTACT)}" class="btn btn-primary">
              <span>{e(t["cta.start"])}</span> {ARROW}
            </a>
            <a href="{href(lang, lang, SERVICES)}" class="btn btn-ghost">{e(t["cta.allServices"])}</a>
          </div>
        </div>

        <div class="groups">
          <div class="group" id="{key}">
            <div class="{CAT_WRAP[key]}">
{cat_cards(lang, t, key)}
            </div>
          </div>
        </div>

{cat_more(lang, t, key)}
      </div>
    </section>

{final_cta(lang, t, href(lang, lang, METHOD), "cta.methodology")}  </main>

"""
    extra = ('\n  <script type="application/ld+json">\n'
             + cat_ld(lang, key, page, t) + "\n  </script>\n")
    return (head(lang, page, t[k + "meta.title"], t[k + "meta.desc"], extra)
            + nav(lang, page, t) + body + footer(lang, t))


def method_page(lang):
    t = T[lang]
    # the run sits on a tinted band that carries the ink-to-warm gradient the
    # cards themselves start and finish, so the five steps read as one arc
    inner = ('        <div class="steps-band">\n'
             '          <div class="steps">\n'
             + steps_html(t).rstrip() + "\n          </div>\n"
             "        </div>")
    return sub_page(lang, METHOD,
                    ("proc.label", "proc.title", "proc.desc",
                     "proc.meta.title", "proc.meta.desc"),
                    inner, SERVICES, "cta.allServices")


# ── contact page ────────────────────────────────────────────────────────
def contact(lang):
    t = T[lang]
    home_url = href(lang, lang, "index.html")

    options = "\n".join(
        '            <option value="' + e(t["c.o." + k]) + '">' + e(t["c.o." + k]) + "</option>"
        for k in ["web", "app", "saas", "design", "growth", "unsure"])

    mic_langs = "\n".join(
        '              <button type="button" class="mic-lang-btn" data-lang="' + l + '">'
        + e(T[l]["lang.code"]) + "</button>" for l in LANGS)

    # the three steps read as the answer to "and then what?", so they sit in a
    # band of their own under the form rather than in the aside beside it
    next_cards = ""
    for n in ["1", "2", "3"]:
        next_cards += f"""          <article class="next-card reveal">
            <span class="next-n">{n}</span>
            <p class="next-t">{e(t["c.tl." + n + "t"])}</p>
            <p class="next-d">{e(t["c.tl." + n + "d"])}</p>
          </article>

"""

    body = f"""
  <main id="main">
    <div class="shell" style="padding-top:clamp(40px,6vw,72px);padding-bottom:clamp(64px,9vw,110px);">

      <div id="formView">
        <div class="page-head">
          <span class="eyebrow" style="display:block;margin-bottom:16px;">{e(t["c.eyebrow"])}</span>
          <h1 class="page-title">{e(t["c.title"])}</h1>
          <p class="page-sub">{e(t["c.sub"])}</p>
        </div>

        <div class="contact-layout">
          <div class="form-card">
            <form id="inquiryForm"
                  data-page-lang="{lang}"
                  data-sending="{e(t["c.sending"])}"
                  data-send="{e(t["c.submit"])}"
                  data-listening="{e(t["c.listening"])}"
                  data-lang-en="{e(T["en"]["lang.name"])}"
                  data-lang-ru="{e(T["ru"]["lang.name"])}"
                  data-lang-fr="{e(T["fr"]["lang.name"])}"
                  data-lang-es="{e(T["es"]["lang.name"])}">

              <div class="row-2">
                <div>
                  <label class="field-label" for="name">{e(t["c.f.name"])} <span class="req">{e(t["c.f.required"])}</span></label>
                  <input type="text" id="name" name="name" placeholder="{e(t["c.f.namePh"])}" autocomplete="name" required>
                </div>
                <div>
                  <label class="field-label" for="email">{e(t["c.f.email"])} <span class="req">{e(t["c.f.required"])}</span></label>
                  <input type="email" id="email" name="email" placeholder="{e(t["c.f.emailPh"])}" autocomplete="email" required>
                </div>
              </div>

              <div class="row-2">
                <div>
                  <label class="field-label" for="company">{e(t["c.f.company"])}</label>
                  <input type="text" id="company" name="company" placeholder="{e(t["c.f.companyPh"])}" autocomplete="organization">
                </div>
                <div>
                  <label class="field-label" for="phone">{e(t["c.f.phone"])}</label>
                  <input type="tel" id="phone" name="phone" placeholder="{e(t["c.f.phonePh"])}" autocomplete="tel">
                </div>
              </div>

              <div>
                <label class="field-label" for="service">{e(t["c.f.service"])} <span class="req">{e(t["c.f.required"])}</span></label>
                <select id="service" name="service" required>
                  <option value="" disabled selected>{e(t["c.f.servicePh"])}</option>
{options}
                </select>
              </div>

              <div>
                <label class="field-label" for="details">{e(t["c.f.details"])} <span class="req">{e(t["c.f.required"])}</span></label>
                <div class="textarea-wrap">
                  <textarea id="details" name="details" placeholder="{e(t["c.f.detailsPh"])}" required></textarea>
                  <button type="button" class="mic-btn" id="micBtn" title="{e(t["c.mic"])}" aria-label="{e(t["c.mic"])}">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                  </button>
                </div>
                <p class="mic-note" id="micNote"></p>
                <div class="mic-lang-row" id="micLangRow">
                  <span class="mic-lang-label">{e(t["c.micLang"])}</span>
{mic_langs}
                </div>
              </div>

              <p class="error-msg" id="errorMsg">{e(t["c.error"])} <a href="mailto:{EMAIL}">{EMAIL}</a></p>

              <div>
                <button type="submit" class="submit-btn" id="submitBtn">
                  <span id="submitBtnText">{e(t["c.submit"])}</span> {ARROW}
                </button>
                <p class="privacy-note">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.5" y="10.5" width="15" height="10" rx="2.2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/></svg>
                  {e(t["c.privacy"])}
                </p>
              </div>
            </form>
          </div>

          <aside class="contact-aside">
            <div class="aside-card">
              <p class="aside-title">{e(t["c.aside.title"])}</p>
              <div class="aside-item">
                <p class="aside-lbl">{e(t["c.aside.emailLbl"])}</p>
                <p class="aside-note">{e(t["c.aside.emailNote"])}</p>
                <a class="aside-link" href="mailto:{EMAIL}">{EMAIL}</a>
              </div>
              <div class="aside-item">
                <p class="aside-lbl">{e(t["c.aside.followLbl"])}</p>
                <p class="aside-note">{e(t["c.aside.followNote"])}</p>
                <div class="footer-social" style="margin-top:10px;">
                  <a href="https://www.youtube.com/@GreDami" aria-label="GreDami · YouTube" target="_blank" rel="noopener">{YOUTUBE}</a>
                  <a href="https://www.instagram.com/gredami/" aria-label="GreDami · Instagram" target="_blank" rel="noopener">{INSTAGRAM}</a>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <div class="next">
          <div class="next-head">
            <h2 class="sec-title">{e(t["c.tl.title"])}</h2>
          </div>
          <div class="next-grid">
{next_cards.rstrip()}
          </div>
        </div>
      </div>

      <div class="success-box" id="successBox">
        <div class="success-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>
        </div>
        <span class="eyebrow" style="display:block;margin-bottom:16px;">{e(t["c.sentEyebrow"])}</span>
        <h1 class="page-title">{e(t["c.sentTitle"])}</h1>
        <p class="page-sub" style="margin-bottom:28px;">{e(t["c.sentDesc"])}</p>
        <a href="{home_url}" class="btn btn-ghost">{e(t["c.backHome"])}</a>
      </div>

    </div>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js"></script>
  <script>\n{CONTACT_JS}\n  </script>

"""
    return (head(lang, "start.html", t["c.meta.title"], t["c.meta.desc"])
            + nav(lang, "start.html", t) + body + footer(lang, t))


# ── write ───────────────────────────────────────────────────────────────
def main():
    written = []
    for lang in LANGS:
        d = ROOT if lang == "en" else ROOT / lang
        d.mkdir(parents=True, exist_ok=True)
        pages = [("index.html", home(lang)), (SERVICES, services_page(lang))]
        pages += [(CAT_PAGE[k], cat_page(lang, k)) for k in CATS]
        pages += [(METHOD, method_page(lang)), (CONTACT, contact(lang))]
        for name, page in pages:
            (d / name).write_text(page, encoding="utf-8")
            written.append(str((d / name).relative_to(ROOT)))

    rows = []
    for page in ["", SERVICES] + [CAT_PAGE[k] for k in CATS] + [METHOD, CONTACT]:
        for lang in LANGS:
            alts = "".join(
                '\n    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, url(l, page))
                for l in LANGS)
            rows.append(
                "  <url>\n    <loc>%s</loc>%s\n    <lastmod>2026-08-28</lastmod>\n"
                "    <changefreq>monthly</changefreq>\n    <priority>%s</priority>\n  </url>"
                % (url(lang, page), alts, "1.0" if not page else "0.8"))

    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8")
    written.append("sitemap.xml")

    (ROOT / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")
    written.append("favicon.svg")

    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE, encoding="utf-8")
    written.append("robots.txt")

    for f in written:
        print("  wrote", f)
    print("\n%d files, %d languages" % (len(written), len(LANGS)))


if __name__ == "__main__":
    main()

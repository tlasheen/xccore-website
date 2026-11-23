#!/usr/bin/env python3
"""Builds the XC Core website's pages from content/ (standard-library
Python only).

  python tools/build_site.py                 # every page and sitemap.xml
  python tools/build_site.py --policy PATH   # first copy the app's
                                             # docs/legal/privacy-policy-and-terms.md
                                             # to content/privacy.md
  python tools/build_site.py --check         # fail if a page is out of date

Each page is a fragment in content/ wrapped in the same header and footer
(the safety note on every page). The privacy policy and terms page is
made from content/privacy.md, a copy of the app's own document, so the
site always shows the same text as the app links to: after the document
changes in the app's repo, run with --policy and commit.

The testers' Google Group: set GOOGLE_GROUP_URL below and run again.
"""

import html
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
SITE = "https://xccore.uk"

# The testers' Google Group. Empty until the pilot fills it in: the beta
# page then asks testers to email instead.
GOOGLE_GROUP_URL = ""
PLAY_OPT_IN = "https://play.google.com/apps/testing/com.tarek.xccore"
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.tarek.xccore"
EMAIL = "tlasheen@gmail.com"

NAV = [
    ("", "Home"),
    ("features/", "Features"),
    ("watches/", "Watches & sensors"),
    ("beta/", "Join the beta"),
    ("contact/", "Contact"),
]

# path (directory under the root, "" for the home page), content file,
# title, description, hero heading (None: the page's own).
PAGES = [
    ("", "home.html", "XC Core: hear where the lift is",
     "XC Core turns your Android phone into a paragliding and paramotor "
     "vario with a voice coach that talks you into the thermal core. "
     "Free, no ads, no account."),
    ("features/", "features.html", "Features: XC Core",
     "Four flight modes, a voice thermal coach, a 3D thermal view, waypoint "
     "routes, offline maps and terrain, IGC logging and XContest, PPG mode "
     "and screen-off flying."),
    ("watches/", "watches.html", "Watches and sensors: XC Core",
     "Which watches and external Bluetooth varios work with XC Core today, "
     "and what is still being built."),
    ("beta/", "beta.html", "Join the beta: XC Core",
     "How to join XC Core's Android beta on Google Play, in English and "
     "Egyptian Arabic."),
    ("privacy/", None, "Privacy policy and terms: XC Core",
     "XC Core's privacy policy and terms of service: no accounts, no "
     "analytics, no advertising and no tracking."),
    ("contact/", "contact.html", "Contact and support: XC Core",
     "Contact XC Core's developer, and answers to common questions."),
]


def picture(name, alt, widths=(360, 720), sizes="(min-width: 760px) 280px, 70vw"):
    """A screenshot as WebP with a JPEG fallback, lazily loaded."""
    w, h = 720, 1280
    if name.startswith("app-"):
        h = 1440
    webp = ", ".join("/assets/img/%s-%d.webp %dw" % (name, x, x) for x in widths)
    jpg = ", ".join("/assets/img/%s-%d.jpg %dw" % (name, x, x) for x in widths)
    return (
        '<picture>'
        '<source type="image/webp" srcset="%s" sizes="%s">'
        '<img src="/assets/img/%s-%d.jpg" srcset="%s" sizes="%s" '
        'width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
        '</picture>' % (webp, sizes, name, widths[-1], jpg, sizes, w, h,
                        html.escape(alt, quote=True)))


def expand(text):
    """Fills a fragment's tokens: {{shot NAME|ALT}}, {{play}}, {{email}},
    {{group}} and the links."""
    def shot(m):
        name, alt = m.group(1).split("|", 1)
        return picture(name.strip(), alt.strip())
    text = re.sub(r"\{\{shot ([^}]+)\}\}", shot, text)
    text = text.replace("{{play}}", (
        '<a class="badge-play" href="%s"><img src="/assets/img/google-play-badge.png" '
        'width="180" height="54" alt="Get it on Google Play"></a>' % PLAY_STORE))
    text = text.replace("{{opt_in}}", PLAY_OPT_IN)
    text = text.replace("{{store}}", PLAY_STORE)
    text = text.replace("{{email}}", EMAIL)
    if GOOGLE_GROUP_URL:
        text = re.sub(r"\{\{group_en\}\}.*?\{\{/group_en\}\}",
                      lambda m: 'Join the testers\' Google Group: '
                      '<a class="link-box" href="%s">%s</a>'
                      % (GOOGLE_GROUP_URL, GOOGLE_GROUP_URL), text, flags=re.S)
        text = re.sub(r"\{\{group_ar\}\}.*?\{\{/group_ar\}\}",
                      lambda m: 'ادخل جروب المختبرين على Google Groups: '
                      '<a class="link-box" dir="ltr" href="%s">%s</a>'
                      % (GOOGLE_GROUP_URL, GOOGLE_GROUP_URL), text, flags=re.S)
    else:
        text = re.sub(r"\{\{/?group_(en|ar)\}\}", "", text)
    return text


# --- The privacy policy: a small Markdown reader for that one document ---

def inline(s):
    """Markdown's inline marks in [s]: links, bold, italics, code."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\"=>/])(https?://[^\s<]+[^\s<.,;:)])",
               r'<a href="\1">\1</a>', s)
    return s


def slug(text):
    """An id for a heading."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def markdown(md):
    """The policy document as HTML: headings (with ids), paragraphs,
    bulleted and numbered lists (nested by indent), rules."""
    out = []
    para = []
    lists = []  # open lists: (indent, tag), each with an open <li>
    text = None  # the open item's text lines, not yet written

    def flush_text():
        nonlocal text
        if text is not None:
            out.append(inline(" ".join(text)))
            text = None

    def close_lists(above=-1):
        flush_text()
        while lists and lists[-1][0] > above:
            out.append("</li></%s>" % lists.pop()[1])

    def close_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    for raw in md.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            close_para()
            flush_text()
            continue
        m_h = re.match(r"^(#{1,6})\s+(.*)$", line)
        m_item = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m_h:
            close_para()
            close_lists()
            level, title = len(m_h.group(1)), m_h.group(2).strip()
            out.append('<h%d id="%s">%s</h%d>' % (level, slug(title),
                                                  inline(title), level))
        elif re.match(r"^-{3,}$", line.strip()):
            close_para()
            close_lists()
            out.append("<hr>")
        elif m_item:
            close_para()
            flush_text()
            indent = len(m_item.group(1))
            tag = "ol" if m_item.group(2)[0].isdigit() else "ul"
            if lists and indent <= lists[-1][0]:
                close_lists(indent)
                if lists:
                    out.append("</li>")
            if not lists or indent > lists[-1][0]:
                out.append("<%s>" % tag)
                lists.append((indent, tag))
            out.append("<li>")
            text = [m_item.group(3)]
        elif lists and raw.startswith(" "):
            if text is None:
                text = []
            text.append(line.strip())
        else:
            close_lists()
            para.append(line.strip())
    close_para()
    close_lists()
    return "\n".join(out)


def policy_page():
    """The privacy policy and terms page's body."""
    md = open(os.path.join(CONTENT, "privacy.md"), encoding="utf-8").read()
    return ('<div class="narrow legal section">\n%s\n'
            '<p class="note">This page is made from the same document the '
            'app links to. Questions: <a href="mailto:%s">%s</a>.</p>\n</div>'
            % (markdown(md), EMAIL, EMAIL))


# --- The page frame ---

def nav(current):
    items = []
    for path, label in NAV:
        cur = ' aria-current="page"' if path == current else ""
        items.append('<li><a href="/%s"%s>%s</a></li>' % (path, cur,
                                                         html.escape(label)))
    return "\n".join(items)


def frame(path, title, description, body):
    url = SITE + "/" + path
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0b1f38">
<meta property="og:type" content="website">
<meta property="og:site_name" content="XC Core">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/assets/img/og-image.jpg">
<meta property="og:image:width" content="1024">
<meta property="og:image:height" content="500">
<meta property="og:image:alt" content="XC Core: Hear where the lift is.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/sora.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap">
<a class="brand" href="/"><img src="/assets/img/mark-64.png" width="30" height="32" alt=""><span><span class="xc">XC</span> <span class="core">Core</span></span></a>
<nav class="site-nav" aria-label="Main">
<ul>
{nav}
</ul>
</nav>
</div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
<div class="wrap">
<p class="safety">XC Core is a flight aid, not a certified instrument. Its readings and suggestions can be wrong: keep watch outside, fly within your skills and make your own decisions.</p>
<ul>
<li><a href="/features/">Features</a></li>
<li><a href="/watches/">Watches &amp; sensors</a></li>
<li><a href="/beta/">Join the beta</a></li>
<li><a href="/privacy/">Privacy policy and terms</a></li>
<li><a href="/contact/">Contact</a></li>
</ul>
<p class="fine">© 2026 Tarek Lasheen. No cookies, no analytics, no trackers on this site. Google Play and the Google Play logo are trademarks of Google LLC. Sora font: SIL Open Font Licence. Map images in the screenshots: © OpenStreetMap contributors, SRTM, OpenTopoMap (CC-BY-SA).</p>
</div>
</footer>
</body>
</html>
""".format(title=html.escape(title), desc=html.escape(description, quote=True),
           url=url, site=SITE, nav=nav(path), body=body)


def build():
    """Every page's file contents, by path relative to the root."""
    files = {}
    for path, content, title, desc in PAGES:
        if content is None:
            body = policy_page()
        else:
            body = expand(open(os.path.join(CONTENT, content),
                               encoding="utf-8").read())
        files[os.path.join(path, "index.html")] = frame(path, title, desc, body)
    nf = expand(open(os.path.join(CONTENT, "404.html"), encoding="utf-8").read())
    files["404.html"] = frame("404.html", "Page not found: XC Core",
                              "This page doesn't exist.", nf)
    urls = "\n".join("  <url><loc>%s/%s</loc></url>" % (SITE, p)
                     for p, *_ in PAGES)
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                            "%s\n</urlset>\n" % urls)
    return files


def main(argv):
    if "--policy" in argv:
        src = argv[argv.index("--policy") + 1]
        shutil.copyfile(src, os.path.join(CONTENT, "privacy.md"))
        print("Policy copied from %s" % src)
    files = build()
    stale = []
    for rel, text in files.items():
        p = os.path.join(ROOT, rel)
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old != text:
            stale.append(rel)
            if "--check" not in argv:
                os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    if "--check" in argv:
        if stale:
            print("Out of date (run tools/build_site.py): " + ", ".join(stale))
            return 1
        print("All pages up to date.")
        return 0
    print("Written: %s" % (", ".join(stale) or "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

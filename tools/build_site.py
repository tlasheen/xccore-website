#!/usr/bin/env python3
"""Builds the XC Core website, in English and Arabic, from content/
(standard-library Python only).

  python tools/build_site.py                 # every page and sitemap.xml
  python tools/build_site.py --policy PATH   # first copy the app's
                                             # docs/legal/privacy-policy-and-terms.md
                                             # to content/privacy.md
  python tools/build_site.py --check         # fail if a page is out of date
                                             # or the Arabic policy is older
                                             # than the English one

English pages are content/en/<page>.html, Arabic ones content/ar/<page>.html
(served under /ar/), each wrapped in the same frame: header with the
language switch, footer with the safety note. The privacy policy is made
from content/privacy.md (a copy of the app's document) and its Arabic
translation content/ar/privacy.md; content/ar/privacy.source-sha256 holds
the hash of the English text it was translated from, so a policy change
without a new translation is caught.

Tokens in the content files:
  {{phone NAME|ALT}}                  a screenshot in a phone frame
  {{carousel ID|LABEL}} ... {{/carousel}}
                                      one slide a line: NAME | CAPTION | ALT
  {{icon NAME}}                       a small inline icon
  {{video}}                           the video block (if assets/video has it)
  {{play}} {{opt_in}} {{store}} {{email}} {{group_en}}..{{/group_en}}

The testers' Google Group: set GOOGLE_GROUP_URL below and run again.
"""

import hashlib
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

# Page key, path under the language's root, title and description by
# language.
PAGES = [
    ("home", "", {
        "en": ("XC Core: hear where the lift is",
               "XC Core turns your Android phone into a paragliding and paramotor "
               "vario with a voice coach that talks you into the thermal core. "
               "Free, no ads, no account."),
        "ar": ("XC Core: اسمع أين الصعود",
               "يحوّل XC Core هاتف أندرويد إلى فاريو للطيران الشراعي والباراموتور، "
               "مع مدرب صوتي يرشدك إلى قلب الثيرمال. مجاني، بلا إعلانات وبلا حساب."),
    }),
    ("features", "features/", {
        "en": ("Features: XC Core",
               "Four flight modes, a voice thermal coach, a 3D thermal view, waypoint "
               "routes, offline maps and terrain, IGC logging and XContest, PPG mode "
               "and screen-off flying."),
        "ar": ("المزايا: XC Core",
               "أربعة أوضاع طيران، ومدرب صوتي للثيرمال، وعرض ثلاثي الأبعاد، ومسارات "
               "بنقاط طريق، وخرائط وتضاريس دون اتصال، وتسجيل IGC وXContest، ووضع PPG."),
    }),
    ("watches", "watches/", {
        "en": ("Watches and sensors: XC Core",
               "Which watches and external Bluetooth varios work with XC Core today, "
               "and what is still being built."),
        "ar": ("الساعات والحساسات: XC Core",
               "ما الذي يعمل اليوم مع XC Core من الساعات وأجهزة الفاريو الخارجية عبر "
               "البلوتوث، وما الذي لا يزال قيد التطوير."),
    }),
    ("beta", "beta/", {
        "en": ("Join the beta: XC Core",
               "How to join XC Core's Android beta on Google Play."),
        "ar": ("انضم إلى التجربة: XC Core",
               "إزاي تشترك في النسخة التجريبية من XC Core على جوجل بلاي."),
    }),
    ("contact", "contact/", {
        "en": ("Contact and support: XC Core",
               "Contact XC Core's developer, and answers to common questions."),
        "ar": ("تواصل معنا: XC Core",
               "تواصل مع مطوّر XC Core، وإجابات عن الأسئلة الشائعة."),
    }),
    ("privacy", "privacy/", {
        "en": ("Privacy policy and terms: XC Core",
               "XC Core's privacy policy and terms of service: no accounts, no "
               "analytics, no advertising and no tracking."),
        "ar": ("سياسة الخصوصية والشروط: XC Core",
               "سياسة الخصوصية وشروط الخدمة لتطبيق XC Core (ترجمة؛ النص الإنجليزي هو "
               "الملزم): بلا حسابات ولا تحليلات ولا إعلانات ولا تتبّع."),
    }),
]

NAV = ["home", "features", "watches", "beta", "contact"]

T = {
    "en": {
        "dir": "ltr", "root": "/", "name": "English",
        "nav": {"home": "Home", "features": "Features", "watches": "Watches & sensors",
                "beta": "Join the beta", "contact": "Contact", "privacy": "Privacy policy and terms"},
        "skip": "Skip to content", "menu": "Menu", "main_nav": "Main",
        "lang_nav": "Language",
        "safety": "XC Core is a flight aid, not a certified instrument. Its readings and "
                  "suggestions can be wrong: keep watch outside, fly within your skills "
                  "and make your own decisions.",
        "fine": "© 2026 Tarek Lasheen. No cookies, no analytics, no trackers on this site. "
                "Google Play and the Google Play logo are trademarks of Google LLC. Fonts: "
                "Sora and Cairo (SIL Open Font Licence). Map images in the screenshots: © "
                "OpenStreetMap contributors, SRTM, OpenTopoMap (CC-BY-SA).",
        "play_alt": "Get it on Google Play",
        "carousel": "Screenshots", "prev": "Previous", "next": "Next",
        "slide": "Screenshot %d of %d", "pause": "Pause", "resume": "Play",
        "notfound": ("Page not found: XC Core", "This page doesn't exist."),
    },
    "ar": {
        "dir": "rtl", "root": "/ar/", "name": "العربية",
        "nav": {"home": "الرئيسية", "features": "المزايا", "watches": "الساعات والحساسات",
                "beta": "انضم إلى التجربة", "contact": "تواصل معنا",
                "privacy": "سياسة الخصوصية والشروط"},
        "skip": "انتقل إلى المحتوى", "menu": "القائمة", "main_nav": "القائمة الرئيسية",
        "lang_nav": "اللغة",
        "safety": "XC Core أداة مساعدة في الطيران، وليس جهازًا معتمدًا. قراءاته واقتراحاته "
                  "قد تخطئ: راقب ما حولك، وطِر في حدود مهاراتك، واتخذ قراراتك بنفسك.",
        "fine": "© 2026 طارق لاشين. لا ملفات تعريف ارتباط (cookies) ولا تحليلات ولا أدوات "
                "تتبّع في هذا الموقع. Google Play وشعار Google Play علامتان تجاريتان لشركة "
                "Google LLC. الخطوط: Sora وCairo (رخصة SIL المفتوحة). صور الخرائط في لقطات "
                "الشاشة: © OpenStreetMap contributors, SRTM, OpenTopoMap (CC-BY-SA).",
        "play_alt": "احصل عليه من Google Play",
        "carousel": "لقطات الشاشة", "prev": "السابق", "next": "التالي",
        "slide": "لقطة %d من %d", "pause": "إيقاف مؤقت", "resume": "تشغيل",
        "notfound": ("الصفحة غير موجودة: XC Core", "هذه الصفحة غير موجودة."),
    },
}

# Small line icons (24 x 24, stroke = currentColor).
ICONS = {
    "voice": '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 9a4 4 0 0 1 0 6"/><path d="M18.5 6.5a7.5 7.5 0 0 1 0 11"/>',
    "thermal": '<ellipse cx="12" cy="19" rx="8" ry="2.2"/><ellipse cx="12" cy="13.5" rx="5.5" ry="1.7"/><ellipse cx="12" cy="8.8" rx="3.4" ry="1.2"/><path d="M8 4.5c2.5-1.4 5.5-1.4 8 0"/>',
    "route": '<path d="M5 21V4"/><path d="M5 4h11l-2 3.5 2 3.5H5"/><circle cx="18" cy="19" r="2"/><path d="M8 19h8"/>',
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14"/><path d="M15 6v14"/>',
    "igc": '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 17l2.5-3 2 2 3-4"/>',
    "ppg": '<circle cx="12" cy="12" r="2"/><path d="M12 10c-1-4-.5-6.5 1.5-7 1.5 2 .5 4.5-1.5 7"/><path d="M13.7 13.2c3.8 1.7 5.6 3.7 4.9 5.6-2.4.2-4.3-1.9-4.9-5.6"/><path d="M10.3 13.2c-3.1 2.8-5.6 3.6-7 2.1 1-2.2 3.9-2.8 7-2.1"/><circle cx="12" cy="12" r="9.5"/>',
    "screen": '<rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M10 18.5h4"/><path d="M9.5 9.5a3.5 3.5 0 0 1 5 0"/><path d="M8 7.5a6 6 0 0 1 8 0"/>',
    "modes": '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
    "speed": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/><circle cx="12" cy="17" r="1.4"/>',
    "soaring": '<path d="M2 19l6-8 4 5 3-3 7 6z"/><path d="M14 6c2-1.5 4-1.5 6 0"/>',
    "xc": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5 13.5 13.5 8.5 15.5 10.5 10.5z"/>',
    "bluetooth": '<path d="M7 7l10 10-5 4V3l5 4L7 17"/>',
    "watch": '<rect x="6.5" y="6" width="11" height="12" rx="3"/><path d="M9 6l1-3h4l1 3"/><path d="M9 18l1 3h4l1-3"/><path d="M12 9.5V12l1.5 1.5"/>',
    "phone": '<rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M10 18.5h4"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "gift": '<rect x="3.5" y="9" width="17" height="11" rx="1.5"/><path d="M12 9v11"/><path d="M3.5 13h17"/><path d="M12 9c-1.5-3-5-3.5-5-1.5S10 9 12 9zm0 0c1.5-3 5-3.5 5-1.5S14 9 12 9z"/>',
    "vario": '<path d="M3 17l5-5 4 3 8-9"/><path d="M15 6h5v5"/>',
    "headset": '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6 8.5 7 8.5-7"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.5-3.5 3-5.5 6.5-5.5s6 2 6.5 5.5"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8"/><path d="M18 14.8c2 .8 3.2 2.5 3.5 5.2"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "arrow": '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
    "back": '<path d="M15 6l-6 6 6 6"/>',
    "forward": '<path d="M9 6l6 6-6 6"/>',
    "play": '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
    "menu": '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
}


def icon(name):
    """An inline icon, hidden from screen readers."""
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            '%s</svg>' % ICONS[name])


def picture(name, alt, sizes="(min-width: 900px) 300px, 74vw", lazy=True):
    """A 9:16 screenshot as WebP with a JPEG fallback."""
    widths = (320, 640)
    webp = ", ".join("/assets/img/%s-%d.webp %dw" % (name, w, w) for w in widths)
    jpg = ", ".join("/assets/img/%s-%d.jpg %dw" % (name, w, w) for w in widths)
    load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return ('<picture><source type="image/webp" srcset="%s" sizes="%s">'
            '<img src="/assets/img/%s-640.jpg" srcset="%s" sizes="%s" width="640" height="1138" '
            'alt="%s"%s></picture>' % (webp, sizes, name, jpg, sizes,
                                      html.escape(alt, quote=True), load))


def phone(name, alt, lazy=True):
    return '<div class="phone">%s</div>' % picture(name, alt, lazy=lazy)


def carousel(cid, label, body, lang):
    t = T[lang]
    slides = [l.split("|") for l in body.strip().splitlines() if l.strip()]
    n = len(slides)
    items, dots = [], []
    for i, (name, caption, alt) in enumerate(slides, 1):
        sid = "%s-%d" % (cid, i)
        items.append(
            '<li class="slide" id="%s" aria-roledescription="slide" aria-label="%s">'
            '<figure>%s<figcaption>%s</figcaption></figure></li>'
            % (sid, t["slide"] % (i, n), phone(name.strip(), alt.strip()), caption.strip()))
        dots.append('<li><a href="#%s" aria-label="%s"%s></a></li>'
                    % (sid, t["slide"] % (i, n), ' aria-current="true"' if i == 1 else ""))
    return (
        '<div class="carousel" data-carousel>'
        '<ul class="track" aria-roledescription="carousel" aria-label="%s" tabindex="0">%s</ul>'
        '<div class="carousel-nav">'
        '<button class="arrow prev" type="button" aria-label="%s" hidden>%s</button>'
        '<ol class="dots">%s</ol>'
        '<button class="arrow next" type="button" aria-label="%s" hidden>%s</button>'
        '</div>'
        '<p class="center"><button class="pause" type="button" hidden data-pause="%s" data-play="%s">%s</button></p>'
        '</div>'
        % (html.escape(label, quote=True), "".join(items), t["prev"], icon("back"),
           "".join(dots), t["next"], icon("forward"), t["pause"], t["resume"], t["pause"]))


VIDEO = {
    "en": {"eyebrow": "Watch", "title": "See it fly", "lead": "A replayed flight through the real app, with its real sound: beeps, voice calls and all.",
           "sound": "Play with sound", "note": "The teaser loops silently. The full video has the app's own sound, with every voice call captioned.",
           "caption": "English", "track_lang": "en"},
    "ar": {"eyebrow": "شاهد", "title": "شاهده أثناء الطيران", "lead": "رحلة مُعادة داخل التطبيق الحقيقي بصوته الحقيقي: الصفير ونداءات المدرب الصوتي.",
           "sound": "شغّل مع الصوت", "note": "المقطع القصير يعمل بلا صوت. الفيديو الكامل بصوت التطبيق نفسه، مع ترجمة عربية لكل نداء صوتي.",
           "caption": "العربية", "track_lang": "ar"},
}


def video(lang):
    """The video block, if the video files are there."""
    d = os.path.join(ROOT, "assets", "video")
    full = "xccore-promo-%s" % lang
    if not os.path.exists(os.path.join(d, full + ".mp4")):
        return ""
    v = VIDEO[lang]
    return """<section class="section tight" id="video">
<div class="wrap video-box">
<div class="section-head center"><span class="eyebrow">{eyebrow}</span><h2>{title}</h2><p class="lead">{lead}</p></div>
<video id="promo" class="promo" playsinline preload="none" poster="/assets/video/xccore-teaser-{lang}-poster.jpg"
 data-teaser-mp4="/assets/video/xccore-teaser-{lang}.mp4" data-teaser-webm="/assets/video/xccore-teaser-{lang}.webm"
 data-full-mp4="/assets/video/{full}.mp4" data-full-webm="/assets/video/{full}.webm" data-full-poster="/assets/video/{full}-poster.jpg"
 controls width="1280" height="720">
<source src="/assets/video/{full}.webm" type="video/webm">
<source src="/assets/video/{full}.mp4" type="video/mp4">
<track kind="captions" src="/assets/video/{full}.vtt" srclang="{tl}" label="{cap}">
</video>
<div class="actions center"><button class="button" type="button" data-sound hidden>{play}{sound}</button></div>
<p class="video-note">{note}</p>
</div>
</section>""".format(lang=lang, eyebrow=v["eyebrow"], title=v["title"], lead=v["lead"], full=full,
                       tl=v["track_lang"], cap=v["caption"], play=icon("play"), sound=v["sound"],
                       note=v["note"])


def expand(text, lang):
    """Fills a fragment's tokens."""
    text = re.sub(r"\{\{carousel ([^|}]+)\|([^}]+)\}\}(.*?)\{\{/carousel\}\}",
                  lambda m: carousel(m.group(1).strip(), m.group(2).strip(), m.group(3), lang),
                  text, flags=re.S)
    text = re.sub(r"\{\{phone ([^|}]+)\|([^}]+)\}\}",
                  lambda m: phone(m.group(1).strip(), m.group(2).strip()), text)
    text = re.sub(r"\{\{phone-hero ([^|}]+)\|([^}]+)\}\}",
                  lambda m: phone(m.group(1).strip(), m.group(2).strip(), lazy=False), text)
    text = re.sub(r"\{\{icon ([a-z0-9-]+)\}\}", lambda m: icon(m.group(1)), text)
    text = text.replace("{{video}}", video(lang))
    text = text.replace("{{thermal}}", THERMAL)
    text = text.replace("{{play}}", (
        '<a class="badge-play" href="%s" hreflang="%s"><img src="/assets/img/google-play-badge%s.png" '
        'width="160" height="48" alt="%s"></a>' % (PLAY_STORE, lang, "", T[lang]["play_alt"])))
    text = text.replace("{{opt_in}}", PLAY_OPT_IN)
    text = text.replace("{{store}}", PLAY_STORE)
    text = text.replace("{{email}}", EMAIL)
    if GOOGLE_GROUP_URL:
        msg = {"en": "Join the testers' Google Group:",
               "ar": "ادخل جروب المختبرين على Google Groups:"}[lang]
        text = re.sub(r"\{\{group_%s\}\}.*?\{\{/group_%s\}\}" % (lang, lang),
                      lambda m: '%s <a class="link-box" href="%s">%s</a>'
                      % (msg, GOOGLE_GROUP_URL, GOOGLE_GROUP_URL), text, flags=re.S)
    else:
        text = re.sub(r"\{\{/?group_(en|ar)\}\}", "", text)
    return text


# The rising thermal over the hero's mountains: the logo's rings.
THERMAL = ('<svg class="thermal" viewBox="0 0 200 420" aria-hidden="true" focusable="false">'
           + "".join('<g class="ring"><ellipse cx="100" cy="%d" rx="%d" ry="%d"/></g>'
                     % (cy, rx, ry) for cy, rx, ry in
                     [(380, 78, 15), (318, 62, 12.5), (262, 48, 10), (212, 36, 8), (170, 26, 6.5)])
           + '<path class="wing" d="M62 104c24-16 52-16 76 0" />'
           + '</svg>')


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


def slug(text, used):
    """An id for a heading, unique on the page."""
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
    base, n = s, 2
    while s in used:
        s, n = "%s-%d" % (base, n), n + 1
    used.add(s)
    return s


def markdown(md):
    """The policy document as HTML: headings (with ids), paragraphs,
    bulleted and numbered lists (nested by indent), rules."""
    out = []
    para = []
    lists = []  # open lists: (indent, tag), each with an open <li>
    text = None  # the open item's text lines, not yet written
    used = set()

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
            out.append('<h%d id="%s">%s</h%d>' % (level, slug(title, used),
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


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def policy_page(lang):
    """The privacy policy and terms page's body."""
    src = os.path.join(CONTENT, "privacy.md") if lang == "en" else os.path.join(CONTENT, "ar", "privacy.md")
    md = open(src, encoding="utf-8").read()
    note = {"en": 'This page is made from the same document the app links to. Questions: '
                  '<a href="mailto:%s">%s</a>. <a href="/ar/privacy/" hreflang="ar" lang="ar">'
                  'الترجمة العربية</a>.' % (EMAIL, EMAIL),
            "ar": 'هذه الصفحة ترجمة للوثيقة التي يشير إليها التطبيق؛ <a href="/privacy/" hreflang="en" '
                  'lang="en">English (binding)</a>. للاستفسار: <a href="mailto:%s">%s</a>.' % (EMAIL, EMAIL)}[lang]
    return ('<div class="narrow legal section">\n%s\n<p class="note">%s</p>\n</div>'
            % (markdown(md), note))


def arabic_policy_current():
    """Whether the Arabic policy was translated from today's English text."""
    p = os.path.join(CONTENT, "ar", "privacy.source-sha256")
    if not os.path.exists(p):
        return False
    return open(p, encoding="utf-8").read().strip() == sha(os.path.join(CONTENT, "privacy.md"))


# --- The page frame ---

def url(lang, path):
    return T[lang]["root"] + path


def lang_switch(lang, path, cls="lang-switch"):
    parts = []
    for other in ("en", "ar"):
        name = T[other]["name"]
        if other == lang:
            parts.append('<span lang="%s" aria-current="true">%s</span>' % (other, name))
        else:
            parts.append('<a href="%s" hreflang="%s" lang="%s">%s</a>'
                         % (url(other, path), other, other, name))
    return ('<nav class="%s" aria-label="%s">%s</nav>'
            % (cls, T[lang]["lang_nav"], '<span class="sep" aria-hidden="true">|</span>'.join(parts)))


def nav_items(lang, current):
    items = []
    for key in NAV:
        path = dict((k, p) for k, p, _ in PAGES)[key]
        cur = ' aria-current="page"' if key == current else ""
        items.append('<li><a href="%s"%s>%s</a></li>'
                     % (url(lang, path), cur, html.escape(T[lang]["nav"][key])))
    return "\n".join(items)


def frame(lang, key, path, title, description, body):
    t = T[lang]
    alt = {"en": url("en", path), "ar": url("ar", path)}
    canonical = SITE + url(lang, path)
    hint = ""
    if lang == "en":
        hint = ('<div class="lang-hint" id="lang-hint" lang="ar" dir="rtl" hidden><div class="wrap">'
                '<span>هذا الموقع متوفر باللغة العربية.</span> <a href="%s" hreflang="ar">اعرضه بالعربية</a> '
                '<button type="button" data-dismiss>لا، شكرًا</button></div></div>' % alt["ar"])
    footer_links = "".join('<li><a href="%s">%s</a></li>' % (url(lang, p), html.escape(t["nav"][k]))
                           for k, p, _ in PAGES if k != "home")
    return """<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{site}{alt_en}">
<link rel="alternate" hreflang="ar" href="{site}{alt_ar}">
<link rel="alternate" hreflang="x-default" href="{site}{alt_en}">
<meta name="theme-color" content="#0b1f38">
<meta property="og:type" content="website">
<meta property="og:site_name" content="XC Core">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{site}/assets/img/og-image.jpg">
<meta property="og:image:width" content="1024">
<meta property="og:image:height" content="500">
<meta property="og:image:alt" content="XC Core: Hear where the lift is.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/sora.woff2" as="font" type="font/woff2" crossorigin>{preload_ar}
<link rel="stylesheet" href="/assets/css/site.css">
<script src="/assets/js/site.js" defer></script>
</head>
<body>
<a class="skip" href="#main">{skip}</a>
{hint}
<header class="site-header">
<div class="wrap">
<a class="brand" href="{home}"><img src="/assets/img/mark-64.png" width="28" height="30" alt=""><bdi><span>XC</span> <span class="core">Core</span></bdi></a>
<nav class="nav-desktop" aria-label="{main_nav}">
<ul>
{nav}
</ul>
</nav>
<div class="header-tools">
{switch}
<details class="menu">
<summary>{menu_icon}<span>{menu}</span></summary>
<div class="panel">
<nav aria-label="{main_nav}"><ul>
{nav}
</ul></nav>
{switch_menu}
</div>
</details>
</div>
</div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
<div class="wrap">
<div class="top">
<a class="brand" href="{home}"><img src="/assets/img/mark-64.png" width="28" height="30" alt=""><bdi><span>XC</span> <span class="core">Core</span></bdi></a>
{switch}
</div>
<p class="safety">{safety}</p>
<ul>{footer_links}</ul>
<p class="fine">{fine}</p>
</div>
</footer>
</body>
</html>
""".format(lang=lang, dir=t["dir"], title=html.escape(title), desc=html.escape(description, quote=True),
           canonical=canonical, site=SITE, alt_en=alt["en"], alt_ar=alt["ar"],
           og_locale="en_GB" if lang == "en" else "ar_EG",
           preload_ar=('\n<link rel="preload" href="/assets/fonts/cairo-arabic.woff2" as="font" '
                       'type="font/woff2" crossorigin>' if lang == "ar" else ""),
           skip=t["skip"], hint=hint, home=t["root"], main_nav=t["main_nav"],
           nav=nav_items(lang, key), switch=lang_switch(lang, path),
           switch_menu=lang_switch(lang, path), menu=t["menu"], menu_icon=icon("menu"),
           body=body, safety=t["safety"], footer_links=footer_links, fine=t["fine"])


def build():
    """Every page's file contents, by path relative to the root."""
    files = {}
    for lang in ("en", "ar"):
        for key, path, meta in PAGES:
            title, desc = meta[lang]
            if key == "privacy":
                body = policy_page(lang)
            else:
                body = expand(open(os.path.join(CONTENT, lang, key + ".html"),
                                   encoding="utf-8").read(), lang)
            rel = os.path.join(T[lang]["root"].strip("/"), path, "index.html").lstrip("/\\")
            files[rel] = frame(lang, key, path, title, desc, body)
    nf = expand(open(os.path.join(CONTENT, "en", "404.html"), encoding="utf-8").read(), "en")
    files["404.html"] = frame("en", "404", "", T["en"]["notfound"][0], T["en"]["notfound"][1], nf)
    urls = []
    for key, path, _ in PAGES:
        for lang in ("en", "ar"):
            urls.append(
                "  <url><loc>%s%s</loc>"
                '<xhtml:link rel="alternate" hreflang="en" href="%s%s"/>'
                '<xhtml:link rel="alternate" hreflang="ar" href="%s%s"/></url>'
                % (SITE, url(lang, path), SITE, url("en", path), SITE, url("ar", path)))
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
                            "%s\n</urlset>\n" % "\n".join(urls))
    return files


def main(argv):
    if "--policy" in argv:
        src = argv[argv.index("--policy") + 1]
        shutil.copyfile(src, os.path.join(CONTENT, "privacy.md"))
        print("Policy copied from %s" % src)
    if "--arabic-policy-done" in argv:
        # After translating the new English policy: record what it was made from.
        with open(os.path.join(CONTENT, "ar", "privacy.source-sha256"), "w", newline="\n") as fh:
            fh.write(sha(os.path.join(CONTENT, "privacy.md")) + "\n")
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
    ok = True
    if not arabic_policy_current():
        print("The Arabic privacy policy was translated from an older English text: "
              "translate the changes into content/ar/privacy.md, then run with "
              "--arabic-policy-done.")
        ok = False
    if "--check" in argv:
        if stale:
            print("Out of date (run tools/build_site.py): " + ", ".join(stale))
            ok = False
        if ok:
            print("All pages up to date.")
        return 0 if ok else 1
    print("Written: %s" % (", ".join(stale) or "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

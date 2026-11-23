# XC Core website

The website of [XC Core](https://xccore.uk), a paragliding and paramotor
vario for Android with a voice thermal coach, in **English and Arabic**.
Plain HTML and CSS, with one small optional script; every page works fully
with JavaScript off. No framework, no cookies, no analytics, no requests to
other sites. Served by GitHub Pages from `main` at **https://xccore.uk**
(`CNAME`).

This repository holds only the website. The app's code is elsewhere.

## Layout

| Path | What |
|---|---|
| `content/en/*.html`, `content/ar/*.html` | Each page's body in English and Arabic (header, language switch and footer are added by the build). Arabic pages are served under `/ar/`, right to left |
| `content/privacy.md` | A copy of the app's privacy policy and terms (`docs/legal/privacy-policy-and-terms.md` in the app's repo): the binding text |
| `content/ar/privacy.md` | Its Arabic translation, marked as a translation; `content/ar/privacy.source-sha256` records which English text it was made from |
| `index.html`, `*/index.html`, `ar/**`, `404.html`, `sitemap.xml` | **Generated** by `tools/build_site.py`: don't edit them by hand |
| `assets/css/site.css` | The one stylesheet (light and dark, phones first, logical properties so RTL mirrors) |
| `assets/js/site.js` | Optional extras: carousel arrows and autoplay (paused on touch, off with reduced motion), the video's teaser and "Play with sound", a one-time suggestion of the Arabic site for Arabic browsers (never a redirect) |
| `assets/img/` | Screenshots at 9:16 as WebP with JPEG fallbacks (`<name>-320/-640`), the logo's mark, the dusk scene, the topographic pattern (`topo.svg`), the Open Graph image, the Google Play badge |
| `assets/video/` | The promo video (English and Arabic captions), the teaser, posters and caption tracks |
| `assets/fonts/` | Sora (subset to Latin) and Cairo (subset to Arabic), both SIL Open Font Licence (`OFL.txt`, `OFL-Cairo.txt`), self-hosted |
| `tools/` | `build_site.py` (the pages), `make_assets.py` (images and fonts), `make_topo.py` (the contour pattern) |

## Changing the site

```sh
python tools/build_site.py           # after editing content/ or the frame
python tools/build_site.py --check   # what CI runs: pages up to date, Arabic policy current
```

Every change goes into both languages. Content tokens are listed at the top
of `tools/build_site.py`; a carousel is

```
{{carousel ID|Label}}
name | Caption | Alt text
{{/carousel}}
```

**The privacy policy** is kept in step with the app: after the policy
changes in the app's repo, run

```sh
python tools/build_site.py --policy ../thermal_vario/docs/legal/privacy-policy-and-terms.md
```

then translate the changes into `content/ar/privacy.md` and run
`python tools/build_site.py --arabic-policy-done`. Until then `--check`
fails. Commit the content and the generated pages.

**The testers' Google Group:** set `GOOGLE_GROUP_URL` in
`tools/build_site.py`, run the build and commit. Until then the beta page
asks testers to email.

**Screenshots** (Pillow): take them with the app at exactly 9:16
(`adb shell wm size 1080x1920`, then `wm size reset`), name them
`<name>.png` and run

```sh
python tools/make_assets.py --screens DIR
```

Anything not 9:16 is cut to 9:16 from the centre, never stretched.

**Fonts** (fontTools and brotli):

```sh
python tools/make_assets.py ../thermal_vario/Assets SCREENSHOTS_DIR Sora-Variable.ttf
python tools/make_assets.py --arabic-font Cairo-Variable.ttf
```

## Rules

- Claim only what the released app does; mark what is being built or
  tested as such.
- No trackers, analytics, cookies or third-party requests.
- Nothing from the app's code, keys, secrets or pilots' flight files.
  Screenshots and the video come from the app's generated demo flight.
- The safety note stays in every page's footer: XC Core is a flight aid,
  not a certified instrument.

© 2026 Tarek Lasheen. Google Play and the Google Play logo are trademarks
of Google LLC.

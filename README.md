# XC Core website

The website of [XC Core](https://xccore.uk), a paragliding and paramotor
vario for Android with a voice thermal coach. Plain HTML and CSS: no
framework, no JavaScript, no cookies, no analytics, no requests to other
sites. Served by GitHub Pages from `main` at **https://xccore.uk**
(`CNAME`).

This repository holds only the website. The app's code is elsewhere.

## Layout

| Path | What |
|---|---|
| `content/*.html` | Each page's body (header and footer are added by the build) |
| `content/privacy.md` | A copy of the app's privacy policy and terms (`docs/legal/privacy-policy-and-terms.md` in the app's repo) |
| `index.html`, `*/index.html`, `404.html`, `sitemap.xml` | **Generated** by `tools/build_site.py`: don't edit them by hand |
| `assets/css/site.css` | The one stylesheet (light and dark, mobile first) |
| `assets/img/` | Images: screenshots as WebP with JPEG fallbacks, the logo's mark, the dusk banner (`dusk.svg`), the Open Graph image, the Google Play badge |
| `assets/fonts/` | Sora (SIL Open Font Licence, `OFL.txt`), subset to Latin, self-hosted |
| `tools/` | `build_site.py` (the pages), `make_assets.py` (the images and the font) |

## Changing the site

```sh
python tools/build_site.py           # after editing content/ or the frame
python tools/build_site.py --check   # what CI runs: are the pages up to date?
```

**The privacy policy** is kept in step with the app: after the policy
changes in the app's repo, run

```sh
python tools/build_site.py --policy ../thermal_vario/docs/legal/privacy-policy-and-terms.md
```

and commit `content/privacy.md` and `privacy/index.html`.

**The testers' Google Group:** set `GOOGLE_GROUP_URL` in
`tools/build_site.py`, run the build and commit. Until then the beta page
asks testers to email.

**Images** (Pillow; fontTools and brotli for the font):

```sh
python tools/make_assets.py ../thermal_vario/Assets SCREENSHOTS_DIR ../thermal_vario/fonts/Sora-Variable.ttf
```

`SCREENSHOTS_DIR` holds 1080 px wide app screenshots named as in
`make_assets.py` (`SHOTS`), from the app's screenshot test on an Android
emulator over its generated demo flight.

## Rules

- Claim only what the released app does; mark what is being built or
  tested as such.
- No trackers, analytics, cookies or third-party requests.
- Nothing from the app's code, keys, secrets or pilots' flight files.
- The safety note stays in every page's footer: XC Core is a flight aid,
  not a certified instrument.

© 2026 Tarek Lasheen. Google Play and the Google Play logo are trademarks
of Google LLC.

#!/usr/bin/env python3
"""Makes the site's images and font from the app's brand assets.

  python tools/make_assets.py APP_ASSETS SCREENS [FONT]

APP_ASSETS  the app's `Assets` folder (the logo sheet, store/feature
            graphic, store/icon_1024.png, store/screenshots/*.png)
SCREENS     a folder of app screenshots (1080 px wide PNGs) named as in
            SHOTS below; the store screenshots are taken from APP_ASSETS
FONT        Sora's variable TTF (SIL Open Font Licence), subset to Latin

Writes assets/img/* (WebP for browsers that take it, JPEG or PNG as the
fallback), the favicons at the site's root and assets/fonts/sora.woff2.
Needs Pillow, and fontTools with brotli for the font. Nothing else from
the app is read or copied.
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")

# Store screenshots (Assets/store/screenshots/xccore_phone_N_1080x1920.png):
# their site names.
STORE = {
    1: "modes",
    2: "glance",
    3: "route",
    4: "speed",
    5: "ppg",
    6: "voice",
}
# App screenshots (SCREENS/<file>): their site names. Status and
# navigation bars are cut off.
SHOTS = {
    "2_thermal_3d.png": "thermal-3d",
    "3_xc_map.png": "xc-map",
    "7_flight_log.png": "flight-log",
}
WIDTHS = (360, 720)


def save_pair(im, name, widths=WIDTHS, quality=78):
    """[im] at each width as WebP and JPEG: name-<w>.webp / .jpg."""
    for w in widths:
        h = round(im.height * w / im.width)
        r = im.resize((w, h), Image.LANCZOS)
        r.save(os.path.join(IMG, "%s-%d.webp" % (name, w)), "WEBP",
               quality=quality, method=6)
        r.convert("RGB").save(os.path.join(IMG, "%s-%d.jpg" % (name, w)),
                              "JPEG", quality=quality + 4, optimize=True,
                              progressive=True)


def cut_bars(im, top=0.035, bottom=0.03):
    """An Android screenshot without its status and navigation bars."""
    return im.crop((0, round(im.height * top), im.width,
                    round(im.height * (1 - bottom))))


def mark_from_sheet(sheet_path):
    """The orange mark cut from the logo sheet (not redrawn), on a
    transparent background: the alpha from how far each pixel is from the
    tile's white towards the brand orange #F28C28."""
    sheet = Image.open(sheet_path).convert("RGB")
    box = (420, 280, 620, 540)
    tile = sheet.crop(box)
    out = Image.new("RGBA", tile.size)
    px, po = tile.load(), out.load()
    for y in range(tile.height):
        for x in range(tile.width):
            r, g, b = px[x, y]
            a = max(0, min(255, round((255 - b) * 255 / (255 - 40))))
            po[x, y] = (0xF2, 0x8C, 0x28, a)
    bbox = out.getbbox()
    return out.crop(bbox)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    assets, screens = argv[1], argv[2]
    font = argv[3] if len(argv) > 3 else None
    os.makedirs(IMG, exist_ok=True)

    for n, name in STORE.items():
        p = os.path.join(assets, "store", "screenshots",
                         "xccore_phone_%d_1080x1920.png" % n)
        save_pair(Image.open(p).convert("RGB"), "store-" + name)
    for f, name in SHOTS.items():
        save_pair(cut_bars(Image.open(os.path.join(screens, f))
                           .convert("RGB")), "app-" + name)

    fg = Image.open(os.path.join(assets, "store",
                                 "feature_graphic_1024x500.png")).convert("RGB")
    fg.save(os.path.join(IMG, "og-image.jpg"), "JPEG", quality=86,
            optimize=True)
    save_pair(fg, "feature-graphic", widths=(512, 1024), quality=82)

    mark = mark_from_sheet(os.path.join(assets, "7b · Stacked lockup@2x.png"))
    for h in (64, 128):
        w = round(mark.width * h / mark.height)
        m = mark.resize((w, h), Image.LANCZOS)
        m.save(os.path.join(IMG, "mark-%d.png" % h), optimize=True)
        m.save(os.path.join(IMG, "mark-%d.webp" % h), "WEBP", quality=90,
               method=6)

    icon = Image.open(os.path.join(assets, "store", "icon_1024.png")).convert("RGB")
    icon.save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32),
                                                        (48, 48)])
    icon.resize((32, 32), Image.LANCZOS).save(
        os.path.join(ROOT, "favicon-32.png"), optimize=True)
    icon.resize((180, 180), Image.LANCZOS).save(
        os.path.join(ROOT, "apple-touch-icon.png"), optimize=True)

    if font:
        from fontTools import subset
        out = os.path.join(ROOT, "assets", "fonts", "sora.woff2")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subset.main([
            font,
            "--unicodes=U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,"
            "U+02DC,U+2000-206F,U+20AC,U+2122,U+2190-2193,U+2212,U+00B0",
            "--layout-features=*",
            "--flavor=woff2",
            "--output-file=" + out,
        ])
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

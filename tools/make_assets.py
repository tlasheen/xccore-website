#!/usr/bin/env python3
"""Makes the site's images and font from the app's brand assets.

  python tools/make_assets.py APP_ASSETS SCREENS [FONT]

APP_ASSETS  the app's `Assets` folder (the logo sheet, store/feature
            graphic, store/icon_1024.png)
SCREENS     unused (kept for the command's shape); screenshots are made
            with --screens below
FONT        Sora's variable TTF (SIL Open Font Licence), subset to Latin

Writes assets/img/* (WebP for browsers that take it, JPEG or PNG as the
fallback), the favicons at the site's root and assets/fonts/sora.woff2.
Needs Pillow, and fontTools with brotli for the font. Nothing else from
the app is read or copied.

  python tools/make_assets.py --screens DIR

The carousel's and phone frames' screenshots: every DIR/<name>.png, taken
with the app at exactly 9:16 (adb shell wm size 1080x1920), becomes
assets/img/<name>-320/-640 .webp/.jpg at 9:16, never stretched: anything
not 9:16 is cut to it from the centre.

  python tools/make_assets.py --arabic-font CAIRO_TTF

Cairo's variable TTF (SIL Open Font Licence) subset to Arabic letters,
weight axis kept, as assets/fonts/cairo-arabic.woff2.
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")

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


def make_screens(folder):
    """Each 9:16 screenshot in [folder] at the carousel's two widths."""
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith(".png"):
            continue
        im = Image.open(os.path.join(folder, f)).convert("RGB")
        w, h = im.size
        if abs(w * 16 - h * 9) > 16:  # not 9:16: cut it to 9:16 from the centre
            if w * 16 > h * 9:
                nw = round(h * 9 / 16)
                im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = round(w * 16 / 9)
                im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        name = os.path.splitext(f)[0]
        for width in (320, 640):
            r = im.resize((width, round(width * 16 / 9)), Image.LANCZOS)
            r.save(os.path.join(IMG, "%s-%d.webp" % (name, width)), "WEBP",
                   quality=80, method=6)
            r.save(os.path.join(IMG, "%s-%d.jpg" % (name, width)), "JPEG",
                   quality=82, optimize=True, progressive=True)
        print("screen", name)


def arabic_font(ttf):
    """Cairo subset to Arabic, its weight axis kept and slant pinned."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    font = TTFont(ttf)
    if "slnt" in [a.axisTag for a in font["fvar"].axes]:
        font = instancer.instantiateVariableFont(font, {"slnt": 0})
    tmp = os.path.join(ROOT, "assets", "fonts", "_cairo.ttf")
    font.save(tmp)
    out = os.path.join(ROOT, "assets", "fonts", "cairo-arabic.woff2")
    try:
        subset.main([
            tmp,
            "--unicodes=U+0600-06FF,U+0750-077F,U+08A0-08FF,U+FB50-FDFF,"
            "U+FE70-FEFF,U+200C-200F",
            "--layout-features=*",
            "--flavor=woff2",
            "--output-file=" + out,
        ])
    finally:
        os.remove(tmp)
    print("font", out, os.path.getsize(out))


def main(argv):
    if len(argv) == 3 and argv[1] == "--screens":
        make_screens(argv[2])
        return 0
    if len(argv) == 3 and argv[1] == "--arabic-font":
        arabic_font(argv[2])
        return 0
    if len(argv) < 3:
        print(__doc__)
        return 2
    assets, screens = argv[1], argv[2]
    font = argv[3] if len(argv) > 3 else None
    os.makedirs(IMG, exist_ok=True)

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

"""pxkit - shared pixel-art kit for ONE MORE SHIFT.

Every asset in the game is drawn through this module so the look stays
consistent: one locked palette, ordered (Bayer) dithering instead of smooth
gradients, hard 1px ink outlines, no anti-aliasing, Galmuri bitmap font.

Game canvas: 320x180. Play area is letterboxed: y 22..157 (136px tall).
The top and bottom 22px bars are black and carry the HUD.
"""
from PIL import Image, ImageDraw, ImageFont
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(os.path.dirname(ROOT), "public", "assets")
PREVIEWS = os.path.join(ROOT, "previews")
FONT_DIR = os.path.join(ROOT, "tools", "fonts")

W, H = 320, 180
BAR = 22                      # letterbox bar height
PLAY = (0, BAR, W, H - BAR)   # x0, y0, x1, y1 of the play area (136px tall)

# ----------------------------------------------------------------- palette
def _h(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

PAL = {
    # ink + neutrals (cool, slightly purple - never pure grey)
    "ink": _h("14101a"), "ink2": _h("2a2233"),
    "grey1": _h("4a4458"), "grey2": _h("7b7689"), "grey3": _h("b3aebd"),
    "grey4": _h("dcd7e0"), "white": _h("f6f1e7"),
    # reds - the tension colour
    "red0": _h("4a0f1c"), "red1": _h("8c1526"), "red2": _h("c8202f"),
    "red3": _h("ef3b4a"), "red4": _h("ff8a86"),
    # oranges / wood / warm light
    "orange0": _h("7a3210"), "orange1": _h("c2571a"), "orange2": _h("f08a24"),
    "orange3": _h("f8b84a"), "orange4": _h("fde08a"),
    # signal yellow (credits, coins, UI accent)
    "yellow": _h("ffd42a"), "yellow2": _h("fff3a8"),
    # skin ramp
    "skin0": _h("8a4f3a"), "skin1": _h("d08a66"), "skin2": _h("f2b98f"),
    "skin3": _h("fbdcc0"),
    # greens
    "green0": _h("1f4a3a"), "green1": _h("3b8a5a"), "green2": _h("7fc77a"),
    "green3": _h("c9eaa2"),
    # blues
    "blue0": _h("1b2450"), "blue1": _h("2f4a9c"), "blue2": _h("4f86d9"),
    "blue3": _h("9ccdf2"), "blue4": _h("dff1fb"),
    # purples
    "purple0": _h("3a2460"), "purple1": _h("6a4ab0"), "purple2": _h("a78be0"),
    # browns
    "brown0": _h("3b2418"), "brown1": _h("6b4226"), "brown2": _h("a06a3c"),
    "brown3": _h("d2a36a"),
    # washed-out pastels for mundane walls / daylight
    "wall1": _h("e9e2c8"), "wall2": _h("cfd8c4"), "wall3": _h("b9c9d6"),
    "wall4": _h("f3d9d0"),
    # sickly entity tones
    "pale1": _h("9fb0a8"), "pale2": _h("d3e0d6"),
}
RAMPS = {
    "grey": ["ink", "ink2", "grey1", "grey2", "grey3", "grey4", "white"],
    "red": ["red0", "red1", "red2", "red3", "red4"],
    "orange": ["orange0", "orange1", "orange2", "orange3", "orange4"],
    "skin": ["skin0", "skin1", "skin2", "skin3"],
    "green": ["green0", "green1", "green2", "green3"],
    "blue": ["blue0", "blue1", "blue2", "blue3", "blue4"],
    "purple": ["purple0", "purple1", "purple2"],
    "brown": ["brown0", "brown1", "brown2", "brown3"],
}
_PAL_SET = set(PAL.values())


def col(c):
    """Resolve a palette name or rgb(a) tuple to an RGBA tuple."""
    if c is None:
        return None
    if isinstance(c, str):
        return PAL[c] + (255,)
    return tuple(c) + (255,) if len(c) == 3 else tuple(c)


# ------------------------------------------------------------------ canvas
def new(w=W, h=H, fill=None):
    return Image.new("RGBA", (w, h), col(fill) if fill else (0, 0, 0, 0))


def draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"          # never anti-alias
    return d


def px(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), col(c))


def rect(img, x, y, w, h, fill=None, outline=None):
    """Filled rect, x/y top-left, w/h in pixels (inclusive size)."""
    draw(img).rectangle([x, y, x + w - 1, y + h - 1], fill=col(fill), outline=col(outline))


def line(img, pts, c, width=1):
    draw(img).line(pts, fill=col(c), width=width)


def poly(img, pts, fill=None, outline=None):
    draw(img).polygon(pts, fill=col(fill), outline=col(outline))


def ellipse(img, x0, y0, x1, y1, fill=None, outline=None):
    draw(img).ellipse([x0, y0, x1, y1], fill=col(fill), outline=col(outline))


def paste(dst, src, x=0, y=0):
    """Alpha-composite src onto dst at x,y (clips safely)."""
    layer = Image.new("RGBA", dst.size, (0, 0, 0, 0))
    layer.paste(src, (x, y))
    dst.alpha_composite(layer)
    return dst


def flip(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


# --------------------------------------------------------------- dithering
_B2 = [[0, 2], [3, 1]]
_B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _thr(x, y, m):
    if m == 2:
        return (_B2[y % 2][x % 2] + 0.5) / 4.0
    return (_B4[y % 4][x % 4] + 0.5) / 16.0


def dither_grad(img, box, c1, c2, axis="y", m=4, t0=0.0, t1=1.0, mask=None):
    """Ordered-dither gradient from c1 to c2 inside box=(x0,y0,x1,y1) exclusive.

    axis: 'y' top->bottom, 'x' left->right, 'd' diagonal.
    m: 2 = coarse checkerboard look (PC-98), 4 = finer dot pattern.
    t0/t1: start/end mix amount (0 = all c1, 1 = all c2).
    mask: optional 'L' image, only pixels where mask>0 are written.
    """
    x0, y0, x1, y1 = box
    a, b = col(c1), col(c2)
    w, h = max(1, x1 - x0 - 1), max(1, y1 - y0 - 1)
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            if mask is not None and mask.getpixel((x, y)) == 0:
                continue
            if axis == "y":
                f = (y - y0) / h
            elif axis == "x":
                f = (x - x0) / w
            else:
                f = ((x - x0) / w + (y - y0) / h) / 2
            t = t0 + (t1 - t0) * f
            img.putpixel((x, y), b if t > _thr(x, y, m) else a)


def dither_ramp(img, box, colors, axis="y", m=4, mask=None):
    """Multi-stop dithered gradient through a list of palette colours."""
    x0, y0, x1, y1 = box
    n = len(colors) - 1
    for i in range(n):
        if axis == "y":
            a = y0 + (y1 - y0) * i // n
            b = y0 + (y1 - y0) * (i + 1) // n
            dither_grad(img, (x0, a, x1, b), colors[i], colors[i + 1], "y", m, mask=mask)
        else:
            a = x0 + (x1 - x0) * i // n
            b = x0 + (x1 - x0) * (i + 1) // n
            dither_grad(img, (a, y0, b, y1), colors[i], colors[i + 1], "x", m, mask=mask)


def dither_flat(img, box, c1, c2, level=0.5, m=2, mask=None):
    """Constant-density dither (level 0..1 of c2 over c1). 0.5 + m=2 = checkerboard."""
    dither_grad(img, box, c1, c2, "y", m, level, level, mask)


def dither_radial(img, cx, cy, r, c_in, c_out=None, m=4, box=None):
    """Dithered glow: c_in at centre fading out to c_out (None = leave pixels)."""
    a = col(c_in)
    b = col(c_out) if c_out else None
    x0, y0, x1, y1 = box or (cx - r, cy - r, cx + r + 1, cy + r + 1)
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r
            if d > 1:
                continue
            if (1 - d) > _thr(x, y, m):
                img.putpixel((x, y), a)
            elif b:
                img.putpixel((x, y), b)


def shade_mask(img):
    """'L' mask of the opaque pixels of img (useful as dither mask)."""
    return img.split()[3].point(lambda v: 255 if v > 0 else 0)


def tint_dither(img, c, level=0.5, m=2, box=None):
    """Overlay colour c on every opaque pixel at a dither density (darkening /
    red 'something is wrong' pass). Keeps the palette locked."""
    cc = col(c)
    x0, y0, x1, y1 = box or (0, 0, img.width, img.height)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if img.getpixel((x, y))[3] and level > _thr(x, y, m):
                img.putpixel((x, y), cc)
    return img


# ----------------------------------------------------------------- outline
def outline(img, c="ink", diag=False):
    """Add a 1px outline around the opaque pixels (sprite needs a 1px margin)."""
    cc = col(c)
    src = img.load()
    out = img.copy()
    o = out.load()
    w, h = img.size
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0:
                for dx, dy in nb:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and src[xx, yy][3] > 0:
                        o[x, y] = cc
                        break
    return out


def swap(img, mapping):
    """Recolour: mapping of palette-name -> palette-name."""
    m = {col(a): col(b) for a, b in mapping.items()}
    out = img.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if p[x, y] in m:
                p[x, y] = m[p[x, y]]
    return out


# -------------------------------------------------------------------- text
_FONT_SPECS = {
    7: ("Galmuri7.ttf", 8), 9: ("Galmuri9.ttf", 10), 11: ("Galmuri11.ttf", 12),
    "11b": ("Galmuri11-Bold.ttf", 12), 14: ("Galmuri14.ttf", 15),
}
_fonts = {}


def font(key=11, mult=1):
    k = (key, mult)
    if k not in _fonts:
        f, s = _FONT_SPECS[key]
        _fonts[k] = ImageFont.truetype(os.path.join(FONT_DIR, f), s * mult)
    return _fonts[k]


def text_size(s, f=11, mult=1):
    l, t, r, b = draw(new(4, 4)).textbbox((0, 0), s, font=font(f, mult))
    return r - l, b


def text(img, x, y, s, c="white", f=11, shadow=None, edge=None, mult=1, align="left"):
    """Pixel text. f: 7, 9, 11, '11b' (bold), 14. Hangul needs 9+ (11 is the body size).
    shadow: colour of a 1px down-right drop shadow. edge: colour of a 1px outline.
    mult: integer scale of the font (2 = chunky title text).
    Credit style from the reference = c='yellow', edge='ink', shadow='ink'."""
    d = draw(img)
    fo = font(f, mult)
    if align != "left":
        w, _ = text_size(s, f, mult)
        x = x - w // 2 if align == "center" else x - w
    if edge:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    d.text((x + dx, y + dy), s, font=fo, fill=col(edge))
    if shadow:
        off = 2 if edge else 1
        d.text((x + off, y + off), s, font=fo, fill=col(shadow))
        if edge:
            d.text((x + 1, y + off), s, font=fo, fill=col(shadow))
            d.text((x + off, y + 1), s, font=fo, fill=col(shadow))
    d.text((x, y), s, font=fo, fill=col(c))
    return img


# ------------------------------------------------------------- scene help
def letterbox(img):
    """Black out the HUD bars of a 320x180 frame."""
    rect(img, 0, 0, W, BAR, "ink")
    rect(img, 0, H - BAR, W, BAR, "ink")
    return img


def persp_floor(img, box, vx, c_line, rows=7, cols=12, spread=2.6, power=1.7):
    """Perspective grid on a floor. box=(x0,y0,x1,y1); y0 is the horizon edge,
    vx the vanishing-point x. Draws tile joints only (fill the floor first)."""
    x0, y0, x1, y1 = box
    hgt = y1 - y0
    for i in range(1, rows + 1):
        yy = y0 + int(hgt * (i / rows) ** power)
        line(img, [(x0, yy), (x1 - 1, yy)], c_line)
    wid = (x1 - x0)
    for i in range(-cols, cols + 1):
        top_x = vx + i * wid / (cols * 1.0) * 0.5
        bot_x = vx + i * wid / (cols * 1.0) * 0.5 * spread
        line(img, [(int(top_x), y0), (int(bot_x), y1 - 1)], c_line)
    # clip anything that spilled outside the box is the caller's job


# ------------------------------------------------------------ save / pack
def off_palette(img):
    """Return the set of opaque colours that are NOT in the palette."""
    bad = set()
    for _, c in (img.getcolors(maxcolors=1 << 24) or []):
        if c[3] and c[:3] not in _PAL_SET:
            bad.add(c[:3])
    return bad


def snap(img):
    """Force every opaque pixel to the nearest palette colour; alpha becomes 0/255."""
    out = img.copy()
    p = out.load()
    cache = {}
    pal = list(_PAL_SET)
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            if a < 128:
                p[x, y] = (0, 0, 0, 0)
                continue
            k = (r, g, b)
            if k not in _PAL_SET:
                if k not in cache:
                    cache[k] = min(pal, key=lambda q: (q[0]-r)**2 + (q[1]-g)**2 + (q[2]-b)**2)
                k = cache[k]
            p[x, y] = k + (255,)
    return out


def save(img, relpath, scale=4):
    """Snap to palette, save 1x to assets/<relpath> and an Nx preview to previews/."""
    img = snap(img)
    a = os.path.join(ASSETS, relpath)
    p = os.path.join(PREVIEWS, relpath)
    os.makedirs(os.path.dirname(a), exist_ok=True)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(a)
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(p)
    return a


def sheet(frames, relpath, names=None, cols=None, scale=4, pad=0):
    """Pack equal-size frames into a grid sheet + Phaser-compatible atlas JSON
    (assets/<relpath>.png and .json). frames: list of images. names: frame names."""
    fw, fh = frames[0].size
    n = len(frames)
    cols = cols or min(n, 8)
    rows = (n + cols - 1) // cols
    out = new(cols * (fw + pad), rows * (fh + pad))
    meta = {}
    for i, fr in enumerate(frames):
        x, y = (i % cols) * (fw + pad), (i // cols) * (fh + pad)
        out.paste(fr, (x, y))
        nm = names[i] if names else str(i)
        meta[nm] = {"frame": {"x": x, "y": y, "w": fw, "h": fh},
                    "sourceSize": {"w": fw, "h": fh},
                    "spriteSourceSize": {"x": 0, "y": 0, "w": fw, "h": fh}}
    png = relpath if relpath.endswith(".png") else relpath + ".png"
    save(out, png, scale)
    js = os.path.join(ASSETS, png[:-4] + ".json")
    with open(js, "w") as f:
        json.dump({"frames": meta, "meta": {"image": os.path.basename(png),
                   "size": {"w": out.width, "h": out.height}, "scale": 1,
                   "frameWidth": fw, "frameHeight": fh}}, f, indent=1)
    return out


def contact(paths, out_relpath, cols=4, scale=2, bg="ink2", label=True):
    """Preview-only contact sheet of asset files (not saved into assets/)."""
    ims = [Image.open(os.path.join(ASSETS, p)).convert("RGBA") for p in paths]
    ims = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in ims]
    cw = max(i.width for i in ims) + 8
    ch = max(i.height for i in ims) + 20
    rows = (len(ims) + cols - 1) // cols
    out = new(cols * cw, rows * ch, bg)
    for k, im in enumerate(ims):
        x, y = (k % cols) * cw + 4, (k // cols) * ch + 4
        out.alpha_composite(im, (x, y))
        if label:
            text(out, x, y + im.height + 2, os.path.basename(paths[k])[:-4][: cw // 6], "grey3", 9)
    p = os.path.join(PREVIEWS, out_relpath)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    out.save(p)
    return p

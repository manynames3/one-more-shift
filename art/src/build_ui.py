"""build_ui.py - ONE MORE SHIFT UI art (logo, dialogs, cards, HUD, buttons, stamps,
pay stub, phone, cursors, vignettes, font preview). Run: python3 src/build_ui.py"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import pxkit
from pxkit import *
from functools import lru_cache

SAVED = []


def S(img, name, scale=4):
    bad = off_palette(img)
    assert not bad, (name, bad)
    save(img, "ui/" + name + ".png", scale)
    SAVED.append("ui/" + name + ".png")
    return img


# ------------------------------------------------------------------ helpers
def hz(x, y=0, s=0):
    n = (x * 374761393 + y * 668265263 + s * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65535.0


def clear(img, x, y):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (0, 0, 0, 0))


@lru_cache(None)
def tbox(s, f=11, mult=1):
    tmp = new(300, 80)
    text(tmp, 16, 16, s, "white", f, mult=mult)
    bb = tmp.getbbox()
    return bb[0] - 16, bb[1] - 16, bb[2] - bb[0], bb[3] - bb[1]


def put(img, x, y, s, c="white", f=11, mult=1, edge=None, shadow=None):
    """Place text so that its pixel bbox top-left sits at x,y."""
    ox, oy, w, h = tbox(s, f, mult)
    text(img, x - ox, y - oy, s, c, f, shadow=shadow, edge=edge, mult=mult)
    return w, h


def putc(img, cx, cy, s, c="white", f=11, mult=1, edge=None, shadow=None):
    ox, oy, w, h = tbox(s, f, mult)
    return put(img, cx - w // 2, cy - h // 2, s, c, f, mult, edge, shadow)


def putr(img, xr, y, s, c="white", f=11, mult=1, edge=None, shadow=None):
    ox, oy, w, h = tbox(s, f, mult)
    return put(img, xr - w, y, s, c, f, mult, edge, shadow)


def rr_cells(w, h, r):
    cuts = {0: [], 1: [1], 2: [2, 1], 3: [3, 1, 1], 4: [4, 2, 1, 1]}[r]
    cells = set()
    for yy in range(h):
        for xx in range(w):
            ins = 0
            if yy < len(cuts):
                ins = cuts[yy]
            elif h - 1 - yy < len(cuts):
                ins = cuts[h - 1 - yy]
            if ins <= xx < w - ins:
                cells.add((xx, yy))
    return cells


def rrect(img, x, y, w, h, fill=None, outline=None, r=1):
    cells = rr_cells(w, h, r)
    for (xx, yy) in cells:
        edge = any((xx + dx, yy + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c = outline if (edge and outline) else fill
        if c:
            px(img, x + xx, y + yy, c)
    return cells


def disc(img, cx, cy, r, fill=None, outline=None):
    for y in range(int(cy - r - 2), int(cy + r + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d <= r * r:
                inner = d <= (r - 1) ** 2
                if outline and not inner:
                    px(img, x, y, outline)
                elif fill:
                    px(img, x, y, fill)


def drop_dither(im, dx, dy, c="ink"):
    a = im.split()[3].load()
    w, h = im.size
    pts = []
    for y in range(h):
        for x in range(w):
            if a[x, y] == 0:
                sx, sy = x - dx, y - dy
                if 0 <= sx < w and 0 <= sy < h and a[sx, sy] > 0 and (x + y) % 2 == 0:
                    pts.append((x, y))
    for x, y in pts:
        px(im, x, y, c)


def dline(img, x0, y0, n, c, horiz=True, on=2, off=2):
    for i in range(n):
        if i % (on + off) < on:
            px(img, x0 + i if horiz else x0, y0 if horiz else y0 + i, c)


# ---------------------------------------------------------- chunky lettering
GLY = {
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#...."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
}


def glyph_mask(s, sc, gap):
    x = 0
    cells = []
    for ch in s:
        if ch == " ":
            x += 3 * sc
            continue
        cells.append((ch, x))
        x += 5 * sc + gap
    w = x - gap
    m = Image.new("L", (w, 5 * sc), 0)
    for ch, x0 in cells:
        for r, row in enumerate(GLY[ch]):
            for c, v in enumerate(row):
                if v == "#":
                    m.paste(255, (x0 + c * sc, r * sc, x0 + (c + 1) * sc, (r + 1) * sc))
    return m


def chunky(m, face="yellow", hi="yellow2", lo="orange2", ext="red1", n=2, edge="ink"):
    w, h = m.size
    out = new(w + n + 2, h + n + 2)
    mp = m.load()

    def inm(x, y):
        return 0 <= x < w and 0 <= y < h and mp[x, y] > 0
    for k in range(n, 0, -1):
        for y in range(h):
            for x in range(w):
                if mp[x, y]:
                    px(out, 1 + x + k, 1 + y + k, ext)
    for y in range(h):
        for x in range(w):
            if mp[x, y]:
                c = face
                if not inm(x, y - 1):
                    c = hi
                elif not inm(x, y + 1):
                    c = lo
                px(out, 1 + x, 1 + y, c)
    return outline(out, edge, diag=True)


# ------------------------------------------------------------------- icons
def clock(r=7, mdeg=0, hdeg=300, shadow=True, ticks=False):
    import math
    n = 2 * r + 2
    im = new(n, n)
    c = r
    if shadow:
        disc(im, c + 1, c + 1, r, "ink2", None)
    disc(im, c, c, r, "white", "ink")
    # lower-right cel shade
    for y in range(n):
        for x in range(n):
            if im.getpixel((x, y)) == col("white"):
                if im.getpixel((min(x + 1, n - 1), y)) == col("ink") or im.getpixel((x, min(y + 1, n - 1))) == col("ink"):
                    if x + y > 2 * c - 1:
                        px(im, x, y, "grey3")
    if ticks:
        for a in range(0, 360, 90):
            tx = c + round(math.sin(math.radians(a)) * (r - 2))
            ty = c - round(math.cos(math.radians(a)) * (r - 2))
            px(im, tx, ty, "grey2")

    def hand(deg, ln, colr):
        ex = c + round(math.sin(math.radians(deg)) * ln)
        ey = c - round(math.cos(math.radians(deg)) * ln)
        line(im, [(c, c), (ex, ey)], colr)
    hand(hdeg, max(2, r - 4), "ink")
    hand(mdeg, r - 2, "red2")
    px(im, c, c, "ink")
    return im


def coin(d=12):
    im = new(d, d)
    r = (d - 1) / 2
    disc(im, r, r, r, "yellow", "ink")
    # inner ring + shade + highlight
    for y in range(d):
        for x in range(d):
            if im.getpixel((x, y)) == col("yellow"):
                if (x - r) + (y - r) > r * 0.9:
                    px(im, x, y, "orange3")
    px(im, 3, 3, "yellow2"); px(im, 4, 3, "yellow2"); px(im, 3, 4, "yellow2")
    mid = d // 2
    for yy in range(mid - 2, mid + 2):
        px(im, mid - 1, yy, "orange1")
        px(im, mid, yy, "orange1")
    return im


def time_card(w=14, h=18):
    im = new(w, h)
    rect(im, 0, 0, w, h, "white", "ink")
    rect(im, 1, 1, w - 2, 4, "red2")
    px(im, 1, 4, "red1")
    for x in range(1, w - 1):
        px(im, x, 4, "red1")
    px(im, w // 2, 2, "white")
    for yy in (7, 10, 13):
        rect(im, 3, yy, w - 6, 1, "grey3")
    rect(im, 3, 15, 5, 1, "red2")
    for y in range(1, h - 1):
        px(im, w - 2, y, "grey4") if y > 4 else None
    return im


# ------------------------------------------------------------------- 1 LOGO
def logo():
    im = new(160, 64)
    one = chunky(glyph_mask("ONE MORE", 2, 2), n=1)
    shift = chunky(glyph_mask("SHIFT", 4, 4), n=3)
    paste(im, one, (160 - one.width) // 2, 1)
    paste(im, shift, (160 - shift.width) // 2, 14)
    # korean line
    kw, kh = tbox("한 번만 더", 14)[2:]
    put(im, (160 - kw) // 2, 45, "한 번만 더", "white", 14, edge="ink", shadow="red1")
    paste(im, time_card(), 28, 43)
    paste(im, clock(8, 0, 330, ticks=True), 116, 43)
    return im


def logo_small():
    im = new(96, 24)
    cl = clock(8, 0, 330, ticks=True)
    one = chunky(glyph_mask("ONE MORE", 1, 1), n=1)
    shift = chunky(glyph_mask("SHIFT", 2, 2), n=1)
    tw = max(one.width, shift.width)
    total = cl.width + 4 + tw
    x0 = (96 - total) // 2
    paste(im, cl, x0, (24 - cl.height) // 2)
    paste(im, one, x0 + cl.width + 4, 2)
    paste(im, shift, x0 + cl.width + 4, 9)
    return im


# ----------------------------------------------------------- 2 DIALOG PARTS
def panel(w, h):
    im = new(w, h)
    rect(im, 0, 0, w, h, "ink")
    rect(im, 1, 1, w - 2, h - 2, None, "white")
    rect(im, 3, 3, w - 6, h - 6, None, "white")
    for k, lvl in enumerate((0.875, 0.5, 0.125)):
        i = 4 + k
        for x in range(i, w - i):
            for y in range(i, h - i):
                if x in (i, w - 1 - i) or y in (i, h - 1 - i):
                    if lvl > pxkit._thr(x, y, 2):
                        px(im, x, y, "ink2")
    for (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        clear(im, x, y)
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2), (3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):
        px(im, x, y, "ink")
    return im


def dialog():
    im = panel(300, 44)
    for y in range(3, 41):
        px(im, 64, y, "white"); px(im, 65, y, "ink"); px(im, 66, y, "white")
    for k, lvl in enumerate((0.875, 0.5, 0.125)):
        x = 67 + k
        for y in range(7, 37):
            if lvl > pxkit._thr(x, y, 2):
                px(im, x, y, "ink2")
    for y in range(4, 40):
        for x in range(4, 64):
            clear(im, x, y)
    return im


def name_tag():
    im = new(56, 12)
    rect(im, 0, 0, 56, 12, "ink")
    rect(im, 1, 1, 54, 10, None, "white")
    for x in range(2, 54):
        if x % 2 == 0:
            px(im, x, 2, "ink2")
        if x % 2 == 1:
            px(im, x, 9, "ink2")
    for (x, y) in ((0, 0), (55, 0), (0, 11), (55, 11)):
        clear(im, x, y)
    for (x, y) in ((1, 1), (54, 1), (1, 10), (54, 10)):
        px(im, x, y, "ink")
    rect(im, 4, 4, 3, 4, "yellow")
    rect(im, 4, 7, 3, 1, "orange2")
    return im


# -------------------------------------------------------------- 3 JOB CARD
def job_card(labels=True):
    w, h = 120, 88
    im = new(w, h)
    pw, ph = 117, 85
    rect(im, 0, 0, pw, ph, "white", "ink")
    dither_grad(im, (1, 60, pw - 1, ph - 1), "white", "wall1", "y", m=4, t0=0.0, t1=0.5)
    # header band
    rect(im, 1, 1, pw - 2, 19, "blue1")
    dither_grad(im, (1, 1, pw - 1, 8), "blue2", "blue1", "y", m=2, t0=0.9, t1=0.0)
    rect(im, 1, 19, pw - 2, 1, "blue0")
    rect(im, 1, 20, pw - 2, 1, "ink")
    # tack
    disc(im, 59, 6, 3, "red3", "ink")
    px(im, 58, 5, "red4"); px(im, 59, 9, "ink2"); px(im, 61, 8, "ink2")
    px(im, 60, 7, "red2"); px(im, 61, 6, "red2")
    if labels:
        putc(im, 58, 14, "오늘의 알바", "white", "11b", shadow="blue0")
    # rows
    for i, lab in enumerate(("장소", "시급")):
        y0 = 25 + i * 14
        if labels:
            put(im, 7, y0, lab, "grey1", 9)
        rect(im, 30, y0 + 9, 80, 1, "blue3")
        for x in range(30, 110, 4):
            px(im, x, y0 + 10, "grey4")
    # rule box
    bx, by, bw, bh = 6, 55, 105, 26
    rect(im, bx, by, bw, bh, "white", "red2")
    rect(im, bx + 1, by + 1, bw - 2, bh - 2, None, "red3")
    for x in range(bx + 1, bx + bw - 1):
        for y in (by + 1, by + bh - 2):
            if (x + y) % 2 == 0:
                px(im, x, y, "white")
    for y in range(by + 1, by + bh - 1):
        for x in (bx + 1, bx + bw - 2):
            if (x + y) % 2 == 0:
                px(im, x, y, "white")
    for yy in (by + 12, by + 19):
        rect(im, bx + 5, yy, bw - 10, 1, "grey4")
    # tab
    rect(im, bx + 4, by - 6, 23, 13, "red2", "ink")
    rect(im, bx + 5, by - 5, 21, 1, "red3")
    if labels:
        putc(im, bx + 15, by, "규칙", "white", 9, shadow="red0")
    drop_dither(im, 3, 3)
    return im


# ---------------------------------------------------------------- 4 HUD
def slot(w, h, rim="grey3"):
    im = new(w, h)
    rrect(im, 0, 0, w, h, "ink", rim, r=1)
    rect(im, 2, 2, w - 4, h - 4, "ink2")
    for x in range(2, w - 2):
        px(im, x, 2, "ink")
    return im


def rule_banner():
    im = new(320, 22, "ink")
    for x in range(0, 320):
        for y in range(2, 20):
            if x < 28:
                s = (x + y) // 3
            elif x >= 292:
                s = (319 - x + y) // 3
            else:
                continue
            px(im, x, y, "red2" if s % 2 == 0 else "ink")
    for x in list(range(0, 28)) + list(range(292, 320)):
        px(im, x, 1, "red1"); px(im, x, 20, "red1")
        px(im, x, 0, "ink"); px(im, x, 21, "ink")
    for y in range(1, 21):
        px(im, 28, y, "red1"); px(im, 291, y, "red1")
    # middle plate
    rect(im, 30, 2, 260, 18, "ink2", "grey1")
    for x in range(31, 289):
        px(im, x, 3, "ink")
    # icon slot (18x18 at 34,2)
    rect(im, 34, 2, 18, 18, "ink", "grey3")
    rect(im, 35, 3, 16, 16, "ink2")
    for y in range(3, 19):
        for x in range(35, 51):
            if (x + y) % 2 == 0:
                px(im, x, y, "ink")
    # text well
    rect(im, 56, 4, 230, 14, "ink")
    for x in range(56, 286):
        if x % 2 == 0:
            px(im, x, 17, "ink2")
    # bottom edge
    rect(im, 0, 21, 320, 1, "red1")
    return im


def hud_bottom():
    im = new(320, 22, "ink")
    rect(im, 0, 0, 320, 1, "red1")
    paste(im, clock(5, 0, 120, shadow=False), 30, 5)
    paste(im, timer_frame(), 44, 5)
    paste(im, coin(12), 110, 5)
    paste(im, slot(60, 12), 125, 5)
    putc(im, 214, 11, "빚", "red3", 9)
    paste(im, debt_meter_frame(), 224, 7)
    return im


def timer_frame():
    return slot(40, 12)


def debt_meter_frame():
    im = new(64, 8)
    rrect(im, 0, 0, 64, 8, "ink", "grey3", r=1)
    rect(im, 2, 2, 60, 4, "ink2")
    for x in range(2, 62):
        px(im, x, 2, "ink")
    for x in (17, 32, 47):
        for y in (2, 3, 4, 5):
            px(im, x, y, "grey1")
    return im


def debt_meter_fill():
    im = new(60, 4)
    for x in range(60):
        px(im, x, 0, "red4" if x % 2 == 0 else "red3")
        for y in (1, 2):
            px(im, x, y, "red3" if (x + y) % 2 == 0 else "red2")
        px(im, x, 3, "red1" if x % 2 == 0 else "red2")
    return im


# -------------------------------------------------------------- 6 BUTTONS
BTN = {
    "green": {"n": ("green2", "green1", "green0"), "h": ("green3", "green2", "green1"), "p": ("green1", "green1", "green0")},
    "grey": {"n": ("grey3", "grey2", "grey1"), "h": ("grey4", "grey3", "grey2"), "p": ("grey2", "grey2", "grey1")},
    "red": {"n": ("red3", "red2", "red1"), "h": ("red4", "red3", "red2"), "p": ("red2", "red2", "red1")},
}


def button(kind, state):
    hi, base, lo = BTN[kind][state]
    im = new(72, 18)
    cells = rrect(im, 0, 0, 72, 18, base, "ink", r=2)
    pressed = state == "p"
    for (x, y) in cells:
        if (x, y) in rr_cells(72, 18, 2):
            e = any((x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if e:
                continue
            if pressed:
                if y == 1:
                    px(im, x, y, lo)
                elif y == 2:
                    px(im, x, y, lo if (x % 2 == 0) else base)
                elif y == 16:
                    px(im, x, y, lo)
            else:
                if y == 1:
                    px(im, x, y, hi)
                elif y == 2:
                    px(im, x, y, hi if (x % 2 == 0) else base)
                elif y >= 15:
                    px(im, x, y, lo)
    if state == "h":
        for x in range(2, 70):
            if x % 2 == 0:
                px(im, x, 15, base)
    return im


def label(s, f="11b"):
    ox, oy, w, h = tbox(s, f)
    im = new(w + 2, h + 2)
    put(im, 0, 0, s, "white", f, shadow="ink")
    return im


# --------------------------------------------------------------- 7 STAMPS
def stamp(txt, c1, c2, solid=False, f="11b", mult=1, seed=1):
    w, h = 72, 28
    im = new(w, h)
    rect(im, 0, 0, w, h, c1 if solid else None, c1)
    rect(im, 1, 1, w - 2, h - 2, None, c1)
    if not solid:
        rect(im, 3, 3, w - 6, h - 6, None, c1)
    tx = new(w, h)
    putc(tx, w // 2, h // 2, txt, "white", f, mult=mult)
    T = set()
    for y in range(h):
        for x in range(w):
            if tx.getpixel((x, y))[3]:
                T.add((x, y))
                if solid:
                    clear(im, x, y)
                else:
                    px(im, x, y, c1)
    a = im.load()
    pts = []
    for y in range(h):
        for x in range(w):
            if not a[x, y][3]:
                continue
            nb = 0
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                out = not (0 <= xx < w and 0 <= yy < h) or (not a[xx, yy][3] and (xx, yy) not in T)
                nb += out
            if (x, y) in T:
                p = 0.05
            else:
                p = 0.28 if nb else 0.04
            if hz(x, y, seed) < p:
                pts.append((x, y, None))
            elif hz(x // 3, y // 3, seed + 7) < 0.30 and (x + y) % 2 == 0:
                pts.append((x, y, c2))
    for x, y, c in pts:
        if c is None:
            clear(im, x, y)
        else:
            px(im, x, y, c)
    return im


# -------------------------------------------------------------- 8 PAY STUB
def paystub(stamp_img=None, vals=None, logo_img=None):
    PW, PH = 176, 235
    pap = new(PW, PH, "white")
    dither_grad(pap, (0, PH - 16, PW, PH), "white", "grey4", "y", m=4, t0=0, t1=0.7)
    paste(pap, logo_img, (PW - 96) // 2, 7)
    put(pap, 10, 37, "급여명세서", "ink", "11b")
    putr(pap, 166, 40, "PAY STUB", "grey2", 9)
    rect(pap, 8, 52, 160, 1, "ink")
    dline(pap, 8, 54, 160, "grey3", True, 1, 1)
    labels = ["근무지", "버틴 교대", "시급", "총 수령액", "사인", "남은 빚"]
    for i, lab in enumerate(labels):
        y0 = 57 + i * 20
        if i == 3:
            rect(pap, 4, y0, 168, 20, "yellow2")
        elif i % 2 == 0:
            rect(pap, 4, y0, 168, 20, "wall1")
        put(pap, 10, y0 + 5, lab, "grey1", 9)
        rect(pap, 62, y0 + 17, 104, 1, "grey3")
        if vals:
            col_ = "red2" if i == 5 else "ink"
            put(pap, 66, y0 + 4, vals[i], col_, "11b" if i in (3, 5) else 11)
    # fine print + stamp area
    put(pap, 10, 182, "NO. 0417-0008", "grey2", 7)
    for i, wd in enumerate((70, 54, 62)):
        rect(pap, 10, 193 + i * 5, wd, 1, "grey4")
    if stamp_img is None:
        sx, sy = 96, 181
        dline(pap, sx, sy, 72, "grey3", True, 2, 2)
        dline(pap, sx, sy + 27, 72, "grey3", True, 2, 2)
        dline(pap, sx, sy, 28, "grey3", False, 2, 2)
        dline(pap, sx + 71, sy, 28, "grey3", False, 2, 2)
        putc(pap, sx + 36, sy + 14, "STAMP", "grey3", 7)
    # barcode
    x = 14
    i = 0
    while x < 160:
        wb = 1 + int(hz(i, 3) * 3)
        gp = 1 + int(hz(i, 7) * 2)
        if x + wb > 162:
            break
        ext = 2 if (i < 2 or x > 150) else 0
        rect(pap, x, 211, wb, 14 + ext, "ink")
        x += wb + gp
        i += 1
    # mask: torn top, scalloped bottom
    mask = Image.new("L", (PW, PH), 255)
    for x in range(PW):
        d = int(hz(x // 3, 1) * 4)
        for y in range(d):
            mask.putpixel((x, y), 0)
    for cx in range(4, PW, 8):
        for y in range(PH - 4, PH):
            for xx in range(cx - 4, cx + 5):
                if 0 <= xx < PW and (xx - cx) ** 2 + (y - PH) ** 2 <= 10:
                    mask.putpixel((xx, y), 0)
    pap.putalpha(mask)
    full = new(180, 240)
    paste(full, pap, 1, 1)
    full = outline(full, "ink")
    drop_dither(full, 3, 3)
    if stamp_img is not None:
        paste(full, stamp_img, 100, 179)
    return full


# -------------------------------------------------------------- 9 PHONE
def phone_screen():
    sc = new(62, 96)
    dither_grad(sc, (0, 0, 62, 96), "blue4", "blue3", "y", m=4, t0=0, t1=0.7)
    rect(sc, 0, 0, 62, 7, "ink2")
    for i, hh in enumerate((2, 3, 4)):
        rect(sc, 44 + i * 3, 5 - hh, 2, hh, "grey4")
    rect(sc, 53, 1, 7, 4, None, "grey4")
    rect(sc, 54, 2, 4, 2, "green2")
    px(sc, 60, 2, "grey4")
    rect(sc, 3, 2, 8, 2, "grey3")
    rect(sc, 0, 7, 62, 13, "blue1")
    rect(sc, 0, 19, 62, 1, "blue0")
    for (x, y) in ((5, 11), (4, 12), (3, 13), (4, 14), (5, 15)):
        px(sc, x, y, "white")
    disc(sc, 14, 13, 3, "yellow", "ink")
    rect(sc, 20, 11, 18, 2, "white")
    rect(sc, 20, 15, 10, 2, "blue3")
    # bubble
    rrect(sc, 3, 24, 38, 13, "white", "ink", r=2)
    rect(sc, 7, 28, 24, 2, "grey3")
    rect(sc, 7, 32, 14, 2, "grey3")
    # offer card
    rrect(sc, 3, 41, 56, 54, "white", "ink", r=2)
    rect(sc, 4, 42, 54, 14, "orange3")
    dither_grad(sc, (4, 50, 58, 56), "orange3", "orange2", "y", m=2, t0=0.2, t1=1.0)
    rect(sc, 4, 56, 54, 1, "ink")
    paste(sc, coin(11), 6, 43)
    put(sc, 20, 46, "새 알바", "brown0", 9)
    put(sc, 7, 59, "시급", "grey2", 9)
    put(sc, 7, 70, "₩12,400", "ink", 9)
    # accept button
    b = rrect(sc, 7, 81, 48, 12, "green1", "ink", r=1)
    rect(sc, 8, 82, 46, 1, "green2")
    rect(sc, 8, 91, 46, 1, "green0")
    putc(sc, 31, 86, "ACCEPT", "white", 7, shadow="green0")
    return sc


def phone(with_screen=True):
    im = new(72, 120)
    rrect(im, 0, 0, 72, 120, "grey1", "ink", r=4)
    for x in range(4, 68):
        px(im, x, 1, "grey2")
    for y in range(4, 116):
        px(im, 1, y, "grey2")
    for x in range(4, 68):
        px(im, x, 118, "ink2")
    for y in range(4, 116):
        px(im, 70, y, "ink2")
    rect(im, 3, 10, 66, 100, "ink")
    rect(im, 28, 4, 16, 2, "ink2")
    rect(im, 28, 4, 16, 1, "ink")
    rect(im, 48, 4, 3, 3, "blue1")
    px(im, 48, 4, "blue3")
    disc(im, 36, 115, 3, "grey2", "ink")
    px(im, 35, 114, "grey3")
    if with_screen:
        paste(im, phone_screen(), 5, 12)
    else:
        for y in range(12, 108):
            for x in range(5, 67):
                clear(im, x, y)
    return im


# ------------------------------------------------------ 10 CURSORS ETC
def bitmap(rows, pal):
    im = new(len(rows[0]), len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal:
                px(im, x, y, pal[ch])
    return im


ARROW = [
    "#...........",
    "##..........",
    "#o#.........",
    "#oo#........",
    "#ooo#.......",
    "#oooo#......",
    "#ooooo#.....",
    "#oooooo#....",
    "#ooooo####..",
    "#oo#oo#.....",
    "#o#.#oo#....",
    "##...##.....",
]
HAND = [
    "....##......",
    "...#oo#.....",
    "...#oo#.....",
    "...#oo#.....",
    "...#oo###...",
    "...#oo#oo##.",
    ".###oo#oo#o#",
    "#oo#oooooo#.",
    "#ooooooooo#.",
    ".#ooooooooo#",
    "..#ooooooo#.",
    "..#########.",
]


def loading():
    fr = []
    for i in range(4):
        fr.append(clock(7, i * 90, 300 + i * 22.5 if False else i * 30))
    return fr


def vignette(c0, c1):
    im = new(320, 180)
    cx, cy = 159.5, 22 + 67.5
    for y in range(22, 158):
        for x in range(320):
            nx = abs(x - cx) / 160.0
            ny = abs(y - cy) / 68.0
            d = (nx ** 3 + ny ** 3) ** (1 / 3.0)
            t = (d - 0.62) / 0.5
            if t <= 0:
                continue
            t = min(1.0, t) ** 1.3
            if t > 0.93:
                px(im, x, y, c1)
            elif t > pxkit._thr(x, y, 2):
                px(im, x, y, c0)
    return im


# ------------------------------------------------------ 11 FONT PREVIEW
def font_preview():
    im = new(300, 150, "ink2")
    rect(im, 0, 0, 300, 150, None, "grey1")
    y = 8
    put(im, 8, y, "BODY  Galmuri 11  white", "grey2", 9)
    put(im, 8, y + 13, "규칙을 어기면 이번 교대는 끝입니다.", "white", 11)
    put(im, 8, y + 28, "Break the rule and the shift is over.", "white", 11)
    rect(im, 8, y + 44, 284, 1, "grey1")
    y = 58
    put(im, 8, y, "SMALL  Galmuri 9  grey", "grey2", 9)
    put(im, 8, y + 13, "야간 근무 3/7 · 시급 ₩12,400 · 남은 빚", "grey3", 9)
    put(im, 8, y + 26, "Night shift 3/7 - wage 12,400 - debt left", "grey3", 9)
    rect(im, 8, y + 40, 284, 1, "grey1")
    y = 102
    rect(im, 1, y - 2, 298, 47, "red0")
    dither_grad(im, (1, y - 2, 299, y + 45), "red0", "red1", "y", m=2, t0=0.0, t1=0.5)
    put(im, 8, y, "ACCENT  11 bold  yellow + ink edge/shadow", "grey4", 9)
    put(im, 8, y + 14, "한 번만 더 - 퇴근 성공!", "yellow", "11b", edge="ink", shadow="ink")
    put(im, 8, y + 29, "ONE MORE SHIFT  GAME OVER", "yellow", "11b", edge="ink", shadow="ink")
    return im


# ======================================================================= MAIN
if __name__ == "__main__":
    LOGO_S = logo_small()
    S(logo(), "logo")
    S(LOGO_S, "logo_small")
    S(dialog(), "dialog_box")
    S(panel(24, 24), "dialog_9slice", 8)
    S(name_tag(), "name_tag")
    S(job_card(True), "job_card")
    S(job_card(False), "job_card_blank")
    S(rule_banner(), "rule_banner", 3)
    S(hud_bottom(), "hud_bottom", 3)
    S(debt_meter_frame(), "debt_meter_frame", 8)
    S(debt_meter_fill(), "debt_meter_fill", 8)
    S(timer_frame(), "timer_frame", 8)
    for k, nm in (("green", "btn_primary"), ("grey", "btn_secondary"), ("red", "btn_danger")):
        sheet([button(k, s) for s in "nhp"], "ui/" + nm, ["normal", "hover", "pressed"], cols=3, scale=4)
        SAVED.append("ui/" + nm + ".png")
    for nm, s in (("lbl_clockin", "출근"), ("lbl_clockout", "퇴근"), ("lbl_retry", "다시"),
                  ("lbl_share", "공유"), ("lbl_accept", "ACCEPT"), ("lbl_quit", "QUIT")):
        S(label(s), nm, 8)
    sf = stamp("퇴근 성공", "green1", "green2", seed=3)
    sx = stamp("퇴근 실패", "red2", "red3", seed=5)
    sd = stamp("해 고", "red2", "red3", seed=9)
    S(sf, "stamp_success", 6)
    S(sx, "stamp_fail", 6)
    S(sd, "stamp_fired", 6)
    S(paystub(None, None, LOGO_S), "paystub", 3)
    vals = ["달빛 편의점 야간", "7번째 교대", "₩12,400", "₩86,800", "문 앞 인사 위반", "₩4,213,000"]
    S(paystub(sx, vals, LOGO_S), "paystub_example", 3)
    S(phone(True), "phone_ui", 6)
    S(phone(False), "phone_frame", 6)
    S(bitmap(ARROW, {"#": "ink", "o": "white"}), "cursor", 12)
    S(bitmap(HAND, {"#": "ink", "o": "white"}), "cursor_hand", 12)
    sheet(loading(), "ui/loading", ["f0", "f1", "f2", "f3"], cols=4, scale=8)
    SAVED.append("ui/loading.png")
    S(vignette("red1", "red0"), "vignette_red", 3)
    S(vignette("ink", "ink"), "vignette_dark", 3)
    S(font_preview(), "font_preview", 3)
    # palette audit over everything on disk
    for p in glob.glob(os.path.join(ASSETS, "ui", "*.png")):
        b = off_palette(Image.open(p).convert("RGBA"))
        assert not b, (p, b)
    contact(SAVED, "_contact/ui.png", cols=4, scale=2)
    print("ok", len(SAVED))

"""Interior backgrounds: convenience store (day / wrong / fg), temp agency office, stock room.

Run:  python3 src/build_bg_interior.py
Writes assets/bg/*.png (+4x previews in previews/bg/) and previews/_contact/bg_interior.png
"""
import sys, os, random, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from pxkit import *
import pxkit
from PIL import Image, ImageDraw

thr = pxkit._thr

# --------------------------------------------------------------------------
# projection shared by the store and the stock room
# eye at (160, VY); camera looks down the +z axis; z=1 is the nearest plane.
# --------------------------------------------------------------------------
VY = 70
FLOOR = 80      # world Y of floor (down is +)
CEIL = -48
XW = 170        # half-width of the room
ZW = 1.8        # back wall depth


def pt(z, X, Y):
    return (int(round(160 + X / z)), int(round(VY + Y / z)))


def mk(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def bb(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(0, min(xs) - 1), max(0, min(ys) - 1), min(W, max(xs) + 2), min(H, max(ys) + 2))


def dpoly(img, pts, c1, c2, t0, t1=None, axis="y", m=4, out=None):
    """polygon filled with an ordered-dither mix of c1/c2."""
    t1 = t0 if t1 is None else t1
    dither_grad(img, bb(pts), c1, c2, axis, m, t0, t1, mk(pts))
    if out:
        poly(img, pts, None, out)


def q3(img, pts3, fill, out="ink"):
    poly(img, [pt(*p) for p in pts3], fill, out)


def dq3(img, pts3, c1, c2, t0, t1=None, axis="y", m=4, out=None):
    dpoly(img, [pt(*p) for p in pts3], c1, c2, t0, t1, axis, m, out)


def ov(img, box, c, t0, t1=None, axis="y", m=4, mask=None, only=True):
    """overlay colour c at dither density t0->t1 (leaves other pixels alone)."""
    t1 = t0 if t1 is None else t1
    x0, y0, x1, y1 = box
    cc = col(c)
    w, h = max(1, x1 - x0 - 1), max(1, y1 - y0 - 1)
    pix = img.load()
    mp = mask.load() if mask is not None else None
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            if mp is not None and mp[x, y] == 0:
                continue
            if only and pix[x, y][3] == 0:
                continue
            f = (x - x0) / w if axis == "x" else (y - y0) / h
            if t0 + (t1 - t0) * f > thr(x, y, m):
                pix[x, y] = cc


def ovoval(img, cx, cy, rx, ry, c, k=1.0, m=4, mask=None, only=True, pw=1.0):
    cc = col(c)
    pix = img.load()
    mp = mask.load() if mask is not None else None
    for y in range(max(0, int(cy - ry)), min(img.height, int(cy + ry) + 1)):
        for x in range(max(0, int(cx - rx)), min(img.width, int(cx + rx) + 1)):
            d = math.hypot((x - cx) / rx, (y - cy) / ry)
            if d >= 1:
                continue
            if mp is not None and mp[x, y] == 0:
                continue
            if only and pix[x, y][3] == 0:
                continue
            if ((1 - d) ** pw) * k > thr(x, y, m):
                pix[x, y] = cc


def hl(img, x0, x1, y, c):
    line(img, [(x0, y), (x1, y)], c)


def vl(img, x, y0, y1, c):
    line(img, [(x, y0), (x, y1)], c)


def rct(img, x, y, w, h, fill, out="ink"):
    rect(img, x, y, w, h, fill, out)


def box3(img, X0, X1, Yt, Yb, z0, z1, cf, cs, ct, faces="fst", out="ink"):
    """3D box: front face at z0, side face on the side that faces the room centre,
    top face if it lies below eye level."""
    if "t" in faces and Yt > 0:
        q3(img, [(z0, X0, Yt), (z1, X0, Yt), (z1, X1, Yt), (z0, X1, Yt)], ct, out)
    if "s" in faces:
        if X0 > 0:
            q3(img, [(z0, X0, Yt), (z1, X0, Yt), (z1, X0, Yb), (z0, X0, Yb)], cs, out)
        elif X1 < 0:
            q3(img, [(z0, X1, Yt), (z1, X1, Yt), (z1, X1, Yb), (z0, X1, Yb)], cs, out)
    if "f" in faces:
        q3(img, [(z0, X0, Yt), (z0, X1, Yt), (z0, X1, Yb), (z0, X0, Yb)], cf, out)


# --------------------------------------------------------------------------
# products
# --------------------------------------------------------------------------
PROD = ["red2", "orange2", "yellow", "green1", "blue2", "purple1", "red3", "green2",
        "blue3", "orange3", "white", "red2", "yellow", "blue2"]
LIGHT = {"red2": "red3", "orange2": "orange3", "yellow": "yellow2", "green1": "green2",
         "blue2": "blue3", "purple1": "purple2", "red3": "red4", "green2": "green3",
         "blue3": "blue4", "orange3": "orange4", "white": "white", "brown2": "brown3",
         "orange1": "orange2", "grey3": "grey4", "blue1": "blue2", "brown1": "brown2",
         "red1": "red2", "grey2": "grey3", "wall1": "white", "yellow2": "white"}
DARK = {"red2": "red1", "orange2": "orange1", "yellow": "orange2", "green1": "green0",
        "blue2": "blue1", "purple1": "purple0", "red3": "red2", "green2": "green1",
        "blue3": "blue2", "orange3": "orange2", "white": "grey3", "brown2": "brown1",
        "orange1": "orange0", "grey3": "grey2", "blue1": "blue0", "brown1": "brown0",
        "red1": "red0", "grey2": "grey1", "wall1": "grey3", "yellow2": "yellow", "brown3": "brown2",
        "grey4": "grey3", "wall2": "grey3", "wall3": "grey3", "wall4": "grey3"}


def gen_items(seed, z0, z1, boards, dzr, hr, gapp=0.06, bottles=0.25, pal=None, labs=None):
    rnd = random.Random(seed)
    out = []
    for k in range(len(boards) - 1):
        Ya, Yb = boards[k] + 3, boards[k + 1]
        gap = Yb - Ya
        z = z0 + rnd.uniform(0, 0.02)
        while z < z1 - 0.02:
            dz = rnd.uniform(*dzr)
            if rnd.random() < bottles:
                dz *= 0.55
                kind = "bottle"
            else:
                kind = "box"
            if z + dz > z1:
                dz = z1 - z
            if rnd.random() < gapp:
                z += dz
                continue
            h = rnd.randint(max(3, int(gap * hr[0])), max(4, int(gap * hr[1])))
            if kind == "bottle":
                h = min(gap - 1, h + 3)
            c = rnd.choice(pal or PROD)
            lab = rnd.choice(labs or ["white", "wall1", "yellow2", "white", "grey4"])
            out.append(dict(za=z, zb=z + dz - 0.008, Yt=Yb - h, Yb=Yb, c=c, lab=lab, kind=kind))
            z += dz
    return out


def draw_item(img, X, it):
    za, zb, Yt, Yb, c = it["za"], it["zb"], it["Yt"], it["Yb"], it["c"]
    q3(img, [(za, X, Yt), (zb, X, Yt), (zb, X, Yb), (za, X, Yb)], c, None)
    h = Yb - Yt
    if it["kind"] == "bottle":
        # cap + neck, label
        q3(img, [(za, X, Yt), (zb, X, Yt), (zb, X, Yt + 2), (za, X, Yt + 2)], LIGHT.get(c, c), None)
        q3(img, [(za, X, Yt + h * 0.45), (zb, X, Yt + h * 0.45), (zb, X, Yt + h * 0.75), (za, X, Yt + h * 0.75)],
           it["lab"], None)
    else:
        q3(img, [(za, X, Yt + h * 0.3), (zb, X, Yt + h * 0.3), (zb, X, Yt + h * 0.62), (za, X, Yt + h * 0.62)],
           it["lab"], None)
        q3(img, [(za, X, Yt), (zb, X, Yt), (zb, X, Yt + 1.5), (za, X, Yt + 1.5)], LIGHT.get(c, c), None)
    q3(img, [(za, X, Yb - 2), (zb, X, Yb - 2), (zb, X, Yb), (za, X, Yb)], DARK.get(c, "ink2"), None)
    line(img, [pt(za, X, Yt), pt(za, X, Yb)], "ink")
    line(img, [pt(za, X, Yt), pt(zb, X, Yt)], "ink")


def side_unit(img, side, Xf, z0, z1, boards, items, panel, board_c="grey2", kick=None, back_dither=None,
              zfrom=None, zto=None):
    """Shelving unit along a side wall, aisle face on plane X = side*Xf.
    Only the part with zfrom <= z < zto is drawn (so near parts can live in the fg layer)."""
    zf = z0 if zfrom is None else zfrom
    zt = z1 if zto is None else zto
    X = side * Xf
    Ytop, Ybot = boards[0], FLOOR
    q3(img, [(zf, X, Ytop), (zt, X, Ytop), (zt, X, Ybot), (zf, X, Ybot)], panel, None)
    if back_dither:
        dq3(img, [(zf, X, Ytop), (zt, X, Ytop), (zt, X, Ybot), (zf, X, Ybot)], panel, back_dither, 0.35, 0.55, "y", 2)
    for it in items:
        if zf <= it["za"] < zt:
            draw_item(img, X, it)
    for i, Yb in enumerate(boards):
        thick = 4 if i == 0 else 3
        q3(img, [(zf, X, Yb), (zt, X, Yb), (zt, X, Yb + thick), (zf, X, Yb + thick)], board_c, "ink")
        if i > 0:
            line(img, [pt(zf, X, Yb + 1), pt(zt, X, Yb + 1)], LIGHT.get(board_c, board_c))
    if kick:
        yk = boards[-1] + 3
        q3(img, [(zf, X, yk), (zt, X, yk), (zt, X, Ybot), (zf, X, Ybot)], kick, "ink")
        line(img, [pt(zf, X, yk + 1), pt(zt, X, yk + 1)], "grey2")
    # unit outline at top and bottom
    line(img, [pt(zf, X, Ybot), pt(zt, X, Ybot)], "ink")


# --------------------------------------------------------------------------
# 7-segment clock
# --------------------------------------------------------------------------
SEG = {"0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg",
       "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def digit(img, x, y, ch, c, off=None):
    segs = {
        "a": (x + 1, y, 3, 1), "g": (x + 1, y + 4, 3, 1), "d": (x + 1, y + 8, 3, 1),
        "f": (x, y + 1, 1, 3), "b": (x + 4, y + 1, 1, 3),
        "e": (x, y + 5, 1, 3), "c": (x + 4, y + 5, 1, 3)}
    on = SEG[ch]
    for k, (sx, sy, sw, sh) in segs.items():
        if k in on:
            rect(img, sx, sy, sw, sh, c)
        elif off:
            rect(img, sx, sy, sw, sh, off)


def clock(img, x, y, c, off, glow=None):
    """03:33 inside a box whose top-left is x,y (34 x 13)."""
    rect(img, x, y, 34, 13, "ink", "ink")
    rect(img, x, y, 34, 13, "ink2", "ink")
    rect(img, x + 1, y + 1, 32, 11, "ink", None)
    if glow:
        for yy in range(y + 1, y + 12):
            for xx in range(x + 1, x + 33):
                if (xx + yy) % 2 == 0 and img.getpixel((xx, yy))[:3] == PAL["ink"]:
                    img.putpixel((xx, yy), col(glow))
    for i, (dx, ch) in enumerate([(3, "0"), (10, "3"), (21, "3"), (28, "3")]):
        digit(img, x + dx - 1 + (0 if i < 2 else -1), y + 2, ch, c, off)
    rect(img, x + 16, y + 4, 2, 2, c)
    rect(img, x + 16, y + 8, 2, 2, c)


# --------------------------------------------------------------------------
# the wrong-state remap: lum -> red ramp with coarse m=2 dither
# --------------------------------------------------------------------------
RAMP_W = ["ink", "red0", "red1", "red2", "red3"]


def lumof(c):
    return (0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255.0


def remap_red(img, gain=0.92, gamma=1.55, floor_lum=0.16):
    out = img.copy()
    pix = out.load()
    ink = PAL["ink"]
    ramp = [PAL[n] for n in RAMP_W]
    n = len(ramp) - 1
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pix[x, y]
            if a == 0:
                continue
            if (r, g, b) == ink:
                continue
            l = lumof((r, g, b))
            if l < floor_lum:
                pix[x, y] = ink + (255,)
                continue
            v = (l ** gamma) * gain * n
            i = int(v)
            f = v - i
            if i >= n:
                i, f = n - 1, 1.0
            pix[x, y] = (ramp[i + 1] if f > thr(x, y, 2) else ramp[i]) + (255,)
    return out


# ==========================================================================
# 1-3. CONVENIENCE STORE
# ==========================================================================
SH_X = 126
SH_BOARDS = [-34, -10, 14, 38, 62]
SH_Z0, SH_Z1, SH_CUT = 1.0, 1.76, 1.26
SHELF_ITEMS = gen_items(11, SH_Z0, SH_Z1, SH_BOARDS, (0.05, 0.09), (0.6, 0.95))
CG_BOARDS = [-36, -24, -12, 0, 12, 24]
CG_ITEMS = gen_items(5, 1.0, 1.78, CG_BOARDS, (0.022, 0.04), (0.55, 0.9), gapp=0.03, bottles=0.0)
CTR_X0, CTR_X1, CTR_YT = 110, 150, 30
CTR_Z0, CTR_Z1, CTR_CUT = 1.12, 1.78, 1.4


def ceiling_lights(img, dead):
    for (xa, xb, za, zb) in [(-104, -44, 1.1, 1.4), (44, 104, 1.1, 1.4), (-104, -44, 1.5, 1.74), (44, 104, 1.5, 1.74)]:
        pts = [(za, xa, CEIL), (za, xb, CEIL), (zb, xb, CEIL), (zb, xa, CEIL)]
        q3(img, pts, "grey1" if dead else "white", "ink")
        if not dead:
            # tubes
            for xx in (xa + (xb - xa) * 0.3, xa + (xb - xa) * 0.7):
                line(img, [pt(za, xx, CEIL), pt(zb, xx, CEIL)], "blue4")
            line(img, [pt(za, xa, CEIL), pt(za, xb, CEIL)], "grey4")
        else:
            for xx in (xa + (xb - xa) * 0.3, xa + (xb - xa) * 0.7):
                line(img, [pt(za, xx, CEIL), pt(zb, xx, CEIL)], "ink2")


def draw_fan(img):
    cx, cy = pt(1.3, 0, CEIL)
    cy += 1
    # down-rod + motor
    rect(img, cx - 1, cy - 4, 3, 4, "grey2", "ink")
    for (dx, dy, w, h) in [(-23, -1, 21, 5), (3, -1, 21, 5)]:
        rct(img, cx + dx, cy + dy, w, h, "grey4", "ink")
        hl(img, cx + dx + 1, cx + dx + w - 2, cy + dy + 1, "white")
    rct(img, cx - 3, cy + 3, 7, 6, "grey3", "ink")
    rct(img, cx - 3, cy - 8, 7, 5, "grey2", "ink")
    rct(img, cx - 3, cy, 7, 5, "grey2", "ink")
    rect(img, cx - 2, cy + 1, 5, 1, "grey4")
    # shadow dither under the fan blades onto ceiling: none, ceiling is flat


def store_clock_housing(img):
    # hanging header beam with the clock
    rct(img, 117, 43, 86, 14, "grey2", "ink")
    hl(img, 118, 201, 44, "grey3")
    for xx in range(120, 138, 2):
        vl(img, xx, 47, 54, "ink")
    for xx in range(184, 200, 2):
        vl(img, xx, 47, 54, "ink")
    hl(img, 118, 201, 56, "grey1")


def store_back_wall(img):
    ax, ay = pt(ZW, -XW, CEIL)
    bx, by = pt(ZW, XW, FLOOR)
    pts = [(ax, ay), (bx, ay), (bx, by), (ax, by)]
    rpoly = pts
    dpoly(img, pts, "wall1", "wall2", 0.0, 0.55, "y", 4)
    # wainscot: lower band
    ytop = pt(ZW, 0, 40)[1]
    rect(img, ax, ytop, bx - ax, by - ytop, "blue3")
    dpoly(img, [(ax, ytop), (bx, ytop), (bx, by), (ax, by)], "blue3", "wall3", 0.1, 0.75, "y", 4)
    hl(img, ax, bx - 1, ytop, "ink")
    hl(img, ax, bx - 1, ytop + 1, "blue4")
    # wall tiles lines in the wainscot
    for xx in range(ax, bx, 12):
        vl(img, xx, ytop + 2, by - 1, "grey3")
    # stains / water marks on the wall for dinginess
    ov(img, (ax, ay, bx, ytop), "grey3", 0.0, 0.18, "y", 4)
    ov(img, (ax, ay, ax + 14, by), "grey3", 0.5, 0.0, "x", 2)
    ov(img, (bx - 14, ay, bx, by), "grey3", 0.0, 0.5, "x", 2)


def store_doors(img, dead):
    xa, ya = pt(ZW, -55, -20)
    xb, yb = pt(ZW, 55, FLOOR)
    # recess / frame
    rct(img, xa - 2, ya - 2, xb - xa + 5, yb - ya + 2, "grey2", "ink")
    hl(img, xa - 1, xb + 1, ya - 1, "grey3")
    gx0, gy0, gx1, gy1 = xa + 1, ya + 1, xb - 1, yb - 3
    rect(img, gx0, gy0, gx1 - gx0 + 1, gy1 - gy0 + 1, "ink")
    # ---- night street seen through the glass
    sky = (gx0, gy0, gx1 + 1, gy0 + 34)
    dither_grad(img, sky, "ink", "blue0", "y", 4, 0.1, 0.95)
    # far buildings
    rect(img, gx0, gy0 + 22, 14, 14, "blue0", "ink")
    rect(img, gx0 + 12, gy0 + 14, 10, 22, "ink2", "ink")
    rect(img, gx0 + 40, gy0 + 18, 17, 20, "blue0", "ink")
    rect(img, gx0 + 52, gy0 + 26, 10, 10, "ink2", "ink")
    for (wx, wy) in [(gx0 + 15, gy0 + 17), (gx0 + 18, gy0 + 23), (gx0 + 44, gy0 + 22), (gx0 + 49, gy0 + 28),
                     (gx0 + 3, gy0 + 27), (gx0 + 15, gy0 + 29)]:
        rect(img, wx, wy, 2, 2, "orange3")
    # neon sign (vertical) + lamp post
    rect(img, gx0 + 28, gy0 + 12, 5, 20, "ink2", "ink")
    rect(img, gx0 + 29, gy0 + 14, 3, 3, "red3")
    rect(img, gx0 + 29, gy0 + 19, 3, 3, "yellow")
    rect(img, gx0 + 29, gy0 + 24, 3, 3, "red3")
    vl(img, gx1 - 6, gy0 + 10, gy0 + 40, "grey1")
    vl(img, gx1 - 7, gy0 + 10, gy0 + 40, "ink2")
    rect(img, gx1 - 10, gy0 + 8, 6, 3, "yellow2", "ink")
    ovoval(img, gx1 - 7, gy0 + 12, 14, 12, "orange3", 0.55, 4, only=False)
    rect(img, gx1 - 10, gy0 + 8, 6, 3, "yellow2", "ink")
    # road / sidewalk
    rr = (gx0, gy0 + 36, gx1 + 1, gy1 + 1)
    dither_grad(img, rr, "ink2", "grey1", "y", 4, 0.0, 1.0)
    hl(img, gx0, gx1, gy0 + 36, "ink")
    for xx in range(gx0 + 4, gx1 - 3, 14):
        rect(img, xx, gy1 - 3, 8, 2, "grey3")
    ovoval(img, gx1 - 7, gy0 + 44, 18, 8, "orange2", 0.4, 4)
    # glass reflections (diagonal pale streaks)
    for k, (sx, w) in enumerate([(gx0 + 8, 5), (gx0 + 30, 3), (gx0 + 36, 7)]):
        for yy in range(gy0 + 2, gy1 - 1):
            x0 = sx + (gy1 - yy) // 2
            for xx in range(x0, x0 + w):
                if gx0 < xx < gx1 and (xx + yy) % 2 == 0:
                    img.putpixel((xx, yy), col("blue1"))
    # mullion + pull handles
    mid = (gx0 + gx1) // 2
    rect(img, mid - 1, ya - 1, 3, gy1 - ya + 2, "grey2", "ink")
    vl(img, mid, ya, gy1, "grey3")
    rect(img, mid - 5, gy0 + 22, 2, 14, "grey4", "ink")
    rect(img, mid + 4, gy0 + 22, 2, 14, "grey4", "ink")
    # frosted sign band across doors
    rect(img, gx0, gy0 + 14, gx1 - gx0 + 1, 9, "grey4", "ink")
    dither_flat(img, (gx0 + 1, gy0 + 15, gx1, gy0 + 22), "grey4", "white", 0.5, 2)
    text(img, gx0 + 3, gy0 + 14, "24H", "red2", 7)
    text(img, mid + 6, gy0 + 14, "OPEN", "blue1", 7)
    # kick plates
    rect(img, gx0, gy1 + 1, gx1 - gx0 + 1, 3, "grey2", "ink")
    # door mat on the floor
    q3(img, [(1.46, -56, FLOOR), (1.78, -56, FLOOR), (1.78, 56, FLOOR), (1.46, 56, FLOOR)], "ink2", "ink")
    dq3(img, [(1.46, -56, FLOOR), (1.78, -56, FLOOR), (1.78, 56, FLOOR), (1.46, 56, FLOOR)], "ink2", "grey1", 0.3, 0.6, "y", 2)
    return (gx0, gy0, gx1, gy1)


def store_back_stuff(img):
    # drinks cooler on the left of the doors
    xa, ya = pt(1.75, -126, -12)
    xb, yb = pt(1.75, -66, FLOOR)
    rct(img, xa, ya, xb - xa + 1, yb - ya + 1, "grey3", "ink")
    rect(img, xa, ya, xb - xa + 1, 11, "blue1", "ink")
    text(img, xa + 3, ya + 1, "음료", "yellow", 9)
    gx0, gy0, gx1, gy1 = xa + 2, ya + 12, xb - 2, yb - 4
    rect(img, gx0, gy0, gx1 - gx0 + 1, gy1 - gy0 + 1, "blue4", "ink")
    dither_grad(img, (gx0 + 1, gy0 + 1, gx1, gy1), "blue4", "blue3", "y", 4, 0.0, 0.8)
    rows = 4
    rnd = random.Random(3)
    for r in range(rows):
        yy = gy0 + 3 + r * ((gy1 - gy0 - 3) // rows)
        for xx in range(gx0 + 2, gx1 - 3, 4):
            c = rnd.choice(["red2", "green1", "blue2", "orange2", "yellow", "purple1", "white", "red3"])
            hh = rnd.choice([8, 9, 10])
            rect(img, xx, yy + 10 - hh, 3, hh, c, "ink")
            px(img, xx + 1, yy + 11 - hh, LIGHT.get(c, c))
        hl(img, gx0 + 1, gx1 - 1, yy + 11, "grey2")
    vl(img, (gx0 + gx1) // 2, gy0, gy1, "grey2")
    rect(img, xa + 2, yb - 3, xb - xa - 3, 3, "grey1", "ink")
    # sign board with the store name, right of the doors
    xa, ya = pt(1.75, 68, -40)
    xb, yb = pt(1.75, 150, -22)
    rct(img, xa, ya, xb - xa + 1, yb - ya + 1, "blue1", "ink")
    hl(img, xa + 1, xb - 1, ya + 1, "blue2")
    text(img, xa + 3, ya, "달빛마트", "yellow", 9, edge="ink")
    # posters
    for (X0, X1, c1, c2, s, tc) in [(70, 104, "red2", "yellow", "신상", "white"), (112, 146, "green1", "wall1", "컵라면", "ink")]:
        xa, ya = pt(1.75, X0, -14)
        xb, yb = pt(1.75, X1, 30)
        rct(img, xa, ya, xb - xa + 1, yb - ya + 1, c2, "ink")
        rect(img, xa + 1, ya + 1, xb - xa - 1, 9, c1)
        text(img, xa + 3, ya + 1, s, tc, 9)
        rect(img, xa + 3, ya + 13, xb - xa - 5, 8, LIGHT.get(c1, c1), "ink")
        rect(img, xa + 3, ya + 24, xb - xa - 5, 3, DARK.get(c2, c2))
    # ice-cream chest freezer
    xa, ya = pt(1.75, 68, 44)
    xb, yb = pt(1.75, 150, FLOOR)
    rct(img, xa, ya, xb - xa + 1, yb - ya + 1, "white", "ink")
    rect(img, xa + 1, ya + 1, xb - xa - 1, 3, "blue3")
    rect(img, xa + 1, yb - 4, xb - xa - 1, 4, "grey3")
    vl(img, (xa + xb) // 2, ya + 4, yb - 4, "grey3")
    text(img, xa + 3, ya + 3, "아이스", "red2", 9)
    dither_grad(img, (xa + 1, ya + 4, xb, yb - 4), "white", "grey4", "x", 4, 0.0, 0.8)
    # gum / small shelf items skipped; clutter: leaning mop sign (wet floor) left of chest
    return


def store_floor(img, dead):
    ZR = [0.9 + 0.15 * k for k in range(7)]
    XR = list(range(-168, 169, 42))
    pts = [pt(0.9, -XW, FLOOR), pt(0.9, XW, FLOOR), pt(ZW, XW, FLOOR), pt(ZW, -XW, FLOOR)]
    poly(img, pts, "grey4")
    for j in range(len(ZR) - 1):
        for i in range(len(XR) - 1):
            if (i + j) % 2 == 0:
                q3(img, [(ZR[j], XR[i], FLOOR), (ZR[j + 1], XR[i], FLOOR), (ZR[j + 1], XR[i + 1], FLOOR),
                         (ZR[j], XR[i + 1], FLOOR)], "white", None)
    for z in ZR:
        line(img, [pt(z, -XW, FLOOR), pt(z, XW, FLOOR)], "grey3")
    for X in XR:
        line(img, [pt(0.9, X, FLOOR), pt(ZW, X, FLOOR)], "grey3")
    fm = mk(pts)
    # grime toward the edges and near the camera
    ov(img, (0, 114, W, 158), "grey3", 0.0, 0.35, "y", 4, fm)
    ov(img, (0, 114, 70, 158), "grey3", 0.6, 0.0, "x", 2, fm)
    ov(img, (250, 114, W, 158), "grey3", 0.0, 0.6, "x", 2, fm)
    if not dead:
        # fluorescent reflections on the glossy floor
        for (X, z) in [(-74, 1.28), (74, 1.28), (-74, 1.62), (74, 1.62)]:
            x, y = pt(z, X, FLOOR)
            ovoval(img, x, y + 1, 30 / z * 0.8, 6.5, "white", 0.95, 4, fm)
        ovoval(img, 160, 132, 36, 8, "white", 0.7, 4, fm)
    # scuff marks
    for (x, y, w) in [(120, 142, 6), (196, 138, 5), (150, 150, 7), (226, 148, 4)]:
        hl(img, x, x + w, y, "grey3")


def store_side_walls(img):
    # left wall
    L = [pt(1.0, -XW, CEIL), pt(ZW, -XW, CEIL), pt(ZW, -XW, FLOOR), pt(1.0, -XW, FLOOR)]
    dpoly(img, L, "wall2", "wall3", 0.15, 0.75, "x", 4)
    # right wall
    R = [pt(1.0, XW, CEIL), pt(ZW, XW, CEIL), pt(ZW, XW, FLOOR), pt(1.0, XW, FLOOR)]
    dpoly(img, R, "wall4", "wall1", 0.0, 0.9, "x", 4)
    ov(img, bb(R), "grey3", 0.4, 0.0, "x", 2, mk(R))
    # floor/wall seam
    line(img, [pt(1.0, -XW, FLOOR), pt(ZW, -XW, FLOOR)], "ink")
    line(img, [pt(1.0, XW, FLOOR), pt(ZW, XW, FLOOR)], "ink")
    line(img, [pt(ZW, -XW, CEIL), pt(ZW, -XW, FLOOR)], "ink")
    line(img, [pt(ZW, XW, CEIL), pt(ZW, XW, FLOOR)], "ink")


def store_ceiling(img, dead):
    pts = [pt(1.0, -XW, CEIL), pt(1.0, XW, CEIL), pt(ZW, XW, CEIL), pt(ZW, -XW, CEIL)]
    pts = [(-12, 22), (332, 22), pts[2], pts[3]]
    poly(img, pts, "grey4")
    cm = mk(pts)
    ov(img, bb(pts), "grey3", 0.0, 0.7, "y", 4, cm)
    # tile grid
    for X in range(-170, 171, 34):
        line(img, [pt(1.0, X, CEIL), pt(ZW, X, CEIL)], "grey3")
    for z in [1.0 + 0.1 * k for k in range(9)]:
        line(img, [pt(z, -XW, CEIL), pt(z, XW, CEIL)], "grey3")
    line(img, [pt(ZW, -XW, CEIL), pt(ZW, XW, CEIL)], "ink")
    line(img, [pt(1.0, -XW, CEIL), pt(ZW, -XW, CEIL)], "ink")
    line(img, [pt(1.0, XW, CEIL), pt(ZW, XW, CEIL)], "ink")
    ceiling_lights(img, dead)
    if not dead:
        for (X, z) in [(-74, 1.25), (74, 1.25), (-74, 1.62), (74, 1.62)]:
            x, y = pt(z, X, CEIL)
            ovoval(img, x, y + 2, 34 / z * 0.8, 9, "white", 0.6, 4, cm)


def left_shelf(img, zfrom, zto):
    side_unit(img, -1, SH_X, SH_Z0, SH_Z1, SH_BOARDS, SHELF_ITEMS, "grey3", "grey2", "grey1", "grey2", zfrom, zto)


def shelf_endcap(img):
    xa, ya = pt(1.0, -XW, -37)
    xb, yb = pt(1.0, -SH_X, FLOOR)
    # side panel that we see on the far side of the end (thickness) - the end face
    rct(img, xa, ya, xb - xa + 1, yb - ya + 1, "grey4", "ink")
    dither_grad(img, (xa + 1, ya + 1, xb, yb), "grey4", "grey3", "x", 4, 0.0, 0.6)
    # header sign
    rect(img, xa + 1, ya + 1, xb - xa - 1, 12, "red2", "ink")
    hl(img, xa + 2, xb - 1, ya + 2, "red3")
    text(img, xb - 27, ya + 1, "신상", "yellow", 9, edge="ink")
    # display rows facing us
    rnd = random.Random(21)
    rows = [ya + 15, ya + 40, ya + 65, ya + 90]
    for r, yy in enumerate(rows):
        for xx in range(max(xa + 2, 2), xb - 3, 7):
            c = rnd.choice(PROD)
            hh = rnd.choice([12, 14, 16]) if r < 3 else 8
            rect(img, xx, yy + 20 - hh, 6, hh, c, "ink")
            rect(img, xx + 1, yy + 22 - hh, 4, 3, "white")
            px(img, xx + 1, yy + 21 - hh, LIGHT.get(c, c))
        rct(img, xa + 1, yy + 20, xb - xa - 1, 4, "grey2", "ink")
        hl(img, xa + 2, xb - 2, yy + 21, "grey3")
    # price rail + kick
    rect(img, xa + 1, yb - 10, xb - xa - 1, 10, "grey1", "ink")
    hl(img, xa + 2, xb - 2, yb - 9, "grey2")
    # cardboard bin on top
    return


def cig_wall(img):
    X = XW
    Y0, Y1 = CG_BOARDS[0], CG_BOARDS[-1] + 3
    q3(img, [(1.0, X, Y0), (ZW, X, Y0), (ZW, X, FLOOR), (1.0, X, FLOOR)], "grey1", None)
    # shutter box above
    q3(img, [(1.0, X, CEIL), (ZW, X, CEIL), (ZW, X, Y0), (1.0, X, Y0)], "grey3", None)
    dq3(img, [(1.0, X, CEIL), (ZW, X, CEIL), (ZW, X, Y0), (1.0, X, Y0)], "grey3", "grey2", 0.0, 0.6, "y", 4)
    for it in CG_ITEMS:
        draw_item(img, X, it)
    for i, Yb in enumerate(CG_BOARDS):
        q3(img, [(1.0, X, Yb), (ZW, X, Yb), (ZW, X, Yb + 2), (1.0, X, Yb + 2)], "grey2", "ink")
    # lit header sign
    q3(img, [(1.1, X, -46), (1.7, X, -46), (1.7, X, -37), (1.1, X, -37)], "ink2", "ink")
    x, y = pt(1.45, X, -45)
    text(img, x - 14, y - 1, "담배", "red3", 9)
    # lower: dark cabinet doors behind the counter
    q3(img, [(1.0, X, 27), (ZW, X, 27), (ZW, X, FLOOR), (1.0, X, FLOOR)], "grey2", "ink")
    for z in [1.15 + 0.15 * k for k in range(5)]:
        line(img, [pt(z, X, 29), pt(z, X, FLOOR - 1)], "grey1")


def counter_body(img, near):
    """near=True: near corner (z<CUT) drawn into fg layer; False: far part (z>=CUT)."""
    if near:
        z0, z1 = CTR_Z0, CTR_CUT
    else:
        z0, z1 = CTR_CUT, CTR_Z1
    Yt, Yb = CTR_YT, FLOOR
    X0, X1 = CTR_X0, CTR_X1
    # aisle side face
    q3(img, [(z0, X0, Yt), (z1, X0, Yt), (z1, X0, Yb), (z0, X0, Yb)], "blue3", "ink")
    dq3(img, [(z0, X0, Yt + 4), (z1, X0, Yt + 4), (z1, X0, Yb - 6), (z0, X0, Yb - 6)], "blue3", "blue2", 0.2, 0.8, "x", 4)
    # kick plate
    q3(img, [(z0, X0, Yb - 7), (z1, X0, Yb - 7), (z1, X0, Yb), (z0, X0, Yb)], "grey1", "ink")
    # panel seams
    for z in [1.25, 1.55, 1.7]:
        if z0 < z < z1:
            line(img, [pt(z, X0, Yt + 5), pt(z, X0, Yb - 8)], "blue1")
    # top surface
    q3(img, [(z0, X0, Yt), (z1, X0, Yt), (z1, X1, Yt), (z0, X1, Yt)], "grey4", "ink")
    dq3(img, [(z0, X0, Yt), (z1, X0, Yt), (z1, X1, Yt), (z0, X1, Yt)], "grey4", "white", 0.2, 0.8, "x", 4)
    line(img, [pt(z0, X0, Yt), pt(z1, X0, Yt)], "white")
    if near:
        # front face (end panel) facing the camera
        q3(img, [(z0, X0, Yt), (z0, X1, Yt), (z0, X1, Yb), (z0, X0, Yb)], "blue2", "ink")
        xa, ya = pt(z0, X0, Yt)
        xb, yb = pt(z0, X1, Yb)
        dither_grad(img, (xa + 1, ya + 3, xb, yb - 7), "blue2", "blue1", "y", 4, 0.0, 0.6)
        hl(img, xa + 1, xb - 1, ya + 1, "blue3")
        rect(img, xa + 1, yb - 7, xb - xa - 1, 7, "grey1", "ink")
        # end-panel poster
        rect(img, xa + 6, ya + 8, 18, 18, "wall1", "ink")
        rect(img, xa + 8, ya + 10, 14, 6, "red2")
        text(img, xa + 8, ya + 9, "마트", "white", 9)
        rect(img, xa + 8, ya + 19, 14, 2, "grey3")
        rect(img, xa + 8, ya + 23, 8, 2, "grey3")


def register(img):
    # register + screen + card reader on the counter top, far part
    # register body
    box3(img, 118, 140, 8, 30, 1.5, 1.72, "grey3", "grey2", "grey4")
    xa, ya = pt(1.5, 118, 8)
    xb, yb = pt(1.5, 140, 30)
    rect(img, xa + 2, ya + 2, xb - xa - 4, 4, "blue3", "ink")
    rect(img, xa + 3, yb - 4, xb - xa - 6, 2, "grey2")
    # customer display on a stalk
    xs, ys = pt(1.6, 123, -2)
    rect(img, xs, ys, 8, 6, "ink2", "ink")
    rect(img, xs + 1, ys + 1, 6, 3, "green2")
    vl(img, xs + 4, ys + 6, ys + 9, "grey2")
    # card reader
    box3(img, 142, 150, 20, 30, 1.38, 1.5, "ink2", "grey1", "grey2")
    # lucky cat-ish jar & receipt roll
    xa, ya = pt(1.62, 112, 30)
    rect(img, xa, ya - 9, 7, 9, "white", "ink")
    rect(img, xa + 1, ya - 7, 5, 3, "red2")
    rect(img, xa + 1, ya - 10, 5, 2, "red2", "ink")


def snack_bag(img):
    # chip bag leaning on the near corner of the counter
    x, y = pt(1.18, 136, CTR_YT)
    x = x - 1
    pts = [(x - 7, y - 1), (x + 7, y - 1), (x + 8, y - 4), (x + 7, y - 20), (x - 7, y - 20), (x - 8, y - 4)]
    poly(img, pts, "orange2", "ink")
    rect(img, x - 6, y - 19, 13, 2, "orange3")
    for xx in range(x - 6, x + 7, 2):  # crimped seals
        px(img, xx, y - 20, "ink")
        px(img, xx, y - 1, "ink")
    rect(img, x - 6, y - 14, 13, 7, "yellow", "ink")
    ellipse(img, x - 4, y - 13, x + 3, y - 8, "red2", "ink")
    text(img, x - 4, y - 14, "새", "yellow2", 9)
    vl(img, x - 6, y - 17, y - 3, "orange3")
    hl(img, x - 6, x + 6, y - 3, "orange1")
    hl(img, x - 6, x + 6, y - 2, "orange1")
    # a second bag leaning
    poly(img, [(x + 9, y - 1), (x + 18, y - 1), (x + 18, y - 14), (x + 9, y - 14)], "green1", "ink")
    rect(img, x + 10, y - 11, 7, 5, "white", "ink")
    vl(img, x + 10, y - 13, y - 2, "green2")


def hanging_signs(img):
    for (X0, X1, z, s, bg) in [(-168, -92, 1.3, "라면·과자", "blue1"), (64, 112, 1.3, "계산대", "red1")]:
        xa, ya = pt(z, X0, -47)
        xb, yb = pt(z, X1, -31)
        yc = pt(z, 0, CEIL)[1]
        vl(img, xa + 3, yc, ya, "ink")
        vl(img, xb - 3, yc, ya, "ink")
        rct(img, xa, ya, xb - xa + 1, yb - ya + 1, bg, "ink")
        hl(img, xa + 1, xb - 1, ya + 1, LIGHT.get(bg, bg))
        text(img, (xa + xb) // 2, ya + 1, s, "white", 9, align="center")


def store_extras_day(img):
    # little saturated bits in the store: wet floor sign near the shelf end
    pass


def draw_far(img, dead):
    store_ceiling(img, dead)
    store_floor(img, dead)
    store_side_walls(img)
    store_back_wall(img)
    store_back_stuff(img)
    store_doors(img, dead)
    store_clock_housing(img)
    cig_wall(img)
    left_shelf(img, SH_CUT, SH_Z1 + 0.01)
    counter_body(img, False)
    register(img)
    hanging_signs(img)
    draw_fan(img)


def draw_near(img):
    left_shelf(img, SH_Z0, SH_CUT)
    shelf_endcap(img)
    counter_body(img, True)
    snack_bag(img)


# ---------------------------------------------------------------- wrong state
def wrong_extras(img):
    fm = mk([pt(0.9, -XW, FLOOR), pt(0.9, XW, FLOOR), pt(ZW, XW, FLOOR), pt(ZW, -XW, FLOOR)])
    # red glow pouring out of the doors onto the floor
    ovoval(img, 160, 122, 60, 22, "red3", 1.2, 2, fm, pw=0.8)
    ovoval(img, 160, 128, 34, 12, "orange2", 1.0, 2, fm, pw=0.9)
    # long ink shadows: bars cast by shelf posts / counter panels
    for k in range(7):
        z = 1.02 + 0.115 * k
        pts = [pt(z, -126, FLOOR), pt(z + 0.05, -126, FLOOR), pt(z - 0.28, 30, FLOOR), pt(z - 0.38, 30, FLOOR)]
        ov(img, bb(pts), "ink", 1.0, 1.0, "y", 2, mk(pts), only=False)
        dpoly(img, [pt(z + 0.05, -126, FLOOR), pt(z + 0.12, -126, FLOOR), pt(z - 0.2, 30, FLOOR), pt(z - 0.28, 30, FLOOR)], "red1", "ink", 0.4, 0.4, "y", 2)
    for k in range(5):
        z = 1.2 + 0.13 * k
        pts = [pt(z, 110, FLOOR), pt(z + 0.05, 110, FLOOR), pt(z - 0.3, -40, FLOOR), pt(z - 0.4, -40, FLOOR)]
        ov(img, bb(pts), "ink", 1.0, 1.0, "y", 2, mk(pts), only=False)
    for X in (-18, 0, 18):
        pts = [pt(ZW, X, FLOOR), pt(ZW, X + 3, FLOOR), pt(0.92, X * 3 + 3, FLOOR), pt(0.92, X * 3, FLOOR)]
        ov(img, bb(pts), "ink", 1.0, 1.0, "y", 2, mk(pts), only=False)


def wrong_door(img):
    xa, ya = pt(ZW, -55, -20)
    xb, yb = pt(ZW, 55, FLOOR)
    gx0, gy0, gx1, gy1 = xa + 1, ya + 1, xb - 1, yb - 3
    gm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(gm).rectangle([gx0, gy0, gx1, gy1], fill=255)
    cx = (gx0 + gx1) // 2
    ovoval(img, cx, gy0 + 30, 36, 34, "red2", 1.4, 2, gm, only=False, pw=0.7)
    ovoval(img, cx, gy0 + 34, 22, 24, "red3", 1.2, 2, gm, only=False, pw=0.9)
    ovoval(img, cx, gy0 + 36, 10, 14, "orange3", 1.0, 2, gm, only=False, pw=1.0)
    # mullion & handles stay ink
    rect(img, cx - 1, gy0 - 1, 3, gy1 - gy0 + 3, "ink", None)
    vl(img, cx, gy0, gy1, "red0")
    rect(img, cx - 5, gy0 + 22, 2, 14, "ink")
    rect(img, cx + 4, gy0 + 22, 2, 14, "ink")
    # frosted band silhouette
    rect(img, gx0, gy0 + 14, gx1 - gx0 + 1, 9, "ink")
    text(img, gx0 + 3, gy0 + 14, "24H", "red3", 7)
    text(img, cx + 6, gy0 + 14, "OPEN", "red3", 7)


def build_store(wrong):
    base = new(fill="ink")
    draw_far(base, dead=wrong)
    fg = new()
    draw_near(fg)
    if wrong:
        base = remap_red(base)
        fg = remap_red(fg)
        wrong_door(base)
        wrong_extras(base)
    cx, cy = 117, 43
    if wrong:
        clock(base, cx + 42, cy + 1, "red4", "red0", glow="red1")
    else:
        clock(base, cx + 42, cy + 1, "red3", "red0")
    scene = base.copy()
    paste(scene, fg)
    letterbox(scene)
    return scene, fg


def build_all_store():
    d, fg = build_store(False)
    w, fgw = build_store(True)
    save(d, "bg/store_day.png")
    save(w, "bg/store_wrong.png")
    save(fg, "bg/store_fg.png")
    save(fgw, "bg/store_fg_wrong.png")
    return [d, w, fg, fgw]



# ==========================================================================
# 4. TEMP AGENCY OFFICE  (flat, front-on, warm)
# ==========================================================================
WALL_BASE = 122          # where the back wall meets the floor
LAMP = (112, 100)        # lamp bulb position on the desk


def office_wall(img):
    rect(img, 0, 0, W, H, "ink")
    # wall: dingy orange, dithered darker at the top and corners
    rect(img, 0, 22, W, WALL_BASE - 22, "orange1")
    dither_grad(img, (0, 22, W, WALL_BASE), "orange0", "orange1", "y", 4, 0.9, 0.0)
    ov(img, (0, 22, W, WALL_BASE), "orange2", 0.0, 0.25, "y", 4)
    ov(img, (0, 22, 40, WALL_BASE), "orange0", 0.55, 0.0, "x", 2)
    ov(img, (280, 22, W, WALL_BASE), "orange0", 0.0, 0.6, "x", 2)
    # wainscot
    wy = 96
    rect(img, 0, wy, W, WALL_BASE - wy, "brown1")
    dither_grad(img, (0, wy, W, WALL_BASE), "brown1", "brown0", "y", 4, 0.0, 0.7)
    for x in range(0, W, 16):
        vl(img, x, wy + 2, WALL_BASE - 1, "brown0")
    hl(img, 0, W - 1, wy, "ink")
    hl(img, 0, W - 1, wy + 1, "brown3")
    hl(img, 0, W - 1, WALL_BASE - 1, "ink")
    # baseboard
    rect(img, 0, WALL_BASE - 4, W, 4, "brown0")
    hl(img, 0, W - 1, WALL_BASE - 5, "ink")
    # water stain on ceiling corner + peeling patches
    for (cx, cy, rx, ry) in [(262, 30, 28, 10), (24, 36, 18, 8), (180, 28, 24, 6)]:
        ovoval(img, cx, cy, rx, ry, "orange0", 0.9, 4)
    for (x, y, w, h) in [(58, 80, 7, 5), (206, 84, 6, 4), (150, 88, 5, 3), (96, 74, 4, 6)]:
        rect(img, x, y, w, h, "orange2")
        hl(img, x, x + w - 1, y + h, "orange0")
    # ceiling strip
    rect(img, 0, 22, W, 6, "brown0")
    hl(img, 0, W - 1, 28, "ink")
    # floor: scuffed linoleum with perspective-lite planks
    rect(img, 0, WALL_BASE, W, H - WALL_BASE, "brown2")
    dither_grad(img, (0, WALL_BASE, W, 158), "brown1", "brown2", "y", 4, 0.9, 0.1)
    hl(img, 0, W - 1, WALL_BASE, "ink")
    for k, y in enumerate([128, 135, 143, 152]):
        hl(img, 0, W - 1, y, "brown0")
    # plank joints, staggered, widening toward the viewer
    for k, y0 in enumerate([WALL_BASE, 128, 135, 143, 152]):
        y1 = [128, 135, 143, 152, 158][k]
        step = 24 + 6 * k
        for x in range(((k * 11) % step) - step, W, step):
            xx = 160 + (x - 160) * (1 + k * 0.08)
            vl(img, int(xx), y0 + 1, y1 - 1, "brown0")


def window_blinds(img):
    x0, y0, w, h = 226, 34, 66, 52
    rct(img, x0 - 3, y0 - 3, w + 6, h + 6, "brown3", "ink")
    rct(img, x0 - 1, y0 - 1, w + 2, h + 2, "brown1", "ink")
    # evening sky / street lamp through the glass
    dither_grad(img, (x0, y0, x0 + w, y0 + h), "orange3", "orange2", "y", 4, 0.0, 1.0)
    ov(img, (x0, y0 + 28, x0 + w, y0 + h), "orange1", 0.0, 0.7, "y", 4)
    rect(img, x0 + 8, y0 + 34, 10, 18, "brown0", "ink")
    rect(img, x0 + 24, y0 + 28, 14, 24, "brown1", "ink")
    rect(img, x0 + 44, y0 + 36, 12, 16, "brown0", "ink")
    for (a, b) in [(28, 32), (32, 36), (30, 42), (48, 40)]:
        rect(img, x0 + a, y0 + b, 2, 2, "yellow2")
    # window cross bar
    rect(img, x0 + w // 2 - 1, y0, 3, h, "brown1")
    vl(img, x0 + w // 2 - 1, y0, y0 + h - 1, "ink")
    vl(img, x0 + w // 2 + 1, y0, y0 + h - 1, "ink")
    # venetian blinds: slats, uneven, a couple bent
    for i, yy in enumerate(range(y0, y0 + 38, 6)):
        sag = 1 if i in (3, 5) else 0
        rect(img, x0, yy, w, 3, "grey4", None)
        hl(img, x0, x0 + w - 1, yy, "white")
        hl(img, x0, x0 + w - 1, yy + 2, "grey2")
        hl(img, x0, x0 + w - 1, yy + 3, "ink")
        if sag:
            rect(img, x0 + 40, yy + 1, 18, 6, "grey3", "ink")
    rect(img, x0, y0 + 38, w, 3, "brown2", "ink")  # headrail wand
    vl(img, x0 + 6, y0 + 38, y0 + 52, "ink")
    rect(img, x0 + 5, y0 + 52, 3, 3, "yellow2", "ink")
    # sill
    rct(img, x0 - 5, y0 + h + 3, w + 10, 4, "brown3", "ink")


def blind_light(img):
    """striped light cast from the window onto wall, floor and desk area (before desk)."""
    # stripes fall down-left on the wall under the window and across the floor
    for i in range(7):
        x0 = 150 + i * 5
        pts = [(x0 + 80, 92 + i * 0), (x0 + 88, 92), (x0 + 10, 158), (x0 + 2, 158)]
    # wall stripes: horizontal bands below the window sill, brightest near the window
    wm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(wm).polygon([(226, 91), (292, 91), (292, WALL_BASE - 5), (226, WALL_BASE - 5)], fill=255)
    for i in range(6):
        y = 93 + i * 5
        rect_mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(rect_mask).rectangle([210 - i * 2, y, 300, y + 2], fill=255)
        ov(img, (200, y, 310, y + 3), "orange3", 0.85 - i * 0.12, 0.2, "x", 4, rect_mask)
    # floor stripes: parallelograms skewing toward the viewer-left
    fm = mk([(0, WALL_BASE), (W, WALL_BASE), (W, 158), (0, 158)])
    for i in range(5):
        a = 232 - i * 6
        pts = [(a + 30 - i * 12, WALL_BASE + 1 + i * 6), (a + 66 - i * 12, WALL_BASE + 1 + i * 6),
               (a + 56 - i * 18, WALL_BASE + 4 + i * 8), (a + 20 - i * 18, WALL_BASE + 4 + i * 8)]
        ov(img, bb(pts), "orange3", 0.75 - i * 0.1, 0.75 - i * 0.1, "y", 2, mk(pts))


def filing_cabinets(img):
    # two tall 4-drawer cabinets against the left wall
    for k, x0 in enumerate([6, 38]):
        y0, w, hgt = 62, 30, WALL_BASE - 62 + 3
        rct(img, x0, y0, w, hgt, "grey2", "ink")
        dither_grad(img, (x0 + 1, y0 + 1, x0 + w - 1, y0 + hgt - 1), "grey3", "grey2", "x", 4, 0.0, 0.9)
        for d in range(4):
            yy = y0 + 3 + d * 14
            rct(img, x0 + 3, yy, w - 6, 12, "grey3", "ink")
            hl(img, x0 + 4, x0 + w - 5, yy + 1, "grey4")
            rect(img, x0 + w // 2 - 4, yy + 4, 8, 2, "ink2", "ink")
            rect(img, x0 + w // 2 - 3, yy + 7, 6, 3, "wall1", "ink")  # label card
            hl(img, x0 + 4, x0 + w - 5, yy + 11, "grey1")
        # rust / dents
        for (rx, ry) in [(5, 30), (22, 14), (12, 50)]:
            rect(img, x0 + rx, y0 + ry, 3, 2, "orange1")
        # feet
        rect(img, x0 + 2, y0 + hgt - 2, w - 4, 2, "ink")
    # clutter on top: stacked folders and a box
    rct(img, 8, 52, 24, 10, "brown3", "ink")
    hl(img, 9, 30, 54, "wall1")
    rect(img, 12, 49, 14, 3, "wall1", "ink")
    rct(img, 40, 55, 22, 7, "wall1", "ink")
    rct(img, 44, 50, 16, 5, "orange3", "ink")
    rct(img, 50, 44, 8, 6, "wall3", "ink")


def wall_calendar(img):
    x0, y0 = 108, 36
    rct(img, x0, y0, 26, 34, "white", "ink")
    rect(img, x0 + 1, y0 + 1, 24, 9, "red2")
    hl(img, x0 + 1, x0 + 24, y0 + 1, "red3")
    text(img, x0 + 13, y0 + 0, "11월", "white", 9, align="center")
    for r in range(5):
        for c in range(7):
            xx, yy = x0 + 2 + c * 3, y0 + 13 + r * 4
            col_ = "red2" if c == 0 else "grey2"
            rect(img, xx, yy, 2, 2, col_)
    # circled / crossed days
    for (c, r) in [(2, 1), (3, 1), (4, 1), (1, 2), (5, 2)]:
        rect(img, x0 + 2 + c * 3, y0 + 13 + r * 4, 2, 2, "ink")
    ellipse(img, x0 + 15, y0 + 21, x0 + 21, y0 + 27, None, "red2")
    px(img, x0 + 13, y0 - 1, "ink")
    vl(img, x0 + 13, y0 - 3, y0 - 1, "ink")


def corkboard(img):
    x0, y0, w, h = 178, 38, 40, 36
    rct(img, x0 - 2, y0 - 2, w + 4, h + 4, "brown1", "ink")
    rect(img, x0, y0, w, h, "brown3")
    dither_grad(img, (x0, y0, x0 + w, y0 + h), "brown3", "brown2", "y", 4, 0.0, 0.8)
    rnd = random.Random(8)
    cards = [(3, 3, 11, 9, "wall1", "red2"), (17, 2, 10, 8, "yellow2", "blue1"), (29, 4, 9, 10, "wall3", "green1"),
             (4, 15, 10, 8, "wall4", "blue1"), (17, 13, 12, 9, "white", "red2"), (31, 17, 8, 9, "yellow2", "orange1"),
             (6, 26, 11, 8, "wall2", "purple1"), (21, 25, 14, 9, "wall1", "red2")]
    for (cx, cy, cw, ch, c, ac) in cards:
        rect(img, x0 + cx, y0 + cy, cw, ch, c, "ink")
        rect(img, x0 + cx + 1, y0 + cy + 1, cw - 3, 2, ac)
        for k in range(2):
            hl(img, x0 + cx + 1, x0 + cx + cw - 3 - k * 2, y0 + cy + 4 + k * 2, "grey2")
        px(img, x0 + cx + cw // 2, y0 + cy, "red2")  # pushpin
    text(img, x0 + 3, y0 + h + 3, "구인", "yellow", 9, edge="ink")


def wall_notice(img):
    # handwritten-ish notices on the wall above the cabinets/centre: small
    rct(img, 76, 40, 24, 22, "wall1", "ink")
    rect(img, 78, 43, 20, 2, "red2")
    for k in range(4):
        hl(img, 78, 96 - (k % 2) * 4, 48 + k * 3, "grey2")
    px(img, 88, 40, "red2")
    # clock stopped
    cx, cy = 150, 52
    ellipse(img, cx - 8, cy - 8, cx + 8, cy + 8, "wall1", "ink")
    line(img, [(cx, cy), (cx, cy - 5)], "ink")
    line(img, [(cx, cy), (cx + 4, cy + 2)], "red2")
    for a in range(12):
        ang = a * math.pi / 6
        px(img, int(cx + 6.3 * math.sin(ang)), int(cy - 6.3 * math.cos(ang)), "grey2")


def leaf(img, x, y, dx, dy, c, n=5):
    """drooping pointed leaf from (x,y) heading (dx,dy)."""
    ex, ey = x + dx, y + dy
    mx, my = (x + ex) // 2, (y + ey) // 2
    nx, ny = (-dy, dx)
    k = 0.28
    pts = [(x, y), (int(mx + nx * k), int(my + ny * k)), (ex, ey), (int(mx - nx * k), int(my - ny * k))]
    poly(img, pts, c, "ink")
    line(img, [(x, y), (ex, ey)], DARK.get(c, "ink"))


def dying_plant(img):
    x, y = 252, 127   # pot base centre
    rct(img, x - 9, y - 15, 18, 15, "orange1", "ink")
    rect(img, x - 8, y - 14, 16, 2, "orange2")
    hl(img, x - 8, x + 7, y - 12, "orange2")
    rect(img, x - 7, y - 4, 14, 3, "orange0")
    rct(img, x - 10, y - 18, 20, 4, "orange2", "ink")        # rim
    rect(img, x - 8, y - 17, 16, 2, "brown0")                # dry soil
    # stems
    for (ex, ey) in [(-3, -34), (3, -38), (-8, -28), (9, -30)]:
        line(img, [(x, y - 17), (x + ex, y + ey)], "brown0")
    # drooping leaves, mostly dead
    leaf(img, x - 3, y - 34, -9, 10, "green1")
    leaf(img, x - 3, y - 34, -2, 12, "brown2")
    leaf(img, x + 3, y - 38, 10, 9, "brown3")
    leaf(img, x + 3, y - 38, 3, 13, "yellow")
    leaf(img, x - 8, y - 28, -10, 9, "brown2")
    leaf(img, x + 9, y - 30, 8, 11, "brown3")
    leaf(img, x, y - 36, 0, -6, "green2")                    # one last green shoot
    # fallen leaves
    for (lx, ly) in [(-15, -1), (13, 0), (-5, 1)]:
        rect(img, x + lx, y + ly - 1, 4, 2, "brown3", "ink")


def desk_layer(lamp_on=True):
    L = new()
    dx0, dx1 = 82, 238
    ty, tb = 104, 111      # desktop top surface y range
    # desk top surface (viewed from slightly above)
    rect(L, dx0, ty, dx1 - dx0, tb - ty, "brown3", "ink")
    # lit by the lamp
    cm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cm).rectangle([dx0 + 1, ty + 1, dx1 - 2, tb - 1], fill=255)
    dither_grad(L, (dx0 + 1, ty + 1, dx1 - 1, tb), "brown3", "brown2", "x", 4, 0.9, 0.5, cm)
    ovoval(L, LAMP[0], ty + 3, 54, 10, "orange4", 1.3, 4, cm, only=False, pw=0.8)
    ovoval(L, LAMP[0], ty + 3, 30, 6, "yellow2", 1.0, 4, cm, only=False, pw=1.0)
    # front lip
    rect(L, dx0 - 2, tb, dx1 - dx0 + 4, 4, "brown2", "ink")
    hl(L, dx0 - 1, dx1 + 1, tb + 1, "brown3")
    # front panel with drawers
    rect(L, dx0, tb + 4, dx1 - dx0, 150 - tb - 4, "brown1", "ink")
    dither_grad(L, (dx0 + 1, tb + 5, dx1 - 1, 149), "brown1", "brown0", "x", 4, 0.0, 0.75)
    ov(L, (dx0 + 1, tb + 5, dx1 - 1, 149), "brown2", 0.15, 0.0, "y", 4)
    # modesty panel + two drawer stacks
    rct(L, dx0 + 6, tb + 8, 40, 36, "brown2", "ink")
    rct(L, dx1 - 46, tb + 8, 40, 36, "brown2", "ink")
    for sx in (dx0 + 6, dx1 - 46):
        for d in range(3):
            yy = tb + 10 + d * 11
            rct(L, sx + 3, yy, 34, 9, "brown1", "ink")
            hl(L, sx + 4, sx + 36, yy + 1, "brown3")
            rect(L, sx + 14, yy + 3, 12, 2, "orange3", "ink")
    # centre knee panel in shadow with a taped note
    rect(L, dx0 + 52, tb + 8, dx1 - dx0 - 104, 38, "brown0", "ink")
    dither_grad(L, (dx0 + 53, tb + 9, dx1 - 53, tb + 46), "brown0", "ink", "y", 2, 0.2, 0.7)
    rect(L, 154, 124, 12, 10, "wall1", "ink")
    hl(L, 156, 163, 127, "grey2")
    hl(L, 156, 161, 130, "grey2")
    # legs / base
    rect(L, dx0 + 2, 146, 8, 4, "ink", None)
    rect(L, dx1 - 10, 146, 8, 4, "ink", None)
    hl(L, dx0, dx1 - 1, 149, "ink")
    # ----- things on the desk
    # stack of papers (left of centre)
    for k, (px0, pw, ph, c) in enumerate([(124, 18, 3, "wall1"), (126, 16, 3, "white"), (123, 17, 3, "wall4")]):
        yy = ty + 2 - ph * k
        rect(L, px0, yy, pw, ph + 1, c, "ink")
    rect(L, 124, 96, 18, 1, "grey2")
    # loose sheet with red stamp
    rect(L, 144, ty + 2, 11, 4, "white", "ink")
    rect(L, 148, ty + 3, 3, 2, "red2")
    # name plate (front-centre)
    rct(L, 146, 92, 30, 15, "orange3", "ink")
    hl(L, 147, 174, 93, "orange4")
    text(L, 161, 95, "곽실장", "ink", 9, align="center")
    rect(L, 148, 106, 26, 1, "brown0")
    # rotary-style phone (right)
    rct(L, 196, 98, 24, 9, "red2", "ink")          # body
    hl(L, 198, 217, 99, "red3")
    rect(L, 199, 94, 18, 5, "red2", "ink")          # handset
    rect(L, 197, 92, 5, 7, "red2", "ink")
    rect(L, 214, 92, 5, 7, "red2", "ink")
    hl(L, 200, 214, 95, "red3")
    ellipse(L, 203, 99, 213, 106, "grey4", "ink")   # dial
    ellipse(L, 206, 101, 210, 104, "red1", "ink")
    for a in range(8):
        ang = a * math.pi / 4
        px(L, int(208 + 4 * math.cos(ang)), int(102.5 + 3 * math.sin(ang)), "ink")
    vl(L, 221, 98, 104, "ink")
    # mug and pen cup
    rct(L, 182, 100, 8, 7, "white", "ink")
    rect(L, 183, 101, 6, 2, "brown1")
    px(L, 190, 103, "ink")
    # desk lamp (left)
    lx = LAMP[0]
    rect(L, lx - 9, 104, 18, 4, "grey2", "ink")             # base
    hl(L, lx - 8, lx + 7, 105, "grey3")
    line(L, [(lx - 1, 104), (lx - 7, 90)], "ink")
    line(L, [(lx, 104), (lx - 6, 90)], "grey3")
    line(L, [(lx - 7, 90), (lx + 6, 80)], "ink")
    line(L, [(lx - 6, 90), (lx + 7, 80)], "grey3")
    poly(L, [(lx + 3, 76), (lx + 17, 76), (lx + 21, 86), (lx - 1, 86)], "orange2", "ink")   # shade
    hl(L, lx + 5, lx + 15, 77, "orange3")
    rect(L, lx + 5, 86, 12, 2, "yellow2")                    # bulb
    # pencils / pen
    line(L, [(166, ty + 4), (178, ty + 2)], "ink")
    return L


def lamp_glow_on_wall(img):
    lx, ly = LAMP[0] + 8, 88
    m = mk([(0, 28), (W, 28), (W, WALL_BASE), (0, WALL_BASE)])
    ovoval(img, lx, ly - 4, 68, 56, "orange2", 0.9, 4, m, pw=1.1)
    ovoval(img, lx, ly - 2, 40, 34, "orange3", 0.9, 4, m, pw=1.0)
    ovoval(img, lx, ly, 18, 16, "orange4", 1.0, 4, m, pw=1.0)
    # also on the floor
    fm = mk([(0, WALL_BASE), (W, WALL_BASE), (W, 158), (0, 158)])
    ovoval(img, lx - 10, 140, 50, 14, "orange2", 0.6, 4, fm)


def office_shadows(img):
    # ink shadows under cabinets / beside desk
    fm = mk([(0, WALL_BASE), (W, WALL_BASE), (W, 158), (0, 158)])
    for (pts) in [[(4, WALL_BASE), (70, WALL_BASE), (90, 135), (12, 135)],
                  [(236, WALL_BASE), (262, WALL_BASE), (276, 133), (250, 133)],
                  [(76, 150), (244, 150), (252, 158), (68, 158)]]:
        ov(img, bb(pts), "ink", 0.65, 0.65, "y", 2, mk(pts))


def build_agency():
    img = new(fill="ink")
    office_wall(img)
    blind_light(img)
    lamp_glow_on_wall(img)
    window_blinds(img)
    wall_notice(img)
    wall_calendar(img)
    corkboard(img)
    filing_cabinets(img)
    dying_plant(img)
    office_shadows(img)
    desk = desk_layer()
    # soft contact shadow under desk (floor)
    scene = img.copy()
    paste(scene, desk)
    letterbox(scene)
    d = desk.copy()
    return scene, d



# ==========================================================================
# 5. BACKROOM / STOCK ROOM
# ==========================================================================
BR_X = 118
BR_BOARDS = [-30, -6, 18, 42, 66]
BOX_PAL = ["brown2", "brown3", "brown1", "brown2", "wall1", "brown3", "grey3", "blue2", "brown2", "orange1"]
BOX_LAB = ["wall1", "orange3", "brown3", "white", "orange2"]
BR_L = gen_items(31, 1.0, 1.72, BR_BOARDS, (0.09, 0.17), (0.65, 1.0), gapp=0.12, bottles=0.0, pal=BOX_PAL, labs=BOX_LAB)
BR_R = gen_items(47, 1.0, 1.72, BR_BOARDS, (0.09, 0.17), (0.65, 1.0), gapp=0.12, bottles=0.0, pal=BOX_PAL, labs=BOX_LAB)
BR_DOOR = (-46, 46)


def br_walls(img):
    # ceiling
    pts = [(-12, 22), (332, 22), pt(ZW, XW, CEIL), pt(ZW, -XW, CEIL)]
    poly(img, pts, "grey1")
    dither_grad(img, (0, 22, W, 46), "ink2", "grey1", "y", 4, 0.9, 0.2, mk(pts))
    for X in range(-170, 171, 56):
        line(img, [pt(1.0, X, CEIL), pt(ZW, X, CEIL)], "ink2")
    # pipes along the ceiling
    for X, w in [(-72, 5), (88, 4)]:
        a, b = pt(1.0, X, CEIL + 8), pt(ZW, X, CEIL + 8)
        line(img, [a, b], "ink", w + 2)
        line(img, [a, b], "grey2", w)
        line(img, [(a[0], a[1] - 1), (b[0], b[1] - 1)], "grey3", 1)
        for z in (1.15, 1.45, 1.7):
            x, y = pt(z, X, CEIL + 8)
            rect(img, x - 1, y - 5, 3, 5, "ink2", "ink")
    line(img, [pt(ZW, -XW, CEIL), pt(ZW, XW, CEIL)], "ink")
    # back wall (concrete block)
    ax, ay = pt(ZW, -XW, CEIL)
    bx, by = pt(ZW, XW, FLOOR)
    bw = [(ax, ay), (bx, ay), (bx, by), (ax, by)]
    poly(img, bw, "grey3")
    dither_grad(img, bb(bw), "grey3", "grey2", "y", 4, 0.0, 0.7, mk(bw))
    for k, y in enumerate(range(ay + 6, by, 8)):
        hl(img, ax, bx - 1, y, "grey2")
        for x in range(ax + (k % 2) * 10, bx, 20):
            vl(img, x, y, min(by - 1, y + 7), "grey2")
    # side walls
    for sd in (-1, 1):
        pts = [pt(1.0, sd * XW, CEIL), pt(ZW, sd * XW, CEIL), pt(ZW, sd * XW, FLOOR), pt(1.0, sd * XW, FLOOR)]
        poly(img, pts, "grey2")
        dither_grad(img, bb(pts), "grey1", "grey2", "x", 4, 0.9 if sd < 0 else 0.0, 0.0 if sd < 0 else 0.9, mk(pts))
        line(img, [pt(1.0, sd * XW, FLOOR), pt(ZW, sd * XW, FLOOR)], "ink")
        line(img, [pt(ZW, sd * XW, CEIL), pt(ZW, sd * XW, FLOOR)], "ink")
    # damp stains + drip
    ov(img, (ax, ay, bx, ay + 22), "grey2", 0.0, 0.5, "y", 2, mk(bw))
    for (x, w) in [(88, 7), (232, 5)]:
        ovoval(img, x, 52, w, 9, "grey1", 1.0, 2, mk(bw))
        vl(img, x, 52, 100, "grey2")
        vl(img, x + 1, 56, 84, "grey1")
    # floor
    fp = [pt(0.9, -XW, FLOOR), pt(0.9, XW, FLOOR), pt(ZW, XW, FLOOR), pt(ZW, -XW, FLOOR)]
    poly(img, fp, "grey3")
    fm = mk(fp)
    dither_grad(img, bb(fp), "grey2", "grey3", "y", 4, 0.9, 0.2, fm)
    # slab joints
    for z in (1.0, 1.35, 1.7):
        line(img, [pt(z, -XW, FLOOR), pt(z, XW, FLOOR)], "grey1")
    for X in (-85, 0, 85):
        line(img, [pt(0.9, X, FLOOR), pt(ZW, X, FLOOR)], "grey1")
    # concrete speckle
    rnd = random.Random(2)
    for _ in range(170):
        x = rnd.randint(0, 319)
        y = rnd.randint(116, 157)
        if fm.getpixel((x, y)):
            px(img, x, y, rnd.choice(["grey1", "grey4", "grey2"]))
    # cracks
    pts_ = [(40, 150), (52, 144), (60, 146), (74, 138), (80, 139)]
    line(img, pts_, "ink2")
    line(img, [(250, 152), (240, 146), (244, 140), (232, 136)], "ink2")
    # a dark stain trail leading toward the door
    for (x, y, rx, ry) in [(160, 126, 14, 4), (150, 134, 10, 3), (168, 141, 12, 3), (156, 150, 9, 3)]:
        ovoval(img, x, y, rx, ry, "ink2", 1.4, 2, fm)
    for (x0, y0, x1, y1) in [(138, 131, 164, 123), (146, 140, 172, 132), (141, 148, 160, 143)]:
        line(img, [(x0, y0), (x1, y1)], "ink2")
    ov(img, (0, 114, W, 158), "grey1", 0.0, 0.3, "y", 4, fm)


def br_rack_posts(img, side, zfrom, zto):
    X = side * BR_X
    for z in [1.0 + 0.24 * k for k in range(4)]:
        if not (zfrom <= z < zto):
            continue
        q3(img, [(z, X, -34), (z + 0.03, X, -34), (z + 0.03, X, FLOOR), (z, X, FLOOR)], "grey3", "ink")
        line(img, [pt(z, X, -32), pt(z, X, FLOOR - 1)], "grey4")


def br_rack(img, side, zfrom, zto):
    items = BR_L if side < 0 else BR_R
    side_unit(img, side, BR_X, 1.0, 1.72, BR_BOARDS, items, "grey1", "grey2", None, "ink2", zfrom, zto)
    br_rack_posts(img, side, zfrom, zto)


def br_rack_end(img, side):
    xa, ya = pt(1.0, side * XW, -34)
    xb, yb = pt(1.0, side * BR_X, FLOOR)
    x0, x1 = min(xa, xb), max(xa, xb)
    rect(img, x0, ya, x1 - x0 + 1, yb - ya + 1, "grey1", "ink")
    rnd = random.Random(7 if side < 0 else 9)
    for k in range(len(BR_BOARDS) - 1):
        top = ya + 4 + k * 26 + 0
        for xx in range(x0 + 4, x1 - 6, 11):
            bw_ = rnd.choice([9, 10, 11])
            bh = rnd.choice([16, 19, 21])
            c = rnd.choice(["brown2", "brown3", "brown1", "wall1"])
            rect(img, xx, top + 24 - bh, bw_, bh, c, "ink")
            rect(img, xx + 1, top + 26 - bh, bw_ - 2, 3, LIGHT.get(c, c))
            hl(img, xx + 1, xx + bw_ - 2, top + 24 - bh // 2, DARK.get(c, "ink"))
            vl(img, xx + bw_ // 2, top + 24 - bh, top + 23 - bh // 2 - 3, "orange2")
        rct(img, x0, top + 24, x1 - x0 + 1, 3, "grey2", "ink")
    # end posts
    for xx in (x0, x1 - 3):
        rct(img, xx, ya, 4, yb - ya + 1, "grey3", "ink")
        vl(img, xx + 1, ya + 1, yb - 1, "grey4")
    rect(img, x0, yb - 6, x1 - x0 + 1, 6, "ink2", "ink")


def br_door(img):
    xa, ya = pt(ZW, BR_DOOR[0], -22)
    xb, yb = pt(ZW, BR_DOOR[1], FLOOR)
    # steel frame
    rct(img, xa - 3, ya - 3, xb - xa + 7, yb - ya + 3, "grey1", "ink")
    rct(img, xa, ya, xb - xa + 1, yb - ya, "grey2", "ink")
    dither_grad(img, (xa + 1, ya + 1, xb, yb), "grey3", "grey2", "x", 4, 0.0, 0.8)
    # panels
    rct(img, xa + 5, ya + 6, xb - xa - 9, 18, "grey2", "ink")
    rct(img, xa + 5, ya + 29, xb - xa - 9, 20, "grey2", "ink")
    hl(img, xa + 6, xb - 5, ya + 7, "grey3")
    hl(img, xa + 6, xb - 5, ya + 30, "grey3")
    for (rx, ry) in [(xa + 3, ya + 3), (xb - 3, ya + 3), (xa + 3, yb - 8), (xb - 3, yb - 8), (xa + 3, ya + 27), (xb - 3, ya + 27)]:
        rect(img, rx, ry, 2, 2, "grey4", "ink")
    # push bar and handle
    rect(img, xa + 4, ya + 26, xb - xa - 7, 3, "grey4", "ink")
    hl(img, xa + 5, xb - 4, ya + 27, "white")
    # sign
    rct(img, xa + 7, ya + 9, xb - xa - 13, 12, "yellow", "ink")
    text(img, (xa + xb) // 2 + 1, ya + 10, "출입금지", "red1", 9, align="center")
    # gap of light under the door
    rect(img, xa + 1, yb - 3, xb - xa - 1, 3, "pale2")
    hl(img, xa + 1, xb - 1, yb - 2, "white")
    # scratches low on the door
    for k in range(4):
        line(img, [(xa + 8 + k * 3, yb - 9), (xa + 10 + k * 3, yb - 20)], "ink2")
    # door light spill on floor: fan widening toward camera
    fan = [pt(ZW, BR_DOOR[0], FLOOR), pt(ZW, BR_DOOR[1], FLOOR), pt(1.1, 95, FLOOR), pt(1.1, -95, FLOOR)]
    ov(img, bb(fan), "pale2", 0.95, 0.0, "y", 4, mk(fan), only=False)
    ov(img, bb(fan), "white", 0.5, 0.0, "y", 4, mk([pt(ZW, -30, FLOOR), pt(ZW, 30, FLOOR), pt(1.45, 52, FLOOR), pt(1.45, -52, FLOOR)]), only=False)


def br_door_post(img):
    """sign + the light under the door, drawn after the bulb glow so they stay crisp."""
    xa, ya = pt(ZW, BR_DOOR[0], -22)
    xb, yb = pt(ZW, BR_DOOR[1], FLOOR)
    rct(img, xa + 7, ya + 9, xb - xa - 13, 12, "yellow", "ink")
    hl(img, xa + 8, xb - 7, ya + 10, "yellow2")
    text(img, (xa + xb) // 2 + 1, ya + 10, "출입금지", "red1", 9, align="center")
    rect(img, xa + 1, yb - 3, xb - xa - 1, 3, "pale2")
    hl(img, xa + 1, xb - 1, yb - 2, "white")
    fan = [pt(ZW, BR_DOOR[0] - 6, FLOOR), pt(ZW, BR_DOOR[1] + 6, FLOOR), pt(1.1, 110, FLOOR), pt(1.1, -110, FLOOR)]
    ov(img, bb(fan), "pale2", 1.0, 0.1, "y", 4, mk(fan), only=False)
    ov(img, bb(fan), "white", 0.6, 0.0, "y", 4, mk([pt(ZW, -34, FLOOR), pt(ZW, 34, FLOOR), pt(1.5, 56, FLOOR), pt(1.5, -56, FLOOR)]), only=False)
    # shadows of the shelf posts crossing the light
    for X in (-76, 76):
        pts = [pt(ZW, X, FLOOR), pt(ZW, X + 4, FLOOR), pt(1.15, X * 0.5, FLOOR), pt(1.15, X * 0.5 - 6, FLOOR)]
        ov(img, bb(pts), "ink2", 0.9, 0.9, "y", 2, mk(pts), only=False)


def br_locker(img):
    x0, y0 = pt(1.75, 62, -32)
    x1, y1 = pt(1.75, 130, FLOOR)
    rct(img, x0, y0, x1 - x0 + 1, y1 - y0 + 1, "pale1", "ink")
    dither_grad(img, (x0 + 1, y0 + 1, x1, y1), "pale1", "grey2", "x", 4, 0.0, 0.9)
    half = (x1 - x0) // 2
    for i in range(2):
        dx = x0 + 2 + i * half
        rct(img, dx, y0 + 3, half - 3, y1 - y0 - 7, "pale1", "ink")
        hl(img, dx + 1, dx + half - 5, y0 + 4, "pale2")
        for k in range(4):
            hl(img, dx + 3, dx + half - 7, y0 + 7 + k * 2, "grey1")
        rect(img, dx + half - 8, y0 + 24, 2, 5, "grey4", "ink")
        rect(img, dx + 3, y0 + 14, half - 9, 5, "wall1", "ink")
    # first door ajar with dark gap + blue sleeve
    dx = x0 + 2
    rect(img, dx + half - 4, y0 + 4, 2, y1 - y0 - 9, "ink")
    rect(img, dx + half - 4, y0 + 30, 2, 6, "pale2")
    rect(img, x0 + 1, y1 - 2, x1 - x0 - 1, 2, "ink2")


def br_bucket(img):
    x, y = pt(1.62, -92, FLOOR)
    # puddle
    ovoval(img, x + 1, y + 1, 20, 4, "grey1", 1.4, 2, None, only=False)
    ovoval(img, x - 3, y + 1, 9, 2, "blue2", 1.2, 4, None, only=False)
    # bucket body (trapezoid)
    poly(img, [(x - 9, y - 14), (x + 9, y - 14), (x + 7, y), (x - 7, y)], "yellow", "ink")
    rect(img, x - 8, y - 12, 16, 2, "yellow2")
    rect(img, x - 7, y - 4, 14, 3, "orange2")
    hl(img, x - 7, x + 6, y - 14, "ink")
    ellipse(img, x - 8, y - 17, x + 8, y - 12, "grey1", "ink")        # dirty water
    hl(img, x - 4, x + 3, y - 15, "grey2")
    # wringer
    rct(img, x + 9, y - 13, 6, 9, "grey2", "ink")
    rect(img, x + 10, y - 12, 4, 3, "grey3")
    # casters
    rect(img, x - 7, y, 3, 2, "ink")
    rect(img, x + 4, y, 3, 2, "ink")
    # mop leaning on the back wall
    line(img, [(x + 2, y - 15), (x + 16, y - 60)], "ink", 3)
    line(img, [(x + 2, y - 15), (x + 16, y - 60)], "brown2", 1)
    poly(img, [(x - 5, y - 20), (x + 10, y - 20), (x + 11, y - 8), (x - 6, y - 8)], "wall1", "ink")
    for k in range(-4, 10, 3):
        vl(img, x + k, y - 18, y - 9, "grey3")


def br_breaker(img):
    x0, y0 = pt(1.8, -112, -20)
    x1, y1 = pt(1.8, -74, 14)
    rct(img, x0, y0, x1 - x0 + 1, y1 - y0 + 1, "grey1", "ink")
    rect(img, x0 + 2, y0 + 2, x1 - x0 - 3, y1 - y0 - 3, "grey2", "ink")
    for k in range(3):
        for j in range(2):
            rect(img, x0 + 4 + j * 6, y0 + 4 + k * 5, 4, 3, "ink2" if (k + j) % 2 else "red2", "ink")
    poly(img, [(x0 + 15, y0 - 3), (x0 + 22, y0 - 3), (x0 + 19, y0 - 10)], "yellow", "ink")
    px(img, x0 + 19, y0 - 6, "ink")
    # wire conduit running up to the ceiling
    vl(img, x0 + 8, ay_ := pt(ZW, 0, CEIL)[1], y0 - 1, "ink")
    vl(img, x0 + 9, ay_, y0 - 1, "grey1")


def br_boxes_floor(img):
    # a few cartons dumped at the foot of the left rack and near the right locker
    for (X, z, w, h, c) in [(-100, 1.35, 22, 14, "brown2"), (-84, 1.52, 18, 11, "brown3")]:
        pass
    x, y = pt(1.55, 92, FLOOR)
    for (dx, dy, w, h, c) in [(0, 0, 14, 11, "brown2"), (12, -1, 12, 9, "brown3"), (4, -11, 11, 8, "brown3")]:
        rct(img, x + dx - 6, y + dy - h, w, h, c, "ink")
        rect(img, x + dx - 5, y + dy - h + 1, w - 2, 2, LIGHT.get(c, "orange3"))
        vl(img, x + dx - 6 + w // 2, y + dy - h + 1, y + dy - h + 3, "orange2")
    ovoval(img, x + 4, y + 1, 17, 3, "ink2", 1.2, 2, None, only=False)


def br_bulb(img):
    cx, cy0 = pt(1.3, 0, CEIL)
    by = pt(1.3, 0, -16)[1]
    vl(img, cx, cy0, by - 4, "ink")
    rect(img, cx - 2, by - 4, 5, 4, "grey2", "ink")
    ellipse(img, cx - 4, by - 1, cx + 4, by + 8, "yellow2", "ink")
    rect(img, cx - 2, by + 1, 2, 3, "white")
    return cx, by + 3


def br_light(img, cx, cy):
    allm = mk([(0, 22), (W, 22), (W, 158), (0, 158)])
    ovoval(img, cx, cy + 22, 96, 64, "orange3", 0.30, 4, allm, pw=1.3)
    ovoval(img, cx, cy + 14, 56, 40, "orange4", 0.38, 4, allm, pw=1.3)
    ovoval(img, cx, cy + 6, 22, 18, "yellow2", 0.75, 4, allm, pw=1.0)
    # pooled light on the floor under the bulb
    fl = mk([(0, 116), (W, 116), (W, 158), (0, 158)])
    ovoval(img, cx, 140, 70, 14, "orange4", 0.5, 4, fl, pw=1.2)
    # dark vignette (m=2) at the edges, deepening toward the corners
    ov(img, (0, 22, 60, 158), "ink2", 0.55, 0.0, "x", 2, allm)
    ov(img, (260, 22, 320, 158), "ink2", 0.0, 0.55, "x", 2, allm)
    ov(img, (0, 22, W, 40), "ink", 0.6, 0.0, "y", 2, allm)
    ov(img, (0, 140, W, 158), "ink2", 0.0, 0.5, "y", 2, allm)


def build_backroom():
    img = new(fill="ink")
    br_walls(img)
    br_breaker(img)
    br_locker(img)
    br_door(img)
    br_bucket(img)
    br_boxes_floor(img)
    br_rack(img, -1, 1.0, 1.8)
    br_rack(img, 1, 1.0, 1.8)
    br_rack_end(img, -1)
    br_rack_end(img, 1)
    cx, cy = br_bulb(img)
    br_light(img, cx, cy)
    br_door_post(img)
    # re-draw the bulb crisp over its own glow
    ellipse(img, cx - 4, cy - 4, cx + 4, cy + 5, "yellow2", "ink")
    rect(img, cx - 2, cy - 2, 2, 3, "white")
    letterbox(img)
    return img


if __name__ == "__main__":
    which = sys.argv[1:] or ["store", "agency", "backroom"]
    files = ["bg/store_day.png", "bg/store_wrong.png", "bg/store_fg.png", "bg/agency_office.png",
             "bg/agency_desk_fg.png", "bg/backroom.png"]
    if "store" in which:
        build_all_store()
    if "agency" in which:
        sc, d = build_agency()
        save(sc, "bg/agency_office.png")
        save(d, "bg/agency_desk_fg.png")
    if "backroom" in which:
        save(build_backroom(), "bg/backroom.png")
    if len(which) == 3:
        for f in files + ["bg/store_fg_wrong.png"]:
            im = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
            print(f, im.size, "off-palette:", off_palette(im) or "none")
        contact(files, "_contact/bg_interior.png", cols=2, scale=2)

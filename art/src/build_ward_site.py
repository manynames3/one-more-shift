"""Act 5 (clinical trial ward) + Act 6 (construction site) assets for ONE MORE SHIFT.

Run:  python3 src/build_ward_site.py
Writes assets/bg/{ward,site}.png
       assets/props/{nurse,nurse_notag,subject,pill,foreman}.png/.json
       assets/props/{hoist_closed,hoist_rider,load,brick}.png
       previews/_contact/ward_site.png
Side views, floor band y 140..154, picture area y 22..157.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
from pxkit import *
from pxkit import _thr
from chibi import chibi, FW, FH
from build_delivery import obox, hline, vline, glow, ovl, speckle, streaks, mk_mask, floor_band, tube
from build_event import pool
from PIL import Image, ImageDraw

Y0, Y1 = 22, 157


def vgrad_rect(im, x, y, w, h, c1, c2, t0=0.0, t1=1.0, m=4, ol="ink"):
    rect(im, x, y, w, h, c1, ol)
    dither_grad(im, (x + 1, y + 1, x + w - 1, y + h - 1), c1, c2, "y", m, t0, t1)


def cone(im, pts, c, s=0.5, m=4, only=None):
    """Dithered light cone polygon, densest at pts[0]-ish top, fading towards the bottom."""
    mk = mk_mask(pts, im.size)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    y0, y1 = min(ys), max(ys)
    cc = col(c)
    on = {col(o) for o in only} if only else None
    for y in range(max(0, y0), min(im.height, y1 + 1)):
        f = 1 - (y - y0) / max(1, y1 - y0)
        for x in range(max(0, min(xs)), min(im.width, max(xs) + 1)):
            if mk.getpixel((x, y)) and f * s > _thr(x, y, m):
                if on and im.getpixel((x, y)) not in on:
                    continue
                im.putpixel((x, y), cc)


# =================================================================== WARD
def clock(im, cx, cy, r, hm=(10, 15)):
    ellipse(im, cx - r, cy - r, cx + r, cy + r, "grey1", "ink")
    ellipse(im, cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, "white", "grey3")
    for k in range(12):
        a = k * math.pi / 6
        px(im, round(cx + math.sin(a) * (r - 2)), round(cy - math.cos(a) * (r - 2)), "ink")
    # 3:07 - small hours
    line(im, [(cx, cy), (cx + (r - 3), cy + 1)], "ink")
    line(im, [(cx, cy), (cx + 1, cy - (r - 2))], "ink")
    px(im, cx, cy, "red2")


def curtain(im, x, w, y0, y1):
    """Gathered hospital curtain hanging from the rail (folds = vertical dither stripes)."""
    rect(im, x, y0, w, y1 - y0, "blue3", "ink")
    for i in range(w):
        xx = x + i
        if i % 4 == 1:
            line(im, [(xx, y0 + 1), (xx, y1 - 2)], "blue2")
        elif i % 4 == 2:
            dither_grad(im, (xx, y0 + 1, xx + 1, y1 - 1), "blue3", "blue2", "y", 2, 0.0, 0.5)
        elif i % 4 == 0:
            line(im, [(xx, y0 + 1), (xx, y1 - 3)], "blue4")
    # scalloped hem
    for i in range(0, w, 2):
        px(im, x + i, y1 - 1, "ink")
        px(im, x + i + 1, y1, "ink") if i + 1 < w else None
    # rings at the rail
    for i in range(0, w, 3):
        px(im, x + i, y0 - 1, "grey4")


def iv_stand(im, x, top=80, bag="blue4", fluid="blue3", to=None):
    # base + casters
    rect(im, x - 7, 146, 15, 2, "grey2", "ink")
    hline(im, x - 6, x + 6, 146, "grey4")
    for cx in (x - 7, x + 6):
        rect(im, cx, 148, 2, 3, "ink2", "ink")
    # pole
    rect(im, x - 1, top, 3, 66, "grey3", "ink")
    vline(im, x, top + 1, 144, "white")
    # hook bar
    rect(im, x - 6, top - 2, 13, 3, "grey2", "ink")
    hline(im, x - 5, x + 5, top - 2, "grey4")
    # bags
    for bx in (x - 6, x + 3):
        rect(im, bx, top + 1, 4, 11, bag, "ink")
        rect(im, bx + 1, top + 5, 2, 6, fluid)
        px(im, bx + 1, top + 2, "white")
        px(im, bx + 1, top + 12, "ink")
    # pump box
    rect(im, x - 4, top + 24, 9, 10, "grey4", "ink")
    rect(im, x - 3, top + 26, 7, 3, "ink2", "ink")
    px(im, x - 2, top + 27, "green2"); px(im, x, top + 27, "green2")
    px(im, x - 2, top + 31, "red2"); px(im, x + 1, top + 31, "orange3")
    hline(im, x - 3, x + 3, top + 24, "white")
    # drip tube towards the bed
    if to:
        tx, ty = to
        sx, sy = x + 5, top + 13
        n = 28
        for i in range(n + 1):
            t = i / n
            xx = sx + (tx - sx) * t
            yy = sy + (ty - sy) * t + math.sin(t * math.pi) * 10
            px(im, int(round(xx)), int(round(yy)), "grey4")


def bedside_table(im, x, num):
    w = 18
    # legs
    for lx in (x + 1, x + w - 4):
        rect(im, lx, 142, 3, 8, "grey2", "ink")
    # body
    obox(im, x, 120, w, 22, "grey4", "white", "grey3")
    rect(im, x + 2, 123, w - 4, 8, "grey3", "ink")
    rect(im, x + 2, 133, w - 4, 7, "grey3", "ink")
    hline(im, x + 3, x + w - 4, 124, "grey4")
    hline(im, x + 3, x + w - 4, 134, "grey4")
    rect(im, x + 7, 126, 4, 1, "grey1"); rect(im, x + 7, 136, 4, 1, "grey1")
    # top
    rect(im, x - 2, 117, w + 4, 4, "white", "ink")
    hline(im, x - 1, x + w + 1, 118, "grey4")
    # tent card (blank, numbered)
    rect(im, x + 1, 107, 9, 10, "white", "ink")
    hline(im, x + 2, x + 8, 112, "grey3"); hline(im, x + 2, x + 8, 114, "grey3")
    hline(im, x + 2, x + 6, 115, "grey3")
    text(im, x + 4, 107, str(num), "ink", 7)
    # water cup + jug
    rect(im, x + 12, 111, 4, 6, "blue4", "ink")
    rect(im, x + 13, 113, 2, 3, "blue3")
    rect(im, x + 17, 113, 3, 4, "white", "ink")
    # shadow under
    ovl(im, (x - 2, 150, x + w + 3, 154), "ink", 0.4, 2)


def monitor(im, x, y):
    rect(im, x, y, 16, 11, "grey1", "ink")
    rect(im, x + 1, y + 1, 14, 9, "ink")
    pts = [(2, 6), (4, 6), (5, 3), (6, 8), (7, 6), (10, 6), (11, 5), (12, 6), (13, 6)]
    for a, b in zip(pts, pts[1:]):
        line(im, [(x + a[0], y + a[1]), (x + b[0], y + b[1])], "green2")
    px(im, x + 3, y + 2, "yellow"); px(im, x + 12, y + 2, "red3")
    rect(im, x + 6, y + 11, 4, 2, "grey2", "ink")
    # wall arm
    rect(im, x + 7, y + 13, 2, 6, "grey2", "ink")


def bed(im, X0, num, blanket=("blue3", "blue2")):
    X1 = X0 + 60
    bc, bs = blanket
    # floor shadow
    ovl(im, (X0 - 2, 147, X1 + 4, 155), "ink", 0.5, 2)
    ovl(im, (X0 + 6, 149, X1 - 4, 153), "ink", 0.5, 4)
    # under-bed dark gap
    rect(im, X0 + 5, 137, 50, 9, "ink2")
    dither_grad(im, (X0 + 5, 137, X0 + 55, 146), "ink2", "ink", "y", 4, 0.0, 1.0)
    # legs + casters
    for lx in (X0 + 1, X1 - 5):
        rect(im, lx, 137, 4, 11, "grey2", "ink")
        vline(im, lx + 1, 138, 146, "grey3")
        rect(im, lx, 148, 4, 3, "ink2", "ink")
        px(im, lx + 1, 149, "grey2")
    # tall headboard (left) + low footboard (right)
    obox(im, X0, 100, 5, 37, "grey3", "white", "grey2")
    px(im, X0, 100, "ink"); px(im, X0 + 4, 100, "ink")
    obox(im, X1 - 5, 114, 5, 23, "grey3", "white", "grey2")
    # frame rail
    obox(im, X0, 131, 60, 6, "grey2", "grey3", "grey1")
    hline(im, X0 + 5, X1 - 6, 133, "grey3")
    # mattress
    rect(im, X0 + 5, 124, 50, 8, "white", "ink")
    dither_grad(im, (X0 + 6, 125, X0 + 54, 131), "white", "grey4", "y", 4, 0.0, 1.0)
    hline(im, X0 + 6, X0 + 53, 125, "white")
    # pillow
    ellipse(im, X0 + 8, 118, X0 + 21, 125, "white", "ink")
    dither_grad(im, (X0 + 9, 119, X0 + 21, 125), "white", "grey4", "d", 2, 0.0, 0.9)
    px(im, X0 + 11, 120, "white")
    # folded blanket at the foot
    rect(im, X0 + 34, 119, 21, 13, bc, "ink")
    dither_grad(im, (X0 + 35, 120, X0 + 54, 131), bc, bs, "d", 2, 0.0, 1.0)
    rect(im, X0 + 35, 120, 19, 3, "white")
    hline(im, X0 + 35, X0 + 53, 123, "grey3")
    vline(im, X0 + 44, 124, 130, bs)
    # headboard plate with number
    rect(im, X0 + 1, 104, 3, 5, "white", "ink")
    # call cord from the wall panel hanging at the head
    line(im, [(X0 + 6, 100), (X0 + 6, 112)], "grey2")
    rect(im, X0 + 5, 112, 3, 3, "red2", "ink")


def build_ward():
    im = new(W, H, "ink")
    # ---------------- back wall: cold green-white, dithered
    dither_ramp(im, (0, 44, W, 112), ["pale2", "wall2", "pale1"], "y", 4)
    ovl(im, (0, 44, W, 112), "blue4", 0.18, 4)
    # wall panel seams
    for sx in range(36, W, 64):
        vline(im, sx, 48, 108, "pale1")
        vline(im, sx + 1, 48, 108, "white")
    # dado + rail
    dither_grad(im, (0, 112, W, 138), "pale1", "grey2", "y", 4, 0.0, 0.8)
    ovl(im, (0, 112, W, 138), "green1", 0.18, 4)
    hline(im, 0, W - 1, 110, "ink")
    hline(im, 0, W - 1, 111, "white")
    hline(im, 0, W - 1, 112, "grey3")
    hline(im, 0, W - 1, 136, "grey1")
    hline(im, 0, W - 1, 137, "ink")
    # ---------------- ceiling
    rect(im, 0, Y0, W, 22, "grey3")
    dither_grad(im, (0, Y0, W, 44), "pale1", "grey4", "y", 4, 0.0, 1.0)
    for sx in range(0, W, 32):
        vline(im, sx, Y0, 42, "grey2")
    hline(im, 0, W - 1, 33, "grey2")
    hline(im, 0, W - 1, 43, "ink")
    dither_grad(im, (0, 44, W, 50), "grey1", "pale2", "y", 4, 0.0, 0.7)
    # tube lights - ON
    for (a, b) in ((38, 118), (130, 210), (226, 300)):
        tube(im, a, b, 29, True, False)
        glow(im, a - 4, 36, b + 4, 100, "white", 0.8, 4, 14)
    # ---------------- curtain rail + curtains (gathered between beds)
    rect(im, 22, 51, 276, 2, "grey2", "ink")
    hline(im, 23, 296, 51, "grey4")
    for X0 in (30, 130, 230):
        for cx, w in ((X0 - 6, 9), (X0 + 56, 9)):
            curtain(im, cx, w, 53, 112)
    # ---------------- night window in gap 1-2
    rect(im, 95, 56, 30, 40, "grey3", "ink")
    rect(im, 97, 58, 26, 36, "blue0", "ink")
    dither_grad(im, (98, 59, 122, 93), "ink", "blue1", "y", 4, 0.0, 0.8)
    for p in ((102, 64), (112, 62), (118, 70), (105, 78), (116, 84), (100, 88)):
        px(im, *p, "grey3")
    ellipse(im, 105, 66, 113, 74, "yellow2"); ellipse(im, 107, 65, 114, 73, "blue1")
    vline(im, 110, 58, 94, "grey2"); hline(im, 97, 122, 76, "grey2")
    for bx in range(100, 122, 4):
        vline(im, bx, 59, 93, "ink2")
    rect(im, 93, 96, 34, 3, "grey3", "ink")
    # ---------------- clock above bed 1
    clock(im, 70, 68, 8)
    # ---------------- notice above bed 2 (invented)
    rect(im, 127, 60, 76, 15, "white", "ink")
    rect(im, 128, 61, 74, 13, "wall1")
    draw(im).rectangle([129, 62, 200, 72], outline=col("red2"))
    text(im, 165, 62, "임상 2상 · 정숙", "red1", 9, align="center")
    px(im, 127, 60, "ink")
    # ---------------- chart board in gap 2-3 (blank)
    rect(im, 208, 64, 22, 28, "white", "ink")
    for yy in range(70, 90, 5):
        hline(im, 210, 227, yy, "grey3")
    vline(im, 217, 66, 89, "grey3")
    rect(im, 210, 66, 18, 3, "blue3")
    rect(im, 211, 92, 16, 2, "grey2", "ink")
    # ---------------- monitors + gas panels above heads
    for X0 in (30, 130, 230):
        monitor(im, X0 + 10, 78)
        rect(im, X0 + 34, 82, 12, 8, "grey4", "ink")
        px(im, X0 + 37, 86, "green1"); px(im, X0 + 42, 86, "blue2"); px(im, X0 + 39, 86, "yellow")
        hline(im, X0 + 35, X0 + 44, 83, "white")
    # ---------------- nurse station hatch (lit) far left
    text(im, 14, 58, "간호", "ink", 9, align="center")
    rect(im, 3, 69, 22, 33, "grey2", "ink")
    rect(im, 4, 70, 20, 30, "orange4", "ink")
    dither_grad(im, (5, 71, 23, 99), "yellow2", "orange3", "y", 4, 0.0, 1.0)
    # inside silhouettes: shelf, folders, lamp
    rect(im, 6, 78, 8, 14, "orange1", "ink")
    for yy in (82, 86, 90):
        hline(im, 7, 12, yy, "orange0")
    for i, c in enumerate(("red2", "blue2", "green1", "orange0")):
        rect(im, 7 + i * 2, 74, 2, 4, c, "ink")
    rect(im, 16, 88, 6, 12, "orange0")
    ellipse(im, 15, 82, 21, 88, "yellow2", "ink")
    vline(im, 18, 88, 92, "ink")
    rect(im, 4, 70, 20, 2, "white"); hline(im, 4, 23, 70, "ink")
    # sliding pane frame + highlight
    vline(im, 14, 70, 99, "grey3")
    hline(im, 5, 22, 80, "white")
    rect(im, 1, 100, 26, 4, "grey3", "ink")
    hline(im, 2, 25, 100, "white")
    glow(im, 25, 70, 44, 108, "orange4", 0.5, 4, 6)
    # ---------------- ward door (far right)
    rect(im, 295, 87, 24, 64, "grey1", "ink")
    rect(im, 296, 88, 22, 62, "pale1", "ink")
    dither_grad(im, (297, 89, 317, 149), "pale2", "pale1", "x", 4, 0.0, 1.0)
    rect(im, 300, 96, 14, 18, "blue0", "ink")
    dither_grad(im, (301, 97, 313, 113), "ink", "blue1", "y", 4, 0.0, 0.7)
    hline(im, 301, 312, 97, "grey2")
    px(im, 303, 100, "green2"); px(im, 304, 100, "green2")     # corridor exit light
    rect(im, 298, 140, 18, 9, "grey2", "ink")
    hline(im, 299, 314, 141, "grey3")
    rect(im, 299, 118, 3, 10, "grey4", "ink")
    rect(im, 300, 122, 15, 3, "grey3", "ink")
    rect(im, 292, 76, 26, 10, "green0", "ink")
    text(im, 305, 76, "출입", "white", 9, align="center")
    # ---------------- floor
    floor_band(im, 138, 157, "grey3", "pale1", "grey2", "white", tw=24, seed=11)
    ovl(im, (0, 138, W, 157), "green1", 0.1, 4)
    for (a, b) in ((20, 120), (140, 220), (230, 300)):
        glow(im, a, 138, b, 157, "white", 0.3, 4, 16, up=False)
    # ---------------- furniture, back to front
    bed(im, 30, 1)
    bed(im, 130, 2, ("blue3", "blue2"))
    bed(im, 230, 3)
    bedside_table(im, 94, 1)
    bedside_table(im, 194, 2)
    iv_stand(im, 24, 80, to=(40, 119))
    iv_stand(im, 124, 80, to=(142, 119))
    iv_stand(im, 224, 80, bag="blue4", fluid="green2", to=(242, 119))
    # medicine cart under the hatch
    rect(im, 3, 119, 20, 3, "grey4", "ink")
    obox(im, 4, 122, 18, 20, "grey3", "white", "grey2")
    for yy in (125, 131, 137):
        hline(im, 6, 20, yy, "grey1"); rect(im, 11, yy + 1, 4, 1, "grey1")
    for cx in (5, 18):
        rect(im, cx, 142, 3, 7, "ink2", "ink")
    rect(im, 6, 114, 4, 5, "white", "ink"); rect(im, 12, 113, 3, 6, "blue2", "ink")
    rect(im, 16, 115, 5, 4, "red2", "ink")
    ovl(im, (2, 150, 24, 154), "ink", 0.4, 2)
    letterbox(im)
    return im


# ================================================================= SPRITES
def dress(im, ox=0):
    return im


def nurse_frames(tag):
    # white uniform, pale blue cardigan, dark hair in a LOW bun (nothing like Sora's purple bob + orange hoodie)
    spec = dict(hair_style="short", hair=("brown0", "brown1"), top=("white", "grey4"), outfit="vest",
                vest=("blue3", "blue2"), pants=("white", "grey4"), shoes="grey3", expr="neutral",
                sleeve="blue3")

    def mouth_front(f, oy):
        my = 14 + oy + 5
        # wipe the small neutral mouth, draw a smile that is only slightly too wide
        px(f, 15, my, "skin2"); px(f, 16, my, "skin2")
        line(f, [(12, my), (19, my)], "ink")
        px(f, 11, my - 1, "ink"); px(f, 20, my - 1, "ink")
        line(f, [(13, my + 1), (18, my + 1)], "white")

    def mouth_side(f, oy):
        ey = 14 + oy
        px(f, 7, ey + 5, "skin2"); px(f, 8, ey + 5, "skin2")
        line(f, [(7, ey + 5), (10, ey + 5)], "ink")
        px(f, 11, ey + 4, "ink")
        line(f, [(8, ey + 6), (10, ey + 6)], "white")

    def bun_front(f, oy):
        # low bun peeking out behind the right of the head, hairnet pin
        ellipse(f, 24, 18 + oy, 30, 25 + oy, "brown0")
        px(f, 26, 19 + oy, "brown1"); px(f, 27, 19 + oy, "brown1")

    def bun_side(f, oy):
        ellipse(f, 20, 17 + oy, 28, 25 + oy, "brown0")
        line(f, [(22, 18 + oy), (25, 18 + oy)], "brown1")
        px(f, 20, 20 + oy, "red2")           # hair tie

    def cap_front(f, oy):
        rect(f, 8, 0 + oy, 16, 5, "white", "ink")
        hline(f, 9, 22, 1 + oy, "grey4"); hline(f, 9, 22, 3 + oy, "grey4")
        rect(f, 14, 1 + oy, 4, 3, "red2")
        px(f, 15, 1 + oy, "white"); px(f, 16, 1 + oy, "white")
        px(f, 15, 3 + oy, "white"); px(f, 16, 3 + oy, "white")

    def cap_side(f, oy):
        rect(f, 8, 0 + oy, 15, 5, "white", "ink")
        hline(f, 9, 21, 1 + oy, "grey4"); hline(f, 9, 21, 3 + oy, "grey4")
        rect(f, 11, 1 + oy, 4, 3, "red2")
        px(f, 12, 1 + oy, "white"); px(f, 13, 1 + oy, "white")
        px(f, 12, 3 + oy, "white"); px(f, 13, 3 + oy, "white")

    def tag_at(f, x, y):
        lay = new(FW, FH)
        rect(lay, x, y, 7, 5, "white")
        hline(lay, x, x + 6, y, "red2")               # the red line
        hline(lay, x, x + 6, y + 1, "red2")
        hline(lay, x + 1, x + 4, y + 3, "grey2")      # name scribble
        f.alpha_composite(outline(lay))
        px(f, x + 3, y - 1, "grey2")                  # clip

    def tag_front(f, oy):
        tag_at(f, 11, 28 + oy)

    def tag_side(f, oy):
        tag_at(f, 9, 28 + oy)

    def finish(f, side, oy):
        (cap_side if side else cap_front)(f, oy)
        (bun_side if side else bun_front)(f, oy)
        (cap_side if side else cap_front)(f, oy)
        if tag:
            (tag_side if side else tag_front)(f, oy)
        else:
            (mouth_side if side else mouth_front)(f, oy)
        return f

    frames, names = [], []
    for i in range(2):
        frames.append(finish(chibi(spec, "down", "idle", i), False, i % 2)); names.append(f"down_idle_{i}")
    L = []
    for i in range(4):
        L.append(finish(chibi(spec, "side", "walk", i), True, i % 2))
    for i in range(4):
        frames.append(L[i]); names.append(f"left_walk_{i}")
    for i in range(4):
        frames.append(flip(L[i])); names.append(f"right_walk_{i}")
    # give: facing left, holding out a syringe tray
    g = chibi(spec, "side", "work", 0)
    tray = new(FW, FH)
    rect(tray, 0, 29, 11, 2, "grey3", "ink")
    hline(tray, 1, 9, 29, "white")
    rect(tray, 1, 26, 7, 3, "white", "ink")                # syringe barrel
    rect(tray, 4, 27, 3, 1, "blue3")
    hline(tray, 0, 1, 27, "grey2")                          # needle tip
    px(tray, 8, 27, "ink"); px(tray, 9, 27, "ink"); px(tray, 9, 26, "ink"); px(tray, 9, 28, "ink")
    rect(tray, 8, 23, 3, 3, "red2", "ink")                  # vial
    g.alpha_composite(tray)
    frames.append(finish(g, True, 0)); names.append("give_0")
    return frames, names


SUBJ = dict(hair_style="messy", hair=("brown0", "brown1"), skin=("skin3", "skin2"),
            top=("blue3", "blue2"), outfit="coat", button="blue3", sleeve="blue3",
            pants=("skin3", "skin2"), shoes="grey3", expr="tired")


def band_front(f, x, oy=0):
    rect(f, x, 32 + oy, 3, 2, "white")
    px(f, x + 1, 32 + oy, "red2")


def subject_frames():
    names, frames = [], []
    # back_0: facing away
    b = chibi(SUBJ, "up", "idle", 0)
    for p in ((14, 27), (17, 27), (15, 29), (16, 31)):
        px(b, *p, "white")
    band_front(b, 6); band_front(b, 23)
    frames.append(b); names.append("back_0")
    # turn_0: body from behind, head turned to look at us
    up = chibi(SUBJ, "up", "idle", 0)
    for p in ((14, 27), (17, 27), (15, 29), (16, 31)):
        px(up, *p, "white")
    band_front(up, 6); band_front(up, 23)
    fr = chibi(SUBJ, "down", "idle", 0, "neutral")
    t = new(FW, FH)
    t.paste(up.crop((0, 24, FW, FH)), (0, 24))
    head = fr.crop((0, 0, FW, 25))
    # wide black dot eyes, flat mouth
    for ex in (10, 20):
        ellipse(head, ex - 2, 11, ex + 3, 18, "ink")
    px(head, 15, 21, "ink"); px(head, 16, 21, "ink"); px(head, 17, 21, "ink")
    t.alpha_composite(head, (1, 0))
    t.alpha_composite(outline(t.crop((0, 0, FW, FH))))
    frames.append(outline(t) if False else t); names.append("turn_0")
    # shuffle left
    for i, fi in enumerate((0, 1)):
        w = chibi(SUBJ, "side", "walk", fi)
        oy = fi % 2
        band_front(w, 14 + (2 if fi == 1 else 0), oy)
        frames.append(w); names.append(f"walk_{i}")
    # lie_0: lying on the back in bed, body horizontal at the bottom
    l = new(FW, FH)
    # legs / feet (toes up)
    rect(l, 22, 38, 9, 7, "skin3", "ink")
    rect(l, 28, 36, 3, 4, "skin3", "ink")
    # gown body
    rect(l, 9, 36, 16, 10, "blue3", "ink")
    rect(l, 9, 42, 16, 3, "blue2")
    hline(l, 10, 23, 37, "blue4")
    vline(l, 17, 37, 44, "blue2")
    # arm resting on top, wristband
    rect(l, 11, 38, 11, 3, "blue3", "ink")
    rect(l, 20, 38, 3, 3, "skin3", "ink")
    px(l, 19, 39, "white"); px(l, 19, 40, "red2")
    # head on pillow, looking at the ceiling
    ellipse(l, 1, 33, 11, 44, "skin3", "ink")
    for p in ((3, 34), (4, 33), (5, 33), (6, 33), (7, 34)):
        px(l, *p, "brown0")
    rect(l, 1, 34, 3, 4, "brown0")
    px(l, 5, 38, "ink"); px(l, 6, 38, "ink"); px(l, 5, 39, "ink"); px(l, 6, 39, "ink")
    px(l, 9, 38, "ink"); px(l, 10, 38, "ink") if False else None
    px(l, 8, 41, "skin2"); px(l, 7, 42, "ink"); px(l, 8, 42, "ink")
    frames.append(l); names.append("lie_0")
    return frames, names


def pill(c1, c2, c3):
    im = new(8, 8)
    # capsule in the cup mouth
    rect(im, 1, 1, 6, 3, c1, "ink")
    rect(im, 4, 2, 2, 1, c2)
    px(im, 2, 2, c3)
    # paper cup
    poly(im, [(0, 3), (7, 3), (6, 7), (1, 7)], "white", "ink")
    hline(im, 1, 6, 3, "grey4")
    hline(im, 2, 5, 5, "grey3")
    px(im, 1, 4, "white")
    return im


# ================================================================== SITE
def build_site():
    im = new(W, H, "ink")
    # ---- night sky with a hazy glow on the horizon
    dither_ramp(im, (0, 22, W, 100), ["ink", "blue0", "purple0", "red0"], "y", 4)
    rnd = random.Random(8)
    for _ in range(26):
        px(im, rnd.randint(0, W - 1), rnd.randint(23, 52), rnd.choice(["grey3", "grey2", "blue3"]))
    # ---- distant tower skeleton (unfinished building)
    def frame(x0, x1, ytop, ybot, floors, step=26):
        h = (ybot - ytop) / floors
        for k in range(floors + 1):
            y = int(ytop + k * h)
            rect(im, x0, y, x1 - x0, 3, "purple0")
            hline(im, x0, x1 - 1, y, "grey1")
        for cx in range(x0, x1 + 1, step):
            rect(im, cx, ytop, 4, ybot - ytop, "purple0")
            vline(im, cx, ytop, ybot, "grey1")
            for k in range(3):
                px(im, cx + 1, ytop - 1 - k, "orange1") if k < 2 else None
        # nets
        ovl(im, (x0, int(ytop + h), x1, ybot), "green0", 0.35, 2)
    frame(66, 252, 48, 100, 3, 30)
    frame(20, 66, 74, 100, 1, 23)
    # work lamps on the frame
    for lx, ly in ((90, 68), (150, 60), (212, 68), (236, 86), (40, 84)):
        px(im, lx, ly, "yellow2"); px(im, lx + 1, ly, "yellow2"); px(im, lx, ly + 1, "orange3")
    # ---- tower crane jib across the top edge + trolley
    rect(im, 110, Y0, 160, 5, "ink2")
    for x in range(112, 268, 6):
        line(im, [(x, Y0), (x + 3, Y0 + 4)], "grey1")
    hline(im, 110, 269, Y0 + 4, "grey1")
    rect(im, 174, Y0, 14, 8, "orange2", "ink")
    rect(im, 176, Y0 + 6, 10, 2, "orange1")
    # ---- site hoarding (corrugated panels)
    rect(im, 0, 99, W, 40, "grey2")
    for x in range(0, W, 3):
        vline(im, x, 100, 137, "grey2" if x % 6 else "grey1")
    dither_grad(im, (0, 100, W, 138), "grey3", "grey1", "y", 4, 0.0, 0.9)
    for x in range(0, W, 3):
        if x % 6 == 0:
            vline(im, x, 100, 137, "grey1")
    hline(im, 0, W - 1, 98, "ink")
    hline(im, 0, W - 1, 99, "grey3")
    hline(im, 0, W - 1, 100, "grey4")
    for x in range(0, W, 40):
        rect(im, x, 99, 3, 39, "grey1"); vline(im, x, 100, 137, "grey3")
    hline(im, 0, W - 1, 137, "ink")
    # ---- floodlight beams over the back layers
    for (hx, hy, dirx) in ((76, 62, 1), (240, 58, -1)):
        pts = [(hx + dirx * 6, hy + 4), (hx + dirx * 2, hy + 8), (hx + dirx * 70, 138), (hx + dirx * 8, 138)]
        cone(im, pts, "yellow2", 0.4, 4, only=["ink","blue0","purple0","red0","grey1","grey2","grey3"])

    # ---- safety signs on the hoarding
    rect(im, 12, 102, 52, 15, "green1", "ink")
    draw(im).rectangle([14, 104, 61, 114], outline=col("white"))
    text(im, 38, 105, "안전제일", "white", 9, align="center")
    rect(im, 135, 104, 52, 15, "yellow", "ink")
    for x in range(137, 185, 8):
        line(im, [(x, 118), (x + 4, 105)], "ink2")
    rect(im, 138, 106, 46, 11, "yellow")
    text(im, 161, 107, "낙하주의", "ink", 9, align="center")
    rect(im, 190, 104, 52, 15, "orange2", "ink")
    draw(im).rectangle([192, 106, 239, 116], outline=col("ink"))
    text(im, 216, 107, "추락주의", "ink", 9, align="center")
    # ---- mud ground
    dither_grad(im, (0, 138, W, 157), "brown1", "brown0", "y", 4, 0.0, 1.0)
    hline(im, 0, W - 1, 138, "ink")
    speckle(im, (0, 140, W, 157), "brown2", 150, 31)
    speckle(im, (0, 140, W, 157), "orange0", 110, 32)
    speckle(im, (0, 140, W, 157), "brown3", 40, 33)
    # tyre ruts
    for yy, c in ((146, "brown0"), (147, "brown0"), (154, "ink2")):
        for x in range(0, W):
            if (x // 5) % 3 != 2:
                px(im, x, yy, c)
    # puddles reflecting the floodlights
    for (cx, cy, rx, ry) in ((100, 153, 14, 2), (236, 152, 12, 2), (36, 154, 10, 1), (298, 154, 9, 1)):
        ellipse(im, cx - rx, cy - ry, cx + rx, cy + ry, "blue0", "ink2")
        dither_grad(im, (cx - rx + 1, cy - ry, cx + rx, cy + ry + 1), "blue0", "blue1", "x", 2, 0.0, 0.8)
        px(im, cx - 3, cy, "blue3"); px(im, cx + 2, cy, "blue3"); px(im, cx + 6, cy, "yellow2")
    pool(im, 150, 146, 70, 10, "orange3", 0.25, 4)
    # ---- brick / material pile (left)
    def brick_stack(x, y, w, h, c=("orange1", "orange0", "orange2")):
        base, joint, hi = c
        rect(im, x, y + h - 3, w, 3, "brown2", "ink")
        rect(im, x, y, w, h - 3, base, "ink")
        for r, yy in enumerate(range(y + 4, y + h - 3, 4)):
            hline(im, x + 1, x + w - 2, yy, joint)
        for r, yy in enumerate(range(y + 1, y + h - 3, 4)):
            off = 4 if r % 2 else 0
            for xx in range(x + 3 + off, x + w - 1, 8):
                vline(im, xx, yy, min(yy + 3, y + h - 5), joint)
        hline(im, x + 1, x + w - 2, y + 1, hi)
        ovl(im, (x + 1, y + 1, x + w - 1, y + h - 3), "orange0", 0.2, 2)
        dither_grad(im, (x + w - 8, y + 1, x + w - 1, y + h - 3), base, joint, "x", 2, 0.0, 0.6)
        # strap
        vline(im, x + w // 2, y, y + h - 4, "grey2")
    brick_stack(10, 128, 26, 22)
    brick_stack(38, 120, 22, 30)
    brick_stack(12, 120, 20, 8, ("orange2", "orange1", "orange3"))
    # cement bags
    for i, (bx, by) in enumerate(((58, 138), (60, 130), (62, 146 - 8 + 8))):
        pass
    for (bx, by) in ((57, 142), (62, 142), (59, 135)):
        rect(im, bx, by, 10, 8, "grey4", "ink")
        hline(im, bx + 1, bx + 8, by + 1, "white")
        rect(im, bx + 3, by + 3, 4, 2, "blue2")
        ovl(im, (bx + 6, by + 1, bx + 9, by + 7), "grey3", 0.6, 2)
    # blue tarp corner
    poly(im, [(10, 128), (22, 128), (30, 136), (10, 140)], "blue1", "ink")
    dither_grad(im, (11, 129, 28, 139), "blue1", "blue0", "d", 2, 0.0, 1.0, mk_mask([(10, 128), (22, 128), (30, 136), (10, 140)], im.size))
    ovl(im, (0, 148, 74, 154), "ink", 0.4, 2)
    # ---- site office container
    rect(im, 80, 86, 54, 64, "blue1", "ink")
    for x in range(81, 133, 3):
        vline(im, x, 90, 147, "blue1")
        vline(im, x + 1, 90, 147, "blue2")
        vline(im, x + 2, 90, 147, "blue0")
    dither_grad(im, (81, 87, 133, 149), "blue2", "blue0", "d", 2, 0.0, 1.0)
    for x in range(81, 133, 3):
        vline(im, x, 90, 147, "blue1")
    rect(im, 80, 86, 54, 4, "grey2", "ink")
    hline(im, 81, 132, 87, "grey4")
    rect(im, 80, 147, 54, 3, "grey1", "ink")
    for cx in (80, 130):
        rect(im, cx, 86, 4, 64, "grey1", "ink"); vline(im, cx + 1, 87, 148, "grey3")
    # roll-call board x 90..124 y 92..120 (blank)
    rect(im, 90, 92, 35, 29, "grey3", "ink")
    rect(im, 91, 93, 33, 27, "white")
    dither_grad(im, (92, 94, 123, 119), "white", "grey4", "d", 2, 0.0, 0.5)
    hline(im, 91, 123, 93, "grey4")
    rect(im, 92, 119, 31, 2, "grey2", "ink")
    rect(im, 96, 118, 6, 1, "red2"); rect(im, 104, 118, 5, 1, "blue2")
    px(im, 91, 93, "ink")
    # door + steps below board
    rect(im, 100, 126, 18, 21, "grey2", "ink")
    rect(im, 102, 128, 14, 8, "ink2", "ink")
    dither_grad(im, (103, 129, 115, 135), "orange4", "orange3", "y", 4, 0.0, 1.0)
    text(im, 109, 137, "사무소", "white", 9, align="center") if False else None
    rect(im, 100, 148, 18, 2, "grey1", "ink")
    rect(im, 113, 138, 3, 3, "grey4", "ink")
    # caged lamp above board
    rect(im, 104, 88, 12, 3, "grey1", "ink")
    glow(im, 94, 90, 128, 118, "yellow2", 0.25, 4, 8)
    # ---- formwork pit: a dark hole in the ground
    rect(im, 148, 139, 64, 18, "ink", "ink")
    dither_grad(im, (149, 140, 211, 157), "ink2", "ink", "y", 2, 0.0, 1.0)
    # far inner wall: shuttering planks fading into the dark
    for x in range(149, 211, 7):
        vline(im, x, 141, 146, "brown0")
    hline(im, 149, 210, 141, "brown1")
    ovl(im, (149, 141, 211, 147), "ink", 0.5, 2)
    # curb on the back rim + stakes + caution tape
    rect(im, 146, 138, 68, 2, "grey2", "ink")
    hline(im, 147, 212, 138, "grey3")
    for x in (150, 206):
        rect(im, x, 124, 3, 15, "brown1", "ink")
        vline(im, x + 1, 125, 137, "brown2")
    for x in range(153, 206):
        sag = int(2 * math.sin((x - 153) / 53 * math.pi))
        px(im, x, 126 + sag, "yellow" if (x // 3) % 2 else "ink")
    # rebar starter bars rising out of the hole
    rnd2 = random.Random(5)
    for x in range(154, 208, 4):
        top = rnd2.randint(112, 128)
        vline(im, x, top, 143, "orange1")
        vline(im, x + 1, top + 1, 143, "orange0")
        px(im, x, top, "orange3"); px(im, x, top + 1, "orange2")
    for yy in (122, 131):
        hline(im, 154, 206, yy, "grey2")
        for x in range(154, 207, 8):
            px(im, x, yy - 1, "grey3")
    # reinforcement mat deep in the hole
    for x in range(152, 210, 6):
        vline(im, x, 153, 156, "grey1")
    hline(im, 150, 209, 155, "grey1")
    # ---- steel floor plates + bridge across the pit
    def plate(x, y, w, h):
        rect(im, x, y, w, h, "grey2", "ink")
        hline(im, x + 1, x + w - 2, y + 1, "grey4")
        for xx in range(x + 3, x + w - 2, 4):
            px(im, xx, y + 3, "grey3"); px(im, xx + 2, y + 5, "grey3") if y + 5 < y + h - 1 else None
        px(im, x + 1, y + h - 2, "grey1"); px(im, x + w - 2, y + h - 2, "grey1")
        px(im, x + 1, y + 1, "white")
    plate(130, 143, 20, 11)
    plate(212, 143, 20, 11)
    plate(110, 150, 18, 6)
    # bridge: two plates joined at the middle, thick front edge
    for (bx, bw) in ((146, 34), (180, 34)):
        rect(im, bx, 147, bw, 4, "grey2", "ink")
        hline(im, bx + 1, bx + bw - 2, 148, "grey4")
        for xx in range(bx + 3, bx + bw - 2, 4):
            px(im, xx, 149, "grey3")
        rect(im, bx, 151, bw, 2, "grey1", "ink")
        px(im, bx + 1, 148, "white")
    # ---- orange barriers
    def barrier(x, y, w=16):
        for lx in (x + 1, x + w - 4):
            rect(im, lx, y + 9, 3, 4, "grey1", "ink")
        rect(im, x, y, w, 9, "white", "ink")
        for sx in range(x + 1, x + w - 2, 5):
            poly(im, [(sx, y + 8), (sx + 2, y + 1), (sx + 4, y + 1), (sx + 2, y + 8)], "orange2")
        hline(im, x + 1, x + w - 2, y + 1, "orange4")
        ovl(im, (x, y + 13, x + w, y + 15), "ink", 0.5, 2)
    barrier(130, 137)
    barrier(216, 137)
    barrier(240, 140, 14)
    # traffic cone
    poly(im, [(125, 150), (131, 150), (129, 140), (127, 140)], "orange2", "ink")
    hline(im, 127, 129, 144, "white")
    rect(im, 124, 150, 8, 2, "orange1", "ink")
    # ---- hoist: mast + cage (open state; door prop covers it)
    mx0, mx1 = 266, 286
    for k in range(Y0, 90, 8):
        line(im, [(mx0, k), (mx1, k + 8)], "grey1")
        line(im, [(mx1, k), (mx0, k + 8)], "grey1")
        hline(im, mx0, mx1, k, "grey2")
    for cx in (mx0 - 1, mx1 - 1):
        rect(im, cx, Y0, 4, 66, "grey1", "ink")
        vline(im, cx + 1, Y0, 86, "grey3")
    rect(im, 262, 52, 28, 3, "grey2", "ink")             # mast tie / guide collar
    rect(im, 264, 54, 4, 4, "orange2", "ink")
    rect(im, 284, 54, 4, 4, "orange2", "ink")
    # cage: interior + frame (open front)
    rect(im, 254, 86, 42, 64, "grey1", "ink")
    rect(im, 257, 91, 36, 54, "ink2", "ink")
    dither_grad(im, (258, 92, 292, 144), "grey1", "ink", "y", 4, 0.0, 1.0)
    for yy in (100, 110, 120, 130, 140):
        hline(im, 258, 292, yy, "ink2")
    rect(im, 254, 86, 42, 5, "grey2", "ink")
    hline(im, 255, 294, 87, "grey4")
    rect(im, 254, 143, 42, 7, "yellow", "ink")
    for x in range(256, 294, 6):
        poly(im, [(x, 149), (x + 3, 149), (x + 5, 144), (x + 2, 144)], "ink")
    # folded door stack on the right post
    rect(im, 289, 92, 4, 50, "grey3", "ink")
    for yy in range(94, 142, 4):
        px(im, 290, yy, "ink2"); px(im, 291, yy + 2, "ink2")
    # beacon above
    rect(im, 268, 82, 10, 4, "grey1", "ink")
    rect(im, 270, 79, 6, 4, "red2", "ink"); px(im, 271, 80, "red4")
    glow(im, 258, 70, 290, 92, "red3", 0.15, 4, 8)
    # hoist floor mark
    ovl(im, (250, 150, 300, 155), "ink", 0.5, 2)
    # ---- crane hook cable + block
    rect(im, 179, Y0 + 8, 3, 24, "grey1", "ink")
    vline(im, 180, Y0 + 8, 52, "grey3")
    rect(im, 174, 40, 14, 9, "yellow", "ink")
    rect(im, 175, 41, 12, 3, "yellow2")
    ellipse(im, 178, 42, 184, 48, "grey2", "ink")
    px(im, 181, 45, "ink")
    rect(im, 179, 49, 4, 3, "grey1", "ink")
    # hook curve
    for (x, y) in ((180, 52), (181, 53), (182, 54), (183, 55), (183, 56), (182, 57), (180, 58), (178, 58), (177, 57), (177, 56)):
        rect(im, x - 1, y - 1, 3, 3, "grey2")
    for (x, y) in ((180, 52), (181, 53), (182, 54), (183, 55), (183, 56), (182, 57), (180, 58), (178, 58), (177, 57), (177, 56)):
        px(im, x - 1, y - 1, "grey4")
    img2 = im.copy()
    # re-outline the hook region
    reg = new(W, H)
    for (x, y) in ((180, 52), (181, 53), (182, 54), (183, 55), (183, 56), (182, 57), (180, 58), (178, 58), (177, 57), (177, 56)):
        rect(reg, x - 1, y - 1, 3, 3, "grey2")
    reg = outline(reg)
    for yy in range(50, 62):
        for xx in range(174, 188):
            p = reg.getpixel((xx, yy))
            if p[3] and p[:3] == PAL["ink"]:
                if im.getpixel((xx, yy))[:3] != PAL["grey2"] and im.getpixel((xx, yy))[:3] != PAL["grey4"]:
                    px(im, xx, yy, "ink")
    # ---- floodlight poles (drawn on top of the beams)
    for (hx, hy, dirx) in ((76, 62, 1), (240, 58, -1)):
        rect(im, hx - 1, hy + 8, 3, 142 - hy - 8 + 0, "grey1", "ink") if False else None
    # pole A sits behind the container gap, B between pit and hoist: thin poles to the ground
    for (hx, hy, dirx) in ((76, 64, 1), (242, 62, -1)):
        rect(im, hx, hy + 6, 3, 150 - hy - 6, "grey1", "ink")
        vline(im, hx + 1, hy + 7, 148, "grey3")
        rect(im, hx - 3, 149, 9, 2, "grey1", "ink")
        # lamp head
        rect(im, hx - 5, hy - 2, 13, 8, "grey1", "ink")
        rect(im, hx - 4 + (6 if dirx > 0 else 0), hy - 1, 6, 6, "yellow2")
        px(im, hx - 4 + (6 if dirx > 0 else 0), hy - 1, "white")
        dither_radial(im, hx + dirx * 4, hy + 2, 12, "yellow2", None, 4)
        rect(im, hx - 5, hy - 2, 13, 8, None, "ink") if False else None
    for (hx, hy, dirx) in ((76, 64, 1), (242, 62, -1)):
        rect(im, hx - 5, hy - 2, 13, 2, "grey2")
        rect(im, hx - 4 + (6 if dirx > 0 else 0), hy, 6, 5, "white")
        rect(im, hx - 4 + (0 if dirx > 0 else 6), hy, 1, 5, "grey1") if False else None
    letterbox(im)
    return im


# ------------------------------------------------------------ site props
def mesh(w, h, x0, y0, c="grey3", bg_dark="ink"):
    """diamond wire mesh pattern writer used by the hoist door sprites"""
    return None


def hoist(rider):
    im = new(42, 64)
    rect(im, 0, 0, 42, 64, "grey1", "ink")
    # inner (cage interior seen through the mesh)
    rect(im, 3, 5, 36, 53, "ink2", "ink")
    dither_grad(im, (4, 6, 38, 57), "grey1", "ink", "y", 4, 0.0, 1.0)
    if rider:
        # dark standing figure behind the mesh
        fig = new(42, 64)
        ellipse(fig, 15, 12, 26, 24, "ink")                 # head
        rect(fig, 18, 23, 6, 4, "ink")                      # neck
        poly(fig, [(9, 29), (14, 26), (28, 26), (33, 29), (34, 58), (8, 58)], "ink")
        rect(fig, 11, 29, 3, 20, "ink"); rect(fig, 28, 29, 3, 20, "ink")
        im.alpha_composite(fig)
        # faint rim light on the shoulders
        hline(im, 14, 20, 27, "ink2")
    # wire mesh door
    for y in range(5, 58):
        for x in range(3, 39):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                if rider:
                    if im.getpixel((x, y))[:3] == PAL["ink"]:
                        px(im, x, y, "grey1")
                    else:
                        px(im, x, y, "grey3")
                else:
                    px(im, x, y, "grey3")
    # middle rail + door frame
    rect(im, 3, 29, 36, 3, "grey2", "ink")
    hline(im, 4, 37, 30, "grey4")
    rect(im, 0, 0, 42, 5, "grey2", "ink")
    hline(im, 1, 40, 1, "grey4")
    for x in range(3, 40, 8):
        px(im, x, 2, "ink2"); px(im, x + 1, 2, "ink2")
    rect(im, 0, 0, 4, 64, "grey1", "ink"); vline(im, 1, 1, 62, "grey3")
    rect(im, 38, 0, 4, 64, "grey1", "ink"); vline(im, 39, 5, 62, "grey2")
    # hazard footer
    rect(im, 0, 58, 42, 6, "yellow", "ink")
    for x in range(2, 40, 6):
        poly(im, [(x, 62), (x + 3, 62), (x + 5, 59), (x + 2, 59)], "ink")
    # latch + padlock
    rect(im, 33, 28, 6, 7, "grey4", "ink")
    rect(im, 35, 31, 2, 3, "yellow", "ink")
    px(im, 35, 29, "red2")
    # hinges
    for yy in (12, 46):
        rect(im, 3, yy, 3, 4, "grey4", "ink")
    if rider:
        # pale hands gripping the mesh
        for hx in (11, 27):
            rect(im, hx, 36, 5, 4, "pale2", "ink")
            for k in range(4):
                px(im, hx + k, 40, "pale2")
                px(im, hx + k, 41, "pale1") if k % 2 == 0 else None
            px(im, hx + 1, 37, "white")
    return im


def pipes_load():
    im = new(36, 24)
    # chain sling: ring on top, two legs
    ellipse(im, 14, 0, 21, 5, None, "grey3")
    px(im, 17, 0, "white")
    for (x0, y0, x1, y1) in ((16, 5, 4, 12), (19, 5, 31, 12)):
        n = 12
        for i in range(n + 1):
            t = i / n
            x = round(x0 + (x1 - x0) * t); y = round(y0 + (y1 - y0) * t)
            px(im, x, y, "grey3" if i % 2 == 0 else "grey1")
            if i % 2 == 0:
                px(im, x, y + 1, "ink")
    # pipe bundle
    rows = ((12, 5, 30), (16, 4, 31), (20, 5, 30))
    for (y, a, b) in rows:
        rect(im, a, y, b - a + 1, 4, "grey2", "ink")
        hline(im, a + 1, b - 1, y + 1, "grey4")
        hline(im, a + 1, b - 1, y + 3, "grey1")
        rect(im, a, y, 3, 4, "ink2", "ink")                 # dark pipe mouth
        px(im, a + 1, y + 1, "grey1")
    # rust speckle + straps
    speckle(im, (6, 12, 30, 23), "orange1", 9, 3, "grey2")
    for sx in (10, 25):
        rect(im, sx, 11, 2, 13, "grey1", "ink")
        px(im, sx, 12, "grey3")
    return im


def brick_sprite():
    im = new(12, 8)
    rect(im, 0, 0, 12, 8, "orange1", "ink")
    hline(im, 1, 10, 3, "orange0")
    hline(im, 1, 10, 5, "orange0")
    for x in (4, 8):
        vline(im, x, 1, 2, "orange0")
    for x in (2, 6, 10):
        vline(im, x, 4, 4, "orange0")
    vline(im, 6, 6, 6, "orange0")
    hline(im, 1, 10, 1, "orange2")
    px(im, 1, 4, "orange2"); px(im, 5, 4, "orange2")
    dither_grad(im, (7, 1, 11, 7), "orange1", "orange0", "x", 2, 0.0, 0.6)
    return im


# ----------------------------------------------------------------- foreman
def limb(layer, p0, p1, w, c):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = max(1.0, math.hypot(dx, dy))
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    poly(layer, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], c)
    ellipse(layer, x0 - w / 2 + 0.5, y0 - w / 2 + 0.5, x0 + w / 2 - 0.5, y0 + w / 2 - 0.5, c)
    ellipse(layer, x1 - w / 2 + 0.5, y1 - w / 2 + 0.5, x1 + w / 2 - 0.5, y1 + w / 2 - 0.5, c)


def fm_arm(sh, el, hd, shade=False, w=9):
    lay = new(48, 64)
    sleeve = "grey1" if shade else "grey2"
    skin = "skin0" if shade else "skin1"
    limb(lay, sh, el, w, sleeve)
    limb(lay, el, hd, w - 1, skin)
    # fist
    rect(lay, hd[0] - 3, hd[1] - 3, 7, 7, skin)
    if not shade:
        # girder highlight along the forearm
        line(lay, [(el[0] - 2, el[1] + 1), (hd[0] - 2, hd[1] - 2)], "skin2")
        px(lay, hd[0] - 2, hd[1] - 2, "skin2")
    out = outline(lay)
    return out


def foreman_head(hd, hx, hf, hatless=False):
    """Head centred (hx,hf). Upper half sits in deep hard-hat shadow with two dim red eyes;
    lower half is lit skin: cheek, jaw line, stubbly chin."""
    rect(hd, hx - 2, hf + 6, 11, 5, "skin0")                    # neck
    ellipse(hd, hx - 8, hf - 8, hx + 8, hf + 8, "brown0" if hatless else "ink2")   # skull / shadow
    t0 = hf - 2 if hatless else hf + 2
    # lit lower face: squared jaw
    poly(hd, [(hx - 8, t0), (hx + 8, t0), (hx + 8, hf + 5), (hx + 5, hf + 9),
              (hx - 5, hf + 9), (hx - 8, hf + 5)], "skin1")
    if not hatless:
        rect(hd, hx - 8, hf + 2, 17, 1, "ink2")                  # hat shadow edge
    # shade the right half of the face, light from top-left
    for y in range(t0 + 1, hf + 10):
        for x in range(hx + 2, hx + 9):
            if hd.getpixel((x, y))[:3] == PAL["skin1"]:
                if (x + y) % 2 == 0 or x > hx + 5:
                    px(hd, x, y, "skin0")
    # jaw line: dark rim under the cheekbone and along the chin
    line(hd, [(hx - 8, hf + 5), (hx - 5, hf + 9)], "skin0")
    line(hd, [(hx - 5, hf + 9), (hx + 5, hf + 9)], "skin0")
    # nose + mouth
    px(hd, hx - 3, hf + 4, "skin2"); px(hd, hx - 3, hf + 5, "skin2")
    line(hd, [(hx - 4, hf + 6), (hx + 1, hf + 6)], "red0")
    # stubble on chin/jaw (ordered dither, darker skin tone)
    for y in range(hf + 7, hf + 10):
        for x in range(hx - 6, hx + 7):
            if hd.getpixel((x, y))[:3] in (PAL["skin1"], PAL["skin0"]) and (x + y) % 2 == 0:
                px(hd, x, y, "brown0")
    # eyes: two dim red glints in the hat shadow
    for ex in (hx - 5, hx):
        if hatless:       # knocked out: X eyes
            for k in range(3):
                px(hd, ex + k, hf - 2 + k, "ink"); px(hd, ex + 2 - k, hf - 2 + k, "ink")
        else:
            px(hd, ex, hf, "red1"); px(hd, ex + 1, hf, "red2"); px(hd, ex, hf - 1, "red0")


def foreman_hurt():
    """Crushed: bent right over, head hanging, hat knocked askew, two pipes across the back."""
    S = new(48, 64)
    # buckled legs
    legs = new(48, 64)
    for x, c in ((26, "ink2"), (12, "grey1")):
        rect(legs, x, 50, 10, 6, c)
        rect(legs, x - 2, 55, 12, 4, c)
        rect(legs, x - 4, 58, 13, 5, "brown0")
        hline(legs, x - 4, x + 8, 61, "ink")
    S.alpha_composite(outline(legs))
    # hunched torso, shoulders low and forward (left), hips high behind
    t = new(48, 64)
    poly(t, [(5, 46), (12, 36), (30, 30), (41, 36), (40, 52), (12, 52)], "orange2")
    dither_grad(t, (24, 30, 42, 53), "orange2", "orange1", "x", 2, 0.0, 1.0,
                Image.composite(Image.new("L", t.size, 255), Image.new("L", t.size, 0), shade_mask(t)))
    for k in (40, 45):
        line(t, [(10, k + 1), (38, k - 8)], "yellow2")             # strips follow the bent back
    hline(t, 12, 40, 51, "ink2")
    S.alpha_composite(outline(t))
    # arms pressed to the floor
    for sh, el, hd, shade in (((12, 42), (6, 50), (5, 58), False), ((36, 44), (42, 52), (40, 58), True)):
        S.alpha_composite(fm_arm(sh, el, hd, shade, 8))
    # head hanging down in front of the chest, bruised
    hd = new(48, 64)
    foreman_head(hd, 17, 43, True)
    S.alpha_composite(outline(hd))
    # hat knocked off to the side, tipped over
    hat = new(48, 64)
    hx, hy = 8, 24
    ellipse(hat, hx - 9, hy - 9, hx + 9, hy + 3, "yellow")
    rect(hat, hx - 9, hy - 3, 19, 5, "yellow")
    dither_grad(hat, (hx, hy - 9, hx + 10, hy + 3), "yellow", "orange3", "x", 2, 0.0, 1.0)
    rect(hat, hx - 14, hy + 1, 24, 2, "orange3")
    hat = hat.rotate(-38, center=(hx, hy), resample=Image.NEAREST)
    # dent
    px(hat, 5, 19, "orange2"); px(hat, 6, 20, "orange2")
    S.alpha_composite(outline(hat))
    # two pipes across the back
    for (p0, p1) in (((14, 29), (45, 47)), ((20, 25), (45, 38))):
        pl = new(48, 64)
        line(pl, [p0, p1], "grey2", 5)
        line(pl, [(p0[0], p0[1] - 1), (p1[0], p1[1] - 1)], "grey4", 1)
        line(pl, [(p0[0], p0[1] + 2), (p1[0], p1[1] + 2)], "grey1", 1)
        ellipse(pl, p1[0] - 3, p1[1] - 3, p1[0] + 1, p1[1] + 2, "grey1")
        S.alpha_composite(outline(pl))
    # dust
    for p in ((3, 52), (2, 56), (44, 56), (46, 50), (30, 62)):
        px(S, *p, "grey3")
    return S


def foreman_frame(pose, f=0):
    if pose == "hurt":
        return foreman_hurt()
    S = new(48, 64)
    dy = 0; tx = 0
    leg_n = 14; leg_f = 25     # x of far/near leg left edge
    kneel = 0
    boots_dy = 0
    if pose == "idle":
        dy = 1 if f == 1 else 0
    elif pose == "walk":
        dy = 1 if f == 1 else 0
        leg_n, leg_f = (11, 28) if f == 0 else (19, 20)
    elif pose == "wind":
        tx = 0; dy = 8; leg_n, leg_f = 15, 27
    elif pose == "slam":
        tx = -3; dy = 3; leg_n, leg_f = 12, 27
    elif pose == "hurt":
        dy = 9; tx = -1

    # ---- legs
    legs = new(48, 64)
    def leg(x, bent=False, shade=False):
        c, s = ("grey1", "ink2") if not shade else ("ink2", "ink")
        if bent:
            rect(legs, x, 48 + dy - 3, 10, 6, c)          # thigh
            rect(legs, x - 3, 53, 9, 6, c)                # shin forward
            rect(legs, x - 6, 58, 13, 5, "brown0")        # boot
            hline(legs, x - 6, x + 6, 61, "ink")
        else:
            rect(legs, x, 42 + dy, 10, 17 - dy, c)
            vline(legs, x + 9, 42 + dy, 58, s)
            rect(legs, x - 3, 58, 13, 5, "brown0")
            rect(legs, x - 3, 58, 13, 1, "brown1")
            rect(legs, x - 3, 62, 13, 1, "ink")
    if pose == "hurt":
        leg(24, True, True); leg(10, True)
        # buckled knees
        px(legs, 14, 53, "grey2")
    else:
        leg(leg_f, shade=True); leg(leg_n)
    S.alpha_composite(outline(legs))

    # ---- far arm (behind torso)
    if pose == "idle" or pose == "walk":
        sw = (-2 if f == 1 else 2) if pose == "walk" else 0
        S.alpha_composite(fm_arm((35 + tx, 29 + dy), (37 + tx + sw, 40 + dy), (37 + tx + 2 * sw, 50 + dy), True))
    elif pose == "slam":
        S.alpha_composite(fm_arm((30 + tx, 33 + dy), (24 + tx, 40 + dy), (16 + tx, 46), True))
    # ---- hammer behind the body in wind (head up behind head)
    # ---- torso
    t = new(48, 64)
    top = 25 + dy
    if pose == "hurt":
        top = 36
    poly(t, [(10 + tx, top + 2), (14 + tx, top), (34 + tx, top), (39 + tx, top + 3),
             (36 + tx, 44 + dy), (13 + tx, 44 + dy)], "orange2")
    if pose == "hurt":
        poly(t, [(10 + tx, top + 2), (14 + tx, top), (34 + tx, top), (39 + tx, top + 3),
                 (36 + tx, 51), (13 + tx, 51)], "orange2")
    bot = 44 + dy if pose != "hurt" else 51
    # shade right side
    dither_grad(t, (28 + tx, top, 40 + tx, bot + 1), "orange2", "orange1", "x", 2, 0.0, 1.0, shade_mask(t).crop((0, 0, 48, 64)) if False else None)
    # restrict dither to the torso by masking on the later outline step
    # reflective strips
    for yy in ((top + 7, top + 8), (top + 13, top + 14)):
        for y in yy:
            if y < bot - 1:
                hline(t, 12 + tx, 36 + tx, y, "yellow2")
    # front opening seam + belt
    vline(t, 17 + tx, top + 2, bot - 3, "orange1")
    hline(t, 13 + tx, 36 + tx, bot - 1, "ink2")
    hline(t, 13 + tx, 36 + tx, bot, "ink2")
    px(t, 18 + tx, bot - 1, "yellow")
    # clip to torso silhouette
    sil = Image.new("L", t.size, 0)
    ImageDraw.Draw(sil).polygon([(10 + tx, top + 2), (14 + tx, top), (34 + tx, top), (39 + tx, top + 3),
                                 (36 + tx, bot), (13 + tx, bot)], fill=255)
    a = t.split()[3].point(lambda v: v)
    t.putalpha(Image.composite(a, Image.new("L", t.size, 0), sil))
    S.alpha_composite(outline(t))

    # ---- neck + head + hat
    hx = 22 + tx
    hy = 14 + dy
    if pose == "slam":
        hx -= 1; hy += 2
    if pose == "hurt":
        hx = 21 + tx; hy = 31
    hd = new(48, 64)
    foreman_head(hd, hx, hy + 5)
    S.alpha_composite(outline(hd))
    hat = new(48, 64)
    ellipse(hat, hx - 10, hy - 14, hx + 10, hy + 2, "yellow")
    rect(hat, hx - 10, hy - 6, 21, 8, "yellow")
    dither_grad(hat, (hx, hy - 14, hx + 11, hy + 3), "yellow", "orange3", "x", 2, 0.0, 1.0)
    rect(hat, hx - 4, hy - 14, 9, 3, "orange3")                 # ridge
    px(hat, hx - 6, hy - 10, "yellow2"); px(hat, hx - 5, hy - 11, "yellow2"); px(hat, hx - 6, hy - 9, "yellow2")
    rect(hat, hx - 15, hy, 27, 3, "yellow")                      # brim juts forward (left)
    rect(hat, hx - 15, hy + 2, 27, 1, "orange3")
    S.alpha_composite(outline(hat))
    # ---- lanyard + blank id card (agency)
    if True:
        ly = 26 + dy
        line(S, [(hx - 2, ly), (hx - 7 if pose != "slam" else hx - 6, ly + 6)], "green1")
        line(S, [(hx + 3, ly), (hx - 4, ly + 6)], "green0")
        cx0 = 12 + tx + (0 if pose != "slam" else 1)
        rect(S, cx0, ly + 6, 6, 8, "white", "ink")
        px(S, cx0 + 2, ly + 5, "grey3")
        hline(S, cx0 + 1, cx0 + 4, ly + 7, "grey4")
    # ---- near arm
    if pose == "idle":
        S.alpha_composite(fm_arm((16 + tx, 29 + dy), (14 + tx, 40 + dy), (13 + tx, 51 + dy)))
    elif pose == "walk":
        sw = 2 if f == 1 else -2
        S.alpha_composite(fm_arm((16 + tx, 29 + dy), (14 + tx + sw, 40 + dy), (13 + tx + 2 * sw, 50 + dy)))
    elif pose == "slam":
        S.alpha_composite(fm_arm((16 + tx, 34 + dy), (12 + tx, 44 + dy), (12 + tx, 50)))

    # ---- sledgehammer raised high above the head
    if pose == "wind":
        hm = new(48, 64)
        rect(hm, 34, 6, 4, 30, "brown2")
        vline(hm, 37, 6, 35, "brown1")
        S.alpha_composite(outline(hm))
        hh = new(48, 64)
        rect(hh, 27, 0, 16, 9, "grey2")
        rect(hh, 27, 0, 16, 2, "grey4")
        rect(hh, 27, 7, 16, 2, "grey1")
        rect(hh, 27, 0, 3, 9, "grey1")                    # striking face
        rect(hh, 40, 0, 3, 9, "grey1")
        vline(hh, 28, 1, 7, "grey3"); vline(hh, 41, 1, 7, "grey3")
        S.alpha_composite(outline(hh))
        S.alpha_composite(fm_arm((38, 38), (40, 30), (36, 24), True, 8))
        S.alpha_composite(fm_arm((16, 39), (27, 36), (35, 31), False, 8))
    elif pose == "slam":
        # dust burst
        for (cx, cy, r) in ((4, 58, 6), (13, 60, 5), (20, 61, 4)):
            for y in range(cy - r, cy + r + 1):
                for x in range(cx - r, cx + r + 1):
                    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r
                    if d <= 1 and 0 <= x < 48 and 0 <= y < 64 and (1 - d) * 1.2 > _thr(x, y, 2):
                        px(S, x, y, "grey4" if d < 0.6 else "grey3")
        for p in ((1, 49), (5, 47), (9, 50), (16, 52), (2, 52)):
            px(S, *p, "grey3")
        hm = new(48, 64)
        line(hm, [(14 + tx, 40), (7, 56)], "brown2", 3)
        S.alpha_composite(outline(hm))
        hh = new(48, 64)
        rect(hh, 0, 54, 13, 8, "grey2")
        rect(hh, 0, 54, 13, 2, "grey4")
        rect(hh, 0, 60, 13, 2, "grey1")
        S.alpha_composite(outline(hh))
        S.alpha_composite(fm_arm((16 + tx, 34 + dy), (12 + tx, 44 + dy), (12 + tx, 50)))
    return S


def foreman_frames():
    names = ["idle_0", "idle_1", "walk_0", "walk_1", "wind_0", "slam_0", "hurt_0"]
    fr = [foreman_frame("idle", 0), foreman_frame("idle", 1), foreman_frame("walk", 0), foreman_frame("walk", 1),
          foreman_frame("wind"), foreman_frame("slam"), foreman_frame("hurt")]
    return fr, names


# ------------------------------------------------------------------ main
def main():
    ward = build_ward()
    assert not off_palette(ward)
    save(ward, "bg/ward.png")
    site = build_site()
    assert not off_palette(site)
    save(site, "bg/site.png")

    fr, nm = nurse_frames(True)
    sheet(fr, "props/nurse", nm, cols=6)
    fr, nm = nurse_frames(False)
    sheet(fr, "props/nurse_notag", nm, cols=6)
    fr, nm = subject_frames()
    sheet(fr, "props/subject", nm, cols=5)
    sheet([pill("blue2", "blue4", "blue3"), pill("red2", "red4", "red3")], "props/pill", ["blue_0", "red_0"], cols=2)
    fr, nm = foreman_frames()
    sheet(fr, "props/foreman", nm, cols=4)
    for name, im in (("hoist_closed", hoist(False)), ("hoist_rider", hoist(True)),
                     ("load", pipes_load()), ("brick", brick_sprite())):
        assert not off_palette(im), name
        save(im, f"props/{name}.png")
    contact(["bg/ward.png", "bg/site.png", "props/nurse.png", "props/nurse_notag.png", "props/subject.png",
             "props/pill.png", "props/foreman.png", "props/hoist_closed.png", "props/hoist_rider.png",
             "props/load.png", "props/brick.png"], "_contact/ward_site.png", cols=4, scale=2)
    print("done")


if __name__ == "__main__":
    main()

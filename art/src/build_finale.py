"""Act 7 finale assets for ONE MORE SHIFT.

Run:  python3 src/build_finale.py
Writes assets/bg/{park,ending_dawn,ending_desk,ending_note}.png
       assets/props/{float,kwak_boss}.png/.json, props/note.png
       assets/characters/junho.png/.json
       previews/_contact/finale.png
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
from pxkit import *
from pxkit import _thr
from PIL import Image, ImageDraw
from chibi import chibi, FW, FH
from build_characters import CAST
from build_delivery import glow, ovl, obox, hline, vline, speckle, floor_band
from build_event import pool, emask, egg
import build_bg_interior as BI

Y0 = 22


def cmask(size, shapes):
    """'L' mask: union of ('e', box) ellipses and ('p', pts) polygons."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for k, g in shapes:
        if k == "e":
            d.ellipse(g, fill=255)
        elif k == "p":
            d.polygon(g, fill=255)
        elif k == "r":
            d.rectangle(g, fill=255)
    return m


def sub_mask(a, b):
    out = Image.new("L", a.size, 0)
    pa, pb, po = a.load(), b.load(), out.load()
    for y in range(a.height):
        for x in range(a.width):
            po[x, y] = 255 if pa[x, y] and not pb[x, y] else 0
    return out


def fill_mask(img, mask, c):
    cc = col(c)
    p = mask.load()
    for y in range(mask.height):
        for x in range(mask.width):
            if p[x, y]:
                img.putpixel((x, y), cc)


def catenary(img, p0, p1, sag, n, lit, seed, dead="grey1", dead_p=0.4, wire="ink", glowc=None):
    """Sagging string of bulbs. lit = list of palette names; some bulbs dead."""
    rnd = random.Random(seed)
    x0, y0 = p0
    x1, y1 = p1
    steps = max(abs(x1 - x0), 1)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        pts.append((int(round(x)), int(round(y))))
    for p in pts:
        px(img, p[0], p[1], wire)
    for k in range(1, n):
        i = int(len(pts) * k / n)
        bx, by = pts[min(i, len(pts) - 1)]
        if rnd.random() < dead_p:
            rect(img, bx, by + 1, 2, 2, dead)
            px(img, bx, by + 1, "grey2")
        else:
            c = rnd.choice(lit)
            if glowc:
                dither_radial(img, bx, by + 2, 6, glowc, None, 4)
            rect(img, bx, by + 1, 2, 2, c)
            px(img, bx, by + 1, "white")


# ======================================================================
#  CHARACTERS: 준호
# ======================================================================
JUNHO = dict(name_ko="준호", role="npc", hair_style="messy", hair=("purple0", "purple1"),
             skin=("skin3", "grey3"), top=("grey3", "grey2"), outfit="vest",
             vest=("green1", "green0"), pants=("grey1", "ink2"), shoes="grey4", expr="tired")


def frost(img, seed=1):
    """faint frost tint: dithered pale blue on the skin + a few rime pixels on hair and vest."""
    sk = col("skin3")
    for y in range(img.height):
        for x in range(img.width):
            if img.getpixel((x, y)) == sk and 0.07 > _thr(x + 1, y, 4):
                img.putpixel((x, y), col("blue4"))
    rnd = random.Random(seed)
    for c, cc, n in (("purple1", "blue3", 3), ("green1", "green3", 2)):
        pts = [(x, y) for y in range(img.height) for x in range(img.width) if img.getpixel((x, y)) == col(c)]
        for (x, y) in rnd.sample(pts, min(n, len(pts))):
            px(img, x, y, cc)
    return img


def junho_decor(f, side=False):
    """worn vest tear + hood collar, drawn over the rig output."""
    if not side:
        rect(f, 11, 24, 10, 2, "grey2")                 # hood collar
        hline(f, 11, 20, 26, "ink2")
        px(f, 11, 34, "green0"); px(f, 12, 33, "green0")     # frayed hem
        px(f, 19, 30, "green0"); px(f, 20, 30, "green0")
        px(f, 12, 28, "yellow2")                             # name-tag blip
    else:
        rect(f, 15, 24, 6, 1, "grey2")
        px(f, 17, 31, "green0"); px(f, 18, 31, "green0")
    return f


def junho_frame(dirn, pose, i):
    f = chibi(JUNHO, dirn, pose, i, "tired")
    junho_decor(f, dirn == "side")
    return frost(f, 3 + i)


def junho_sit():
    s = JUNHO
    out = new(FW, FH)
    tc, ts = s["top"]; vc, vs = s["vest"]; pc, ps = s["pants"]
    t = new(FW, FH)                                   # shoulders / back
    rect(t, 8, 31, 16, 9, tc); rect(t, 22, 31, 2, 9, ts)
    rect(t, 8, 32, 4, 8, vc); rect(t, 20, 32, 4, 8, vc); rect(t, 22, 32, 2, 8, vs)
    out.alpha_composite(outline(t))
    l = new(FW, FH)                                   # raised knees + shoes
    rect(l, 7, 37, 18, 8, pc); rect(l, 7, 43, 18, 2, ps); rect(l, 15, 37, 1, 7, ps)
    rect(l, 5, 44, 7, 2, s["shoes"]); rect(l, 20, 44, 7, 2, s["shoes"])
    out.alpha_composite(outline(l))
    a = new(FW, FH)                                   # arms hugging the shins
    rect(a, 5, 38, 22, 3, tc); rect(a, 5, 40, 22, 1, ts)
    rect(a, 3, 38, 3, 3, "skin3"); rect(a, 26, 38, 3, 3, "skin3")
    out.alpha_composite(outline(a))
    h = new(FW, FH)                                   # head tipped down toward the knees
    h.alpha_composite(chibi(s, "down", "idle", 0, "tired").crop((0, 0, FW, 24)), (0, 10))
    out.alpha_composite(h)
    return frost(out, 9)


def build_junho():
    frames, names = [], []
    def add(n, im):
        names.append(n); frames.append(im)
    for i in range(2): add(f"down_idle_{i}", junho_frame("down", "idle", i))
    for i in range(4): add(f"left_walk_{i}", junho_frame("side", "walk", i))
    for i in range(4): add(f"right_walk_{i}", flip(junho_frame("side", "walk", i)))
    add("sit_0", junho_sit())
    sheet(frames, "characters/junho", names, cols=8)
    return frames


# ======================================================================
#  PROPS: note, float, kwak_boss
# ======================================================================
def build_note():
    im = new(10, 10)
    rect(im, 1, 1, 8, 8, "wall1", "ink")
    # folded corner (top right) + fold crease
    poly(im, [(6, 1), (8, 1), (8, 3)], "grey4", "ink")
    px(im, 6, 1, "ink"); px(im, 7, 2, "ink"); px(im, 8, 1, "ink")
    line(im, [(2, 5), (7, 5)], "grey3")                 # centre fold
    # tiny scribble
    for p in ((2, 3), (3, 2), (4, 3), (5, 2)):
        px(im, *p, "ink2")
    for p in ((2, 7), (3, 6), (4, 7), (5, 6), (6, 7)):
        px(im, *p, "red2")
    return im


def float_frame(state, blink):
    wrong = state == "wrong"
    im = new(96, 64)
    cx, cy, R = 36, 27, 25
    icx, icy, iR = 50, 22, 19
    outer = cmask((96, 64), [("e", (cx - R, cy - R, cx + R, cy + R))])
    inner = cmask((96, 64), [("e", (icx - iR, icy - iR, icx + iR, icy + iR))])
    moon = sub_mask(outer, inner)
    # --- moon mounting arm behind the cart
    rect(im, 10, 44, 54, 6, "grey2", "ink")
    # --- moon body: base + dithered shadow on the right/bottom, highlight top-left
    body = new(96, 64)
    fill_mask(body, moon, "yellow2")
    dither_grad(body, (0, 0, 96, 64), "yellow2", "orange3", "d", 4, -0.35, 1.15, moon)
    # thicker rim shadow near the inner curve
    for y in range(64):
        for x in range(96):
            if moon.getpixel((x, y)):
                d = ((x - icx) ** 2 + (y - icy) ** 2) ** 0.5 - iR
                if d < 2.5 and 0.5 > _thr(x, y, 2):
                    body.putpixel((x, y), col("orange3"))
    # craters
    for (x, y, r) in ((16, 13, 1), (28, 7, 1), (19, 38, 2), (27, 45, 1), (14, 24, 1)):
        px(body, x, y, "orange3"); px(body, x + 1, y, "orange3")
        if r > 1:
            px(body, x, y + 1, "orange3")
    for p in ((17, 8), (18, 8), (13, 17), (13, 18), (22, 4)):
        px(body, *p, "white")
    im.alpha_composite(outline(body))
    # --- face
    if not wrong:
        for p in ((19, 19), (20, 18), (21, 18), (22, 18), (23, 18), (24, 19)):
            px(im, *p, "ink")
        px(im, 18, 20, "ink"); px(im, 25, 20, "ink")
        for p in ((17, 25), (18, 25), (19, 25), (17, 26), (18, 26)):
            px(im, *p, "red4")
        for p in ((18, 31), (19, 32), (20, 33), (21, 33), (22, 33), (23, 33), (24, 32), (25, 31)):
            px(im, *p, "ink")
        px(im, 17, 30, "ink"); px(im, 26, 30, "ink")
    else:
        # black eye with a thin red ring
        ellipse(im, 18, 14, 25, 24, "ink", "ink")
        px(im, 23, 17, "red3")
        px(im, 17, 22, "red2"); px(im, 26, 22, "red2")
        # a gash: the smile splits the moon open from edge to edge
        gash = [(14, 31), (22, 27), (32, 25), (36, 34), (28, 40), (18, 39)]
        poly(im, gash, "ink", "ink")
        # red throat
        poly(im, [(18, 34), (24, 31), (31, 30), (33, 34), (27, 37), (20, 37)], "red0")
        # teeth, top and bottom rows
        for (x, y) in ((19, 31), (22, 29), (25, 28), (28, 27), (31, 27)):
            poly(im, [(x, y), (x + 2, y - 1), (x + 2, y + 2)], "white")
        for (x, y) in ((21, 38), (24, 38), (27, 37), (30, 35)):
            poly(im, [(x, y), (x + 2, y + 1), (x + 3, y - 2)], "white")
    # --- bulbs along both edges (blink between frames)
    on = ("red3", "red2") if wrong else ("yellow", "orange3")
    off = ("red0", "red1") if wrong else ("orange1", "orange0")
    k = 0
    for a in range(-80, 262, 17):
        ang = math.radians(a)
        bx = int(round(cx + (R + 1) * math.cos(ang))); by = int(round(cy + (R + 1) * math.sin(ang)))
        if ((bx - icx) ** 2 + (by - icy) ** 2) ** 0.5 > iR + 1.5:
            lit = (k + blink) % 2 == 0
            rect(im, bx - 1, by - 1, 3, 3, on[0] if lit else off[0], "ink")
            if lit:
                px(im, bx - 1, by - 1, "white" if not wrong else "red4")
            else:
                px(im, bx, by, off[1])
        k += 1
    k = 1
    for a in range(-62, 63, 22):
        ang = math.radians(a)
        bx = int(round(icx - (iR + 1) * math.cos(ang) * 1.0)); by = int(round(icy + (iR + 1) * math.sin(ang)))
        lit = (k + blink) % 2 == 0
        rect(im, bx - 1, by - 1, 3, 3, on[0] if lit else off[0], "ink")
        if lit:
            px(im, bx - 1, by - 1, "white" if not wrong else "red4")
        k += 1
    # --- cart
    bc, bs = ("purple1", "purple0")
    rect(im, 4, 48, 88, 11, bc, "ink")
    dither_grad(im, (5, 49, 91, 58), bc, bs, "y", 4, 0.0, 0.9)
    rect(im, 3, 46, 90, 3, "orange2" if not wrong else "red2", "ink")
    hline(im, 4, 91, 47, "orange3" if not wrong else "red3")
    for x in range(8, 90, 9):                                 # skirt tassels
        rect(im, x, 54, 5, 5, "red2" if (x // 9 + blink) % 2 else "yellow", "ink") if False else None
    for i, x in enumerate(range(7, 88, 10)):                  # lamp row on the cart front
        lit = (i + blink) % 2 == 0
        c1 = ("red3" if wrong else "yellow") if lit else ("red1" if wrong else "orange1")
        rect(im, x, 51, 3, 3, c1, "ink")
        if lit:
            px(im, x, 51, "red4" if wrong else "white")
    hline(im, 5, 90, 57, "ink2")
    # drawbar + hitch on the left
    rect(im, 0, 55, 5, 3, "grey2", "ink")
    # wheels
    for wx in (14, 36, 62, 82):
        ellipse(im, wx - 4, 58, wx + 4, 63, "ink2", "ink")
        ellipse(im, wx - 2, 59, wx + 2, 62, "grey2", "ink")
        px(im, wx, 60, "ink")
    # --- little star pole on the cart (right side)
    px_x = 79
    rect(im, px_x, 26, 2, 22, "grey3", "ink")
    sc = "red3" if wrong else ("yellow" if blink == 0 else "yellow2")
    star = [(px_x + 1, 14), (px_x + 3, 19), (px_x + 8, 19), (px_x + 4, 22), (px_x + 6, 27),
            (px_x + 1, 24), (px_x - 4, 27), (px_x - 2, 22), (px_x - 6, 19), (px_x - 1, 19)]
    poly(im, star, sc, "ink")
    if not wrong:
        px(im, px_x + 1, 18, "white")
    # ribbon streamer
    for i in range(10):
        px(im, px_x + 2 + i, 34 + int(math.sin(i * 0.9 + blink * 1.6) * 2), "red2" if not wrong else "red1")
    return im


def build_float():
    frames = [float_frame("ok", 0), float_frame("ok", 1), float_frame("wrong", 0)]
    sheet(frames, "props/float", ["f_0", "f_1", "f_wrong_0"], cols=3)
    return frames


# ---- 곽 실장, final form -------------------------------------------------
SKIN = ("skin2", "skin1")


def limb(layer, pts, c="green0", w=2):
    for a, b in zip(pts, pts[1:]):
        line(layer, [a, b], c, w)


def paper(img, cx, by, w=10, h=12, tilt=0, stamp=True, c="white"):
    """sheet of paper: bottom centre at (cx, by); tilt shears the top by `tilt` px."""
    x0 = cx - w // 2
    y0 = by - h
    pts = [(x0 + tilt, y0), (x0 + w - 1 + tilt, y0), (x0 + w - 1, by), (x0, by)]
    poly(img, pts, c, "ink")
    for k in range(3):
        yy = y0 + 3 + k * 2
        xa = x0 + 2 + int(tilt * (by - yy) / h * 0 + tilt * (1 - (yy - y0) / h))
        line(img, [(xa, yy), (xa + w - 6, yy)], "grey2")
    if stamp:
        rect(img, x0 + w - 5 + tilt // 2, y0 + h - 4, 3, 2, "red2")
    px(img, x0 + 1 + tilt, y0 + 1, "grey4") if False else None
    return img


def kwak_frame(pose, f=0):
    S = pose
    im = new(64, 64)
    bob = S.get("bob", 0)
    lean = S.get("lean", 0)
    hdy = S.get("hdy", 0)
    top = 18 + bob            # shoulder line
    # ---- extra arms (behind torso)
    back = new(64, 64)
    sheets = []
    shoulders = [(26 + lean, top + 4), (38 + lean, top + 4), (27 + lean, top + 13), (37 + lean, top + 13)]
    for (S0, (hx, hy)) in zip(shoulders, S["hands"]):
        ex = (S0[0] + hx) // 2
        ey = (S0[1] + hy) // 2 + S.get("sag", 3)
        limb(back, [S0, (ex, ey), (hx, hy)])
        sheets.append((hx, hy))
    im.alpha_composite(outline(back))
    for (hx, hy) in sheets:
        hand = new(64, 64)
        rect(hand, hx - 1, hy - 1, 3, 3, SKIN[0])
        im.alpha_composite(outline(hand))
    # ---- legs
    legs = new(64, 64)
    sp = S.get("legspread", 0)
    for (lx, sx) in ((27 - sp, -1), (35 + sp, 1)):
        rect(legs, lx, 47 + bob // 2, 3, 14 - bob // 2, "green0")
        rect(legs, lx + (2 if sx < 0 else 0), 47, 1, 14, "ink2") if False else None
        rect(legs, lx - 1 + (0 if sx < 0 else 1) - (1 if sx > 0 else 0), 61, 5 if sx > 0 else 5, 2, "brown0")
    im.alpha_composite(outline(legs))
    # ---- torso: skewed by lean (top shifted, bottom planted)
    t = new(64, 64)
    poly(t, [(25 + lean, top), (39 + lean, top), (37, 49), (27, 49)], "green0")
    poly(t, [(36 + lean, top), (39 + lean, top), (37, 49), (35, 49)], "ink2")
    # shirt + tie
    poly(t, [(30 + lean, top), (34 + lean, top), (32 + lean // 2, top + 8), (32 + lean // 2, top + 8)], "white")
    line(t, [(32 + lean, top + 1), (32 + lean // 2, top + 10)], "yellow", 2)
    px(t, 32 + lean // 2, top + 11, "yellow"); px(t, 31 + lean // 2, top + 11, "yellow")
    line(t, [(29 + lean, top), (31 + lean // 2, top + 8)], "ink2")
    line(t, [(35 + lean, top), (33 + lean // 2, top + 8)], "ink2")
    px(t, 32 + lean // 2 + 3, top + 20, "yellow2")                # tie pin / button
    px(t, 32 + lean // 2, top + 18, "ink2"); px(t, 32 + lean // 2, top + 23, "ink2")
    im.alpha_composite(outline(t))
    # ---- normal arms hanging at the sides
    arms = new(64, 64)
    swing = S.get("armswing", 0)
    limb(arms, [(25 + lean, top + 2), (23 + lean // 2 - swing, top + 14), (22 + lean // 3 - swing, top + 25)], "green0")
    limb(arms, [(39 + lean, top + 2), (41 + lean // 2 + swing, top + 14), (42 + lean // 3 + swing, top + 25)], "green0")
    rect(arms, 21 + lean // 3 - swing, top + 26, 3, 3, SKIN[0])
    rect(arms, 41 + lean // 3 + swing, top + 26, 3, 3, SKIN[0])
    im.alpha_composite(outline(arms))
    # ---- sheets over the hands
    for (hx, hy), (tilt, sc) in zip(sheets, S["tilts"]):
        paper(im, hx, hy - 1, tilt=tilt)
    # ---- neck + head
    hx0 = 32 + lean + S.get("hshift", 0)
    hy0 = 3 + bob + hdy
    head = new(64, 64)
    rect(head, hx0 - 2, hy0 + 14, 4, 5, SKIN[1])
    ellipse(head, hx0 - 8, hy0, hx0 + 8, hy0 + 17, SKIN[0])
    # slicked grey hair
    hair = new(64, 64)
    ellipse(hair, hx0 - 8, hy0 - 1, hx0 + 8, hy0 + 14, "grey1")
    draw(hair).rectangle([0, hy0 + 5, 63, 63], fill=(0, 0, 0, 0))
    head.alpha_composite(hair)
    rect(head, hx0 - 8, hy0 + 5, 2, 4, "grey1"); rect(head, hx0 + 7, hy0 + 5, 2, 4, "grey1")
    line(head, [(hx0 - 4, hy0 + 1), (hx0 + 3, hy0 + 1)], "grey3")
    line(head, [(hx0 - 6, hy0 + 3), (hx0 - 2, hy0 + 3)], "grey3")
    im.alpha_composite(outline(head))
    # face
    ey = hy0 + 9
    lens = "grey4"
    crack = S.get("crack", False)
    for (lx0) in (hx0 - 7, hx0 + 2):
        rect(im, lx0, ey - 2, 6, 5, lens, "ink2")
    line(im, [(hx0 - 1, ey), (hx0 + 1, ey)], "ink2")
    if S.get("squint"):
        for lx0 in (hx0 - 6, hx0 + 3):
            line(im, [(lx0, ey - 1), (lx0 + 3, ey)], "ink"); line(im, [(lx0 + 3, ey - 1 + 2), (lx0, ey + 1)], "ink") if False else None
            px(im, lx0 + 1, ey + 1, "ink"); px(im, lx0 + 2, ey + 1, "ink")
    else:
        for lx0 in (hx0 - 6, hx0 + 3):
            rect(im, lx0 + 1, ey - 1, 2, 3, "ink")
    # glint
    gx = [hx0 - 6, hx0 + 3][f % 2] if not S.get("noglint") else None
    if gx is not None:
        px(im, gx, ey - 2 + 0, "white"); px(im, gx + 1, ey - 2, "white"); px(im, gx, ey - 1, "white")
        px(im, [hx0 + 3, hx0 - 6][f % 2] + 4, ey + 1, "white")
    if crack:
        line(im, [(hx0 - 7, ey - 2), (hx0 - 2, ey + 2)], "ink")
        line(im, [(hx0 - 5, ey + 2), (hx0 - 4, ey - 2)], "ink2") if False else None
        line(im, [(hx0 + 7, ey - 2), (hx0 + 3, ey + 2)], "ink")
        px(im, hx0 - 4, ey, "blue3"); px(im, hx0 + 5, ey + 1, "blue3")
    # mouth
    my = ey + 5
    if S.get("grimace"):
        rect(im, hx0 - 3, my - 1, 7, 3, "red0", "ink")
        px(im, hx0 - 2, my - 1, "white"); px(im, hx0, my - 1, "white"); px(im, hx0 + 2, my - 1, "white")
    elif S.get("grin"):
        line(im, [(hx0 - 4, my), (hx0 + 4, my)], "ink")
        px(im, hx0 - 5, my - 1, "ink"); px(im, hx0 + 5, my - 1, "ink")
        for k in range(-3, 4, 2):
            px(im, hx0 + k, my + 1, "white")
    else:
        line(im, [(hx0 - 3, my), (hx0 + 3, my)], "ink")
        px(im, hx0 - 4, my - 1, "ink"); px(im, hx0 + 4, my - 1, "ink")
    return im


def hands_set(spread=1.0, up=0, drop=0):
    return None


KW_POSES = {
    "idle_0": dict(hands=[(10, 17), (54, 17), (8, 36), (56, 36)], tilts=[(0, 0)] * 4, f=0),
    "idle_1": dict(hands=[(11, 15), (53, 15), (9, 34), (55, 34)], tilts=[(1, 0), (-1, 0), (0, 0), (0, 0)], bob=1, f=1),
    "tell_0": dict(hands=[(14, 13), (50, 13), (7, 21), (57, 21)], tilts=[(-1, 0), (1, 0), (-2, 0), (2, 0)],
                   lean=-1, hdy=-1, sag=-2, f=0, grin=True),
    "lunge_0": dict(hands=[(50, 28), (57, 21), (45, 40), (56, 38)], tilts=[(2, 0)] * 4, lean=7, hdy=4, hshift=2,
                    legspread=3, sag=0, f=1, grin=True, armswing=-2),
    "hurt_0": dict(hands=[(12, 26), (50, 15), (8, 40), (57, 30)], tilts=[(-3, 0), (3, 0), (-3, 0), (3, 0)],
                   lean=-5, hdy=2, hshift=-1, crack=True, grimace=True, squint=True, noglint=True, sag=6, f=0,
                   armswing=3),
}


def kwak_defeat():
    im = new(64, 64)
    rnd = random.Random(21)
    # a ragged heap of contracts, lower edge on the bottom row
    sheets = []
    for i in range(34):
        t = i / 33
        x = int(32 + (rnd.random() - 0.5) * 56 * (1 - t * 0.55))
        y = int(63 - 4 - t * 28 + rnd.random() * 4)
        sheets.append((x, y))
    sheets.sort(key=lambda p: -p[1])
    # a bit of green suit and yellow tie sticking out of the pile
    suit = new(64, 64)
    poly(suit, [(14, 56), (28, 44), (44, 46), (54, 58), (50, 62), (18, 62)], "green0")
    poly(suit, [(40, 47), (54, 58), (50, 62), (42, 56)], "ink2")
    im.alpha_composite(outline(suit))
    line(im, [(30, 46), (35, 52)], "yellow", 2)
    for (x, y) in sheets:
        tilt = rnd.choice([-3, -2, 2, 3])
        w = rnd.choice([10, 11, 12])
        h = rnd.choice([6, 7, 8])
        pts = [(x - w // 2 + tilt, y - h), (x + w // 2 + tilt, y - h + (tilt // 2)), (x + w // 2, y), (x - w // 2, y)]
        poly(im, pts, "white" if rnd.random() < .6 else "wall1", "ink")
        yy = y - h + 2
        line(im, [(x - w // 2 + 2 + tilt, yy), (x + w // 2 - 3 + tilt, yy)], "grey2")
        line(im, [(x - w // 2 + 2 + tilt // 2, yy + 2), (x + w // 2 - 5, yy + 2)], "grey2")
        if rnd.random() < 0.3:
            rect(im, x + 1, y - 3, 3, 2, "red2")
    # dangling arm bits: thin limbs poking out
    for (a, b) in (((10, 58), (4, 52)), ((54, 54), (60, 48))):
        arm = new(64, 64); limb(arm, [a, b], "green0"); rect(arm, b[0] - 1, b[1] - 1, 3, 3, SKIN[0])
        im.alpha_composite(outline(arm))
    # glasses on top
    gx, gy = 25, 19
    rect(im, gx, gy, 7, 6, "grey4", "ink2"); rect(im, gx + 9, gy + 1, 7, 6, "grey4", "ink2")
    line(im, [(gx + 7, gy + 3), (gx + 8, gy + 3)], "ink2")
    px(im, gx + 1, gy + 1, "white"); px(im, gx + 2, gy + 1, "white")
    line(im, [(gx, gy), (gx + 5, gy + 5)], "ink"); line(im, [(gx + 16, gy + 1), (gx + 11, gy + 6)], "ink")
    line(im, [(gx - 1, gy + 1), (gx - 3, gy + 5)], "ink2")
    # shadow the pile base
    line(im, [(6, 63), (58, 63)], "ink")
    # the pile top rises toward the centre; glasses rest on it
    return im


# ======================================================================
#  BACKGROUND: closed amusement park, 3 AM
# ======================================================================
def sky_night(im, y0=Y0, y1=118):
    dither_ramp(im, (0, y0, W, y1), ["ink", "blue0", "blue0", "blue1", "purple0"], "y", 4)
    rnd = random.Random(7)
    for _ in range(46):
        x, y = rnd.randint(0, W - 1), rnd.randint(y0 + 1, 80)
        px(im, x, y, rnd.choice(["grey3", "blue3", "white", "grey2", "blue2"]))
    for (x, y) in ((22, 34), (150, 28), (296, 40)):          # a few brighter twinkles
        px(im, x, y, "white"); px(im, x - 1, y, "grey3"); px(im, x + 1, y, "grey3")
        px(im, x, y - 1, "grey3"); px(im, x, y + 1, "grey3")
    # crescent moon (echoes the float)
    mc = cmask((W, H), [("e", (30, 28, 52, 50))])
    mi = cmask((W, H), [("e", (38, 25, 60, 47))])
    cres = sub_mask(mc, mi)
    pool(im, 42, 40, 22, 18, "blue1", 0.5, 4)
    fill_mask(im, cres, "yellow2")
    for y in range(H):
        for x in range(W):
            if cres.getpixel((x, y)) and 0.35 > _thr(x, y, 4) and x > 38:
                im.putpixel((x, y), col("orange4"))
    # thin cloud streaks
    for (x, y, w) in ((196, 52, 44), (24, 70, 56), (240, 86, 60)):
        for k in range(w):
            if (k + y) % 3:
                px(im, x + k, y + (k // 17) % 2, "blue1")
    # distant tree line
    rnd = random.Random(11)
    x = 0
    while x < W:
        r = rnd.randint(9, 17)
        ellipse(im, x - r // 2, 108 - r, x + r, 124, "ink2")
        x += r - 3
    rect(im, 0, 112, W, 12, "ink2")
    dither_grad(im, (0, 104, W, 124), "ink2", "blue0", "y", 4, 0.0, 0.8)
    for xx in range(2, W, 7):
        px(im, xx, 104 + (xx * 7) % 6, "blue0")


def coaster(im):
    """far roller-coaster track silhouette behind the arch (dark, low contrast)."""
    pts = [(100, 100), (118, 82), (134, 68), (146, 70), (154, 90), (164, 100), (180, 92), (196, 76), (214, 74), (226, 96)]
    for a, b in zip(pts, pts[1:]):
        line(im, [a, b], "ink2", 2)
    for a, b in zip(pts, pts[1:]):
        line(im, [(a[0], a[1] - 2), (b[0], b[1] - 2)], "blue0")
    for (x, y) in pts[::1]:
        if y < 100:
            line(im, [(x, y + 1), (x, 112)], "ink2")
    for x in range(106, 226, 12):                         # cross braces
        y = 100
    return im


def ferris(im, cx, cy, R):
    """Ferris wheel silhouette with half-dead rim lights."""
    # A-frame legs
    for sx in (-1, 1):
        poly(im, [(cx - 2, cy), (cx + 2, cy), (cx + sx * 20 + 2, 124), (cx + sx * 20 - 3, 124)], "ink2")
        line(im, [(cx, cy), (cx + sx * 20, 124)], "ink")
    rect(im, cx - 26, 122, 54, 4, "ink2", "ink")
    # rim + inner rim
    for r, c in ((R, "ink2"), (R - 1, "ink2"), (R - 11, "ink2")):
        ellipse(im, cx - r, cy - r, cx + r, cy + r, None, c)
    ellipse(im, cx - R - 1, cy - R - 1, cx + R + 1, cy + R + 1, None, "ink")
    for k in range(12):
        a = k * math.pi / 6
        line(im, [(cx, cy), (int(cx + R * math.cos(a)), int(cy + R * math.sin(a)))], "ink2")
    ellipse(im, cx - 4, cy - 4, cx + 4, cy + 4, "ink2", "ink")
    px(im, cx - 1, cy - 1, "grey1")
    rnd = random.Random(5)
    lit_cols = ["yellow", "orange2", "red3", "blue3"]
    for k in range(24):
        a = k * math.pi / 12
        bx, by = int(cx + (R + 1) * math.cos(a)), int(cy + (R + 1) * math.sin(a))
        if rnd.random() < 0.45:
            c = rnd.choice(lit_cols)
            dither_radial(im, bx, by, 5, c, None, 4)
            rect(im, bx - 1, by - 1, 2, 2, c)
        else:
            rect(im, bx - 1, by - 1, 2, 2, "grey1")
    # gondolas hang from every second spoke tip
    for k in range(0, 12):
        a = k * math.pi / 6 + math.pi / 12
        gx, gy = int(cx + R * math.cos(a)), int(cy + R * math.sin(a))
        rect(im, gx - 2, gy + 1, 5, 5, "ink2", "ink")
        px(im, gx - 1, gy + 2, "blue1" if k % 3 else "grey1")
        px(im, gx, gy, "ink")


def carousel(im):
    x0, x1 = 8, 104
    # --- back of the ride: mirror panels in shadow + central column
    rect(im, x0 + 3, 100, x1 - x0 - 6, 40, "ink")
    for i, x in enumerate(range(x0 + 4, x1 - 4, 8)):
        rect(im, x, 104, 7, 34, "blue0")
        dither_grad(im, (x, 104, x + 7, 138), "blue0", "blue1", "y", 4, 0.0, 0.7)
        px(im, x + 1, 106, "blue3"); px(im, x + 1, 107, "blue2")
        vline(im, x + 7, 104, 138, "ink")
    rect(im, 52, 80, 7, 60, "orange1", "ink")
    vline(im, 53, 82, 140, "orange3"); vline(im, 57, 82, 140, "orange0")
    for y in range(86, 138, 9):
        rect(im, 52, y, 7, 2, "yellow", "ink")
    # --- warm glow from the few live bulbs (drawn before the horses so they stay crisp)
    for x in (22, 40, 64, 82):
        pool(im, x, 118, 9, 8, "orange1", 0.55, 4)
    # --- platform
    rect(im, x0, 138, x1 - x0, 12, "brown1", "ink")
    dither_grad(im, (x0 + 1, 139, x1 - 1, 149), "brown2", "brown0", "y", 4, 0.0, 0.9)
    hline(im, x0, x1 - 1, 139, "brown3")
    for x in range(x0 + 3, x1 - 3, 8):
        rect(im, x, 143, 4, 3, "orange0", "ink")
        px(im, x + 1, 144, "yellow2" if (x // 8) % 3 else "grey1")
    # --- horses on brass poles: far row then near row
    spec = [(19, 0, "white", "grey3", "orange3", False), (88, 0, "wall4", "red4", "yellow", True),
            (37, 6, "blue3", "blue2", "white", False), (70, 6, "wall2", "green2", "red3", True)]
    for hx, lift, base, sh, mane, fx in spec:
        pole_x = hx + (11 if not fx else 9)
        rect(im, pole_x, 98, 2, 40 - lift, "orange2", "ink")
        vline(im, pole_x, 99, 136 - lift, "orange3")
        horse(im, hx, 134 - lift, base, sh, mane, flipx=fx)
    # --- roof: striped canopy (red / pale), shaded toward the lower rim
    x_l, x_r = x0 - 3, x1 + 3
    roof = [(x_l, 108), (x_r, 108), (62, 72), (50, 72)]
    mk = cmask((W, H), [("p", roof)])
    for y in range(70, 109):
        for x in range(x_l - 1, x_r + 2):
            if mk.getpixel((x, y)):
                k = int((x - 56) * 8 / max(1, (y - 66))) // 6
                im.putpixel((x, y), col("wall1" if k % 2 else "red2"))
    for y in range(70, 109):
        for x in range(x_l - 1, x_r + 2):
            if mk.getpixel((x, y)):
                c = im.getpixel((x, y))
                t = (y - 70) / 38
                if c == col("wall1") and 0.7 * t > _thr(x, y, 4):
                    im.putpixel((x, y), col("grey3"))
                if c == col("red2") and 0.55 * (x - x_l) / (x_r - x_l) > _thr(x, y, 4):
                    im.putpixel((x, y), col("red1"))
    poly(im, roof, None, "ink")
    rect(im, x_l, 106, x_r - x_l + 1, 3, "orange1", "ink")
    hline(im, x_l + 1, x_r - 1, 107, "orange3")
    for i, x in enumerate(range(x0 - 2, x1 + 2, 8)):
        c = "wall1" if i % 2 else "red2"
        poly(im, [(x, 108), (x + 8, 108), (x + 4, 115)], c, "ink")
        px(im, x + 1, 109, "white" if i % 2 else "red3")
    # bulbs under the valance (some lit, some dead)
    for i, x in enumerate(range(x0 + 2, x1, 6)):
        lit = (i * 5) % 7 in (0, 2, 3)
        rect(im, x, 116 if i % 2 else 115, 2, 2, "yellow2" if lit else "grey1")
    # finial + flag
    rect(im, 55, 62, 2, 10, "orange2", "ink")
    ellipse(im, 53, 58, 58, 63, "yellow", "ink")
    poly(im, [(57, 62), (68, 65), (57, 69)], "red2", "ink")


def horse(im, x, by, base, sh, mane, flipx=False):
    """carousel horse, side view facing right, ~22x20, hooves on y=by."""
    h = new(24, 22)
    poly(h, [(3, 8), (14, 7), (16, 12), (14, 15), (4, 14)], base)            # barrel
    poly(h, [(13, 8), (17, 1), (21, 2), (22, 7), (18, 7), (16, 12)], base)   # neck + head
    poly(h, [(19, 0), (21, 0), (21, 2)], base)                              # ear
    rect(h, 4, 14, 2, 6, base); rect(h, 7, 14, 2, 5, base)                  # back legs
    rect(h, 12, 14, 2, 5, base); rect(h, 15, 13, 2, 6, base)                # front legs
    line(h, [(17, 2), (14, 8)], mane)                                       # mane
    line(h, [(2, 8), (0, 12)], mane); line(h, [(3, 9), (1, 13)], mane)      # tail
    rect(h, 6, 6, 6, 3, "red2")                                             # saddle
    rect(h, 4, 18, 2, 2, sh); rect(h, 7, 17, 2, 2, sh); rect(h, 12, 17, 2, 2, sh); rect(h, 15, 18, 2, 2, sh)
    for (a, b) in ((5, 13), (7, 13), (9, 14), (11, 13), (13, 13)):
        px(h, a, b, sh)
    h = outline(h)
    px(h, 20, 4, "ink")
    if flipx:
        h = flip(h)
    paste(im, h, x, by - 20)


def booth(im):
    x0, x1 = 258, 304
    # body
    rect(im, x0, 110, x1 - x0, 40, "blue2", "ink")
    dither_grad(im, (x0 + 1, 111, x1 - 1, 149), "blue2", "blue1", "y", 4, 0.0, 0.9)
    for x in range(x0 + 4, x1 - 2, 6):
        vline(im, x, 112, 148, "blue1")
    ovl(im, (x0 + 1, 111, x1 - 1, 149), "blue0", 0.18, 2)
    rect(im, x0, 144, x1 - x0, 6, "grey1", "ink")
    hline(im, x0 + 1, x1 - 2, 145, "grey2")
    # awning
    for i, x in enumerate(range(x0 - 3, x1 + 3, 7)):
        poly(im, [(x, 104), (x + 7, 104), (x + 7, 112), (x + 3, 114), (x, 112)],
             "wall1" if i % 2 else "red2", "ink")
        px(im, x + 1, 105, "white" if i % 2 else "red3")
    rect(im, x0 - 4, 101, x1 - x0 + 8, 4, "grey1", "ink")
    hline(im, x0 - 3, x1 + 2, 102, "grey2")
    # blank sign
    rect(im, 266, 90, 30, 11, "grey4", "ink")
    dither_grad(im, (267, 91, 295, 100), "grey4", "grey3", "y", 4, 0.0, 0.9)
    px(im, 267, 91, "white"); px(im, 268, 91, "white")
    vline(im, 270, 85, 90, "ink"); vline(im, 292, 85, 90, "ink")
    # little dead bulb row on the sign
    for x in range(268, 295, 4):
        px(im, x, 99, "grey2")
    # window with a grille + sill
    rect(im, 266, 118, 24, 17, "ink", "ink")
    dither_grad(im, (267, 119, 289, 134), "ink", "blue0", "y", 2, 0.0, 0.6)
    for x in range(269, 289, 4):
        vline(im, x, 119, 133, "grey2")
    hline(im, 267, 288, 126, "grey2")
    px(im, 284, 130, "yellow")                              # a tiny dim lamp left on
    dither_radial(im, 284, 130, 4, "orange1", None, 4)
    px(im, 284, 130, "yellow")
    rect(im, 263, 134, 30, 4, "brown2", "ink")
    hline(im, 264, 291, 135, "brown3")
    # a ticket roll and coin tray on the sill
    rect(im, 270, 131, 6, 3, "wall1", "ink")
    # door
    rect(im, 293, 117, 9, 27, "grey1", "ink")
    rect(im, 295, 119, 5, 8, "blue0", "ink")
    px(im, 299, 133, "yellow")
    # lamp stuck to the awning, flickering (dead)
    rect(im, x0 - 1, 98, 3, 3, "grey1", "ink")
    # ticket board leaning at the side
    rect(im, 250, 128, 8, 22, "wall1", "ink")
    hline(im, 251, 256, 132, "grey3"); hline(im, 251, 255, 136, "grey3"); hline(im, 251, 256, 140, "grey3")
    px(im, 253, 129, "red2")


def gate_arch(im):
    xl, xr = 114, 200
    top = 46
    # pillars
    for (x0, x1) in ((xl, xl + 9), (xr - 9, xr)):
        rect(im, x0, top + 8, 9, 76, "brown3", "ink")
        dither_grad(im, (x0 + 1, top + 9, x0 + 8, top + 83), "brown3", "brown2", "x", 4, 0.0, 1.0)
        for y in range(top + 14, top + 80, 10):
            hline(im, x0 + 1, x0 + 7, y, "brown2")
        rect(im, x0 - 2, top + 82, 13, 4, "brown1", "ink")
        rect(im, x0 - 1, top + 5, 11, 4, "brown1", "ink")
    # crown: sign board
    pts = [(xl - 8, top + 12), (xr + 8, top + 12), (xr + 8, top - 6), (160 + 30, top - 14), (160, top - 18),
           (160 - 30, top - 14), (xl - 8, top - 6)]
    poly(im, pts, "purple1", "ink")
    dither_grad(im, (xl - 8, top - 18, xr + 9, top + 13), "purple1", "purple0", "y", 4, 0.0, 0.9,
                cmask((W, H), [("p", pts)]))
    poly(im, pts, None, "ink")
    # inner panel
    rect(im, xl + 2, top - 6, xr - xl - 3, 16, "blue0", "ink")
    text(im, 157, top - 5, "달빛랜드", "yellow", 11, edge="ink", shadow="ink", align="center")
    # bulbs around the board: some lit, a couple dead
    bulbs = [(x, top - 7 + (6 if False else 0)) for x in range(xl - 5, xr + 6, 7)]
    for i, (x, _) in enumerate(bulbs):
        lit = i % 3 != 1 and i != 6
        y = top + 12
        if lit:
            dither_radial(im, x, y, 5, "orange3", None, 4)
            rect(im, x, y, 2, 2, "yellow2")
        else:
            rect(im, x, y, 2, 2, "grey1")
    for i, x in enumerate(range(xl - 6, xr + 6, 9)):
        y = top - 16 + abs(x - 157) // 4 if False else top - 13 + (abs(x - 157) * 14 // 70 if False else 0)
    # flag pennants strung under the board
    for x in range(xl + 12, xr - 10, 8):
        poly(im, [(x, top + 12), (x + 6, top + 12), (x + 3, top + 18)],
             ["red2", "yellow", "blue2", "wall1"][(x // 8) % 4], "ink")
    # one pennant hangs by a thread
    px(im, xl + 44, top + 19, "ink")


def lamp_post(im, x, top_y, bot_y, lit=True, seed=0):
    rect(im, x, top_y + 4, 2, bot_y - top_y - 4, "ink2", "ink")
    rect(im, x - 2, bot_y - 2, 6, 3, "ink2", "ink")
    rect(im, x - 3, top_y, 8, 4, "grey1", "ink")
    if lit:
        dither_radial(im, x + 1, top_y + 8, 11, "orange2", None, 4)
        rect(im, x - 2, top_y + 3, 6, 2, "yellow2")
    else:
        rect(im, x - 2, top_y + 3, 6, 2, "grey2")


def road(im):
    y0, y1 = 140, 157
    # curb
    rect(im, 0, y0, W, 3, "grey2")
    hline(im, 0, W - 1, y0, "ink")
    hline(im, 0, W - 1, y0 + 1, "grey3")
    hline(im, 0, W - 1, y0 + 2, "grey1")
    # asphalt
    dither_grad(im, (0, y0 + 3, W, y1 + 1), "grey1", "ink2", "y", 4, 0.0, 0.85)
    for i in range(14):                                      # patches
        pass
    speckle(im, (0, y0 + 4, W, y1), "grey2", 70, 3)
    speckle(im, (0, y0 + 4, W, y1), "ink", 50, 4)
    # edge lines
    hline(im, 0, W - 1, y0 + 4, "grey3")
    # dashed centre line
    for x in range(-4, W, 22):
        rect(im, x, 149, 13, 2, "yellow")
        hline(im, x, x + 12, 150, "orange2")
    hline(im, 0, W - 1, y1, "ink")
    # crosswalk-ish chevrons
    # worn paint: erase bits of dashes
    speckle(im, (0, 149, W, 151), "grey1", 28, 9)
    # confetti + a dropped balloon on the road
    rnd = random.Random(13)
    for _ in range(26):
        px(im, rnd.randint(0, W - 1), rnd.randint(143, 156), rnd.choice(["red3", "yellow", "blue2", "green2", "orange2"]))
    ellipse(im, 172, 150, 179, 156, "red2", "ink"); px(im, 174, 151, "red4")
    line(im, [(176, 156), (180, 157)], "ink")


def lane(im):
    """mid-ground parade lane y 96..140: dark plaza paving, clear for floats."""
    dither_grad(im, (0, 96, W, 140), "blue0", "ink2", "y", 4, 0.0, 0.9)
    # back kerb + low fence at the far edge
    rect(im, 0, 112, W, 3, "ink2")
    hline(im, 0, W - 1, 112, "ink")
    hline(im, 0, W - 1, 113, "grey1")
    for x in range(0, W, 8):
        vline(im, x, 100, 111, "ink")
    hline(im, 0, W - 1, 100, "ink"); hline(im, 0, W - 1, 105, "ink2")
    # hedge behind the fence
    for x in range(0, W, 5):
        ellipse(im, x - 2, 95 + (x * 3) % 3, x + 4, 103, "green0", None)
    ovl(im, (0, 92, W, 100), "ink", 0.5, 4)
    # paving seams with perspective hint
    for x in range(-20, W + 40, 26):
        line(im, [(x, 115), (x - 10, 139)], "ink")
    for y in (121, 129, 138):
        hline(im, 0, W - 1, y, "ink")
    speckle(im, (0, 116, W, 139), "grey1", 60, 22)
    speckle(im, (0, 116, W, 139), "blue1", 40, 23)
    # pooled cold moonlight and warm string-light spill on the paving
    pool(im, 150, 124, 60, 11, "blue1", 0.35, 4)
    pool(im, 60, 126, 40, 8, "orange1", 0.35, 4)
    pool(im, 282, 128, 28, 8, "orange1", 0.3, 4)


def build_park():
    im = new(fill="ink")
    sky_night(im)
    coaster(im)
    ferris(im, 238, 70, 32)
    lane(im)
    gate_arch(im)
    road(im)
    carousel(im)
    booth(im)
    lamp_post(im, 106, 92, 126, False)
    lamp_post(im, 214, 94, 126, True)
    lamp_post(im, 244, 98, 128, False)
    lit = ["yellow", "orange2", "red3", "blue3"]
    catenary(im, (0, 52), (56, 62), 8, 8, ["yellow", "orange3", "blue3"], 5, glowc="orange1")
    catenary(im, (60, 64), (118, 52), 6, 8, ["yellow", "orange3", "red3", "green2"], 3, glowc="orange1")
    catenary(im, (196, 52), (258, 101), 8, 10, lit, 2, glowc="orange1")
    catenary(im, (262, 101), (319, 60), 8, 8, lit, 4, glowc="orange1")
    BI.ov(im, (0, 22, 40, 158), "ink", 0.5, 0.0, "x", 4)
    BI.ov(im, (290, 22, 320, 158), "ink", 0.0, 0.45, "x", 4)
    BI.ov(im, (0, 22, 320, 40), "ink", 0.5, 0.0, "y", 4)
    letterbox(im)
    return im


# ======================================================================
#  ENDING 1: dawn outside the agency
# ======================================================================
def vtext(img, cx, y, s, c, f=11, step=12, edge=None):
    for i, ch in enumerate(s):
        text(img, cx, y + i * step, ch, c, f, edge=edge, align="center")


def shadow_of(sprite, fx, fy, k=1.25):
    """long ground shadow lying to the left of a sprite (sun on the right): 'L' mask."""
    m = Image.new("L", (W, H), 0)
    for y in range(sprite.height):
        for x in range(sprite.width):
            if sprite.getpixel((x, y))[3]:
                d = (fy - (y + (fy - 45 - 0)) + 0) if False else (45 - y)
                sx = int(fx + (x - 16) - d * k)
                th = 2 if d < 14 else (3 if d < 30 else 5)
                for dy in range(th):
                    sy = fy - 1 + dy
                    if 0 <= sx < W and 0 <= sy < H:
                        m.putpixel((sx, sy), 255)
    return m


def rim_light(spr, c="orange3", level=0.8):
    """sun is on the right: tint the lit right edge of a sprite (the pixel left of the ink outline)."""
    out = spr.copy()
    ink = col("ink")
    for y in range(spr.height):
        for x in range(spr.width - 1):
            p = spr.getpixel((x, y))
            if p[3] and p != ink and spr.getpixel((x + 1, y)) in (ink, (0, 0, 0, 0)) and level > _thr(x, y, 2):
                out.putpixel((x, y), col(c))
    return out


def dawn_sky(im):
    dither_ramp(im, (0, Y0, W, 134), ["purple1", "purple2", "red4", "orange3", "orange4"], "y", 4)
    # sun glow centred where the sun rises between the far blocks
    sx, sy = 262, 120
    dither_radial(im, sx, sy, 62, "yellow2", None, 4, box=(sx - 62, 60, sx + 63, 134))
    dither_radial(im, sx, sy, 34, "white", None, 4, box=(sx - 34, 84, sx + 35, 134))
    # cloud banks (flat, dithered edges)
    rnd = random.Random(31)
    for (cx0, cy0, wd) in ((30, 44, 84), (150, 36, 70), (212, 62, 90), (74, 78, 64), (14, 100, 70)):
        for yy in range(cy0, cy0 + 5):
            ww = wd - abs(yy - cy0 - 2) * 12
            for xx in range(cx0 - ww // 2, cx0 + ww // 2):
                if 0 < xx < W:
                    t = (yy - cy0) / 4
                    c = "red3" if t > 0.55 else "red4"
                    if (1 - abs(2 * (xx - cx0) / max(1, wd))) > _thr(xx, yy, 4) * 1.2:
                        px(im, xx, yy, c)
                    if t < 0.3 and (xx + yy) % 2 == 0 and abs(xx - cx0) < wd // 4:
                        px(im, xx, yy, "orange4")
    for _ in range(14):                                          # fading stars
        px(im, rnd.randint(0, 200), rnd.randint(Y0 + 1, 50), "white")
    # sun disc, partly hidden by far buildings
    ellipse(im, sx - 11, sy - 11, sx + 11, sy + 11, "yellow2", "orange4")
    ellipse(im, sx - 8, sy - 8, sx + 8, sy + 8, "white", None)


def far_blocks(im):
    """distant silhouettes (purple haze) with a few early lit windows."""
    rnd = random.Random(5)
    x = 150
    while x < W:
        w = rnd.randint(14, 26)
        h = rnd.randint(18, 52)
        if 232 < x < 288:
            x += w
            continue
        rect(im, x, 134 - h, w, h, "purple1", "purple0")
        dither_grad(im, (x + 1, 135 - h, x + w - 1, 134), "purple1", "red1", "y", 4, 0.0, 0.9)
        for yy in range(136 - h, 130, 6):
            for xx in range(x + 3, x + w - 3, 5):
                if rnd.random() < 0.16:
                    rect(im, xx, yy, 2, 2, "yellow2")
                elif rnd.random() < 0.5:
                    rect(im, xx, yy, 2, 2, "purple0")
        x += w - 1


def agency_front(im):
    x0, x1, top, base = 0, 150, 46, 132
    # facade: cool shade on the left, sun-kissed on the right
    rect(im, x0, top, x1 - x0, base - top, "wall4", "ink")
    dither_grad(im, (x0 + 1, top + 1, x1 - 1, base), "wall3", "wall4", "x", 4, 0.0, 0.8)
    dither_grad(im, (x0 + 60, top + 1, x1 - 1, base), "wall4", "orange4", "x", 4, 0.0, 0.75)
    # parapet + roof junk
    rect(im, x0, top - 6, x1 - x0 + 2, 7, "grey3", "ink")
    hline(im, x0 + 1, x1, top - 5, "grey4")
    hline(im, x0 + 1, x1, top, "grey2")
    rect(im, 104, top - 16, 24, 10, "grey2", "ink")                 # rooftop water tank
    rect(im, 106, top - 14, 20, 2, "grey3")
    rect(im, 110, top - 20, 2, 4, "ink"); rect(im, 122, top - 20, 2, 4, "ink")
    rect(im, 18, top - 12, 16, 6, "grey3", "ink")                    # AC box
    for k in range(4):
        vline(im, 20 + k * 4, top - 11, top - 8, "grey2")
    # upper floor windows (dark, with dawn reflection at the top right)
    for wx in (14, 56, 98):
        rect(im, wx - 2, 56, 30, 26, "grey4", "ink")
        rect(im, wx, 58, 26, 22, "blue0", "ink")
        dither_grad(im, (wx + 1, 59, wx + 25, 79), "blue0", "blue1", "y", 4, 0.0, 0.7)
        dither_grad(im, (wx + 13, 59, wx + 25, 70), "blue1", "orange3", "d", 4, 0.1, 0.9)
        vline(im, wx + 13, 58, 79, "ink")
        hline(im, wx, wx + 25, 69, "ink")
        rect(im, wx - 3, 82, 32, 3, "grey2", "ink")
        hline(im, wx - 2, wx + 28, 83, "grey3")
    # ground floor: roll shutter (closed) + glass door; blank fascia band
    rect(im, 4, 90, 142, 8, "grey2", "ink")
    dither_grad(im, (5, 91, 145, 97), "grey3", "grey2", "x", 4, 0.0, 1.0)
    rect(im, 46, 100, 56, 32, "grey3", "ink")
    for y in range(102, 131, 3):
        hline(im, 47, 100, y, "grey2")
    dither_grad(im, (47, 100, 101, 132), "grey3", "grey2", "x", 4, 0.0, 0.4)
    rect(im, 44, 98, 60, 3, "grey1", "ink")
    rect(im, 72, 124, 4, 3, "ink2", "ink")                            # handle
    rect(im, 8, 100, 30, 32, "grey3", "ink")                          # door
    rect(im, 11, 103, 24, 22, "blue0", "ink")
    dither_grad(im, (12, 104, 34, 124), "blue0", "blue1", "y", 4, 0.0, 0.8)
    rect(im, 14, 106, 7, 4, "wall1", "ink")                            # taped paper: HELP WANTED (blank)
    line(im, [(15, 108), (19, 108)], "grey2")
    rect(im, 30, 112, 2, 4, "grey1")
    rect(im, 108, 104, 34, 26, "wall1", "ink")                        # shuttered notice board
    for k in range(4):
        hline(im, 111, 138 - (k % 2) * 6, 109 + k * 5, "grey2")
    # building base
    rect(im, 0, 128, 150, 4, "grey1", "ink")
    # vertical agency sign: bracket, panel, text - switched OFF
    rect(im, 128, 60, 22, 3, "grey1", "ink")
    rect(im, 131, 62, 16, 54, "blue1", "ink")
    dither_grad(im, (132, 63, 146, 115), "blue1", "blue0", "y", 4, 0.0, 0.9)
    vtext(im, 139, 65, "새벽인력", "grey3", 11, 12, edge="ink")
    # dead tube bulbs along the sign edge
    for y in range(66, 114, 8):
        px(im, 132, y, "grey1"); px(im, 145, y, "grey1")


def street_dawn_scene():
    im = new(fill="ink")
    dawn_sky(im)
    far_blocks(im)
    # mid block (right) closer than the far silhouettes
    rect(im, 150, 80, 78, 52, "wall4", "ink")
    dither_grad(im, (151, 81, 227, 132), "wall3", "orange4", "x", 4, 0.1, 1.0)
    rect(im, 150, 74, 78, 6, "grey3", "ink")
    for wx in (160, 190):
        rect(im, wx, 88, 20, 14, "blue0", "ink")
        dither_grad(im, (wx + 1, 89, wx + 19, 101), "blue0", "orange3", "d", 4, 0.1, 0.8)
        vline(im, wx + 10, 88, 101, "ink")
    rect(im, 164, 108, 44, 24, "grey3", "ink")                       # closed shop shutter
    for y in range(110, 131, 3):
        hline(im, 165, 207, y, "grey2")
    rect(im, 162, 106, 48, 3, "red2", "ink")
    for x in range(164, 210, 6):
        px(im, x, 107, "red3")
    rect(im, 150, 128, 78, 4, "grey1", "ink")
    agency_front(im)
    # right-most low shop (partial)
    rect(im, 284, 104, 40, 28, "wall1", "ink")
    dither_grad(im, (285, 105, 323, 131), "wall3", "orange4", "x", 4, 0.0, 0.8)
    rect(im, 284, 100, 40, 5, "grey2", "ink")
    rect(im, 290, 110, 16, 12, "blue0", "ink")
    dither_grad(im, (291, 111, 305, 121), "blue0", "orange2", "d", 4, 0.0, 0.8)
    rect(im, 284, 128, 40, 4, "grey1", "ink")
    # sidewalk
    dither_grad(im, (0, 132, W, 151), "grey4", "wall4", "y", 4, 0.0, 0.8)
    hline(im, 0, W - 1, 132, "ink")
    for x in range(0, W, 16):
        vline(im, x + (x // 16 % 2) * 8, 133, 150, "grey3")
    hline(im, 0, W - 1, 141, "grey3")
    dither_grad(im, (150, 133, W, 151), "orange4", "wall4", "x", 4, 0.0, 0.2) if False else None
    # warm sun streak over the pavement (right side)
    for y in range(133, 151):
        for x in range(120, W):
            t = (x - 120) / 200
            if t * 0.65 > _thr(x, y, 4):
                px(im, x, y, "orange4" if (y + x) % 3 else "yellow2")
    speckle(im, (0, 134, W, 150), "grey2", 40, 14)
    # curb + road
    rect(im, 0, 150, W, 2, "grey2")
    hline(im, 0, W - 1, 150, "ink"); hline(im, 0, W - 1, 151, "grey3")
    dither_grad(im, (0, 152, W, 158), "purple0", "ink2", "y", 4, 0.0, 1.0)
    for x in range(10, W, 40):
        rect(im, x, 155, 16, 1, "orange3")
    # lamp posts, unlit
    for lx in (170, 292):
        rect(im, lx, 92, 3, 58, "ink2", "ink")
        rect(im, lx - 3, 148, 9, 3, "ink2", "ink")
        rect(im, lx - 6, 88, 14, 5, "grey1", "ink")
        hline(im, lx - 5, lx + 6, 89, "grey2")
        rect(im, lx - 4, 93, 10, 2, "grey3")
    # power pole + wires
    rect(im, 307, 50, 3, 100, "brown1", "ink")
    rect(im, 299, 54, 20, 3, "brown1", "ink")
    rect(im, 301, 62, 16, 2, "brown1", "ink")
    for (ya, yb, sag) in ((55, 66, 6), (56, 60, 5), (63, 72, 7)):
        catenary(im, (318, ya), (319, yb), 0, 1, ["grey1"], 1, wire="ink2")
        catenary(im, (300, ya), (150, ya + 4), sag + 3, 1, ["grey1"], 1, wire="ink2")
    # litter and a newspaper
    rect(im, 182, 144, 6, 3, "white", "ink"); px(im, 184, 145, "grey3")
    # birds
    for (bx, by) in ((84, 34), (96, 30), (106, 36)):
        px(im, bx, by, "ink"); px(im, bx + 1, by + 1, "ink"); px(im, bx + 2, by, "ink")
        px(im, bx - 1, by + 1, "ink") if False else None
    return im


def build_dawn():
    im = street_dawn_scene()
    # the two figures walking away to the right
    sora = rim_light(chibi(CAST["sora"], "side", "walk", 1))
    jun = rim_light(chibi(JUNHO, "side", "walk", 3))
    sora = frost(rim_light(flip(chibi(CAST["sora"], "side", "walk", 1))), 2) if False else rim_light(flip(chibi(CAST["sora"], "side", "walk", 1)))
    jun = rim_light(flip(junho_frame("side", "walk", 3)))
    fy = 146
    for (spr, fx) in ((sora, 204), (jun, 240)):
        top_y = fy - 45
        # long shadow, left, dither on the paving
        m = shadow_of(spr, fx, fy)
        ovl_mask = m
        for y in range(H):
            for x in range(W):
                if m.getpixel((x, y)) and 133 <= y <= 150 and x < fx - 6:
                    im.putpixel((x, y), col("purple0") if (x + y) % 3 else col("purple1"))
        paste(im, spr, fx - 16, top_y)
    letterbox(im)
    return im


# ======================================================================
#  ENDINGS 2 + 3: the agency desk, visitor's side
# ======================================================================
SICK = {   # bleak night: cold green-grey wall, no warmth anywhere
    "orange0": "ink2", "orange1": "green0", "orange2": "green1", "orange3": "pale1", "orange4": "pale2",
    "brown0": "ink", "brown1": "ink2", "brown2": "grey1", "brown3": "grey2",
    "yellow2": "pale2", "yellow": "pale2", "wall1": "pale2", "wall3": "grey3", "wall4": "grey4",
    "red2": "grey2", "red3": "grey3",
}
SOFT = {   # dawn: pastel, soft light
    "orange0": "brown3", "orange1": "wall4", "orange2": "wall1", "orange3": "white", "orange4": "white",
    "brown0": "brown1", "brown1": "brown2", "brown2": "brown3", "brown3": "wall1",
}


def office_base(variant):
    img = new(fill="ink")
    BI.office_wall(img)
    BI.filing_cabinets(img)
    BI.wall_calendar(img)
    if variant == "sick":
        BI.dying_plant(img)
    img = swap(img, SICK if variant == "sick" else SOFT)
    return img


def office_window(img, variant):
    x0, y0, w, h = 226, 34, 66, 52
    rect(img, x0 - 3, y0 - 3, w + 6, h + 6, "grey3" if variant == "sick" else "wall1", "ink")
    rect(img, x0 - 1, y0 - 1, w + 2, h + 2, "grey1" if variant == "sick" else "brown2", "ink")
    if variant == "sick":
        # black glass, a faint reflection of the tube light and one dead red dot far away
        rect(img, x0, y0, w, h, "ink")
        dither_grad(img, (x0, y0, x0 + w, y0 + h), "ink", "blue0", "y", 4, 0.0, 0.5)
        for k in range(3):
            hline(img, x0 + 6, x0 + 22 - k * 3, y0 + 8 + k * 2, "grey1")
        px(img, x0 + 50, y0 + 18, "red2"); px(img, x0 + 50, y0 + 19, "red1")
        px(img, x0 + 12, y0 + 38, "grey1")
        vline(img, x0 + w // 2, y0, y0 + h - 1, "ink2")
        # blinds fully up but one slat bent
        rect(img, x0, y0, w, 3, "grey2", "ink")
    else:
        dither_ramp(img, (x0, y0, x0 + w, y0 + h), ["purple2", "red4", "orange3", "orange4"], "y", 4)
        for (bx, bw, bh) in ((2, 10, 20), (14, 14, 28), (30, 12, 18), (44, 18, 24)):      # skyline
            rect(img, x0 + bx, y0 + h - bh, bw, bh, "purple1", "purple0")
        dither_radial(img, x0 + 52, y0 + 40, 14, "yellow2", None, 4, box=(x0, y0, x0 + w, y0 + h))
        vline(img, x0 + w // 2, y0, y0 + h - 1, "brown2")
        vline(img, x0 + w // 2 + 1, y0, y0 + h - 1, "ink")
        rect(img, x0, y0, w, 3, "wall1", "ink")
        hline(img, x0, x0 + w - 1, y0 + 3, "grey3")
    rect(img, x0 - 5, y0 + h + 3, w + 10, 4, "grey3" if variant == "sick" else "wall1", "ink")


def wall_clock(img, cx, cy, hour, minute, variant):
    ellipse(img, cx - 10, cy - 10, cx + 10, cy + 10, "grey3" if variant == "sick" else "brown3", "ink")
    ellipse(img, cx - 8, cy - 8, cx + 8, cy + 8, "pale2" if variant == "sick" else "white", "grey2")
    for k in range(12):
        a = k * math.pi / 6
        px(img, int(round(cx + 6.2 * math.sin(a))), int(round(cy - 6.2 * math.cos(a))), "ink2")
    ah = (hour % 12 + minute / 60) * math.pi / 6
    am = minute * math.pi / 30
    line(img, [(cx, cy), (int(round(cx + 4 * math.sin(ah))), int(round(cy - 4 * math.cos(ah))))], "ink", 2)
    line(img, [(cx, cy), (int(round(cx + 7 * math.sin(am))), int(round(cy - 7 * math.cos(am))))], "ink")
    px(img, cx, cy, "red2")


def chair_back(img, variant):
    cx = 160
    c1, c2 = ("ink2", "ink") if variant == "sick" else ("brown2", "brown1")
    rect(img, cx - 25, 64, 50, 50, c1, "ink")
    dither_grad(img, (cx - 24, 65, cx + 24, 113), c1, c2, "x", 4, 0.0, 0.9)
    ellipse(img, cx - 25, 58, cx + 24, 76, c1, "ink")
    dither_grad(img, (cx - 24, 59, cx + 24, 75), c1, c2, "x", 4, 0.0, 0.9)
    rect(img, cx - 26, 70, 3, 40, c2, "ink"); rect(img, cx + 24, 70, 3, 40, c2, "ink")       # side rails
    for y in range(74, 110, 9):                                                              # tufting
        for x in range(cx - 18, cx + 20, 12):
            px(img, x, y, "ink" if variant == "sick" else "brown0")
    hline(img, cx - 20, cx + 20, 62, "grey1" if variant == "sick" else "brown3")


def desk_front(img, variant):
    sick = variant == "sick"
    top_c = ("grey2", "grey1") if sick else ("brown3", "brown2")
    body_c = ("grey1", "ink2") if sick else ("brown2", "brown1")
    dx0, dx1 = 84, 236
    ty, tb = 106, 119
    rect(img, dx0 - 2, ty, dx1 - dx0 + 4, tb - ty, top_c[0], "ink")             # desktop (seen from above)
    dither_grad(img, (dx0 - 1, ty + 1, dx1 + 1, tb), top_c[0], top_c[1], "y", 4, 0.0, 0.8)
    hline(img, dx0 - 1, dx1 + 1, ty + 1, "pale2" if sick else "white")
    rect(img, dx0 - 4, tb, dx1 - dx0 + 8, 4, top_c[1], "ink")                    # front lip
    rect(img, dx0, tb + 4, dx1 - dx0, 150 - tb - 4, body_c[0], "ink")
    dither_grad(img, (dx0 + 1, tb + 5, dx1 - 1, 149), body_c[0], body_c[1], "x", 4, 0.0, 0.8)
    for sx in (dx0 + 5, dx1 - 45):                                                # drawer stacks
        rect(img, sx, tb + 8, 40, 26, body_c[1], "ink")
        for d in range(3):
            yy = tb + 10 + d * 8
            rect(img, sx + 3, yy, 34, 7, body_c[0], "ink")
            hline(img, sx + 4, sx + 36, yy + 1, top_c[0])
            rect(img, sx + 14, yy + 3, 12, 2, "grey3" if sick else "orange3", "ink")
    rect(img, dx0 + 52, tb + 8, dx1 - dx0 - 104, 26, "ink", "ink")                # knee well
    dither_grad(img, (dx0 + 53, tb + 9, dx1 - 53, tb + 33), "ink", "ink2", "y", 2, 0.2, 0.6)
    rect(img, dx0 + 2, 146, 8, 4, "ink"); rect(img, dx1 - 10, 146, 8, 4, "ink")


def rule_stack(img, x, y, n, variant):
    """stack of rule sheets seen from the front edge; y = bottom of the stack."""
    for k in range(n):
        off = (k * 7) % 3 - 1
        yy = y - k * 2
        rect(img, x + off, yy - 2, 24, 3, "pale2" if variant == "sick" else "white", "ink")
        hline(img, x + off + 1, x + off + 22, yy - 1, "grey3")
    top = y - n * 2
    rect(img, x, top - 1, 24, 3, "white", "ink")
    for k in range(2):
        hline(img, x + 3, x + 20 - k * 6, top, "grey2")
    px(img, x + 20, top, "red2")


def job_card(img, x, y, variant):
    """new job card lying on the desk facing the visitor: blank (empty fields, no writing)."""
    pts = [(x + 4, y), (x + 33, y), (x + 37, y + 10), (x, y + 10)]
    poly(img, pts, "pale2" if variant == "sick" else "white", "ink")
    poly(img, [(x + 4, y + 1), (x + 33, y + 1), (x + 34, y + 3), (x + 3, y + 3)], "red2" if variant != "sick" else "red1")
    for k, yy in enumerate((y + 5, y + 7)):
        hline(img, x + 5 - k, x + 32 + k, yy, "grey3")
    rect(img, x + 3, y + 8, 6, 1, "grey3")                       # empty box for a name
    px(img, x + 35, y + 9, "grey3")


def office_scene(variant, who):
    sick = variant == "sick"
    img = office_base(variant)
    office_window(img, variant)
    if sick:
        wall_clock(img, 156, 48, 3, 0, variant)
        BI.corkboard(img) if False else None
        # a sheet of rules taped up: empty bulletin shadow
        rect(img, 182, 40, 26, 32, "pale2", "ink")
        for k in range(7):
            hline(img, 185, 204 - (k % 3) * 3, 44 + k * 4, "grey2")
        px(img, 195, 40, "red2")
        px(img, 183, 72, "ink")
        # long fluorescent tube, one end dead, with a cold cone of light
        rect(img, 118, 28, 84, 5, "grey2", "ink")
        rect(img, 121, 30, 56, 2, "pale2")
        rect(img, 180, 30, 19, 2, "grey1")
        cone = [(118, 33), (202, 33), (232, 120), (88, 120)]
        m = cmask((W, H), [("p", cone)])
        for y in range(33, 121):
            for x in range(80, 240):
                if m.getpixel((x, y)):
                    t = 1 - (y - 33) / 87
                    if t * 0.38 > _thr(x, y, 4):
                        c = img.getpixel((x, y))
                        if c != col("ink"):
                            img.putpixel((x, y), col("pale1"))
    else:
        wall_clock(img, 156, 48, 6, 0, variant)
        rect(img, 182, 40, 26, 32, "wall1", "ink")                 # tidy corkboard, almost empty
        rect(img, 184, 42, 22, 28, "brown3", "ink")
        rect(img, 190, 46, 10, 8, "white", "ink")
        px(img, 195, 46, "red2")
        # window light spilling over wall and floor (soft stripes)
        for i in range(5):
            y = 91 + i * 6
            BI.ov(img, (176 - i * 6, y, 300, y + 3), "orange4", 0.55 - i * 0.08, 0.1, "x", 4)
        for i in range(4):
            fy = 126 + i * 7
            BI.ov(img, (170 - i * 14, fy, 290 - i * 18, fy + 3), "orange4", 0.4 - i * 0.07, 0.4 - i * 0.07, "y", 4)
    chair_back(img, variant)
    # the person behind the desk
    if who == "sora":
        spec = dict(CAST["sora"], glasses=True, expr="tired")
        spr = chibi(spec, "down", "idle", 0, "tired")
    else:
        spr = chibi(CAST["regular"], "down", "idle", 0, "smile")
        for (x, y) in ((12, 18), (19, 18), (13, 19), (18, 19)):       # shrink the grin to a faint smile
            px(spr, x, y, "pale2")
        px(spr, 13, 18, "ink"); px(spr, 18, 18, "ink")
    paste(img, spr, 144, 73)
    if sick:
        # sickly cast over the person as well
        for y in range(73, 120):
            for x in range(144, 176):
                c = img.getpixel((x, y))
                if c in (col("skin2"), col("skin3")) and 0.5 > _thr(x, y, 4):
                    img.putpixel((x, y), col("pale2"))
    desk_front(img, variant)
    # ---- things on the desk
    if sick:
        rule_stack(img, 108, 116, 8, variant)
        job_card(img, 140, 108, variant)
        # name plate (title only)
        rect(img, 196, 106, 28, 13, "grey3", "ink")
        hline(img, 197, 222, 107, "pale2")
        text(img, 210, 108, "실장", "ink", 9, align="center")
    else:
        # one folded note, a mug, the stack gone
        note = build_note()
        note_big = new(20, 14)
        poly(note_big, [(4, 0), (17, 0), (19, 12), (1, 12)], "wall1", "ink")
        poly(note_big, [(12, 1), (17, 1), (17, 5)], "grey4", "ink")
        line(note_big, [(3, 6), (17, 6)], "grey3")
        for p in ((5, 3), (6, 2), (7, 3), (8, 2), (9, 3), (6, 9), (7, 8), (8, 9), (9, 8), (10, 9), (11, 8)):
            px(note_big, *p, "ink2")
        paste(img, note_big, 148, 105)
        rect(img, 196, 108, 8, 8, "white", "ink"); rect(img, 197, 109, 6, 2, "brown1")
        px(img, 204, 111, "ink"); px(img, 205, 112, "ink")
        for k in range(4):
            px(img, 199 + (k % 2), 105 - k, "grey4")                   # steam
    # contact shadow under the desk
    BI.ov(img, (76, 150, 244, 158), "ink", 0.7, 0.7, "y", 2)
    if sick:
        BI.ov(img, (0, 22, 320, 40), "ink", 0.6, 0.0, "y", 4)
        BI.ov(img, (0, 22, 50, 158), "ink", 0.6, 0.0, "x", 4)
        BI.ov(img, (270, 22, 320, 158), "ink", 0.0, 0.6, "x", 4)
    letterbox(img)
    return img


# ======================================================================
def main():
    build_junho()
    save(build_note(), "props/note.png")
    build_float()
    frames, names = [], []
    for k, p in KW_POSES.items():
        frames.append(kwak_frame(p, p.get("f", 0))); names.append(k)
    frames.append(kwak_defeat()); names.append("defeat_0")
    order = ["idle_0", "idle_1", "tell_0", "lunge_0", "hurt_0", "defeat_0"]
    frames = [frames[names.index(n)] for n in order]
    sheet(frames, "props/kwak_boss", order, cols=6)
    save(build_park(), "bg/park.png")
    save(build_dawn(), "bg/ending_dawn.png")
    save(office_scene("sick", "sora"), "bg/ending_desk.png")
    save(office_scene("soft", "regular"), "bg/ending_note.png")
    files = ["bg/park.png", "bg/ending_dawn.png", "bg/ending_desk.png", "bg/ending_note.png",
             "props/float.png", "props/kwak_boss.png", "characters/junho.png", "props/note.png"]
    for f in files:
        im = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
        print(f, im.size, "off-palette:", off_palette(im) or "none")
    contact(files, "_contact/finale.png", cols=2, scale=2)
    print("ok")


if __name__ == "__main__":
    main()

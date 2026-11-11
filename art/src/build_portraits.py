"""Dialog portraits (64x64 close-ups) for ONE MORE SHIFT.

A small shared rig: head (superellipse rows), eyes / brows / mouths as variants,
hair as a few big shapes (shadow / base / one highlight band), shoulders + outfit.
Everything is built from boolean masks, shaded cel-style with light from top-left,
then outlined with 1px ink per layer.  Output: assets/portraits/<key>.png (+json)
and <key>_<expr>.png singles.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *
import numpy as np

S = 64


# ------------------------------------------------------------------ masks
def M(fn):
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    fn(d)
    return np.array(im) > 0


def sym(pts):
    return list(pts) + [(63 - x, y) for x, y in reversed(pts)]


def mpoly(pts):
    return M(lambda d: d.polygon(pts, fill=255))


def msym(pts):
    return mpoly(sym(pts))


def mboth(pts):
    return mpoly(pts) | mpoly([(63 - x, y) for x, y in pts])


def mrect(x0, y0, x1, y1):
    m = np.zeros((S, S), bool)
    m[y0:y1 + 1, x0:x1 + 1] = True
    return m


def mell(x0, y0, x1, y1):
    return M(lambda d: d.ellipse([x0, y0, x1, y1], fill=255))


def shift(m, dx, dy, edge=False):
    P = np.pad(m, 8, mode="edge" if edge else "constant")
    return P[8 - dy:8 - dy + S, 8 - dx:8 - dx + S]


def dilate(m, r=1):
    o = m.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            o |= shift(m, dx, dy)
    return o


def erode4(m):
    return m & shift(m, 1, 0) & shift(m, -1, 0) & shift(m, 0, 1) & shift(m, 0, -1)


def layer(mask, base, shade=None, hi=None, so=(3, 2), hio=(2, 4), hirect=None, extra=None):
    a = np.zeros((S, S, 4), np.uint8)
    a[mask] = col(base)
    sm = np.zeros((S, S), bool)
    if shade:
        sm = mask & ~shift(mask, -so[0], -so[1], edge=True)
        if extra is not None:
            sm |= extra & mask
        a[sm] = col(shade)
    if hi:
        band = mask & ~shift(mask, hio[1], hio[1]) & shift(mask, hio[0], hio[0]) & ~sm
        if hirect:
            r = mrect(*hirect)
            band &= r
        a[band] = col(hi)
    return Image.fromarray(a, "RGBA")


def paint(img, mask, c):
    cc = col(c)
    for y, x in np.argwhere(mask):
        img.putpixel((int(x), int(y)), cc)


def alpha(img):
    return np.array(img)[:, :, 3] > 0


def put(fig, im):
    fig.alpha_composite(outline(im))


# ------------------------------------------------------------------- head
def head_mask(hw=15.5, top=11, chin=45, p=2.0, cy=27):
    m = np.zeros((S, S), bool)
    for y in range(top, chin + 1):
        if y <= cy:
            u = (cy - y) / (cy - top)
            w = hw * (1 - u ** 2) ** 0.5
        else:
            u = (y - cy) / (chin - cy)
            w = hw * (1 - u ** p) ** (1 / p)
        n = int(w + 0.5)
        if n > 0:
            m[y, 32 - n:32 + n] = True
    return m


# ------------------------------------------------------------------- hair
def hair_shapes(st):
    """returns (back_mask or None, front_mask, extras dict)"""
    ex = {}
    if st == "bob":
        back = msym([(31, 4), (24, 5), (17, 8), (12, 14), (10, 24), (10, 36), (11, 44), (14, 47), (18, 45), (31, 45)])
        front = msym([(31, 5), (24, 6), (18, 9), (14, 14), (12, 22), (11, 33), (12, 43), (15, 46), (18, 44),
                      (19, 36), (19, 26), (21, 22), (25, 21), (28, 20), (31, 21)])
        ex["hirect"] = (12, 5, 46, 17)
    elif st == "slick":
        back = None
        front = msym([(31, 5), (24, 6), (18, 8), (15, 13), (14, 20), (14, 27), (17, 27), (17, 22), (18, 18),
                      (21, 15), (26, 14), (31, 17)])
        ex["hirect"] = (14, 5, 50, 16)
    elif st == "short":
        back = None
        front = msym([(31, 5), (24, 6), (18, 8), (14, 13), (13, 20), (13, 28), (16, 29), (17, 21), (19, 19),
                      (21, 23), (24, 19), (27, 23), (30, 20), (31, 22)])
        ex["hirect"] = (13, 5, 48, 16)
    elif st == "ponytail":
        tail = mpoly([(45, 10), (52, 12), (57, 18), (58, 28), (56, 38), (52, 45), (49, 38), (50, 28), (48, 22), (45, 18)])
        back = tail
        front = msym([(31, 5), (24, 6), (18, 8), (14, 14), (13, 22), (13, 31), (16, 31), (17, 26), (19, 22),
                      (23, 18), (27, 15), (31, 14)])
        ex["hirect"] = (13, 5, 46, 16)
    elif st == "long":
        back = msym([(31, 4), (23, 5), (16, 8), (11, 14), (8, 24), (7, 40), (7, 56), (7, 63), (31, 63)])
        front = msym([(31, 4), (23, 5), (17, 8), (13, 14), (11, 24), (10, 40), (10, 56), (11, 63), (19, 63),
                      (19, 52), (18, 42), (17, 34), (17, 28), (19, 25), (23, 22), (27, 24), (31, 23)])
        ex["hirect"] = (11, 4, 46, 18)
    elif st == "bun":
        back = mell(24, 1, 39, 12)
        front = msym([(31, 7), (24, 8), (18, 11), (15, 16), (14, 23), (14, 30), (17, 30), (17, 24), (19, 19),
                      (24, 16), (31, 15)])
        ex["hirect"] = (14, 1, 48, 14)
    elif st == "cap":
        back = None
        front = mboth([(13, 21), (13, 29), (16, 29), (16, 23)])
        ex["hirect"] = (0, 0, 0, 0)
    return back, front, ex


# ------------------------------------------------------------- face parts
def draw_eye(img, side, kind, o, sp):
    ss = sp["skin"][2]
    ec = sp["eye"]
    L = side == "L"

    def P(x, y, c):
        px(img, x if L else 63 - x, y, c)

    gx = o.get("gx", 0) * (1 if L else -1)
    gy = o.get("gy", 0)
    OPEN = {28: (23, 27), 29: (22, 28), 30: (22, 28), 31: (22, 28), 32: (22, 28), 33: (23, 27)}
    BIG = {26: (23, 27), 27: (22, 28), 28: (21, 28), 29: (21, 28), 30: (21, 28), 31: (21, 28),
           32: (21, 28), 33: (22, 28), 34: (23, 27)}

    def inrows(x, y, rows):
        return y in rows and rows[y][0] <= x <= rows[y][1]

    def fillrows(rows, c):
        for y, (a, b) in rows.items():
            for x in range(a, b + 1):
                P(x, y, c)

    def ring(rows):
        for y, (a, b) in rows.items():
            for x in range(a - 1, b + 2):
                if inrows(x, y, rows):
                    continue
                if inrows(x + 1, y, rows) or inrows(x - 1, y, rows) or inrows(x, y + 1, rows) or inrows(x, y - 1, rows):
                    P(x, y, "ink")
        for x in range(21, 30):
            for y in (rows and [min(rows) - 1, max(rows) + 1]):
                if inrows(x, y + (1 if y < min(rows) else -1), rows):
                    P(x, y, "ink")

    def box(x0, y0, x1, y1, c, rows):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if inrows(x, y, rows):
                    P(x, y, c)

    if kind in ("open", "lid"):
        fillrows(OPEN, "white")
        box(23 + gx, 28 + gy, 27 + gx, 33 + gy, ec, OPEN)
        box(24 + gx, 29 + gy, 26 + gx, 32 + gy, "ink", OPEN)
        if not o.get("nohl"):
            for (x, y) in ((24, 29), (25, 29), (24, 30)):
                if inrows(x + gx, y + gy, OPEN):
                    P(x + gx, y + gy, "white")
        for x in range(22, 29):
            P(x, 27, "ink")
        if sp.get("lash", True):
            P(21, 28, "ink")
        if not o.get("tiredbag"):
            for x in range(23, 28):
                P(x, 34, ss)
        if "lid" in o:
            y0, sl = o["lid"]
            for x in range(22, 29):
                cy = int(round(y0 + sl * (x - 22) / 6.0))
                for y in range(27, cy):
                    P(x, y, ss)
                P(x, cy, "ink")
            if sp.get("lash", True) and o["lid"][1] <= 0:
                P(21, o["lid"][0] - 0, "ink")
        if o.get("tiredbag"):
            for x in range(22, 28):
                P(x, 35, ss)
            for x in range(23, 27):
                P(x, 36, ss)
    elif kind in ("big", "stare"):
        fillrows(BIG, "white")
        ring(BIG)
        if kind == "big":
            box(22 + gx, 27 + gy, 27 + gx, 32 + gy, ec, BIG)
            box(23 + gx, 28 + gy, 26 + gx, 31 + gy, "ink", BIG)
            for (x, y) in ((23, 28), (24, 28), (23, 29)):
                P(x + gx, y + gy, "white")
        elif o.get("small"):
            box(23 + gx, 28 + gy, 26 + gx, 31 + gy, ec, BIG)
            box(24 + gx, 29 + gy, 25 + gx, 30 + gy, "ink", BIG)
        else:
            box(24 + gx, 30 + gy, 25 + gx, 31 + gy, "ink", BIG)
    elif kind == "arc_up":
        for (x, y) in [(22, 32), (23, 31), (24, 30), (25, 30), (26, 30), (27, 31), (28, 32)]:
            P(x, y, "ink")
        if o.get("thick"):
            for (x, y) in [(22, 33), (23, 32), (24, 31), (25, 31), (26, 31), (27, 32), (28, 33)]:
                P(x, y, "ink")
    elif kind == "arc_down":
        for (x, y) in [(22, 30), (23, 31), (24, 32), (25, 32), (26, 32), (27, 31), (28, 30)]:
            P(x, y, "ink")
        P(21, 29, "ink")
    elif kind == "oval":      # entity: solid ink eyes
        rows = {27: (23, 27), 28: (22, 28), 29: (22, 28), 30: (22, 28), 31: (22, 28), 32: (22, 28),
                33: (22, 28), 34: (23, 27)}
        fillrows(rows, "ink")
        if o.get("red"):
            P(24, 29, "red3")
            P(24, 30, "red3")
        for x in range(22, 29):
            P(x, 26, sp["skin"][2])
            P(x, 35, sp["skin"][2])


BROWS = {
    "flat": [(21, 24), (22, 24), (23, 24), (24, 24), (25, 24), (26, 24), (27, 24), (28, 24)],
    "arch": [(21, 25), (22, 24), (23, 23), (24, 23), (25, 23), (26, 23), (27, 24), (28, 25)],
    "worried": [(21, 26), (22, 26), (23, 25), (24, 25), (25, 24), (26, 24), (27, 23), (28, 23)],
    "angry": [(21, 22), (22, 22), (23, 23), (24, 23), (25, 24), (26, 24), (27, 25), (28, 25)],
    "determined": [(21, 23), (22, 23), (23, 23), (24, 24), (25, 24), (26, 24), (27, 25), (28, 25)],
    "tired": [(21, 26), (22, 25), (23, 25), (24, 25), (25, 25), (26, 25), (27, 24), (28, 24)],
}


def draw_brow(img, side, kind, sp, dy=0, thick=False):
    c = sp["brow"]
    pts = BROWS[kind]
    for (x, y) in pts:
        xx = x if side == "L" else 63 - x
        px(img, xx, y + dy, c)
        if thick and 22 <= x <= 27:
            px(img, xx, y + dy + 1, c)


def draw_mouth(img, kind, sp):
    ss = sp["skin"][2]
    deep = sp["skin"][3]

    def P(x, y, c):
        px(img, x, y, c)

    def PM(x, y, c):
        px(img, x, y, c)
        px(img, 63 - x, y, c)

    if kind == "neutral":
        for x in range(29, 32):
            PM(x, 40, deep)
        PM(31, 41, ss)
    elif kind == "smile":
        for x in range(29, 32):
            PM(x, 41, "ink")
        PM(28, 40, "ink")
    elif kind == "bigsmile":
        for x in range(29, 32):
            PM(x, 41, "ink")
        PM(28, 40, "ink")
        PM(27, 39, "ink")
        PM(31, 42, ss)
    elif kind == "gentle":
        for x in range(29, 32):
            PM(x, 41, deep)
        PM(28, 40, deep)
    elif kind == "laugh":
        for x in range(26, 32):
            PM(x, 38, "ink")
        PM(26, 39, "ink"); PM(27, 40, "ink"); PM(28, 41, "ink")
        for x in range(27, 32):
            PM(x, 39, "white")
        for x in range(28, 32):
            PM(x, 40, "red0")
        for x in range(29, 32):
            PM(x, 41, "red0")
        for x in range(30, 32):
            PM(x, 41, "red3")
        for x in range(29, 32):
            PM(x, 42, "ink")
    elif kind == "scared":
        for x in range(29, 32):
            PM(x, 39, "ink")
        for y in (40, 41):
            PM(28, y, "ink")
            for x in range(29, 32):
                PM(x, y, "red0")
        for x in range(29, 32):
            PM(x, 40, "white")
        for x in range(29, 32):
            PM(x, 42, "ink")
    elif kind == "oh":
        for x in range(30, 32):
            PM(x, 39, "ink")
        for y in (40, 41, 42):
            PM(29, y, "ink")
            for x in range(30, 32):
                PM(x, y, "red0")
        for x in range(30, 32):
            PM(x, 43, "ink")
        PM(30, 42, "red3"); PM(31, 42, "red3")
    elif kind == "tired":
        for x in range(29, 32):
            PM(x, 40, "ink2" if "ink2" else "ink")
        PM(28, 41, "ink2")
    elif kind == "firm":
        for x in range(28, 32):
            PM(x, 40, "ink")
        PM(28, 41, "ink")
        PM(31, 42, ss)
    elif kind == "smirk":
        for x in range(28, 34):
            P(x, 41, "ink")
        P(34, 40, "ink"); P(35, 39, "ink"); P(36, 39, "ink")
        P(27, 40, "ink")
        P(31, 42, ss)
    elif kind == "grit":
        for x in range(28, 36):
            P(x, 39, "ink"); P(x, 42, "ink")
        for y in (40, 41):
            P(27, y, "ink"); P(36, y, "ink")
            for x in range(28, 36):
                P(x, y, "white")
        for x in (30, 33):
            P(x, 40, "ink"); P(x, 41, "ink")
        for x in range(28, 36):
            P(x, 41 if x in (28, 35) else 41, "white") if x in (28, 35) else None
    elif kind == "drunk":
        for (x, y) in [(27, 40), (28, 41), (29, 41), (30, 40), (31, 40), (32, 41), (33, 41), (34, 40), (35, 39)]:
            P(x, y, "ink")
        for (x, y) in [(30, 42), (31, 42), (32, 42)]:
            P(x, y, "red3")
    elif kind == "thin":
        for x in range(29, 32):
            PM(x, 41, "ink2")
        PM(28, 40, "ink2")
    elif kind == "flatline":
        for x in range(28, 32):
            PM(x, 41, "ink2")
    elif kind == "grin":
        for x in range(20, 44):
            dx = abs(x - 31.5)
            yt = 39 - int(round(4 * (dx / 12.0) ** 2))
            yb = 42 - int(round(7 * (dx / 12.0) ** 1.5))
            if yb < yt:
                yb = yt
            P(x, yt - 1, "ink")
            P(x, yb + 1, "ink")
            for y in range(yt, yb + 1):
                P(x, y, "white")
            if yb - yt >= 3:
                P(x, (yt + yb) // 2 + 0, "grey3")
        for k in (1.5, 4.5, 7.5, 10.5):
            for x in (int(31.5 - k), int(31.5 + k)):
                dx = abs(x - 31.5)
                yt = 39 - int(round(4 * (dx / 12.0) ** 2))
                yb = 42 - int(round(7 * (dx / 12.0) ** 1.5))
                for y in range(yt - 1, max(yt, yb) + 2):
                    P(x, y, "ink")
        P(19, 34, "ink"); P(44, 34, "ink")
        P(19, 35, "ink"); P(44, 35, "ink")


# ------------------------------------------------------------------ bodies
def body(sp, face_m):
    o = sp["outfit"]
    sk = sp["skin"]
    tc, ts = sp["top"]
    sh_poly = [(31, 47), (25, 47), (19, 48), (12, 51), (8, 56), (5, 63), (31, 63)]
    shoulders = msym(sh_poly)
    neck_rect = mrect(26, 38, 37, 52)
    hole = np.zeros((S, S), bool)
    if o == "hoodie":
        hole = msym([(31, 46), (27, 46), (24, 49), (25, 53), (31, 55)])
    elif o == "suit":
        hole = msym([(31, 46), (25, 46), (22, 48), (27, 58), (31, 62)])
    elif o == "vest":
        hole = msym([(31, 46), (27, 46), (25, 48), (26, 51), (31, 53)])
    elif o == "floral":
        hole = msym([(31, 46), (26, 46), (24, 49), (26, 53), (31, 55)])
    elif o == "coat":
        hole = msym([(31, 46), (26, 46), (24, 50), (31, 60)])
    skin_m = neck_rect | hole
    chin_shadow = shift(face_m, 0, 5)
    neck = layer(skin_m, sk[1], sk[2], so=(3, 0), extra=chin_shadow)
    bmask = shoulders & ~hole
    bimg = layer(bmask, tc, ts, hi=sp.get("top_hi"), so=(5, 3), hio=(2, 4), hirect=(5, 46, 30, 63))
    over = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # ink line where the body meets the neckline
    edge = bmask & dilate(hole, 1)
    if o != "track":
        paint(bimg, edge, "ink")
    if o == "hoodie":
        rim = dilate(hole, 2) & shoulders & ~hole & ~edge
        paint(bimg, rim, "orange2")
        paint(bimg, rim & shift(rim, -2, -1) & False, "orange2")
        paint(bimg, rim & ~shift(rim, 2, 2), "orange3")   # light rim top-left
        for y in range(55, 62):
            px(over, 28, y, "white"); px(over, 35, y, "white")
        px(over, 28, 62, "grey3"); px(over, 35, 62, "grey3")
        px(over, 28, 55, "ink"); px(over, 35, 55, "ink")
        # pocket-ish seam
        for x in range(14, 20):
            px(over, x, 62, "orange1")
    elif o == "suit":
        shirt = hole & ~mrect(26, 40, 37, 49)
        paint(over, shirt, "white")
        paint(over, shirt & shift(shirt, -3, 0, True) & False, "grey4")
        # collar flaps
        for pts in ([(25, 46), (30, 51), (27, 55), (21, 49)],):
            cl = mboth(pts)
            paint(over, cl, "white")
            paint(over, cl & ~erode4(cl), "ink")
        # neck opening
        # tie
        tie = sp["tie"]
        knot = mrect(30, 51, 33, 53)
        tmask = msym([(31, 53), (30, 54), (29, 60), (31, 63)])
        t_img = layer(knot | tmask, tie, "red1" if tie == "red2" else "orange2", so=(2, 1))
        over.alpha_composite(outline(t_img))
        # lapel crease lines
        for (x0, y0, x1, y1) in [(20, 51, 27, 62), (43, 51, 36, 62)]:
            line(over, [(x0, y0), (x1, y1)], ts if ts != "ink" else "ink")
        # jacket button
        px(over, 31, 63, "ink"); px(over, 32, 63, "ink")
        edge2 = bmask & dilate(hole, 1)
        paint(over, edge2, "ink")
    elif o == "vest":
        tee_rim = dilate(hole, 1) & shoulders & ~hole
        paint(bimg, tee_rim, "grey4")
        paint(bimg, bmask & dilate(hole, 2) & ~dilate(hole, 1) & False, "grey4")
        vl = mpoly([(19, 49), (25, 50), (29, 54), (30, 63), (10, 63), (11, 56)])
        vr = mpoly([(63 - x, y) for x, y in [(19, 49), (25, 50), (29, 54), (30, 63), (10, 63), (11, 56)]])
        vest = (vl | vr) & bmask
        vimg = layer(vest, sp["vest"][0], sp["vest"][1], hi="blue3", so=(3, 2), hirect=(10, 48, 30, 63))
        over.alpha_composite(vimg)
        paint(over, vest & ~erode4(vest) & ~mrect(0, 63, 63, 63), "blue0")
        # tee collar edge ink
        paint(over, edge, "ink")
        for y in range(57, 62, 2):
            px(over, 29, y, "white"); px(over, 34, y, "white")
    elif o == "floral":
        rim = dilate(hole, 1) & shoulders & ~hole
        paint(bimg, rim, "purple2")
        paint(bimg, edge, "ink")
        flowers = [(14, 56), (22, 61), (11, 62), (26, 55), (38, 60), (48, 57), (53, 62), (42, 53), (20, 52), (34, 56)]
        for (fx, fy) in flowers:
            for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                if bmask[fy + dy, fx + dx]:
                    px(bimg, fx + dx, fy + dy, "yellow")
            px(bimg, fx, fy, "orange2")
        for (fx, fy) in [(17, 60), (30, 61), (44, 62), (36, 52), (9, 59)]:
            if bmask[fy, fx]:
                px(bimg, fx, fy, "purple2")
    elif o == "track":
        coll = msym([(31, 48), (25, 47), (23, 48), (24, 53), (31, 54)])
        cimg = layer(coll, "red2", "red1", so=(3, 2))
        trim = coll & ~shift(coll, 0, 2, False)
        paint(cimg, trim, "white")
        over.alpha_composite(outline(cimg))
        for y in range(54, 63):
            px(over, 31, y, "ink2"); px(over, 32, y, "red1")
        px(over, 31, 55, "grey3"); px(over, 31, 56, "grey3")
        # white sleeve stripes
        sl = M(lambda d: (d.line([(18, 49), (12, 52), (9, 57), (7, 63)], fill=255, width=2)))
        paint(over, sl & bmask, "white")
        sr = M(lambda d: (d.line([(63 - 18, 49), (63 - 12, 52), (63 - 9, 57), (63 - 7, 63)], fill=255, width=2)))
        paint(over, sr & bmask, "white")
    elif o == "coat":
        lap = mboth([(25, 46), (31, 60), (27, 63), (19, 56), (21, 49)])
        paint(over, lap & bmask, "ink")
        paint(over, lap & ~erode4(lap) & bmask, "grey1")
        paint(over, (hole & ~mrect(26, 40, 37, 49)) & False, "pale1")
        paint(bimg, edge, "grey1")
        for (bx, by) in [(26, 56), (37, 56), (26, 61), (37, 61)]:
            px(over, bx, by, "red3"); px(over, bx + 1, by, "red2"); px(over, bx, by + 1, "red1")
        for y in range(60, 64):
            px(over, 31, y, "ink"); px(over, 32, y, "ink")
    return neck, bimg, over


# -------------------------------------------------------------------- build
def make_bg(a, b):
    img = new(S, S, a)
    dither_grad(img, (0, 28, S, 50), a, b, "y", 2)
    rect(img, 0, 50, S, 14, b)
    return img


def build(sp, ex):
    fig = new(S, S)
    head = sp.get("head", {})
    face_m = head_mask(**head)
    sk = sp["skin"]
    back, front, hx = hair_shapes(sp["hair_style"])
    hc = sp["hair"]
    cap = sp["hair_style"] == "cap"
    # ---- back hair
    if back is not None:
        put(fig, layer(back, hc[1], hc[0], hc[2], so=(3, 3), hirect=hx["hirect"]))
    # ---- neck / body
    neck, bimg, over = body(sp, face_m)
    put(fig, neck)
    put(fig, bimg)
    fig.alpha_composite(over)
    # ---- ears
    if sp["hair_style"] not in ("long",):
        ears = mboth([(14, 29), (17, 29), (17, 36), (14, 35), (13, 32)])
        eimg = layer(ears, sk[1], sk[2], so=(1, 1))
        put(fig, eimg)
    # ---- face
    fm = layer(face_m, sk[1], sk[2], None, so=(3, 2), extra=None)
    # cast shadow from front hair / cap
    if cap:
        brim = msym([(31, 24), (24, 24), (17, 23), (12, 21), (11, 19), (14, 17), (31, 17)])
        crown = msym([(31, 3), (22, 4), (16, 8), (13, 13), (13, 18), (31, 18)])
        cast_src = brim
    else:
        cast_src = front
    cast = shift(cast_src, 1, 2) & face_m & ~cast_src
    fm_arr = np.array(fm)
    fm_arr[cast] = col(sk[2])
    # skin highlight band
    if sk[0]:
        band = face_m & ~shift(face_m, 4, 4) & shift(face_m, 2, 2) & mrect(16, 14, 30, 38) & ~cast
        fm_arr[band] = col(sk[0])
    put(fig, Image.fromarray(fm_arr, "RGBA"))
    # ---- features
    f = new(S, S)
    e = ex
    kl = e.get("eyeL", e["eye"])
    kr = e.get("eyeR", e["eye"])
    draw_eye(f, "L", kl, e.get("optL", e.get("opt", {})), sp)
    draw_eye(f, "R", kr, e.get("optR", e.get("opt", {})), sp)
    bd = e.get("brow_dy", sp.get("brow_dy", 0))
    if e.get("brow") != "none":
        draw_brow(f, "L", e.get("browL", e["brow"]), sp, e.get("bdyL", bd), sp.get("thick_brow", False) or e.get("thick", False))
        draw_brow(f, "R", e.get("browR", e["brow"]), sp, e.get("bdyR", bd), sp.get("thick_brow", False) or e.get("thick", False))
    # nose
    px(f, 31, 36, sk[3]); px(f, 32, 36, sk[3])
    px(f, 31, 35, sk[2]); px(f, 32, 35, sk[2])
    px(f, 33, 34, sk[2]); px(f, 33, 33, sk[2])
    # wrinkles / age
    for (x, y) in sp.get("wrinkles", []):
        px(f, x, y, sk[2]); px(f, 63 - x, y, sk[2])
    if e.get("bags") or sp.get("bags"):
        pass
    draw_mouth(f, e["mouth"], sp)
    # blush
    bl = e.get("blush", sp.get("blush"))
    if bl:
        lvl = 0.5
        c = "red4" if bl == "soft" else "red3"
        for (x0, x1) in ((18, 23), (40, 45)):
            for y in (37, 38):
                for x in range(x0, x1 + 1):
                    if (x + y) % 2 == 0 and face_m[y, x]:
                        px(f, x, y, c)
    if e.get("nose_red"):
        for (x, y) in ((31, 35), (32, 35), (31, 36), (32, 36), (30, 36), (33, 36)):
            px(f, x, y, "red3" if (x + y) % 2 == 0 else "red4")
    # restrict features to the face
    fa = np.array(f)
    fa[~face_m] = 0
    f = Image.fromarray(fa, "RGBA")
    fig.alpha_composite(f)
    # ---- front hair
    if cap:
        himg = layer(mboth([(13, 21), (13, 29), (16, 29), (16, 23)]), hc[1], hc[0], so=(1, 1))
        put(fig, himg)
        crown_img = layer(crown, "blue1", "blue0", "blue2", so=(3, 3), hirect=(13, 3, 40, 12))
        # logo patch
        patch = mrect(27, 8, 36, 13)
        paint(crown_img, patch, "white")
        paint(crown_img, patch & ~erode4(patch), "grey3")
        px(crown_img, 30, 10, "blue1"); px(crown_img, 33, 10, "blue1"); px(crown_img, 31, 11, "blue1"); px(crown_img, 32, 11, "blue1")
        px(crown_img, 31, 2, "blue2"); px(crown_img, 32, 2, "blue2")
        put(fig, crown_img)
        brim_img = layer(brim, "blue1", "blue0", "blue2", so=(2, 3), hio=(1, 2), hirect=(9, 17, 32, 24))
        put(fig, brim_img)
    else:
        hi_img = layer(front, hc[1], hc[0], hc[2], so=(3, 3), hirect=hx["hirect"])
        extra_lines = sp.get("hair_lines", [])
        for (pts, c) in extra_lines:
            for i in range(len(pts) - 1):
                line(hi_img, [pts[i], pts[i + 1]], c)
                line(hi_img, [(63 - pts[i][0], pts[i][1]), (63 - pts[i + 1][0], pts[i + 1][1])], c)
        # clip lines to the hair mask
        arr = np.array(hi_img)
        arr[~front] = 0
        put(fig, Image.fromarray(arr, "RGBA"))
        if sp["hair_style"] == "ponytail":
            tie = mrect(49, 12, 53, 15)
            ti = layer(tie, "blue2", "blue1", so=(1, 1))
            put(fig, ti)
    # ---- accessories
    acc = new(S, S)
    if sp.get("glasses"):
        for (x0, x1) in ((20, 30), (33, 43)):
            for x in range(x0 + 1, x1):
                px(acc, x, 26, "ink2"); px(acc, x, 35, "ink2")
            for y in range(27, 35):
                px(acc, x0, y, "ink2"); px(acc, x1, y, "ink2")
        px(acc, 31, 29, "ink2"); px(acc, 32, 29, "ink2")
        for x in (17, 18, 19):
            px(acc, x, 28, "ink2")
            px(acc, 63 - x, 28, "ink2")
        if e.get("glint"):
            for (x, y) in [(22, 34), (23, 33), (24, 32), (25, 31), (26, 30), (27, 29), (28, 28), (22, 31), (23, 30), (24, 29)]:
                px(acc, x, y, "blue4")
                px(acc, 63 - x, y, "blue4")
    fig.alpha_composite(acc)
    # ---- extras
    if e.get("sweat"):
        s = new(S, S)
        ox, oy = sp.get("sweat_off", (0, 0))
        for (x, y) in [(45, 20), (44, 21), (45, 21), (46, 21), (44, 22), (45, 22), (46, 22), (45, 23)]:
            px(s, x + ox, y + oy, "blue3")
        px(s, 44 + ox, 21 + oy, "white")
        fig.alpha_composite(outline(s))
    bgimg = make_bg(*sp["bg"])
    if sp.get("bg_extra"):
        sp["bg_extra"](bgimg)
    bgimg.alpha_composite(fig)
    if e.get("glitch"):
        glitch(bgimg)
    return bgimg


def glitch(img):
    a = np.array(img)
    # sheared slice
    for y in range(26, 31):
        a[y, 33:60] = np.roll(a[y, 33:60], 3, axis=0)
    for y in range(41, 44):
        a[y, 20:50] = np.roll(a[y, 20:50], -3, axis=0)
    img2 = Image.fromarray(a, "RGBA")
    poly_pts = [(34, 10), (50, 10), (52, 28), (46, 36), (50, 48), (37, 50), (39, 41), (33, 34), (38, 26), (33, 18)]
    m = mpoly(poly_pts)
    for y, x in np.argwhere(m):
        if (x + y) % 2 == 0:
            img2.putpixel((int(x), int(y)), col("red2"))
        else:
            img2.putpixel((int(x), int(y)), col("ink"))
        if y % 9 in (0, 1) and (x + y) % 2 == 1:
            img2.putpixel((int(x), int(y)), col("red3"))
    # leave an intact eye fragment
    for (x, y) in ((40, 29), (41, 29), (40, 30)):
        img2.putpixel((x, y), col("red4"))
    # dither feathering on the left edge of the tear
    for y in range(12, 49):
        for x in range(28, 34):
            if m[y, x + 1 if x + 1 < S else x] and not m[y, x] and (x + y) % 4 == 0 and a[y, x, 3]:
                img2.putpixel((x, y), col("red1"))
    img.paste(img2, (0, 0))


# ------------------------------------------------------------------- cast
def ramp_hair(sh, ba, hi):
    return (sh, ba, hi)


SK = ("skin3", "skin2", "skin1", "skin0")
SKP = (None, "pale2", "pale1", "grey2")

CAST = {
    "sora": dict(skin=SK, eye="brown1", brow="purple0", hair_style="bob", hair=("purple0", "purple1", "purple2"),
                 outfit="hoodie", top=("orange3", "orange2"), top_hi="orange4", bg=("wall4", "orange4"),
                 blush="soft",
                 hair_lines=[([(24, 8), (22, 14), (21, 19)], "purple0")],
                 head=dict(hw=15.5, chin=45, p=2.0)),
    "kwak": dict(skin=SK, eye="brown0", brow="grey1", hair_style="slick", hair=("grey1", "grey2", "grey4"),
                 outfit="suit", top=("green0", "ink2"), top_hi="green1", tie="yellow", glasses=True, lash=False,
                 bg=("brown3", "brown2"), thick_brow=True,
                 wrinkles=[(24, 38), (24, 39), (25, 40)],
                 hair_lines=[([(30, 7), (22, 9), (17, 13)], "grey3"), ([(30, 10), (24, 11), (19, 15)], "grey3")],
                 head=dict(hw=15.5, chin=46, p=2.6)),
    "deokgu": dict(skin=SK, eye="brown0", brow="brown0", hair_style="cap", hair=("brown0", "brown1", "brown2"),
                   outfit="vest", top=("white", "grey4"), vest=("blue2", "blue1"), top_hi=None, lash=False,
                   bg=("orange4", "orange3"), brow_dy=1, thick_brow=True, sweat_off=(4, 8),
                   head=dict(hw=15.5, chin=45, p=2.2)),
    "halmae": dict(skin=SK, eye="brown0", brow="grey2", hair_style="bun", hair=("grey2", "grey3", "white"),
                   outfit="floral", top=("purple1", "purple0"), top_hi="purple2", bg=("wall4", "orange4"),
                   wrinkles=[(24, 37), (23, 38), (24, 39), (19, 31), (19, 33)], blush="soft",
                   hair_lines=[([(30, 11), (24, 12), (19, 16)], "grey2")],
                   head=dict(hw=15.5, chin=45, p=1.9)),
    "daeri": dict(skin=SK, eye="brown0", brow="ink2", hair_style="short", hair=("ink", "ink2", "grey1"),
                  outfit="suit", top=("blue0", "ink2"), top_hi="blue1", tie="red2", lash=False,
                  bg=("wall3", "blue3"), thick_brow=True,
                  head=dict(hw=15.5, chin=46, p=2.4)),
    "jisu": dict(skin=SK, eye="brown0", brow="brown0", hair_style="ponytail", hair=("brown0", "brown1", "brown2"),
                 outfit="track", top=("red2", "red1"), top_hi="red3", bg=("yellow2", "orange4"), blush="soft",
                 head=dict(hw=15.5, chin=45, p=2.0)),
    "regular": dict(skin=SKP, eye="ink", brow="ink", hair_style="long", hair=("ink", "ink", "ink2"),
                    outfit="coat", top=("ink2", "ink"), top_hi="grey1", bg=("red1", "red0"), lash=False,
                    head=dict(hw=14.5, chin=47, p=2.0)),
}

EXPR = {
    "sora": {
        "neutral": dict(eye="open", brow="flat", mouth="neutral"),
        "scared": dict(eye="big", opt=dict(), brow="worried", brow_dy=-1, mouth="scared", sweat=True),
        "tired": dict(eye="open", opt=dict(lid=(29, 0), tiredbag=True, gy=1), brow="tired", brow_dy=1, mouth="tired"),
        "determined": dict(eye="open", opt=dict(lid=(27, 2)), brow="determined", mouth="firm"),
        "relieved": dict(eye="arc_down", brow="arch", mouth="smile", blush="soft"),
    },
    "kwak": {
        "smile": dict(eye="arc_up", brow="arch", mouth="bigsmile"),
        "serious": dict(eye="open", opt=dict(lid=(27, 1)), brow="flat", mouth="firm"),
        "sly": dict(eye="open", opt=dict(lid=(30, 0), gx=-1), brow="flat", browR="arch", bdyR=-2, bdyL=1,
                    mouth="smirk", glint=True),
        "angry": dict(eye="open", opt=dict(lid=(27, 3)), brow="angry", mouth="grit"),
    },
    "deokgu": {
        "tired": dict(eye="open", opt=dict(lid=(29, -1), tiredbag=True, gy=1), brow="tired", mouth="tired"),
        "scared": dict(eye="big", brow="worried", brow_dy=0, mouth="scared", sweat=True),
        "laugh": dict(eye="arc_up", opt=dict(thick=True), brow="arch", mouth="laugh"),
    },
    "halmae": {
        "smile": dict(eye="arc_up", opt=dict(thick=True), brow="arch", mouth="bigsmile", blush="soft"),
        "stare": dict(eye="stare", brow="flat", brow_dy=-1, mouth="flatline", blush=None),
    },
    "daeri": {
        "tired": dict(eye="open", opt=dict(lid=(29, 0), tiredbag=True, gy=1), brow="tired", mouth="tired"),
        "drunk": dict(eye="open", opt=dict(lid=(30, -1), gx=1, nohl=True), brow="tired", brow_dy=-1,
                      mouth="drunk", blush="hard", nose_red=True),
    },
    "jisu": {
        "neutral": dict(eye="open", brow="flat", mouth="neutral"),
        "surprised": dict(eye="big", brow="arch", brow_dy=-1, mouth="oh"),
    },
    "regular": {
        "smile": dict(eye="oval", opt=dict(red=True), brow="none", mouth="grin"),
        "blank": dict(eye="oval", brow="none", mouth="flatline"),
        "glitch": dict(eye="oval", opt=dict(red=True), brow="none", mouth="flatline", glitch=True),
    },
}


def main():
    keys = []
    for key, sp in CAST.items():
        frames, names = [], []
        for name, ex in EXPR[key].items():
            im = build(sp, ex)
            bad = off_palette(im)
            assert not bad, (key, name, bad)
            frames.append(im)
            names.append(name)
            save(im, f"portraits/{key}_{name}.png")
            keys.append(f"portraits/{key}_{name}.png")
        sheet(frames, f"portraits/{key}", names, cols=5)
    contact(keys, "_contact/portraits.png", cols=5, scale=3)
    print("ok", len(keys))


if __name__ == "__main__":
    main()

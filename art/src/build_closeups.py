"""Cinematic close-up cutscene shots + gig title cards for ONE MORE SHIFT.

Regenerates everything in assets/cutscenes/:
  cu_sora_phone, cu_kwak_offer, cu_junho, cu_regular, cu_sora_relief, cu_sora_desk
  tc_store, tc_event, tc_milk, tc_cinema, tc_trial, tc_site, tc_park
All 320x180 with the standard 22px letterbox bars. Palette names only, ordered dither, 1px ink outlines.
Characters are built from boolean masks (as in build_portraits.py), cel shaded (base + shadow + highlight,
shadow edge dithered), outlined per layer.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *
from pxkit import _thr, _B4, _B2
import numpy as np

SW, SH = 320, 180
YY, XX = np.mgrid[0:SH, 0:SW]
T4 = np.array([[(_B4[y % 4][x % 4] + 0.5) / 16.0 for x in range(4)] for y in range(4)])
T4 = np.tile(T4, (SH // 4 + 1, SW // 4 + 1))[:SH, :SW]
T2 = np.array([[(_B2[y % 2][x % 2] + 0.5) / 4.0 for x in range(2)] for y in range(2)])
T2 = np.tile(T2, (SH // 2 + 1, SW // 2 + 1))[:SH, :SW]
CHK = ((XX + YY) % 2 == 0)


# ------------------------------------------------------------------ masks
def MK(fn):
    im = Image.new("L", (SW, SH), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    fn(d)
    return np.array(im) > 0


def mpoly(pts):
    return MK(lambda d: d.polygon([(int(x), int(y)) for x, y in pts], fill=255))


def mell(x0, y0, x1, y1):
    return MK(lambda d: d.ellipse([x0, y0, x1, y1], fill=255))


def mrect(x0, y0, x1, y1):
    m = np.zeros((SH, SW), bool)
    m[max(0, y0):max(0, y1 + 1), max(0, x0):max(0, x1 + 1)] = True
    return m


def mline(pts, w=1):
    return MK(lambda d: d.line([(int(x), int(y)) for x, y in pts], fill=255, width=w))


def ell_pts(cx, cy, rx, ry, a0, a1, n=24):
    """points along an ellipse from angle a0..a1 degrees (0=right, 90=down)."""
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def mirror_pts(pts, cx):
    return [(2 * cx - x, y) for x, y in pts]


def sh(m, dx, dy, edge=True):
    """out[y,x] = m[y-dy, x-dx]  (edge-replicated so canvas borders do not create fake rims)."""
    P = np.pad(m, 40, mode="edge" if edge else "constant")
    return P[40 - dy:40 - dy + SH, 40 - dx:40 - dx + SW]


def dil(m, r=1):
    o = m.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if abs(dx) + abs(dy) <= r:
                o |= sh(m, dx, dy, edge=False)
    return o


def ero(m, r=1):
    return ~dil(~m, r)


def dthr(level, m=4):
    t = T4 if m == 4 else T2
    return level > t


# ----------------------------------------------------------------- canvas
class CV:
    def __init__(self, fill="ink"):
        self.img = new(SW, SH, fill)

    def paint(self, mask, c):
        cc = col(c)
        a = np.array(self.img)
        a[mask] = cc
        self.img = Image.fromarray(a, "RGBA")

    def dth(self, mask, c, level, m=4):
        """ordered-dither c over mask at density level (float or HxW array)."""
        lv = level if isinstance(level, np.ndarray) else np.full((SH, SW), level)
        self.paint(mask & dthr(lv, m), c)

    def alpha_mask(self):
        return np.array(self.img)[:, :, 3] > 0

    def layer(self, mask, base, shade=None, hi=None, sd=(3, 3), hd=(2, 2), dith=True, ol="ink",
              extra_shade=None, extra_hi=None, hi2=None, sd2=None, flat_shade=None, keep=None, olmask=True):
        """cel-shaded, outlined object. light from top-left unless sd/hd say otherwise.
        sd: shadow offset (band on the side opposite the light), hd: highlight offset.
        extra_shade/extra_hi: extra boolean regions (cast shadows) painted on top."""
        a = np.zeros((SH, SW, 4), np.uint8)
        a[mask] = col(base)
        sm = np.zeros((SH, SW), bool)
        if shade:
            sm = mask & ~sh(mask, -sd[0], -sd[1])
            if dith:
                sg = lambda v: (v > 0) - (v < 0)
                fr = mask & ~sm & ~sh(mask, -(sd[0] + 2 * sg(sd[0])), -(sd[1] + 2 * sg(sd[1]))) & CHK
                a[fr] = col(shade)
            a[sm] = col(shade)
        if flat_shade is not None and shade:
            fs = flat_shade & mask
            a[fs] = col(shade)
            sm = sm | fs
        if extra_shade is not None and shade:
            e = extra_shade & mask
            a[e] = col(shade)
            sm = sm | e
        if hi:
            hm = mask & ~sh(mask, hd[0], hd[1]) & ~sm
            a[hm] = col(hi)
        if extra_hi is not None and hi:
            e = extra_hi & mask & ~sm
            a[e] = col(hi)
        if hi2 is not None:
            a[hi2[0] & mask] = col(hi2[1])
        L = Image.fromarray(a, "RGBA")
        if ol:
            L = outline(L, ol)
        self.img.alpha_composite(L)
        return mask

    def pts(self, pl, c):
        for x, y in pl:
            px(self.img, int(x), int(y), c)

    def save(self, name, bars=True):
        im = self.img
        if bars:
            letterbox(im)
        bad = off_palette(im)
        assert not bad, (name, bad)
        save(im, f"cutscenes/{name}.png")
        return f"cutscenes/{name}.png"


def tint_mask(cv, mask, c, level, m=4):
    cv.dth(mask, c, level, m)


def glow(cv, cx, cy, r, stops, only=None, m=4, power=1.0):
    """light pass: overlays palette colours with dither on pixels (optionally only where `only`).
    stops: list of (colour, strength) painted from far (weak) to near (strong)."""
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2) / r
    fall = np.clip(1 - d, 0, 1) ** power
    msk = (d < 1) if only is None else ((d < 1) & only)
    for c, s in stops:
        cv.paint(msk & dthr(fall * s, m), c)


def vgrad(y0, y1, a=0.0, b=1.0):
    return np.clip(a + (b - a) * (YY - y0) / max(1, (y1 - y0)), 0, 1)


def hgrad(x0, x1, a=0.0, b=1.0):
    return np.clip(a + (b - a) * (XX - x0) / max(1, (x1 - x0)), 0, 1)


def bokeh(cv, x, y, r, c, c2=None, lv=0.5, rim=0.9, m=4):
    disc = mell(x - r, y - r, x + r, y + r)
    inner = ero(disc, 1)
    cv.dth(inner, c, lv, m)
    cv.dth(disc & ~inner, c2 or c, rim, m)


def stripes_light(cv, y0, y1, period, thick, slope, c, mask=None):
    ph = (YY + XX * slope) % period
    m = (ph < thick) & (YY >= y0) & (YY < y1)
    if mask is not None:
        m &= mask
    cv.paint(m, c)
    return m


# --------------------------------------------------------------- the face rig
# skin ramps: (hi, base, shade, deep)
SKIN = dict(hi="skin3", base="skin2", sh="skin1", deep="skin0")


def head_mask(cx, yt, h, hw, jaw=2.0, cheek=0.44):
    m = np.zeros((SH, SW), bool)
    cy = yt + int(h * cheek)
    yc = yt + h
    for y in range(yt, yc + 1):
        if y <= cy:
            u = (cy - y) / max(1, (cy - yt))
            w = hw * max(0, 1 - u ** 2) ** 0.5
        else:
            u = (y - cy) / max(1, (yc - cy))
            w = hw * max(0, 1 - u ** jaw) ** (1 / jaw)
        n = int(w + 0.5)
        if n > 0:
            m[y, cx - n:cx + n + 1] = True
    return m


def eye(cv, x, y, side, w=9, h=10, iris="brown1", iris2="brown2", lid=0, look=(0, 0), hl="white",
        dull=False, lashes=True, skin_sh="skin1", wide=False, hl2=True, lidc=None, bag=False, white="white",
        slant=0):
    """anime eye centred x,y. side -1 = left eye on screen, +1 = right. lid = rows covered from top."""
    x0, x1 = x - w // 2, x + w // 2
    y0, y1 = y - h // 2, y + h // 2
    E = mell(x0, y0, x1, y1)
    if slant:   # outer corner raised (slant>0) / lowered
        pass
    openm = E & (YY >= y0 + lid)
    cv.paint(openm, white)
    # shade under the lid
    cv.paint(openm & (YY < y0 + lid + 2) & dthr(0.7, 2), "grey3")
    # iris
    ix, iy = x + look[0], y + look[1] + (1 if lid else 0)
    iw = w - 4 if w > 9 else w - 3
    ih = h - 1 if not wide else h
    I = mell(ix - iw // 2, iy - ih // 2, ix + iw // 2, iy + ih // 2) & openm
    cv.paint(I, iris)
    low = I & (YY >= iy + 1)
    cv.paint(low, iris2)
    cv.paint(I & (YY <= iy - ih // 2 + 2), "ink")            # top of iris shadowed by lid
    cv.paint(I & (YY == iy - ih // 2 + 3), iris)
    cv.paint(I & (YY == iy - ih // 2 + 3) & CHK, "ink")
    cv.paint(I & (YY >= iy + ih // 2 - 1) & CHK, iris2) if False else None
    pu = mell(ix - 1, iy - 2, ix + 1, iy + 1) & openm
    cv.paint(pu, "ink")
    if dull:
        cv.paint(I, "ink2")
        cv.paint(I & (YY >= iy + 2) & CHK, "grey1")
    elif hl:
        cv.pts([(ix - 2, iy - 2), (ix - 1, iy - 2), (ix - 2, iy - 1), (ix - 1, iy - 1)], hl)
        if hl2:
            cv.pts([(ix + 1, iy + 2)], hl)
    # lid skin
    lidm = E & (YY < y0 + lid)
    if lid:
        cv.paint(lidm, lidc or skin_sh)
    # lashes (upper outline thick) + flick
    top = E & ~sh(E, 0, 1, edge=False)
    if lid:
        top = openm & ~sh(openm, 0, 1, edge=False)
    top2 = top | sh(top, 0, -1, edge=False)
    cv.paint(top2 & (XX >= x0) & (XX <= x1), "ink")
    if lashes:
        ox = x1 + 1 if side > 0 else x0 - 1
        cv.pts([(ox, (y0 + lid) + 1), (ox, (y0 + lid))], "ink")
        cv.pts([(ox + (1 if side > 0 else -1), (y0 + lid))], "ink")
    # lower lash line / bag
    if bag:
        low = E & ~sh(E, 0, -1, edge=False)
        cv.paint(sh(low, 0, 2, edge=False) & ~E & (XX >= x0 + 1) & (XX <= x1 - 1), skin_sh)


def eye_closed(cv, x, y, side, w=9, up=True, thick=2, c="ink"):
    pl = []
    for i in range(w):
        t = (i - (w - 1) / 2) / ((w - 1) / 2)
        d = round(2.0 * (1 - t * t))
        yy = y - d if up else y + d
        pl.append((x - w // 2 + i, yy))
    for (px_, py_) in pl:
        for k in range(thick):
            px(cv.img, px_, py_ + k, c)
    ox = x + (w // 2 + 1) * side
    px(cv.img, ox, y + (1 if up else -1), c)


def brow(cv, x, y, side, w=9, tilt=0, c="purple0", thick=1, arch=0):
    """tilt>0: inner end lower (angry/determined). tilt<0: inner end higher (worried)."""
    for i in range(w):
        t = i / (w - 1)           # 0 outer ... 1 inner (relative)
        yy = y + round(tilt * t) - round(arch * 4 * t * (1 - t))
        xx = x + (i - w // 2) * (-side)   # i=0 outer for side=-1 is leftmost
        for k in range(thick):
            px(cv.img, xx, yy + k, c)


def mouth(cv, x, y, kind, c="skin0", teeth="white", lip="red2"):
    P = lambda dx, dy, cc=c: px(cv.img, x + dx, y + dy, cc)
    if kind == "flat":
        for dx in range(-3, 4): P(dx, 0)
    elif kind == "small":
        for dx in range(-2, 3): P(dx, 0)
        P(-3, -1); P(3, -1)
    elif kind == "firm":
        for dx in range(-3, 4): P(dx, 0)
        P(-4, 1); P(4, 1)
    elif kind == "down":
        for dx in range(-2, 3): P(dx, 0)
        P(-3, 1); P(3, 1)
    elif kind == "smile":
        for dx in range(-3, 4): P(dx, 0)
        P(-4, -1); P(4, -1)
        for dx in range(-2, 3): P(dx, 1, lip)
    elif kind == "faint":
        for dx in range(-3, 4): P(dx, 0)
        P(-4, -1); P(4, -1); P(-5, -2, "skin1") if False else None
    elif kind == "grin":         # wide, teeth
        for dx in range(-6, 7): P(dx, 0)
        for dx in range(-5, 6):
            P(dx, 1, teeth)
        for dx in range(-4, 5):
            P(dx, 2, teeth)
        for dx in range(-3, 4): P(dx, 3)
        P(-7, -1); P(7, -1)
        for dx in (-2, 0, 2): P(dx, 1, "grey3")
    elif kind == "grin2":
        for dx in range(-8, 9): P(dx, 0)
        P(-9, -1); P(9, -1); P(-10, -2)  ; P(10, -2)
        for dx in range(-7, 8): P(dx, 1, teeth)
        for dx in range(-6, 7): P(dx, 2, teeth)
        for dx in range(-4, 5): P(dx, 3, teeth)
        for dx in range(-3, 4): P(dx, 4)
        for dx in (-4, -1, 2, 5): P(dx, 1, "grey3"); P(dx, 2, "grey3")
    elif kind == "soft":
        for dx in range(-2, 3): P(dx, 0)
        P(-3, -1); P(3, -1)
    elif kind == "open":
        for dx in range(-2, 3): P(dx, 0)
        for dx in range(-1, 2): P(dx, 1, "red1")
        for dx in range(-2, 3): P(dx, 2)


# ============================================================ SORA (shared)
def K(k, *v):
    return [int(round(a * k)) for a in v]


FRINGE = [(-23, 27), (-19, 17), (-15, 25), (-11, 14), (-7, 23), (-3, 13), (0, 20), (4, 12), (8, 22),
          (12, 14), (16, 24), (20, 17), (23, 28)]


class Head:
    """geometry of a head at centre x=cx, top y=yt, scale k (k=1 -> 40w x 52h)."""
    def __init__(s, cx, yt, k=1.0, hw=20, h=52, jaw=1.9):
        s.cx, s.yt, s.k = cx, yt, k
        s.hw, s.h, s.jaw = int(round(hw * k)), int(round(h * k)), jaw
        s.eye_y = yt + int(round(29 * k))
        s.eye_dx = int(round(10 * k))
        s.mouth_y = yt + int(round(43 * k))
        s.chin = yt + s.h

    def p(s, dx, dy):
        return (s.cx + dx * s.k, s.yt + dy * s.k)

    def pl(s, pts):
        return [s.p(a, b) for a, b in pts]


def sora_masks(H, drop=0):
    k, cx, yt = H.k, H.cx, H.yt
    top = [H.p((x - cx) / k * k * 0 + 0, 0) for x in []]
    top = [(cx + (x - cx) * 1.0, y) for x, y in ell_pts(cx, yt + 22 * k, 24 * k, 27 * k, 180, 360, 28)]
    fr = [H.p(dx, dy + (drop if dy > 20 else 0)) for dx, dy in FRINGE]
    cap = mpoly(top + [H.p(24, 36)] + fr[::-1] + [H.p(-24, 36)])
    L = [(-24, 22), (-14, 20), (-15, 36), (-13, 46), (-11, 56), (-21, 58), (-26, 46)]
    ll = mpoly(H.pl(L))
    lr = mpoly(H.pl([(-x, y) for x, y in L]))
    back = mpoly(H.pl([(-26, 12), (26, 12), (29, 38), (27, 54), (22, 58), (-22, 58), (-27, 54), (-29, 38)]))
    back |= mell(int(cx - 25 * k), int(yt - 4 * k), int(cx + 25 * k), int(yt + 40 * k))
    return cap, ll, lr, back


def sora_hair_back(cv, H, hair, masks):
    cap, ll, lr, back = masks
    cv.layer(back, hair[1], "ink", None, sd=(3, 3), dith=True)


def sora_hair_front(cv, H, hair, masks, sd=(3, 3), hd=(2, 2), ring=True):
    b, s, hi = hair
    cap, ll, lr, back = masks
    k, cx, yt = H.k, H.cx, H.yt
    hm = cap | ll | lr
    cl = np.zeros((SH, SW), bool)
    for dx, dy in FRINGE[1::2]:
        cl |= mline([H.p(dx * 0.55, 1), H.p(dx * 0.85, 9), H.p(dx, dy - 1)], 1)
    for sgn in (-1, 1):
        cl |= mline([H.p(sgn * 21, 24), H.p(sgn * 18, 38), H.p(sgn * 17, 52)], 1)
    ringm = np.zeros((SH, SW), bool)
    if ring:
        a = int(18 * k); 
        ringm = mell(cx - a, int(yt - 3 * k), cx + a, int(yt + 17 * k)) & ~mell(cx - a + 2, int(yt + 1 * k), cx + a - 2, int(yt + 22 * k))
    cv.layer(hm, b, s, hi, sd=sd, hd=hd, extra_shade=cl & ~ringm, extra_hi=ringm, dith=True)
    return hm


def sora_face_base(cv, H, skin, masks, sd=(3, 3), hd=(2, 2), neck_to=None):
    cap, ll, lr, back = masks
    cx, yt, k, hw, h = H.cx, H.yt, H.k, H.hw, H.h
    hmask = head_mask(cx, yt, h, hw, H.jaw)
    ears = mell(cx - hw - 2, yt + int(h * .5), cx - hw + 3, yt + int(h * .5) + int(8 * k)) | \
        mell(cx + hw - 3, yt + int(h * .5), cx + hw + 2, yt + int(h * .5) + int(8 * k))
    nw = int(9 * k)
    nk = mpoly([(cx - nw, yt + h - 14), (cx + nw, yt + h - 14), (cx + nw + 1, yt + h + 22), (cx - nw - 1, yt + h + 22)])
    cv.layer(nk, skin["base"], skin["sh"], None, sd=sd, hd=hd, extra_shade=sh(hmask, 0, int(8 * k)) & nk, dith=True)
    cv.layer(ears, skin["base"], skin["sh"], None, sd=sd, hd=hd)
    extra = sh(cap, 0, 4) | sh(cap, 2, 5) | sh(ll, 4, 0) | sh(lr, -4, 0)
    cv.layer(hmask, skin["base"], skin["sh"], skin["hi"], sd=sd, hd=hd, extra_shade=extra, dith=True)
    return hmask


# ============================================================ 1. SORA PHONE
def sky_bokeh_night(cv, seed=7):
    dither_ramp(cv.img, (0, 22, SW, 158), ["ink", "blue0", "purple0", "blue0"], "y", 4)
    rng = np.random.RandomState(seed)
    x = 0
    sky = np.zeros((SH, SW), bool)
    while x < SW:
        w = int(rng.randint(18, 38)); hh = int(rng.randint(26, 62))
        sky |= mrect(x, 120 - hh, x + w - 1, 158)
        x += w + int(rng.randint(0, 5))
    cv.paint(sky, "ink2")
    cv.dth(sky, "blue0", 0.35, 4)
    for i in range(80):
        wx, wy = int(rng.randint(0, SW - 2)), int(rng.randint(50, 118))
        if sky[wy, wx] and sky[wy + 1, wx + 1]:
            cv.paint(mrect(wx, wy, wx + 1, wy + 1), ["orange3", "yellow", "blue3"][i % 3] if i % 5 else "orange2")
    pal = [("orange3", "orange4"), ("yellow", "yellow2"), ("red3", "red4"), ("orange2", "orange3"),
           ("blue3", "blue4"), ("green2", "green3"), ("red2", "red3"), ("orange3", "yellow")]
    big = [(18, 48, 13), (50, 76, 9), (84, 40, 7), (112, 58, 11), (30, 94, 10), (66, 108, 6), (96, 88, 8),
           (214, 44, 8), (246, 66, 13), (282, 40, 10), (300, 82, 12), (268, 104, 7), (230, 92, 6), (196, 70, 5),
           (130, 34, 5), (186, 36, 6), (305, 120, 9), (12, 124, 8), (258, 128, 5), (80, 128, 5),
           (152, 28, 4), (122, 118, 4), (206, 126, 4)]
    for i, (bx, by, r) in enumerate(big):
        c, c2 = pal[i % len(pal)]
        bokeh(cv, bx, by, r, c, c2, lv=0.42, rim=0.85)
    dither_radial(cv.img, 40, 62, 22, "yellow2", None, 4)
    return sky


def cu_sora_phone():
    cv = CV("ink")
    sky = sky_bokeh_night(cv)
    k = 1.4
    cx, yt = 160, 27
    H = Head(cx, yt, k)
    hair = ("purple0", "ink2", "purple1")
    skin = dict(hi="blue4", base="skin3", sh="skin2", deep="purple1")
    M_ = sora_masks(H)
    sora_hair_back(cv, H, hair, M_)
    sy = H.chin + 6
    L = ell_pts(cx - 52, sy + 30, 34, 30, 180, 270, 12)
    torso = mpoly([(cx - 88, 158), (cx - 86, sy + 30)] + L + [(cx - 20, sy - 2)] + mirror_pts(L[::-1], cx) + [(cx + 86, sy + 30), (cx + 88, 158)])
    hood = mell(cx - 38, H.chin - 10, cx + 38, H.chin + 36)
    cv.layer(hood, "orange0", "ink", None, sd=(0, -3), dith=True)
    folds = mline([(cx - 62, sy + 36), (cx - 70, sy + 70)], 1) | mline([(cx + 62, sy + 36), (cx + 70, sy + 70)], 1) | \
        mline([(cx - 40, sy + 50), (cx - 30, 158)], 1) | mline([(cx + 40, sy + 50), (cx + 30, 158)], 1)
    cv.layer(torso, "orange1", "orange0", "orange2", sd=(0, -6), hd=(0, -2), dith=True, extra_shade=folds)
    fm = sora_face_base(cv, H, skin, M_, sd=(0, -3), hd=(0, -2))
    # hood collar in front of the neck
    col_ = mell(cx - 34, H.chin + 2, cx + 34, H.chin + 38) & ~mell(cx - 17, H.chin - 6, cx + 17, H.chin + 15)
    col_ &= ~fm
    cv.layer(col_, "orange1", "orange0", "orange2", sd=(0, -3), hd=(0, -2), dith=True)
    ey = H.eye_y
    # lighting from below: upper face deeper, lower face icy
    cv.paint(fm & (YY <= ey - 3), "skin2")
    cv.dth(fm & (YY > ey - 3) & (YY < ey + 9), "skin2", 0.5, 2)
    cv.dth(fm & (YY >= ey + 9), "blue4", vgrad(ey + 9, H.chin, 0.1, 0.62))
    cv.dth(fm & (YY < yt + 22), "skin1", 0.5, 2)
    nk_ = cv.alpha_mask() & (XX > cx - 13) & (XX < cx + 13) & (YY > H.chin - 2) & (YY < H.chin + 16) & ~fm & ~col_
    cv.dth(nk_, "blue3", 0.4)
    cv.dth(nk_ & (YY < H.chin + 9), "skin1", 0.5, 2)
    for sd_ in (-1, 1):
        ex = cx + sd_ * H.eye_dx
        eye(cv, ex, ey, sd_, w=13, h=14, iris="brown1", iris2="brown2", lid=3, look=(0, 2), hl="blue4", bag=False,
            skin_sh="skin1", lidc="skin2")
        brow(cv, ex, ey - 11, sd_, 11, tilt=3, c="purple0", thick=1)
    cv.pts([(cx, ey + 13), (cx + 1, ey + 13)], "skin1")
    cv.pts([(cx - 1, ey + 14), (cx, ey + 14)], "blue4")
    mouth(cv, cx, H.mouth_y, "firm", c="skin0")
    cv.pts([(cx - 2, H.mouth_y + 3), (cx - 1, H.mouth_y + 3), (cx, H.mouth_y + 3), (cx + 1, H.mouth_y + 3)], "blue4")
    hm = sora_hair_front(cv, H, hair, M_, sd=(0, -3), hd=(0, -2))
    rimm = hm & ~sh(hm, -2, 1) & (XX > cx + 8)
    cv.paint(rimm, "orange3")
    rimm2 = hm & ~sh(hm, 2, 1) & (XX < cx - 8)
    cv.dth(rimm2, "red3", 0.7)
    cv.pts([(cx - 14, H.chin + 34 + i) for i in range(16)], "grey4")
    cv.pts([(cx + 14, H.chin + 34 + i) for i in range(12)], "grey4")
    glow(cv, cx, 168, 60, [("blue2", 0.45), ("blue3", 0.75)], only=torso & (YY > 120), power=1.4)
    cv.dth(mell(cx - 46, 146, cx + 46, 190) & (YY < 158), "blue3", 0.6)
    cv.paint(mell(cx - 30, 152, cx + 30, 190) & (YY < 158), "blue4")
    hand = mpoly([(cx - 30, 158), (cx - 28, 146), (cx - 20, 138), (cx - 10, 136), (cx - 2, 141), (cx + 6, 138),
                  (cx + 16, 139), (cx + 26, 145), (cx + 32, 158)])
    cv.layer(hand, "skin3", "skin1", "blue4", sd=(0, -5), hd=(0, -2), extra_shade=None)
    for fx in (cx - 14, cx - 3, cx + 9, cx + 20):
        cv.pts([(fx, 143), (fx, 144), (fx, 145), (fx, 146)], "skin1")
    cv.dth(hand, "blue4", 0.35, 2)
    return cv.save("cu_sora_phone")


# ============================================================ 2. KWAK OFFER
def glasses(cv, H, lens_w=18, lens_h=13, dy=0, glint=(True, False), lens_c="blue4"):
    cx, ey = H.cx, H.eye_y + dy
    g = {}
    for sd_ in (-1, 1):
        lx = cx + sd_ * (H.eye_dx + 2)
        x0, x1 = lx - lens_w // 2, lx + lens_w // 2
        y0, y1 = ey - lens_h // 2, ey + lens_h // 2
        L = mpoly([(x0 + 2, y0), (x1 - 2, y0), (x1, y0 + 2), (x1, y1 - 2), (x1 - 2, y1), (x0 + 2, y1), (x0, y1 - 2), (x0, y0 + 2)])
        g[sd_] = (L, x0, x1, y0, y1)
    return g


def draw_glasses_frame(cv, g, H, frame="ink"):
    for sd_, (L, x0, x1, y0, y1) in g.items():
        ring = dil(L, 1) & ~L
        cv.paint(ring, frame)
        # temple arm to ear
        ox = x1 + 1 if sd_ > 0 else x0 - 1
        for i in range(1, 6):
            px(cv.img, ox + sd_ * i, y0 + 3, frame)
    # bridge
    xa = g[-1][2] + 1
    xb = g[1][1] - 1
    cv.paint(mrect(xa, g[-1][3] + 3, xb, g[-1][3] + 3), "ink")


def cu_kwak_offer():
    cv = CV("red1")
    # --- backdrop: coarse red/orange dither with blind stripes of light
    dither_ramp(cv.img, (0, 22, SW, 158), ["red0", "red1", "red2", "red1"], "y", 2)
    cv.dth(mrect(0, 22, SW, 100), "red2", vgrad(22, 100, 0.0, 0.5), 2)
    ph = (YY % 12)
    light = (ph < 5) & (YY >= 22) & (YY < 140)
    cv.paint(light, "orange1")
    cv.paint(light & (ph >= 1) & (ph < 4), "orange2")
    cv.paint(light & (ph == 2), "orange3")
    tail = (ph >= 5) & (ph < 7) & (YY >= 22) & (YY < 140)
    cv.dth(tail, "orange1", 0.5, 2)
    # window frame uprights (hard dark)
    for fx in (-2, 300):
        cv.paint(mrect(fx, 22, fx + 22, 140), "ink2")
        cv.dth(mrect(fx, 22, fx + 22, 140), "red0", 0.5, 2)
    vignette(cv, "ink", 0.7, 2, 0.9)
    # --- Kwak
    k = 1.3
    cx, yt = 214, 28
    H = Head(cx, yt, k, hw=21, h=50, jaw=2.6)
    skin = dict(hi="skin3", base="skin2", sh="skin1", deep="skin0")
    sy = H.chin + 5
    # torso (green suit)
    L = ell_pts(cx - 58, sy + 24, 36, 24, 180, 270, 12)
    torso = mpoly([(cx - 96, 158), (cx - 94, sy + 24)] + L + [(cx - 20, sy - 3)] + mirror_pts(L[::-1], cx) + [(cx + 94, sy + 24), (cx + 96, 158)])
    cv.layer(torso, "green0", "ink2", "green1", sd=(3, 3), hd=(2, 2), dith=True)
    # white shirt V + collar
    shirt = mpoly([(cx - 22, sy - 3), (cx + 22, sy - 3), (cx + 4, sy + 34), (cx - 4, sy + 34)])
    cv.layer(shirt, "white", "grey4", None, sd=(3, 3))
    # neck
    hmask = head_mask(cx, yt, H.h, H.hw, 2.6, 0.46)
    nk = mpoly([(cx - 12, H.chin - 14), (cx + 12, H.chin - 14), (cx + 13, sy + 8), (cx - 13, sy + 8)])
    cv.layer(nk, skin["base"], skin["sh"], None, sd=(3, 3), extra_shade=sh(hmask, 0, 9) & nk)
    # collar wings + lapels
    cw = mpoly([(cx - 24, sy - 8), (cx - 11, sy - 2), (cx, sy + 22), (cx - 18, sy + 18), (cx - 28, sy + 2)]) | \
        mpoly([(cx + 24, sy - 8), (cx + 11, sy - 2), (cx, sy + 22), (cx + 18, sy + 18), (cx + 28, sy + 2)])
    cv.layer(cw, "white", "grey4", None, sd=(2, 2))
    lap_l = mpoly([(cx - 30, sy - 4), (cx - 14, sy + 24), (cx - 4, sy + 52), (cx - 34, sy + 44), (cx - 44, sy + 10)])
    lap_r = mpoly(mirror_pts([(cx - 30, sy - 4), (cx - 14, sy + 24), (cx - 4, sy + 52), (cx - 34, sy + 44), (cx - 44, sy + 10)], cx))
    cv.layer(lap_l | lap_r, "green0", "ink2", "green1", sd=(3, 3), hd=(2, 2), dith=True)
    # tie
    tie = mpoly([(cx - 5, sy + 16), (cx + 5, sy + 16), (cx + 4, sy + 22), (cx + 8, sy + 58), (cx, sy + 64), (cx - 8, sy + 58), (cx - 4, sy + 22)])
    cv.layer(tie, "yellow", "orange2", "yellow2", sd=(3, 0), hd=(2, 0))
    cv.pts([(cx - 1, sy + 30 + i) for i in range(0, 20, 5)], "orange2")
    # head
    ears = mell(cx - H.hw - 3, yt + 30, cx - H.hw + 3, yt + 42) | mell(cx + H.hw - 3, yt + 30, cx + H.hw + 3, yt + 42)
    cv.layer(ears, skin["base"], skin["sh"], None, sd=(3, 3))
    hair_top = ell_pts(cx, yt + 22, H.hw + 2, 28, 180, 360, 30)
    hair = mpoly(hair_top + [(cx + H.hw + 2, yt + 34), (cx + H.hw - 3, yt + 34), (cx + H.hw - 4, yt + 24), (cx + 10, yt + 17),
                             (cx - 4, yt + 13), (cx - H.hw + 5, yt + 20), (cx - H.hw + 3, yt + 34), (cx - H.hw - 2, yt + 34)])
    extra = sh(hair, 0, 5) | sh(hair, 2, 6)
    cv.layer(hmask, skin["base"], skin["sh"], skin["hi"], sd=(3, 3), hd=(2, 2), dith=True, extra_shade=extra)
    ey = H.eye_y
    # cheek / smile lines + under-eye wrinkles
    for sd_ in (-1, 1):
        cv.pts([(cx + sd_ * (H.eye_dx + 12), ey + 9), (cx + sd_ * (H.eye_dx + 12), ey + 10), (cx + sd_ * (H.eye_dx + 11), ey + 11)], "skin1")
        cv.pts([(cx + sd_ * 9, ey + 16 + i) for i in range(0, 8)], "skin1")
        cv.pts([(cx + sd_ * (H.eye_dx + 13), ey - 1), (cx + sd_ * (H.eye_dx + 14), ey - 2)], "skin1")
    # glasses lenses: left one blank glint, right shows smiling eye
    g = glasses(cv, H, 19, 14)
    (Ll, xl0, xl1, yl0, yl1) = g[-1]
    (Lr, xr0, xr1, yr0, yr1) = g[1]
    cv.paint(Ll, "blue4")
    cv.dth(Ll, "white", 0.55, 2)
    cv.paint(Ll & (((XX + YY) % 9) < 2) & (XX > xl0 + 2), "white")
    cv.paint(Ll & (((XX + YY) % 9) < 1) & (YY > yl0 + 3), "blue3")
    cv.paint(Lr, "skin3")
    cv.dth(Lr, "blue4", 0.35, 2)
    eye_closed(cv, xr0 + 9, ey + 3, 1, w=11, up=True, thick=2)
    cv.paint(Lr & (((XX + YY) % 11) < 1) & (XX > xr0 + 2) & (YY < ey), "white")
    draw_glasses_frame(cv, g, H)
    # brows (thick, lifted: kind)
    for sd_ in (-1, 1):
        brow(cv, cx + sd_ * (H.eye_dx + 2), ey - 12, sd_, 13, tilt=-2, c="grey1", thick=2, arch=1)
    # nose + big smile
    cv.pts([(cx, ey + 9), (cx - 1, ey + 10), (cx - 1, ey + 11), (cx, ey + 12), (cx + 1, ey + 12)], "skin1")
    cv.pts([(cx - 2, ey + 13), (cx - 1, ey + 13), (cx, ey + 13), (cx + 1, ey + 13), (cx + 2, ey + 13)], "skin1")
    mouth(cv, cx, H.mouth_y, "grin2", c="skin0")
    # hair on top
    extra = mline([(cx + 14, yt + 2), (cx + 4, yt + 9), (cx - 8, yt + 14)], 1) | mline([(cx + 22, yt + 8), (cx + 10, yt + 14), (cx, yt + 17)], 1) | \
        mline([(cx - 4, yt - 2), (cx - 14, yt + 6), (cx - 22, yt + 14)], 1)
    hl_ = mell(cx - 14, yt - 3, cx + 24, yt + 7) & ~mell(cx - 14, yt + 0, cx + 24, yt + 12)
    cv.layer(hair, "grey2", "grey1", "grey4", sd=(3, 3), hd=(2, 2), extra_shade=extra, extra_hi=hl_, dith=True)
    # --- desk in the foreground
    desk_top = mpoly([(0, 140), (SW, 136), (SW, 148), (0, 152)])
    cv.layer(desk_top, "brown2", "brown1", "brown3", sd=(0, 3), hd=(0, -2), dith=True)
    cv.paint(mrect(0, 150, SW, 158), "brown0")
    cv.dth(mrect(0, 150, SW, 158), "ink", 0.5, 2)
    # nameplate on the desk
    plate = mrect(222, 138, 266, 152)
    cv.layer(plate, "yellow", "orange2", "yellow2", sd=(0, 2), hd=(0, -1))
    text(cv.img, 229, 140, "곽 실장", "ink", 9)
    # --- blind stripes cast over the character: hard shadow bars (palette steps down one notch)
    charm = torso | hmask | hair | ears | shirt | nk | lap_l | lap_r | cw | tie
    darkband = charm & (ph >= 6) & (ph < 10) & (YY < 139)
    DARKER = {"skin3": "skin2", "skin2": "skin1", "skin1": "skin0", "white": "grey4", "grey4": "grey3",
              "green1": "green0", "green0": "ink2", "ink2": "ink", "grey2": "grey1", "grey1": "ink2",
              "yellow": "orange2", "yellow2": "yellow", "orange2": "orange1", "blue4": "blue3", "blue3": "blue2",
              "skin0": "brown0", "grey3": "grey2"}
    a_ = np.array(cv.img)
    inv = {PAL[n] + (255,): PAL[d] + (255,) for n, d in DARKER.items()}
    ys, xs = np.nonzero(darkband)
    for y_, x_ in zip(ys, xs):
        t = tuple(a_[y_, x_])
        if t in inv:
            a_[y_, x_] = inv[t]
    cv.img = Image.fromarray(a_, "RGBA")
    # --- the contract held out to the viewer
    sleeve = mpoly([(146, 156), (150, 136), (176, 134), (196, 138), (206, 156)])
    cv.layer(sleeve, "green0", "ink2", "green1", sd=(3, 3), hd=(2, 2), dith=True)
    cuff = mpoly([(148, 128), (178, 126), (178, 136), (148, 138)])
    cv.layer(cuff, "white", "grey4", None, sd=(2, 2))
    hand_back = mpoly([(140, 92), (160, 88), (176, 100), (180, 118), (176, 128), (150, 128), (142, 114)])
    cv.layer(hand_back, "skin2", "skin1", "skin3", sd=(3, 3), hd=(2, 2))
    cv.pts([(170, 100 + i) for i in range(0, 12)], "skin1")
    paper = mpoly([(24, 92), (132, 80), (142, 138), (34, 150)])
    cv.layer(paper, "white", "grey4", None, sd=(3, 4), hd=(0, 0), dith=True)
    def pl(p0, p1, c):
        for t in range(0, 101):
            px(cv.img, int(p0[0] + (p1[0] - p0[0]) * t / 100), int(p0[1] + (p1[1] - p0[1]) * t / 100), c)
    for yy in range(0, 7):
        pl((38 + yy * 0.3, 103 + yy * 6), (118 + yy * 0.6 - (6 if yy > 4 else 0), 94 + yy * 6 + 1), "grey3")
    text(cv.img, 56, 88, "계약서", "ink", 11)
    ellipse(cv.img, 104, 124, 118, 138, "red2", "red1")
    text(cv.img, 107, 126, "인", "white", 9)
    for i, xx in enumerate(range(44, 80, 3)):
        px(cv.img, xx, 138 - (3 if i % 2 else 0), "ink2")
    thumb = mpoly([(158, 98), (140, 100), (124, 106), (122, 112), (130, 116), (150, 114), (160, 110)])
    cv.layer(thumb, "skin2", "skin1", "skin3", sd=(3, 3), hd=(2, 2))
    cv.pts([(124, 108), (125, 108), (124, 109)], "skin3")
    return cv


# ============================================================ 3. JUNHO
def messy_hair_masks(H, drop=0):
    k, cx, yt = H.k, H.cx, H.yt
    P = H.p
    top = ell_pts(cx, yt + 22 * k, 23 * k, 27 * k, 180, 360, 28)
    fr = [(-23, 31), (-21, 17), (-17, 26), (-12, 12), (-7, 23), (-2, 9), (3, 22), (8, 12), (13, 25), (18, 14), (23, 31)]
    cap = mpoly(top + [P(23, 38)] + [P(dx, dy) for dx, dy in fr[::-1]] + [P(-23, 38)])
    spikes = mpoly([P(-21, 14), P(-30, 0), P(-12, 4)]) | mpoly([P(-14, 4), P(-12, -12), P(0, 0)]) | \
        mpoly([P(-3, 0), P(8, -13), P(14, 2)]) | mpoly([P(10, 2), P(26, -6), P(23, 12)]) | \
        mpoly([P(20, 12), P(31, 12), P(25, 24)]) | mpoly([P(-22, 20), P(-31, 26), P(-22, 32)])
    ll = mpoly([P(-24, 24), P(-15, 22), P(-16, 38), P(-20, 42), P(-25, 36)])
    lr = mpoly([P(24, 24), P(15, 22), P(16, 38), P(20, 42), P(25, 36)])
    return cap | spikes, ll, lr


def draw_carousel_bg(cv):
    dither_ramp(cv.img, (0, 22, SW, 158), ["ink", "blue0", "purple0", "blue0", "ink2"], "y", 4)
    # canopy: dark scalloped roof along the top with panel stripes
    roof = mpoly([(0, 22), (SW, 22), (SW, 62), (0, 62)])
    sc = np.zeros((SH, SW), bool)
    for x in range(-6, SW + 12, 24):
        sc |= mell(x, 46, x + 24, 72)
    roof = (roof | sc) & (YY < 80)
    cv.paint(roof, "ink")
    for x in range(0, SW, 24):
        cv.dth(roof & (XX >= x) & (XX < x + 12), "blue0", 0.5, 2)
    cv.paint(mrect(0, 22, SW, 25), "ink2")
    # bulbs along the scallop edge, mostly dead, a few lit & blurred
    cols = [("red3", "red4"), ("yellow", "yellow2"), ("green2", "green3"), ("blue2", "blue3"), ("purple2", "blue3"), ("orange3", "orange4")]
    for i, x in enumerate(range(6, SW, 12)):
        y = 70 + (3 if (i % 2) else 0)
        c, c2 = cols[i % len(cols)]
        if i % 3 == 0:
            bokeh(cv, x, y, 6 if i % 2 else 5, c, c2, lv=0.5, rim=0.9)
        else:
            cv.paint(mrect(x - 1, y - 1, x, y), "grey1")
    # horses on poles: dark silhouettes, soft in dither
    for x in (40, 96, 224, 280):
        pole = mrect(x, 74, x + 1, 136)
        cv.paint(pole, "ink2")
        horse = mell(x - 20, 92, x + 22, 114) | mell(x + 10, 80, x + 28, 100) | mrect(x - 14, 108, x - 10, 124) | mrect(x + 10, 108, x + 14, 124)
        cv.layer(horse, "ink2", "ink", None, sd=(2, 2), dith=False, ol=None)
        cv.dth(horse, "blue0", 0.3, 2)
    cv.dth(mrect(0, 124, SW, 158), "ink", vgrad(124, 158, 0.0, 0.7), 4)
    # platform floor: frosty dither
    cv.dth(mrect(0, 132, SW, 158), "blue1", vgrad(132, 158, 0.35, 0.05), 4)


def cu_junho():
    cv = CV("ink")
    draw_carousel_bg(cv)
    # more big blurred coloured lights hovering behind him
    for i, (x, y, r, c, c2) in enumerate([(52, 96, 13, "red3", "red4"), (96, 112, 8, "yellow", "yellow2"), (262, 100, 14, "blue2", "blue3"),
                                          (292, 128, 9, "green2", "green3"), (30, 128, 8, "orange3", "orange4"), (230, 124, 7, "purple2", "blue3"),
                                          (118, 82, 6, "orange3", "yellow"), (206, 84, 6, "red3", "orange3"), (70, 74, 5, "green2", "green3"),
                                          (302, 86, 5, "yellow", "yellow2")]):
        bokeh(cv, x, y, r, c, c2, lv=0.4, rim=0.85)
    glow(cv, 20, 112, 70, [("red2", 0.3), ("red3", 0.35)], m=4)
    k = 1.3
    cx, yt = 160, 36
    H = Head(cx, yt, k, hw=20, h=50, jaw=2.1)
    skin = dict(hi="skin3", base="skin2", sh="skin1", deep="skin0")
    hairc = ("purple1", "purple0", "purple2")
    hm_all, ll, lr = messy_hair_masks(H)
    # back hair mass behind the head
    cv.layer(mell(cx - H.hw - 4, yt - 2, cx + H.hw + 4, yt + 52), "purple0", "ink", None, sd=(3, 3))
    sy = H.chin + 4
    # torso: grey hoodie + green vest
    L = ell_pts(cx - 50, sy + 26, 30, 26, 180, 270, 10)
    torso = mpoly([(cx - 76, 158), (cx - 74, sy + 26)] + L + [(cx - 18, sy - 2)] + mirror_pts(L[::-1], cx) + [(cx + 74, sy + 26), (cx + 76, 158)])
    cv.layer(torso, "grey3", "grey2", "grey4", sd=(3, 3), hd=(2, 2), dith=True)
    # hood bunched at the neck
    hood = mell(cx - 30, H.chin - 6, cx + 30, H.chin + 24)
    cv.layer(hood, "grey2", "grey1", "grey3", sd=(3, 3), hd=(2, 2))
    # vest panels
    VP = [(cx - 62, 156), (cx - 62, sy + 20), (cx - 54, sy + 6), (cx - 30, sy - 2), (cx - 6, sy + 8), (cx - 3, 156)]
    vl = mpoly(VP)
    vr = mpoly(mirror_pts(VP, cx))
    cv.layer(vl | vr, "green1", "green0", "green2", sd=(3, 3), hd=(2, 2), dith=True, ol="green0")
    cv.paint(mrect(cx - 1, sy + 8, cx, 156), "grey2")
    cv.pts([(cx, sy + 14 + i * 5) for i in range(0, 8)], "grey4")
    # neck + ears + head
    hmask = head_mask(cx, yt, H.h, H.hw, 2.1, 0.45)
    nk = mpoly([(cx - 10, H.chin - 14), (cx + 10, H.chin - 14), (cx + 11, H.chin + 10), (cx - 11, H.chin + 10)])
    cv.layer(nk, skin["base"], skin["sh"], None, sd=(3, 3), extra_shade=sh(hmask, 0, 8) & nk)
    ears = mell(cx - H.hw - 3, yt + 32, cx - H.hw + 3, yt + 44) | mell(cx + H.hw - 3, yt + 32, cx + H.hw + 3, yt + 44)
    cv.layer(ears, skin["base"], skin["sh"], None, sd=(3, 3))
    extra = sh(hm_all, 0, 5) | sh(hm_all, 2, 6) | sh(ll, 4, 0) | sh(lr, -4, 0)
    cv.layer(hmask, skin["base"], skin["sh"], skin["hi"], sd=(3, 3), hd=(2, 2), dith=True, extra_shade=extra)
    ey = H.eye_y
    # cold fill from the frost on the shadow side + blush
    cv.dth(hmask & (XX > cx + 8), "blue3", 0.15, 4)
    for sd_ in (-1, 1):
        cv.dth(mell(cx + sd_ * 14 - 5, ey + 9, cx + sd_ * 14 + 5, ey + 15) & hmask, "red4", 0.25, 2)
        ex = cx + sd_ * H.eye_dx
        eye(cv, ex, ey, sd_, w=13, h=14, iris="brown1", iris2="brown2", lid=3, look=(0, -2), hl="white", bag=True,
            skin_sh="skin1", lidc="skin2")
        cv.pts([(ex - 3, ey + 6), (ex - 2, ey + 6), (ex + 2, ey + 6)], "blue4")      # wet lower lid
        brow(cv, ex, ey - 11, sd_, 11, tilt=-3, c="purple0", thick=2)
        # tired bags
        cv.pts([(ex + i, ey + 9) for i in range(-4, 5)], "skin1")
        cv.dth(mrect(ex - 4, ey + 10, ex + 4, ey + 10), "skin1", 0.5, 2)
    cv.pts([(cx, ey + 12), (cx + 1, ey + 12), (cx - 1, ey + 13)], "skin1")
    mouth(cv, cx, H.mouth_y, "faint", c="skin0")
    # hair
    extra = np.zeros((SH, SW), bool)
    for dx in (-16, -9, -1, 6, 14, 20):
        extra |= mline([H.p(dx * 0.6, 0), H.p(dx * 0.8, 10), H.p(dx, 22)], 1)
    ringm = mell(cx - 17, yt - 4, cx + 15, yt + 12) & ~mell(cx - 17, yt + 1, cx + 15, yt + 17)
    hh = hm_all | ll | lr
    cv.layer(hh, "purple1", "purple0", "purple2", sd=(3, 3), hd=(2, 2), extra_shade=extra & ~ringm, extra_hi=ringm, dith=True)
    # FROST on the hair
    rng = np.random.RandomState(3)
    top_zone = hh & (YY < yt + 14)
    cv.dth(top_zone, "blue4", vgrad(yt - 12, yt + 14, 0.35, 0.05), 4)
    cv.dth(hh & (YY >= yt + 14), "blue3", 0.08, 4)
    for _ in range(34):
        fx = int(rng.randint(cx - 26, cx + 28)); fy = int(rng.randint(yt - 10, yt + 26))
        if 0 <= fy < SH and hh[fy, fx]:
            px(cv.img, fx, fy, "white")
            if rng.rand() < 0.4:
                px(cv.img, fx + 1, fy, "blue4")
    # frost fleck on lashes/brows/cheek
    cv.pts([(cx - 17, ey - 12), (cx + 18, ey - 12), (cx + 20, ey + 10), (cx - 19, ey + 11)], "blue4")
    # knees (pants) + arms wrapped round them
    knees = mell(cx - 66, 122, cx + 66, 200)
    cv.layer(knees, "blue1", "blue0", "blue2", sd=(3, 4), hd=(2, 3), dith=True)
    cv.paint(mline([(cx - 2, 130), (cx - 2, 158)], 1), "blue0")
    up_l = mpoly([(cx - 52, sy + 4), (cx - 68, sy + 10), (cx - 86, 136), (cx - 78, 150), (cx - 62, 146), (cx - 56, 124)])
    up_r = mpoly(mirror_pts([(cx - 52, sy + 4), (cx - 68, sy + 10), (cx - 86, 136), (cx - 78, 150), (cx - 62, 146), (cx - 56, 124)], cx))
    cv.layer(up_l | up_r, "grey3", "grey2", "grey4", sd=(3, 3), hd=(2, 2), dith=True)
    fa_l = mpoly([(cx - 84, 134), (cx - 70, 126), (cx - 30, 134), (cx - 12, 140), (cx - 12, 150), (cx - 34, 154), (cx - 74, 152), (cx - 86, 146)])
    fa_r = mpoly([(cx + 84, 134), (cx + 70, 126), (cx + 30, 134), (cx + 12, 140), (cx + 12, 150), (cx + 34, 154), (cx + 74, 152), (cx + 86, 146)])
    cv.layer(fa_l, "grey3", "grey2", "grey4", sd=(3, 4), hd=(2, 2), dith=True)
    cv.layer(fa_r, "grey3", "grey2", "grey4", sd=(3, 4), hd=(2, 2), dith=True)
    cv.paint(mline([(cx - 70, 134), (cx - 40, 142)], 1), "grey2")
    cv.paint(mline([(cx + 70, 134), (cx + 40, 142)], 1), "grey2")
    h1 = mell(cx - 26, 136, cx + 2, 154)
    h2 = mell(cx - 4, 132, cx + 24, 150)
    cv.layer(h1, "skin2", "skin1", "skin3", sd=(3, 4), hd=(2, 2))
    cv.layer(h2, "skin2", "skin1", "skin3", sd=(3, 4), hd=(2, 2))
    for fx in (0, 5, 10, 15):
        cv.pts([(cx + fx, 138), (cx + fx, 139), (cx + fx, 140)], "skin1")
    cv.pts([(cx + 22, 140), (cx + 22, 141), (cx + 23, 142)], "skin1")
    kn1 = knees; kn2 = knees
    # carousel light spill on the vest + hair rim + knees
    fig = cv.alpha_mask()
    cv.dth(torso & (XX < cx - 30) & (YY < 150), "red3", hgrad(cx - 30, cx - 80, 0.0, 0.35), 4)
    cv.dth(knees & (XX > cx + 30), "blue3", hgrad(cx + 30, cx + 66, 0.0, 0.5), 4)
    cv.dth(knees & (XX < cx - 30), "orange3", hgrad(cx - 30, cx - 66, 0.0, 0.4), 4)
    rim = hh & ~sh(hh, 2, 1) & (XX < cx - 6)
    cv.paint(rim, "orange3")
    rim = hh & ~sh(hh, -2, 1) & (XX > cx + 6)
    cv.paint(rim, "blue3")
    return cv


# ============================================================ 4. THE REGULAR
def window_dawn(cv, x0, y0, x1, y1, blind=0):
    """sunrise window: dithered sky, haze, skyline, low sun. blind = rows of lowered slats."""
    cv.paint(mrect(x0 - 3, y0 - 3, x1 + 3, y1 + 3), "brown1")
    cv.paint(mrect(x0 - 1, y0 - 1, x1 + 1, y1 + 1), "ink2")
    dither_ramp(cv.img, (x0, y0, x1 + 1, y1 + 1), ["orange3", "orange4", "yellow2", "wall1"], "y", 4)
    w = x1 - x0
    sx, sy = x0 + w * 0.35, y1 - 24
    dither_radial(cv.img, int(sx), int(sy), 26, "white", None, 4, box=(x0, y0, x1 + 1, y1 + 1))
    cv.paint(mell(int(sx) - 9, int(sy) - 9, int(sx) + 9, int(sy) + 9) & mrect(x0, y0, x1, y1), "yellow2")
    # skyline silhouettes (warm hazy)
    rng = np.random.RandomState(11)
    x = x0
    while x < x1:
        bw = int(rng.randint(9, 20)); bh = int(rng.randint(10, 34))
        b = mrect(x, y1 - bh, min(x1, x + bw - 1), y1)
        cv.paint(b, "orange1")
        cv.dth(b, "orange0", 0.45, 2)
        for wy in range(y1 - bh + 3, y1 - 2, 5):
            for wx in range(x + 2, min(x1, x + bw - 2), 4):
                if rng.rand() < 0.35:
                    px(cv.img, wx, wy, "yellow2")
        x += bw + int(rng.randint(0, 3))
    if blind:
        for yy in range(y0, y0 + blind, 5):
            cv.paint(mrect(x0, yy, x1, yy + 2), "wall1")
            cv.paint(mrect(x0, yy + 3, x1, yy + 3), "wall3")
            cv.paint(mrect(x0, yy + 4, x1, yy + 4), "ink2")
    # mullion
    cv.paint(mrect((x0 + x1) // 2 - 1, y0, (x0 + x1) // 2 + 1, y1), "brown1")


def void_eye(cv, x, y, w=12, h=14, lit=True):
    E = mell(x - w // 2, y - h // 2, x + w // 2, y + h // 2)
    cv.paint(E, "ink")
    cv.dth(E & (YY > y + 2), "ink2", 0.5, 2)
    cv.pts([(x - 3, y - 3), (x - 2, y - 3), (x - 3, y - 2)], "pale1")
    if lit:
        cv.pts([(x + 3, y + 3)], "grey2")
    top = E & ~sh(E, 0, 1, edge=False)
    cv.paint(top | sh(top, 0, -1, edge=False), "ink")


def cu_regular():
    cv = CV("wall1")
    # --- room at dawn: pastel wall, cool shade on the left, warm light from the right window
    dither_ramp(cv.img, (0, 22, SW, 158), ["wall3", "wall2", "wall1", "wall4"], "x", 4)
    cv.dth(mrect(0, 22, SW, 134), "wall3", hgrad(180, 0, 0.0, 0.7), 4)
    # wall details: cork notice board + clock, silhouetted soft
    cv.layer(mrect(20, 36, 66, 78), "brown3", "brown2", "wall1", sd=(2, 2), hd=(1, 1), dith=True)
    for (nx, ny, c) in [(26, 42, "white"), (40, 44, "yellow2"), (30, 58, "wall4"), (48, 58, "white"), (44, 68, "blue4")]:
        cv.layer(mrect(nx, ny, nx + 10, ny + 11), c, "grey4", None, sd=(1, 1), ol="brown1")
        cv.pts([(nx + 5, ny + 1)], "red3")
    ell = ellipse
    cv.layer(mell(196, 38, 216, 58), "white", "grey4", None, sd=(2, 2))
    cv.pts([(206, 48 - i) for i in range(0, 7)] + [(206 + i, 48) for i in range(0, 5)], "ink")
    # window (right)
    window_dawn(cv, 226, 34, 306, 112, blind=22)
    # sunbeam wedges falling on wall from the window (soft dither)
    for k_ in range(4):
        ox = 224 - k_ * 46
        beam = mpoly([(226, 40 + k_ * 16), (226, 56 + k_ * 16), (ox - 150, 148 + k_ * 10), (ox - 150, 126 + k_ * 10)]) if False else None
    ph = (YY * 1.0 + XX * 0.55) % 24
    beam = (ph < 9) & (XX < 224) & (XX > 60) & (YY > 28) & (YY < 134)
    cv.dth(beam, "orange4", hgrad(60, 224, 0.0, 0.55), 4)
    cv.dth(mrect(150, 22, 224, 134), "yellow2", hgrad(150, 224, 0.0, 0.3), 4)
    # --- the Regular
    k = 1.25
    cx, yt = 134, 27
    H = Head(cx, yt, k, hw=18, h=54, jaw=1.8)
    pale = dict(hi="grey4", base="pale2", sh="pale1", deep="grey2")
    P = H.p
    # back hair: long, falls behind shoulders
    back = mpoly([P(-26, 10), P(26, 10), P(30, 40), P(32, 70), P(34, 100), (cx - 44, 158), (cx + 44, 158), P(-34, 100), P(-32, 70), P(-30, 40)])
    back |= mell(cx - int(26 * k), yt - 4, cx + int(26 * k), yt + int(40 * k))
    cv.layer(back, "ink2", "ink", None, sd=(-3, 3), dith=True)
    # coat torso
    sy = H.chin - 3
    L = ell_pts(cx - 44, sy + 28, 30, 26, 180, 270, 10)
    torso = mpoly([(cx - 76, 158), (cx - 74, sy + 28)] + L + [(cx - 16, sy - 2)] + mirror_pts(L[::-1], cx) + [(cx + 74, sy + 28), (cx + 76, 158)])
    cv.layer(torso, "ink2", "ink", "grey1", sd=(-4, 3), hd=(-2, 1), dith=True)
    # inner blouse: pale high collar + dark V
    blouse = mpoly([(cx - 16, sy - 2), (cx + 16, sy - 2), (cx + 8, sy + 34), (cx - 8, sy + 34)])
    cv.layer(blouse, "grey4", "grey3", None, sd=(-3, 3))
    lap = mpoly([(cx - 22, sy), (cx - 8, sy + 6), (cx - 6, sy + 44), (cx - 30, sy + 40), (cx - 40, sy + 12)])
    lap2 = mpoly(mirror_pts([(cx - 22, sy), (cx - 8, sy + 6), (cx - 6, sy + 44), (cx - 30, sy + 40), (cx - 40, sy + 12)], cx))
    cv.layer(lap | lap2, "ink2", "ink", "grey1", sd=(-3, 3), hd=(-2, 1), dith=True)
    for by in (sy + 24, sy + 36):
        for bx in (cx - 9, cx + 9):
            cv.layer(mell(bx - 2, by - 2, bx + 2, by + 2), "red3", "red1", "red4", sd=(-1, 1), hd=(-1, 0))
    # neck, head
    hmask = head_mask(cx, yt, H.h, H.hw, 1.8, 0.44)
    nk = mpoly([(cx - 8, H.chin - 12), (cx + 8, H.chin - 12), (cx + 9, sy + 10), (cx - 9, sy + 10)])
    cv.layer(nk, "pale2", "pale1", None, sd=(-3, 3), extra_shade=sh(hmask, 0, 9) & nk)
    # bangs + side curtains
    top = ell_pts(cx, yt + 24 * k, 23 * k, 28 * k, 180, 360, 28)
    bang = [(-23, 34), (-22, 21), (-12, 21), (-3, 20), (6, 21), (14, 20), (22, 21), (23, 34)]
    cap = mpoly(top + [P(23, 34)] + [P(dx, dy) for dx, dy in bang[::-1]] + [P(-23, 34)])
    side_l = mpoly([P(-24, 18), P(-14, 20), P(-15, 40), P(-16, 62), P(-20, 90), P(-30, 92), P(-28, 50)])
    side_r = mpoly(mirror_pts([(-24, 18), (-14, 20), (-15, 40), (-16, 62), (-20, 90), (-30, 92), (-28, 50)], 0) if False else
                   [P(24, 18), P(14, 20), P(15, 40), P(16, 62), P(20, 90), P(30, 92), P(28, 50)])
    extra = sh(cap, 0, 5) | sh(cap, -1, 6) | sh(side_l, 5, 0) | sh(side_r, -5, 0)
    cv.layer(hmask, "pale2", "pale1", "grey4", sd=(-3, 2), hd=(-2, 1), dith=True, extra_shade=extra)
    ey = H.eye_y
    # warm window light across the right half of the face
    cv.dth(hmask & (XX > cx), "orange4", hgrad(cx, cx + 22, 0.0, 0.5), 4)
    cv.dth(hmask & (XX > cx + 8), "yellow2", hgrad(cx + 8, cx + 22, 0.0, 0.35), 4)
    cv.dth(nk & (XX > cx), "orange3", 0.3, 4)
    # features
    for sd_ in (-1, 1):
        ex = cx + sd_ * (H.eye_dx + 1)
        void_eye(cv, ex, ey, 11, 15)
        cv.pts([(ex + i, ey + 10) for i in range(-3, 4)], "pale1")
    cv.pts([(cx, ey + 12), (cx, ey + 13)], "pale1")
    # calm faint smile
    my = H.mouth_y
    cv.pts([(cx + i, my) for i in range(-4, 5)], "grey2")
    cv.pts([(cx - 5, my - 1), (cx + 5, my - 1)], "grey2")
    cv.pts([(cx + i, my + 1) for i in range(-2, 3)], "pale1")
    # hair on top
    cl = np.zeros((SH, SW), bool)
    for dx in (-15, -8, -1, 6, 13, 20):
        cl |= mline([P(dx * 0.7, 0), P(dx * 0.9, 12), P(dx, 20)], 1)
    for sgn in (-1, 1):
        cl |= mline([P(sgn * 21, 24), P(sgn * 20, 50), P(sgn * 22, 80)], 1)
    ringm = mell(cx - 22, yt - 3, cx + 22, yt + 14) & ~mell(cx - 22, yt + 2, cx + 22, yt + 19)
    hh = cap | side_l | side_r
    cv.layer(hh, "ink2", "ink", "grey1", sd=(-3, 2), hd=(-2, 1), extra_shade=cl & ~ringm, extra_hi=ringm, dith=True)
    # warm sheen on the right of the hair
    cv.dth(hh & (XX > cx + 6) & (YY < yt + 16), "orange3", 0.5, 4)
    rim = hh & ~sh(hh, -2, 0)
    cv.paint(rim, "orange4")
    cv.dth(side_r & (XX > cx + 20), "orange3", 0.3, 4)
    # --- desk, note, hand
    desk = mpoly([(0, 136), (SW, 132), (SW, 158), (0, 158)])
    cv.layer(desk, "brown2", "brown1", "brown3", sd=(0, 4), hd=(0, -2), dith=True)
    cv.paint(mrect(0, 148, SW, 158), "brown1")
    cv.dth(mrect(0, 148, SW, 158), "brown0", 0.45, 2)
    cv.dth(mrect(0, 136, SW, 148), "orange3", hgrad(0, SW, 0.0, 0.55), 4)
    # window light parallelograms on the desk top
    cv.dth(mpoly([(190, 134), (216, 134), (240, 148), (212, 148)]) | mpoly([(246, 133), (276, 133), (300, 148), (268, 148)]), "yellow2", 0.6, 4)
    # her pale hand resting by the note
    for i in range(4):
        fg = mpoly([(164 + i * 3, 138 + i * 3), (192, 137 + i * 3), (194, 141 + i * 3), (166 + i * 3, 141 + i * 3)])
        cv.layer(fg, "pale2", "pale1", "grey4", sd=(-2, 2), hd=(-1, 1))
    palm = mell(186, 135, 216, 152)
    cv.layer(palm, "pale2", "pale1", "grey4", sd=(-3, 3), hd=(-2, 1), dith=True)
    cv.pts([(214, 144), (213, 145)], "pale1")
    cv.dth(palm | mrect(168, 140, 190, 150), "orange4", 0.3, 4)
    # folded note, standing like a tent
    note_l = mpoly([(58, 148), (60, 130), (82, 126), (82, 148)])
    note_r = mpoly([(82, 148), (82, 126), (104, 130), (106, 148)])
    cv.layer(note_l, "wall4", "grey3", None, sd=(3, 0), dith=True)
    cv.layer(note_r, "white", "wall4", "yellow2", sd=(0, 0), hd=(-1, 0), dith=False)
    cv.pts([(86 + i, 133 + (i // 8)) for i in range(0, 16)], "grey2")
    cv.pts([(92 + i, 139 + (i // 8)) for i in range(0, 10)], "grey2")
    cv.dth(note_r, "orange4", 0.35, 4)
    cv.paint(mrect(82, 126, 82, 148), "grey3")
    # soft shadow of the note on the desk
    cv.dth(mpoly([(104, 148), (130, 148), (126, 152), (100, 152)]), "brown0", 0.5, 2)
    return cv


# ============================================================ 5. RELIEF (from behind)
def dawn_street(cv, sx, sy):
    hz = sy + 12
    dither_ramp(cv.img, (0, 22, SW, hz + 1), ["blue3", "wall4", "orange3", "orange4", "yellow2"], "y", 4)
    # thin cloud streaks
    for (cy_, x0_, x1_) in [(40, 20, 120), (52, 190, 300), (64, 60, 140), (34, 230, 310)]:
        cv.dth(mrect(x0_, cy_, x1_, cy_ + 1), "wall4", 0.7, 2)
    glow(cv, sx, sy, 80, [("yellow2", 0.45), ("white", 0.35)], m=4)
    cv.paint(mell(sx - 15, sy - 15, sx + 15, sy + 15) & (YY <= hz), "white")
    cv.paint(mell(sx - 11, sy - 11, sx + 11, sy + 11) & (YY <= hz), "yellow2")
    # light rays across sky
    for ang in (-62, -40, -22, 18, 38, 60):
        a = math.radians(ang)
        ray = mpoly([(sx, sy), (sx + 200 * math.sin(a - 0.05), sy - 200 * math.cos(a - 0.05)), (sx + 200 * math.sin(a + 0.05), sy - 200 * math.cos(a + 0.05))])
        cv.dth(ray & (YY < hz) & (YY > 22), "yellow2", 0.16, 4)
    for (bx_, by_) in [(70, 44), (78, 40), (88, 47), (238, 52), (246, 48), (256, 55), (140, 36)]:
        cv.pts([(bx_ - 2, by_), (bx_ - 1, by_ + 1), (bx_, by_), (bx_ + 1, by_ + 1), (bx_ + 2, by_)], "ink2")
    # distant skyline (hazy) + near buildings (backlit silhouettes with warm rim)
    rng = np.random.RandomState(5)
    x = 0
    far = np.zeros((SH, SW), bool)
    while x < SW:
        bw = int(rng.randint(10, 22)); bh = int(rng.randint(12, 36))
        far |= mrect(x, hz - bh, x + bw - 1, hz)
        x += bw + int(rng.randint(0, 3))
    cv.paint(far, "wall3")
    cv.dth(far, "purple2", 0.35, 2)
    # near blocks left / right (perspective: tall at edges)
    def block(x0, x1, top, tint):
        b = mrect(x0, top, x1, hz + 14)
        cv.layer(b, "purple0", "ink2", "purple1", sd=(-4, 0), hd=(-2, 0), dith=True, ol=None)
        cv.dth(b, "orange0", 0.25, 2)
        for wy in range(top + 6, hz + 8, 9):
            for wx in range(x0 + 5, x1 - 4, 9):
                if rng.rand() < 0.22:
                    cv.paint(mrect(wx, wy, wx + 3, wy + 4), "yellow2")
                    cv.paint(mrect(wx, wy + 5, wx + 3, wy + 5), "orange2")
                else:
                    cv.paint(mrect(wx, wy, wx + 3, wy + 4), "blue0")
        return b
    bl = [block(0, 34, 40, "red3"), block(34, 66, 66, "red3"), block(66, 92, 84, "orange2")]
    br = [block(286, 320, 36, "red3"), block(256, 286, 62, "red3"), block(236, 256, 80, "orange2")]
    for b in bl + br:
        r_ = b & ~sh(b, -1, 0) & ~sh(b, 0, 1)
    # warm rim on the sun-facing edges
    for b in bl:
        cv.paint(b & ~sh(b, -1, 0, edge=False), "orange4")
    for b in br:
        cv.paint(b & ~sh(b, 1, 0, edge=False), "orange4")
    # road with perspective
    road = mpoly([(0, 158), (SW, 158), (SW, hz + 14), (0, hz + 14)])
    cv.paint(road, "grey2")
    cv.dth(road, "orange3", vgrad(hz + 14, 158, 0.65, 0.05), 4)
    cv.paint(mrect(0, hz + 14, SW, hz + 15), "ink2")
    # lane dashes converge on the vanishing point
    for k_ in range(-5, 6):
        for t in np.linspace(0.12, 1.0, 8)[::2]:
            yy = int(hz + 14 + (158 - hz - 14) * t ** 1.6)
            xx = int(sx + k_ * 46 * t ** 1.6)
            w_ = int(2 + 3 * t)
            if abs(k_) % 2 == 1:
                cv.paint(mrect(xx - w_, yy, xx + w_, yy + 1), "grey4")
    # lamp posts going out
    for lx, ly in [(100, 82), (222, 82)]:
        cv.paint(mrect(lx, ly, lx + 1, hz + 14), "ink2")
        cv.paint(mrect(lx, ly, lx + 6, ly), "ink2")
        cv.paint(mrect(lx + 5, ly + 1, lx + 7, ly + 2), "grey2")
    return hz


def back_torso_shadowed(cv, cx, sy, spread, base, shade, hi, rim, sd=(4, 2), bottom=158):
    pass


def cu_sora_relief():
    cv = CV("blue3")
    sxs, sys_ = 163, 92
    hz = dawn_street(cv, sxs, sys_)
    RIM = "yellow2"
    # ------------------ Junho (right, taller), seen from behind
    k = 1.12
    jx, jt = 222, 40
    HJ = Head(jx, jt, k, hw=20, h=50)
    P = HJ.p
    jy = HJ.chin + 4
    L = ell_pts(jx - 50, jy + 26, 30, 26, 180, 270, 10)
    torso = mpoly([(jx - 78, 158), (jx - 76, jy + 26)] + L + [(jx - 14, jy - 2)] + mirror_pts(L[::-1], jx) + [(jx + 76, jy + 26), (jx + 78, 158)])
    cv.layer(torso, "grey2", "grey1", "grey3", sd=(-4, 3), hd=(2, 2), dith=True)
    hood = mell(jx - 26, HJ.chin - 8, jx + 26, HJ.chin + 20)
    cv.layer(hood, "grey2", "grey1", "grey3", sd=(-4, 3), hd=(2, 2), dith=True)
    VP = [(jx - 58, 158), (jx - 58, jy + 24), (jx - 50, jy + 8), (jx - 26, jy + 3), (jx - 2, jy + 10), (jx - 2, 158)]
    vl = mpoly(VP); vr = mpoly(mirror_pts(VP, jx))
    cv.layer(vl | vr, "green0", "ink2", "green1", sd=(-4, 3), hd=(2, 2), dith=True, ol="ink2")
    cv.paint(mrect(jx - 1, jy + 10, jx, 158), "ink2")
    text(cv.img, jx - 26, jy + 26, "새벽", "yellow", 9, edge="ink")
    neck = mpoly([(jx - 9, HJ.chin - 24), (jx + 9, HJ.chin - 24), (jx + 10, HJ.chin + 6), (jx - 10, HJ.chin + 6)])
    cv.layer(neck, "skin1", "skin0", None, sd=(-3, 3))
    ears = mell(jx - HJ.hw - 3, jt + 28, jx - HJ.hw + 3, jt + 39) | mell(jx + HJ.hw - 3, jt + 28, jx + HJ.hw + 3, jt + 39)
    cv.layer(ears, "skin1", "skin0", None, sd=(-3, 3))
    hairm = mell(jx - HJ.hw - 4, jt - 2, jx + HJ.hw + 4, jt + int(44 * k)) & (YY < jt + int(34 * k))
    nape = mpoly([P(-22, 32), P(-19, 44), P(-11, 38), P(-5, 47), P(2, 39), P(9, 46), P(16, 38), P(22, 32), P(22, 14), P(-22, 14)])
    spikes = mpoly([P(-21, 14), P(-30, 0), P(-12, 4)]) | mpoly([P(-14, 4), P(-12, -12), P(0, 0)]) | \
        mpoly([P(-3, 0), P(8, -13), P(14, 2)]) | mpoly([P(10, 2), P(26, -6), P(23, 12)]) | \
        mpoly([P(20, 12), P(31, 14), P(25, 26)]) | mpoly([P(-22, 20), P(-31, 28), P(-22, 34)])
    hair = hairm | nape | spikes
    cl = np.zeros((SH, SW), bool)
    for dx in (-16, -8, 0, 8, 16):
        cl |= mline([P(dx * 0.7, 6), P(dx * 0.9, 24), P(dx, 40)], 1)
    ringm = mell(jx - 22, jt - 4, jx + 22, jt + 12) & ~mell(jx - 22, jt + 1, jx + 22, jt + 17)
    cv.layer(hair, "purple0", "ink2", "purple1", sd=(-4, 3), hd=(2, 2), extra_shade=cl, extra_hi=ringm, dith=True)
    cv.paint(hair & ~sh(hair, 0, 1, edge=False), RIM)
    cv.dth(hair & ~sh(hair, 0, 3, edge=False), "orange3", 0.5, 4)
    cv.dth(hair & ~sh(hair, 3, 0, edge=False), "orange3", 0.55, 4)
    cv.paint(torso & ~sh(torso, 0, 1, edge=False) & (YY < jy + 40), "orange4")
    arm_r = mpoly([(jx + 54, jy + 6), (jx + 76, jy + 20), (jx + 86, 158), (jx + 62, 158), (jx + 50, jy + 38)])
    cv.layer(arm_r, "grey2", "grey1", "grey3", sd=(-4, 3), hd=(2, 2), dith=True)
    # ------------------ Sora (left, shorter)
    k2 = 1.02
    sx_, st = 108, 64
    HS = Head(sx_, st, k2)
    Ps = HS.p
    sy2 = st + int(58 * k2) + 2
    L = ell_pts(sx_ - 46, sy2 + 22, 30, 24, 180, 270, 10)
    torso_s = mpoly([(sx_ - 74, 158), (sx_ - 72, sy2 + 22)] + L + [(sx_ - 14, sy2 - 2)] + mirror_pts(L[::-1], sx_) + [(sx_ + 72, sy2 + 22), (sx_ + 74, 158)])
    hood_s = mell(sx_ - 28, st + 40, sx_ + 28, st + int(58 * k2) + 12)
    cv.layer(hood_s, "orange0", "ink", None, sd=(-3, 3))
    cv.layer(torso_s, "orange1", "orange0", "orange2", sd=(-4, 3), hd=(2, 2), dith=True)
    cv.paint(torso_s & ~sh(torso_s, 0, 1, edge=False), "orange4")
    cv.paint(mline([(sx_ + 44, sy2 + 28), (sx_ + 40, 158)], 1), "orange0")
    cv.paint(mline([(sx_ - 44, sy2 + 28), (sx_ - 40, 158)], 1), "orange0")
    # ------------------ Junho's arm across her shoulders (thick polyline), hand hanging past her far shoulder
    cl_ = [(jx - 58, jy + 12), (jx - 76, jy + 20), (sx_ + 40, sy2 + 4), (sx_ - 20, sy2 + 8), (sx_ - 54, sy2 + 14)]
    arm_l = mline(cl_, 15)
    arm_l |= mell(jx - 70, jy + 4, jx - 44, jy + 30)
    cv.layer(arm_l, "grey2", "grey1", "grey3", sd=(-4, 3), hd=(2, 2), dith=True)
    cv.paint(arm_l & ~sh(arm_l, 0, 1, edge=False) & (XX < sx_ + 80), "orange4")
    cv.paint(mline([(sx_ - 38, sy2 + 8), (sx_ - 36, sy2 + 18)], 1), "grey1")
    hand = mpoly([(sx_ - 62, sy2 + 8), (sx_ - 54, sy2 + 5), (sx_ - 44, sy2 + 10), (sx_ - 44, sy2 + 24), (sx_ - 52, sy2 + 28), (sx_ - 62, sy2 + 22)])
    cv.layer(hand, "skin1", "skin0", "skin2", sd=(-3, 3), hd=(2, 2))
    for fx in (-58, -53, -48):
        cv.pts([(sx_ + fx, sy2 + 20), (sx_ + fx, sy2 + 21), (sx_ + fx, sy2 + 22)], "skin0")
    cv.paint(hand & ~sh(hand, 0, 1, edge=False), "orange4")
    # ------------------ Sora's head: bob from behind (hangs in front of the arm)
    back = mpoly(Ps_pl(HS, [(-27, 10), (27, 10), (29, 38), (27, 52), (22, 58), (14, 54), (6, 59), (-3, 54), (-10, 59), (-18, 54), (-24, 58), (-27, 52), (-29, 38)]))
    back |= mell(sx_ - int(26 * k2), st - 4, sx_ + int(26 * k2), st + int(40 * k2))
    cl = np.zeros((SH, SW), bool)
    for dx in (-18, -10, -3, 5, 13, 20):
        cl |= mline([Ps(dx * 0.7, 6), Ps(dx * 0.95, 28), Ps(dx, 52)], 1)
    cl |= mline([Ps(1, -2), Ps(2, 20), Ps(1, 40)], 1)
    ringm = mell(sx_ - 22, st - 4, sx_ + 22, st + 14) & ~mell(sx_ - 22, st + 1, sx_ + 22, st + 20)
    cv.layer(back, "purple1", "purple0", "purple2", sd=(-4, 3), hd=(2, 2), extra_shade=cl, extra_hi=ringm, dith=True)
    cv.paint(back & ~sh(back, 0, 1, edge=False), RIM)
    cv.dth(back & ~sh(back, 0, 3, edge=False), "orange3", 0.5, 4)
    cv.dth(back & ~sh(back, -3, 0, edge=False), "orange3", 0.6, 4)
    return cv


def Ps_pl(H, pts):
    return H.pl(pts)


# ============================================================ 6. SORA AT KWAK'S DESK
def lum(c):
    return (0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255.0


def grade(cv, ramp, level, mask=None, m=4, gamma=1.0, keep=()):
    """monochrome wash through a palette ramp, ordered-dithered between ramp steps.
    only `level` (0..1) of the pixels (ordered dither) are replaced."""
    a = np.array(cv.img)
    n = len(ramp) - 1
    rc = [col(c) for c in ramp]
    keepc = {col(c) for c in keep}
    t = T4 if m == 4 else T2
    H_, W_ = a.shape[:2]
    for y in range(H_):
        for x in range(W_):
            p = a[y, x]
            if p[3] == 0 or (mask is not None and not mask[y, x]):
                continue
            if tuple(p) in keepc:
                continue
            lv = level if not isinstance(level, np.ndarray) else level[y, x]
            if lv <= t[y, x]:
                continue
            v = min(1.0, lum(p) ** gamma) * n
            i0 = int(v)
            if i0 >= n:
                a[y, x] = rc[n]
                continue
            f = v - i0
            a[y, x] = rc[i0 + 1] if f > t[(y * 3 + 1) % SH, (x * 5 + 2) % SW] else rc[i0]
    cv.img = Image.fromarray(a, "RGBA")


def vignette(cv, c="ink", start=0.55, m=2, strength=1.0):
    d = np.sqrt(((XX - SW / 2) / (SW / 2)) ** 2 + ((YY - 90) / 68) ** 2)
    lv = np.clip((d - start) / (1.2 - start), 0, 1) * strength
    cv.dth((YY >= 22) & (YY < 158), c, lv, m)


def paper_stack(cv, x0, y0, n=5, w=60, h=34, tilt=0):
    for i in range(n):
        ox = x0 + (i % 2) * 2 - 1 + tilt * i
        oy = y0 - i * 3
        pg = mpoly([(ox, oy), (ox + w, oy - 4), (ox + w + 3, oy + h - 5), (ox + 3, oy + h)])
        cv.layer(pg, "white" if i % 2 else "wall1", "grey4", None, sd=(3, 3), dith=False)


def cu_sora_desk():
    cv = CV("pale1")
    # --- office wall under sickly fluorescent light
    dither_ramp(cv.img, (0, 22, SW, 158), ["grey2", "pale1", "green1", "green0", "ink2"], "y", 4)
    win = mrect(14, 30, 86, 100)
    cv.paint(win, "ink2")
    for yy in range(32, 100, 7):
        cv.paint(mrect(16, yy, 84, yy + 3), "pale2")
        cv.paint(mrect(16, yy + 4, 84, yy + 4), "grey2")
    cv.paint(mrect(14, 30, 86, 31), "grey1")
    cv.dth(win, "green1", 0.3, 4)
    cab = mrect(256, 54, 306, 140)
    cv.layer(cab, "green0", "ink2", "green1", sd=(3, 3), hd=(2, 2), dith=True)
    for yy in (62, 84, 106):
        cv.paint(mrect(262, yy, 300, yy + 16), "green1")
        cv.paint(mrect(262, yy + 17, 300, yy + 17), "ink")
        cv.paint(mrect(274, yy + 6, 288, yy + 8), "ink2")
    cv.dth(mrect(0, 22, SW, 76), "green3", vgrad(22, 76, 0.3, 0.0), 4)
    # --- the chair: tall dark leather back
    k = 1.3
    cx, yt = 160, 28
    H = Head(cx, yt, k)
    chair = mpoly([(cx - 82, 158), (cx - 84, 70), (cx - 74, 44), (cx - 50, 30), (cx + 50, 30), (cx + 74, 44), (cx + 84, 70), (cx + 82, 158)])
    cv.layer(chair, "ink2", "ink", "grey1", sd=(3, 3), hd=(2, 2), dith=True)
    for gy in range(54, 146, 14):
        for gx in range(cx - 70, cx + 71, 20):
            xx = gx + (10 if ((gy // 14) % 2) else 0)
            if abs(xx - cx) < 44 and gy < 120:
                continue
            cv.pts([(xx, gy), (xx + 1, gy)], "grey2")
    hairc = ("purple0", "ink2", "purple1")
    skin = dict(hi="grey4", base="pale2", sh="pale1", deep="grey2")
    M_ = sora_masks(H)
    sora_hair_back(cv, H, hairc, M_)
    sy = H.chin + 6
    L = ell_pts(cx - 48, sy + 28, 32, 28, 180, 270, 12)
    torso = mpoly([(cx - 80, 158), (cx - 78, sy + 28)] + L + [(cx - 18, sy - 2)] + mirror_pts(L[::-1], cx) + [(cx + 78, sy + 28), (cx + 80, 158)])
    hood = mell(cx - 36, H.chin - 10, cx + 36, H.chin + 34)
    cv.layer(hood, "orange0", "ink", None, sd=(2, 3), dith=True)
    cv.layer(torso, "brown2", "brown1", "brown3", sd=(3, 5), hd=(2, 2), dith=True)
    cv.dth(torso, "green0", 0.3, 2)
    fm = sora_face_base(cv, H, skin, M_, sd=(3, 3), hd=(2, 2))
    col_ = mell(cx - 32, H.chin + 2, cx + 32, H.chin + 36) & ~mell(cx - 16, H.chin - 6, cx + 16, H.chin + 14) & ~fm
    cv.layer(col_, "brown2", "brown1", "brown3", sd=(3, 3), hd=(2, 2), dith=True)
    cv.dth(col_, "green0", 0.28, 2)
    cv.dth(fm, "green3", 0.14, 4)
    cv.dth(fm & (YY > yt + 40), "pale1", 0.3, 2)
    ey = H.eye_y
    for sd_ in (-1, 1):
        ex = cx + sd_ * H.eye_dx
        eye(cv, ex, ey, sd_, w=13, h=14, iris="ink2", iris2="grey1", lid=2, look=(0, 0), hl=None, dull=True, bag=False,
            skin_sh="pale1", lidc="pale1", white="grey4")
        cv.pts([(ex + i, ey + 8) for i in range(-5, 6)], "grey2")
        cv.pts([(ex + i, ey + 9) for i in range(-3, 4)], "pale1")
        brow(cv, ex, ey - 11, sd_, 11, tilt=0, c="purple0", thick=1)
    cv.pts([(cx, ey + 13), (cx + 1, ey + 13)], "pale1")
    mouth(cv, cx, H.mouth_y, "flat", c="grey1")
    hm = sora_hair_front(cv, H, hairc, M_, sd=(3, 3), hd=(2, 2))
    cv.dth(hm, "green0", 0.22, 2)
    # glasses (Kwak's rectangular frames, now on her)
    g = glasses(cv, H, 21, 16, dy=0)
    for sd_, (Lm, x0, x1, y0, y1) in g.items():
        cv.paint(Lm & (((XX + YY) % 16) == 0) & (XX < x0 + 9) & (YY < y0 + 8), "white")
    draw_glasses_frame(cv, g, H)
    cv.pts([(cx - 1, ey + 3), (cx, ey + 3)], "ink")
    cv.pts([(cx - 14, H.chin + 36 + i) for i in range(14)], "grey3")
    cv.pts([(cx + 14, H.chin + 36 + i) for i in range(11)], "grey3")
    # arms down to the desk + folded hands
    for sg in (-1, 1):
        arm = mline([(cx + sg * 62, sy + 18), (cx + sg * 70, 126), (cx + sg * 30, 146)], 17)
        cv.layer(arm, "brown2", "brown1", "brown3", sd=(3, 4), hd=(2, 2), dith=True)
        cv.dth(arm, "green0", 0.3, 2)
    # --- desk (foreground)
    desk = mpoly([(0, 146), (SW, 143), (SW, 158), (0, 158)])
    cv.layer(desk, "brown1", "brown0", "brown2", sd=(0, 4), hd=(0, -2), dith=True)
    cv.dth(desk, "green0", 0.3, 2)
    cv.paint(mrect(0, 153, SW, 158), "brown0")
    cv.dth(mrect(0, 153, SW, 158), "ink", 0.5, 2)
    h1 = mell(cx - 30, 129, cx + 2, 148)
    h2 = mell(cx - 4, 126, cx + 28, 145)
    cv.layer(h1, "pale2", "pale1", "grey4", sd=(3, 4), hd=(2, 2))
    cv.layer(h2, "pale2", "pale1", "grey4", sd=(3, 4), hd=(2, 2))
    for fx in (0, 6, 12, 18):
        cv.pts([(cx + fx, 132), (cx + fx, 133), (cx + fx, 134)], "pale1")
    # stack of rule sheets (leaning, ragged), the top one written on
    for i in range(7):
        ox = 38 + (i * 7 % 5) - 2
        oy = 146 - i * 3
        pg = mpoly([(ox, oy), (ox + 62, oy - 3), (ox + 64, oy + 8), (ox + 1, oy + 11)])
        cv.layer(pg, "grey4" if i % 2 else "pale2", "grey3", None, sd=(3, 3), dith=False)
    for ln in range(3):
        yy = 131 + ln * 3
        cv.paint(mrect(44 + ln % 2 * 2, yy, 88 - (ln * 5) % 9, yy), "grey2")
    # nameplate: the only warm colour left in the room
    # sickly fluorescent light from above, flicker bands
    vignette(cv, "ink", 1.0, 2, 0.8)
    plate = mrect(224, 143, 274, 157)
    cv.layer(plate, "yellow", "orange2", "yellow2", sd=(0, 2), hd=(0, -1))
    text(cv.img, 231, 145, "곽 실장", "ink", 9)
    text(cv.img, 44, 112, "규칙 1~99", "yellow2", 9, edge="ink")
    return cv


# ============================================================ 7. TITLE CARDS
def text_mask(s, x, y, f=11, mult=1):
    t = new(SW, SH)
    text(t, x, y, s, "white", f, mult=mult)
    return np.array(t)[:, :, 3] > 0


def neon(cv, x, y, s, c, glow_c=None, f=11, mult=1, edge=None, glow=0.45, gr=2, outline_c=None):
    tm = text_mask(s, x, y, f, mult)
    if glow_c:
        g = dil(tm, gr)
        cv.dth(g & ~tm, glow_c, glow, 4)
    if outline_c:
        cv.paint(dil(tm, 1) & ~tm, outline_c)
    text(cv.img, x, y, s, c, f, mult=mult)
    return tm


def stars(cv, n, y0, y1, seed=1, cols=("white", "grey4", "blue3", "yellow2")):
    rng = np.random.RandomState(seed)
    for i in range(n):
        px(cv.img, int(rng.randint(0, SW)), int(rng.randint(y0, y1)), cols[i % len(cols)])


def lamp(cv, x, top, base, c="ink2", bulb="yellow2", glow_c="yellow2", r=26, arm=0):
    cv.paint(mrect(x, top, x + 1, base), c)
    if arm:
        cv.paint(mrect(x, top, x + arm, top), c)
    bx = x + arm
    dither_radial(cv.img, bx, top + 3, r, glow_c, None, 4)
    cv.paint(mrect(bx - 2, top + 1, bx + 2, top + 3), bulb)


def ground_fade(cv, y0=112, c="ink", top=0.0, bot=0.75):
    """quiet lower third: dither darkening so the game can write a title there."""
    cv.dth(mrect(0, y0, SW, 158), c, vgrad(y0, 158, top, bot), 4)


def window_grid(cv, x0, y0, cols, rows, w=8, h=10, gx=5, gy=5, lit=None, off="blue0", on="yellow2", seed=2, lit_p=0.25, on2="orange3"):
    rng = np.random.RandomState(seed)
    for r in range(rows):
        for c in range(cols):
            wx, wy = x0 + c * (w + gx), y0 + r * (h + gy)
            isl = lit(r, c) if lit else rng.rand() < lit_p
            cv.paint(mrect(wx, wy, wx + w - 1, wy + h - 1), on if isl else off)
            if isl:
                cv.paint(mrect(wx, wy + h - 2, wx + w - 1, wy + h - 1), on2)
            else:
                cv.paint(mrect(wx, wy, wx + w - 1, wy), "blue1")
            cv.paint(mrect(wx - 1, wy + h, wx + w, wy + h), "ink")


def tc_store():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 118), ["ink", "blue0", "purple0", "blue0"], "y", 4)
    stars(cv, 40, 24, 70, 4)
    # neighbours
    for (x0, x1, top) in [(0, 70, 54), (260, 320, 46)]:
        b = mrect(x0, top, x1, 124)
        cv.layer(b, "ink2", "ink", "grey1", sd=(3, 3), hd=(2, 2), dith=True)
        window_grid(cv, x0 + 8, top + 8, 4, 5, 8, 9, 5, 5, lit_p=0.15)
    # the store: wide glass front on the corner
    body = mrect(76, 62, 254, 124)
    cv.layer(body, "grey1", "ink2", "grey2", sd=(3, 3), hd=(2, 2), dith=True)
    cv.paint(mrect(76, 62, 254, 64), "grey2")
    # sign band
    cv.paint(mrect(80, 66, 250, 86), "blue1")
    cv.paint(mrect(80, 66, 250, 67), "blue2")
    cv.paint(mrect(80, 85, 250, 86), "blue0")
    cv.paint(mrect(84, 70, 100, 82), "yellow")
    cv.paint(mell(86, 70, 98, 82), "blue1")
    cv.paint(mell(91, 70, 100, 82), "yellow")
    neon(cv, 108, 69, "달빛 편의점", "white", "blue3", f=14, glow=0.5)
    text(cv.img, 218, 72, "24", "yellow", 14, edge="ink")
    # glass front glowing + shelves
    for (x0, x1) in [(82, 160), (172, 248)]:
        g = mrect(x0, 90, x1, 120)
        cv.paint(g, "blue4")
        cv.dth(g, "white", 0.55, 4)
        for sy_ in (97, 106, 115):
            cv.paint(mrect(x0 + 2, sy_, x1 - 2, sy_), "grey3")
            for i, xx in enumerate(range(x0 + 4, x1 - 4, 5)):
                cv.paint(mrect(xx, sy_ - 5, xx + 2, sy_ - 1), ["red3", "blue2", "green2", "yellow", "orange2", "purple2"][(i + sy_) % 6])
        cv.paint(mrect(x0, 90, x1, 90), "ink")
    # door
    door = mrect(162, 90, 170, 122)
    cv.paint(door, "blue3")
    cv.paint(mrect(165, 100, 166, 112), "grey2")
    # awning stripes
    for i, xx in enumerate(range(76, 254, 10)):
        cv.paint(mrect(xx, 87, xx + 9, 89), "green2" if i % 2 == 0 else "white")
    # corner vertical sign
    cv.paint(mrect(256, 40, 268, 104), "ink2")
    cv.paint(mrect(257, 41, 267, 103), "red2")
    dither_radial(cv.img, 262, 72, 24, "red3", None, 4, box=(240, 30, 290, 110))
    cv.paint(mrect(256, 40, 268, 104), "ink2")
    cv.paint(mrect(257, 41, 267, 103), "red2")
    cv.dth(mrect(257, 41, 267, 103), "red1", 0.35, 2)
    for i, ch in enumerate("새벽영업"):
        text(cv.img, 257, 44 + i * 14, ch, "white", 11)
    # sidewalk glow pool
    walk = mrect(0, 124, SW, 140)
    cv.paint(walk, "grey1")
    cv.dth(walk, "ink2", 0.5, 2)
    pool = np.zeros((SH, SW), bool)
    pool = mell(60, 124, 270, 156) & (YY >= 124)
    cv.dth(pool, "blue3", 0.5, 4)
    glow(cv, 166, 126, 100, [("blue4", 0.45)], only=(YY >= 124) & (YY < 150), m=4)
    # road + crosswalk, curb
    cv.paint(mrect(0, 140, SW, 158), "ink2")
    cv.paint(mrect(0, 140, SW, 141), "grey2")
    for xx in range(12, SW, 26):
        cv.paint(mrect(xx, 146, xx + 12, 156), "grey1")
    lamp(cv, 38, 70, 126, arm=8, r=30)
    # bokeh traffic light far left
    bokeh(cv, 20, 100, 5, "red3", "red4", 0.5, 0.9)
    ground_fade(cv, 126, "ink", 0.15, 0.7)
    return cv


def tc_event():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 130), ["ink", "blue0", "purple0", "red0"], "y", 4)
    stars(cv, 28, 24, 50, 9)
    # searchlight beams
    for (bx, ang, c) in [(50, -22, "yellow2"), (270, 22, "blue4"), (112, 14, "orange4")]:
        a = math.radians(ang)
        ex, ey = bx + 150 * math.sin(a), 130 - 150 * math.cos(a)
        beam = mpoly([(bx - 3, 126), (bx + 3, 126), (ex + 14, ey), (ex - 14, ey)])
        cv.dth(beam, c, 0.2, 4)
        cv.dth(mpoly([(bx - 1, 126), (bx + 1, 126), (ex + 5, ey), (ex - 5, ey)]), c, 0.28, 4)
    # mall block
    mall = mrect(34, 52, 286, 128)
    cv.layer(mall, "grey2", "grey1", "grey3", sd=(3, 3), hd=(2, 2), dith=True)
    cv.paint(mrect(34, 52, 286, 58), "ink2")
    neon(cv, 96, 34, "해오름 타운몰", "yellow2", "orange3", f=14, mult=1, glow=0.4)
    cv.paint(mrect(34, 52, 286, 53), "grey4")
    # upper floor glass
    for x0 in range(42, 280, 36):
        cv.paint(mrect(x0, 62, x0 + 28, 82), "blue1")
        cv.dth(mrect(x0, 62, x0 + 28, 82), "blue2", 0.4, 2)
        cv.paint(mrect(x0, 62, x0 + 28, 62), "blue3")
    # entrance: tall glass doors lit warm
    ent = mrect(112, 88, 208, 128)
    cv.paint(ent, "orange3")
    cv.dth(ent, "orange4", 0.5, 4)
    glow(cv, 160, 130, 70, [("yellow2", 0.4)], only=(YY > 100), m=4)
    for xx in (112, 144, 176, 207):
        cv.paint(mrect(xx, 88, xx + 1, 128), "ink2")
    cv.paint(mrect(112, 88, 208, 89), "ink2")
    for xx in (128, 160, 192):
        cv.paint(mrect(xx, 88, xx, 128), "grey2")
    # side shop windows
    for (x0, x1) in [(40, 104), (216, 280)]:
        w_ = mrect(x0, 90, x1, 124)
        cv.paint(w_, "wall3")
        cv.dth(w_, "blue4", 0.5, 4)
        for i, xx in enumerate(range(x0 + 6, x1 - 8, 14)):
            cv.paint(mrect(xx, 100, xx + 8, 124), ["red3", "purple2", "blue2", "green2"][i % 4])
            cv.paint(mrect(xx + 2, 94, xx + 6, 99), "white")
    # grand-opening arch (balloon arch over the entrance), bulbs
    arch_pts = ell_pts(160, 112, 82, 44, 180, 360, 40)
    for i, (ax, ay) in enumerate(arch_pts):
        c, c2 = [("red3", "red4"), ("yellow", "yellow2"), ("blue2", "blue3"), ("green2", "green3"), ("purple2", "blue4")][i % 5]
        r = 5 if i % 2 else 4
        bl = mell(int(ax) - r, int(ay) - r, int(ax) + r, int(ay) + r)
        cv.layer(bl, c, "ink", c2, sd=(2, 2), hd=(1, 1), ol="ink2")
    cv.paint(mrect(74, 112, 80, 128), "red2"); cv.paint(mrect(240, 112, 246, 128), "red2")
    # banner across
    cv.paint(mrect(104, 72, 216, 90), "red2")
    cv.paint(mrect(104, 72, 216, 73), "red3")
    cv.paint(mrect(104, 89, 216, 90), "red1")
    text(cv.img, 112, 63, "그랜드 오픈 · 첫날 반값!", "yellow", 11, edge="ink") if False else None
    neon(cv, 110, 62, "GRAND OPEN", "yellow", None, f=11, outline_c="red1") if False else None
    neon(cv, 118, 74, "그랜드 오픈!!", "yellow", None, f=14, outline_c="red1")
    # bulbs along banner
    for xx in range(106, 216, 8):
        px(cv.img, xx, 92, "yellow2")
    # red carpet
    carpet = mpoly([(150, 128), (170, 128), (196, 158), (124, 158)])
    cv.paint(carpet, "red2")
    cv.dth(carpet, "red1", 0.4, 2)
    cv.paint(mline([(150, 128), (124, 158)], 1), "red3"); cv.paint(mline([(170, 128), (196, 158)], 1), "red3")
    # pavement
    cv.paint(mrect(0, 128, 124, 158), "ink2"); cv.paint(mrect(196, 128, 320, 158), "ink2")
    cv.dth(mrect(0, 128, 320, 158), "grey1", 0.3, 2)
    ground_fade(cv, 120, "ink", 0.2, 0.75)
    return cv


def tc_milk():
    cv = CV("wall3")
    dither_ramp(cv.img, (0, 22, SW, 120), ["blue3", "wall4", "orange3", "orange4", "yellow2"], "y", 4)
    cv.dth(mrect(0, 22, SW, 60), "blue3", vgrad(22, 60, 0.5, 0.0), 4)
    glow(cv, 60, 118, 90, [("yellow2", 0.3)], m=4)
    # distant blocks
    rng = np.random.RandomState(8)
    x = 0
    while x < SW:
        bw = int(rng.randint(14, 30)); bh = int(rng.randint(24, 60))
        b = mrect(x, 124 - bh, x + bw, 124)
        cv.paint(b, "wall3")
        cv.dth(b, "purple2", 0.45, 2)
        x += bw + 2
    # the narrow officetel: tall, slim, centre-right
    bx0, bx1 = 170, 268
    bld = mrect(bx0, 28, bx1, 128)
    cv.layer(bld, "wall1", "wall3", "wall4", sd=(4, 0), hd=(2, 0), dith=True)
    cv.dth(bld, "orange3", hgrad(bx0, bx0 + 20, 0.3, 0.0), 4)
    cv.paint(mrect(bx0, 28, bx1, 32), "grey2")
    window_grid(cv, bx0 + 8, 38, 5, 6, 10, 8, 4, 6, lit_p=0.3, off="blue2", on="yellow2", on2="orange3", seed=5)
    cv.dth(mrect(bx0 + 2, 36, bx1 - 2, 108), "blue3", 0.12, 4)
    # sign + entrance
    cv.paint(mrect(bx0 + 10, 108, bx0 + 88, 118), "green1")
    cv.paint(mrect(bx0 + 10, 108, bx0 + 88, 108), "green2")
    text(cv.img, bx0 + 12, 107, "새벽 오피스텔", "white", 9)
    cv.paint(mrect(bx0 + 34, 118, bx0 + 62, 128), "blue1")
    cv.dth(mrect(bx0 + 34, 118, bx0 + 62, 128), "blue3", 0.45, 4)
    cv.paint(mrect(bx0 + 47, 118, bx0 + 48, 128), "ink2")
    # mailboxes by the door
    for i in range(4):
        cv.paint(mrect(bx0 + 66 + i * 5, 118, bx0 + 69 + i * 5, 123), ["grey3", "grey2"][i % 2])
    # vertical sign on side
    cv.paint(mrect(bx1 + 3, 50, bx1 + 14, 100), "red2")
    for i, ch in enumerate("배달"):
        text(cv.img, bx1 + 3, 54 + i * 14, ch, "white", 11)
    cv.dth(mrect(bx1 + 3, 50, bx1 + 14, 100), "red3", 0.4, 2)
    # neighbouring low shop with shutter
    sh_ = mrect(268, 84, 320, 128)
    cv.layer(sh_, "wall4", "wall3", "white", sd=(3, 3), hd=(2, 2), dith=True)
    for yy in range(96, 126, 3):
        cv.paint(mrect(274, yy, 316, yy), "grey3")
    cv.paint(mrect(274, 92, 316, 94), "ink2")
    # road + sidewalk
    cv.paint(mrect(0, 128, SW, 140), "grey3")
    cv.dth(mrect(0, 128, SW, 140), "wall4", 0.4, 2)
    cv.paint(mrect(0, 140, SW, 158), "grey2")
    cv.dth(mrect(0, 140, SW, 158), "grey1", 0.5, 2)
    cv.paint(mrect(0, 140, SW, 141), "grey4")
    # moped with milk box (delivery), parked at the left, in front
    mx, my = 62, 130
    # shadow
    cv.dth(mell(mx - 26, my + 14, mx + 58, my + 22), "ink2", 0.6, 2)
    for wx in (mx, mx + 44):
        cv.layer(mell(wx - 8, my + 4, wx + 8, my + 20), "ink2", "ink", "grey1", sd=(2, 2), hd=(1, 1))
        cv.paint(mell(wx - 3, my + 9, wx + 3, my + 15), "grey2")
    body = mpoly([(mx + 4, my + 6), (mx + 20, my - 4), (mx + 34, my - 2), (mx + 40, my + 8), (mx + 30, my + 14), (mx + 12, my + 14)])
    cv.layer(body, "blue2", "blue1", "blue3", sd=(3, 3), hd=(2, 2), dith=True)
    cv.layer(mrect(mx + 14, my - 8, mx + 32, my - 4), "ink2", "ink", "grey1", sd=(2, 2), hd=(1, 1))
    cv.paint(mline([(mx + 4, my + 2), (mx - 6, my - 10)], 2), "grey1")
    cv.paint(mrect(mx - 10, my - 12, mx - 2, my - 11), "ink2")
    box = mrect(mx + 22, my - 34, mx + 56, my - 8)
    cv.layer(box, "white", "grey4", None, sd=(3, 3), dith=False)
    cv.paint(mrect(mx + 22, my - 34, mx + 56, my - 31), "blue2")
    cv.paint(mrect(mx + 22, my - 12, mx + 56, my - 10), "blue2")
    text(cv.img, mx + 25, my - 29, "우유", "blue1", 11)
    cv.pts([(mx + 58, my - 20)], "red3")
    # milk crate stack on pavement
    for i in range(3):
        cr = mrect(116, 120 - i * 7 + 8, 138, 126 - i * 7 + 8)
        cv.layer(cr, "orange2", "orange1", "orange3", sd=(2, 2), hd=(1, 1))
    ground_fade(cv, 124, "ink2", 0.0, 0.55)
    return cv


def tc_cinema():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 124), ["ink", "purple0", "blue0", "purple0"], "y", 4)
    stars(cv, 26, 24, 44, 12)
    # old brick facade
    fac = mrect(46, 38, 274, 128)
    cv.layer(fac, "brown1", "brown0", "brown2", sd=(4, 3), hd=(2, 2), dith=True)
    for yy in range(40, 128, 5):
        for xx in range(48 + (yy // 5 % 2) * 6, 274, 12):
            px(cv.img, xx, yy, "brown0")
        cv.paint(mrect(48, yy, 272, yy), "brown0") if False else None
    cv.dth(fac, "ink2", 0.3, 2)
    # cornice
    cv.paint(mrect(40, 34, 280, 40), "brown3")
    cv.paint(mrect(40, 40, 280, 42), "brown0")
    cv.paint(mrect(40, 34, 280, 34), "orange4")
    # vertical name sign
    cv.paint(mrect(30, 40, 44, 124), "ink2")
    cv.paint(mrect(31, 41, 43, 123), "red2")
    cv.dth(mrect(31, 41, 43, 123), "red3", 0.55, 2)
    dither_radial(cv.img, 37, 80, 30, "red3", None, 4, box=(10, 40, 70, 124))
    cv.paint(mrect(30, 40, 44, 124), "ink2")
    cv.paint(mrect(31, 41, 43, 123), "red2")
    cv.dth(mrect(31, 41, 43, 123), "red1", 0.3, 2)
    for i, ch in enumerate("월광극장"):
        text(cv.img, 31, 46 + i * 18, ch, "yellow2", 11)
    # marquee with bulbs
    dither_radial(cv.img, 160, 74, 70, "yellow2", None, 4, box=(60, 40, 260, 124))
    mq = mrect(76, 56, 244, 92)
    cv.layer(mq, "red1", "red0", "red2", sd=(3, 3), hd=(2, 2), ol="ink")
    cv.paint(mrect(80, 60, 240, 88), "ink")
    cv.paint(mrect(82, 62, 238, 86), "yellow2")
    cv.dth(mrect(82, 62, 238, 86), "orange3", 0.35, 2)
    text(cv.img, 90, 62, "심야 상영", "red2", 14)
    text(cv.img, 172, 62, "마지막 회", "ink", 14)
    cv.paint(mrect(86, 83, 234, 83), "orange2")
    text(cv.img, 92, 73, "〈 끝나지 않는 밤 〉", "red1", 11) if False else None
    text(cv.img, 90, 75, "끝나지 않는 밤 · 24:30", "red1", 9)
    for xx in range(78, 244, 6):
        px(cv.img, xx, 58, "yellow") ; px(cv.img, xx + 3, 90, "yellow")
    for yy in range(60, 90, 6):
        px(cv.img, 78, yy, "yellow"); px(cv.img, 242, yy + 3, "yellow")
    # posters + doors
    for (x0, c) in [(58, "blue2"), (84, "purple1")]:
        cv.paint(mrect(x0, 98, x0 + 18, 124), "ink")
        cv.paint(mrect(x0 + 1, 99, x0 + 17, 123), c)
        cv.paint(mell(x0 + 5, 104, x0 + 13, 114), "skin2")
        cv.paint(mrect(x0 + 3, 116, x0 + 15, 120), "white")
    for (x0, c) in [(238, "red2"), (214, "green1")]:
        cv.paint(mrect(x0, 98, x0 + 18, 124), "ink")
        cv.paint(mrect(x0 + 1, 99, x0 + 17, 123), c)
        cv.paint(mell(x0 + 5, 104, x0 + 13, 114), "skin2")
    # glass entrance
    for xx in (112, 140, 168):
        d = mrect(xx, 98, xx + 24, 126)
        cv.paint(d, "orange3")
        cv.dth(d, "orange4", 0.5, 4)
        cv.paint(mrect(xx + 12, 98, xx + 12, 126), "ink2")
        cv.paint(mrect(xx, 98, xx + 24, 98), "ink2")
    # ticket booth
    cv.layer(mrect(194, 100, 210, 126), "grey1", "ink2", "grey2", sd=(2, 2), hd=(1, 1))
    cv.paint(mrect(197, 106, 207, 114), "yellow2")
    # steps + pavement
    for i in range(3):
        cv.paint(mrect(100 - i * 4, 126 + i * 3, 220 + i * 4, 128 + i * 3), "grey2")
        cv.paint(mrect(100 - i * 4, 129 + i * 3, 220 + i * 4, 129 + i * 3), "grey1")
    cv.paint(mrect(0, 126, SW, 158), "ink2")
    cv.dth(mrect(0, 126, SW, 158), "grey1", 0.3, 2)
    glow(cv, 160, 128, 110, [("orange3", 0.35)], only=(YY >= 126), m=4)
    ground_fade(cv, 128, "ink", 0.2, 0.8)
    return cv


def tc_trial():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 130), ["ink", "blue0", "blue0", "ink2"], "y", 4)
    stars(cv, 22, 24, 40, 21)
    # fog bands
    wing = mrect(26, 38, 294, 128)
    cv.layer(wing, "grey1", "ink2", "grey2", sd=(4, 3), hd=(2, 2), dith=True)
    cv.paint(mrect(26, 38, 294, 42), "grey2")
    # window rows: mostly dark, a few lit green-white
    lit_set = {(0, 5), (1, 11), (2, 3), (2, 12), (3, 7), (1, 2), (3, 14), (0, 9)}
    window_grid(cv, 36, 50, 16, 4, 10, 12, 6, 6, lit=lambda r, c: (r, c) in lit_set, off="blue0", on="green3", on2="green2", seed=3)
    for (r, c) in lit_set:
        wx, wy = 36 + c * 16, 50 + r * 18
        g_ = mrect(wx - 3, wy - 3, wx + 12, wy + 14) & ~mrect(wx, wy, wx + 9, wy + 11)
        cv.dth(g_, "green1", 0.5, 2)
        cv.paint(mrect(wx, wy, wx + 9, wy + 11), "green3")
        cv.paint(mrect(wx + 4, wy, wx + 5, wy + 11), "green1")
        cv.paint(mrect(wx, wy + 9, wx + 9, wy + 11), "yellow2")
    # sign plate + cross
    cv.paint(mrect(112, 126 - 18, 208, 126 - 8), "ink") if False else None
    # ground floor lobby
    cv.paint(mrect(120, 106, 200, 128), "pale2")
    cv.dth(mrect(120, 106, 200, 128), "green3", 0.6, 4)
    cv.paint(mrect(158, 106, 160, 128), "ink2")
    cv.paint(mrect(110, 100, 210, 105), "ink2")
    cv.paint(mrect(112, 86, 208, 100), "ink")
    cv.paint(mrect(112, 86, 208, 86), "green2")
    text(cv.img, 117, 88, "제3 임상시험센터", "green3", 9)
    # green cross on side
    cv.paint(mrect(268, 94, 280, 100), "green2"); cv.paint(mrect(271, 91, 277, 103), "green2")
    # overhead canopy glow + ambulance bay light (red)
    cv.dth(mell(100, 126, 220, 150), "green3", 0.3, 4)
    bokeh(cv, 288, 120, 5, "red3", "red4", 0.5, 0.9)
    # trees, fog, path
    for tx in (14, 306):
        cv.paint(mell(tx - 20, 80, tx + 20, 130), "green0")
        cv.dth(mell(tx - 20, 80, tx + 20, 130), "ink", 0.5, 2)
    cv.paint(mrect(0, 128, SW, 158), "ink2")
    cv.dth(mrect(0, 128, SW, 158), "blue0", 0.5, 2)
    path = mpoly([(150, 128), (170, 128), (210, 158), (110, 158)])
    cv.paint(path, "grey1")
    cv.dth(path, "green1", 0.25, 4)
    fog = (YY > 112) & (YY < 140)
    cv.dth(fog, "pale1", vgrad(112, 140, 0.0, 0.3) * 1.0, 4)
    lamp(cv, 96, 100, 130, bulb="green3", glow_c="green2", r=14, arm=6)
    lamp(cv, 230, 100, 130, bulb="green3", glow_c="green2", r=14, arm=-6)
    ground_fade(cv, 128, "ink", 0.2, 0.8)
    return cv


def tc_site():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 130), ["ink", "blue0", "purple0", "blue0"], "y", 4)
    stars(cv, 18, 24, 50, 33)
    # tower crane: mast, slewing unit, long jib, counter-jib, weights
    mx = 214
    mast_l, mast_r = mx - 6, mx + 6
    for yy in range(46, 130, 8):
        cv.paint(mline([(mast_l, yy), (mast_r, yy + 8)], 1), "grey2")
        cv.paint(mline([(mast_r, yy), (mast_l, yy + 8)], 1), "grey2")
    cv.paint(mrect(mast_l - 1, 46, mast_l + 1, 130), "grey3")
    cv.paint(mrect(mast_r - 1, 46, mast_r + 1, 130), "grey3")
    cv.layer(mrect(mx - 12, 38, mx + 12, 46), "grey2", "grey1", "grey3", sd=(2, 2), hd=(1, 1))
    cv.layer(mrect(mx - 6, 28, mx + 6, 38), "grey1", "ink2", "grey2", sd=(2, 2), hd=(1, 1))
    cv.paint(mrect(mx - 4, 32, mx + 2, 35), "yellow2")
    # jib (to the left) + counter jib (right)
    cv.layer(mpoly([(mx, 34), (mx - 150, 40), (mx - 150, 46), (mx, 44)]), "grey2", "grey1", "grey3", sd=(2, 2), hd=(1, 1))
    for xx in range(mx - 148, mx, 10):
        cv.paint(mline([(xx, 41), (xx + 5, 45), (xx + 10, 41)], 1), "grey1")
    cv.paint(mline([(mx, 22), (mx - 150, 40)], 1), "grey2") if False else None
    cv.layer(mpoly([(mx, 34), (mx + 52, 38), (mx + 52, 43), (mx, 44)]), "grey2", "grey1", "grey3", sd=(2, 2), hd=(1, 1))
    cv.paint(mrect(mx + 36, 42, mx + 52, 54), "grey2")
    cv.paint(mrect(mx + 36, 42, mx + 52, 43), "grey3")
    # A-frame cable
    cv.paint(mline([(mx - 3, 22), (mx - 120, 40)], 1), "grey3"); cv.paint(mline([(mx + 3, 22), (mx + 50, 38)], 1), "grey3")
    cv.paint(mrect(mx - 1, 22, mx + 1, 36), "grey1")
    cv.dth(mpoly([(250, 98), (268, 98), (mx + 24, 28), (mx - 24, 28)]), "yellow2", 0.1, 4)
    # hook line + load
    cv.paint(mrect(80, 44, 80, 92), "grey2")
    cv.paint(mrect(74, 92, 86, 96), "yellow")
    cv.paint(mrect(66, 96, 94, 110), "orange1")
    cv.dth(mrect(66, 96, 94, 110), "orange2", 0.4, 2)
    # red aircraft beacon
    bokeh(cv, mx, 18 + 6, 3, "red3", "red4", 0.7, 1.0)
    px(cv.img, mx, 24, "red4")
    # unfinished concrete building (frame) left
    for fl in range(4):
        y = 118 - fl * 22
        cv.paint(mrect(22, y, 150, y + 3), "grey2")
        cv.paint(mrect(22, y + 3, 150, y + 3), "grey1")
    for xx in (24, 62, 100, 138):
        cv.paint(mrect(xx, 52, xx + 5, 120), "grey2")
        cv.paint(mrect(xx, 52, xx, 120), "grey3")
        cv.paint(mrect(xx + 5, 52, xx + 5, 120), "grey1")
    for (xx, yy) in [(26, 51), (64, 51), (102, 51), (140, 51)]:
        for i in range(4):
            cv.paint(mrect(xx + i, yy - 8 - (i % 2) * 2, xx + i, yy), "orange1")
    cv.dth(mrect(22, 52, 150, 120), "ink", 0.35, 2)
    # floodlights on stands (bright cones)
    for (fx, fy, tx_) in [(172, 92, 140), (96, 100, 130), (262, 98, 232)]:
        cv.paint(mrect(fx, fy, fx + 1, 126), "ink2")
        cv.paint(mrect(fx - 5, fy - 4, fx + 6, fy + 1), "grey3")
        cone = mpoly([(fx - 4, fy), (fx + 5, fy), (tx_ + 40, 128), (tx_ - 36, 128)])
        cv.dth(cone, "yellow2", 0.18, 4)
        cv.dth(mpoly([(fx - 2, fy), (fx + 3, fy), (tx_ + 16, 128), (tx_ - 14, 128)]), "white", 0.18, 4)
        dither_radial(cv.img, fx, fy, 14, "white", None, 4)
        cv.paint(mrect(fx - 4, fy - 2, fx + 5, fy), "white")
    # hoarding fence with sheets + gate sign
    fence = mrect(0, 112, SW, 130)
    cv.paint(fence, "blue1")
    for xx in range(0, SW, 20):
        cv.paint(mrect(xx, 112, xx + 1, 130), "blue0")
        cv.paint(mrect(xx + 2, 112, xx + 2, 130), "blue2")
    cv.paint(mrect(0, 112, SW, 113), "grey3")
    cv.dth(fence, "ink", 0.25, 2)
    sign = mrect(222, 98, 310, 122)
    cv.layer(sign, "yellow", "orange2", "yellow2", sd=(2, 2), hd=(1, 1))
    text(cv.img, 228, 98, "안전제일", "ink", 11)
    text(cv.img, 228, 110, "신축 공사 현장", "ink", 9)
    # gravel ground, hazard stripes
    cv.paint(mrect(0, 130, SW, 158), "grey1")
    cv.dth(mrect(0, 130, SW, 158), "ink2", 0.5, 2)
    glow(cv, 150, 130, 120, [("grey3", 0.3)], only=(YY >= 130), m=4)
    for xx in range(0, SW, 14):
        cv.paint(mpoly([(xx, 131), (xx + 6, 131), (xx + 2, 135), (xx - 4, 135)]), "yellow")
    # dust haze
    cv.dth(mrect(0, 100, SW, 132), "yellow2", vgrad(100, 132, 0.0, 0.18), 4)
    ground_fade(cv, 126, "ink", 0.15, 0.8)
    return cv


def tc_park():
    cv = CV("ink")
    dither_ramp(cv.img, (0, 22, SW, 130), ["ink", "blue0", "purple0", "red0"], "y", 4)
    stars(cv, 26, 24, 60, 17)
    # big wheel silhouette behind (half lit)
    wx, wy, wr = 232, 78, 46
    ring = mell(wx - wr, wy - wr, wx + wr, wy + wr) & ~mell(wx - wr + 3, wy - wr + 3, wx + wr - 3, wy + wr - 3)
    cv.paint(ring, "ink2")
    for a_ in range(0, 360, 30):
        r_ = math.radians(a_)
        cv.paint(mline([(wx, wy), (wx + (wr - 2) * math.cos(r_), wy + (wr - 2) * math.sin(r_))], 1), "ink2")
        gx, gy = wx + wr * math.cos(r_), wy + wr * math.sin(r_)
        if (a_ // 30) % 3 == 0:
            bokeh(cv, int(gx), int(gy), 3, "red3", "red4", 0.5, 0.9)
        else:
            cv.paint(mell(int(gx) - 3, int(gy) - 3, int(gx) + 3, int(gy) + 3), "ink2")
    cv.paint(mline([(wx, wy), (wx - 24, 130)], 2), "ink2"); cv.paint(mline([(wx, wy), (wx + 24, 130)], 2), "ink2")
    # far tents / coaster hump
    cv.paint(mpoly([(0, 112), (30, 84), (60, 112)]), "ink2")
    cv.paint(mpoly([(40, 112), (70, 70), (100, 112)]), "ink2")
    cv.dth(mpoly([(40, 112), (70, 70), (100, 112)]), "purple0", 0.4, 2)
    # entrance arch gate
    cv.paint(mrect(92, 32, 224, 52), "ink2")
    cv.paint(mrect(92, 32, 224, 32), "grey1")
    arch = mpoly([(80, 128), (80, 74), (110, 54), (206, 54), (236, 74), (236, 128), (226, 128), (226, 78), (204, 62), (112, 62), (90, 78), (90, 128)])
    cv.layer(arch, "purple1", "purple0", "purple2", sd=(3, 3), hd=(2, 2), dith=True)
    # sign letters, only some lit
    word = "달나라 놀이공원"
    lit_i = {0, 2, 4, 5, 8}
    x = 96
    for i, ch in enumerate(word):
        if ch == " ":
            x += 6
            continue
        if i in lit_i:
            neon(cv, x, 34, ch, "yellow2", "orange3", f=14, glow=0.45, gr=1)
        else:
            text(cv.img, x, 34, ch, "grey1", 14)
            if i % 3 == 1:
                px(cv.img, x + 5, 48, "red2")
        x += 14
    # bulbs around the arch (half dead)
    pts = ell_pts(158, 108, 78, 52, 180, 360, 34)
    for i, (bx, by) in enumerate(pts):
        if i % 2 == 0:
            px(cv.img, int(bx), int(by) - 3, "yellow2"); px(cv.img, int(bx) + 1, int(by) - 3, "orange3")
        else:
            px(cv.img, int(bx), int(by) - 3, "grey1")
    for i, y in enumerate(range(84, 124, 5)):
        for xx in (83, 233):
            px(cv.img, xx, y, "yellow2" if i % 3 else "grey1")
    # iron gates, chained
    gate = mrect(92, 84, 224, 128)
    cv.paint(gate, "ink")
    for xx in range(94, 224, 7):
        cv.paint(mrect(xx, 84, xx + 1, 128), "grey1")
        cv.paint(mrect(xx, 84, xx, 128), "grey2")
        px(cv.img, xx, 82, "grey2")
    cv.paint(mrect(92, 98, 224, 99), "grey1")
    cv.paint(mrect(92, 116, 224, 117), "grey1")
    cv.paint(mrect(156, 84, 160, 128), "ink2")
    # chain + padlock
    for i in range(0, 18, 3):
        cv.paint(mell(150 + i, 104 + (i % 2) * 2, 154 + i, 108 + (i % 2) * 2), "grey3")
    cv.layer(mrect(154, 108, 162, 116), "yellow", "orange2", "yellow2", sd=(1, 1), hd=(1, 1))
    # ticket booth, shuttered
    cv.layer(mrect(236, 98, 270, 128), "grey1", "ink2", "grey2", sd=(3, 3), hd=(2, 2))
    for yy in range(102, 126, 3):
        cv.paint(mrect(240, yy, 266, yy), "grey2")
    text(cv.img, 241, 89, "매표소", "grey3", 9)
    # ground
    cv.paint(mrect(0, 128, SW, 158), "ink2")
    cv.dth(mrect(0, 128, SW, 158), "purple0", 0.5, 2)
    for xx in range(0, SW, 18):
        cv.paint(mrect(xx, 140, xx + 8, 141), "grey1")
    lamp(cv, 40, 84, 130, bulb="orange3", glow_c="orange3", r=20, arm=6)
    # broken lamp
    cv.paint(mrect(280, 90, 281, 130), "ink2"); cv.paint(mrect(280, 90, 274, 90), "ink2")
    px(cv.img, 274, 92, "red3")
    # fog
    cv.dth((YY > 108) & (YY < 140), "purple2", vgrad(108, 140, 0.0, 0.25), 4)
    ground_fade(cv, 126, "ink", 0.15, 0.8)
    return cv


# ============================================================ run
def build_all():
    out = []
    out.append(cu_sora_phone())
    out.append(cu_kwak_offer().save("cu_kwak_offer"))
    out.append(cu_junho().save("cu_junho"))
    out.append(cu_regular().save("cu_regular"))
    out.append(cu_sora_relief().save("cu_sora_relief"))
    out.append(cu_sora_desk().save("cu_sora_desk"))
    for name, fn in [("tc_store", tc_store), ("tc_event", tc_event), ("tc_milk", tc_milk), ("tc_cinema", tc_cinema),
                     ("tc_trial", tc_trial), ("tc_site", tc_site), ("tc_park", tc_park)]:
        out.append(fn().save(name))
    contact(out, "_contact/closeups.png", cols=3, scale=2)
    return out


if __name__ == "__main__":
    only = sys.argv[1:]
    if only:
        fns = {k: v for k, v in globals().items() if k.startswith(("cu_", "tc_")) and callable(v)}
        for n in only:
            r = fns[n]()
            if isinstance(r, CV):
                r.save(n)
    else:
        for p in build_all():
            print(p)

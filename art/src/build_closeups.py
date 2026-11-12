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
    mouth(cv, cx, H.mouth_y + 1, "grin", c="skin0")
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
    plate = mrect(222, 140, 262, 149)
    cv.layer(plate, "yellow", "orange2", "yellow2", sd=(0, 2), hd=(0, -1))
    text(cv.img, 227, 138, "곽 실장", "ink", 9)
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
        cv.dth(mell(cx + sd_ * 14 - 5, ey + 7, cx + sd_ * 14 + 5, ey + 13) & hmask, "red4", 0.4, 2)
        ex = cx + sd_ * H.eye_dx
        eye(cv, ex, ey, sd_, w=13, h=14, iris="brown1", iris2="brown2", lid=2, look=(0, -2), hl="white", bag=True,
            skin_sh="skin1", lidc="skin2")
        cv.pts([(ex - 3, ey + 6), (ex - 2, ey + 6), (ex + 2, ey + 6)], "blue4")      # wet lower lid
        brow(cv, ex, ey - 11, sd_, 11, tilt=-3, c="purple0", thick=2)
        # tired bags
        cv.pts([(ex + i, ey + 9) for i in range(-4, 5)], "skin1")
    cv.pts([(cx, ey + 12), (cx + 1, ey + 12), (cx - 1, ey + 13)], "skin1")
    mouth(cv, cx, H.mouth_y, "smile", c="skin0", lip="skin1")
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
    hands = mell(cx - 22, 132, cx + 22, 154)
    cv.layer(hands, "skin2", "skin1", "skin3", sd=(3, 4), hd=(2, 2))
    for fx in (-12, -5, 2, 9, 16):
        cv.pts([(cx + fx, 141), (cx + fx, 142), (cx + fx, 143)], "skin1")
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


if __name__ == "__main__":
    cu_junho().save("cu_junho")

"""Exterior / title / death / clock-in backgrounds for ONE MORE SHIFT.
Run:  python3 src/build_bg_exterior.py   -> assets/bg/*.png, previews/bg/*.png
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from pxkit import *
from pxkit import _thr

Y0, Y1 = 22, 157          # picture area


# ------------------------------------------------------------------ helpers
def obox(img, x, y, w, h, fill, hi=None, sh=None, ol="ink"):
    """Outlined box with optional top-left highlight / bottom-right shadow line."""
    rect(img, x, y, w, h, fill, ol)
    if hi and w > 3 and h > 3:
        line(img, [(x + 1, y + 1), (x + w - 3, y + 1)], hi)
        line(img, [(x + 1, y + 1), (x + 1, y + h - 3)], hi)
    if sh and w > 3 and h > 3:
        line(img, [(x + 2, y + h - 2), (x + w - 2, y + h - 2)], sh)
        line(img, [(x + w - 2, y + 2), (x + w - 2, y + h - 2)], sh)


def hline(img, x0, x1, y, c):
    line(img, [(x0, y), (x1, y)], c)


def vline(img, x, y0, y1, c):
    line(img, [(x, y0), (x, y1)], c)


def wire(img, p0, p1, sag, c="ink", steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((round(p0[0] + (p1[0] - p0[0]) * t),
                    round(p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t))))
    line(img, pts, c)


def streaks(img, box, c1, c2, n, seed, maxlen=14, level=0.5):
    """Vertical dithered stain streaks inside box (only on pixels currently c1)."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    base = col(c1)
    for _ in range(n):
        x = rnd.randint(x0, x1 - 2)
        y = rnd.randint(y0, y1 - 4)
        w = rnd.choice([1, 2, 2, 3])
        l = rnd.randint(4, maxlen)
        for yy in range(y, min(y1, y + l)):
            f = 1 - (yy - y) / l
            for xx in range(x, min(x1, x + w)):
                if img.getpixel((xx, yy)) == base and f * level * 1.6 > _thr(xx, yy, 4):
                    img.putpixel((xx, yy), col(c2))


def patches(img, box, c1, c2, n, seed, level=0.5, wmax=14, hmax=8):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    base = col(c1)
    for _ in range(n):
        w, h = rnd.randint(3, wmax), rnd.randint(2, hmax)
        x, y = rnd.randint(x0, x1 - w), rnd.randint(y0, y1 - h)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if img.getpixel((xx, yy)) == base and level > _thr(xx, yy, 2):
                    img.putpixel((xx, yy), col(c2))


def cloud(img, x, y, w, h=7):
    m = new(W, H)
    ellipse(m, x, y + h // 2, x + w, y + h, "white")
    ellipse(m, x + w // 5, y, x + w // 2 + 4, y + h, "white")
    ellipse(m, x + w // 2 - 2, y + 2, x + w - 6, y + h, "white")
    ys = img
    for yy in range(y, y + h + 2):
        for xx in range(x - 1, x + w + 2):
            if m.getpixel((xx, yy))[3]:
                below = m.getpixel((xx, min(H - 1, yy + 2)))[3]
                ys.putpixel((xx, yy), col("grey4") if (not below) else col("white"))


def window(img, x, y, w, h, frame="grey4", glass="blue3", lit=False):
    obox(img, x, y, w, h, frame, "white", "grey3")
    gx, gy, gw, gh = x + 2, y + 2, w - 4, h - 4
    rect(img, gx, gy, gw, gh, glass, "ink")
    # sky reflection (dithered diagonal)
    dither_grad(img, (gx + 1, gy + 1, gx + gw - 1, gy + gh - 1), "blue4", glass, "d", 4, 0.9, 0.0)
    if w >= 14:
        vline(img, gx + gw // 2, gy, gy + gh - 1, "ink")
    hline(img, gx, gx + gw - 1, gy + gh // 2 + 1, "ink")


def ac_unit(img, x, y, w=13, h=9):
    # bracket
    line(img, [(x + 1, y + h), (x - 2, y + h + 4)], "ink")
    line(img, [(x + w - 2, y + h), (x + w + 1, y + h + 4)], "ink")
    obox(img, x, y, w, h, "grey4", "white", "grey3")
    cx, cy = x + w // 2 - 2, y + h // 2
    ellipse(img, cx - 3, cy - 3, cx + 3, cy + 3, "grey2", "ink")
    px(img, cx, cy, "ink")
    for i in range(x + w - 5, x + w - 2, 2):
        vline(img, i, y + 2, y + h - 3, "grey2")
    # drip stain below
    for yy in range(y + h + 1, y + h + 9):
        if (yy - y) % 2 == 0 or yy < y + h + 5:
            px(img, x + w - 4, yy, "grey3")
            px(img, x + w - 3, yy, "grey3")


def stripes(img, box, c1, c2, period=6, axis_slant=True):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = ((x + y) // (period // 2)) % 2
            img.putpixel((x, y), col(c1 if k else c2))


def sign(img, x, y, w, h, bg, s, tc="white", edge="ink", f=9, bgh=None, ty=1):
    obox(img, x, y, w, h, bg, bgh, None)
    tw, _ = text_size(s, f)
    text(img, x + (w - tw) // 2, y + ty, s, tc, f, edge=edge)


def lift_map(m):
    return {col(a): col(b) for a, b in m.items()}


def apply_map(img, mp, mask_fn, passes=1):
    for y in range(Y0, Y1):
        for x in range(W):
            f = mask_fn(x, y)
            if f > 0 and f > _thr(x, y, 4):
                c = img.getpixel((x, y))
                for _ in range(passes):
                    c = mp.get(c, c)
                img.putpixel((x, y), c)


# ------------------------------------------------------------ scene 1 / 2
GY = 138          # ground line of building
WALK = 150

STREET_LIT = {"conv": (138, 91, 66, 12), "win3": (124, 60, 62, 22), "lamp": (40, 60)}


def apt_block(img, x, y, w, h, night=False, seed=0):
    rnd = random.Random(seed)
    rect(img, x, y, w, h, "blue3", "grey2")
    dither_flat(img, (x + 1, y + 1, x + w // 2, y + h), "blue3", "blue4", 0.5, 2)
    for yy in range(y + 4, y + h - 3, 5):
        for xx in range(x + 3, x + w - 3, 5):
            c = "blue2" if rnd.random() > 0.12 else "grey3"
            rect(img, xx, yy, 3, 2, c)
    hline(img, x, x + w - 1, y + 1, "grey3")
    # rooftop box
    rect(img, x + w // 3, y - 3, w // 3, 3, "blue3", "grey2")


def street(night=False):
    img = new(W, H, "ink")
    # ---- sky
    if night:
        dither_ramp(img, (0, Y0, W, 118), ["ink", "blue0", "blue1"], m=4)
        rnd = random.Random(5)
        for _ in range(26):
            px(img, rnd.randint(2, W - 3), rnd.randint(Y0 + 1, 60), rnd.choice(["white", "yellow2", "blue3"]))
        ellipse(img, 272, 30, 284, 42, "yellow2", None)
        ellipse(img, 276, 29, 288, 41, "blue0", None)   # crescent bite
        dither_radial(img, 278, 36, 16, "blue1", None, 4)
    else:
        dither_ramp(img, (0, Y0, W, 118), ["blue3", "blue4", "wall1"], m=4)
        cloud(img, 22, 32, 36)
        cloud(img, 120, 26, 30, 6)
        cloud(img, 232, 34, 40)
        cloud(img, 186, 44, 24, 5)
    # ---- distant apartment blocks
    for i, (x, y, w, h) in enumerate([(6, 44, 26, 80), (36, 58, 20, 66), (96, 50, 22, 74), (130, 62, 16, 62),
                                        (206, 46, 24, 78), (262, 56, 22, 68), (292, 40, 26, 84)]):
        apt_block(img, x, y, w, h, night, i)
    # horizon haze
    dither_grad(img, (0, 104, W, 124), "blue3", "wall3", "y", 4, 0, 0.8,
                mask=None) if False else None

    # ---- left neighbour (3-storey, pink plaster)
    lx0, lx1, lt = 0, 50, 44
    rect(img, lx0 - 1, lt, lx1 - lx0 + 1, GY - lt, "wall4", "ink")
    dither_flat(img, (lx0, lt + 1, lx1, GY), "wall4", "wall1", 0.25, 2)
    streaks(img, (lx0 + 1, lt + 2, lx1 - 1, GY - 2), "wall4", "grey3", 14, 11)
    obox(img, lx0 - 1, lt - 3, lx1 - lx0 + 2, 4, "grey3", "grey4")
    for fy in (lt + 6, lt + 30, lt + 54):
        pass
    for (wx, wy) in [(6, lt + 7), (28, lt + 7), (6, lt + 30), (28, lt + 30)]:
        window(img, wx, wy, 16, 16)
        obox(img, wx - 1, wy + 17, 18, 3, "grey3", "grey4")
    ac_unit(img, 8, lt + 53 - 11, 12, 8)
    # laundry on railing
    obox(img, 24, lt + 52, 24, 3, "grey2", None)
    for i, c in enumerate(["white", "blue3", "wall4", "yellow2", "white"]):
        rect(img, 25 + i * 4, lt + 55, 3, 6, c, "ink")
    # ground shop front left
    rect(img, 0, 96, 50, 42, "wall1", "ink")
    sign(img, 6, 98, 38, 11, "orange1", "복덕방", "yellow", "ink", 9, "orange2")
    window(img, 4, 112, 36, 24, "grey3", "blue3")
    rect(img, 6, 120, 32, 14, "wall1", "ink")  # paper-covered listings
    for i in range(5):
        rect(img, 8 + i * 6, 122 + (i % 2) * 4, 5, 6, ["white", "yellow2", "wall4", "white", "green3"][i], "ink")

    # ---- right neighbour (low, blue-grey plaster)
    rx0, rt = 250, 74
    rect(img, rx0, rt, W - rx0 + 1, GY - rt, "wall3", "ink")
    dither_flat(img, (rx0 + 1, rt + 1, W, GY), "wall3", "wall2", 0.3, 2)
    streaks(img, (rx0 + 2, rt + 2, W - 1, GY - 2), "wall3", "grey3", 10, 21)
    obox(img, rx0 - 1, rt - 4, W - rx0 + 2, 5, "grey3", "grey4")
    window(img, 262, rt + 8, 18, 14)
    window(img, 290, rt + 8, 18, 14)
    ac_unit(img, 292, rt + 29, 12, 8)
    # pharmacy
    rect(img, 252, 106, 68, 32, "wall1", "ink")
    sign(img, 254, 97, 50, 11, "green1", "초록약국", "white", "ink", 9, "green2")
    ellipse(img, 308, 98, 318, 108, "white", "ink")
    rect(img, 312, 99, 2, 8, "green1")
    rect(img, 309, 102, 8, 2, "green1")
    window(img, 256, 112, 30, 22, "grey4", "blue3")
    obox(img, 290, 110, 24, 28, "grey4", "white", "grey3")
    rect(img, 293, 113, 18, 22, "blue3", "ink")
    vline(img, 302, 113, 134, "ink")

    # ================= MAIN BUILDING  x 54..246
    BX0, BX1 = 54, 246
    BW = BX1 - BX0
    # roof clutter
    obox(img, 66, 36, 18, 12, "blue2", "blue3", "blue1")          # water tank
    for yy in (40, 44):
        hline(img, 67, 82, yy, "blue1")
    rect(img, 68, 48, 2, 4, "ink"); rect(img, 80, 48, 2, 4, "ink")
    line(img, [(214, 50), (214, 34)], "ink")                        # tv antenna
    line(img, [(208, 38), (220, 38)], "ink"); line(img, [(210, 43), (218, 43)], "ink")
    line(img, [(209, 34), (219, 34)], "ink")
    # parapet / roof edge
    obox(img, BX0 - 3, 49, BW + 6, 6, "grey3", "grey4", "grey2")
    # upper floor wall
    rect(img, BX0, 55, BW, 34, "wall1", "ink")
    dither_flat(img, (BX0 + 1, 56, BX1 - 1, 88), "wall1", "wall2", 0.22, 2)
    # floor band
    obox(img, BX0 - 2, 87, BW + 4, 4, "grey3", "grey4", "grey2")
    # ground floor wall
    rect(img, BX0, 91, BW, GY - 91, "wall2", "ink")
    dither_flat(img, (BX0 + 1, 92, BX1 - 1, GY), "wall2", "wall1", 0.3, 2)
    # plinth
    rect(img, BX0, GY - 3, BW, 3, "grey2", "ink")
    hline(img, BX0 + 1, BX1 - 2, GY - 3, "grey3")

    dither_grad(img, (BX0 + 1, 56, BX1 - 1, 62), "grey2", "wall1", "y", 4, 0.0, 1.0)
    # ---- upper floor windows
    # w1: residence with curtain
    window(img, 60, 60, 22, 24, "grey4", "blue3")
    rect(img, 63, 63, 8, 18, "wall4", "ink")
    for yy in range(65, 80, 3):
        hline(img, 64, 69, yy, "wall1")
    # w2 with AC
    window(img, 92, 60, 22, 24, "grey4", "blue3")
    ac_unit(img, 96, 74, 13, 9)
    # bars on w2
    for xx in (96, 100, 104, 108):
        pass
    # w3: agency ribbon window (taped paper)
    obox(img, 124, 59, 62, 26, "grey4", "white", "grey3")
    rect(img, 126, 61, 58, 22, "blue3", "ink")
    dither_grad(img, (127, 62, 183, 82), "blue4", "blue3", "d", 4, 0.9, 0.0)
    for xx in (144, 164):
        vline(img, xx, 61, 82, "ink")
    # film-lettering and taped notices on glass
    rect(img, 129, 65, 12, 9, "white", "ink"); hline(img, 131, 138, 68, "grey3"); hline(img, 131, 138, 71, "grey3")
    rect(img, 148, 64, 11, 8, "yellow2", "ink"); hline(img, 150, 157, 67, "orange2")
    rect(img, 168, 66, 12, 10, "white", "ink"); hline(img, 170, 177, 69, "grey3"); hline(img, 170, 177, 72, "grey3")
    # blind slats
    for yy in range(62, 66, 2):
        hline(img, 146, 162, yy, "wall3")
    # vertical hanging sign (new dawn staffing)
    obox(img, 190, 47, 15, 48, "blue1", "blue2", "blue0")
    for i, ch in enumerate("새벽인력"):
        text(img, 192, 49 + i * 10, ch, "yellow", 9, edge="ink")
    line(img, [(197, 43), (197, 47)], "ink")
    # w4 with AC
    window(img, 210, 60, 28, 24, "grey4", "blue3")
    ac_unit(img, 226, 74, 12, 8)
    # ---- railings under windows
    for (rx, rw) in [(58, 26), (90, 26), (208, 32)]:
        obox(img, rx, 84, rw, 3, "grey2", "grey3")
    # stains
    streaks(img, (BX0 + 1, 56, BX1 - 1, 88), "wall1", "grey3", 22, 3, 14, 0.7)
    streaks(img, (BX0 + 1, 92, BX1 - 1, GY - 4), "wall2", "grey3", 24, 4, 16, 0.6)
    patches(img, (BX0 + 2, 56, BX1 - 2, 86), "wall1", "wall4", 8, 9)
    # exposed brick patch (peeling plaster)
    for (px0, py0, pw, ph) in [(116, 58, 8, 5), (240, 70, 4, 6)]:
        rect(img, px0, py0, pw, ph, "brown3", None)
        dither_flat(img, (px0, py0, px0 + pw, py0 + ph), "brown3", "orange1", 0.4, 2)
    # cracks
    for pts in [[(118, 74), (120, 77), (119, 80), (122, 83)], [(88, 58), (86, 62), (87, 66)], [(176, 93), (178, 97), (177, 101)]]:
        line(img, pts, "grey2")

    # ---- ground floor
    # laundry (은하 세탁)  x 54..101
    sign(img, 54, 91, 48, 12, "green1", "세탁", "white", "ink", 9, "green2")
    obox(img, 56, 105, 44, 31, "grey3", "grey4", "grey2")
    rect(img, 58, 107, 40, 27, "blue3", "ink")
    dither_grad(img, (59, 108, 97, 133), "blue4", "blue3", "d", 4, 0.9, 0.0)
    for i in range(3):
        mx = 60 + i * 12
        obox(img, mx, 118, 11, 14, "white", None, "grey3")
        ellipse(img, mx + 2, 121, mx + 8, 127, "blue2", "ink")
        ellipse(img, mx + 3, 122, mx + 5, 124, "blue3", None)
    hline(img, 59, 96, 113, "ink")
    for i, c in enumerate(["yellow2", "wall4", "white", "blue3", "yellow2"]):   # hanging clothes
        line(img, [(61 + i * 7, 108), (61 + i * 7, 109)], "ink")
        rect(img, 60 + i * 7, 109, 5, 5, c, "ink")
    # stairwell entry  x 102..127
    obox(img, 102, 95, 26, 43, "grey3", "grey4", "grey2")
    rect(img, 105, 98, 20, 40, "ink2", "ink")
    for i in range(7):
        y_ = 134 - i * 5
        rect(img, 107 + i * 2, y_, 18 - i * 2, 4, "grey2" if i % 2 else "grey1")
        hline(img, 107 + i * 2, 124, y_, "grey3")
    rect(img, 110, 101, 10, 2, "grey4", "ink")
    dither_radial(img, 115, 103, 9, "grey1", None, 4, (106, 99, 124, 112))
    obox(img, 105, 98, 7, 40, "grey4", "white", "grey3")
    rect(img, 107, 101, 3, 30, "blue3", "ink")
    px(img, 111, 118, "ink")
    # intercom plate
    rect(img, 129 - 0, 104, 0, 0, "ink") if False else None
    # convenience store (달빛 편의점) x 128..194
    sign(img, 128, 91, 66, 12, "blue1", "달빛 편의점", "yellow", "ink", 9, "blue2", 1)
    ellipse(img, 131, 93, 137, 99, "yellow2", None); ellipse(img, 133, 92, 139, 98, "blue1", None)
    # redo text offset (right aligned) so logo never overlaps
    rect(img, 140, 92, 53, 10, "blue1", None)
    rect(img, 139, 92, 1, 10, "blue1", None)
    text(img, 141, 92, "달빛 편의점", "yellow", 9, edge="ink")
    obox(img, 128, 105, 66, 31, "grey4", "white", "grey3")
    rect(img, 130, 107, 62, 27, "blue3", "ink")
    rect(img, 131, 108, 60, 25, "wall1", None)
    dither_flat(img, (131, 108, 191, 133), "wall1", "white", 0.5, 2)
    for sy in (115, 123, 131):
        hline(img, 131, 190, sy, "grey2")
    prod = ["red2", "yellow", "blue2", "green2", "orange2", "white", "purple2", "red3", "green1", "blue3"]
    rnd = random.Random(8)
    for r_, sy in enumerate((108, 116, 124)):
        for i in range(11):
            h_ = rnd.choice([4, 5, 6])
            if 7 <= i <= 9:
                continue
            rect(img, 132 + i * 5 + (r_ % 2) * 1, sy + 7 - h_, 4, h_, prod[(i + r_ * 3) % len(prod)], "ink")
    # door
    obox(img, 164, 106, 26, 30, "grey4", "white", "grey3")
    rect(img, 166, 108, 22, 26, "blue3", "ink")
    dither_grad(img, (167, 109, 187, 133), "blue4", "blue3", "d", 4, 0.9, 0.0)
    rect(img, 176, 120, 2, 8, "grey2", "ink")
    vline(img, 177, 108, 133, "ink")
    rect(img, 169, 112, 7, 7, "red2", "ink"); text(img, 169, 110, "24", "white", 7)
    # hardware shop (만복 철물) x 196..246 -- roll-down shutter
    sign(img, 196, 91, 50, 12, "red1", "만복 철물", "yellow", "ink", 9, "red2")
    obox(img, 196, 105, 50, 33, "grey3", "grey4", "grey2")
    rect(img, 198, 107, 46, 29, "grey3", "ink")
    for yy in range(108, 135, 3):
        hline(img, 199, 242, yy, "grey2")
        hline(img, 199, 242, yy + 1, "grey4")
    patches(img, (199, 108, 242, 134), "grey3", "orange1", 7, 77, 0.35, 5, 3)
    rect(img, 218, 130, 7, 3, "grey1", "ink")
    rect(img, 220, 133, 2, 2, "yellow", None)
    dither_flat(img, (198, 107, 244, 112), "grey3", "grey1", 0.5, 2)
    dither_flat(img, (198, 112, 244, 114), "grey3", "grey1", 0.25, 2)
    # pavement
    rect(img, 0, GY, W, WALK + 3 - GY, "grey4", None)
    hline(img, 0, W, GY, "ink")
    dither_grad(img, (0, GY + 1, W, WALK + 2), "grey4", "grey3", "y", 4, 0.0, 0.5)
    for x in range(0, W, 18):
        vline(img, x + (4 if (x // 18) % 2 else 0), GY + 2, WALK + 1, "grey3")
    hline(img, 0, W, GY + 6, "grey3")
    # kerb
    rect(img, 0, WALK + 3, W, 3, "grey3", None)
    hline(img, 0, W, WALK + 2, "ink")
    hline(img, 0, W, WALK + 4, "grey2")
    hline(img, 0, W, WALK + 5, "ink")
    # road
    rect(img, 0, WALK + 6, W, Y1 - WALK - 6, "grey2", None)
    dither_flat(img, (0, WALK + 6, W, Y1), "grey2", "grey1", 0.5, 2)
    for x in range(8, W, 36):
        rect(img, x, 155, 18, 1, "yellow2", None)

    # ---- street furniture
    # trash bags by the door
    for (bx, by, bw, bh, c) in [(96, 128, 11, 10, "grey2"), (104, 124, 9, 14, "blue2"), (88, 131, 9, 7, "white")]:
        ellipse(img, bx, by, bx + bw, by + bh, c, "ink")
        px(img, bx + bw // 2, by - 1, "ink")
        px(img, bx + 2, by + 2, "grey4" if c != "white" else "grey3")
    # plastic planters (styrofoam boxes) at laundry
    for bx in (56, 76):
        obox(img, bx, 129, 16, 9, "white", None, "grey3")
        for i in range(4):
            ellipse(img, bx + 1 + i * 4, 123 + (i % 2) * 2, bx + 5 + i * 4, 130, "green1", "ink")
            px(img, bx + 3 + i * 4, 125 + (i % 2) * 2, "green3")
    # bucket stack at hardware shop
    for (bx, by, c) in [(207, 126, "red2"), (219, 129, "blue2")]:
        poly(img, [(bx, by), (bx + 9, by), (bx + 8, by + 11), (bx + 1, by + 11)], c, "ink")
        hline(img, bx + 1, bx + 8, by + 2, "ink")
    line(img, [(238, 134), (243, 112)], "brown2")    # mop
    rect(img, 236, 132, 6, 6, "grey4", "ink")
    # plastic stool + table at conv store
    obox(img, 171, 138, 10, 3, "blue2", "blue3")
    rect(img, 173, 141, 2, 5, "ink"); rect(img, 178, 141, 2, 5, "ink")
    # scooter at right neighbour
    for wx in (262, 282):
        ellipse(img, wx, 134, wx + 10, 146, "ink2", "ink")
        ellipse(img, wx + 3, 138, wx + 7, 142, "grey3", "ink")
    poly(img, [(266, 128), (284, 128), (287, 134), (274, 140), (266, 140)], "red2", "ink")
    hline(img, 268, 283, 129, "red3")
    obox(img, 262, 124, 14, 4, "ink2", "grey1")                     # seat
    line(img, [(284, 128), (286, 118)], "ink")
    line(img, [(283, 118), (291, 118)], "ink")
    rect(img, 288, 122, 3, 4, "yellow2", "ink")                      # headlight
    rect(img, 264, 138, 22, 1, "red1", None)

    # ---- utility pole + wires
    pxx = 249
    obox(img, pxx - 2, 28, 5, 121, "grey3", "grey4", "grey1")
    for yy in range(36, 140, 8):
        px(img, pxx - 3, yy, "ink"); px(img, pxx + 3, yy, "ink")
    obox(img, pxx - 14, 32, 28, 3, "brown2", "brown3", "brown1")
    obox(img, pxx - 10, 40, 20, 3, "brown2", "brown3", "brown1")
    for (ix, iy) in [(pxx - 12, 29), (pxx - 6, 29), (pxx + 6, 29), (pxx + 12, 29), (pxx - 8, 37), (pxx + 8, 37)]:
        rect(img, ix, iy, 3, 3, "green2" if ix % 2 else "grey4", "ink")
    obox(img, pxx + 4, 50, 8, 11, "grey2", "grey3", "grey1")       # transformer can
    rect(img, pxx + 5, 62, 6, 2, "ink", None)
    obox(img, pxx - 2, 94, 6, 8, "yellow", None, "orange2")          # notice plate
    # wires from pole
    for (dy, tgt, sag) in [(31, (0, 33), 6), (33, (0, 40), 8), (41, (0, 47), 5), (34, (W, 40), 8), (41, (W, 50), 10)]:
        wire(img, (pxx - 12 + (dy % 5) * 6, dy), tgt, sag, "ink")
    # service drops to the building (thin, grey so they do not swamp the facade)
    for i, (x1, y1, sag) in enumerate([(160, 50, 5), (206, 50, 3), (110, 50, 6)]):
        wire(img, (pxx - 3, 38 + i * 2), (x1, y1), sag, "ink2")
    # wire tangle knots
    for (kx, ky) in [(236, 40), (232, 46), (168, 48)]:
        line(img, [(kx - 3, ky), (kx, ky - 3), (kx + 3, ky), (kx, ky + 2), (kx - 4, ky - 2)], "ink")
    # cable duct on facade
    line(img, [(246, 50), (246, 88)], "ink"); line(img, [(247, 56), (247, 88)], "grey1")

    # ---- streetlamp (left)
    lpx = 30
    obox(img, lpx - 1, 70, 4, 79, "grey1", "grey2", "ink2")
    rect(img, lpx - 3, 144, 8, 6, "grey1", "ink")
    line(img, [(lpx + 1, 68), (lpx + 2, 62), (lpx + 8, 58), (lpx + 16, 58)], "ink", 3)
    line(img, [(lpx + 1, 68), (lpx + 2, 62), (lpx + 8, 58), (lpx + 16, 58)], "grey1", 1)
    obox(img, lpx + 12, 58, 14, 5, "grey2", "grey3", "grey1")
    rect(img, lpx + 14, 63, 10, 2, "yellow2" if night else "grey4", "ink")
    # bollards
    for bx in (92, 204):
        obox(img, bx, 143, 4, 8, "yellow", "yellow2", "orange2")
        hline(img, bx, bx + 3, 146, "ink")
    return img


# --- night lighting -------------------------------------------------------
NIGHT_MAP = {
    "white": "grey3", "grey4": "grey2", "grey3": "grey1", "grey2": "grey1", "grey1": "ink2", "ink2": "ink",
    "wall1": "grey1", "wall2": "ink2", "wall3": "ink2", "wall4": "grey1",
    "blue4": "blue1", "blue3": "blue0", "blue2": "blue0", "blue1": "blue0",
    "brown3": "brown2", "brown2": "brown1", "brown1": "brown0",
    "orange2": "orange1", "orange1": "orange0", "yellow": "orange2", "yellow2": "orange3",
    "green3": "green2", "green2": "green1", "green1": "green0",
    "red3": "red2", "red2": "red1", "red1": "red0", "skin3": "skin2",
    "purple2": "purple1", "orange3": "orange2", "orange4": "orange3",
}
WARM = {"ink": "brown0", "ink2": "brown0", "grey1": "brown1", "grey2": "brown2", "grey3": "brown3",
        "blue0": "purple0", "blue1": "purple1", "brown0": "orange0", "brown1": "orange1", "brown2": "orange3",
        "brown3": "orange4", "purple0": "orange0", "orange0": "orange1", "orange1": "orange2",
        "green0": "green1", "green1": "green2", "red0": "red1", "red1": "red2", "red2": "red3",
        "orange2": "orange3", "orange3": "orange4", "yellow": "yellow2", "grey4": "white"}
COOL = {"ink": "blue0", "ink2": "blue0", "grey1": "grey2", "grey2": "grey3", "grey3": "grey4", "blue0": "blue1",
        "blue1": "blue2", "brown0": "brown1", "brown1": "brown2", "brown2": "brown3", "red0": "red1",
        "orange0": "orange1", "green0": "green1", "green1": "green2", "grey4": "white", "purple0": "purple1"}


def make_street_night():
    day = street(False)
    nsk = street(True)
    # sky mask: pixels equal in structure... simplest: night image has been drawn w/ night sky; for all
    # other pixels use remap of the day image.
    out = new(W, H, "ink")
    pd, pn, po = day.load(), nsk.load(), out.load()
    mp = lift_map(NIGHT_MAP)
    skyday = {col("blue3"), col("blue4"), col("wall1")}
    # structure differs only in sky pixels: detect via comparing the two renders
    for y in range(H):
        for x in range(W):
            if pd[x, y] != pn[x, y] and y >= Y0 and y < Y1:
                po[x, y] = pn[x, y]
            else:
                po[x, y] = mp.get(pd[x, y], pd[x, y])
    return out


def ell_mask(cx, cy, rx, ry, k=1.0, floor_y=None):
    def f(x, y):
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        if d >= 1:
            return 0
        return min(1.0, (1 - d) * k)
    return f


def copy_region(dst, src, box, remap=None):
    x0, y0, x1, y1 = box
    mp = lift_map(remap) if remap else {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = src.getpixel((x, y))
            dst.putpixel((x, y), mp.get(c, c))


def street_night_full():
    day = street(False)
    img = make_street_night()
    warm, cool = lift_map(WARM), lift_map(COOL)
    # far lit windows in the distant blocks
    rnd = random.Random(4)
    for (x, y, w, h) in [(6, 44, 26, 80), (36, 58, 20, 66), (96, 50, 22, 74), (130, 62, 16, 62),
                         (206, 46, 24, 78), (262, 56, 22, 68), (292, 40, 26, 84)]:
        for yy in range(y + 4, y + h - 3, 5):
            for xx in range(x + 3, x + w - 3, 5):
                if rnd.random() < 0.25 and all(day.getpixel((xx + i, yy + j)) == col("blue2") for i in range(3) for j in range(2)):
                    rect(img, xx, yy, 3, 2, "orange3")
    # --- convenience store: lit window + door copied from the day render
    copy_region(img, day, (130, 107, 192, 135))
    copy_region(img, day, (166, 108, 188, 134))
    # lit sign
    rect(img, 129, 92, 64, 10, "blue2", None)
    dither_flat(img, (129, 92, 193, 102), "blue2", "blue1", 0.35, 2)
    ellipse(img, 131, 93, 137, 99, "yellow2", None); ellipse(img, 133, 92, 139, 98, "blue2", None)
    text(img, 141, 92, "달빛 편의점", "yellow2", 9, edge="blue0")
    # glow spill from the store (cool-white), onto pavement and wall
    apply_map(img, cool, ell_mask(161, 124, 66, 34, 1.1), 1)
    apply_map(img, cool, ell_mask(161, 124, 40, 22, 1.2), 1)
    apply_map(img, warm, ell_mask(161, 96, 34, 10, 1.1), 1)               # sign halo
    # --- upstairs agency window lit (warm) with a silhouette at the desk
    copy_region(img, day, (126, 61, 184, 83), {"blue3": "orange3", "blue4": "yellow2"})
    dither_flat(img, (127, 62, 183, 82), "orange3", "yellow2", 0.45, 2)
    for xx in (144, 164):
        vline(img, xx, 61, 82, "ink")
    rect(img, 150, 74, 10, 9, "ink2", "ink")        # desk
    ellipse(img, 152, 66, 158, 73, "ink", None)      # head silhouette
    rect(img, 150, 73, 10, 3, "ink", None)
    apply_map(img, warm, ell_mask(155, 71, 52, 30, 1.0), 1)
    apply_map(img, warm, ell_mask(155, 71, 24, 14, 1.0), 1)
    # vertical sign glows faintly
    rect(img, 191, 48, 13, 46, "blue1", None)
    for i, ch in enumerate("새벽인력"):
        text(img, 192, 49 + i * 10, ch, "yellow2", 9, edge="blue0")
    # --- streetlamp cone
    ax, ay = 43, 65
    def cone(x, y):
        if y < ay or y > 152:
            return 0
        t = (y - ay) / (152 - ay)
        half = 6 + 40 * t
        if abs(x - ax - 6 * t) > half:
            return 0
        edge = 1 - abs(x - ax - 6 * t) / half
        return 0.62 - 0.22 * t if edge > 0.12 else 0
    apply_map(img, warm, cone, 1)
    # pole head bright
    rect(img, 44, 63, 10, 2, "yellow2", "ink")
    dither_radial(img, 49, 66, 7, "yellow2", None, 4)
    # --- little point lights: pole plate / 24h door
    return img


# ============================================================ scene 3: crossing
def fieldfill(img, box, colors, fn, m=4):
    """Dither a scalar field fn(x,y)->0..len-1 through a colour list."""
    x0, y0, x1, y1 = box
    n = len(colors) - 1
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = max(0.0, min(float(n) - 1e-6, fn(x, y)))
            i = int(v)
            fr = v - i
            k = i + (1 if fr > _thr(x, y, m) else 0)
            img.putpixel((x, y), col(colors[min(n, k)]))


def train_car(img, x, y, w=76, h=19, body="white", stripe="blue2", skirt="grey2"):
    obox(img, x, y, w, h, body, None, "grey3")
    rect(img, x + 1, y + 1, w - 2, 3, "grey4", None)              # roof curve highlight
    # roof gear
    obox(img, x + 8, y - 3, 12, 3, "grey3", "grey4")
    obox(img, x + w - 22, y - 3, 12, 3, "grey3", "grey4")
    # windows
    n = 5
    ww = (w - 14 - (n - 1) * 2) // n
    for i in range(n):
        wx = x + 7 + i * (ww + 2)
        rect(img, wx, y + 4, ww, 7, "blue3", "ink")
        dither_grad(img, (wx + 1, y + 5, wx + ww - 1, y + 10), "blue4", "blue3", "d", 4, 0.9, 0.0)
    # doors between windows (vertical seams)
    for dx in (x + w // 4, x + 3 * w // 4):
        vline(img, dx, y + 2, y + h - 4, "ink")
        vline(img, dx + 1, y + 2, y + h - 4, "grey3")
    # livery stripe
    rect(img, x + 1, y + 13, w - 2, 2, stripe, None)
    rect(img, x + 1, y + 15, w - 2, 1, "blue1", None)
    # underframe + bogies
    rect(img, x + 2, y + h, w - 4, 2, "ink2", "ink")
    for bx in (x + 8, x + w - 20):
        rect(img, bx, y + h + 1, 12, 2, "ink", None)
        for wx in (bx + 1, bx + 7):
            rect(img, wx, y + h + 1, 3, 2, "grey1", None)


def hazard_post(img, x, y, w, h):
    rect(img, x, y, w, h, "yellow", "ink")
    stripes(img, (x + 1, y + 1, x + w - 1, y + h - 1), "yellow", "ink", 6)
    rect(img, x, y, w, h, None, "ink")


def traffic_light(img, x, y, lit="red"):
    obox(img, x, y, 24, 9, "grey1", "grey2", "ink2")
    for i, (c, off) in enumerate([("green2", "green0"), ("yellow", "orange1"), ("red3", "red1")]):
        on = {"green2": "green", "yellow": "yellow", "red3": "red"}[c] == lit
        ellipse(img, x + 2 + i * 7, y + 2, x + 6 + i * 7, y + 6, c if on else off, "ink")
        if on:
            px(img, x + 3 + i * 7, y + 3, "white")
    # visor
    for i in range(3):
        hline(img, x + 2 + i * 7, x + 6 + i * 7, y + 1, "ink")


def road_sign_round(img, cx, cy, r, txt):
    ellipse(img, cx - r, cy - r, cx + r, cy + r, "white", "ink")
    ellipse(img, cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, "red2", None)
    ellipse(img, cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3, "white", None)
    tw, _ = text_size(txt, 7)
    text(img, cx - tw // 2, cy - 4, txt, "ink", 7)


def crossing():
    img = new(W, H, "ink")
    dither_ramp(img, (0, Y0, W, 110), ["blue3", "blue4", "wall1"], m=4)
    cloud(img, 40, 30, 38); cloud(img, 188, 26, 30, 6); cloud(img, 262, 38, 34, 6)
    # distant skyline seen through the arch
    for i, (x, y, w, h) in enumerate([(60, 82, 20, 30), (84, 70, 16, 42), (104, 88, 22, 24), (178, 76, 18, 36),
                                       (200, 66, 22, 46), (226, 84, 20, 28), (130, 92, 14, 20), (150, 86, 24, 26)]):
        apt_block(img, x, y, w, h, False, i + 20)
    # low shops on the horizon
    for (x, w, c) in [(70, 30, "wall4"), (100, 26, "wall1"), (126, 34, "wall3"), (160, 30, "wall2"), (190, 34, "wall4"), (224, 30, "wall1")]:
        rect(img, x, 102, w, 10, c, "grey2")
        for i in range(2, w - 2, 7):
            rect(img, x + i, 105, 4, 3, "blue3", "grey2")
    # trees
    for tx in (96, 172, 240):
        ellipse(img, tx - 7, 96, tx + 7, 110, "green2", "green0")
        dither_flat(img, (tx - 6, 103, tx + 7, 110), "green2", "green1", 0.5, 2)
    # ---- ground / road
    rect(img, 0, 112, W, Y1 - 112, "grey4", None)
    hline(img, 0, W, 112, "grey2")
    # pavement tile rows (perspective: spacing grows downwards)
    yy, step = 114, 2
    while yy < Y1:
        hline(img, 0, W, yy, "grey3")
        yy += step; step += 1
    dither_grad(img, (0, 113, W, Y1), "grey4", "grey3", "y", 4, 0.0, 0.35)
    road = [(104, 112), (216, 112), (312, 157), (8, 157)]
    poly(img, road, "grey2", None)
    # road texture (m=2 dither, darker towards viewer)
    mk = new(W, H); poly(mk, road, "ink")
    dither_grad(img, (0, 112, W, Y1), "grey2", "grey1", "y", 2, 0.0, 0.8, mask=mk.split()[3])
    line(img, [(104, 112), (8, 157)], "ink"); line(img, [(216, 112), (312, 157)], "ink")
    line(img, [(106, 112), (14, 157)], "white"); line(img, [(214, 112), (306, 157)], "white")
    # centre dashes
    for (ya, yb) in [(114, 117), (121, 126), (131, 139), (146, 157)]:
        hw0 = 1 + (ya - 112) // 18
        hw1 = 1 + (yb - 112) // 18
        poly(img, [(160 - hw0, ya), (160 + hw0, ya), (160 + hw1, yb), (160 - hw1, yb)], "yellow", None)
    # crosswalk
    for k in range(-5, 6):
        a = 160 + k * 20; b = 160 + k * 24
        poly(img, [(a - 5, 136), (a + 5, 136), (b + 7, 148), (b - 7, 148)], "white", None)
    hline(img, 0, 0, 0, "ink")
    # ---- viaduct deck
    rect(img, 0, 56, W, 22, "grey3", "ink")
    dither_flat(img, (1, 57, W - 1, 77), "grey3", "grey4", 0.3, 2)
    rect(img, 0, 50, W, 7, "grey4", "ink")                      # parapet
    hline(img, 1, W - 2, 51, "white")
    for x in range(8, W, 24):                                    # parapet panel joints
        vline(img, x, 51, 55, "grey3")
    rect(img, 0, 76, W, 4, "grey2", "ink")                       # underside lip
    for x in range(4, W, 8):
        px(img, x, 62, "grey2"); px(img, x + 4, 68, "grey2")    # rivets
    hline(img, 1, W - 2, 70, "grey2")
    # shadow under deck onto the scene
    dither_grad(img, (56, 80, 264, 98), "grey1", "grey1", "y", 4, 0.75, 0.0)
    # girder text plate
    sign(img, 134, 62, 52, 12, "blue1", "동진교 하부", "white", "blue0", 9, "blue2")
    # ---- piers
    for (px0, side) in [(0, 0), (264, 1)]:
        rect(img, px0, 80, 56, 58, "grey3", "ink")
        dither_flat(img, (px0 + 1, 81, px0 + 55, 137), "grey3", "grey4", 0.35, 2)
        dither_flat(img, (px0 + (36 if side == 0 else 1), 81, px0 + (55 if side == 0 else 20), 137), "grey3", "grey2", 0.55, 2)
        for y_ in range(88, 130, 10):
            hline(img, px0 + 1, px0 + 54, y_, "grey2")
        streaks(img, (px0 + 2, 82, px0 + 54, 128), "grey3", "grey2", 18, 40 + side, 18, 0.9)
        patches(img, (px0 + 2, 84, px0 + 54, 120), "grey3", "grey4", 5, 50 + side, 0.5, 8, 4)
        # hazard striped base + corner guard
        hazard_post(img, px0 + (44 if side == 0 else 0), 108, 12, 30)
        rect(img, px0, 130, 56, 8, "grey2", "ink")
        stripes(img, (px0 + 1, 131, px0 + 55, 137), "yellow", "ink", 8)
        rect(img, px0, 130, 56, 8, None, "ink")
    # pier edge pillars shading
    # ---- height limit gate hanging in the arch
    rect(img, 62, 82, 2, 16, "ink2", None); rect(img, 256, 82, 2, 16, "ink2", None)
    obox(img, 56, 96, 208, 7, "yellow", None, None)
    stripes(img, (57, 97, 263, 102), "yellow", "ink", 8)
    rect(img, 56, 96, 208, 7, None, "ink")
    sign(img, 120, 105, 80, 13, "yellow", "높이제한 3.2m", "ink", None, 9, "yellow2", 2)
    line(img, [(140, 103), (140, 105)], "ink"); line(img, [(180, 103), (180, 105)], "ink")
    # ---- train
    x = -30
    for i in range(5):
        train_car(img, x + i * 80, 31, 78, 19, "white", "blue2" if i != 2 else "red2")
    # couplings
    for i in range(1, 5):
        rect(img, x + i * 80 - 3, 40, 4, 4, "ink2", "ink")
    # catenary
    for mx in (40, 150, 262):
        obox(img, mx - 1, 22, 3, 30, "grey1", "grey2", "ink2")
        line(img, [(mx - 12, 24), (mx + 12, 24)], "ink")
        rect(img, mx - 12, 24, 2, 3, "ink", None); rect(img, mx + 11, 24, 2, 3, "ink", None)
    wire(img, (-2, 25), (W, 25), 0, "ink")
    wire(img, (0, 27), (W, 27), 0, "ink2")
    for xx in range(10, W, 14):
        vline(img, xx, 25, 27 + (xx // 14) % 2, "ink2")
    for px_ in (36, 130, 254):                                   # pantographs
        line(img, [(px_, 30), (px_ + 4, 27), (px_ + 8, 30)], "ink")
    # ---- signage + traffic lights (left)
    obox(img, 62, 84, 3, 70, "grey2", "grey3", "grey1")
    rect(img, 58, 152, 11, 4, "grey1", "ink")
    obox(img, 64, 86, 40, 3, "grey2", "grey3", "grey1")
    traffic_light(img, 80, 90, "red")
    sign(img, 70, 106, 34, 12, "blue1", "동진로", "white", "blue0", 9, "blue2")
    rect(img, 86, 103, 2, 3, "ink", None)
    # ---- right side
    obox(img, 254, 84, 3, 70, "grey2", "grey3", "grey1")
    rect(img, 250, 152, 11, 4, "grey1", "ink")
    obox(img, 216, 86, 40, 3, "grey2", "grey3", "grey1")
    traffic_light(img, 222, 90, "red")
    road_sign_round(img, 270, 98, 9, "30")
    rect(img, 269, 108, 2, 40, "grey2", "ink")
    # warning triangle sign
    poly(img, [(292, 92), (306, 92), (299, 80)], "yellow", "ink")
    rect(img, 298, 85, 2, 4, "ink", None)
    rect(img, 298, 90, 2, 1, "ink", None)
    rect(img, 298, 92, 2, 50, "grey2", "ink")
    # barrier arm (hazard stripes) at left lane
    obox(img, 36, 126, 8, 12, "grey1", "grey2", "ink2")
    obox(img, 44, 128, 62, 5, "white", None, None)
    stripes(img, (45, 129, 105, 132), "red2", "white", 8)
    rect(img, 44, 128, 62, 5, None, "ink")
    # power lines across the sky/foreground
    for (a, b, sag) in [((0, 34), (W, 44), 10), ((0, 40), (W, 50), 12)]:
        pass
    wire(img, (62, 86), (-2, 70), 6, "ink")
    wire(img, (62, 88), (-2, 80), 4, "ink")
    wire(img, (256, 86), (W, 68), 6, "ink")
    wire(img, (256, 88), (W, 78), 4, "ink")
    # manhole + cracks + shadows under the poles
    ellipse(img, 196, 144, 214, 150, "grey1", "ink")
    for xx in range(199, 212, 3):
        vline(img, xx, 145, 149, "grey2")
    line(img, [(120, 140), (126, 144), (124, 148), (131, 152)], "grey1")
    line(img, [(240, 134), (236, 139), (239, 143)], "grey1")
    dither_flat(img, (60, 153, 74, 157), "grey2", "ink2", 0.5, 2)
    dither_flat(img, (252, 153, 266, 157), "grey2", "ink2", 0.5, 2)
    return img


# ============================================================ scene 4: title
def bil(c, u, v):
    (x00, y00), (x10, y10), (x11, y11), (x01, y01) = c
    x = (1 - u) * (1 - v) * x00 + u * (1 - v) * x10 + u * v * x11 + (1 - u) * v * x01
    y = (1 - u) * (1 - v) * y00 + u * (1 - v) * y10 + u * v * y11 + (1 - u) * v * y01
    return (round(x), round(y))


def qpoly(img, c, u0, v0, u1, v1, fill, ol=None):
    poly(img, [bil(c, u0, v0), bil(c, u1, v0), bil(c, u1, v1), bil(c, u0, v1)], fill, ol)


def qline(img, c, a, b, col_):
    line(img, [bil(c, *a), bil(c, *b)], col_)


def coin(img, cx, cy, rx, ry, th, label=None):
    ellipse(img, cx - rx, cy - ry + th, cx + rx, cy + ry + th, "orange1", "ink")
    rect(img, cx - rx, cy, 2 * rx + 1, th + 1, "orange1", None)
    rect(img, cx - rx, cy, 1, th + 1, "ink", None); rect(img, cx + rx, cy, 1, th + 1, "ink", None)
    for xx in range(cx - rx + 2, cx + rx - 1, 3):
        vline(img, xx, cy + ry - 1 if False else cy + 2, cy + th + ry - 2 if th > 4 else cy + th + 1, "orange0")
    ellipse(img, cx - rx, cy - ry, cx + rx, cy + ry, "yellow", "ink")
    ellipse(img, cx - rx + 2, cy - ry + 2, cx + rx - 2, cy + ry - 2, None, "orange3")
    dither_flat(img, (cx - rx + 3, cy, cx + rx - 2, cy + ry - 2), "yellow", "orange3", 0.4, 2)
    px(img, cx - rx + 3, cy - ry + 3, "yellow2"); px(img, cx - rx + 4, cy - ry + 2, "yellow2")
    if label:
        tw, _ = text_size(label, 7)
        text(img, cx - tw // 2, cy - 4, label, "orange1", 7)


DARKEN = {"orange4": "orange3", "orange3": "orange2", "orange2": "orange1", "orange1": "orange0", "orange0": "brown0",
          "brown3": "brown2", "brown2": "brown1", "brown1": "brown0", "brown0": "ink", "white": "grey3", "wall1": "grey3",
          "grey4": "grey3", "grey3": "grey2", "grey2": "grey1", "grey1": "ink2", "yellow": "orange2", "yellow2": "orange3",
          "blue4": "blue3", "blue3": "blue2", "blue2": "blue1", "blue1": "blue0", "red3": "red2", "red2": "red1",
          "red1": "red0", "red0": "ink", "green2": "green1", "green1": "green0", "green3": "green2"}
LIGHTEN = {v: k for k, v in DARKEN.items() if v != "ink"}
LIGHTEN.update({"ink": "ink2", "ink2": "grey1"})


def tone(img, mask, mp, level, m=2, passes=1):
    mm = lift_map(mp)
    for y in range(Y0, Y1):
        for x in range(W):
            if mask.getpixel((x, y)) and level > _thr(x, y, m):
                c = img.getpixel((x, y))
                for _ in range(passes):
                    c = mm.get(c, c)
                img.putpixel((x, y), c)


def shadow_dither(img, pts, c="ink", level=0.6):
    m = new(W, H)
    poly(m, pts, "ink")
    tone(img, m.split()[3], DARKEN, 0.9 if level >= 0.6 else level, 2, 2)


def title_bg():
    img = new(W, H, "ink")
    cx0, cy0 = 160, 20

    def field(x, y):
        d = math.hypot((x - 160) / 1.5, (y - 70)) / 120.0
        L = 3.0 - 3.2 * d
        ang = math.atan2(x - cx0, y - cy0 + 0.001)
        ray = int(math.floor(ang / (math.pi / 26)))
        if ray % 2:
            L += 0.3
        return L

    fieldfill(img, (0, Y0, W, Y1), ["red0", "red1", "red2", "red3"], field, 2)
    # ---- counter (forced perspective) -------------------------------------
    far, near = 106, 168
    top = [(8, far), (312, far), (460, near), (-140, near)]
    poly(img, top, "orange1", None)
    mk = new(W, H); poly(mk, top, "ink"); mask = mk.split()[3]
    # depth shading: far = darker, near = lighter
    fieldfill(img, (0, far, W, Y1), ["brown1", "orange0", "orange1", "orange2"],
              lambda x, y: (y - far) / (Y1 - far) * 2.6 + 0.2, 2)
    # clip to counter polygon: repaint outside with the red field
    for y in range(far, Y1):
        for x in range(W):
            if mask.getpixel((x, y)) == 0:
                img.putpixel((x, y), col(["red0", "red1", "red2", "red3"][max(0, min(3, int(field(x, y))))]))
    # planks: lines from vanishing point
    vpx, vpy = 160, 30
    for k in range(-9, 10):
        xf = 160 + k * 32
        xn = 160 + k * 76
        line(img, [(round(xf), far), (round(xn), Y1 - 1)], "orange0")
        # clip handled by mask later
    # wood grain strokes along the depth direction
    rnd = random.Random(3)
    for _ in range(80):
        y = rnd.randint(far + 2, Y1 - 2)
        x = rnd.randint(0, W - 1)
        t = (y - far) / (168 - far)
        dx = (x - 160) / (y - vpy + 0.01) * 4
        L = rnd.randint(3, 9)
        c = rnd.choice(["orange0", "orange2", "orange2", "orange3", "brown2"])
        for i in range(L):
            xx, yy = round(x + dx * i / 4), y + i
            if 0 <= xx < W and yy < Y1 and mask.getpixel((xx, yy)):
                img.putpixel((xx, yy), col(c))
    # restore palette-edge: far lip of the counter
    for x in range(W):
        if mask.getpixel((x, far + 1)):
            px(img, x, far, "ink"); px(img, x, far + 1, "brown2")
    hline(img, 8, 311, far + 2, "brown1")
    line(img, [(8, far), (-140, near)], "ink"); line(img, [(312, far), (460, near)], "ink")
    # soft highlight glaze, top-left
    gl = new(W, H)
    poly(gl, [(0, far + 3), (190, far + 3), (150, Y1), (0, Y1)], "ink")
    tone(img, gl.split()[3], LIGHTEN, 0.35, 2, 1)

    # ---- objects ---------------------------------------------------------
    # time cards (left)
    for c, fill in [([(6, 120), (62, 114), (84, 152), (-6, 160)], "wall1"),
                    ([(30, 112), (84, 108), (108, 140), (28, 146)], "white")]:
        shadow_dither(img, [(p[0] + 5, p[1] + 5) for p in c])
        poly(img, c, fill, "ink")
        qpoly(img, c, 0.0, 0.0, 1.0, 0.18, "red2")
        qline(img, c, (0, 0.18), (1, 0.18), "ink")
        for i in range(1, 7):
            qline(img, c, (0.05, 0.18 + i * 0.115), (0.95, 0.18 + i * 0.115), "grey3")
        qline(img, c, (0.5, 0.18), (0.5, 0.98), "grey3")
        for i in range(3):
            qpoly(img, c, 0.08, 0.28 + i * 0.23, 0.42, 0.33 + i * 0.23, "grey4")
        qpoly(img, c, 0.62, 0.55, 0.85, 0.66, "red1")                # stamp
    # name badge standing on the counter (left, tall)
    shadow_dither(img, [(18, 118), (62, 116), (76, 128), (36, 132)], level=0.7)
    obox(img, 14, 62, 40, 56, "white", "white", "grey3")
    rect(img, 15, 63, 38, 11, "red2", None)
    hline(img, 15, 52, 74, "ink")
    rect(img, 29, 58, 12, 3, "grey2", "ink")                       # clip slot
    rect(img, 31, 56, 8, 3, "grey1", "ink")
    text(img, 34, 63, "신입", "white", 9, edge="red1", align="center")
    rect(img, 19, 79, 14, 18, "blue3", "ink")
    ellipse(img, 22, 82, 30, 90, "skin2", "ink")
    rect(img, 20, 91, 12, 5, "blue1", None)
    for i in range(3):
        hline(img, 37, 50, 82 + i * 5, "grey2")
    rect(img, 19, 101, 32, 11, "grey4", "ink")
    for xx in range(21, 49, 2):
        vline(img, xx, 103, 109, "ink2" if xx % 4 else "ink")
    # receipt roll (right-bottom) with paper strip falling to the viewer
    c = [(236, 152), (266, 150), (284, 157), (222, 157)]
    shadow_dither(img, [(238, 136), (292, 136), (300, 150), (232, 152)], level=0.7)
    poly(img, [(244, 130), (262, 130), (278, 157), (252, 157)], "white", "ink")
    for i in range(6):
        hline(img, 252 + i // 2, 270 + i, 136 + i * 3, "grey3")
    for xx in range(250, 272, 2):
        px(img, xx, 154, "ink")
    obox(img, 230, 96, 46, 34, "white", "white", "grey3")
    ellipse(img, 222, 96, 240, 130, "grey4", "ink")
    ellipse(img, 227, 107, 235, 119, "ink2", "ink")
    ellipse(img, 229, 109, 233, 117, "brown2", "ink")
    rect(img, 241, 97, 33, 1, "white", None)
    dither_grad(img, (241, 99, 275, 129), "white", "grey3", "y", 4, 0.0, 0.7)
    hline(img, 241, 274, 112, "grey3"); hline(img, 241, 274, 118, "grey3")
    # barcode scanner (right, upright)
    shadow_dither(img, [(262, 112), (312, 112), (318, 124), (264, 124)], level=0.7)
    # grip first, then the head over it
    poly(img, [(276, 82), (298, 82), (302, 112), (282, 112)], "blue2", "ink")
    vline(img, 277, 84, 110, "blue3")
    dither_flat(img, (290, 84, 301, 111), "blue2", "blue1", 0.5, 2)
    rect(img, 268, 96, 8, 9, "blue1", "ink")                     # trigger guard
    rect(img, 272, 98, 3, 5, "grey4", "ink")
    rect(img, 280, 112, 22, 4, "ink2", "ink")                    # cable boot
    obox(img, 258, 58, 48, 26, "blue2", "blue3", "blue1")
    rect(img, 252, 63, 7, 14, "ink2", "ink")                     # scan window
    rect(img, 253, 64, 4, 12, "red3", None)
    rect(img, 264, 64, 28, 10, "ink2", "ink")                    # status display
    rect(img, 266, 66, 24, 6, "green2", "ink")
    hline(img, 268, 280, 68, "green3")
    rect(img, 296, 64, 6, 4, "yellow", "ink")
    # laser fan
    for k in range(-4, 5):
        line(img, [(258, 72), (150 + k * 6, 100 + k * 9)], "yellow2") if False else None
    for i in range(0, 60, 2):
        yy = 72 + i // 2 * 0
    pts = [(257, 72), (190, 60), (190, 92)]
    m = new(W, H); poly(m, pts, "ink"); mk2 = m.split()[3]
    dither_grad(img, (180, 55, 258, 100), "red4", "red4", "x", 2, 0.0, 0.0, mask=None) if False else None
    for y in range(55, 100):
        for x in range(185, 258):
            if mk2.getpixel((x, y)) and ((x + y) % 2 == 0) and (x - 190) / 70 > _thr(x, y, 2) * 0.6:
                img.putpixel((x, y), col("red4"))
    line(img, [(257, 72), (190, 76)], "yellow2")
    # coins bottom centre
    for (cxx, cyy, r) in [(132, 150, 9), (150, 143, 8), (196, 148, 9), (118, 136, 6)]:
        shadow_dither(img, [(cxx - r + 4, cyy + 2), (cxx + r + 6, cyy + 2), (cxx + r + 6, cyy + 7), (cxx - r + 4, cyy + 7)], level=0.6)
        coin(img, cxx, cyy, r, max(3, r // 2), 3)
    coin(img, 178, 150, 12, 6, 4, "100")
    coin(img, 178, 146, 12, 6, 4)
    coin(img, 178, 142, 12, 6, 4, "100")
    # bottom vignette so the HUD bar reads
    return img


# ============================================================ scene 5: death
def death_bg():
    img = new(W, H, "ink")

    def vig(x, y):
        d = math.hypot((x - 160) / 170.0, (y - 100) / 78.0)
        return max(0.0, (d - 0.62) * 3.4)

    fieldfill(img, (0, Y0, W, Y1), ["ink", "red0", "red1"], vig, 2)
    # faint floor perspective in the dark
    flo = new(W, H)
    persp_floor(flo, (0, 112, W, 158), 160, "red0", rows=6, cols=14, spread=3.6, power=1.7)
    for y in range(112, Y1):
        for x in range(W):
            if flo.getpixel((x, y))[3] and img.getpixel((x, y)) == col("ink"):
                img.putpixel((x, y), col("ink2"))
    # spotlight cone
    apex_y = Y0
    cone = new(W, H)
    poly(cone, [(150, apex_y), (170, apex_y), (244, 138), (76, 138)], "ink")
    ellipse(cone, 76, 124, 244, 152, "ink")
    cm = cone.split()[3]

    def lightf(x, y):
        t = (y - apex_y) / (140 - apex_y)
        half = 10 + (244 - 160 - 10) * t
        e = abs(x - 160) / half
        return 1.0 + (1 - e) * 1.2 - t * 0.5
    for y in range(Y0, Y1):
        for x in range(W):
            if cm.getpixel((x, y)):
                v = lightf(x, y)
                i = img.getpixel((x, y))
                fieldfill(img, (x, y, x + 1, y + 1), ["ink", "ink2", "grey1", "grey2", "grey3"], lambda a, b, v=v: v * 1.25, 4)
    # hard cone edges
    line(img, [(150, apex_y), (76, 138)], "grey2"); line(img, [(170, apex_y), (244, 138)], "grey2")
    # pool of light on the floor
    pool = new(W, H); ellipse(pool, 76, 124, 244, 152, "ink"); pm = pool.split()[3]
    for y in range(120, 154):
        for x in range(70, 250):
            if pm.getpixel((x, y)):
                d = math.hypot((x - 160) / 84.0, (y - 138) / 14.0)
                v = 3.6 - 2.8 * d
                fieldfill(img, (x, y, x + 1, y + 1), ["grey1", "grey2", "grey3", "grey4"], lambda a, b, v=v: v - 0.0, 4)
    # tile joints in the pool
    for i in range(-6, 7):
        xa = 160 + i * 8; xb = 160 + i * 16
        for y in range(124, 153):
            t = (y - 124) / 28.0
            xx = round(xa + (xb - xa) * t)
            if 0 <= xx < W and pm.getpixel((xx, y)):
                px(img, xx, y, "grey2")
    for yy in (128, 133, 140, 148):
        for x in range(76, 245):
            if pm.getpixel((x, yy)):
                px(img, x, yy, "grey2")
    ellipse(img, 76, 124, 244, 152, None, "grey3")
    # objects in the light: dropped badge, time card, coins, mop bucket
    shadow_dither(img, [(170, 140), (196, 140), (200, 146), (174, 146)], "ink2", 0.7)
    poly(img, [(150, 134), (172, 132), (176, 147), (153, 149)], "white", "ink")
    qpoly(img, [(150, 134), (172, 132), (176, 147), (153, 149)], 0, 0, 1, 0.25, "red2")
    poly(img, [(112, 138), (132, 140), (130, 148), (108, 146)], "wall1", "ink")
    qpoly(img, [(112, 138), (132, 140), (130, 148), (108, 146)], 0.1, 0.3, 0.9, 0.45, "grey3")
    for (cx, cy) in [(190, 142), (200, 146), (122, 130)]:
        ellipse(img, cx - 4, cy - 2, cx + 4, cy + 2, "yellow", "ink")
        px(img, cx - 2, cy - 1, "yellow2")
    # dust motes in the cone
    rnd = random.Random(9)
    for _ in range(44):
        y = rnd.randint(30, 118)
        t = (y - apex_y) / (140 - apex_y)
        half = 10 + 150 * t
        x = int(160 + rnd.uniform(-1, 1) * half * 0.8)
        px(img, x, y, rnd.choice(["white", "grey4", "grey3"]))
    # lamp housing & cable
    rect(img, 148, Y0, 24, 4, "ink2", "ink")
    rect(img, 156, Y0, 8, 2, "yellow2", None)
    vline(img, 160, Y0 - 1, Y0, "ink")
    return img


# ============================================================ scene 6: clock-in
def clockin_bg():
    img = new(W, H, "ink")
    # wall: pale panel wall, lit from the fluorescent tube at the top
    fieldfill(img, (0, Y0, W, Y1), ["wall1", "wall2", "wall3"],
              lambda x, y: 0.05 + (y - Y0) / 80.0 + 0.2 * abs(x - 160) / 160.0, 4)
    for x in range(0, W, 40):
        vline(img, x, Y0, 142, "wall3")
        vline(img, x + 1, Y0, 142, "wall1")
    hline(img, 0, W, 142, "grey2")
    # skirting / shelf
    rect(img, 0, 143, W, 14, "grey3", "ink")
    dither_grad(img, (1, 144, W - 1, 156), "grey4", "grey3", "y", 4, 0.0, 0.8)
    hline(img, 0, W, 144, "white")
    # fluorescent fixture across the top
    rect(img, 30, Y0 - 1, 260, 11, "grey4", "ink")
    rect(img, 34, Y0 + 1, 252, 6, "white", "ink")
    dither_flat(img, (35, Y0 + 2, 285, Y0 + 6), "white", "blue4", 0.3, 2)
    hline(img, 32, 288, Y0 + 9, "grey2")
    # glow cast on the wall
    for y in range(Y0 + 10, Y0 + 40):
        for x in range(26, 296):
            t = (y - Y0 - 10) / 30.0
            if (1 - t) * 0.7 > _thr(x, y, 4):
                c = img.getpixel((x, y))
                mp = {col("wall2"): col("wall1"), col("wall3"): col("wall2"), col("wall1"): col("white")}
                img.putpixel((x, y), mp.get(c, c))
    # ----- machine shadow on wall
    shadow_dither(img, [(108, 34), (206, 34), (206, 152), (108, 152)], "wall3", 0.7)
    # ----- machine body
    obox(img, 98, 30, 104, 114, "grey4", "white", "grey3")
    rect(img, 100, 32, 100, 4, "white", None)
    dither_flat(img, (100, 36, 198, 142), "grey4", "grey3", 0.12, 2)
    # screws
    for (sx, sy) in [(102, 34), (194, 34), (102, 138), (194, 138)]:
        rect(img, sx, sy, 3, 3, "grey2", "ink")
        px(img, sx + 1, sy + 1, "ink")
    # label plate
    sign(img, 108, 37, 84, 14, "blue1", "출퇴근 기록기", "white", None, 9, "blue2", 2)
    # LCD
    obox(img, 108, 54, 84, 32, "ink2", "grey1", "ink")
    rect(img, 111, 57, 78, 26, "green0", "ink")
    dither_grad(img, (112, 58, 188, 82), "green0", "green1", "y", 4, 0.0, 0.5)
    text(img, 150, 59, "23:58", "green3", 11, mult=2, align="center")
    # indicator lamps + keypad
    for i, c in enumerate(["red3", "green2", "yellow"]):
        ellipse(img, 112 + i * 9, 91, 118 + i * 9, 97, c, "ink")
        px(img, 114 + i * 9, 92, "white")
    for r in range(2):
        for k in range(3):
            obox(img, 150 + k * 12, 90 + r * 8, 10, 7, "grey3", "white", "grey2")
            px(img, 154 + k * 12, 93 + r * 8, "ink2")
    # card slot assembly
    poly(img, [(110, 108), (190, 108), (186, 140), (114, 140)], "grey3", "ink")
    rect(img, 116, 110, 68, 3, "white", None)
    obox(img, 118, 114, 64, 6, "ink2", "ink", None)
    rect(img, 120, 116, 60, 2, "ink", None)
    # inserted card (leaving the slot) + arrow decal
    poly(img, [(136, 100), (166, 100), (166, 124), (136, 124)], "wall1", "ink")
    rect(img, 137, 101, 28, 5, "red2", None)
    hline(img, 138, 163, 109, "grey3"); hline(img, 138, 163, 113, "grey3")
    rect(img, 140, 116, 10, 3, "grey4", "ink")
    for i in range(3):
        poly(img, [(122 + i * 5, 128), (127 + i * 5, 128), (125 + i * 5, 133)], "yellow", "ink") if False else None
    poly(img, [(146, 126), (156, 126), (151, 134)], "yellow", "ink")
    # re-draw slot lip over the card bottom
    rect(img, 118, 120, 64, 5, "grey2", "ink")
    rect(img, 118, 120, 64, 1, "white", None)
    # conduit + cable
    rect(img, 196, Y0 + 9, 4, 10, "grey3", "ink")
    vline(img, 197, Y0 + 10, Y0 + 17, "white")
    # ----- time card rack (right)
    obox(img, 216, 34, 80, 108, "grey2", "grey3", "grey1")
    rect(img, 219, 37, 74, 102, "grey1", "ink")
    rnd = random.Random(12)
    tabs = ["red2", "blue2", "yellow", "green2", "orange2", "purple2", "white", "red3"]
    for r in range(5):
        for k in range(2):
            sx, sy = 222 + k * 35, 40 + r * 20
            # pocket
            obox(img, sx, sy + 7, 32, 13, "grey3", "grey4", "grey2")
            if not (r == 3 and k == 1):
                lift = 3 if (r == 1 and k == 0) else 0
                rect(img, sx + 3, sy - lift, 26, 12, "wall1", "ink")
                rect(img, sx + 4, sy + 1 - lift, 24, 3, tabs[(r * 2 + k) % len(tabs)], None)
                hline(img, sx + 5, sx + 26, sy + 6 - lift, "grey3")
                hline(img, sx + 5, sx + 20, sy + 9 - lift, "grey3")
                obox(img, sx, sy + 7, 32, 13, "grey3", "grey4", "grey2")
            else:
                rect(img, sx + 2, sy + 9, 28, 9, "ink2", "ink")    # empty pocket: your card is missing
            num = "%02d" % (r * 2 + k + 1)
            text(img, sx + 16, sy + 10, num, "ink" if not (r == 3 and k == 1) else "grey3", 7, align="center")
    # ----- left wall decor: notices
    obox(img, 20, 44, 52, 64, "wall4", "white", "wall3")
    rect(img, 24, 48, 44, 14, "red2", "ink")
    text(img, 46, 50, "지각 금지", "yellow2", 9, align="center")
    for i in range(5):
        hline(img, 26, 64, 66 + i * 7, "grey3")
    rect(img, 26, 98, 14, 6, "yellow2", "ink")
    for (nx, ny, c) in [(14, 36, "yellow2")]:
        pass
    # tape corners
    for (tx, ty) in [(20, 44), (70, 44), (20, 106), (70, 106)]:
        rect(img, tx, ty, 4, 3, "grey4", None)
    obox(img, 22, 116, 40, 22, "white", "white", "grey3")          # clipboard w/ schedule
    for rr in range(3):
        for cc in range(5):
            rect(img, 25 + cc * 7, 120 + rr * 6, 5, 4, "grey4", "grey3")
    rect(img, 36, 112, 12, 5, "grey2", "ink")
    # sticky note on the machine side
    rect(img, 84, 62, 10, 10, "yellow", "ink"); hline(img, 86, 91, 66, "orange1"); hline(img, 86, 91, 69, "orange1")
    # pen cup on the shelf
    obox(img, 250, 146, 10, 10, "red2", "red3", "red1")
    for i, c in enumerate(["blue2", "ink", "red3"]):
        line(img, [(252 + i * 2, 146), (250 + i * 3, 138)], c)
    return img


def main():
    out = {
        "street_day": street(False),
        "street_night": street_night_full(),
        "crossing": crossing(),
        "title_bg": title_bg(),
        "death_bg": death_bg(),
        "clockin_bg": clockin_bg(),
    }
    names = []
    for n, im in out.items():
        letterbox(im)
        bad = off_palette(im)
        assert not bad, (n, bad)
        save(im, "bg/%s.png" % n)
        names.append("bg/%s.png" % n)
    print("wrote", names)
    contact(names, "_contact/bg_exterior.png", cols=2, scale=2)


if __name__ == "__main__":
    main()

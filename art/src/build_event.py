"""Act 2 night event gig assets for ONE MORE SHIFT.

Run:  python3 src/build_event.py
Writes assets/bg/event_plaza.png
       assets/props/{mascot,kid}.png/.json, balloon.png, balloon_b.png, water.png
       previews/_contact/event.png
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
from pxkit import *
from pxkit import _thr
from PIL import Image, ImageDraw
from build_delivery import glow, ovl, obox, hline, vline, speckle, floor_band

Y0 = 22


# ------------------------------------------------------------------ helpers
def pool(img, cx, cy, rx, ry, c, s=0.7, m=4, only=None):
    cc = col(c)
    on = {col(o) for o in only} if only else None
    for y in range(max(0, cy - ry), min(img.height, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(img.width, cx + rx + 1)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d >= 1:
                continue
            if on and img.getpixel((x, y)) not in on:
                continue
            if (1 - d) * s > _thr(x, y, m):
                img.putpixel((x, y), cc)


def emask(size, box):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m


def egg(img, x0, y0, x1, y1, base, sh, hi=None, t0=-0.5, t1=1.0, m=4):
    """Shaded ellipse: ink outline, base fill, dithered shadow bottom-right, highlight top-left."""
    ellipse(img, x0, y0, x1, y1, base, "ink")
    mk = emask(img.size, (x0 + 1, y0 + 1, x1 - 1, y1 - 1))
    dither_grad(img, (x0, y0, x1 + 1, y1 + 1), base, sh, "d", m, t0, t1, mk)
    if hi:
        w, h = x1 - x0, y1 - y0
        for dx, dy in ((0.28, 0.2), (0.2, 0.28), (0.34, 0.16)):
            px(img, x0 + int(w * dx) + 1, y0 + int(h * dy) + 1, hi)


def balloon_sprite(c="red"):
    """10x22 balloon + string. c: 'red' or 'yellow' (other ramps via tuple)."""
    base, sh, hi = {"red": ("red2", "red1", "red4"), "yellow": ("yellow", "orange2", "yellow2"),
                    "blue": ("blue2", "blue1", "blue3"), "green": ("green1", "green0", "green3"),
                    "pale": ("pale2", "pale1", "white"), "orange": ("orange2", "orange1", "orange4"),
                    "purple": ("purple2", "purple1", "grey4")}[c]
    im = new(10, 22)
    ellipse(im, 0, 0, 9, 12, base, "ink")
    # shadow crescent on the right/bottom (ordered dither between base and shadow)
    mk = emask(im.size, (1, 1, 8, 11))
    dither_grad(im, (0, 0, 10, 13), base, sh, "d", 2, -0.4, 1.1, mk)
    px(im, 7, 9, sh); px(im, 6, 10, sh)
    rect(im, 2, 2, 2, 3, hi)
    px(im, 2, 2, "white")
    # knot + string
    px(im, 4, 13, "ink"); px(im, 5, 13, "ink")
    px(im, 4, 14, sh); px(im, 5, 14, "ink")
    for i, y in enumerate(range(15, 22)):
        px(im, 5 if (i // 2) % 2 == 0 else 4, y, "grey3")
    return im


def water_sprite():
    im = new(6, 12)
    rect(im, 1, 0, 4, 3, "blue1", "ink")          # cap
    rect(im, 0, 3, 6, 9, "blue4", "ink")          # body
    rect(im, 1, 4, 1, 6, "white")                 # highlight
    rect(im, 1, 6, 4, 3, "blue2")                 # label
    px(im, 1, 6, "blue3")
    px(im, 4, 10, "blue3"); px(im, 3, 10, "blue3")
    px(im, 2, 3, "blue4"); px(im, 3, 3, "blue4")
    return im


def string_to(img, x0, y0, x1, y1, c="grey3"):
    """1px wavy string with a slight sag."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t + math.sin(t * 6.0 + x0) * 0.9
        y = y0 + (y1 - y0) * t
        px(img, int(round(x)), int(round(y)), c)


def place_balloon(img, bx, by, c, anchor):
    spr = balloon_sprite(c)
    # blank string of the sprite is redrawn towards the anchor
    spr2 = spr.crop((0, 0, 10, 15))
    paste(img, spr2, bx, by)
    string_to(img, bx + 5, by + 15, anchor[0], anchor[1])


def wave_line(img, pts, c, width=1):
    line(img, pts, c, width)


# =========================================================== BACKGROUND
def ceiling(im):
    rect(im, 0, Y0, W, 20, "ink")
    dither_grad(im, (0, Y0, W, 42), "ink", "blue0", "y", 4, 0.0, 0.8)
    # moon seen through a glass pane
    pool(im, 300, 31, 20, 14, "blue1", 0.4, 4)
    ellipse(im, 293, 24, 307, 38, "white", "grey4")
    for p in ((296, 29), (301, 33), (299, 35), (303, 27), (304, 31)):
        px(im, *p, "grey3")
    px(im, 295, 27, "white"); px(im, 296, 26, "white")
    # glass roof ribs + glints
    for sx in range(0, W, 40):
        rect(im, sx, Y0, 2, 20, "ink2")
        px(im, sx, Y0, "grey1")
    for sx in (40, 120, 200):
        line(im, [(sx + 2, Y0), (sx + 38, 41)], "ink2")
    rnd = random.Random(4)
    for _ in range(26):
        px(im, rnd.randint(0, W - 1), rnd.randint(Y0 + 1, 38), rnd.choice(["blue2", "grey2", "blue1"]))
    # steel beam under the glass
    rect(im, 0, 40, W, 3, "grey1")
    hline(im, 0, W - 1, 40, "ink")
    hline(im, 0, W - 1, 42, "ink")
    hline(im, 0, W - 1, 41, "grey2")


def back_wall(im):
    dither_grad(im, (0, 43, W, 138), "blue0", "blue1", "y", 4, 0.0, 0.85)
    # tall panel seams
    for sx in range(6, W, 40):
        vline(im, sx, 43, 129, "ink2")
        vline(im, sx + 1, 43, 129, "blue1")
    # kick rail
    rect(im, 0, 130, W, 8, "ink2")
    hline(im, 0, W - 1, 130, "grey1")
    hline(im, 0, W - 1, 137, "ink")
    dither_grad(im, (0, 131, W, 137), "ink2", "grey1", "y", 4, 0.0, 0.6)


def stage_backdrop(im):
    # truss poles + beam
    rect(im, 8, 58, 3, 71, "grey1", "ink")
    rect(im, 115, 58, 3, 71, "grey1", "ink")
    rect(im, 8, 58, 110, 3, "grey1", "ink")
    hline(im, 9, 116, 59, "grey2")
    # curtain
    rect(im, 11, 61, 104, 67, "purple0")
    for x in range(12, 114):
        k = (x - 12) % 6
        if k in (0, 1):
            vline(im, x, 62, 127, "purple1")
        elif k == 5:
            vline(im, x, 62, 127, "ink")
    dither_grad(im, (11, 61, 115, 128), "purple0", "ink", "y", 4, 0.0, 0.55)
    # warm spot pool on the curtain (stage lights)
    pool(im, 63, 98, 52, 36, "purple2", 0.5, 4, only=["purple1"])
    pool(im, 63, 98, 44, 30, "purple1", 0.35, 4, only=["purple0"])
    # banner (left blank - the game draws the text)
    rect(im, 16, 40, 95, 17, "wall1", "ink")
    rect(im, 18, 42, 91, 13, None, "red2")
    dither_grad(im, (19, 43, 108, 54), "white", "wall1", "y", 4, 0.0, 0.9)
    vline(im, 17, 41, 55, "white")
    hline(im, 17, 109, 56, "grey3")
    for hx in (24, 102):
        vline(im, hx, 43, 40, "ink")
    # bunting under the beam
    cols_ = ["red2", "yellow", "blue2", "white", "green1", "orange2"]
    for i, x in enumerate(range(12, 112, 6)):
        t = (x - 12) / 100
        y = 62 + int(4 * math.sin(math.pi * t))
        c = cols_[i % len(cols_)]
        poly(im, [(x, y), (x + 5, y), (x + 2, y + 5)], c, "ink")
        px(im, x + 1, y + 1, "white" if c != "white" else "grey3")


def shutters_and_signs(im):
    names = {124: "달빛문구", 164: "행복분식"}
    for sx in (124, 164):
        w = 38
        # shop sign (unlit)
        rect(im, sx, 66, w, 12, "ink2", "ink")
        text(im, sx + w // 2, 67, names[sx], "grey2", 9, align="center")
        # rolled-down shutter
        rect(im, sx, 80, w, 57, "grey2", "ink")
        dither_grad(im, (sx + 1, 81, sx + w - 1, 137), "grey3", "grey1", "y", 4, 0.1, 0.9)
        for y in range(83, 136, 3):
            hline(im, sx + 1, sx + w - 2, y, "grey1")
            hline(im, sx + 1, sx + w - 3, y - 1, "grey3")
        rect(im, sx + w // 2 - 3, 126, 7, 3, "grey1", "ink")
    # closed-notice paper
    rect(im, 130, 98, 14, 16, "white", "ink")
    text(im, 137, 99, "휴업", "red2", 9, align="center")
    hline(im, 132, 141, 109, "grey3")
    hline(im, 132, 139, 111, "grey3")


def escalator(im):
    # far-back escalator running up to the right, nobody on it
    # upper level void
    rect(im, 292, 43, 28, 33, "ink")
    pool(im, 306, 52, 14, 8, "blue1", 0.5, 4)
    for p in ((300, 56), (312, 50), (308, 62), (316, 58)):
        px(im, *p, "yellow")
    # truss under steps
    pts = [(220, 138), (292, 78), (320, 78), (320, 138)]
    poly(im, pts, "ink2", "ink")
    dither_grad(im, (220, 78, 320, 138), "ink2", "blue0", "y", 4, 0.0, 0.7,
                Image.new("L", im.size, 0))
    sl = lambda x: 138 - (x - 220) * 60 / 72
    for x in range(224, 292, 4):
        y = int(sl(x))
        line(im, [(x, y + 1), (x, y + 5)], "grey1")
    for x in range(220, 293):
        y = int(sl(x))
        px(im, x, y - 1, "ink")
        px(im, x, y, "grey3")
        px(im, x, y + 1, "grey2")
    # landing slab
    rect(im, 290, 76, 30, 4, "grey2", "ink")
    hline(im, 291, 318, 77, "grey3")
    # glass balustrade and handrail
    off = 16
    glass = Image.new("L", im.size, 0)
    ImageDraw.Draw(glass).polygon([(222, 136 - 2), (292, 78 - 2), (292, 78 - off), (222, 136 - off)], fill=255)
    for y in range(0, im.height):
        for x in range(0, im.width):
            if glass.getpixel((x, y)) and (x + y) % 2 == 0 and 40 < y:
                px(im, x, y, "blue2")
    for x in range(222, 293, 12):
        y = int(sl(x))
        vline(im, x, y - off - 1, y - 2, "ink")
    for x in range(222, 293):
        y = int(sl(x)) - off - 1
        px(im, x, y, "ink")
        px(im, x, y + 1, "grey3")
    # tiny red "out of service" cone-less light on the landing
    rect(im, 296, 70, 3, 2, "red2", "ink")


def plant(im, x, base_y, seed=1):
    rnd = random.Random(seed)
    # pot
    poly(im, [(x, base_y - 12), (x + 12, base_y - 12), (x + 10, base_y), (x + 2, base_y)], "orange1", "ink")
    rect(im, x + 1, base_y - 12, 11, 2, "orange2", "ink")
    for yy in range(base_y - 9, base_y - 1):
        px(im, x + 8 + (base_y - yy) // 5, yy, "orange0")
    # leaves
    for i in range(7):
        ang = -math.pi / 2 + (i - 3) * 0.42
        ln = rnd.randint(14, 24)
        ex = x + 6 + int(math.cos(ang) * ln)
        ey = base_y - 12 + int(math.sin(ang) * ln)
        line(im, [(x + 6, base_y - 12), (ex, ey)], "ink", 3)
    for i in range(7):
        ang = -math.pi / 2 + (i - 3) * 0.42
        ln = [20, 16, 22, 24, 21, 15, 19][i]
        ex = x + 6 + int(math.cos(ang) * ln)
        ey = base_y - 12 + int(math.sin(ang) * ln)
        line(im, [(x + 6, base_y - 12), (ex, ey)], "green1", 1)
        ellipse(im, ex - 2, ey - 2, ex + 2, ey + 1, "green1", "ink")
        px(im, ex - 1, ey - 1, "green2")
    px(im, x + 6, base_y - 13, "green0")


def string_lights(im):
    rnd = random.Random(9)
    cs = ["yellow", "red3", "blue3", "green2", "orange3"]
    for a in range(0, W, 80):
        pts = []
        for x in range(a, a + 81):
            t = (x - a) / 80
            y = 25 + 10 * (4 * t * (1 - t))
            pts.append((x, int(y)))
        for p in pts:
            if abs(p[0] - 300) >= 12:
                px(im, p[0], p[1], "grey1")
        for i, p in enumerate(pts):
            if abs(p[0] - 300) < 12:
                continue
            if i % 10 == 4 and i < 79:
                bulb = cs[(i // 10 + a // 80) % len(cs)]
                dead = (a, i) in ((160, 34), (80, 54))
                c = "grey2" if dead else bulb
                px(im, p[0], p[1] + 1, "ink")
                rect(im, p[0] - 1, p[1] + 2, 3, 3, c)
                px(im, p[0], p[1] + 3, "white" if not dead else "grey3")
    # anchor knobs at the rib joints
    for sx in range(0, W, 80):
        rect(im, sx, 24, 3, 3, "grey2", "ink")


def open_sign(im):
    # hanging "grand opening" sign
    x0, y0, w, h = 122, 45, 78, 17
    for cx in (x0 + 8, x0 + w - 9):
        vline(im, cx, 43, y0, "ink")
        vline(im, cx + 1, 43, y0, "grey2")
    rect(im, x0, y0, w, h, "blue1", "ink")
    rect(im, x0 + 2, y0 + 2, w - 4, h - 4, None, "yellow")
    dither_grad(im, (x0 + 3, y0 + 3, x0 + w - 3, y0 + h - 3), "blue1", "blue0", "y", 4, 0.0, 0.8)
    text(im, x0 + w // 2, y0 + 3, "그랜드 오픈", "yellow", 11, shadow="ink", edge="ink", align="center")
    # light spill under the sign
    pool(im, x0 + w // 2, y0 + h + 6, 44, 14, "blue2", 0.4, 4, only=["blue0", "blue1"])
    # marquee dots round the frame (every third one burnt out)
    for i, x in enumerate(range(x0 + 4, x0 + w - 3, 5)):
        if i % 4 != 2:
            px(im, x, y0, "yellow2")
            px(im, x, y0 + h - 1, "yellow2")


def stage(im):
    # floor pool of warm light first (so props sit in it)
    glow(im, 4, 138, 124, 157, "orange3", 0.28, 4, 14)
    # skirt
    rect(im, 8, 128, 111, 23, "ink")
    rect(im, 9, 129, 109, 21, "purple1")
    dither_grad(im, (9, 129, 118, 150), "purple1", "purple0", "y", 4, 0.0, 0.9)
    for x in range(10, 118, 7):
        vline(im, x, 134, 149, "purple0")
        px(im, x + 1, 135, "purple2")
    # deck lip (top surface line at y128)
    rect(im, 8, 128, 111, 3, "orange2", "ink")
    hline(im, 9, 117, 128, "orange3")
    hline(im, 9, 117, 129, "orange2")
    hline(im, 9, 117, 130, "orange1")
    # bunting along the skirt top
    cs = ["red2", "yellow", "blue2", "white", "green1", "orange2"]
    for i, x in enumerate(range(11, 116, 7)):
        c = cs[i % len(cs)]
        poly(im, [(x, 132), (x + 5, 132), (x + 2, 138)], c, "ink")
        px(im, x + 1, 133, "white" if c != "white" else "grey3")
    # shadow at base
    hline(im, 8, 118, 150, "ink")
    dither_flat(im, (8, 151, 119, 154), "blue1", "ink", 0.5, 2)
    # speakers
    for sx in (20, 94):
        rect(im, sx, 100, 14, 28, "grey1", "ink")
        dither_grad(im, (sx + 1, 101, sx + 13, 127), "grey2", "grey1", "d", 4, 0.0, 1.0)
        hline(im, sx + 1, sx + 12, 101, "grey3")
        ellipse(im, sx + 2, 112, sx + 11, 123, "ink2", "ink")
        ellipse(im, sx + 4, 114, sx + 9, 121, "grey1", "ink")
        rect(im, sx + 6, 116, 2, 2, "ink")
        px(im, sx + 5, 115, "grey2")
        ellipse(im, sx + 5, 104, sx + 8, 108, "grey2", "ink")
        px(im, sx + 5, 104, "grey4")
        rect(im, sx + 1, 126, 3, 2, "ink")
        rect(im, sx + 10, 126, 3, 2, "ink")
    # corner balloons tied at the stage corners
    for (bx, by, c, anc) in ((0, 88, "red", (9, 127)), (7, 98, "yellow", (9, 127)),
                             (2, 106, "blue", (9, 127))):
        place_balloon(im, bx, by, c, anc)
    for (bx, by, c, anc) in ((108, 80, "yellow", (116, 127)), (116, 90, "red", (116, 127)),
                             (120, 104, "green", (116, 127))):
        place_balloon(im, bx, by, c, anc)
    for ax in (9, 116):
        rect(im, ax - 1, 125, 3, 3, "red1", "ink")


def cart(im):
    glow(im, 138, 138, 204, 157, "orange3", 0.4, 4, 12)
    pool(im, 170, 118, 40, 40, "orange2", 0.22, 4, only=["blue0", "blue1"])
    # balloons first so the cart sits in front of the strings
    anchor = (170, 117)
    cl = [(150, 98, "red"), (160, 84, "yellow"), (172, 74, "red"), (183, 88, "blue"),
          (176, 100, "yellow"), (142 + 8, 80, "pale"), (186, 70, "green"), (163, 99, "orange"),
          (190, 96, "red"), (156, 70, "blue"), (168, 88, "purple")]
    for (bx, by, c) in sorted(cl, key=lambda t: -t[1]):
        place_balloon(im, bx, by, c, anchor)
    # post holding the strings
    rect(im, 169, 108, 3, 11, "grey2", "ink")
    rect(im, 167, 107, 7, 3, "grey3", "ink")
    # counter top
    rect(im, 146, 117, 49, 5, "grey4", "ink")
    hline(im, 147, 192, 118, "white")
    hline(im, 147, 192, 120, "grey3")
    # body with stripes
    rect(im, 148, 122, 45, 22, "white", "ink")
    for x in range(149, 192, 6):
        rect(im, x, 123, 3, 20, "red2")
        px(im, x, 123, "red3")
    dither_grad(im, (149, 123, 192, 143), "white", "grey3", "y", 4, 0.0, 0.5, None) if False else None
    dither_flat(im, (149, 136, 192, 143), "red2", "red1", 0.5, 2, mask=None) if False else None
    # sign panel
    rect(im, 160, 126, 22, 13, "yellow2", "ink")
    hline(im, 161, 180, 127, "white")
    text(im, 171, 128, "풍선", "red1", 9, align="center")
    # underside + wheels + handle
    rect(im, 148, 143, 45, 3, "ink2", "ink")
    for wx in (156, 185):
        ellipse(im, wx - 4, 145, wx + 4, 153, "ink2", "ink")
        ellipse(im, wx - 2, 147, wx + 2, 151, "grey3", "ink")
        px(im, wx, 149, "ink")
    rect(im, 144, 122, 4, 2, "grey2", "ink")
    vline(im, 144, 124, 140, "ink")
    # cooler box with water bottles standing on its lid
    rect(im, 196, 139, 14, 11, "blue2", "ink")
    dither_grad(im, (197, 141, 209, 149), "blue2", "blue1", "d", 4, 0.0, 0.9)
    rect(im, 195, 136, 16, 4, "white", "ink")
    hline(im, 196, 209, 137, "grey4")
    rect(im, 200, 143, 6, 2, "white", "ink")
    wb = water_sprite()
    paste(im, wb, 197, 124)
    paste(im, wb, 203, 125)
    # a third bottle lying in front, tipped over


def queue(im):
    glow(im, 204, 138, 320, 157, "blue3", 0.16, 4, 10)
    # floor sticker line + footprints
    for x in range(207, 318, 9):
        rect(im, x, 147, 6, 2, "yellow")
        hline(im, x, x + 5, 149, "orange1")
    for fx in (222, 250, 280):
        rect(im, fx, 151, 2, 3, "grey4")
        rect(im, fx + 4, 152, 2, 3, "grey4")
        px(im, fx, 151, "white")
    # confetti on the floor
    rnd = random.Random(11)
    for _ in range(60):
        px(im, rnd.randint(4, 316), rnd.randint(140, 156),
           rnd.choice(["red3", "yellow", "blue3", "green2", "orange3", "white"]))
    # a lost child's shoe
    rect(im, 232, 144, 5, 3, "red2", "ink")
    px(im, 233, 144, "red4")
    # stanchions (posts stand behind the floor line so walkers overlap them)
    posts = [213, 239, 265, 291, 316]
    for a, b in zip(posts[:-1], posts[1:]):
        for x in range(a, b + 1):
            t = (x - a) / (b - a)
            y = 129 + int(round(3 * math.sin(math.pi * t)))
            px(im, x, y - 1, "red3")
            px(im, x, y, "red2")
            px(im, x, y + 1, "red1")
    px(im, 212, 130, "red2")
    for x in posts:
        ellipse(im, x - 4, 139, x + 4, 142, "grey2", "ink")
        hline(im, x - 2, x + 2, 140, "grey3")
        rect(im, x - 1, 126, 3, 14, "grey3", "ink")
        vline(im, x, 127, 138, "grey4")
        ellipse(im, x - 2, 124, x + 2, 128, "yellow", "ink")
        px(im, x - 1, 125, "yellow2")
        # rope clip
        rect(im, x - 1, 129, 3, 3, "red2", "ink")


def build_plaza():
    im = new(W, H, "ink")
    ceiling(im)
    back_wall(im)
    stage_backdrop(im)
    shutters_and_signs(im)
    escalator(im)
    plant(im, 121 - 1 + 1, 138, 2)       # plant between stage and shutters (x 122..134)
    plant(im, 205, 138, 5)
    string_lights(im)
    open_sign(im)
    floor_band(im, 138, 158, "grey1", "grey2", "ink2", "blue2", 20, 5)
    # the floor beyond the guest area reflects the cold moon
    pool(im, 276, 148, 40, 8, "blue3", 0.3, 4, only=["grey1", "grey2"])
    stage(im)
    cart(im)
    queue(im)
    letterbox(im)
    return im


# =========================================================== MASCOT
BODY = ("blue2", "blue1", "blue3")


def bun_head(img, cx, top, small=False):
    """Steamed-bun head. Big: x cx-18..cx+18, y top..top+35."""
    if not small:
        rx, ry, cy = 18, 16, top + 19
        ellipse(img, cx - 3, top, cx + 3, top + 5, "white", "ink")   # twisted top knot
        egg(img, cx - rx, cy - ry, cx + rx, cy + ry, "white", "grey4", "white", -0.3, 1.1, 4)
        # pleat lines from the knot
        for dx, ex in ((-3, -10), (-1, -4), (1, 4), (3, 10)):
            line(img, [(cx + dx, top + 6), (cx + ex, top + 13)], "grey3")
        # eyes
        rect(img, cx - 9, top + 17, 2, 3, "ink")
        rect(img, cx + 7, top + 17, 2, 3, "ink")
        px(img, cx - 9, top + 17, "grey2"); px(img, cx + 7, top + 17, "grey2")
        # cheeks
        for sx in (-1, 1):
            x0 = cx + sx * 12 - 2
            rect(img, x0, top + 22, 4, 3, "red3")
            dither_flat(img, (x0, top + 22, x0 + 4, top + 25), "red3", "red4", 0.5, 2)
        # smile
        for (dx, dy) in ((-3, 23), (3, 23), (-2, 24), (2, 24), (-1, 25), (0, 25), (1, 25)):
            px(img, cx + dx, top + dy, "ink")
    else:
        rx, ry, cy = 12, 11, top + 13
        egg(img, cx - rx, cy - ry, cx + rx, cy + ry, "white", "grey4", "white", -0.3, 1.1, 4)
        ellipse(img, cx - 2, top, cx + 2, top + 3, "white", "ink")
        egg(img, cx - rx, cy - ry, cx + rx, cy + ry, "white", "grey4", "white", -0.3, 1.1, 4)
        for dx, ex in ((-2, -6), (0, 0), (2, 6)):
            line(img, [(cx + dx, top + 4), (cx + ex, top + 8)], "grey3")
        rect(img, cx - 6, cy - 2, 1, 2, "ink")
        rect(img, cx + 5, cy - 2, 1, 2, "ink")
        for sx in (-1, 1):
            x0 = cx + sx * 8 - 1
            rect(img, x0, cy + 1, 3, 2, "red3")
        for (dx, dy) in ((-2, 2), (2, 2), (-1, 3), (0, 3), (1, 3)):
            px(img, cx + dx, cy + dy, "ink")


def mascot_arm(img, cx, side, mode, dy=0, swing=0):
    s = -1 if side == "L" else 1
    sx = cx + s * 11
    if mode == "down":
        x = sx + (0 if s > 0 else -5)
        rect(img, x, 38 + dy + swing, 6, 9, "blue2", "ink")
        vline(img, x + (4 if s > 0 else 1), 40 + dy + swing, 45 + dy + swing, "blue1" if s > 0 else "blue3")
        egg(img, x, 45 + dy + swing, x + 5, 50 + dy + swing, "white", "grey4")
    else:
        hx, hy = mode
        line(img, [(sx - 1, 40 + dy), (hx, hy)], "ink", 7)
        line(img, [(sx - 1, 40 + dy), (hx, hy)], "blue2", 5)
        line(img, [(sx - 2, 38 + dy), (hx - 1, hy + 1)], "blue3", 1)
        egg(img, hx - 3, hy - 4, hx + 3, hy + 2, "white", "grey4")


def mascot_body(cx, dy=0, lift=(0, 0), arms=("down", "down"), swing=(0, 0), tilt=0, spread=0):
    im = new(48, 64)
    # legs + shoes (feet stay on the bottom row except lifted ones)
    for i, sx in enumerate((-1, 1)):
        lx = cx + sx * 7 - 4 + (sx * spread)
        lf = lift[i]
        rect(im, lx, 50 - lf, 9, 9, "blue1", "ink")
        vline(im, lx + 1, 51 - lf, 56 - lf, "blue2")
        sx0 = lx - 2 if sx < 0 else lx - 1
        egg(im, sx0, 58 - lf, sx0 + 12, 63 - lf, "white", "grey3")
        hline(im, sx0 + 2, sx0 + 10, 60 - lf, "grey3") if False else None
    # arms behind torso
    mascot_arm(im, cx, "R", arms[1], dy, swing[1])
    # torso with collar
    egg(im, cx - 12, 31 + dy, cx + 12, 54 + dy, *BODY)
    # sash (blank) across the chest
    line(im, [(cx - 10, 38 + dy), (cx + 9, 51 + dy)], "ink", 6)
    line(im, [(cx - 10, 38 + dy), (cx + 9, 51 + dy)], "orange3", 4)
    line(im, [(cx - 10, 37 + dy), (cx + 8, 50 + dy)], "yellow2", 1)
    # zipper down the middle
    vline(im, cx, 36 + dy, 52 + dy, "ink")
    for y in range(37 + dy, 52 + dy):
        px(im, cx - 1 if y % 2 else cx + 1, y, "grey3")
    rect(im, cx - 1, 36 + dy, 3, 3, "yellow", "ink")
    mascot_arm(im, cx, "L", arms[0], dy, swing[0])
    # neck collar: dark ring with a hollow interior
    ellipse(im, cx - 9, 28 + dy, cx + 9, 36 + dy, "red2", "ink")
    ellipse(im, cx - 7, 29 + dy, cx + 7, 34 + dy, "ink", "red1")
    px(im, cx - 8, 31 + dy, "red3")
    if tilt:
        out = new(48, 64)
        for y in range(64):
            sh = int(round((63 - y) * tilt))
            row = im.crop((0, y, 48, y + 1))
            out.paste(row, (-sh, y))
        im = out
    return im


def mascot_frame(kind):
    cx = 24
    if kind in ("idle_0", "idle_1"):
        d = 1 if kind == "idle_1" else 0
        im = mascot_body(cx, dy=d)
        bun_head(im, cx, 1 + d)
        return im
    if kind in ("wave_0", "wave_1"):
        hand = (42, 24) if kind == "wave_0" else (45, 27)
        im = mascot_body(cx, arms=("down", hand), dy=0)
        bun_head(im, cx, 1)
        return im
    if kind in ("walk_0", "walk_1"):
        a = kind == "walk_0"
        im = mascot_body(cx, dy=1 if a else 0, lift=(2, 0) if a else (0, 2), swing=(-1, 1) if a else (1, -1), spread=0)
        bun_head(im, cx, 1 + (1 if a else 0))
        return im
    # headless: body shifted left, the fallen full-size bun head resting on the floor in front of it
    # (head 32px wide; it overlaps the body's right side and reaches the frame edge)
    t = 0.0 if kind == "headoff_0" else 0.05
    im = mascot_body(16, tilt=t)
    cx, cy = 31, 49
    dither_flat(im, (cx - 14, 61, cx + 17, 64), "ink2", "ink2", 0.6, 2)          # floor shadow
    tilt_y = 1 if kind == "headoff_0" else -1                                     # head rocks a little between the frames
    ellipse(im, cx + 2 - tilt_y, cy - 18, cx + 8 - tilt_y, cy - 13, "white", "ink")   # knot, flopped to the side
    egg(im, cx - 16, cy - 14, cx + 16, cy + 14, "white", "grey4", "white", -0.3, 1.1, 4)
    for dx, ex in ((-3, -9), (0, -2), (3, 5), (6, 11)):                            # pleats
        line(im, [(cx + dx, cy - 11), (cx + ex, cy - 6)], "grey3")
    for sx_, ey in ((-1, cy - 3 + (0 if tilt_y > 0 else 1)), (1, cy - 3 + (1 if tilt_y > 0 else 0))):
        ex = cx + sx_ * 8 - (1 if sx_ < 0 else 0)
        if kind == "headoff_0":
            rect(im, ex, ey - 1, 2, 4, "ink")
            px(im, ex, ey - 1, "grey2")
        else:
            for (dx, dy) in ((0, 1), (1, 0), (2, 0), (3, 1)):                       # squeezed-shut arcs
                px(im, ex - 1 + dx, ey + dy, "ink")
    for sx_ in (-1, 1):                                                            # cheeks
        x0 = cx + sx_ * 11 - 2
        rect(im, x0, cy + 1 + (1 if sx_ > 0 else 0), 4, 3, "red3")
        dither_flat(im, (x0, cy + 1 + (1 if sx_ > 0 else 0), x0 + 4, cy + 4 + (1 if sx_ > 0 else 0)), "red3", "red4", 0.5, 2)
    for (dx, dy) in ((-3, 4), (-2, 5), (-1, 6), (0, 6), (1, 6), (2, 5), (3, 4)):    # a small wobbly smile
        px(im, cx + dx, cy + dy + (1 if kind == "headoff_1" else 0), "ink")
    return im


MASC_NAMES = ["idle_0", "idle_1", "wave_0", "wave_1", "headoff_0", "headoff_1", "walk_0", "walk_1"]


# =========================================================== KID
def kid_down(bob=0, happy=False):
    im = new(32, 48)
    cx = 16
    # legs + shoes
    for sx in (-1, 1):
        x = cx + sx * 3 - (2 if sx < 0 else 1)
        rect(im, x, 42, 4, 4, "blue1", "ink")
        rect(im, x - 1, 45, 6, 3, "white", "ink")
        px(im, x, 45, "grey4")
    # arms
    for sx in (-1, 1):
        x = cx - 10 if sx < 0 else cx + 6
        if happy and sx > 0:
            line(im, [(cx + 8, 35), (cx + 11, 28)], "ink", 4)
            line(im, [(cx + 8, 35), (cx + 11, 28)], "green1", 2)
            continue
        rect(im, x, 33 + bob, 4, 8, "green1", "ink")
        rect(im, x + 1, 40 + bob, 2, 2, "skin2", "ink")
    # jacket
    rect(im, cx - 7, 32 + bob, 14, 11, "green1", "ink")
    dither_grad(im, (cx - 6, 33 + bob, cx + 6, 42 + bob), "green1", "green0", "d", 4, -0.9, 0.7)
    for y in (35, 38, 41):
        hline(im, cx - 6, cx + 5, y + bob, "green0")
    for y in (34, 37, 40):
        px(im, cx - 6, y + bob, "green2"); px(im, cx - 5, y + bob, "green2")
    vline(im, cx, 33 + bob, 42 + bob, "green0")
    px(im, cx, 33 + bob, "yellow")
    # head
    ellipse(im, cx - 6, 24 + bob, cx + 6, 34 + bob, "skin2", "ink")
    rect(im, cx - 5, 31 + bob, 10, 2, "skin2")
    # beanie
    ellipse(im, cx - 7, 19 + bob, cx + 7, 26 + bob, "orange2", "ink")
    rect(im, cx - 7, 24 + bob, 15, 3, "orange3", "ink")
    for x in range(cx - 6, cx + 7, 2):
        px(im, x, 25 + bob, "orange2")
    px(im, cx - 4, 22 + bob, "orange3"); px(im, cx - 3, 21 + bob, "orange3")
    ellipse(im, cx - 2, 17 + bob, cx + 2, 21 + bob, "white", "ink")
    px(im, cx - 1, 18 + bob, "white")
    # face
    if happy:
        for ex in (cx - 4, cx + 2):
            px(im, ex, 30 + bob, "ink"); px(im, ex + 1, 29 + bob, "ink"); px(im, ex + 2, 30 + bob, "ink")
        rect(im, cx - 1, 32 + bob, 3, 1, "ink")
        px(im, cx - 2, 31 + bob, "ink"); px(im, cx + 2, 31 + bob, "ink")
        px(im, cx, 32 + bob, "red2")
    else:
        rect(im, cx - 4, 29 + bob, 2, 2, "ink")
        rect(im, cx + 2, 29 + bob, 2, 2, "ink")
        px(im, cx - 1, 32 + bob, "skin1"); px(im, cx, 32 + bob, "skin1")
    px(im, cx - 5, 31 + bob, "red4"); px(im, cx + 5, 31 + bob, "red4")
    if happy:
        # balloon held up by the string
        line(im, [(cx + 11, 27), (cx + 11, 14)], "grey3")
        paste(im, balloon_sprite("red").crop((0, 0, 10, 15)), cx + 6, 1)
        px(im, cx + 11, 28, "skin2"); rect(im, cx + 10, 27, 2, 2, "skin2", "ink")
    return im


def kid_side(phase):
    im = new(32, 48)
    cx = 16
    bob = 1 if phase in (1, 3) else 0
    # stride: legs (front, back)
    strides = {0: (-3, 3), 1: (0, 0), 2: (3, -3), 3: (0, 0)}
    fl, bl = strides[phase]
    for off, back in ((bl, True), (fl, False)):
        x = cx - 2 + off
        lift = 1 if (phase in (1, 3) and not back and phase == 1) or (phase == 3 and back) else 0
        rect(im, x, 41, 4, 5 - lift, "blue1" if back else "blue1", "ink")
        rect(im, x - 2, 45 - lift, 6, 3, "grey4" if back else "white", "ink")
    # back arm
    ax = {0: 2, 1: 0, 2: -2, 3: 0}[phase]
    rect(im, cx - 1 + ax, 34 + bob, 4, 7, "green0", "ink")
    # jacket
    rect(im, cx - 6, 32 + bob, 12, 11, "green1", "ink")
    dither_grad(im, (cx - 5, 33 + bob, cx + 5, 42 + bob), "green1", "green0", "d", 4, -0.9, 0.7)
    for y in (35, 38, 41):
        hline(im, cx - 5, cx + 4, y + bob, "green0")
    px(im, cx - 5, 34 + bob, "green2"); px(im, cx - 4, 34 + bob, "green2")
    # head facing left
    ellipse(im, cx - 6, 24 + bob, cx + 5, 34 + bob, "skin2", "ink")
    px(im, cx - 7, 29 + bob, "skin2"); px(im, cx - 7, 30 + bob, "ink"); px(im, cx - 7, 28 + bob, "ink")
    px(im, cx - 6, 29 + bob, "skin2")
    # beanie (pom trails behind)
    ellipse(im, cx - 6, 19 + bob, cx + 6, 26 + bob, "orange2", "ink")
    rect(im, cx - 6, 24 + bob, 13, 3, "orange3", "ink")
    for x in range(cx - 5, cx + 6, 2):
        px(im, x, 25 + bob, "orange2")
    px(im, cx - 3, 22 + bob, "orange3"); px(im, cx - 2, 21 + bob, "orange3")
    ellipse(im, cx + 3, 18 + bob, cx + 7, 22 + bob, "white", "ink")
    # face
    rect(im, cx - 4, 29 + bob, 2, 2, "ink")
    px(im, cx - 5, 32 + bob, "skin1")
    px(im, cx - 3, 31 + bob, "red4")
    # front arm
    fx = {0: -2, 1: 0, 2: 2, 3: 0}[phase]
    rect(im, cx - 2 + fx, 34 + bob, 4, 7, "green1", "ink")
    rect(im, cx - 2 + fx, 40 + bob, 3, 2, "skin2", "ink")
    return im


KID_NAMES = ["down_idle_0", "down_idle_1", "left_walk_0", "left_walk_1", "left_walk_2", "left_walk_3", "happy_0"]


def main():
    plaza = build_plaza()
    assert not off_palette(plaza)
    save(plaza, "bg/event_plaza.png")

    frames = [mascot_frame(n) for n in MASC_NAMES]
    for f in frames:
        assert not off_palette(f)
    sheet([outline(f) if False else f for f in frames], "props/mascot", MASC_NAMES, cols=4)

    kf = [kid_down(0), kid_down(1)] + [kid_side(p) for p in range(4)] + [kid_down(0, happy=True)]
    for f in kf:
        assert not off_palette(f)
    sheet(kf, "props/kid", KID_NAMES, cols=7)

    for nm, c in (("balloon", "red"), ("balloon_b", "yellow")):
        b = balloon_sprite(c)
        assert not off_palette(b)
        save(b, f"props/{nm}.png", 8)
    w = water_sprite()
    assert not off_palette(w)
    save(w, "props/water.png", 8)

    contact(["bg/event_plaza.png", "props/mascot.png", "props/kid.png",
             "props/balloon.png", "props/balloon_b.png", "props/water.png"],
            "_contact/event.png", cols=2, scale=3)
    print("done")


if __name__ == "__main__":
    main()

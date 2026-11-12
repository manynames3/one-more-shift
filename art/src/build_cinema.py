"""Act 4 (night cinema 별빛극장) assets for ONE MORE SHIFT.

Run:  python3 src/build_cinema.py
Writes assets/bg/{cinema_lobby,cinema_hall,cinema_booth}.png
       assets/props/{screen_film,usher}.png/.json, beam.png, reel.png
       previews/_contact/cinema.png
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
from pxkit import *
from pxkit import _thr
from PIL import Image, ImageDraw
from build_delivery import glow, ovl, obox, hline, vline, speckle, mk_mask, dpoly

Y0, Y1 = 22, 157


def lit_sign(im, x, y, w, h, s, c="yellow", bc="orange2", f=9, tdx=0, tdy=-1):
    rect(im, x, y, w, h, "ink", "ink")
    rect(im, x + 1, y + 1, w - 2, h - 2, None, bc)
    text(im, x + w // 2 + tdx, y + tdy + 1, s, c, f, align="center")


def poster(im, x, y, w, h, kind, title, frame="orange3"):
    rect(im, x - 1, y - 1, w + 2, h + 2, "ink")
    rect(im, x, y, w, h, frame)
    rect(im, x, y, w, 1, "orange4")
    ix, iy, iw, ih = x + 2, y + 2, w - 4, h - 4
    ty = iy + ih - 12
    if kind == "moon":
        dither_grad(im, (ix, iy, ix + iw, ty), "blue0", "blue1", "y", 4, 0, 1)
        cx, cy = ix + iw // 2, iy + 9
        ellipse(im, cx - 5, cy - 5, cx + 5, cy + 5, "yellow2", "ink")
        px(im, cx - 2, cy - 2, "white")
        rect(im, ix, ty - 6, iw, 6, "ink2")
        rect(im, ix + 3, ty - 11, 4, 5, "ink"); rect(im, ix + iw - 8, ty - 9, 3, 3, "ink")
    elif kind == "umbrella":
        dither_grad(im, (ix, iy, ix + iw, ty), "wall4", "red4", "y", 2, 0, 0.7)
        cx = ix + iw // 2
        poly(im, [(cx - 8, iy + 15), (cx - 6, iy + 8), (cx, iy + 5), (cx + 6, iy + 8), (cx + 8, iy + 15)], "red2", "ink")
        for sx in (cx - 3, cx + 3):
            line(im, [(sx, iy + 6), (sx, iy + 15)], "red1")
        line(im, [(cx, iy + 15), (cx, iy + 26)], "ink")
        px(im, cx - 1, iy + 26, "ink"); px(im, cx - 2, iy + 25, "ink")
    elif kind == "train":
        dither_grad(im, (ix, iy, ix + iw, ty), "ink2", "purple1", "y", 4, 0, 1)
        rect(im, ix, ty - 14, iw, 7, "grey2", "ink")
        for k in range(ix + 1, ix + iw - 3, 6):
            rect(im, k, ty - 12, 4, 3, "yellow2")
        line(im, [(ix, ty - 4), (ix + iw, ty - 4)], "ink")
        px(im, ix + 3, iy + 4, "yellow2"); px(im, ix + iw - 5, iy + 7, "white")
    else:  # face / hands
        dither_grad(im, (ix, iy, ix + iw, ty), "green0", "green1", "y", 2, 0, 0.8)
        ellipse(im, ix + iw // 2 - 6, iy + 5, ix + iw // 2 + 6, iy + 19, "skin2", "ink")
        rect(im, ix + iw // 2 - 6, iy + 5, 13, 5, "brown0")
        px(im, ix + iw // 2 - 3, iy + 12, "ink"); px(im, ix + iw // 2 + 3, iy + 12, "ink")
    rect(im, ix, ty, iw, ih - (ty - iy), "ink")
    if title:
        text(im, x + w // 2, ty + 1, title, "yellow2", 9, align="center")


def hanging_bulb(im, x, y, r=22, s=0.6, c="orange3"):
    glow_r = r
    for yy in range(max(0, y - r), min(im.height, y + r)):
        for xx in range(max(0, x - r), min(im.width, x + r)):
            d = ((xx - x) ** 2 + (yy - y) ** 2) ** 0.5 / r
            if d < 1 and (1 - d) * s > _thr(xx, yy, 4):
                im.putpixel((xx, yy), col(c))


def wall_pattern(im, box, base, hi, step=8):
    x0, y0, x1, y1 = box
    for y in range(y0 + 3, y1, step):
        for x in range(x0 + 3 + ((y - y0) // step % 2) * step // 2, x1, step):
            px(im, x, y, hi); px(im, x + 1, y, hi); px(im, x, y + 1, hi)


# ================================================================== LOBBY
def build_lobby():
    im = new(W, H, "ink")
    # wall
    dither_grad(im, (0, 34, W, 139), "brown0", "orange0", "y", 2, 0.0, 0.9)
    wall_pattern(im, (0, 34, W, 112), "brown0", "brown1", 8)
    # wainscot
    rect(im, 0, 114, W, 25, "brown0")
    dither_grad(im, (0, 116, W, 139), "brown0", "brown1", "y", 4, 0.0, 0.5)
    for x in range(0, W, 24):
        rect(im, x + 2, 118, 20, 18, None, "ink")
        hline(im, x + 3, x + 21, 119, "brown1")
    hline(im, 0, W - 1, 113, "ink"); hline(im, 0, W - 1, 114, "orange1"); hline(im, 0, W - 1, 115, "orange0")
    # ceiling + cornice
    rect(im, 0, Y0, W, 12, "ink")
    dither_grad(im, (0, Y0, W, 34), "ink", "brown0", "y", 4, 0.0, 0.7)
    hline(im, 0, W - 1, 33, "ink"); hline(im, 0, W - 1, 34, "orange0")
    for x in range(0, W, 16):
        px(im, x, 32, "orange0")
    # carpet floor
    dither_grad(im, (0, 139, W, Y1), "red0", "red1", "y", 4, 0.1, 0.9)
    hline(im, 0, W - 1, 138, "ink")
    rect(im, 0, 139, W, 2, "orange0")
    for x in range(-8, W + 16, 16):
        for k, (dy) in enumerate(range(0, 3)):
            pass
        cx, cy = x + 8, 148
        poly(im, [(cx, cy - 5), (cx + 6, cy), (cx, cy + 5), (cx - 6, cy)], None, "orange0")
        px(im, cx, cy, "orange1"); px(im, cx - 12, cy, "orange1")
    speckle(im, (0, 142, W, Y1), "red2", 60, 5)
    speckle(im, (0, 142, W, Y1), "ink2", 40, 6)
    rect(im, 0, Y1 - 1, W, 1, "red0")

    # ---- ticket booth x40..100
    lit_sign(im, 52, 42, 38, 12, "매표소", f=9)
    obox(im, 40, 54, 60, 66, "brown1", "brown2", "brown0")
    dither_grad(im, (41, 55, 99, 119), "brown1", "brown0", "y", 2, 0.0, 0.5)
    # window
    rect(im, 45, 59, 50, 52, "ink")
    rect(im, 46, 60, 48, 50, "orange3")
    rect(im, 47, 61, 46, 48, "ink2")
    # inside: shelf, ticket printer, lamp
    rect(im, 50, 94, 18, 14, "grey1", "ink"); rect(im, 52, 96, 10, 3, "grey3")
    rect(im, 52, 102, 12, 2, "grey4")
    rect(im, 76, 64, 3, 20, "ink"); poly(im, [(72, 64), (84, 64), (80, 58), (76, 58)], "orange3", "ink")
    glow(im, 66, 66, 92, 100, "orange3", 0.5, 4, 6)
    # glass shine
    for k in range(0, 40, 2):
        px(im, 50 + k // 2, 62 + k, "blue3"); px(im, 51 + k // 2, 62 + k, "blue4")
    for k in range(0, 24, 2):
        px(im, 78 + k // 2, 62 + k, "blue3")
    # speaker grille + slot
    for gx in range(65, 76, 2):
        for gy in (76, 78, 80):
            px(im, gx, gy, "grey2")
    rect(im, 54, 109, 32, 4, "ink"); rect(im, 56, 110, 28, 2, "orange0")
    # counter
    rect(im, 40, 116, 62, 5, "brown3", "ink")
    hline(im, 41, 100, 117, "orange4")
    rect(im, 40, 121, 60, 28, "brown1", "ink")
    dither_grad(im, (41, 122, 99, 148), "brown1", "brown0", "y", 4, 0.0, 0.6)
    for x in (46, 66, 86):
        rect(im, x, 125, 14, 18, None, "ink")
        hline(im, x + 1, x + 12, 126, "brown2")
    rect(im, 40, 148, 60, 2, "ink")
    # small items on counter
    rect(im, 88, 109, 9, 7, "grey3", "ink"); rect(im, 89, 110, 7, 2, "blue3")   # ticket machine
    rect(im, 92, 112, 5, 2, "yellow")

    # ---- showtimes board x108..150
    rect(im, 107, 37, 44, 46, "ink")
    rect(im, 108, 38, 42, 44, "brown2")
    rect(im, 110, 40, 38, 40, "ink2")
    rect(im, 110, 40, 38, 11, "ink")
    text(im, 129, 40, "상영표", "yellow", 9, align="center")
    for k in range(4):
        yy = 54 + k * 7
        rect(im, 112, yy, 9, 3, "grey3")
        rect(im, 124, yy, 22, 3, "grey1")
        hline(im, 112, 146, yy + 5, "ink")
    glow(im, 108, 83, 150, 100, "orange3", 0.12, 4, 6)

    # ---- posters
    poster(im, 9, 44, 26, 56, "moon", "달빛")
    poster(im, 208, 52, 18, 46, "umbrella", "우산")
    poster(im, 266, 54, 16, 44, "train", "")
    poster(im, 120, 92, 20, 18, "face", "")

    # ---- popcorn machine + snack counter (x150..205)
    rect(im, 150, 118, 56, 5, "orange4", "ink")
    rect(im, 150, 123, 56, 27, "red2", "ink")
    dither_grad(im, (151, 124, 205, 149), "red2", "red1", "y", 4, 0.0, 0.9)
    for x in range(152, 204, 6):
        vline(im, x, 125, 147, "red1")
        vline(im, x + 1, 125, 147, "white") if (x // 6) % 2 == 0 else None
    rect(im, 150, 148, 56, 2, "ink")
    # machine
    rect(im, 154, 84, 26, 34, "red2", "ink")
    rect(im, 155, 85, 24, 3, "red3")
    rect(im, 157, 91, 20, 20, "ink", "ink")
    rect(im, 158, 92, 18, 18, "yellow2")
    dither_grad(im, (158, 92, 176, 110), "yellow2", "orange3", "y", 4, 0.0, 0.9)
    rng = random.Random(8)
    for _ in range(70):
        x, y = rng.randint(159, 174), rng.randint(97, 109)
        px(im, x, y, rng.choice(["white", "orange4", "white", "yellow2"]))
    rect(im, 158, 92, 18, 3, "ink2")
    rect(im, 154, 80, 26, 5, "red1", "ink")
    rect(im, 158, 112, 18, 5, "grey2", "ink")
    rect(im, 159, 100, 1, 8, "white")  # glass shine
    lit_sign(im, 160, 73, 14, 8, "팝", f=9, tdy=-2)
    # cup tower + soda
    for k in range(4):
        rect(im, 186, 104 + k * 3, 9, 3, "white" if k % 2 == 0 else "red3", "ink")
    rect(im, 197, 100, 7, 18, "blue2", "ink"); rect(im, 198, 103, 5, 4, "white")
    px(im, 200, 109, "yellow2")
    glow(im, 150, 120, 206, 140, "orange3", 0.18, 4, 6)
    # menu board
    rect(im, 177, 60, 29, 20, "ink"); rect(im, 178, 61, 27, 18, "brown0", "orange1")
    for k in range(3):
        rect(im, 181, 65 + k * 5, 12, 2, "grey3"); rect(im, 196, 65 + k * 5, 6, 2, "yellow")

    # ---- Hall 3 door x230..262 top 88 bottom 150
    rect(im, 229, 87, 34, 64, "ink")
    rect(im, 230, 88, 32, 62, "brown0")
    for sx in (231, 247):
        rect(im, sx, 89, 14, 59, "red1", "ink")
        dither_grad(im, (sx + 1, 90, sx + 14, 147), "red2", "red0", "y", 2, 0.0, 0.8)
        for yy in range(95, 146, 8):
            for xx in range(sx + 3, sx + 13, 5):
                px(im, xx, yy, "red3")
        rect(im, sx + 3, 100, 8, 8, "ink"); rect(im, sx + 4, 101, 6, 6, "blue0")
        px(im, sx + 5, 102, "blue3")
    rect(im, 244, 122, 2, 10, "orange3", "ink"); rect(im, 247, 122, 2, 10, "orange3", "ink")
    rect(im, 229, 150, 34, 2, "ink2")
    lit_sign(im, 235, 73, 24, 13, "3관", f=9)
    glow(im, 226, 74, 266, 92, "orange3", 0.18, 4, 5)
    # floor light spill from door window
    glow(im, 230, 151, 262, 157, "orange2", 0.15, 4, 6, up=True)

    # ---- stairs to booth x284..318
    rect(im, 282, 34, 38, 105, "ink")
    dither_grad(im, (284, 35, W, 150), "ink", "brown0", "y", 4, 0.1, 0.75)
    vline(im, 283, 34, 150, "orange0"); vline(im, 282, 34, 150, "ink")
    rise, run = 6, 5
    n = 8
    for k in range(n):
        x = 284 + k * run
        y = 150 - (k + 1) * rise
        rect(im, x, y, W - x, 150 - y, "brown0", None)
        hline(im, x, W - 1, y, "orange4")        # tread
        hline(im, x, x + run - 1, y + 1, "brown2")
        vline(im, x, y, y + rise, "ink")         # riser edge
        rect(im, x, y + 2, run, rise - 2, "brown1") if False else None
    # fill under stairs w/ dither shadow
    ovl(im, (284, 100, W, 150), "ink", 0.15, 2, "brown0")
    # banister
    pts = [(284, 124), (320, 80)]
    line(im, [(285, 130), (319, 94)], "ink", 3)
    line(im, [(285, 129), (319, 93)], "orange3")
    for k in range(0, 8):
        x = 286 + k * 5
        yb = 150 - (k + 1) * rise
        yt = 129 - int(k * 4.6)
        vline(im, x, yt + 1, yb, "orange0")
    rect(im, 284, 126, 3, 24, "orange1", "ink")
    # sign 영사실
    lit_sign(im, 285, 50, 32, 13, "영사실", c="yellow", bc="red2", f=9)
    poly(im, [(299, 66), (305, 66), (302, 71)], "red3", "ink")
    glow(im, 284, 50, 320, 76, "red3", 0.14, 4, 4)

    # ---- chandelier x168 (dim)
    cx = 168
    vline(im, cx, Y0, 34, "ink2"); vline(im, cx + 1, Y0, 34, "grey1")
    ellipse(im, cx - 13, 36, cx + 14, 44, "orange0", "ink")
    rect(im, cx - 3, 33, 8, 4, "orange2", "ink")
    for bx in (cx - 12, cx - 6, cx + 1, cx + 7, cx + 13):
        rect(im, bx, 31, 2, 6, "ink2")
    for bx in (cx - 12, cx - 4, cx + 3, cx + 12):
        px(im, bx, 45, "orange3"); px(im, bx, 46, "ink")
        px(im, bx + 1, 45, "ink")
    for bx in (cx - 11, cx - 5, cx + 2, cx + 8, cx + 14):
        px(im, bx, 38, "orange3")
    px(im, cx - 13, 40, "yellow2"); px(im, cx + 12, 40, "yellow2")
    hanging_bulb(im, cx, 41, 26, 0.35, "orange2")

    # wall sconces
    for sx in (104, 152, 224, 272):
        rect(im, sx, 66, 6, 3, "orange0", "ink"); rect(im, sx + 1, 62, 4, 4, "orange4", "ink")
        hanging_bulb(im, sx + 3, 64, 12, 0.35, "orange3")
    # 2AM dimness
    ovl(im, (0, Y0, W, 60), "ink", 0.22, 2)
    ovl(im, (0, 138, W, Y1), "ink", 0.12, 2)
    ovl(im, (0, Y0, 22, Y1), "ink", 0.3, 2); ovl(im, (W - 14, Y0, W, Y1), "ink", 0.2, 2)
    # floor guard shadows under booth/popcorn
    letterbox(im)
    return im


# ================================================================== HALL
def seat(im, x, y, w, h, base, sh, hi):
    poly(im, [(x + 2, y), (x + w - 3, y), (x + w - 1, y + 2), (x + w - 1, y + h - 1), (x, y + h - 1), (x, y + 2)], base, "ink")
    dither_grad(im, (x + 1, y + 1, x + w - 1, y + h - 1), base, sh, "d", 2, 0.0, 1.0, mk_mask(
        [(x + 3, y + 1), (x + w - 4, y + 1), (x + w - 2, y + 3), (x + w - 2, y + h - 2), (x + 1, y + h - 2), (x + 1, y + 3)], im.size))
    hline(im, x + 3, x + w - 5, y + 1, hi)
    vline(im, x + 1, y + 3, y + h // 2, hi)
    hline(im, x + 1, x + w - 2, y + h - 3, sh)


def build_hall():
    im = new(W, H, "ink")
    # back wall
    dither_grad(im, (0, 34, W, 140), "ink", "purple0", "y", 4, 0.1, 0.8)
    for x in range(4, W, 14):
        vline(im, x, 34, 112, "ink2")
        if x % 28 == 4:
            px(im, x + 1, 50, "purple0")
    # ceiling
    rect(im, 0, Y0, W, 12, "ink")
    hline(im, 0, W - 1, 33, "ink2"); hline(im, 0, W - 1, 34, "purple0")
    # side wall acoustic panels at right
    dither_grad(im, (270, 34, W, 140), "purple0", "ink2", "y", 2, 0.0, 0.6)
    rect(im, 269, 34, 1, 106, "ink")
    # screen with frame + stage
    rect(im, 4, 32, 120, 90, "ink")
    rect(im, 5, 33, 118, 88, "grey1")
    rect(im, 6, 34, 116, 86, "grey4")
    dither_grad(im, (6, 34, 122, 120), "grey4", "white", "d", 4, 0.1, 0.8)
    # curtains
    rect(im, 0, 30, 4, 100, "red0", "ink"); rect(im, 124, 30, 5, 100, "red0", "ink")
    for y in range(30, 130, 3):
        px(im, 1, y, "red1"); px(im, 126, y, "red1")
    rect(im, 0, Y0, W, 8, "red1", "ink")
    for x in range(1, W, 5):
        vline(im, x, 23, 28, "red0"); px(im, x + 2, 24, "red2")
    # stage
    rect(im, 0, 121, 128, 19, "ink2")
    dither_grad(im, (0, 122, 128, 140), "ink2", "ink", "y", 2, 0.0, 0.9)
    hline(im, 0, 127, 121, "grey2"); hline(im, 0, 127, 122, "ink")
    # screen glow spill on floor / seat front
    glow(im, 0, 140, 135, 157, "grey2", 0.28, 4, 10)
    # exit side wall details
    rect(im, 277, 38, 3, 98, "ink"); vline(im, 281, 38, 136, "purple1")
    # seats: back row (higher, darker), front row
    for k, x in enumerate(range(130, 272, 14)):
        seat(im, x, 109, 12, 22, "red1", "red0", "red2")
    ovl(im, (128, 109, 272, 131), "ink", 0.22, 2)
    # row riser shadow
    rect(im, 128, 131, 144, 2, "ink")
    for k, x in enumerate(range(137, 272, 14)):
        seat(im, x, 120, 12, 21, "red2", "red1", "red3")
    ovl(im, (128, 120, 272, 141), "ink", 0.10, 2)
    # aisle step lights
    hline(im, 128, 271, 141, "ink")
    for x in range(130, 272, 10):
        px(im, x, 142, "orange2"); px(im, x + 1, 142, "orange1")
    # floor
    dither_grad(im, (0, 142, W, Y1), "red0", "ink", "y", 4, 0.1, 0.8)
    hline(im, 0, W - 1, 141, "ink2")
    for x in range(0, W, 12):
        for y in range(146, Y1, 4):
            px(im, x + (y // 4 % 2) * 6, y, "red1")
    speckle(im, (0, 144, W, Y1), "grey1", 25, 3)
    glow(im, 0, 143, 140, 157, "grey1", 0.3, 4, 12)
    # exit door x282..312 top 88 bottom 150
    rect(im, 281, 87, 32, 64, "ink")
    rect(im, 282, 88, 30, 62, "grey1")
    rect(im, 284, 90, 26, 58, "grey1", "ink")
    dither_grad(im, (285, 91, 309, 147), "grey1", "ink2", "y", 2, 0.0, 0.9)
    rect(im, 286, 104, 22, 12, "ink", "ink2"); dither_grad(im, (287, 105, 307, 115), "blue0", "green0", "x", 4, 0.0, 0.8)
    rect(im, 286, 126, 22, 2, "ink")
    rect(im, 286, 120, 22, 2, "grey3", "ink")
    rect(im, 281, 150, 32, 2, "ink2")
    # exit light
    rect(im, 288, 74, 18, 11, "ink")
    rect(im, 289, 75, 16, 9, "green1", "ink")
    rect(im, 290, 76, 14, 7, "green2")
    text(im, 297, 75, "비상구", "green0", 9, align="center") if False else None
    # running man icon
    px(im, 294, 77, "white"); rect(im, 293, 78, 3, 2, "white"); px(im, 292, 80, "white"); px(im, 295, 80, "white")
    rect(im, 298, 77, 4, 2, "white"); rect(im, 298, 80, 4, 1, "white")
    hanging_bulb(im, 297, 80, 26, 0.45, "green1")
    glow(im, 282, 150, 314, 157, "green1", 0.2, 4, 6, up=True)
    # projector port
    rect(im, 295, 39, 11, 11, "ink")
    rect(im, 296, 40, 9, 9, "ink2")
    rect(im, 298, 42, 5, 5, "ink")
    dither_flat(im, (297, 41, 304, 48), "ink", "grey2", 0.18, 4)
    px(im, 300, 44, "yellow2"); px(im, 301, 44, "yellow2")
    glow(im, 288, 30, 312, 58, "orange3", 0.14, 4, 6)
    # wall sconce lights (very dim)
    for sx, sy in ((150, 62), (200, 62), (250, 62)):
        rect(im, sx, sy, 6, 3, "ink2", "ink"); px(im, sx + 2, sy + 1, "orange0"); px(im, sx + 3, sy + 1, "orange0")
    ovl(im, (0, Y0, W, 40), "ink", 0.35, 2)
    letterbox(im)
    return im


# ================================================================== BOOTH
def reel_big(im, cx, cy, r=13):
    ellipse(im, cx - r, cy - r, cx + r, cy + r, "grey3", "ink")
    dither_grad(im, (cx - r, cy - r, cx + r + 1, cy + r + 1), "grey3", "grey2", "d", 2, -0.2, 1.1,
                mk_mask([(cx + math.cos(a / 16 * 6.283) * (r - 1), cy + math.sin(a / 16 * 6.283) * (r - 1)) for a in range(16)], im.size))
    ellipse(im, cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3, "brown0", "ink")  # film wound
    dither_grad(im, (cx - r + 3, cy - r + 3, cx + r - 2, cy + r - 2), "brown0", "brown1", "d", 4, 0, 0.6,
                mk_mask([(cx + math.cos(a / 16 * 6.283) * (r - 4), cy + math.sin(a / 16 * 6.283) * (r - 4)) for a in range(16)], im.size))
    for a in range(5):
        ang = a / 5 * 6.283 + 0.5
        ex, ey = cx + math.cos(ang) * (r - 4), cy + math.sin(ang) * (r - 4)
        ellipse(im, int(ex) - 1, int(ey) - 1, int(ex) + 1, int(ey) + 1, "ink", None)
    ellipse(im, cx - 3, cy - 3, cx + 3, cy + 3, "grey2", "ink")
    px(im, cx, cy, "ink")
    px(im, cx - 2, cy - 2, "grey4")


def can(im, x, y, w=22, h=7):
    rect(im, x, y, w, h, "grey3", "ink")
    rect(im, x + 1, y + 1, w - 2, 1, "grey4")
    rect(im, x + 1, y + h - 3, w - 2, 2, "grey2")
    rect(im, x + 5, y + 2, 12, 2, "red2")
    rect(im, x - 1, y + 2, 1, h - 4, "grey2"); rect(im, x + w, y + 2, 1, h - 4, "grey2")


def build_booth():
    im = new(W, H, "ink")
    # walls
    dither_grad(im, (0, 34, W, 141), "brown0", "orange0", "y", 2, 0.0, 0.9)
    for x in range(0, W, 14):
        vline(im, x, 34, 140, "brown0")
    speckle(im, (0, 34, W, 140), "brown1", 80, 2)
    rect(im, 0, Y0, W, 12, "ink")
    dither_grad(im, (0, Y0, W, 34), "ink", "brown0", "y", 4, 0.0, 0.6)
    hline(im, 0, W - 1, 33, "ink"); hline(im, 0, W - 1, 34, "orange0")
    # pipes along ceiling
    rect(im, 0, 36, W, 3, "grey1"); hline(im, 0, W - 1, 36, "ink"); hline(im, 0, W - 1, 38, "ink"); hline(im, 0, W - 1, 37, "grey2")
    for x in (60, 120, 240, 300):
        rect(im, x, 36, 3, 3, "grey3", "ink")
    # floor planks
    dither_grad(im, (0, 141, W, Y1), "brown1", "brown0", "y", 4, 0.0, 0.9)
    hline(im, 0, W - 1, 140, "ink")
    for x in range(0, W, 28):
        vline(im, x, 141, Y1 - 1, "brown0"); vline(im, x + 14, 149, Y1 - 1, "brown0")
    hline(im, 0, W - 1, 148, "brown0")
    speckle(im, (0, 142, W, Y1), "brown2", 40, 4)
    # door/stair down left x6..36
    rect(im, 5, 87, 32, 64, "ink")
    rect(im, 6, 88, 30, 62, "ink")
    dither_grad(im, (6, 88, 36, 150), "ink", "blue0", "y", 2, 0.0, 0.8)
    for k in range(6):
        y = 150 - k * 6 - 6
        rect(im, 6, y, 30 - k * 4, 6, None)
        hline(im, 6, 36 - k * 4 - 1, y, "grey1")
        hline(im, 6, 36 - k * 4 - 1, y + 1, "grey2") if k < 3 else None
    rect(im, 6, 88, 30, 3, "ink")
    rect(im, 5, 87, 32, 2, "brown3"); rect(im, 36, 87, 2, 64, "orange1")  # frame
    vline(im, 4, 87, 150, "orange0")
    rect(im, 6, 150, 30, 2, "ink2")
    glow(im, 6, 120, 36, 150, "blue2", 0.08, 4, 5)
    # port window x32..50, y52..68 looking into dark hall
    rect(im, 31, 51, 20, 18, "ink")
    rect(im, 32, 52, 18, 16, "orange1")
    rect(im, 33, 53, 16, 14, "blue0")
    dither_grad(im, (33, 53, 49, 67), "blue0", "grey3", "y", 4, 0.0, 0.9)
    for x in range(36, 49, 4):
        rect(im, x, 60, 3, 3, "red0")   # tiny seat backs
    vline(im, 40, 53, 66, "orange0")
    line(im, [(34, 54), (38, 54)], "white")
    glow(im, 24, 68, 58, 90, "grey3", 0.10, 4, 6)
    # schedule posters on right wall (blank lines)
    for px0, w in ((256, 22), (282, 30)):
        rect(im, px0, 50, w, 32, "ink"); rect(im, px0 + 1, 51, w - 2, 30, "wall1")
        rect(im, px0 + 1, 51, w - 2, 5, "red2")
        for k in range(5):
            rect(im, px0 + 3, 59 + k * 4, w - 7, 1, "grey2")
        rect(im, px0 + w // 2 - 1, 49, 3, 2, "red3")
    # clock
    ellipse(im, 70, 48, 86, 64, "white", "ink")
    line(im, [(78, 56), (78, 51)], "ink"); line(im, [(78, 56), (82, 58)], "ink")
    # shelf with film boxes on right wall
    rect(im, 252, 100, 62, 3, "orange1", "ink")
    for k, x in enumerate(range(255, 310, 8)):
        rect(im, x, 90, 7, 10, ["grey3", "red2", "blue2", "grey4", "orange3", "red1", "grey3"][k % 7], "ink")
        px(im, x + 2, 92, "white")
    # workbench with splicer
    rect(im, 262, 120, 52, 4, "brown3", "ink"); rect(im, 264, 124, 4, 26, "brown1", "ink"); rect(im, 308, 124, 4, 26, "brown1", "ink")
    rect(im, 268, 112, 14, 8, "grey2", "ink"); rect(im, 270, 114, 10, 2, "grey4")
    rect(im, 292, 114, 10, 6, "orange3", "ink")
    # film cans
    for k in range(4):
        can(im, 216, 143 - k * 7 - 7 + 7, 22, 7)
    for k in range(3):
        can(im, 218, 121 - k * 7 - 0 if False else 143 - 28 - k * 7, 22, 7)
    for k in range(3):
        can(im, 232, 143 - k * 7, 22, 7) if False else None
    can(im, 100, 143, 22, 7); can(im, 100, 136, 22, 7)
    can(im, 214, 143, 22, 7) if False else None
    # stool
    rect(im, 82, 124, 14, 5, "red2", "ink"); hline(im, 83, 94, 125, "red3")
    for x in (84, 93):
        vline(im, x, 129, 149, "ink"); vline(im, x + 1, 129, 149, "grey2")
    hline(im, 84, 94, 140, "ink")
    # ---- projector x130..200
    rect(im, 140, 132, 50, 18, "grey1", "ink")            # pedestal
    dither_grad(im, (141, 133, 189, 149), "grey2", "grey1", "x", 2, 0.0, 0.9)
    rect(im, 136, 148, 58, 3, "ink2", "ink")
    rect(im, 130, 86, 70, 47, "grey2", "ink")             # body
    dither_grad(im, (131, 87, 199, 132), "grey3", "grey1", "d", 2, 0.0, 1.0)
    rect(im, 131, 87, 68, 1, "grey4")
    vline(im, 131, 88, 130, "grey4")
    for x in (150, 175):
        vline(im, x, 88, 131, "ink2")
    for y in (100, 118):
        hline(im, 132, 198, y, "ink2")
    # lens barrel (points left)
    rect(im, 114, 98, 17, 14, "grey3", "ink")
    rect(im, 108, 100, 7, 10, "grey1", "ink")
    rect(im, 106, 102, 3, 6, "yellow2", "ink")
    hline(im, 115, 129, 100, "grey4")
    glow(im, 76, 98, 108, 112, "yellow2", 0.45, 4, 5)
    # gate / controls
    for x in (140, 160, 182):
        ellipse(im, x, 106, x + 6, 112, "red2", "ink"); px(im, x + 2, 107, "red4")
    rect(im, 142, 90, 30, 6, "ink", "ink"); rect(im, 143, 91, 28, 4, "orange2")
    rect(im, 178, 120, 16, 8, "ink2", "ink")
    for k in range(4):
        px(im, 181 + k * 3, 123, "green2")
    # reel arms
    for ax, cx in ((142, 142), (184, 188)):
        rect(im, ax, 70, 4, 17, "grey1", "ink")
    reel_big(im, 144, 56, 14)
    reel_big(im, 189, 56, 14)
    # film path
    line(im, [(144, 70), (146, 88)], "brown0"); line(im, [(189, 70), (186, 88)], "brown0")
    # chimney
    rect(im, 156, 78, 14, 9, "grey1", "ink"); rect(im, 158, 72, 10, 7, "grey2", "ink")
    # hanging bulb
    vline(im, 110, 39, 62, "ink"); rect(im, 107, 62, 7, 4, "grey2", "ink")
    ellipse(im, 106, 65, 114, 73, "yellow2", "ink"); px(im, 108, 67, "white")
    hanging_bulb(im, 110, 68, 44, 0.6, "orange3")
    hanging_bulb(im, 110, 68, 22, 0.55, "orange4")
    # dither vignette
    ovl(im, (0, Y0, 28, Y1), "ink", 0.3, 2); ovl(im, (292, Y0, W, Y1), "ink", 0.25, 2)
    letterbox(im)
    return im


# ================================================================== FILMS
def grain(im, seed, n, cols=("grey1", "grey2", "grey4"), box=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box or (0, 0, im.width, im.height)
    for _ in range(n):
        px(im, rnd.randint(x0, x1 - 1), rnd.randint(y0, y1 - 1), rnd.choice(cols))


def film_frame(k):
    im = new(116, 86, "ink")
    dither_grad(im, (0, 0, 116, 56), "ink2", "grey1", "y", 4, 0.0, 1.0)
    # moon + halo
    mx, my = 82, 20
    for y in range(86):
        for x in range(116):
            d = ((x - mx) ** 2 + (y - my) ** 2) ** 0.5 / 28
            if d < 1 and (1 - d) * 0.8 > _thr(x, y, 4) and y < 58:
                im.putpixel((x, y), col("grey2"))
    ellipse(im, mx - 9, my - 9, mx + 9, my + 9, "white", "grey4")
    for p in ((-4, -2), (2, 3), (4, -4), (-2, 5)):
        px(im, mx + p[0], my + p[1], "grey4")
    # trees
    for tx, th in ((10, 30), (24, 22), (100, 26)):
        rect(im, tx, 56 - th, 3, th, "ink")
        ellipse(im, tx - 9, 56 - th - 10, tx + 11, 56 - th + 12, "ink", None)
    # ground
    rect(im, 0, 56, 116, 30, "ink")
    dither_grad(im, (0, 56, 116, 66), "grey1", "ink", "y", 4, 0.0, 1.0)
    # lamp post
    rect(im, 60, 24, 2, 34, "ink"); rect(im, 57, 21, 8, 4, "ink")
    px(im, 59, 25, "grey4") ; px(im, 60, 25, "white")
    # bench
    sh = 1 if k else 0
    rect(im, 34, 54, 40, 3, "ink2"); hline(im, 34, 73, 54, "grey2")
    rect(im, 36, 57, 3, 8, "ink2"); rect(im, 70, 57, 3, 8, "ink2")
    rect(im, 34, 44, 40, 2, "ink2"); hline(im, 34, 73, 44, "grey2")
    # figure A (tall) left
    ax = 43
    ellipse(im, ax, 32 + sh, ax + 8, 41 + sh, "ink", "ink")
    rect(im, ax - 2, 41 + sh, 12, 14 - sh, "ink")
    poly(im, [(ax - 2, 41 + sh), (ax + 10, 41 + sh), (ax + 8, 38 + sh), (ax, 38 + sh)], "ink")
    hline(im, ax + 1, ax + 6, 32 + sh, "grey1")
    # figure B right, leans towards A in frame 1
    bx = 58 - sh
    ellipse(im, bx, 35, bx + 7, 43, "ink", "ink")
    rect(im, bx - 1, 43, 10, 12, "ink")
    hline(im, bx + 1, bx + 5, 35, "grey1")
    # arm / shared cigarette glow
    px(im, ax + 11, 45, "grey4") if k else None
    # boundary shadow to legs
    rect(im, 40, 58, 36, 4, "ink")
    # film border dither (vignette)
    for y in range(86):
        for x in range(116):
            e = min(x, 115 - x, (y) * 1.3, (85 - y) * 1.3)
            if e < 12 and (1 - e / 12) * 0.9 > _thr(x, y, 4):
                im.putpixel((x, y), col("ink"))
    grain(im, 10 + k, 160, box=(0, 0, 116, 86))
    # scratch
    sx = 20 + k * 47
    for y in range(0, 86, 2):
        px(im, sx, y, "grey3")
    # frame jitter band
    if k:
        for x in range(116):
            if x % 2 == 0: px(im, x, 0, "grey1")
    return im


def cctv_frame(k):
    im = new(116, 86, "grey2")
    # floor tiles
    for y in range(0, 86, 10):
        for x in range(0, 116, 10):
            c = "grey2" if ((x // 10 + y // 10) % 2) else "grey1"
            rect(im, x, y, 10, 10, c)
    dither_flat(im, (0, 0, 116, 86), "grey2", "grey3", 0.15, 4)
    # shelves (top-down) upper left: rows
    for i in range(3):
        rect(im, 6, 10 + i * 9, 40, 5, "grey3", "ink")
        for x in range(8, 44, 5):
            px(im, x, 12 + i * 9, "grey1"); px(im, x + 1, 12 + i * 9, "grey4")
    # fridge strip right
    rect(im, 98, 4, 14, 44, "grey4", "ink")
    for y in range(8, 46, 9):
        hline(im, 100, 110, y, "grey2")
    # counter (top-down)
    rect(im, 22, 54, 72, 12, "grey4", "ink")
    rect(im, 22, 54, 72, 2, "white")
    rect(im, 70, 56, 12, 8, "ink2", "ink"); rect(im, 72, 58, 8, 3, "grey3")   # register
    rect(im, 30, 57, 6, 5, "grey2", "ink")                                    # items
    rect(im, 40, 58, 4, 4, "grey3", "ink")
    # figure behind counter (tiny, from above)
    fx, fy = 54 + (1 if k else 0), 70 + k
    ellipse(im, fx - 7, fy - 1, fx + 7, fy + 8, "grey3", "ink")           # shoulders
    ellipse(im, fx - 3, fy + 1, fx + 3, fy + 7, "ink2", "ink")        # head w/ hair
    px(im, fx - 1, fy + 3, "grey1")
    # shadow dither
    ovl(im, (0, 0, 116, 86), "ink", 0.28, 2)
    # vignette
    for y in range(86):
        for x in range(116):
            e = min(x, 115 - x, y * 1.2, (85 - y) * 1.2)
            if e < 14 and (1 - e / 14) * 0.9 > _thr(x, y, 4):
                im.putpixel((x, y), col("ink"))
    # scanline band
    sy = 14 + k * 38
    for dy in range(4):
        for x in range(116):
            if (x + dy) % (2 if dy < 2 else 3) == 0:
                px(im, x, sy + dy, "grey4")
    # horizontal noise lines
    rnd = random.Random(40 + k)
    for _ in range(5):
        y = rnd.randint(0, 85); x = rnd.randint(0, 80)
        hline(im, x, x + rnd.randint(10, 30), y, "grey3")
    grain(im, 30 + k, 150, cols=("grey1", "grey3", "ink2", "grey4"))
    # HUD: REC + time
    ellipse(im, 6, 5, 11, 10, "red2", None) if True else None
    text(im, 14, 2, "REC", "white", 7, shadow="ink")
    text(im, 112, 74, "02:1%d:0%d" % (3, 7 + k * 2), "white", 7, shadow="ink", align="right")
    text(im, 5, 74, "CAM 02", "white", 7, shadow="ink")
    return im


def off_frame():
    im = new(116, 86, "ink2")
    dither_flat(im, (0, 0, 116, 86), "ink2", "grey1", 0.12, 4)
    for y in range(0, 86, 2):
        for x in range(0, 116, 2):
            pass
    grain(im, 77, 20, cols=("grey1",))
    return im


# ================================================================== USHER
def usher_frame(dx=0, bob=0, lleg=(0, 0), rleg=(0, 0), arm="hold", head=(0, 0), tilt=False, hurt=False):
    im = new(32, 48)
    b = bob
    # far leg (right) / near leg (left): (x offset, lift)
    def leg(x0, off, lift, shade):
        x = x0 + off
        top = 36 + b
        bot = 45 - lift
        rect(im, x, top, 4, bot - top + 1, "ink2")
        vline(im, x, top, bot, "grey1") if shade else None
        rect(im, x - 2, bot - 1, 6, 2, "ink")   # shoe pointing left
        px(im, x - 2, bot - 1, "grey1")
    leg(18 + dx, rleg[0], rleg[1], False)
    leg(12 + dx, lleg[0], lleg[1], True)
    # far arm (right)
    if arm in ("hold", "lunge"):
        rect(im, 22 + dx, 24 + b, 3, 10, "red0")
        rect(im, 22 + dx, 33 + b, 3, 3, "grey4")
    elif arm == "up":
        rect(im, 23 + dx, 16 + b, 3, 10, "red0"); rect(im, 23 + dx, 14 + b, 3, 3, "grey4")
    # torso
    tx = 9 + dx
    rect(im, tx, 22 + b, 14, 16, "red1")
    dither_grad(im, (tx + 7, 23 + b, tx + 14, 38 + b), "red1", "red0", "x", 2, 0.0, 1.0)
    vline(im, tx, 23 + b, 36 + b, "red2")
    hline(im, tx, tx + 13, 37 + b, "red0")
    hline(im, tx, tx + 13, 22 + b, "orange3")           # collar trim
    hline(im, tx + 1, tx + 12, 23 + b, "red2")
    rect(im, tx + 3, 22 + b, 3, 3, "ink2")   # bow tie hint
    for yy in (26, 30, 34):
        px(im, tx + 3, yy + b, "yellow"); px(im, tx + 3, yy + b + 1, "orange2")
    hline(im, tx + 1, tx + 12, 35 + b, "orange0") if False else None
    # near arm
    if arm == "hold":
        rect(im, tx - 3, 23 + b, 4, 10, "red1"); vline(im, tx - 3, 24 + b, 31 + b, "red2")
        rect(im, tx - 3, 33 + b, 4, 3, "grey4")
        # flashlight pointing left
        rect(im, tx - 9, 32 + b, 7, 4, "grey2", "ink")
        rect(im, tx - 9, 32 + b, 2, 4, "yellow2")
        px(im, tx - 7, 33 + b, "grey4")
    elif arm == "lunge":
        rect(im, 1, 24 + b, tx - 1, 4, "red1")
        hline(im, 1, tx - 1, 24 + b, "red2")
        rect(im, 0 + 1, 23 + b, 4, 6, "grey4")
        hline(im, 1, tx, 27 + b, "red0")
    elif arm == "up":
        rect(im, tx - 3, 14 + b, 4, 10, "red1"); rect(im, tx - 3, 12 + b, 4, 3, "grey4")
        rect(im, tx - 9, 11 + b, 7, 4, "grey2", "ink"); rect(im, tx - 9, 11 + b, 2, 4, "yellow2")
    # head
    hx, hy = 8 + dx + head[0], 6 + b + head[1]
    ellipse(im, hx, hy, hx + 15, hy + 15, "pale2", "ink")
    dither_grad(im, (hx + 1, hy + 1, hx + 15, hy + 15), "pale2", "pale1", "d", 2, -0.3, 1.1,
                mk_mask([(hx + 4 + 8 * math.cos(a / 16 * 6.283) + 3.5, hy + 8 + 7 * math.sin(a / 16 * 6.283)) for a in range(16)], im.size))
    px(im, hx + 3, hy + 4, "white") ; px(im, hx + 4, hy + 3, "white")
    # cap (pillbox)
    cx = hx + 1
    cy = hy - 5
    if tilt:
        poly(im, [(cx + 1, cy + 6), (cx + 12, cy + 1), (cx + 15, cy + 5), (cx + 3, cy + 10)], "red1", "ink")
        line(im, [(cx + 2, cy + 8), (cx + 14, cy + 4)], "orange3")
    else:
        rect(im, cx, cy, 14, 7, "red1", "ink")
        hline(im, cx + 1, cx + 12, cy + 1, "red2")
        rect(im, cx, cy + 4, 14, 2, "orange3"); hline(im, cx + 1, cx + 12, cy + 5, "orange2")
        px(im, cx + 6, cy + 4, "yellow")
        vline(im, cx + 12, cy + 1, cy + 3, "red0")
    return outline(im)


def usher_frames():
    fr, nm = [], []
    def add(n, f):
        fr.append(f); nm.append(n)
    add("idle_0", usher_frame())
    add("idle_1", usher_frame(bob=1, head=(0, 0)))
    add("walk_0", usher_frame(lleg=(-2, 0), rleg=(1, 2), bob=0))
    add("walk_1", usher_frame(lleg=(0, 0), rleg=(0, 0), bob=1))
    add("walk_2", usher_frame(lleg=(2, 2), rleg=(-1, 0), bob=0))
    add("walk_3", usher_frame(lleg=(0, 0), rleg=(0, 0), bob=1))
    add("lunge_0", usher_frame(dx=3, bob=1, arm="lunge", head=(-1, 1), lleg=(-3, 0), rleg=(3, 0)))
    add("hurt_0", usher_frame(dx=2, arm="up", head=(2, -1), tilt=True, bob=0, lleg=(1, 0), rleg=(2, 0)))
    # dark silhouette
    base = fr[0].copy()
    a = base.split()[3].point(lambda v: 255 if v else 0)
    sil = new(32, 48, "ink")
    sil.putalpha(a)
    px(sil, 12, 12, "pale1"); px(sil, 13, 12, "pale1")
    px(sil, 17, 12, "pale1"); px(sil, 18, 12, "pale1")
    add("dark_0", sil)
    return fr, nm


# ================================================================== BEAM / REEL
def build_beam():
    w, h = 200, 70
    im = new(w, h)
    ay0, ay1 = 30, 38              # aperture at the right edge
    for x in range(w):
        t = (w - 1 - x) / (w - 1)  # 0 at apex, 1 at left edge
        top = ay0 - t * ay0
        bot = ay1 + t * (h - 1 - ay1)
        for y in range(h):
            if y < top or y > bot:
                continue
            f = (y - top) / max(1, bot - top)           # 0..1 across the cone
            edge = 1 - abs(f - 0.5) * 2                  # 1 in the middle
            dens = (0.50 - 0.28 * t) * (0.35 + 0.65 * edge ** 0.6)
            # faint dusty rays
            dens *= 0.8 + 0.4 * math.sin(f * 17 + 1.3)
            if y in (int(top), int(bot)):
                dens = max(dens, 0.30) * 0.9
            if dens > _thr(x, y, 4):
                c = "white" if (dens - 0.25 > _thr(x + 1, y + 2, 4) and edge > 0.5) else "yellow2"
                px(im, x, y, c)
    # remove isolated stray pixels at far left? keep ordered dither as is
    return im


def build_reel():
    im = new(14, 14)
    ellipse(im, 0, 0, 13, 13, "grey3", "ink")
    dither_grad(im, (1, 1, 13, 13), "grey3", "grey2", "d", 2, 0.0, 1.0,
                mk_mask([(7 + 5.5 * math.cos(a / 16 * 6.283) , 7 + 5.5 * math.sin(a / 16 * 6.283)) for a in range(16)], im.size))
    for ang in range(5):
        a = ang / 5 * 6.283 - 1.2
        ex, ey = 7 + math.cos(a) * 4, 7 + math.sin(a) * 4
        rect(im, int(round(ex)) - 1, int(round(ey)) - 1, 2, 2, "ink")
    rect(im, 6, 6, 2, 2, "ink")
    px(im, 6, 6, "grey4")
    px(im, 3, 2, "white"); px(im, 2, 3, "white"); px(im, 4, 1, "grey4")
    # film edge ring
    for a in range(24):
        ang = a / 24 * 6.283
        x, y = int(round(6.5 + 5.6 * math.cos(ang))), int(round(6.5 + 5.6 * math.sin(ang)))
        if a % 2 == 0 and im.getpixel((x, y))[:3] == PAL["grey3"] or im.getpixel((x, y))[:3] == PAL["grey2"]:
            px(im, x, y, "brown1")
    return im


def main():
    save(build_lobby(), "bg/cinema_lobby.png")
    save(build_hall(), "bg/cinema_hall.png")
    save(build_booth(), "bg/cinema_booth.png")
    frames = [film_frame(0), film_frame(1), cctv_frame(0), cctv_frame(1), off_frame()]
    sheet(frames, "props/screen_film", ["film_0", "film_1", "cctv_0", "cctv_1", "off_0"], cols=5)
    uf, un = usher_frames()
    sheet(uf, "props/usher", un, cols=9)
    save(build_beam(), "props/beam.png")
    save(build_reel(), "props/reel.png", scale=8)
    contact(["bg/cinema_lobby.png", "bg/cinema_hall.png", "bg/cinema_booth.png", "props/screen_film.png",
             "props/usher.png", "props/beam.png", "props/reel.png"], "_contact/cinema.png", cols=2, scale=2)
    for p in ("bg/cinema_lobby.png", "bg/cinema_hall.png", "bg/cinema_booth.png", "props/screen_film.png",
              "props/usher.png", "props/beam.png", "props/reel.png"):
        im = Image.open(os.path.join(ASSETS, p)).convert("RGBA")
        assert not off_palette(im), p
        print(p, im.size)


if __name__ == "__main__":
    main()

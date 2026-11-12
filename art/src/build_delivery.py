"""Act 2 (night delivery) assets for ONE MORE SHIFT.

Run:  python3 src/build_delivery.py
Writes assets/bg/{delivery_hub,apt_hall,stairwell}.png
       assets/props/{moped,moped_b,delivery_bag,apt_door_open,elevator_open}.png
       previews/_contact/delivery.png
All scenes are flat side views; the walkable floor band is y 140..154.
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from pxkit import *
from pxkit import _thr
from PIL import Image, ImageDraw

Y0, Y1 = 22, 157
FLOOR_TOP = 138


# ------------------------------------------------------------------ helpers
def obox(img, x, y, w, h, fill, hi=None, sh=None, ol="ink"):
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


def glow(img, x0, y0, x1, y1, c, s=0.6, m=4, fade_x=8, up=False):
    """Dithered light spill: c written over pixels, densest at the top (or bottom if up)."""
    cc = col(c)
    h = max(1, y1 - y0 - 1)
    for y in range(max(0, y0), min(img.height, y1)):
        f = (y - y0) / h
        f = f if up else 1 - f
        for x in range(max(0, x0), min(img.width, x1)):
            g = min(1.0, (x - x0 + 1) / fade_x, (x1 - x) / fade_x)
            if f * g * s > _thr(x, y, m):
                img.putpixel((x, y), cc)


def ovl(img, box, c, level, m=2, only=None):
    """Overlay colour c at constant dither density; only= palette name to restrict to."""
    cc = col(c)
    on = col(only) if only else None
    x0, y0, x1, y1 = box
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            if on and img.getpixel((x, y)) != on:
                continue
            if level > _thr(x, y, m):
                img.putpixel((x, y), cc)


def speckle(img, box, c, n, seed, only=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    on = col(only) if only else None
    for _ in range(n):
        x, y = rnd.randint(x0, x1 - 1), rnd.randint(y0, y1 - 1)
        if on is None or img.getpixel((x, y)) == on:
            px(img, x, y, c)


def streaks(img, box, c, n, seed, maxlen=14, level=0.6, only=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    on = col(only) if only else None
    for _ in range(n):
        x = rnd.randint(x0, x1 - 2)
        y = rnd.randint(y0, y1 - 4)
        w = rnd.choice([1, 2, 2, 3])
        l = rnd.randint(4, maxlen)
        for yy in range(y, min(y1, y + l)):
            f = 1 - (yy - y) / l
            for xx in range(x, min(x1, x + w)):
                if (on is None or img.getpixel((xx, yy)) == on) and f * level * 1.6 > _thr(xx, yy, 4):
                    img.putpixel((xx, yy), col(c))


def mk_mask(pts, size=(W, H)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(0, min(xs) - 1), max(0, min(ys) - 1), min(W, max(xs) + 2), min(H, max(ys) + 2))


def dpoly(img, pts, c1, c2, t0, t1=None, axis="y", m=4, out=None):
    t1 = t0 if t1 is None else t1
    dither_grad(img, bbox(pts), c1, c2, axis, m, t0, t1, mk_mask(pts, img.size))
    if out:
        poly(img, pts, None, out)


def tube(img, x0, x1, y, on=True, spill=True):
    """Ceiling fluorescent fixture (housing + tube) with cold dithered spill."""
    obox(img, x0, y, x1 - x0 + 1, 6, "grey2", "grey3")
    rect(img, x0 + 2, y + 2, x1 - x0 - 3, 2, "white" if on else "grey3")
    if on and spill:
        glow(img, x0 - 6, y + 7, x1 + 6, y + 44, "white", 0.55, 4, 14)


def floor_band(img, y0, y1, a, b, joint, hi, tw=20, seed=3, x0=0, x1=W):
    """Side-view floor strip: dither from a (back) to b (front), tile joints, speckle."""
    dither_grad(img, (x0, y0, x1, y1), a, b, "y", 4, 0.0, 1.0)
    # back edge shadow under the wall
    hline(img, x0, x1 - 1, y0, "ink")
    for x in range(x0, x1):
        if (x + y0) % 2 == 0:
            px(img, x, y0 + 1, joint)
    ym = y0 + (y1 - y0) // 2 + 1
    hline(img, x0, x1 - 1, ym, joint)
    for k, (ya, yb) in enumerate(((y0 + 1, ym), (ym, y1 - 1))):
        off = (tw // 2) * k
        for x in range(x0 + off, x1, tw):
            vline(img, x, ya, yb, joint)
            px(img, x + 1, ya + 1, hi)
    hline(img, x0, x1 - 1, y1 - 1, joint)
    speckle(img, (x0, y0 + 2, x1, y1 - 1), joint, (x1 - x0) // 5, seed)
    speckle(img, (x0, y0 + 2, x1, y1 - 1), hi, (x1 - x0) // 8, seed + 1)


def clock_face(img, cx, cy, r, h=3, m=4):
    ellipse(img, cx - r, cy - r, cx + r, cy + r, "grey1", "ink")
    ellipse(img, cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, "white", "grey3")
    for k in range(12):
        a = k * math.pi / 6
        px(img, round(cx + math.sin(a) * (r - 2)), round(cy - math.cos(a) * (r - 2)), "ink")
    # hands: 3:10-ish, mundane
    line(img, [(cx, cy), (cx + round(math.sin(math.radians(95)) * (r - 3)), cy - round(math.cos(math.radians(95)) * (r - 3)))], "ink")
    line(img, [(cx, cy), (cx + round(math.sin(math.radians(300)) * (r - 5)), cy - round(math.cos(math.radians(300)) * (r - 5)))], "ink")
    px(img, cx, cy, "red2")


def helmet(img, x, y, c="orange2", cs="orange1", ch="orange3"):
    """14x11 hanging helmet, dome + visor, hook at top."""
    ellipse(img, x, y, x + 13, y + 12, c, "ink")
    rect(img, x + 1, y + 7, 12, 4, cs)
    rect(img, x + 4, y + 5, 9, 4, "blue0", "ink")
    hline(img, x + 5, x + 11, y + 6, "blue1")
    px(img, x + 3, y + 2, ch); px(img, x + 4, y + 1, ch); px(img, x + 5, y + 1, ch)
    hline(img, x + 1, x + 12, y + 11, "ink")


def bag_prop(img, x, y, big=False):
    """small insulated bag for the hub cubbies (14x13)."""
    w, h = (14, 13)
    rect(img, x + 1, y + 4, w - 2, h - 4, "orange2", "ink")
    rect(img, x + 2, y + 5, w - 4, 2, "orange3")
    rect(img, x + 2, y + 9, w - 4, 2, "orange1")
    hline(img, x + 1, x + w - 2, y + 4, "ink")
    line(img, [(x + 4, y + 4), (x + 4, y + 1), (x + w - 5, y + 1), (x + w - 5, y + 4)], "ink")
    px(img, x + 6, y + 8, "yellow"); px(img, x + 7, y + 8, "yellow")


def wire_cage(img, cx, cy, r=5):
    ellipse(img, cx - r, cy - r, cx + r, cy + r, None, "grey1")
    vline(img, cx, cy - r, cy + r, "grey1")
    hline(img, cx - r, cx + r, cy, "grey1")


# ======================================================================
# 1. DELIVERY HUB
# ======================================================================
def helmet_hook_row(img, x0, x1, y):
    rect(img, x0, y, x1 - x0 + 1, 3, "brown1", "ink")
    hline(img, x0 + 1, x1 - 1, y + 1, "brown2")
    for hx in range(x0 + 6, x1 - 3, 14):
        line(img, [(hx, y + 3), (hx, y + 6), (hx + 2, y + 6)], "grey3")
        px(img, hx + 2, y + 5, "grey3")


def cubby_unit(img):
    ux, uy, uw, uh = 14, 50, 99, 78
    # header plate
    obox(img, ux + 14, 37, 70, 12, "blue1", "blue2")
    text(img, ux + 14 + 35, 38, "픽업 선반 A", "white", 9, align="center")
    line(img, [(ux + 18, 49), (ux + 18, 50)], "ink")
    line(img, [(ux + 79, 49), (ux + 79, 50)], "ink")
    # body
    rect(img, ux, uy, uw, uh, "grey3", "ink")
    rect(img, ux + 1, uy + 1, uw - 2, 1, "white")
    vline(img, ux + 1, uy + 1, uy + uh - 2, "grey4")
    vline(img, ux + uw - 2, uy + 2, uy + uh - 2, "grey2")
    cw, ch, gp = 22, 23, 3
    nbag = {1: "o", 4: "o", 6: "w", 9: "o", 10: "b"}
    n = 0
    for r in range(3):
        for c in range(4):
            cx = ux + 2 + c * (cw + gp)
            cy = uy + 2 + r * (ch + gp) + (1 if r else 0)
            rect(img, cx, cy, cw, ch, "ink2", "ink")
            # inner shadow top + left (light from top-left means shade under the lip)
            hline(img, cx + 1, cx + cw - 2, cy + 1, "ink")
            hline(img, cx + 1, cx + cw - 2, cy + 2, "grey1")
            vline(img, cx + 1, cy + 3, cy + ch - 2, "grey1")
            dither_grad(img, (cx + 2, cy + 3, cx + cw - 1, cy + ch - 1), "ink2", "grey1", "y", 2, 0.0, 0.5)
            hline(img, cx + 1, cx + cw - 2, cy + ch - 2, "grey2")
            n += 1
            # number plate
            pcol = "yellow" if n in (2, 7, 11) else "white"
            rect(img, cx + 2, cy + 3, 12, 9, pcol, "ink")
            text(img, cx + 8, cy + 3, str(n), "ink", 7, align="center")
            kind = nbag.get(n - 1)
            if kind == "o":
                bag_prop(img, cx + 6, cy + ch - 15)
            elif kind == "w":
                rect(img, cx + 3, cy + ch - 12, 16, 10, "white", "ink")
                hline(img, cx + 4, cx + 17, cy + ch - 10, "grey3")
                vline(img, cx + 11, cy + ch - 12, cy + ch - 3, "grey3")
                rect(img, cx + 12, cy + ch - 9, 5, 3, "red2")
            elif kind == "b":
                rect(img, cx + 3, cy + ch - 13, 16, 11, "blue2", "ink")
                rect(img, cx + 4, cy + ch - 12, 14, 2, "blue3")
                rect(img, cx + 8, cy + ch - 14, 8, 2, "blue1", "ink")
    # little card slots on frame sides + label strip bottom
    for r in range(3):
        for c in range(1, 4):
            vline(img, ux + 2 + c * (cw + gp) - 2, uy + 4 + r * (ch + gp), uy + 6 + r * (ch + gp), "grey2")
    # legs and kickplate
    rect(img, ux + 2, uy + uh, 6, 8, "grey2", "ink")
    rect(img, ux + uw - 8, uy + uh, 6, 8, "grey2", "ink")
    hline(img, ux + 3, ux + 6, uy + uh + 1, "grey3")
    # screws
    for sx in (ux + 3, ux + uw - 4):
        px(img, sx, uy + 1, "grey2")
    # shadow on floor
    ovl(img, (ux + 2, FLOOR_TOP + 1, ux + uw + 6, FLOOR_TOP + 7), "ink", 0.45, 2)


def hub_counter(img):
    # warm spill on wall behind
    dither_radial(img, 169, 96, 48, "wall1", None, 4, box=(124, 38, 214, 118))
    # hanging sign
    for chx in (140, 198):
        vline(img, chx, 34, 55, "grey1")
        for yy in range(36, 55, 3):
            px(img, chx - 1, yy, "grey2")
    obox(img, 132, 55, 75, 24, "blue1", "blue2", "blue0")
    rect(img, 134, 57, 71, 20, "blue0", "ink")
    dither_grad(img, (135, 58, 204, 76), "blue1", "blue0", "y", 4, 0.0, 0.8)
    text(img, 169, 61, "새벽배송 허브", "yellow", 9, edge="ink", shadow="ink", align="center")
    hline(img, 136, 202, 74, "orange2")
    for sx in range(140, 202, 9):
        px(img, sx, 75, "orange3")
    # counter body (waist-high, top at y118)
    rect(img, 132, 118, 75, 24, "brown2", "ink")
    rect(img, 133, 119, 73, 4, "white", None)
    hline(img, 133, 205, 119, "white")
    hline(img, 133, 205, 122, "grey3")
    hline(img, 132, 206, 123, "ink")
    # wood front, dither shading
    dither_grad(img, (133, 124, 206, 141), "brown2", "brown1", "y", 4, 0.0, 0.7)
    for vx in range(144, 206, 12):
        vline(img, vx, 124, 138, "brown1")
        px(img, vx - 1, 125, "brown3")
    rect(img, 133, 138, 73, 3, "ink2")
    hline(img, 133, 205, 138, "grey1")
    # cash drawer / slot detail and a taped receipt
    rect(img, 150, 128, 20, 6, "brown1", "ink")
    hline(img, 151, 168, 129, "brown2")
    rect(img, 158, 131, 4, 2, "orange3")
    rect(img, 186, 127, 8, 10, "white", "ink")
    hline(img, 188, 192, 130, "grey3"); hline(img, 188, 192, 132, "grey3"); hline(img, 188, 191, 134, "grey3")
    # --- order printer
    rect(img, 139, 108, 20, 10, "grey4", "ink")
    hline(img, 140, 157, 109, "white")
    rect(img, 141, 111, 12, 2, "ink2")
    rect(img, 155, 111, 2, 2, "red3")
    rect(img, 144, 104, 10, 4, "white", "ink")             # paper roll
    hline(img, 145, 152, 106, "grey3")
    # paper strip hanging
    rect(img, 143, 118, 9, 6, "white", "ink")
    hline(img, 145, 150, 120, "grey3"); hline(img, 145, 148, 122, "grey3")
    hline(img, 143, 151, 123, "grey2")
    # --- monitor
    rect(img, 175, 114, 10, 4, "grey2", "ink")             # foot
    rect(img, 178, 111, 4, 4, "grey1", "ink")              # neck
    rect(img, 164, 94, 32, 19, "grey4", "ink")
    hline(img, 165, 193, 95, "white")
    rect(img, 166, 96, 28, 14, "blue0", "ink")
    rect(img, 167, 97, 26, 3, "blue1")                     # header bar
    for ry in (102, 105, 108):                             # blank rows
        hline(img, 168, 191, ry, "blue1")
    vline(img, 177, 100, 109, "blue1")
    px(img, 169, 98, "green2"); px(img, 171, 98, "grey3")
    px(img, 192, 112, "green2")
    # light spill from the screen on the counter
    glow(img, 164, 114, 197, 119, "blue3", 0.3, 4, 4)
    # --- small stuff on counter
    rect(img, 198, 112, 8, 6, "yellow", "ink")             # service bell base
    rect(img, 200, 110, 4, 2, "grey3", "ink")
    px(img, 202, 109, "ink")
    rect(img, 160, 112, 3, 6, "white", "ink")              # pen cup
    px(img, 161, 110, "red2"); px(img, 162, 109, "blue2")
    rect(img, 196, 104, 1, 1, "ink")
    # sticky notes on monitor
    rect(img, 196, 96, 5, 5, "yellow2", "ink")
    rect(img, 198, 102, 4, 4, "red4", "ink")
    # shadow under counter
    ovl(img, (130, FLOOR_TOP + 4, 211, FLOOR_TOP + 9), "ink", 0.5, 2)
    ovl(img, (130, FLOOR_TOP + 4, 211, FLOOR_TOP + 7), "ink", 0.5, 4)


def glass_door(img):
    x, y, w, h = 268, 62, 43, 89            # x268..310, bottom at y150
    # exterior light spill on the floor in front of door (cold)
    # frame
    rect(img, x - 1, y - 1, w + 2, h + 2, "grey2", "ink")
    rect(img, x, y, w, h, "grey3")
    hline(img, x, x + w - 1, y, "white")
    vline(img, x, y, y + h - 1, "grey4")
    vline(img, x + w - 1, y + 1, y + h - 1, "grey2")
    # glass
    gx, gy, gw, gh = x + 4, y + 4, w - 8, 76
    rect(img, gx - 1, gy - 1, gw + 2, gh + 2, "ink")
    # night street seen through the glass
    dither_ramp(img, (gx, gy, gx + gw, gy + gh), ["blue0", "blue1", "blue0"], "y", 4)
    # distant buildings
    for bx, bw, bh in ((gx, 9, 30), (gx + 9, 8, 22), (gx + 17, 10, 34), (gx + 27, 9, 26)):
        rect(img, bx, gy + gh - bh - 12, bw, bh, "blue0")
        for wy in range(gy + gh - bh - 9, gy + gh - 16, 5):
            for wx in range(bx + 2, bx + bw - 2, 3):
                if (wx + wy) % 4 == 0:
                    px(img, wx, wy, "orange3" if (wx * 3 + wy) % 7 else "yellow2")
    # street lamp + glow
    vline(img, gx + 24, gy + 10, gy + gh - 8, "ink")
    hline(img, gx + 20, gx + 24, gy + 10, "ink")
    dither_radial(img, gx + 20, gy + 12, 13, "orange3", None, 4)
    px(img, gx + 20, gy + 12, "yellow2")
    # kerb + road
    rect(img, gx, gy + gh - 12, gw, 12, "ink2")
    hline(img, gx, gx + gw - 1, gy + gh - 12, "grey1")
    dither_grad(img, (gx, gy + gh - 11, gx + gw, gy + gh), "ink2", "blue0", "y", 2, 0.0, 0.6)
    for rx in range(gx + 3, gx + gw - 4, 10):
        hline(img, rx, rx + 4, gy + gh - 4, "yellow")
    # reflection streaks
    for k, (sx, sl) in enumerate(((gx + 5, 22), (gx + 9, 10))):
        for t in range(sl):
            if t % 2 == 0 or k:
                px(img, sx + t // 2 + 0, gy + 2 + t, "blue3")
    ovl(img, (gx, gy, gx + gw, gy + gh), "blue2", 0.12, 4)
    # reflected tube light of the hub (warm) on glass
    px(img, gx + 30, gy + 18, "yellow2")
    # bars: push bar on the left side
    rect(img, x + 6, y + 40, 2, 20, "grey4", "ink")
    rect(img, x + 3, y + 44, 3, 2, "grey2", "ink")
    rect(img, x + 3, y + 56, 3, 2, "grey2", "ink")
    # kick plate
    rect(img, x + 3, y + 84, w - 6, 5, "grey2", "ink")
    hline(img, x + 4, x + w - 5, y + 85, "grey3")
    # sticker "24" on the glass
    ellipse(img, x + 30, y + 52, x + 39, y + 61, "yellow", "ink")
    text(img, x + 34, y + 53, "24", "ink", 7, align="center")
    # lower pane edge in front of kick, hinges
    for hy in (y + 12, y + 70):
        rect(img, x + w - 1, hy, 2, 4, "grey1", "ink")
    # open-hours sign hanging
    rect(img, x + 2, y + 18, 9, 4, "red2", "ink")
    # transom light above the door
    glow(img, x - 14, y - 3, x + w + 6, y + 30, "green2", 0.18, 4, 6)
    rect(img, x - 1, y - 18, w + 2, 16, "green0", "ink")
    rect(img, x + 1, y - 16, w - 2, 12, "green1", "ink")
    text(img, x + w // 2, y - 16, "출구", "white", 9, align="center")
    # floor mat
    rect(img, x - 2, 150, w + 4, 5, "grey1", "ink")
    for mx in range(x, x + w, 4):
        px(img, mx, 152, "grey2")


def build_hub():
    im = new(W, H, "ink")
    # wall: cold fluorescent
    dither_ramp(im, (0, 34, W, FLOOR_TOP), ["grey4", "wall3", "wall3", "grey3"], "y", 4)
    # wall panel seams
    for sx in range(6, W, 38):
        vline(im, sx, 36, FLOOR_TOP - 1, "grey3")
        vline(im, sx + 1, 36, FLOOR_TOP - 1, "grey4")
    # steel wainscot
    rect(im, 0, 120, W, 18, "grey2")
    dither_grad(im, (0, 121, W, 137), "grey3", "grey1", "y", 4, 0.0, 0.8)
    hline(im, 0, W - 1, 120, "ink")
    hline(im, 0, W - 1, 121, "grey4")
    for sx in range(0, W, 19):
        vline(im, sx, 122, 137, "grey1")
        px(im, sx + 1, 124, "grey3")
    # baseboard line
    hline(im, 0, W - 1, 137, "ink2")
    # ceiling
    rect(im, 0, Y0, W, 13, "ink2")
    dither_grad(im, (0, Y0, W, 35), "ink", "ink2", "y", 4, 0.0, 1.0)
    for sx in range(0, W, 32):
        vline(im, sx, Y0, 34, "ink")
    hline(im, 0, W - 1, 35, "ink")
    hline(im, 0, W - 1, 36, "grey2")
    # fluorescent tubes (one dying)
    tube(im, 22, 104, 29)
    tube(im, 126, 212, 29)
    tube(im, 232, 262, 29, on=False)
    # a little vent + cable tray at ceiling
    for vx in range(268, 306, 4):
        vline(im, vx, 26, 33, "ink")
    # floor
    floor_band(im, FLOOR_TOP, 158, "grey2", "grey3", "grey1", "grey4", 20, 5)
    glow(im, 10, FLOOR_TOP + 1, 118, 156, "grey4", 0.35, 4, 16, up=False)
    glow(im, 130, FLOOR_TOP + 1, 214, 156, "wall1", 0.4, 4, 16, up=False)
    ovl(im, (0, 150, W, 158), "grey1", 0.25, 4)
    # cold light from the glass door on the floor
    glow(im, 232, 140, 316, 158, "blue3", 0.4, 4, 12)

    cubby_unit(im)
    hub_counter(im)

    # ---------------- middle-right wall: clock, notice board, helmet hooks
    clock_face(im, 237, 47, 8)
    # board
    obox(im, 216, 60, 48, 30, "brown3", "brown3", "brown2", ol="ink")
    rect(im, 217, 61, 46, 28, "brown3")
    dither_grad(im, (218, 62, 262, 88), "brown3", "brown2", "y", 4, 0.0, 0.5)
    rect(im, 216, 60, 48, 1, "brown1")
    # rule sheet (big white paper)
    rect(im, 221, 63, 20, 24, "white", "ink")
    rect(im, 223, 65, 16, 3, "red2")
    for ly in range(70, 85, 3):
        hline(im, 223, 237 - (ly % 2) * 3, ly, "grey2")
    px(im, 231, 63, "red3"); px(im, 231, 62, "red3")
    # other notes
    rect(im, 244, 64, 8, 9, "yellow2", "ink"); hline(im, 246, 250, 67, "grey2"); hline(im, 246, 249, 69, "grey2")
    rect(im, 253, 70, 8, 10, "wall4", "ink"); hline(im, 255, 259, 73, "grey2"); hline(im, 255, 258, 75, "grey2")
    rect(im, 244, 76, 7, 8, "blue4", "ink"); hline(im, 245, 249, 79, "grey2")
    for pxx, pyy in ((231, 64), (248, 65), (257, 71), (247, 77)):
        px(im, pxx, pyy, "red3")
    # hooks + helmets
    helmet_hook_row(im, 212, 262, 98)
    helmet(im, 218, 102, "orange2", "orange1", "orange3")
    helmet(im, 240, 102, "white", "grey3", "white")
    # key on hook
    px(im, 258, 105, "yellow"); px(im, 258, 106, "yellow"); px(im, 257, 107, "yellow")
    # crates and a bin at the wall base
    for i, (cx, cy) in enumerate(((214, 124), (214, 130))):
        rect(im, cx, cy, 24, 7, "blue2", "ink")
        hline(im, cx + 1, cx + 22, cy + 1, "blue3")
        rect(im, cx + 8, cy + 3, 8, 2, "blue1")
    rect(im, 216, 122, 18, 2, "ink")
    rect(im, 247, 124, 14, 14, "grey3", "ink")
    hline(im, 248, 259, 125, "grey4")
    hline(im, 246, 261, 123, "ink")
    rect(im, 249, 128, 10, 4, "green1")
    text(im, 254, 127, "병", "white", 9, align="center") if False else None
    for gy in (133,):
        hline(im, 248, 259, gy, "grey2")

    # wet floor sign left of counter (A-frame)
    poly(im, [(114, 138), (128, 138), (124, 122), (118, 122)], "yellow", "ink")
    rect(im, 119, 126, 4, 6, "ink")
    px(im, 121, 134, "ink")
    hline(im, 115, 127, 137, "orange2")
    # outlets, cable, thermostat on wall between unit and counter
    rect(im, 120, 96, 6, 9, "white", "ink"); px(im, 122, 99, "ink"); px(im, 123, 99, "ink"); px(im, 122, 102, "red3")
    # cardboard stack
    rect(im, 115, 104, 12, 14, "brown3", "ink")
    hline(im, 116, 125, 108, "brown2"); rect(im, 119, 104, 4, 3, "yellow2")
    # exit door
    glass_door(im)
    # cable along the ceiling to door
    line(im, [(212, 36), (212, 44), (268, 44), (268, 58)], "ink2")

    letterbox(im)
    return im


# ======================================================================
# 2. APARTMENT HALL
# ======================================================================
def steel_leaf(img, x, y, lw, h, kind, slant=0, lock=True, side="right", flyers=False, hinge=False):
    """A steel apartment door leaf. kind: 'brown' | 'green'."""
    P = {"brown": ("brown2", "brown1", "brown3", "brown0"),
         "green": ("green1", "green0", "green2", "ink2")}[kind]
    base, shade, hi, deep = P
    pts = [(x, y + slant), (x + lw - 1, y), (x + lw - 1, y + h - 1), (x, y + h - 1 - slant)]
    poly(img, pts, base, "ink")
    # vertical dither shading toward the right edge (light top-left)
    dpoly(img, [(a + (1 if a == x else 0), b) for a, b in pts], base, shade, 0.0, 0.55, "x", 4)
    poly(img, pts, None, "ink")
    # top-left highlight
    hline(img, x + 1, x + lw - 3, y + 1 + (slant // 2), hi)
    vline(img, x + 1, y + 2 + slant, y + h - 3 - slant, hi)
    if lw >= 14:
        pl = lw - 8
        px0 = x + 4
        # raised panels
        for (py0, ph) in ((y + 6, 22), (y + 33, 19)):
            rect(img, px0, py0, pl, ph, base, deep)
            hline(img, px0 + 1, px0 + pl - 2, py0 + 1, hi)
            vline(img, px0 + 1, py0 + 1, py0 + ph - 2, hi)
            hline(img, px0 + 1, px0 + pl - 2, py0 + ph - 2, shade)
            vline(img, px0 + pl - 2, py0 + 1, py0 + ph - 2, shade)
    # peephole
    if lw >= 14:
        hx = x + lw // 2
        ellipse(img, hx - 1, y + 14, hx + 1, y + 16, "grey4", "ink")
        px(img, hx, y + 15, "blue2")
    return base, shade, hi, deep


def digital_lock(img, x, y, c="grey3"):
    rect(img, x, y, 6, 13, c, "ink")
    for ky in (y + 2, y + 5, y + 8):
        px(img, x + 1, ky, "ink2"); px(img, x + 3, ky, "ink2")
    px(img, x + 4, y + 11, "red3")
    # lever handle
    rect(img, x - 4, y + 5, 5, 2, "grey4", "ink")


def apt_door(img, cx, kind, flyers=False, tag=False, lock_right=True, light=False):
    x, y = cx - 14, 92
    # casing
    rect(img, x - 2, y - 2, 32, 60, "grey3", "ink")
    vline(img, x - 1, y - 1, y + 56, "grey4")
    hline(img, x - 1, x + 28, y - 1, "grey4")
    steel_leaf(img, x, y, 28, 58, kind)
    lx = x + 20 if lock_right else x + 2
    digital_lock(img, lx, y + 29, "grey3")
    if flyers:
        for (fx, fy, fw, fh, fc) in ((x + 4, y + 8, 7, 9, "red3"), (x + 12, y + 22, 8, 7, "yellow2"), (x + 6, y + 36, 7, 9, "blue3")):
            rect(img, fx, fy, fw, fh, fc, "ink")
            hline(img, fx + 1, fx + fw - 2, fy + 2, "white")
            hline(img, fx + 1, fx + fw - 3, fy + 4, "ink2")
            px(img, fx, fy, "grey4"); px(img, fx + fw - 1, fy + fh - 1, "grey4")
    if tag:
        # delivery tag hung on the handle (pink slip)
        line(img, [(lx - 3, y + 36), (lx - 3, y + 40)], "ink")
        rect(img, lx - 5, y + 40, 5, 6, "wall4", "ink")
    # threshold + mat
    rect(img, x - 2, 150, 32, 2, "grey1", "ink")
    rect(img, x + 2, 151, 24, 4, "ink2", "ink")
    for mx in range(x + 3, x + 26, 3):
        px(img, mx, 153, "grey1")
    if light:
        hline(img, x + 3, x + 24, 150, "yellow2")
        glow(img, x + 1, 151, x + 27, 158, "orange3", 0.6, 4, 4, up=True)
    # plaque (blank)
    rect(img, cx - 9, 80, 19, 9, "wall1", "ink")
    hline(img, cx - 8, cx + 8, 81, "white")
    hline(img, cx - 8, cx + 8, 87, "grey3")


def elevator_closed(img):
    # casing
    rect(img, 15, 83, 46, 67, "grey2", "ink")
    hline(img, 16, 59, 84, "grey4")
    vline(img, 16, 84, 148, "grey4")
    # door leaves
    rect(img, 18, 86, 40, 64, "grey3", "ink")
    dither_grad(img, (19, 87, 57, 149), "grey4", "grey3", "x", 4, 0.0, 0.5)
    for vx in range(21, 56, 3):
        if abs(vx - 38) > 1:
            vline(img, vx, 88, 146, "grey3" if (vx // 3) % 2 else "grey4")
    # seam
    vline(img, 38, 86, 149, "ink")
    vline(img, 39, 87, 149, "grey2")
    vline(img, 37, 87, 149, "grey2")
    # leaf frame inner panel lines
    for (ax, bx) in ((20, 36), (41, 56)):
        rect(img, ax, 90, bx - ax, 54, None, "grey2")
    hline(img, 19, 57, 140, "grey2")
    # kick plates
    rect(img, 19, 143, 19, 6, "grey2")
    rect(img, 39, 143, 18, 6, "grey2")
    hline(img, 19, 57, 143, "ink")
    # scuffs and grime
    for (sx, sy, sl) in ((24, 120, 6), (47, 108, 4), (50, 128, 5)):
        hline(img, sx, sx + sl, sy, "grey2")
    streaks(img, (19, 130, 57, 148), "grey2", 8, 21, 12, 0.5)
    # sticker near the seam
    rect(img, 33, 112, 4, 8, "yellow2", "ink")
    # floor indicator box (BLANK dark; game writes the number)
    rect(img, 21, 69, 34, 14, "grey1", "ink")
    rect(img, 22, 70, 32, 13, "ink")
    hline(img, 23, 52, 71, "ink2")
    # brand-less plate above indicator
    rect(img, 18, 63, 40, 5, "grey3", "ink")
    for sx in range(22, 54, 5):
        px(img, sx, 65, "grey1")
    # threshold
    rect(img, 16, 150, 44, 2, "grey1", "ink")
    hline(img, 17, 58, 150, "grey2")
    # call panel
    rect(img, 62, 112, 5, 11, "grey4", "ink")
    rect(img, 63, 114, 3, 3, "orange3", "ink")
    rect(img, 63, 118, 3, 3, "grey2", "ink")
    px(img, 64, 115, "yellow2")
    glow(img, 58, 104, 76, 130, "orange3", 0.3, 4, 3)
    px(img, 64, 115, "yellow2")


def fire_ext_box(img, x, y):
    rect(img, x, y, 15, 29, "red2", "ink")
    rect(img, x + 1, y + 1, 13, 2, "red3")
    rect(img, x + 3, y + 5, 9, 19, "grey4", "ink")           # glass window
    ovl(img, (x + 4, y + 6, x + 11, y + 23), "blue3", 0.25, 4)
    # extinguisher inside
    rect(img, x + 5, y + 10, 5, 12, "red1", "ink")
    rect(img, x + 6, y + 7, 3, 3, "ink2", "ink")
    px(img, x + 7, y + 11, "red3")
    hline(img, x + 5, x + 9, y + 15, "white")
    rect(img, x + 2, y + 25, 11, 3, "red1")
    px(img, x + 7, y + 26, "white")


def stroller(img, x, y):
    """Folded-ish stroller seen from the side: x..x+24, bottom y."""
    # wheels
    for wx in (x + 5, x + 20):
        ellipse(img, wx - 3, y - 6, wx + 3, y, "ink2", "ink")
        px(img, wx, y - 3, "grey3")
    # frame
    line(img, [(x + 5, y - 6), (x + 12, y - 12), (x + 20, y - 6)], "ink")
    # seat/hood
    poly(img, [(x + 6, y - 14), (x + 18, y - 14), (x + 20, y - 24), (x + 8, y - 26)], "blue2", "ink")
    poly(img, [(x + 8, y - 24), (x + 20, y - 24), (x + 19, y - 18), (x + 9, y - 20)], "blue3", "ink")
    hline(img, x + 8, x + 17, y - 15, "blue1")
    # handle
    line(img, [(x + 20, y - 24), (x + 24, y - 28), (x + 25, y - 22)], "ink")
    # blanket on the seat
    rect(img, x + 9, y - 20, 8, 4, "wall4", "ink")
    hline(img, x + 10, x + 15, y - 19, "white")


def shoe_rack(img, x, y):
    """Open rack x..x+20, bottom y."""
    rect(img, x, y - 16, 21, 16, "brown2", "ink")
    rect(img, x + 1, y - 15, 19, 14, "ink2")
    for sy in (y - 11, y - 6):
        rect(img, x + 1, sy, 19, 2, "brown3", "ink")
    # shoes on each shelf
    shoes = [(x + 2, y - 15, "red3"), (x + 11, y - 15, "blue2"), (x + 3, y - 10, "grey4"), (x + 12, y - 10, "orange2"), (x + 6, y - 5, "ink"), (x + 14, y - 5, "yellow")]
    for sx, sy, c in shoes:
        rect(img, sx, sy - 0 if False else sy, 6, 3, c, "ink")
    # slippers on the floor in front
    rect(img, x - 7, y - 3, 6, 3, "green2", "ink")
    rect(img, x - 14, y - 2, 6, 2, "wall3", "ink")


def umbrella_stand(img, x, y):
    rect(img, x, y - 14, 12, 14, "grey3", "ink")
    hline(img, x + 1, x + 8, y - 13, "white")
    hline(img, x + 1, x + 8, y - 8, "grey2")
    # umbrellas
    for (ux, uc, tip) in ((x + 1, "blue2", 9), (x + 4, "red2", 13), (x + 7, "green1", 7)):
        rect(img, ux, y - 14 - tip, 4, tip, uc, "ink")
        vline(img, ux + 1, y - 13 - tip, y - 16, "white" if uc != "red2" else "red3")
        rect(img, ux, y - 14 - tip + 4, 4, 1, "ink")        # strap
        px(img, ux + 2, y - 15 - tip, "ink")


def cctv_dome(img, x, y):
    rect(img, x - 4, y, 9, 2, "grey3", "ink")
    ellipse(img, x - 4, y + 1, x + 4, y + 7, "ink2", "ink")
    px(img, x + 2, y + 3, "red3"); px(img, x + 1, y + 2, "grey2")


def build_hall():
    im = new(W, H, "ink")
    # ceiling
    rect(im, 0, Y0, W, 18, "grey1")
    dither_grad(im, (0, Y0, W, 40), "ink2", "grey1", "y", 4, 0.0, 1.0)
    # ceiling panels
    for sx in range(0, W, 24):
        vline(im, sx, Y0, 39, "ink2")
    hline(im, 0, W - 1, 40, "ink")
    # cornice
    hline(im, 0, W - 1, 41, "grey3")
    hline(im, 0, W - 1, 42, "grey2")
    # wall upper: pastel mint, dim at top, lit under tubes
    dither_ramp(im, (0, 43, W, 108), ["grey3", "wall2", "wall2"], "y", 4)
    # wall panel joints (precast apartment wall) faint
    for sx in (92, 152, 212, 272):
        vline(im, sx, 43, 107, "grey3")
    # wainscot: pastel blue lower wall with dividing rail
    rect(im, 0, 108, W, 30, "wall3")
    dither_grad(im, (0, 109, W, 138), "wall3", "grey3", "y", 4, 0.0, 0.8)
    hline(im, 0, W - 1, 107, "ink")
    hline(im, 0, W - 1, 108, "white")
    hline(im, 0, W - 1, 109, "wall1")
    hline(im, 0, W - 1, 110, "grey3")
    hline(im, 0, W - 1, 137, "ink")
    for sx in range(0, W, 3):
        px(im, sx, 111, "wall2")
    # stains and peeling paint
    streaks(im, (0, 44, W, 106), "grey3", 28, 11, 18, 0.5, "wall2")
    patches = [(70, 60, 8, 3), (136, 50, 5, 4), (252, 64, 7, 3), (118, 96, 9, 2), (288, 94, 6, 4)]
    for (px_, py_, pw, ph) in patches:
        ovl(im, (px_, py_, px_ + pw, py_ + ph), "wall1", 0.6, 2)
        hline(im, px_, px_ + pw - 1, py_ + ph, "grey3")
    # floor
    floor_band(im, FLOOR_TOP, 158, "grey2", "grey3", "grey1", "wall1", 24, 17)
    ovl(im, (0, 142, W, 158), "brown3", 0.18, 4, "grey3")
    # lit puddles of tube light on the floor
    for (a, b) in ((30, 118), (136, 244)):
        glow(im, a, 141, b, 158, "wall1", 0.4, 4, 18)
    # fluorescent fixtures
    tube(im, 34, 96, 30)
    tube(im, 124, 200, 30)
    tube(im, 224, 262, 30, on=False)
    px(im, 262, 33, "white"); px(im, 263, 33, "white")
    cctv_dome(im, 122, 41)
    # a pipe running the ceiling
    rect(im, 0, 24, W, 3, "grey2", "ink")
    hline(im, 0, W - 1, 25, "grey3")
    for bx in range(18, W, 52):
        rect(im, bx, 23, 3, 5, "grey1", "ink")

    elevator_closed(im)

    # doors: brown, green, brown
    apt_door(im, 110, "brown", tag=True)
    apt_door(im, 170, "green", flyers=True, lock_right=False, light=True)
    apt_door(im, 230, "brown")

    # --- gap A: notice board + umbrellas
    obox(im, 72, 92, 20, 26, "brown3", "brown3", "brown2")
    rect(im, 73, 93, 18, 24, "brown3")
    for (fx, fy, fw, fh, fc) in ((75, 95, 8, 10, "white"), (84, 97, 6, 7, "yellow2"), (76, 107, 7, 8, "wall4"), (85, 106, 5, 9, "blue4")):
        rect(im, fx, fy, fw, fh, fc, "ink")
        hline(im, fx + 1, fx + fw - 2, fy + 2, "grey2")
        if fh > 7:
            hline(im, fx + 1, fx + fw - 3, fy + 4, "grey3")
    px(im, 78, 95, "red3"); px(im, 86, 97, "red3"); px(im, 79, 107, "red3")
    umbrella_stand(im, 73, 150)
    # --- gap B: milk box on wall + shoe rack
    rect(im, 127, 114, 9, 10, "white", "ink")
    rect(im, 128, 115, 7, 3, "blue2")
    px(im, 131, 120, "grey2")
    rect(im, 127, 124, 9, 1, "ink")
    shoe_rack(im, 136, 150)
    # --- gap C: stroller + a folded newspaper bundle
    stroller(im, 187, 150)
    rect(im, 211, 142, 8, 8, "grey4", "ink")
    hline(im, 212, 217, 145, "grey2"); hline(im, 212, 217, 147, "grey2")
    # --- gap D: extinguisher + recycling
    fire_ext_box(im, 248, 100)
    rect(im, 247, 130, 17, 1, "ink")
    # recycling bags + flattened boxes
    rect(im, 254, 136, 14, 14, "green1", "ink")
    hline(im, 255, 266, 137, "green2")
    rect(im, 252, 143, 16, 7, "brown3", "ink")
    hline(im, 253, 266, 146, "brown2")
    rect(im, 250, 148, 13, 2, "wall1", "ink")

    # --- stairwell fire door (x276..310, y88..150)
    x, y, w, h = 276, 88, 35, 63
    rect(im, x - 2, y - 2, w + 4, h + 2, "grey2", "ink")
    rect(im, x, y, w, h - 1, "grey3", "ink")
    dither_grad(im, (x + 1, y + 1, x + w - 1, y + h - 2), "grey4", "grey2", "x", 4, 0.0, 0.7)
    hline(im, x + 1, x + w - 2, y + 1, "white")
    # wire window
    rect(im, x + 10, y + 8, 14, 22, "blue0", "ink")
    dither_grad(im, (x + 11, y + 9, x + 23, y + 29), "blue1", "blue0", "d", 4, 0.0, 1.0)
    for gy in range(y + 11, y + 29, 4):
        hline(im, x + 11, x + 22, gy, "grey1")
    for gx in range(x + 13, x + 23, 4):
        vline(im, gx, y + 9, y + 29, "grey1")
    # push plate and bar, kick plate
    rect(im, x + 4, y + 34, 27, 4, "grey4", "ink")
    rect(im, x + 5, y + 40, 6, 12, "grey2", "ink")
    rect(im, x, y + h - 9, w, 8, "grey2", "ink")
    hline(im, x + 1, x + w - 2, y + h - 8, "grey3")
    # door closer arm (top)
    line(im, [(x + 4, y - 1), (x + 12, y - 5), (x + 20, y - 1)], "ink")
    rect(im, x + 12, y - 7, 8, 3, "grey1", "ink")
    # fire-door stripe
    for sx in range(x + 2, x + w - 2, 4):
        px(im, sx, y + 3, "red2")
    # EXIT sign box above (invented, green, "계단")
    glow(im, 268, 70, 316, 100, "green2", 0.28, 4, 8)
    rect(im, 279, 71, 29, 15, "green0", "ink")
    rect(im, 280, 72, 27, 13, "green1", "ink")
    text(im, 299, 73, "계단", "white", 9, align="center")
    # small stairs/figure glyph
    px(im, 283, 82, "green3"); px(im, 284, 81, "green3"); px(im, 285, 80, "green3")
    # threshold + hazard
    rect(im, x - 2, 150, w + 4, 2, "grey1", "ink")
    # window strip far right top (dim night)
    rect(im, 262, 34, 54, 24, "grey2", "ink")
    rect(im, 264, 36, 50, 20, "blue0", "ink")
    dither_grad(im, (265, 37, 313, 55), "blue1", "blue0", "y", 4, 0.0, 0.9)
    for mx in (276, 289, 301):
        vline(im, mx, 36, 55, "grey2")
    hline(im, 264, 313, 46, "grey2")
    for (sx, sy) in ((268, 40), (283, 42), (296, 38), (306, 50), (272, 51)):
        px(im, sx, sy, "blue3")
    px(im, 309, 42, "yellow2")
    rect(im, 262, 58, 54, 2, "grey1", "ink")
    # lighting: dim window glow into the corridor
    glow(im, 250, 60, 318, 80, "blue2", 0.15, 4, 8)

    # vignette: dim ends of the corridor
    ovl(im, (0, 43, 12, 138), "ink2", 0.3, 2)
    ovl(im, (0, 43, 6, 138), "ink2", 0.3, 2)
    ovl(im, (0, 138, 12, 158), "ink2", 0.25, 2)

    letterbox(im)
    return im


# ======================================================================
# 3. STAIRWELL
# ======================================================================
STEP_RUN, STEP_RISE = 8, 7


def build_stairs():
    im = new(W, H, "ink")
    # concrete wall: dim, cold
    dither_ramp(im, (0, Y0, W, FLOOR_TOP), ["ink2", "grey1", "grey2", "grey2"], "y", 4)
    # shuttering seams (board-marked concrete)
    for sx in range(0, W, 46):
        vline(im, sx, Y0, FLOOR_TOP - 1, "grey1")
    for sy in (52, 84, 112):
        hline(im, 0, W - 1, sy, "grey1")
    speckle(im, (0, Y0, W, FLOOR_TOP), "grey3", 70, 5, "grey2")
    speckle(im, (0, Y0, W, FLOOR_TOP), "ink2", 60, 6)
    # dado: painted lower wall
    rect(im, 0, 100, W, 38, "grey1")
    dither_grad(im, (0, 101, W, 138), "grey2", "ink2", "y", 4, 0.0, 0.9)
    hline(im, 0, W - 1, 99, "ink")
    hline(im, 0, W - 1, 100, "grey3")
    hline(im, 0, W - 1, 101, "grey2")
    hline(im, 0, W - 1, 137, "ink")

    # caged bulb glow (cold) - drawn before objects
    bx, by = 162, 40
    dither_radial(im, bx, by + 6, 64, "grey3", None, 4, box=(60, 22, 270, 136))
    dither_radial(im, bx, by + 6, 34, "grey4", None, 4, box=(120, 22, 210, 100))
    dither_radial(im, bx, by + 6, 15, "white", None, 4)

    # floor (landing) - concrete
    floor_band(im, FLOOR_TOP, 158, "grey1", "grey2", "ink2", "grey3", 28, 9, x0=119, x1=W)
    glow(im, 120, 141, 250, 158, "grey3", 0.3, 4, 20)

    # ----- left: descending flight pit
    rect(im, 0, FLOOR_TOP, 119, 20, "ink")
    dither_grad(im, (0, FLOOR_TOP + 1, 119, 158), "ink", "ink2", "y", 2, 0.0, 0.6)
    # stringer diagonal on the back wall
    for xx in range(2, 119):
        yy = FLOOR_TOP + round((118 - xx) * 7 / 8) - 1
        if yy < 158 and xx > 96:
            px(im, xx, yy, "grey3")
    # slab edge
    rect(im, 114, FLOOR_TOP + 1, 6, 19, "grey2", "ink")
    vline(im, 115, FLOOR_TOP + 2, 156, "grey3")
    # steps descending out of the frame
    for k in range(3):
        sx = 116 - 8 * k
        sy = 147 + 6 * k
        if sy < 157:
            rect(im, sx - 8, sy, 9, 2, "grey3", "ink")
            hline(im, sx - 7, sx - 1, sy, "white")
    # handrail going down-left, posts
    for xx in range(2, 120):
        yy = 112 + round((118 - xx) * 7 / 8)
        if yy < 158:
            px(im, xx, yy, "ink"); px(im, xx, yy - 1, "grey4"); px(im, xx, yy + 1, "grey1") if False else None
    for pxx in (118, 102, 86, 70, 54):
        yy = 112 + round((118 - pxx) * 7 / 8)
        vline(im, pxx, yy, min(157, 150 + round((118 - pxx) * 7 / 8)) if pxx == 118 else min(157, yy + 40), "grey1")
    rect(im, 117, 110, 4, 3, "grey2", "ink")
    # the guard rail continuing along the landing edge (small horizontal run)
    # ----- right: ascending flight (stairs rising to the right)
    pts = [(205, 150)]
    k = 0
    while True:
        x0s = 205 + STEP_RUN * k
        ytop = 150 - STEP_RISE * (k + 1)
        pts.append((x0s, ytop))
        pts.append((x0s + STEP_RUN, ytop))
        k += 1
        if x0s + STEP_RUN >= 318:
            break
    pts.append((318, 150))
    mass = [(205, 150)] + pts[1:]
    dpoly(im, mass, "grey2", "grey1", 0.1, 0.9, "x", 4)
    sh = [(220, 147), (318, 68), (318, 150), (220, 150)]
    dither_grad(im, bbox(sh), "grey2", "ink2", "d", 2, 0.45, 0.8, mk_mask(sh, im.size))
    # steps: tread highlight and riser shadow
    for k in range(0, 15):
        x0s = 205 + STEP_RUN * k
        ytop = 150 - STEP_RISE * (k + 1)
        if x0s > 318:
            break
        hline(im, x0s, min(317, x0s + STEP_RUN - 1), ytop, "grey4")
        hline(im, x0s, min(317, x0s + STEP_RUN - 1), ytop + 1, "grey3")
        vline(im, x0s, ytop + 1, ytop + STEP_RISE, "ink")
        hline(im, x0s, min(317, x0s + STEP_RUN - 1), ytop + 2, "grey2")
        # riser face shadow band
        ovl(im, (x0s + 1, ytop + 2, min(318, x0s + STEP_RUN), ytop + STEP_RISE), "ink2", 0.35, 2)
        # nosing wear
        px(im, x0s + 1, ytop + 2, "grey4")
    poly(im, mass, None, "ink")
    # dark gap beneath the flight (a cupboard with a mop bucket)
    poly(im, [(214, 150), (214, 137), (232, 137), (232, 150)], "ink")
    for xx in range(215, 232):
        px(im, xx, 138, "ink2")
    rect(im, 218, 142, 8, 8, "blue2", "ink"); hline(im, 219, 224, 143, "blue3")
    line(im, [(225, 142), (228, 128)], "brown3")
    # handrail up
    for k in range(0, 14):
        x0s = 205 + STEP_RUN * k
        ytop = 150 - STEP_RISE * (k + 1)
        ry = ytop - 30
        for t in range(STEP_RUN):
            xx = x0s + t
            yy = ry - round(t * STEP_RISE / STEP_RUN)
            if 0 <= xx < W and yy >= Y0:
                px(im, xx, yy, "grey4"); px(im, xx, yy + 1, "ink")
        if k % 2 == 0:
            vline(im, x0s + 1, max(Y0, ry + 2), ytop - 1, "grey2")
    # newel post at the bottom
    rect(im, 203, 112, 4, 38, "grey2", "ink")
    vline(im, 204, 113, 148, "grey3")
    rect(im, 202, 109, 6, 3, "grey3", "ink")
    # step numbering paint on the first riser? (kept clean) - stair edge tape
    for k in range(0, 14):
        x0s = 205 + STEP_RUN * k
        ytop = 150 - STEP_RISE * (k + 1)
        if k % 1 == 0:
            for t in range(0, STEP_RUN, 2):
                px(im, x0s + t, ytop, "yellow" if k < 4 else "grey4")

    # ----- wall features
    # painted blank rectangle (x60..110, y40..76) for the floor number
    rect(im, 60, 40, 51, 37, "grey4")
    dither_grad(im, (60, 40, 111, 77), "grey4", "wall3", "y", 4, 0.0, 0.55)
    dither_grad(im, (60, 40, 111, 77), "white", "grey4", "d", 4, 0.0, 0.4, None) if False else None
    # ragged edges: stray roller marks
    for (ex, ey) in ((60, 44), (60, 58), (110, 50), (110, 66), (74, 77), (96, 77), (88, 40)):
        px(im, ex, ey, "grey2")
    ovl(im, (60, 40, 111, 41), "grey3", 0.5, 4); ovl(im, (60, 76, 111, 77), "grey3", 0.5, 4)
    ovl(im, (60, 40, 61, 77), "grey3", 0.5, 4); ovl(im, (110, 40, 111, 77), "grey3", 0.5, 4)
    for (ex, ey) in ((61, 41), (109, 41), (61, 75), (109, 75), (62, 40), (108, 76)):
        px(im, ex, ey, "grey2")
    # paint drips below
    for dx_, dl in ((66, 7), (79, 4), (101, 9)):
        vline(im, dx_, 77, 77 + dl, "grey4")
    # water stain
    streaks(im, (60, 41, 110, 76), "grey3", 5, 40, 16, 0.5, "grey4")
    streaks(im, (30, 30, 200, 99), "ink2", 14, 41, 22, 0.6, "grey2")
    # wall pipe: vertical conduit + a horizontal run
    rect(im, 128, Y0, 5, 116, "grey2", "ink")
    vline(im, 129, Y0 + 1, 136, "grey3")
    for by_ in (40, 74, 108):
        rect(im, 126, by_, 9, 3, "grey1", "ink")
    rect(im, 0, 28, 132, 4, "grey2", "ink")
    hline(im, 1, 127, 29, "grey3")
    for bx_ in (14, 56, 98):
        rect(im, bx_, 26, 3, 8, "grey1", "ink")
    # pipe valve wheel
    ellipse(im, 130 - 4, 96 - 4, 130 + 4, 96 + 4, None, "red2")
    px(im, 130, 96, "red3")
    # peeling flyers
    flyers = [(22, 58, 12, 16, "yellow2"), (28, 76, 10, 13, "wall4"), (10, 66, 8, 12, "blue4"),
              (190, 58, 11, 15, "white"), (196, 74, 9, 12, "wall1")]
    for (fx, fy, fw, fh, fc) in flyers:
        rect(im, fx, fy, fw, fh, fc, "ink")
        for ly in range(fy + 3, fy + fh - 2, 3):
            hline(im, fx + 1, fx + fw - 3, ly, "grey2")
        px(im, fx + fw - 1, fy, "grey3"); px(im, fx + fw - 1, fy + 1, "ink")   # curled corner
        px(im, fx, fy + fh - 1, "grey3")
    px(im, 26, 58, "red3")
    # fuse / breaker box
    rect(im, 184, 104, 14, 20, "grey3", "ink")
    rect(im, 186, 106, 10, 16, "grey2", "ink")
    hline(im, 187, 194, 110, "ink")
    for ly in (113, 116, 119):
        hline(im, 188, 193, ly, "grey4")
    rect(im, 190, 107, 2, 2, "red3")

    # ----- door back to corridor (x146..178, y90..150)
    x, y, w, h = 146, 90, 33, 61
    rect(im, x - 3, y - 3, w + 6, h + 3, "grey3", "ink")
    rect(im, x, y, w, h - 1, "green1", "ink")
    dither_grad(im, (x + 1, y + 1, x + w - 1, y + h - 2), "green1", "green0", "x", 4, 0.0, 0.8)
    hline(im, x + 1, x + w - 2, y + 1, "green2")
    vline(im, x + 1, y + 1, y + h - 3, "green2")
    # small window with wire glass, warm light of the corridor beyond
    rect(im, x + 9, y + 8, 15, 18, "ink", "ink")
    rect(im, x + 10, y + 9, 13, 16, "wall1")
    dither_grad(im, (x + 10, y + 9, x + 23, y + 25), "wall1", "wall2", "d", 4, 0.0, 1.0)
    for gy in range(y + 13, y + 25, 4):
        hline(im, x + 10, x + 22, gy, "grey3")
    for gx in range(x + 14, x + 23, 4):
        vline(im, gx, y + 9, y + 24, "grey3")
    # handle, plate, kickplate
    rect(im, x + 24, y + 30, 4, 10, "grey3", "ink")
    rect(im, x + 5, y + 32, 4, 4, "grey4", "ink")
    rect(im, x, y + h - 10, w, 9, "grey2", "ink")
    hline(im, x + 1, x + w - 2, y + h - 9, "grey3")
    # light under the door
    hline(im, x + 2, x + w - 3, 150, "yellow2")
    glow(im, x - 6, 150, x + w + 6, 158, "wall1", 0.5, 4, 8, up=True)
    # exit sign above door
    rect(im, 149, 72, 26, 14, "green0", "ink")
    rect(im, 150, 73, 24, 12, "green1", "ink")
    text(im, 163, 76, "비상구", "white", 9, align="center") if False else None
    text(im, 162, 73, "계단", "white", 9, align="center")
    # door hinge, closer
    for hy in (y + 8, y + 40):
        rect(im, x + w - 1, hy, 2, 5, "grey1", "ink")
    line(im, [(x + 3, y - 2), (x + 12, y - 6), (x + 21, y - 2)], "ink")

    # ----- bulb (cage + wire) drawn on top
    vline(im, bx, Y0, by - 6, "ink")
    rect(im, bx - 4, by - 8, 9, 3, "grey1", "ink")
    ellipse(im, bx - 3, by - 5, bx + 3, by + 3, "white", "ink")
    px(im, bx - 1, by - 3, "white"); px(im, bx, by - 2, "white")
    wire_cage(im, bx, by - 1, 6)
    # moths
    for (mx, my) in ((bx - 12, by + 8), (bx + 9, by + 12)):
        px(im, mx, my, "grey4"); px(im, mx + 1, my - 1, "grey3")

    # vignette
    ovl(im, (0, Y0, 14, 138), "ink", 0.3, 2)
    ovl(im, (306, Y0, 320, 60), "ink", 0.3, 2)
    letterbox(im)
    return im


# ======================================================================
# PROPS
# ======================================================================
def wheel(img, cx, cy, ang, r=6):
    ellipse(img, cx - r, cy - r, cx + r, cy + r, "ink2", "ink")
    # tyre tread marks rotate with the wheel
    for k in range(4):
        a = math.radians(ang + 45 + k * 90)
        px(img, round(cx + math.cos(a) * (r - 1)), round(cy + math.sin(a) * (r - 1)), "grey1")
    ellipse(img, cx - 3, cy - 3, cx + 3, cy + 3, "grey3", "ink2")
    for k in range(4):
        a = math.radians(ang + k * 90)
        line(img, [(cx, cy), (round(cx + math.cos(a) * 3), round(cy + math.sin(a) * 3))], "grey1")
    px(img, cx, cy, "grey4")


def build_moped(frame):
    ang = 0 if frame == 0 else 40
    im = new(44, 30)
    # rear rack + delivery box
    rect(im, 1, 13, 15, 2, "grey2", "ink")
    rect(im, 0, 1, 16, 13, "orange2", "ink")
    rect(im, 1, 2, 14, 2, "orange3")
    vline(im, 1, 3, 12, "orange3")
    rect(im, 1, 8, 14, 2, "orange1")
    rect(im, 5, 5, 6, 3, "yellow", "ink")
    px(im, 6, 6, "orange1"); px(im, 9, 6, "orange1")
    hline(im, 1, 14, 12, "orange1")
    # lid line
    hline(im, 1, 14, 5, "orange1") if False else None
    # tail light
    rect(im, 0, 14, 2, 3, "red3", "ink")
    # wheels first (body overlaps)
    wheel(im, 9, 23, ang)
    wheel(im, 35, 23, ang)
    # rear fender
    poly(im, [(3, 17), (16, 15), (16, 18), (4, 19)], "blue1", "ink")
    # body: blue shell
    poly(im, [(15, 14), (27, 14), (31, 19), (31, 23), (14, 23), (13, 17)], "blue2", "ink")
    rect(im, 16, 15, 10, 1, "blue3")
    poly(im, [(14, 20), (31, 20), (31, 23), (14, 23)], "blue1", "ink")
    hline(im, 15, 29, 21, "blue0")
    # engine casing under rear
    rect(im, 14, 17, 5, 5, "blue1", "ink")
    # seat
    poly(im, [(14, 10), (26, 10), (27, 14), (14, 14)], "ink2", "ink")
    hline(im, 15, 25, 11, "grey1")
    # floorboard
    rect(im, 22, 22, 11, 2, "grey2", "ink")
    # front shield + handlebar
    poly(im, [(30, 8), (34, 8), (36, 21), (31, 22)], "blue2", "ink")
    vline(im, 31, 10, 20, "blue3")
    rect(im, 31, 4, 7, 2, "ink2", "ink")                 # handlebar
    px(im, 37, 4, "grey3")
    rect(im, 32, 6, 2, 3, "ink")
    # mirror
    px(im, 34, 1, "ink"); px(im, 34, 2, "ink"); px(im, 35, 1, "grey4")
    # headlight
    rect(im, 36, 8, 4, 4, "yellow2", "ink")
    px(im, 37, 9, "white")
    # front fork + fender
    line(im, [(35, 12), (36, 22)], "ink")
    poly(im, [(31, 16), (40, 16), (42, 19), (31, 19)], "blue1", "ink")
    hline(im, 32, 40, 17, "blue2")
    # shadow under the wheels
    return im


def build_bag():
    im = new(14, 14)
    # handle straps
    line(im, [(3, 4), (3, 1), (10, 1), (10, 4)], "ink")
    line(im, [(4, 4), (4, 2), (9, 2), (9, 4)], "grey4")
    rect(im, 0, 4, 14, 10, "orange2", "ink")
    rect(im, 1, 5, 12, 2, "orange3")         # top flap light
    vline(im, 1, 5, 11, "orange3")
    hline(im, 1, 12, 7, "orange1")           # flap edge
    rect(im, 1, 9, 12, 2, "orange1")         # dark stripe
    hline(im, 1, 12, 12, "orange1")
    rect(im, 5, 8, 4, 4, "yellow", "ink")    # label
    px(im, 6, 9, "orange1"); px(im, 7, 10, "orange1")
    return im


def build_open_door():
    im = new(28, 58)
    # black gap (pitch black) with a slim frame shadow
    poly(im, [(0, 0), (11, 2), (11, 55), (0, 57)], "ink")

    # door leaf swung inward: hinge on right, free edge (left) shorter by perspective
    base, shade, hi, deep = steel_leaf(im, 10, 0, 18, 58, "brown", slant=2, lock=False)
    # thickness edge on the free side
    vline(im, 10, 3, 54, "orange1")
    vline(im, 11, 4, 53, "brown3")
    # digital lock on the free edge side, tilted
    rect(im, 12, 30, 4, 11, "grey3", "ink")
    px(im, 13, 32, "ink2"); px(im, 14, 32, "ink2"); px(im, 13, 35, "ink2"); px(im, 13, 38, "red3")
    # hinge side hardware
    for hy in (6, 28, 46):
        rect(im, 26, hy, 2, 5, "grey1", "ink")
    # eyes in the gap
    rect(im, 2, 18, 2, 2, "pale1")
    rect(im, 6, 18, 2, 2, "pale1")
    # faint sliver of floor light under the opening
    return im


def build_elevator_open():
    im = new(40, 64)
    # frame of the doorway
    rect(im, 0, 0, 40, 64, "ink")
    # cabin back wall: dim greenish lit
    rect(im, 5, 1, 30, 62, "green0")
    dither_ramp(im, (5, 1, 35, 56), ["green1", "green0", "green0"], "y", 4)
    # ceiling light panel
    rect(im, 8, 1, 24, 4, "green3", "ink")
    rect(im, 10, 2, 20, 2, "pale2")
    glow(im, 6, 5, 34, 30, "green2", 0.5, 4, 6)
    # mirror (back wall)
    rect(im, 9, 14, 22, 24, "grey4", "ink")
    dither_grad(im, (10, 15, 30, 37), "blue4", "pale1", "d", 4, 0.0, 1.0)
    for k in range(5):
        px(im, 13 + k * 2, 31 - k * 2, "white")
        px(im, 14 + k * 2, 31 - k * 2, "white")
    # faint reflected silhouette smudge (empty, slightly off)
    ovl(im, (17, 20, 25, 36), "pale1", 0.25, 4)
    # handrail
    rect(im, 6, 42, 28, 2, "grey3", "ink")
    hline(im, 7, 32, 42, "grey4")
    rect(im, 6, 42, 2, 4, "grey2", "ink")
    rect(im, 32, 42, 2, 4, "grey2", "ink")
    # button strip on the right side wall
    rect(im, 31, 8, 3, 14, "grey3", "ink")
    for by_ in (10, 14, 18):
        px(im, 32, by_, "orange3")
    # dado + floor
    rect(im, 5, 46, 30, 10, "green1")
    dither_grad(im, (5, 47, 35, 56), "green1", "green0", "y", 2, 0.0, 0.7)
    hline(im, 5, 34, 46, "green2")
    rect(im, 5, 56, 30, 7, "grey2")
    dither_grad(im, (5, 56, 35, 63), "grey3", "grey1", "y", 4, 0.0, 1.0)
    hline(im, 5, 34, 56, "ink")
    for fx in range(9, 34, 8):
        vline(im, fx, 57, 62, "grey1")
    # doors parked in the sides (two leaves, steel)
    rect(im, 0, 0, 6, 64, "grey3", "ink")
    rect(im, 34, 0, 6, 64, "grey3", "ink")
    vline(im, 1, 1, 62, "grey4"); vline(im, 35, 1, 62, "grey4")
    vline(im, 4, 1, 62, "grey2"); vline(im, 38, 1, 62, "grey2")
    for sy in (14, 30, 46):
        hline(im, 1, 4, sy, "grey2"); hline(im, 35, 38, sy, "grey2")
    # sill
    hline(im, 0, 39, 63, "grey1")
    # greenish light leaking out onto the floor
    return im


# ======================================================================
def main():
    hub = build_hub()
    assert not off_palette(hub)
    save(hub, "bg/delivery_hub.png")
    hall = build_hall()
    assert not off_palette(hall)
    save(hall, "bg/apt_hall.png")
    st = build_stairs()
    assert not off_palette(st)
    save(st, "bg/stairwell.png")
    outs = [("props/moped.png", build_moped(0)), ("props/moped_b.png", build_moped(1)),
            ("props/delivery_bag.png", build_bag()), ("props/apt_door_open.png", build_open_door()),
            ("props/elevator_open.png", build_elevator_open())]
    for p, im in outs:
        assert not off_palette(im), p
        save(im, p)
    paths = ["bg/delivery_hub.png", "bg/apt_hall.png", "bg/stairwell.png",
             "props/moped.png", "props/moped_b.png", "props/delivery_bag.png",
             "props/apt_door_open.png", "props/elevator_open.png"]
    contact(paths, "_contact/delivery.png", cols=2, scale=2)
    print("done")


if __name__ == "__main__":
    main()

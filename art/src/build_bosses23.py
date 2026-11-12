"""Act 2/3 boss + retheme assets for ONE MORE SHIFT.

Run:  python3 src/build_bosses23.py [part ...]     (parts: sprites bgs props; default all)
Writes assets/props/{suit_boss,resident}.png/.json, milk_carrier.png, officetel_door_open.png
       assets/bg/{stairwell_scissor,roof,milk_depot,officetel_hall}.png
       previews/_contact/bosses23.png
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
from pxkit import *
from pxkit import _thr
from PIL import Image, ImageDraw
from build_delivery import (glow, ovl, obox, hline, vline, speckle, streaks, mk_mask, bbox, dpoly,
                            tube, floor_band, wire_cage, digital_lock, elevator_closed,
                            fire_ext_box, cctv_dome, glass_door, FLOOR_TOP, Y0)
from build_event import (mascot_body, mascot_arm, egg, balloon_sprite, string_to, place_balloon, BODY)


# ====================================================================== SUIT BOSS
def lean(im, tilt):
    """Shear rows sideways (feet stay put). tilt>0 leans to the left."""
    out = new(*im.size)
    for y in range(im.height):
        sh = int(round((im.height - 1 - y) * tilt))
        out.paste(im.crop((0, y, im.width, y + 1)), (-sh, y))
    return out


def body_parts(cx, dy=0, legs=None, arms=("down", "down"), swing=(0, 0)):
    """Headless dumpling body: same torso/arms/collar code as the mascot, custom legs.
    legs: list of (x0, ytop, ysole) per leg in sprite px (shoe drawn at the bottom)."""
    im = new(48, 64)
    for (lx, lt, lb) in legs:
        rect(im, lx, lt, 9, lb - lt - 4, "blue1", "ink")
        vline(im, lx + 1, lt + 1, lb - 7, "blue2")
        sx0 = lx - 2 if lx < cx else lx - 1
        egg(im, sx0, lb - 5, sx0 + 12, lb, "white", "grey3")
    mascot_arm(im, cx, "R", arms[1], dy, swing[1])
    egg(im, cx - 12, 31 + dy, cx + 12, 54 + dy, *BODY)
    line(im, [(cx - 10, 38 + dy), (cx + 9, 51 + dy)], "ink", 6)
    line(im, [(cx - 10, 38 + dy), (cx + 9, 51 + dy)], "orange3", 4)
    line(im, [(cx - 10, 37 + dy), (cx + 8, 50 + dy)], "yellow2", 1)
    vline(im, cx, 36 + dy, 52 + dy, "ink")
    for y in range(37 + dy, 52 + dy):
        px(im, cx - 1 if y % 2 else cx + 1, y, "grey3")
    rect(im, cx - 1, 36 + dy, 3, 3, "yellow", "ink")
    mascot_arm(im, cx, "L", arms[0], dy, swing[0])
    # collar: red ring, opening of pure ink (the head is gone)
    ellipse(im, cx - 9, 28 + dy, cx + 9, 36 + dy, "red2", "ink")
    ellipse(im, cx - 7, 29 + dy, cx + 7, 34 + dy, "ink", "red1")
    px(im, cx - 8, 31 + dy, "red3")
    return im


def std_legs(cx, lift=(0, 0), spread=0, bottom=63):
    out = []
    for i, sx in enumerate((-1, 1)):
        lx = cx + sx * 7 - 4 + sx * spread
        lf = lift[i]
        out.append((lx, 50 - lf + (bottom - 63), bottom - lf))
    return out


def sparkle(im, x, y, c="yellow"):
    px(im, x, y, c); px(im, x - 1, y, "yellow2"); px(im, x + 1, y, "yellow2")
    px(im, x, y - 1, "yellow2"); px(im, x, y + 1, "yellow2")


def dash_leg(layer, hip, knee, foot):
    line(layer, [hip, knee], "blue1", 8)
    line(layer, [knee, foot], "blue1", 7)
    line(layer, [(hip[0] - 1, hip[1]), (knee[0] - 1, knee[1])], "blue2", 2)


def dash_frame(a):
    """Clean running lean (dashing left): torso tilted about the hips, legs mid-stride,
    arms trailing behind, speed lines to the right."""
    cx, hy = 26, 52
    ang = math.radians(28)
    ca, sa = math.cos(ang), math.sin(ang)

    def rot(x, y):
        dx, dy = x - cx, y - hy
        return (cx + dx * ca + dy * sa, hy - dx * sa + dy * ca)

    def rp(pts):
        return [tuple(int(round(v)) for v in rot(*p)) for p in pts]

    out = new(48, 64)
    # ---- legs
    if a:
        spec = (((cx - 2, 53), (cx - 9, 56), (cx - 17, 59)), ((cx + 3, 53), (cx + 11, 55), (cx + 15, 48)))
    else:
        spec = (((cx - 2, 53), (cx - 8, 58), (cx - 9, 61)), ((cx + 3, 53), (cx + 12, 57), (cx + 19, 56)))
    for k in (1, 0):
        lay = new(48, 64)
        dash_leg(lay, *spec[k])
        out.alpha_composite(outline(lay))
        ft = spec[k][2]
        egg(out, ft[0] - 5, ft[1] - 2, ft[0] + 5, ft[1] + 3, "white", "grey3")
    # ---- far arm trailing back (behind the torso)
    def arm(sh, hand, dark=False):
        lay = new(48, 64)
        line(lay, [sh, hand], "blue1" if dark else "blue2", 5)
        out.alpha_composite(outline(lay))
        egg(out, hand[0] - 3, hand[1] - 3, hand[0] + 3, hand[1] + 3, "white", "grey4")
    sh_far = tuple(int(v) for v in rot(cx + 10, 38))
    arm(sh_far, (sh_far[0] + 8, sh_far[1] + 7 + (0 if a else 3)), True)
    # ---- torso: tilted egg, tilted sash + collar
    t = new(48, 64)
    ellipse(t, cx - 12, 31, cx + 12, 54, "blue2")
    t = t.rotate(28, center=(cx, hy), resample=Image.NEAREST)
    dither_grad(t, (cx - 4, 20, 48, 62), "blue2", "blue1", "x", 2, 0.0, 0.9, shade_mask(t))
    out.alpha_composite(outline(t))
    p0, p1 = rot(cx - 10, 36), rot(cx + 9, 53)
    line(out, [p0, p1], "ink", 6)
    line(out, [p0, p1], "orange3", 4)
    line(out, [(p0[0], p0[1] - 1), (p1[0], p1[1] - 1)], "yellow2", 1)
    ring = []
    for i in range(16):
        th = i / 16 * 2 * math.pi
        ring.append(rot(cx + 9 * math.cos(th), 32 + 4 * math.sin(th)))
    poly(out, ring, "red2", "ink")
    inner = [rot(cx + 7 * math.cos(i / 16 * 2 * math.pi), 32 + 2.5 * math.sin(i / 16 * 2 * math.pi)) for i in range(16)]
    poly(out, inner, "ink", "red1")
    # ---- near arm trailing back
    sh_near = tuple(int(v) for v in rot(cx + 11, 40))
    arm(sh_near, (sh_near[0] + 9, sh_near[1] + 3 + (3 if a else 0)))
    # ---- speed lines streaming to the right
    for (y, x0, l, c) in (((18, 37, 9, "white"), (28, 40, 7, "grey4"), (39, 41, 6, "white")) if a else
                          ((22, 38, 8, "white"), (33, 41, 6, "grey4"), (44, 41, 6, "white"))):
        line(out, [(x0, y), (min(47, x0 + l), y)], c)
        px(out, x0 - 1, y, "grey3")
    return out


def boss_frame(kind):
    cx = 24
    if kind in ("idle_0", "idle_1"):
        d = 1 if kind == "idle_1" else 0
        return body_parts(cx, d, std_legs(cx), swing=(0, 0))
    if kind == "crouch_0":
        # low, knees bent out, arms swept back: coiled for the lunge
        dy = 9
        legs = [(cx - 15, 53, 63), (cx + 7, 53, 63)]
        im = body_parts(cx, dy, legs, arms=((cx - 20, 59), (cx + 20, 59)))
        # bent knees poking out at the sides
        for sx in (-1, 1):
            kx = cx + sx * 13 - 3
            rect(im, kx, 52, 7, 6, "blue1", "ink")
            vline(im, kx + 1, 53, 56, "blue2")
        return lean(im, -0.06)
    if kind in ("dash_0", "dash_1"):
        return dash_frame(kind == "dash_0")
    if kind in ("stun_0", "stun_1"):
        w = kind == "stun_0"
        dy = 6
        legs = [(cx - 12, 56, 63), (cx + 4, 56, 63)]
        im = body_parts(cx, dy, legs, arms=("down", "down"), swing=(3, 3) if w else (1, 5))
        im = lean(im, 0.16 if w else -0.16)
        # dizzy sparks wheeling above the empty collar
        pts = ((13, 30), (33, 26), (24, 21)) if w else ((15, 24), (34, 31), (23, 27))
        for (x, y) in pts:
            sparkle(im, x, y)
        return im
    # float: balloons tied to the wrists, body lifted, legs dangling
    f = kind == "float_1"
    dy = -7 + (1 if f else 0)
    legs = [(cx - 11, 47 + dy + 3, 58 + dy + 3 - 0), (cx + 2, 47 + dy + 3, 58 + dy + 3)]
    lh = (cx - 15, 33 + dy + (0 if f else 1))
    rh = (cx + 15, 33 + dy + (1 if f else 0))
    im = body_parts(cx, dy, legs, arms=(lh, rh))
    # balloons: 3 on the left wrist, 2 on the right (anchors tie to the hands)
    cols = ["red", "yellow", "blue", "green", "purple"]
    sway = 1 if f else 0
    spots = [(3 + sway, 1), (14 - sway, 0 + 1), (24 + sway, 0), (32 - sway, 1), (38 + sway, 3)]
    anchors = [(lh[0] - 1, lh[1] - 3), (lh[0] + 1, lh[1] - 4), (lh[0] + 2, lh[1] - 3),
               (rh[0] - 1, rh[1] - 4), (rh[0] + 1, rh[1] - 3)]
    for (bx, by), c, an in zip(spots, cols, anchors):
        string_to(im, bx + 5, by + 14, an[0], an[1], "grey4")
    for (bx, by), c in zip(spots, cols):
        paste(im, balloon_sprite(c).crop((0, 0, 10, 15)), bx, by)
    return im


BOSS_NAMES = ["idle_0", "idle_1", "crouch_0", "dash_0", "dash_1", "stun_0", "stun_1", "float_0", "float_1"]


# ====================================================================== RESIDENT
def thick(im, pts, c, w):
    d = draw(im)
    d.line(pts, fill=col(c), width=w)


def hand_long(im, x, y, dx=0, dy=1, spread=True):
    """Pale hand with long fingers pointing along (dx,dy), base at x,y."""
    for k, off in enumerate((-2, -1, 0, 1, 2) if spread else (-1, 0, 1)):
        for t in range(1, 6 - abs(off) // 2):
            fx = x + (off if dy else t * dx)
            fy = y + (t * dy if dy else off)
            if dy:
                fx = x + off + (off * t) // 3
            px(im, fx, fy, "ink" if t == 5 - abs(off) // 2 - 1 else "pale2")
    return im


def res_head(im, c, bob=0, hairsw=0, tilt=0):
    """Hair curtain: narrow skull, hair falling over the shoulders and chest."""
    ellipse(im, c - 5 + tilt, 2 + bob, c + 5 + tilt, 16 + bob, "ink2", "ink")
    # the curtain widens a little over the shoulders, ragged tips
    poly(im, [(c - 5 + tilt, 12 + bob), (c + 5 + tilt, 12 + bob), (c + 6, 27 + bob), (c - 6, 27 + bob)], "ink2", "ink")
    for k, hxx in enumerate((c - 6, c - 4, c - 2, c, c + 2, c + 4, c + 6)):
        l_ = 3 + (k * 5) % 4
        rect(im, hxx, 27 + bob, 1, l_, "ink")
    dither_grad(im, (c - 5, 4 + bob, c + 6, 28 + bob), "ink", "ink2", "x", 4, 0.15, 0.95,
                mk_mask([(c - 4 + tilt, 4 + bob), (c + 4 + tilt, 4 + bob), (c + 5, 27 + bob), (c - 5, 27 + bob)], im.size))
    for sx_, l_, o in ((-3, 16, 0), (-1, 20, 3), (2, 14, 1), (4, 17, 4)):
        for t in range(l_):
            if t % 3 != 2:
                px(im, c + sx_ + (hairsw if t > 10 else 0), 5 + bob + t + o, "grey1")
    px(im, c - 3, 4 + bob, "grey2"); px(im, c - 2, 3 + bob, "grey2")
    # a parting where a sliver of unhealthy skin shows
    px(im, c, 11 + bob, "pale1"); px(im, c, 12 + bob, "pale1")


def res_torso(im, c, bob=0):
    rect(im, c - 7, 17 + bob, 14, 25, "grey3", "ink")
    dither_grad(im, (c - 6, 18 + bob, c + 6, 41 + bob), "grey3", "grey2", "x", 4, 0.0, 0.85)
    hline(im, c - 6, c + 5, 18 + bob, "grey4")
    vline(im, c - 6, 19 + bob, 38 + bob, "grey4")
    vline(im, c, 20 + bob, 41 + bob, "ink2")
    for y in range(21 + bob, 41 + bob, 2):
        px(im, c + 1, y, "grey1")
    hline(im, c - 6, c + 5, 40 + bob, "grey1")
    hline(im, c - 6, c + 5, 41 + bob, "grey2")
    # faded stripe down the side of the jacket
    vline(im, c + 4, 20 + bob, 39 + bob, "grey4")


def res_legs(im, c, bob=0, dxl=0):
    for sx in (-1, 1):
        lx = c + sx * 3 - 1
        rect(im, lx, 40 + bob, 4, 20 - bob, "grey3", "ink")
        vline(im, lx + 1, 41 + bob, 58, "grey4")
        vline(im, lx + 2, 44 + bob, 58, "grey2")
        vline(im, lx + (3 if sx > 0 else 0), 41 + bob, 58, "grey2")
        sx0 = lx - 2 if sx < 0 else lx - 1
        rect(im, sx0, 60, 7, 4, "white", "ink")
        hline(im, sx0 + 1, sx0 + 5, 61, "grey4")
        hline(im, sx0 + 1, sx0 + 5, 62, "grey3")


def res_arm(im, x, top, out=0, droop=0):
    """Absurdly long arm: x is the shoulder column, hand hangs far below the knee."""
    rect(im, x, top, 3, 14, "grey3", "ink")
    x2 = x + out
    rect(im, x2, top + 13, 3, 20, "grey3", "ink")
    vline(im, x + 1, top + 1, top + 12, "grey4")
    vline(im, x2 + 1, top + 14, top + 30, "grey4")
    px(im, x2 + 1, top + 13, "grey2")
    hline(im, x2, x2 + 2, top + 28, "grey1")                     # cuff
    rect(im, x2, top + 33, 3, 3, "pale2", "ink")                   # hand
    for fi in range(3):
        rect(im, x2 + fi, top + 36, 1, 4 + (fi == 1), "pale1" if fi == 0 else "pale2")
        px(im, x2 + fi, top + 40 + (fi == 1), "ink")
    px(im, x2 + 3, top + 35, "ink"); px(im, x2 - 1, top + 35, "ink")


def res_body(dx=0, bob=0, sway=0, hairsw=0):
    """Front view. Tall thin tracksuit figure, face hidden by a hair curtain."""
    im = new(32, 64)
    c = 16 + dx
    res_legs(im, c, bob)
    res_arm(im, c - 10 - sway, 19 + bob, -sway)
    res_arm(im, c + 7 + sway, 19 + bob, sway)
    res_torso(im, c, bob)
    res_head(im, c, bob, hairsw)
    return im


def res_reach():
    im = new(32, 64)
    c = 21
    res_legs(im, c)
    res_arm(im, c + 7, 19, 1)
    res_torso(im, c)
    # the reaching arm: shoulder out to the far left, long fingers clawing
    thick(im, [(c - 6, 22), (c - 13, 27), (5, 29)], "ink", 5)
    thick(im, [(c - 6, 22), (c - 13, 27), (5, 29)], "grey3", 3)
    thick(im, [(c - 6, 21), (c - 13, 26), (6, 28)], "grey4", 1)
    rect(im, 2, 27, 4, 5, "pale2", "ink")
    for fy in (25, 27, 29, 31, 33):
        rect(im, 0, fy, 3, 1, "pale2")
        px(im, 0, fy, "ink")
    px(im, 1, 26, "ink"); px(im, 1, 28, "ink"); px(im, 1, 30, "ink"); px(im, 1, 32, "ink")
    res_head(im, c - 4, 1, 0, tilt=-1)
    return im


def res_run(phase):
    """Side view facing left, loping, arms dragging ahead and low."""
    im = new(32, 64)
    a = phase == 0
    hx, hy = (11, 22) if a else (13, 24)       # head centre
    sh = (14, 24)                              # shoulder
    hip = (19, 44) if a else (20, 45)
    # back leg
    bk = [(hip[0], hip[1]), (24 if a else 21, 53), (28 if a else 17, 61)]
    thick(im, bk, "ink", 6)
    thick(im, bk, "grey2", 4)
    thick(im, [(bk[0][0] - 1, bk[0][1]), (bk[1][0] - 1, bk[1][1])], "grey3", 1)
    rect(im, bk[2][0] - 3, 60, 7, 4, "white", "ink")
    # torso leaning forward-left
    poly(im, [(sh[0] - 5, sh[1] - 4), (sh[0] + 5, sh[1] - 4), (hip[0] + 5, hip[1]), (hip[0] - 5, hip[1])], "grey3", "ink")
    dither_grad(im, (hip[0] - 4, sh[1] - 3, hip[0] + 5, hip[1]), "grey3", "grey2", "x", 4, 0.1, 0.9, mk_mask([(sh[0] - 4, sh[1] - 3), (sh[0] + 4, sh[1] - 3), (hip[0] + 4, hip[1] - 1), (hip[0] - 4, hip[1] - 1)], im.size))
    line(im, [(sh[0] - 4, sh[1] - 3), (hip[0] - 4, hip[1] - 1)], "grey4")
    # front leg, long stride to the left
    fr = [(hip[0] - 1, hip[1]), (14 if a else 12, 52), (7 if a else 9, 61)] if a else [(hip[0] - 1, hip[1]), (14, 54), (13, 61)]
    thick(im, fr, "ink", 6)
    thick(im, fr, "grey3", 4)
    thick(im, [(fr[0][0] - 1, fr[0][1]), (fr[1][0] - 1, fr[1][1])], "grey4", 1)
    rect(im, fr[2][0] - 4, 60, 7, 4, "white", "ink")
    hline(im, fr[2][0] - 3, fr[2][0] + 1, 61, "grey4")
    # long arms swinging: one far forward, one trailing
    arm1 = [(sh[0] - 2, sh[1]), (4, 34) if a else (3, 40), (1, 46) if a else (2, 54)]
    thick(im, arm1, "ink", 5)
    thick(im, arm1, "grey3", 3)
    arm2 = [(sh[0] + 3, sh[1]), (25, 36) if a else (24, 33), (30, 50) if a else (29, 44)]
    thick(im, arm2, "ink", 5)
    thick(im, arm2, "grey2", 3)
    # long pale hands
    for (hxy, d) in ((arm1[2], -1), (arm2[2], 1)):
        rect(im, hxy[0] - 1, hxy[1], 3, 5, "pale2", "ink")
        for fi in (-1, 0, 1):
            px(im, hxy[0] + fi, hxy[1] + 5, "pale2"); px(im, hxy[0] + fi, hxy[1] + 6, "ink")
    # head + hair streaming back (to the right)
    ellipse(im, hx - 6, hy - 8, hx + 6, hy + 7, "ink2", "ink")
    for k, (ty, tl) in enumerate(((hy - 6, 12), (hy - 2, 15), (hy + 2, 11), (hy + 5, 8))):
        x0 = hx + 2 + (k % 2)
        poly(im, [(x0, ty), (x0 + tl, ty + 4 + (k % 2) * 3 + (0 if a else 2)), (x0 + 2, ty + 5)], "ink2", "ink")
    dither_grad(im, (hx - 5, hy - 7, hx + 6, hy + 7), "ink", "ink2", "x", 4, 0.2, 0.9, mk_mask([(hx - 5, hy - 5), (hx + 5, hy - 5), (hx + 5, hy + 6), (hx - 5, hy + 6)], im.size))
    px(im, hx - 4, hy - 5, "grey2"); px(im, hx - 3, hy - 6, "grey2"); px(im, hx - 2, hy - 2, "grey1")
    return im


def res_peek():
    im = new(32, 64)
    # sliver of pitch-black room behind a door edge
    rect(im, 12, 6, 8, 54, "ink")
    # door edge (steel, dim)
    rect(im, 8, 4, 4, 58, "grey2", "ink")
    vline(im, 9, 5, 60, "grey3")
    vline(im, 11, 6, 60, "grey1")
    # one red eye in the dark
    rect(im, 14, 21, 4, 3, "red1")
    rect(im, 14, 21, 4, 3, "red3")
    px(im, 14, 21, "red1"); px(im, 17, 23, "red1")
    px(im, 15, 22, "red4"); px(im, 16, 22, "yellow2")
    # pale hand curled around the edge: long fingers
    for k, fy in enumerate((33, 37, 41, 45)):
        rect(im, 5, fy, 6, 3, "pale2", "ink")
        hline(im, 6, 9, fy, "white")
        px(im, 4, fy + 1, "pale1")
        px(im, 4, fy, "ink"); px(im, 4, fy + 2, "ink")
    rect(im, 10, 32, 4, 17, "pale1", "ink")
    vline(im, 11, 33, 47, "pale2")
    rect(im, 11, 48, 3, 4, "pale1", "ink")
    return im


RES_NAMES = ["idle_0", "idle_1", "reach_0", "run_0", "run_1", "peek_0"]


def build_sprites():
    boss = [boss_frame(n) for n in BOSS_NAMES]
    for n, f in zip(BOSS_NAMES, boss):
        assert not off_palette(f), n
    sheet(boss, "props/suit_boss", BOSS_NAMES, cols=5)
    res = [res_body(0, 0, 0), res_body(1, 1, 1, hairsw=1), res_reach(), res_run(0), res_run(1), res_peek()]
    for n, f in zip(RES_NAMES, res):
        assert not off_palette(f), n
    sheet(res, "props/resident", RES_NAMES, cols=6)


# ====================================================================== SCISSOR STAIRWELL
def stair_layer():
    """Right-hand flight (x210..316, rising to the upper right) on its own layer."""
    L = new(W, H)
    RUN, RISE, X0, XM = 8, 7, 210, 316
    pts = [(X0, 150)]
    k = 0
    while True:
        xa = X0 + RUN * k
        yt = 150 - RISE * (k + 1)
        pts += [(xa, yt), (min(XM, xa + RUN), yt)]
        if xa + RUN >= XM:
            break
        k += 1
    pts.append((XM, 150))
    nk = k + 1
    dpoly(L, pts, "grey2", "grey1", 0.1, 0.9, "x", 4)
    sh = [(222, 147), (XM, 62), (XM, 150), (222, 150)]
    dither_grad(L, bbox(sh), "grey2", "ink2", "d", 2, 0.45, 0.85, mk_mask(sh, L.size))
    for k in range(nk):
        xa = X0 + RUN * k
        xb = min(XM - 1, xa + RUN - 1)
        yt = 150 - RISE * (k + 1)
        hline(L, xa, xb, yt, "grey4")
        hline(L, xa, xb, yt + 1, "grey3")
        vline(L, xa, yt + 1, yt + RISE, "ink")
        hline(L, xa, xb, yt + 2, "grey2")
        ovl(L, (xa + 1, yt + 2, xb + 1, yt + RISE), "ink2", 0.35, 2)
        px(L, xa + 1, yt + 2, "grey4")
        for t in range(0, RUN, 2):                    # edge tape
            px(L, xa + t, yt, "yellow" if k < 3 else "grey4")
    poly(L, pts, None, "ink")
    # handrail rising with the flight, balusters every other step
    for k in range(nk):
        xa = X0 + RUN * k
        yt = 150 - RISE * (k + 1)
        ry = yt - 30
        for t in range(RUN):
            xx = xa + t
            yy = ry - round(t * RISE / RUN)
            if xx <= XM and yy >= 20:
                px(L, xx, yy, "grey4"); px(L, xx, yy + 1, "ink")
        if k % 2 == 0 and xa + 1 <= XM:
            vline(L, xa + 1, max(20, ry + 2), yt - 1, "grey2")
    # newel post at the foot of the flight
    rect(L, 204, 112, 4, 38, "grey2", "ink")
    vline(L, 205, 113, 148, "grey3")
    rect(L, 203, 109, 6, 3, "grey3", "ink")
    return L


def bulb(im, bx, by):
    """Big caged bulb centred on (bx, by): 12x14 wire cage, bright yellow2/white glass."""
    vline(im, bx, Y0, by - 8, "ink")                      # cable
    vline(im, bx + 1, Y0, by - 8, "grey1")
    rect(im, bx - 4, by - 8, 9, 3, "grey1", "ink")        # ceiling socket
    hline(im, bx - 3, bx + 2, by - 7, "grey3")
    # glass
    ellipse(im, bx - 4, by - 5, bx + 4, by + 5, "yellow2", "yellow")
    rect(im, bx - 2, by - 3, 5, 6, "white")
    px(im, bx - 3, by - 4, "white")
    # cage: 12 wide x 14 tall, ink frame, grey bars over the bulb
    rect(im, bx - 6, by - 7, 12, 14, None, "ink")
    for vx in (bx - 3, bx, bx + 3):
        vline(im, vx, by - 6, by + 5, "grey2")
    for hy in (by - 3, by + 1, by + 4):
        hline(im, bx - 5, bx + 4, hy, "grey2")
    px(im, bx - 6, by - 7, "grey1"); px(im, bx + 5, by - 7, "grey1")
    hline(im, bx - 6, bx + 5, by + 7, "grey1")
    for (mx, my) in ((bx - 14, by + 12), (bx + 12, by + 16), (bx + 15, by - 2)):
        px(im, mx, my, "grey4"); px(im, mx + 1, my - 1, "grey3")


def light_cone(im, bx, by, ybot=138, half=54):
    """Dithered cone of light from the bulb down over its flight."""
    y0 = by + 8
    pts = [(bx - 6, y0), (bx + 6, y0), (bx + half, ybot), (bx - half, ybot)]
    m = mk_mask(pts, im.size)
    cc = col("yellow2"); c2 = col("white")
    for y in range(y0, ybot):
        f = (y - y0) / (ybot - y0)
        for x in range(max(0, bx - half), min(W, bx + half + 1)):
            if m.getpixel((x, y)) and im.getpixel((x, y))[:3] != PAL["ink"]:
                lv = 0.62 * (1 - f) ** 0.8
                edge = abs(x - bx) / (6 + (half - 6) * f)       # 0 centre .. 1 edge
                lv *= 1 - 0.55 * edge ** 2
                if lv > _thr(x, y, 4):
                    im.putpixel((x, y), c2 if lv > 0.5 else cc)
    # cone edges: a thin dithered line so the shape is readable
    for t in range(0, ybot - y0, 2):
        f = t / (ybot - y0)
        for sx in (-1, 1):
            xx = int(bx + sx * (6 + (half - 6) * f))
            if 0 <= xx < W and im.getpixel((xx, y0 + t))[:3] != PAL["ink"] and f < 0.8:
                px(im, xx, y0 + t, "yellow2")


def flyer(im, fx, fy, fw, fh, fc):
    rect(im, fx, fy, fw, fh, fc, "ink")
    for ly in range(fy + 3, fy + fh - 2, 3):
        hline(im, fx + 1, fx + fw - 3, ly, "grey2")
    px(im, fx + fw - 1, fy, "grey3"); px(im, fx + fw - 1, fy + 1, "ink")
    px(im, fx, fy + fh - 1, "grey3")


def build_scissor():
    im = new(W, H, "ink")
    FT = 140
    # cold concrete wall
    dither_ramp(im, (0, Y0, W, FT), ["ink2", "grey1", "grey2", "grey1"], "y", 4)
    ovl(im, (0, Y0, W, FT), "blue0", 0.18, 4)
    for sx in range(0, W, 46):
        vline(im, sx, Y0, FT - 1, "grey1")
    for sy in (52, 84, 112):
        hline(im, 0, W - 1, sy, "grey1")
    speckle(im, (0, Y0, W, FT), "grey3", 70, 15, "grey2")
    speckle(im, (0, Y0, W, FT), "ink2", 60, 16)
    # painted dado
    rect(im, 0, 100, W, FT - 100, "grey1")
    dither_grad(im, (0, 101, W, FT), "grey2", "ink2", "y", 4, 0.0, 0.9)
    ovl(im, (0, 101, W, FT), "blue0", 0.2, 4)
    hline(im, 0, W - 1, 99, "ink"); hline(im, 0, W - 1, 100, "grey3"); hline(im, 0, W - 1, 101, "grey2")
    hline(im, 0, W - 1, FT - 1, "ink")
    # bulb light pools (cold)
    for bx in (57, 263):
        dither_radial(im, bx, 46, 62, "grey3", None, 4, box=(max(0, bx - 62), Y0, min(W, bx + 63), 128))
        dither_radial(im, bx, 46, 34, "grey4", None, 4)
        dither_radial(im, bx, 42, 14, "white", None, 4)
    # landing floor
    floor_band(im, FT, 158, "grey1", "grey2", "ink2", "grey3", 28, 9)
    glow(im, 112, FT + 1, 208, 158, "grey3", 0.3, 4, 20)

    # ---- centre wall x120..200
    # horizontal pipe along the ceiling + vertical drop
    rect(im, 0, 28, W, 4, "grey2", "ink")
    hline(im, 1, W - 2, 29, "grey3")
    for bx in (14, 56, 98, 224, 266, 300):
        rect(im, bx, 26, 3, 8, "grey1", "ink")
    rect(im, 120, Y0, 5, FT - Y0, "grey2", "ink")
    vline(im, 121, Y0 + 1, FT - 2, "grey3")
    for by_ in (44, 76, 112):
        rect(im, 118, by_, 9, 3, "grey1", "ink")
    ellipse(im, 122 - 4, 92 - 4, 122 + 4, 92 + 4, None, "red2"); px(im, 122, 92, "red3")
    # big pale painted rectangle (x128..192, y40..76) for the floor number
    rect(im, 128, 40, 65, 37, "grey4")
    dither_grad(im, (128, 40, 193, 77), "grey4", "wall3", "y", 4, 0.0, 0.55)
    for (ex, ey) in ((128, 46), (128, 60), (192, 52), (192, 68), (140, 76), (170, 76), (156, 40)):
        px(im, ex, ey, "grey2")
    ovl(im, (128, 40, 193, 41), "grey3", 0.5, 4); ovl(im, (128, 76, 193, 77), "grey3", 0.5, 4)
    ovl(im, (128, 40, 129, 77), "grey3", 0.5, 4); ovl(im, (192, 40, 193, 77), "grey3", 0.5, 4)
    for dx_, dl in ((134, 8), (151, 4), (180, 10)):
        vline(im, dx_, 77, 77 + dl, "grey4")
    streaks(im, (129, 41, 192, 76), "grey3", 6, 40, 16, 0.5, "grey4")
    streaks(im, (110, 30, 210, 99), "ink2", 12, 41, 22, 0.6, "grey2")
    # peeling flyers
    for f in ((133, 86, 11, 15, "yellow2"), (146, 91, 9, 12, "wall4"), (176, 84, 12, 16, "white"), (190, 94, 7, 11, "blue4")):
        flyer(im, *f)
    px(im, 138, 86, "red3"); px(im, 181, 84, "red3")
    # breaker box + fire bell
    rect(im, 150, 108, 14, 20, "grey3", "ink")
    rect(im, 152, 110, 10, 16, "grey2", "ink")
    hline(im, 153, 160, 114, "ink")
    for ly in (117, 120, 123):
        hline(im, 154, 159, ly, "grey4")
    rect(im, 156, 111, 2, 2, "red3")
    ellipse(im, 184, 108, 192, 116, "red2", "ink"); px(im, 187, 110, "red4"); px(im, 188, 112, "red1")
    # a mop bucket and a wedged box on the landing
    rect(im, 128, 142, 10, 8, "blue2", "ink"); hline(im, 129, 136, 143, "blue3")
    line(im, [(135, 142), (138, 128)], "brown3")
    rect(im, 178, 140, 14, 10, "brown3", "ink"); hline(im, 179, 190, 144, "brown2"); rect(im, 183, 140, 4, 3, "yellow2")

    # ---- both flights
    L = stair_layer()
    im.alpha_composite(L)
    im.alpha_composite(flip(L))
    # dark crawl-space gaps under each flight foot
    for gx in (96, 214):
        pass

    # ---- brighten the scene a little so the stairs read
    ovl(im, (0, Y0, W, 158), "grey1", 0.5, 2, only="ink2")
    ovl(im, (0, Y0, W, 158), "grey2", 0.3, 4, only="grey1")
    ovl(im, (0, Y0, W, 158), "grey3", 0.2, 4, only="grey2")
    # ---- caged bulbs over each flight, each with a light cone onto its stairs
    for bx in (57, 263):
        light_cone(im, bx, 40)
    bulb(im, 57, 40)
    bulb(im, 263, 40)

    # floor number slot hint: nothing (game writes it). vignette
    ovl(im, (0, Y0, 8, FT), "ink", 0.3, 2)
    ovl(im, (312, Y0, 320, FT), "ink", 0.3, 2)
    ovl(im, (0, FT, W, 158), "ink2", 0.2, 4)
    letterbox(im)
    return im


# ====================================================================== ROOF
def building(im, x, y0, w, base, c, windows=None, seed=0, lit=0.12, wc=("yellow", "orange3", "yellow2")):
    rect(im, x, y0, w, base - y0, c, "ink")
    if windows:
        rnd = random.Random(seed)
        for wy in range(y0 + 4, base - 3, 5):
            for wx in range(x + 3, x + w - 3, 4):
                if rnd.random() < lit:
                    rect(im, wx, wy, 2, 2, rnd.choice(wc))
                elif rnd.random() < 0.25:
                    px(im, wx, wy, windows)


def build_roof():
    im = new(W, H, "ink")
    CAP = 143
    # pre-dawn sky: blue-violet at the top, pale at the horizon
    dither_ramp(im, (0, Y0, W, 138), ["purple0", "purple1", "purple2", "blue3", "blue4"], "y", 4)
    dither_grad(im, (0, 100, W, 140), "blue3", "wall4", "y", 4, 0.0, 0.45)
    rnd = random.Random(7)
    for _ in range(26):
        px(im, rnd.randint(0, W - 1), rnd.randint(Y0 + 1, 60), rnd.choice(["white", "grey4", "blue4"]))
    px(im, 214, 36, "white"); px(im, 213, 36, "grey4"); px(im, 215, 36, "grey4"); px(im, 214, 35, "grey4"); px(im, 214, 37, "grey4")
    # thin cloud streaks
    for (cx_, cy_, l_) in ((40, 70, 60), (190, 58, 70), (262, 84, 40)):
        for t in range(l_):
            if (t // 2) % 2 == 0:
                px(im, cx_ + t, cy_ + (t // 14), "purple2" if cy_ > 65 else "purple1")
    # far skyline (pale violet) and near skyline (dark)
    far = [(0, 96, 18), (16, 108, 14), (28, 88, 16), (42, 104, 20), (60, 94, 12), (70, 110, 18), (86, 100, 14),
           (98, 86, 12), (108, 106, 20), (126, 96, 16), (140, 112, 14), (152, 90, 18), (168, 104, 14), (180, 98, 16),
           (194, 84, 12), (204, 108, 20), (222, 94, 14), (234, 102, 18), (250, 88, 14), (262, 110, 18), (278, 98, 16),
           (292, 106, 14), (304, 92, 16)]
    for (x, y, w) in far:
        rect(im, x, y, w, 144 - y, "purple1", "ink")
        dither_grad(im, (x + 1, y + 1, x + w - 1, 143), "purple1", "purple2", "y", 4, 0.0, 0.7)
    near = [(0, 116, 22), (20, 108, 18), (38, 120, 16), (92, 112, 24), (116, 100, 20), (134, 118, 26), (160, 110, 18),
            (178, 122, 24), (202, 106, 20), (222, 116, 22), (242, 124, 20), (262, 104, 24), (286, 114, 18), (304, 108, 16)]
    for i, (x, y, w) in enumerate(near):
        building(im, x, y, w, 144, "blue0", "blue1", 20 + i, 0.14)
        hline(im, x + 1, x + w - 2, y + 1, "blue1")
    # a few lit windows in the far layer, antenna blinkers on near buildings
    for (x, y) in ((33, 92), (73, 114), (102, 90), (158, 94), (198, 88), (255, 92), (297, 96)):
        px(im, x, y, "yellow2")
    for (x, y) in ((127, 99), (213, 105), (275, 103)):
        vline(im, x, y - 7, y, "ink"); px(im, x, y - 8, "red3")
    # horizon haze over the lower skyline (pale, dithered)
    glow(im, 0, 118, W, 143, "blue3", 0.35, 4, 4, up=True)

    # ---- parapet back wall with railing
    for x in range(0, W, 20):
        vline(im, x, 126, CAP - 1, "ink2"); vline(im, x + 1, 126, CAP - 1, "grey2")
    hline(im, 0, W - 1, 126, "ink"); hline(im, 0, W - 1, 127, "grey3")
    # concrete cap (ledge) + wall face
    rect(im, 0, CAP, W, 4, "grey3", "ink")
    hline(im, 0, W - 1, CAP + 1, "grey4")
    for x in range(0, W, 9):
        px(im, x, CAP + 2, "grey2")
    rect(im, 0, CAP + 4, W, 4, "grey1")
    dither_grad(im, (0, CAP + 4, W, 151), "grey2", "grey1", "y", 4, 0.0, 0.8)
    for x in range(14, W, 36):
        vline(im, x, CAP + 4, 150, "ink2")
    speckle(im, (0, CAP + 4, W, 150), "grey3", 24, 41)

    # ---- roof floor
    floor_band(im, 150, 158, "grey1", "ink2", "ink2", "grey2", 24, 51)
    hline(im, 0, W - 1, 150, "ink")
    # puddle reflecting the pale sky
    ellipse(im, 112, 152, 178, 156, "blue1")
    for (x0_, x1_, y_) in ((120, 140, 153), (146, 168, 154), (126, 134, 155)):
        hline(im, x0_, x1_, y_, "blue3")
    px(im, 118, 153, "blue4"); px(im, 150, 153, "blue4")

    # ---- stair hut (left) with the rooftop door x20..56
    rect(im, 8, 78, 66, 72, "grey2", "ink")
    dither_grad(im, (9, 79, 73, 150), "grey3", "grey1", "x", 4, 0.0, 0.9)
    ovl(im, (9, 79, 73, 150), "purple1", 0.18, 4)
    for sy in (92, 112, 130):
        hline(im, 9, 72, sy, "grey1")
    rect(im, 4, 74, 74, 6, "grey3", "ink")         # roof slab
    hline(im, 5, 76, 75, "grey4")
    hline(im, 5, 76, 79, "grey1")
    # water stains on the hut
    streaks(im, (9, 80, 73, 140), "ink2", 8, 61, 22, 0.6)
    # door frame + door (x20..56, bottom y150)
    rect(im, 18, 92, 40, 59, "grey1", "ink")
    rect(im, 20, 94, 36, 56, "blue1", "ink")
    dither_grad(im, (21, 95, 55, 149), "blue2", "blue0", "x", 4, 0.0, 0.85)
    hline(im, 21, 54, 95, "blue3"); vline(im, 21, 96, 148, "blue3")
    rect(im, 40, 99, 12, 16, "ink", "ink")         # wire window
    dither_grad(im, (41, 100, 51, 114), "blue1", "blue0", "d", 4, 0.0, 1.0)
    for gy in (103, 107, 111):
        hline(im, 41, 50, gy, "grey1")
    for gx in (44, 48):
        vline(im, gx, 100, 114, "grey1")
    rect(im, 24, 124, 4, 10, "grey3", "ink")       # handle
    rect(im, 50, 94, 6, 4, "grey1", "ink")
    rect(im, 20, 140, 36, 10, "blue1", "ink")      # kick plate
    hline(im, 21, 54, 141, "blue2")
    for hy in (100, 122, 140):
        rect(im, 54, hy, 2, 4, "grey1", "ink")
    rect(im, 20, 148, 36, 2, "grey1", "ink")
    # lamp over the door (warm) + sign
    rect(im, 31, 84, 14, 6, "green0", "ink"); rect(im, 32, 85, 12, 4, "green1")
    text(im, 38, 83, "옥상", "white", 9, align="center") if False else None
    px(im, 34, 87, "green3"); px(im, 36, 87, "green3"); px(im, 38, 87, "green3"); px(im, 40, 87, "green3")
    rect(im, 62, 94, 6, 8, "grey1", "ink"); px(im, 64, 96, "orange3"); px(im, 64, 99, "orange3")
    dither_radial(im, 65, 98, 9, "orange3", None, 4, box=(56, 88, 75, 110))
    rect(im, 62, 94, 6, 8, "grey1", "ink"); px(im, 64, 96, "yellow2"); px(im, 64, 99, "yellow2")
    # vent pipes + chimney on the roof slab
    rect(im, 14, 64, 8, 10, "grey2", "ink"); rect(im, 12, 62, 12, 3, "grey3", "ink")
    rect(im, 60, 68, 5, 6, "grey2", "ink"); rect(im, 58, 66, 9, 3, "grey3", "ink")
    # TV antenna on the hut
    vline(im, 41, 44, 74, "ink"); vline(im, 42, 44, 74, "grey2")
    for (ay, al) in ((46, 9), (52, 11), (58, 13), (64, 11)):
        hline(im, 42 - al // 2, 42 + al // 2, ay, "ink"); hline(im, 42 - al // 2 + 1, 42 + al // 2 - 1, ay, "grey3")
    px(im, 42, 43, "red3")

    # ---- water tank (centre-left) on a steel frame
    tx0, tx1 = 96, 148
    for lx in (tx0 + 4, tx1 - 7):
        rect(im, lx, 118, 3, 32, "grey1", "ink")
        vline(im, lx + 1, 119, 148, "grey2")
    line(im, [(tx0 + 5, 126), (tx1 - 6, 144)], "grey1"); line(im, [(tx1 - 6, 126), (tx0 + 5, 144)], "grey1")
    rect(im, tx0 + 2, 135, tx1 - tx0 - 4, 2, "grey1", "ink")
    rect(im, tx0, 118, tx1 - tx0, 4, "grey1", "ink")                    # base ring
    # drum
    rect(im, tx0 + 1, 84, tx1 - tx0 - 2, 35, "grey3", "ink")
    dither_grad(im, (tx0 + 2, 85, tx1 - 1, 118), "blue3", "blue1", "x", 4, 0.0, 0.95)
    ovl(im, (tx0 + 2, 85, tx1 - 1, 118), "purple1", 0.15, 4)
    for by_ in (94, 108):
        rect(im, tx0 + 1, by_, tx1 - tx0 - 2, 2, "grey2", "ink")
        hline(im, tx0 + 2, tx1 - 3, by_, "grey4")
    vline(im, tx0 + 4, 86, 117, "blue4"); vline(im, tx0 + 5, 88, 100, "blue4")
    poly(im, [(tx0 + 1, 84), (tx0 + 6, 76), (tx1 - 7, 76), (tx1 - 1, 84)], "grey3", "ink")
    hline(im, tx0 + 8, tx1 - 9, 77, "grey4")
    rect(im, 118, 70, 8, 7, "grey2", "ink")                              # hatch
    rect(im, 120, 67, 4, 4, "grey1", "ink")
    # ladder up the side
    vline(im, tx1 + 3, 84, 148, "ink"); vline(im, tx1 + 8, 84, 148, "ink")
    for ly in range(88, 148, 5):
        hline(im, tx1 + 3, tx1 + 8, ly, "grey2")
    vline(im, tx1 + 4, 85, 147, "grey1")
    # water pipe down to the floor
    rect(im, tx0 + 20, 122, 3, 28, "grey2", "ink"); rect(im, tx0 + 17, 144, 9, 3, "grey1", "ink")
    # dripping valve puddle
    px(im, tx0 + 21, 150, "blue3")

    # ---- radio mast (far right of centre) with a red blinker and guy wires
    mx = 204
    vline(im, mx, 46, CAP, "ink"); vline(im, mx + 1, 46, CAP, "grey2"); vline(im, mx - 1, 46, CAP, "ink")
    for my in range(52, CAP, 8):
        line(im, [(mx - 1, my), (mx + 2, my + 8)], "grey1")
    hline(im, mx - 6, mx + 7, 60, "ink"); hline(im, mx - 4, mx + 5, 68, "ink"); hline(im, mx - 7, mx + 8, 76, "ink")
    px(im, mx, 45, "red3"); px(im, mx + 1, 45, "red3")
    dither_radial(im, mx, 45, 8, "red3", None, 4)
    px(im, mx, 45, "red4")
    line(im, [(mx, 50), (mx - 22, CAP)], "grey1"); line(im, [(mx + 1, 50), (mx + 22, CAP)], "grey1")

    # ---- satellite dish + AC units (right)
    ellipse(im, 284, 108, 300, 124, "grey4", "ink")
    ellipse(im, 286, 110, 298, 122, "grey3")
    dither_grad(im, (286, 110, 299, 123), "grey3", "grey2", "d", 4, 0.0, 1.0, mk_mask([(288, 111), (297, 111), (298, 121), (288, 122)], im.size))
    vline(im, 292, 116, 141, "ink"); px(im, 292, 113, "ink")
    line(im, [(300, 106), (294, 116)], "ink")
    for (ax, ay, aw) in ((266, 128, 26), (294, 134, 20)):
        rect(im, ax, ay, aw, 22 - (ay - 128) + 0, "grey3", "ink")
        dither_grad(im, (ax + 1, ay + 1, ax + aw - 1, 149), "grey3", "grey1", "x", 4, 0.0, 0.8)
        hline(im, ax + 1, ax + aw - 2, ay + 1, "grey4")
        cxx = ax + aw // 2
        ellipse(im, cxx - 6, ay + 5, cxx + 6, ay + 17, "ink2", "ink")
        for fy_ in (ay + 8, ay + 11, ay + 14):
            hline(im, cxx - 4, cxx + 4, fy_, "grey1")
        vline(im, cxx, ay + 6, ay + 16, "grey1")
        rect(im, ax + 2, 149, 3, 1, "ink"); rect(im, ax + aw - 5, 149, 3, 1, "ink")
    # cables from hut to mast along the sky
    line(im, [(66, 70), (130, 74), (204, 52)], "ink")

    # ---- the flip phone, open, on the ledge (x244..256, y136..142)
    # screen half
    rect(im, 244, 136, 6, 7, "grey2", "ink")
    rect(im, 245, 137, 4, 4, "blue0")
    px(im, 245, 137, "blue1"); px(im, 246, 138, "blue1")
    hline(im, 245, 141, 141, "grey3") if False else None
    # key half
    rect(im, 250, 136, 7, 7, "grey4", "ink")
    for ky in (138, 140):
        for kx in (252, 254):
            px(im, kx, ky, "ink2")
    px(im, 251, 137, "grey4"); px(im, 255, 137, "grey4")
    px(im, 250, 138, "ink"); px(im, 250, 140, "ink")   # hinge
    # vignette
    ovl(im, (0, Y0, 10, 151), "ink", 0.2, 2)
    ovl(im, (310, Y0, 320, 151), "ink", 0.2, 2)
    letterbox(im)
    return im


# ====================================================================== MILK DEPOT
def carton(im, x, y, c="blue2", label="white"):
    """6x10 milk carton: gable top, coloured label band."""
    rect(im, x, y + 2, 6, 8, "white", "ink")
    for gx in (x + 1, x + 4):
        px(im, gx, y + 1, "ink")
    px(im, x + 2, y, "ink"); px(im, x + 3, y, "ink"); px(im, x + 2, y + 1, "grey4"); px(im, x + 3, y + 1, "grey4")
    rect(im, x + 1, y + 5, 4, 3, c)
    px(im, x + 1, y + 3, "white"); px(im, x + 4, y + 9, "grey3")


def milk_crate(im, x, y, flavours, empty=False):
    """20x7 plastic crate with 3 cartons poking out above (cartons first, crate in front)."""
    if not empty:
        for i, c in enumerate(flavours[:3]):
            carton(im, x + 1 + i * 6, y - 9, c)
    rect(im, x, y, 20, 8, "blue2", "ink")
    hline(im, x + 1, x + 18, y + 1, "blue3")
    for sx in range(x + 3, x + 18, 5):
        rect(im, sx, y + 3, 3, 2, "blue0")
    hline(im, x + 1, x + 18, y + 6, "blue1")


def cooler(im):
    ux, uy, uw, uh = 14, 50, 99, 78
    obox(im, ux + 14, 37, 70, 12, "blue1", "blue2")
    text(im, ux + 14 + 35, 38, "냉장 선반", "white", 9, align="center")
    line(im, [(ux + 18, 49), (ux + 18, 50)], "ink")
    line(im, [(ux + 79, 49), (ux + 79, 50)], "ink")
    rect(im, ux, uy, uw, uh, "grey4", "ink")
    rect(im, ux + 1, uy + 1, uw - 2, 1, "white")
    vline(im, ux + 1, uy + 1, uy + uh - 2, "white")
    vline(im, ux + uw - 2, uy + 2, uy + uh - 2, "grey3")
    dither_grad(im, (ux + 2, uy + 2, ux + uw - 2, uy + uh - 1), "grey4", "blue3", "y", 4, 0.0, 0.4)
    cw, ch, gp = 95, 23, 3
    fl = [["blue2", "blue2", "blue2", "blue2"], ["red3", "red3", "blue2", "blue2"], ["yellow", "yellow", "blue2", "orange2"],
          ["brown1", "brown1", "blue2", "blue2"], ["blue2", "red3", "yellow", "brown1"], ["blue2", "blue2", "blue2", "blue2"]]
    for r in range(3):
        cx = ux + 2
        cy = uy + 2 + r * (ch + gp) + (1 if r else 0)
        rect(im, cx, cy, cw, ch, "blue0", "ink")
        dither_grad(im, (cx + 1, cy + 1, cx + cw - 1, cy + ch - 1), "blue1", "blue0", "y", 2, 0.0, 0.45)
        hline(im, cx + 1, cx + cw - 2, cy + 1, "blue4")              # LED strip
        glow(im, cx + 1, cy + 2, cx + cw - 1, cy + 9, "blue3", 0.45, 4, 6)
        hline(im, cx + 1, cx + cw - 2, cy + ch - 2, "grey3")        # shelf lip
        for k in range(4):
            x0 = cx + 3 + k * 23
            n = r * 4 + k
            milk_crate(im, x0, cy + ch - 10, fl[(n + r) % 6], empty=(n == 5 or n == 10))
        # frost on the glass front (dither)
        ovl(im, (cx + 1, cy + 1, cx + cw - 1, cy + ch - 1), "white", 0.10, 4)
        # price tag on lip
        rect(im, cx + 6 + r * 11, cy + ch - 3, 7, 2, "yellow", "ink")
    # little temperature LED
    rect(im, ux + 88, 38, 10, 8, "ink", "ink")
    for k in range(3):
        px(im, ux + 90 + k * 2, 41, "green2")
    px(im, ux + 90, 43, "red3")
    # legs / kickplate
    rect(im, ux + 2, uy + uh, 6, 8, "grey2", "ink")
    rect(im, ux + uw - 8, uy + uh, 6, 8, "grey2", "ink")
    hline(im, ux + 3, ux + 6, uy + uh + 1, "grey3")
    ovl(im, (ux + 2, FLOOR_TOP + 1, ux + uw + 6, FLOOR_TOP + 7), "ink", 0.45, 2)


def depot_counter(im):
    dither_radial(im, 169, 96, 48, "wall1", None, 4, box=(124, 38, 214, 118))
    for chx in (138, 200):
        vline(im, chx, 34, 55, "grey1")
        for yy in range(36, 55, 3):
            px(im, chx - 1, yy, "grey2")
    obox(im, 128, 55, 83, 24, "blue1", "blue2", "blue0")
    rect(im, 130, 57, 79, 20, "blue0", "ink")
    dither_grad(im, (131, 58, 208, 76), "blue1", "blue0", "y", 4, 0.0, 0.8)
    text(im, 170, 61, "해달우유 대리점", "white", 9, shadow="ink", align="center")
    hline(im, 133, 206, 74, "blue3")
    for sx in range(137, 206, 9):
        px(im, sx, 75, "white")
    # counter body
    rect(im, 132, 118, 75, 24, "brown2", "ink")
    rect(im, 133, 119, 73, 4, "white", None)
    hline(im, 133, 205, 119, "white")
    hline(im, 133, 205, 122, "grey3")
    hline(im, 132, 206, 123, "ink")
    dither_grad(im, (133, 124, 206, 141), "brown2", "brown1", "y", 4, 0.0, 0.7)
    for vx in range(144, 206, 12):
        vline(im, vx, 124, 138, "brown1")
        px(im, vx - 1, 125, "brown3")
    rect(im, 133, 138, 73, 3, "ink2")
    hline(im, 133, 205, 138, "grey1")
    rect(im, 150, 128, 20, 6, "brown1", "ink")
    hline(im, 151, 168, 129, "brown2")
    rect(im, 158, 131, 4, 2, "orange3")
    rect(im, 186, 127, 8, 10, "white", "ink")
    hline(im, 188, 192, 130, "grey3"); hline(im, 188, 192, 132, "grey3"); hline(im, 188, 191, 134, "grey3")
    # order printer
    rect(im, 139, 108, 20, 10, "grey4", "ink")
    hline(im, 140, 157, 109, "white")
    rect(im, 141, 111, 12, 2, "ink2")
    rect(im, 155, 111, 2, 2, "red3")
    rect(im, 144, 104, 10, 4, "white", "ink")
    hline(im, 145, 152, 106, "grey3")
    rect(im, 143, 118, 9, 6, "white", "ink")
    hline(im, 145, 150, 120, "grey3"); hline(im, 145, 148, 122, "grey3")
    hline(im, 143, 151, 123, "grey2")
    # monitor
    rect(im, 175, 114, 10, 4, "grey2", "ink")
    rect(im, 178, 111, 4, 4, "grey1", "ink")
    rect(im, 164, 94, 32, 19, "grey4", "ink")
    hline(im, 165, 193, 95, "white")
    rect(im, 166, 96, 28, 14, "blue0", "ink")
    rect(im, 167, 97, 26, 3, "blue1")
    for ry in (102, 105, 108):
        hline(im, 168, 191, ry, "blue1")
    vline(im, 177, 100, 109, "blue1")
    px(im, 169, 98, "green2"); px(im, 171, 98, "grey3")
    px(im, 192, 112, "green2")
    glow(im, 164, 114, 197, 119, "blue3", 0.3, 4, 4)
    # milk cartons stacked on the counter + pen cup
    carton(im, 196, 108, "blue2"); carton(im, 201, 108, "red3"); carton(im, 198, 99, "blue2")
    rect(im, 160, 112, 3, 6, "white", "ink")
    px(im, 161, 110, "red2"); px(im, 162, 109, "blue2")
    rect(im, 196, 96, 5, 5, "yellow2", "ink")
    ovl(im, (130, FLOOR_TOP + 4, 211, FLOOR_TOP + 9), "ink", 0.5, 2)
    ovl(im, (130, FLOOR_TOP + 4, 211, FLOOR_TOP + 7), "ink", 0.5, 4)


def clock4(im, cx, cy, r):
    ellipse(im, cx - r, cy - r, cx + r, cy + r, "grey1", "ink")
    ellipse(im, cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, "white", "grey3")
    for k in range(12):
        a = k * math.pi / 6
        px(im, round(cx + math.sin(a) * (r - 2)), round(cy - math.cos(a) * (r - 2)), "ink")
    line(im, [(cx, cy), (cx, cy - (r - 3))], "ink")                       # minute: 12
    a = math.radians(120)
    line(im, [(cx, cy), (cx + round(math.sin(a) * (r - 4)), cy - round(math.cos(a) * (r - 4)))], "ink")  # hour: 4
    px(im, cx, cy, "red2")


def hang_bag(im, hx, y, c, cs, ch):
    """insulated delivery bag hanging from a hook at hx (16x14)."""
    line(im, [(hx - 4, y + 3), (hx - 4, y), (hx + 4, y), (hx + 4, y + 3)], "ink")
    rect(im, hx - 8, y + 3, 17, 12, c, "ink")
    rect(im, hx - 7, y + 4, 15, 2, ch)
    hline(im, hx - 7, hx + 7, y + 7, cs)
    rect(im, hx - 7, y + 11, 15, 3, cs)
    rect(im, hx - 2, y + 8, 5, 4, "white", "ink")
    px(im, hx, y + 9, "blue2"); px(im, hx, y + 10, "blue2")


def build_depot():
    im = new(W, H, "ink")
    dither_ramp(im, (0, 34, W, FLOOR_TOP), ["grey4", "wall3", "wall3", "grey3"], "y", 4)
    for sx in range(6, W, 38):
        vline(im, sx, 36, FLOOR_TOP - 1, "grey3")
        vline(im, sx + 1, 36, FLOOR_TOP - 1, "grey4")
    # steel wainscot with blue milk-tile band
    rect(im, 0, 120, W, 18, "grey2")
    dither_grad(im, (0, 121, W, 137), "grey3", "grey1", "y", 4, 0.0, 0.8)
    hline(im, 0, W - 1, 120, "ink"); hline(im, 0, W - 1, 121, "grey4")
    for sx in range(0, W, 19):
        vline(im, sx, 122, 137, "grey1"); px(im, sx + 1, 124, "grey3")
    hline(im, 0, W - 1, 137, "ink2")
    # ceiling
    rect(im, 0, Y0, W, 13, "ink2")
    dither_grad(im, (0, Y0, W, 35), "ink", "ink2", "y", 4, 0.0, 1.0)
    for sx in range(0, W, 32):
        vline(im, sx, Y0, 34, "ink")
    hline(im, 0, W - 1, 35, "ink"); hline(im, 0, W - 1, 36, "grey2")
    tube(im, 22, 104, 29); tube(im, 126, 212, 29); tube(im, 232, 262, 29, on=False)
    for vx in range(268, 306, 4):
        vline(im, vx, 26, 33, "ink")
    # floor
    floor_band(im, FLOOR_TOP, 158, "grey2", "grey3", "grey1", "grey4", 20, 5)
    glow(im, 10, FLOOR_TOP + 1, 118, 156, "grey4", 0.35, 4, 16)
    glow(im, 130, FLOOR_TOP + 1, 214, 156, "wall1", 0.4, 4, 16)
    ovl(im, (0, 150, W, 158), "grey1", 0.25, 4)
    glow(im, 232, 140, 316, 158, "blue3", 0.4, 4, 12)
    # spilled milk puddle at the cooler's foot
    ellipse(im, 40, 152, 66, 156, "white")
    hline(im, 44, 58, 153, "grey4")

    cooler(im)
    depot_counter(im)

    # clock (4:00), notice board, bag hooks
    clock4(im, 237, 47, 8)
    obox(im, 216, 60, 48, 30, "brown3", "brown3", "brown2", ol="ink")
    rect(im, 217, 61, 46, 28, "brown3")
    dither_grad(im, (218, 62, 262, 88), "brown3", "brown2", "y", 4, 0.0, 0.5)
    rect(im, 216, 60, 48, 1, "brown1")
    rect(im, 221, 63, 20, 24, "white", "ink")                         # route sheet
    rect(im, 223, 65, 16, 3, "blue2")
    for ly in range(70, 85, 3):
        hline(im, 223, 237 - (ly % 2) * 3, ly, "grey2")
    px(im, 231, 63, "red3"); px(im, 231, 62, "red3")
    rect(im, 244, 64, 8, 9, "yellow2", "ink"); hline(im, 246, 250, 67, "grey2"); hline(im, 246, 249, 69, "grey2")
    rect(im, 253, 70, 8, 10, "blue4", "ink"); hline(im, 255, 259, 73, "grey2"); hline(im, 255, 258, 75, "grey2")
    rect(im, 244, 76, 7, 8, "wall4", "ink"); hline(im, 245, 249, 79, "grey2")
    for pxx, pyy in ((231, 64), (248, 65), (257, 71), (247, 77)):
        px(im, pxx, pyy, "red3")
    # hooks + delivery bags
    rect(im, 212, 98, 51, 3, "brown1", "ink")
    hline(im, 213, 261, 99, "brown2")
    hang_bag(im, 222, 98, "orange2", "orange1", "orange3")
    hang_bag(im, 240, 98, "blue2", "blue1", "blue3")
    hang_bag(im, 257, 98, "white", "grey3", "grey4")
    # crates + bin at the wall base
    for (cx, cy) in ((214, 124), (214, 130)):
        rect(im, cx, cy, 24, 7, "blue2", "ink")
        hline(im, cx + 1, cx + 22, cy + 1, "blue3")
        for sx in range(cx + 3, cx + 21, 5):
            rect(im, sx, cy + 3, 3, 2, "blue0")
    carton(im, 218, 115, "blue2"); carton(im, 223, 115, "blue2"); carton(im, 228, 115, "red3")
    rect(im, 216, 122, 18, 2, "ink")
    rect(im, 247, 124, 14, 14, "grey3", "ink")
    hline(im, 248, 259, 125, "grey4"); hline(im, 246, 261, 123, "ink")
    rect(im, 249, 128, 10, 4, "blue2"); hline(im, 248, 259, 133, "grey2")
    # A-frame sign + polystyrene ice box left of the counter
    poly(im, [(114, 138), (128, 138), (124, 122), (118, 122)], "yellow", "ink")
    rect(im, 119, 126, 4, 6, "ink"); px(im, 121, 134, "ink")
    hline(im, 115, 127, 137, "orange2")
    rect(im, 120, 96, 6, 9, "white", "ink") if False else None
    # thermostat / outlet
    rect(im, 120, 86, 6, 9, "white", "ink"); px(im, 122, 89, "ink"); px(im, 123, 89, "ink"); px(im, 122, 92, "red3")
    glass_door(im)
    line(im, [(212, 36), (212, 44), (268, 44), (268, 58)], "ink2")
    letterbox(im)
    return im


# ====================================================================== OFFICETEL HALL
DOOR_GREY = ("grey3", "grey2", "grey4", "ink2")
DOOR_BLUE = ("blue2", "blue1", "blue3", "blue0")


def flat_leaf(img, x, y, lw, h, pal, slant=0):
    base, shade, hi, deep = pal
    pts = [(x, y + slant), (x + lw - 1, y), (x + lw - 1, y + h - 1), (x, y + h - 1 - slant)]
    poly(img, pts, base, "ink")
    dpoly(img, [(a + (1 if a == x else 0), b) for a, b in pts], base, shade, 0.0, 0.7, "x", 4)
    poly(img, pts, None, "ink")
    hline(img, x + 1, x + lw - 3, y + 1 + slant // 2, hi)
    vline(img, x + 1, y + 2 + slant, y + h - 3 - slant, hi)
    if lw >= 14:
        # flat laminated panel: faint brushed grain + kick strip + frame groove
        for gy in range(y + 6, y + h - 10, 4):
            hline(img, x + 3, x + lw - 4, gy + slant // 2, shade) if False else None
        rect(img, x + 3, y + 5, lw - 6, h - 16, None, deep)
        hline(img, x + 4, x + lw - 5, y + 6, hi)
        rect(img, x + 1, y + h - 8 - slant, lw - 2, 7, shade, "ink")
        hline(img, x + 2, x + lw - 3, y + h - 7 - slant, hi)
        ellipse(img, x + lw // 2 - 1, y + 13, x + lw // 2 + 1, y + 15, "grey4", "ink")
        px(img, x + lw // 2, y + 14, "blue2")
    return base, shade, hi, deep


def milk_box(im, x, y):
    """small white insulated milk box with two bottle necks and a blue lid, 12x9, bottom y."""
    rect(im, x + 2, y - 12, 2, 4, "yellow", "ink"); rect(im, x + 7, y - 12, 2, 4, "red2", "ink")
    rect(im, x, y - 9, 12, 9, "white", "ink")
    rect(im, x + 1, y - 8, 10, 3, "blue2")
    hline(im, x + 2, x + 9, y - 3, "grey3")
    px(im, x + 1, y - 7, "blue3")


def parcel(im, x, y, w=11, h=8):
    rect(im, x, y - h, w, h, "brown3", "ink")
    hline(im, x + 1, x + w - 2, y - h + 2, "brown2")
    rect(im, x + w // 2 - 1, y - h, 3, h, "white", None)
    vline(im, x + w // 2 - 1, y - h, y - 1, "ink") if False else None


def off_door(im, cx, pal, extra=None):
    x, y = cx - 14, 92
    rect(im, x - 2, y - 2, 32, 60, "grey2", "ink")
    vline(im, x - 1, y - 1, y + 56, "grey3")
    hline(im, x - 1, x + 28, y - 1, "grey3")
    flat_leaf(im, x, y, 28, 58, pal)
    digital_lock(im, x + 19, y + 29, "grey4")
    if extra == "pouch":
        line(im, [(x + 6, y + 30), (x + 6, y + 34)], "ink")
        rect(im, x + 2, y + 34, 9, 10, "white", "ink")
        rect(im, x + 3, y + 35, 7, 3, "blue2")
        rect(im, x + 4, y + 30, 2, 4, "yellow", "ink") if False else None
        px(im, x + 5, y + 31, "red2")
        hline(im, x + 3, x + 9, y + 41, "grey3")
    if extra == "slip":
        rect(im, x + 5, y + 20, 8, 10, "yellow2", "ink")
        hline(im, x + 6, x + 11, y + 23, "grey2"); hline(im, x + 6, x + 10, y + 25, "grey2"); hline(im, x + 6, x + 11, y + 27, "grey2")
        px(im, x + 8, y + 20, "red3")
    rect(im, x - 2, 150, 32, 2, "grey1", "ink")
    rect(im, x + 2, 151, 24, 3, "ink2", "ink")
    for mx in range(x + 3, x + 26, 3):
        px(im, mx, 152, "grey1")
    # blank LED plaque (x cx-9..cx+9, y80..88)
    rect(im, cx - 9, 80, 19, 9, "grey4", "ink")
    hline(im, cx - 8, cx + 8, 81, "white")
    hline(im, cx - 8, cx + 8, 87, "grey3")


def fire_door_dark(im):
    x, y, w, h = 276, 88, 35, 63
    rect(im, x - 2, y - 2, w + 4, h + 2, "grey2", "ink")
    rect(im, x, y, w, h - 1, "grey3", "ink")
    dither_grad(im, (x + 1, y + 1, x + w - 1, y + h - 2), "grey3", "grey1", "x", 4, 0.0, 0.8)
    hline(im, x + 1, x + w - 2, y + 1, "grey4")
    rect(im, x + 10, y + 8, 14, 22, "blue0", "ink")
    dither_grad(im, (x + 11, y + 9, x + 23, y + 29), "blue1", "blue0", "d", 4, 0.0, 1.0)
    for gy in range(y + 11, y + 29, 4):
        hline(im, x + 11, x + 22, gy, "grey1")
    for gx in range(x + 13, x + 23, 4):
        vline(im, gx, y + 9, y + 29, "grey1")
    rect(im, x + 4, y + 34, 27, 4, "grey4", "ink")
    rect(im, x + 5, y + 40, 6, 12, "grey2", "ink")
    rect(im, x, y + h - 9, w, 8, "grey2", "ink")
    hline(im, x + 1, x + w - 2, y + h - 8, "grey3")
    line(im, [(x + 4, y - 1), (x + 12, y - 5), (x + 20, y - 1)], "ink")
    rect(im, x + 12, y - 7, 8, 3, "grey1", "ink")
    for sx in range(x + 2, x + w - 2, 4):
        px(im, sx, y + 3, "red2")
    glow(im, 268, 70, 316, 100, "green2", 0.28, 4, 8)
    rect(im, 279, 71, 29, 15, "green0", "ink")
    rect(im, 280, 72, 27, 13, "green1", "ink")
    text(im, 299, 73, "계단", "white", 9, align="center")
    px(im, 283, 82, "green3"); px(im, 284, 81, "green3"); px(im, 285, 80, "green3")
    rect(im, x - 2, 150, w + 4, 2, "grey1", "ink")


def build_hall():
    im = new(W, H, "ink")
    # ceiling: dark slab with recessed LED panels
    rect(im, 0, Y0, W, 18, "ink2")
    dither_grad(im, (0, Y0, W, 40), "ink", "ink2", "y", 4, 0.0, 1.0)
    for sx in range(0, W, 24):
        vline(im, sx, Y0, 39, "ink")
    hline(im, 0, W - 1, 40, "ink"); hline(im, 0, W - 1, 41, "grey2"); hline(im, 0, W - 1, 42, "grey1")
    # wall: cool dark grey, lit under the panels
    dither_ramp(im, (0, 43, W, 108), ["grey1", "grey2", "grey2"], "y", 4)
    ovl(im, (0, 43, W, 108), "blue0", 0.14, 4)
    for sx in (92, 152, 212, 272):
        vline(im, sx, 43, 107, "grey1")
    # dark metal dado
    rect(im, 0, 108, W, 30, "grey1")
    dither_grad(im, (0, 109, W, 138), "grey1", "ink2", "y", 4, 0.0, 0.85)
    ovl(im, (0, 109, W, 138), "blue0", 0.15, 4)
    hline(im, 0, W - 1, 107, "ink"); hline(im, 0, W - 1, 108, "grey3"); hline(im, 0, W - 1, 109, "grey2")
    hline(im, 0, W - 1, 137, "ink")
    for sx in range(0, W, 3):
        px(im, sx, 111, "ink2")
    streaks(im, (0, 44, W, 106), "grey1", 20, 31, 16, 0.5, "grey2")
    # glossy dark floor with reflected light
    floor_band(im, FLOOR_TOP, 158, "grey1", "ink2", "ink", "grey2", 24, 27)
    for (a, b) in ((30, 118), (136, 244)):
        glow(im, a, 141, b, 158, "grey2", 0.35, 4, 18)
    for rx in (60, 160, 240):
        for yy in range(142, 156, 2):
            px(im, rx + (yy % 4), yy, "grey3")
    # LED panels (one failing)
    tube(im, 34, 96, 30); tube(im, 124, 200, 30); tube(im, 224, 262, 30, on=False)
    px(im, 262, 33, "white"); px(im, 263, 33, "white")
    cctv_dome(im, 122, 41)
    rect(im, 0, 24, W, 3, "grey1", "ink")
    for bx in range(18, W, 52):
        rect(im, bx, 23, 3, 5, "grey2", "ink")

    elevator_closed(im)
    ovl(im, (15, 83, 62, 152), "ink2", 0.22, 4)
    # elevator: re-blank the indicator after the tint (stays dark)
    rect(im, 22, 70, 32, 13, "ink")
    hline(im, 23, 52, 71, "ink2")

    off_door(im, 110, DOOR_GREY, "pouch")
    off_door(im, 170, DOOR_BLUE, "slip")
    off_door(im, 230, DOOR_GREY)

    # --- gap A: floor directory board + parcel
    rect(im, 72, 92, 20, 26, "blue1", "ink")
    rect(im, 73, 93, 18, 24, "blue0")
    for ly in range(96, 116, 4):
        hline(im, 75, 88 - (ly % 8) // 2, ly, "blue3")
        px(im, 74, ly, "yellow")
    hline(im, 73, 90, 93, "blue2")
    parcel(im, 72, 150, 14, 9); parcel(im, 75, 141, 10, 7)
    # --- gap B: smoke detector, milk box + parcels by door
    ellipse(im, 138, 56, 144, 61, "grey4", "ink"); px(im, 141, 58, "red3")
    milk_box(im, 130, 150)
    parcel(im, 143, 150, 9, 6)
    # --- gap C: wall sensor panel, milk boxes
    rect(im, 195, 98, 8, 12, "grey4", "ink"); px(im, 197, 101, "green2"); px(im, 197, 104, "ink2"); px(im, 200, 104, "ink2"); px(im, 197, 107, "ink2"); px(im, 200, 107, "red3")
    milk_box(im, 191, 150); milk_box(im, 203, 150)
    rect(im, 203, 136, 10, 4, "white", None) if False else None
    # --- gap D: extinguisher + recycling
    fire_ext_box(im, 248, 100)
    rect(im, 247, 130, 17, 1, "ink")
    rect(im, 254, 136, 14, 14, "green1", "ink"); hline(im, 255, 266, 137, "green2")
    rect(im, 252, 143, 16, 7, "brown3", "ink"); hline(im, 253, 266, 146, "brown2")
    milk_box(im, 250, 141) if False else None
    # fire door + sign
    fire_door_dark(im)
    # vignette
    ovl(im, (0, 43, 12, 138), "ink2", 0.3, 2)
    ovl(im, (0, 138, 12, 158), "ink2", 0.25, 2)
    ovl(im, (308, 43, 320, 138), "ink2", 0.3, 2)
    letterbox(im)
    return im


# ====================================================================== SMALL PROPS
def build_milk_carrier():
    im = new(14, 14)
    # two bottles poking out of the top
    for bx, cc in ((1, "red2"), (8, "yellow")):
        rect(im, bx + 1, 0, 4, 3, cc, "ink")
        rect(im, bx, 2, 6, 6, "white", "ink")
        px(im, bx + 1, 3, "grey4")
        rect(im, bx + 2, 5, 3, 2, "blue2")
    # insulated bag body
    rect(im, 0, 7, 14, 7, "grey3", "ink")
    rect(im, 1, 8, 12, 2, "grey4")
    hline(im, 1, 12, 10, "grey2")
    rect(im, 1, 11, 12, 2, "blue2")
    hline(im, 1, 12, 12, "blue1")
    px(im, 6, 11, "white"); px(im, 7, 11, "white")
    return im


def build_open_office_door():
    im = new(28, 58)
    poly(im, [(0, 0), (11, 2), (11, 55), (0, 57)], "ink")
    flat_leaf(im, 10, 0, 18, 58, DOOR_GREY, slant=2)
    vline(im, 10, 3, 54, "grey2")
    vline(im, 11, 4, 53, "grey4")
    rect(im, 12, 30, 4, 11, "grey4", "ink")
    px(im, 13, 32, "ink2"); px(im, 14, 32, "ink2"); px(im, 13, 35, "ink2"); px(im, 13, 38, "red3")
    for hy in (6, 28, 46):
        rect(im, 26, hy, 2, 5, "grey1", "ink")
    rect(im, 2, 18, 2, 2, "pale1")
    rect(im, 6, 18, 2, 2, "pale1")
    return im


def build_props():
    for nm, im in (("milk_carrier", build_milk_carrier()), ("officetel_door_open", build_open_office_door())):
        assert not off_palette(im), nm
        save(im, f"props/{nm}.png", 8)


def build_bgs():
    for nm, fn in (("stairwell_scissor", build_scissor), ("roof", build_roof),
                   ("milk_depot", build_depot), ("officetel_hall", build_hall)):
        im = fn()
        assert not off_palette(im), nm
        save(im, f"bg/{nm}.png")


if __name__ == "__main__":
    parts = sys.argv[1:] or ["sprites", "bgs", "props"]
    if "sprites" in parts:
        build_sprites()
    if "bgs" in parts:
        build_bgs()
    if "props" in parts:
        build_props()
    if set(parts) >= {"sprites", "bgs", "props"}:
        contact(["props/suit_boss.png", "props/resident.png", "bg/stairwell_scissor.png", "bg/roof.png",
                 "bg/milk_depot.png", "bg/officetel_hall.png", "props/milk_carrier.png",
                 "props/officetel_door_open.png"], "_contact/bosses23.png", cols=2, scale=2)
    print("done")

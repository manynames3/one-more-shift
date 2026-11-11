"""The Rat King boss (what the fake coworker really is), its rats, and fight effects.

Outputs (public/assets/boss/):
  ratking.png/.json  72x64 frames: idle_0, idle_1, tell, dash, stun_0, stun_1, hurt, die_0, die_1
  rat.png/.json      16x12 frames: run_0, run_1 (facing left; flip in game for right)
  fx.png/.json       24x24 frames: swing_0..2 (mop arc), hit, star_0, star_1, splat
  mop.png            12x20 the mop you fight with
"""
import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *

R = random.Random(7)


# ------------------------------------------------------------------- rats
def rat_body(img, cx, cy, s=1.0, facing=-1, frame=0, eye="red3", base="grey2", shade="grey1", hi="grey3"):
    """One rat, side view, centred on cx,cy. facing -1 = left."""
    w, h = int(9 * s), int(5 * s)
    b = new(img.width, img.height)
    ellipse(b, cx - w, cy - h, cx + w, cy + h, base)
    ellipse(b, cx - w + 2, cy, cx + w - 1, cy + h, shade)             # belly shadow
    line(b, [(cx - w + 3, cy - h + 1), (cx + w - 4, cy - h + 1)], hi)  # back highlight
    hx = cx + facing * (w - 1)
    poly(b, [(hx, cy - 3), (hx + facing * 5, cy), (hx, cy + 3)], base)  # snout
    ellipse(b, hx - 3, cy - h - 2, hx + 1, cy - h + 2, "red4")         # ear
    img.alpha_composite(outline(b))
    px(img, hx + facing * 1, cy - 2, eye)
    px(img, hx + facing * 5, cy, "red4")                               # nose
    # tail curls behind
    tx = cx - facing * w
    pts = [(tx, cy + 1), (tx - facing * 3, cy + (2 if frame else 0)), (tx - facing * 6, cy - 1), (tx - facing * 8, cy + (1 if frame else -2))]
    line(img, pts, "red4")
    # legs
    for lx in (cx - 4, cx + 3):
        o = 1 if (frame and lx < cx) or (not frame and lx > cx) else 0
        rect(img, lx, cy + h, 2, 2 - o, "ink")


def rat_frames():
    out = []
    for f in range(2):
        im = new(16, 12)
        rat_body(im, 8, 6, 0.75, -1, f)
        out.append(im)
    return out


# ------------------------------------------------------------- the king
def ratking(state="idle", f=0):
    im = new(72, 64)
    rr = random.Random(11)          # same pile every frame, so it doesn't boil
    bob = {"idle": f, "tell": -4, "dash": 2, "stun": 1 + f, "hurt": 0, "die": 4 + f * 8}[state]
    squash = 1.0 if state != "dash" else 0.82
    # the pile: rats stacked into a hunched mound
    mound = new(72, 64)
    ellipse(mound, 6, 22 + bob, 66, 62, "brown0")
    dither_grad(mound, (6, 22 + bob, 66, 62), "brown0", "ink2", "y", 2, 0.2, 0.9, mask=shade_mask(mound))
    im.alpha_composite(outline(mound))
    spots = [(rr.randint(12, 60), rr.randint(28 + bob, 58), rr.choice([-1, 1]), rr.uniform(0.6, 1.0)) for _ in range(22)]
    spots.sort(key=lambda s: s[1])
    for (x, y, fc, s) in spots:
        if state == "die" and f == 1 and rr.random() < 0.5:
            continue
        rat_body(im, x, y, s * squash, fc, (x + f) % 2, eye="red3",
                 base=rr.choice(["grey2", "brown1", "grey1"]), shade="ink2", hi="grey3")
    if state == "die":
        return im
    # the coworker's blue cap, still on top, and a scrap of his vest
    hy = 20 + bob
    ellipse(im, 24, hy - 9, 48, hy + 5, "blue1", "ink")
    rect(im, 18, hy - 1, 36, 3, "blue0", "ink")
    rect(im, 32, hy - 7, 8, 3, "white")
    poly(im, [(44, 40 + bob), (56, 38 + bob), (54, 50 + bob), (46, 48 + bob)], "blue2", "ink")
    px(im, 50, 43 + bob, "white"); px(im, 51, 43 + bob, "white")
    # face: two big eyes and a crooked mouth full of little teeth
    ey = 28 + bob
    for ex in (27, 43):
        if state == "stun":
            for k in range(5):
                px(im, ex - 2 + k, ey - 2 + k, "yellow"); px(im, ex + 2 - k, ey - 2 + k, "yellow")
        elif state == "hurt":
            rect(im, ex - 3, ey, 7, 2, "white", "ink")
        else:
            ellipse(im, ex - 4, ey - 3, ex + 4, ey + 4, "red3" if state != "tell" else "yellow", "ink")
            rect(im, ex - 1, ey - 1, 2, 3, "ink")
            px(im, ex - 2, ey - 2, "red4" if state != "tell" else "white")
    mw = 22 if state in ("tell", "dash") else 16
    mx, my = 36 - mw // 2, 36 + bob
    rect(im, mx, my, mw, 7 if state in ("tell", "dash") else 4, "red0", "ink")
    for k in range(mx + 2, mx + mw - 2, 3):
        px(im, k, my + 1, "white"); px(im, k + 1, my + 1, "white")
        if state in ("tell", "dash"):
            px(im, k + 1, my + 5, "white")
    if state == "hurt":
        tint_dither(im, "white", 0.5, 2)
    return im


def ratking_core(state, f, bob):
    # redraw the creature over its glow so the glow only shows around the edge
    return ratking("idle" if state == "tell" else state, f) if False else new(72, 64)


def king_frames():
    names, frames = [], []
    for st, n in (("idle", 2), ("tell", 1), ("dash", 1), ("stun", 2), ("hurt", 1), ("die", 2)):
        for f in range(n):
            names.append(f"{st}_{f}" if n > 1 else st)
            frames.append(ratking(st, f))
    # tell: glow behind, creature in front
    i = names.index("tell")
    glow = new(72, 64); dither_radial(glow, 36, 40, 34, "red2", None, 2)
    body = ratking("idle", 0)
    # keep the rearing face from the tell frame
    face = ratking("tell", 0)
    glow.alpha_composite(face)
    frames[i] = glow
    return names, frames


# ------------------------------------------------------------- effects
def fx_frames():
    names, out = [], []
    for k in range(3):                  # mop swing arc, sweeping left->right
        im = new(24, 24)
        a0 = -150 + k * 50
        d = draw(im)
        d.arc([2, 2, 22, 22], a0, a0 + 70, fill=col("white"), width=3)
        d.arc([4, 4, 20, 20], a0, a0 + 70, fill=col("grey3"), width=1)
        names.append(f"swing_{k}"); out.append(im)
    im = new(24, 24)                    # hit spark
    for (a, b) in [((12, 2), (12, 22)), ((2, 12), (22, 12)), ((5, 5), (19, 19)), ((19, 5), (5, 19))]:
        line(im, [a, b], "yellow")
    ellipse(im, 8, 8, 16, 16, "white")
    names.append("hit"); out.append(im)
    for k in range(2):                  # dizzy star
        im = new(24, 24)
        cx, cy = 12, 12
        pts = []
        import math
        for i in range(10):
            r = 9 if i % 2 == 0 else 4
            ang = math.pi / 2 + i * math.pi / 5 + k * 0.6
            pts.append((cx + r * math.cos(ang), cy - r * math.sin(ang)))
        poly(im, pts, "yellow", "ink")
        names.append(f"star_{k}"); out.append(im)
    im = new(24, 24)                    # splat where a rat died
    rr = random.Random(3)
    for _ in range(9):
        x, y = rr.randint(4, 19), rr.randint(10, 20)
        ellipse(im, x - 2, y - 1, x + 2, y + 1, "red1")
    names.append("splat"); out.append(im)
    return names, out


def mop():
    im = new(12, 22)
    rect(im, 5, 0, 2, 14, "brown2", "ink")
    rect(im, 1, 13, 10, 3, "grey1", "ink")
    for x in range(1, 11, 2):
        rect(im, x, 16, 2, 5, "grey4", "ink")
    return im


if __name__ == "__main__":
    sheet(rat_frames(), "boss/rat", ["run_0", "run_1"], cols=2, scale=6)
    n, f = king_frames(); sheet(f, "boss/ratking", n, cols=5, scale=4)
    n, f = fx_frames(); sheet(f, "boss/fx", n, cols=7, scale=4)
    save(mop(), "boss/mop.png", 6)
    contact(["boss/ratking.png", "boss/rat.png", "boss/fx.png", "boss/mop.png"], "_contact/boss.png", cols=2, scale=4)
    print("ok")

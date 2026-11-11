"""Parametric chibi character rig (32x48 frames, feet on y=45).

chibi(spec, dir, pose, frame, expr) -> RGBA frame.
  dir : 'down' (facing camera), 'side' (facing LEFT; flip() for right), 'up'
  pose: 'idle' (2 frames), 'walk' (4), 'scared' (2), 'work' (2)
  expr: neutral | tired | scared | smile | creepy | dead | angry
spec keys: skin=(base,shade) hair=(base,highlight) hair_style top=(base,shade)
  pants=(base,shade) shoes outfit + outfit extras, glasses, blush, expr
"""
from pxkit import *

FW, FH = 32, 48
_FRINGE = [1, 2, 1, 0, 1, 2, 3, 2, 1, 0, 1, 2, 1, 1, 2, 3, 2, 1]
CLEAR = (0, 0, 0, 0)


def _erase(img, x, y, w, h):
    draw(img).rectangle([x, y, x + w - 1, y + h - 1], fill=CLEAR)


# ------------------------------------------------------------------- hair
def _hair_front(head, s, oy):
    st = s.get("hair_style", "short")
    hc, hh = s.get("hair", ("ink2", "grey1"))
    if st == "bald":
        rect(head, 5, 10 + oy, 1, 4, hc); rect(head, 26, 10 + oy, 1, 4, hc)
        px(head, 11, 6 + oy, "skin3"); px(head, 12, 5 + oy, "skin3")
        return
    if st == "cap":
        kc, ks = s.get("hat", ("red2", "red1"))
        rect(head, 5, 11 + oy, 2, 3, hc); rect(head, 25, 11 + oy, 2, 3, hc)
        t = new(FW, FH); ellipse(t, 4, 1 + oy, 27, 15 + oy, kc); _erase(t, 0, 9 + oy, 32, 40)
        head.alpha_composite(t)
        rect(head, 3, 9 + oy, 26, 2, ks)
        rect(head, 13, 4 + oy, 6, 3, "white")
        return
    clip = {"slick": 7}.get(st, 9)
    top = 0 if st == "messy" else 1
    t = new(FW, FH)
    ellipse(t, 4 if st != "messy" else 3, top + oy, 27 if st != "messy" else 28, 15 + oy, hc)
    _erase(t, 0, clip + oy, 32, 40)
    head.alpha_composite(t)
    if st == "slick":
        rect(head, 5, 7 + oy, 2, 6, hc); rect(head, 25, 7 + oy, 2, 6, hc)
        px(head, 15, 7 + oy, hc); px(head, 16, 7 + oy, hc)
        line(head, [(9, 3 + oy), (20, 3 + oy)], hh)
        line(head, [(8, 5 + oy), (14, 5 + oy)], hh)
    else:
        for i, k in enumerate(_FRINGE):
            if k:
                rect(head, 7 + i, 9 + oy, 1, k, hc)
        rect(head, 5, 9 + oy, 2, 5, hc); rect(head, 25, 9 + oy, 2, 5, hc)
        line(head, [(10, 4 + oy), (15, 4 + oy)], hh); px(head, 17, 4 + oy, hh)
        px(head, 9, 5 + oy, hh)
    if st == "messy":
        poly(head, [(6, 4 + oy), (8, 0 + oy), (11, 3 + oy)], hc)
        poly(head, [(13, 2 + oy), (16, 0 + oy), (18, 2 + oy)], hc)
        poly(head, [(20, 3 + oy), (24, 0 + oy), (25, 5 + oy)], hc)
        rect(head, 3, 8 + oy, 2, 4, hc); rect(head, 27, 8 + oy, 2, 4, hc)
    if st == "bob":
        rect(head, 3, 9 + oy, 4, 13, hc); rect(head, 25, 9 + oy, 4, 13, hc)
        px(head, 7, 21 + oy, hc); px(head, 24, 21 + oy, hc)
        line(head, [(4, 12 + oy), (4, 18 + oy)], hh)
    if st == "long":
        rect(head, 3, 9 + oy, 4, 23, hc); rect(head, 25, 9 + oy, 4, 23, hc)
        line(head, [(4, 12 + oy), (4, 26 + oy)], hh)
    if st == "ponytail":
        poly(head, [(26, 5 + oy), (30, 7 + oy), (30, 16 + oy), (28, 19 + oy), (27, 11 + oy)], hc)
        px(head, 26, 6 + oy, "blue2"); px(head, 26, 7 + oy, "blue2")
    if st == "bun":
        ellipse(head, 12, 1 + oy, 19, 6 + oy, hc)
        px(head, 14, 2 + oy, hh)


def _hair_side(head, s, oy):
    st = s.get("hair_style", "short")
    hc, hh = s.get("hair", ("ink2", "grey1"))
    if st == "bald":
        rect(head, 19, 11 + oy, 5, 3, hc); return
    if st == "cap":
        kc, ks = s.get("hat", ("red2", "red1"))
        rect(head, 18, 10 + oy, 7, 6, hc)
        t = new(FW, FH); ellipse(t, 4, 1 + oy, 27, 15 + oy, kc); _erase(t, 0, 9 + oy, 32, 40)
        head.alpha_composite(t)
        rect(head, 1, 9 + oy, 26, 2, ks)
        return
    clip = {"slick": 7}.get(st, 9)
    back = {"bob": 23, "long": 23}.get(st, 19)
    t = new(FW, FH)
    ellipse(t, 4, (0 if st == "messy" else 1) + oy, 28, 23 + oy, hc)
    _erase(t, 0, clip + oy, 18, 40)       # face side: only the fringe band
    _erase(t, 0, back + oy, 32, 40)
    head.alpha_composite(t)
    if st != "slick":
        for i, k in enumerate(_FRINGE[:11]):
            if k:
                rect(head, 7 + i, 9 + oy, 1, k, hc)
    line(head, [(12, 4 + oy), (19, 4 + oy)], hh)
    if st == "messy":
        poly(head, [(8, 4 + oy), (10, 0 + oy), (13, 3 + oy)], hc)
        poly(head, [(18, 2 + oy), (22, 0 + oy), (24, 3 + oy)], hc)
        rect(head, 27, 9 + oy, 2, 5, hc)
    if st == "long":
        rect(head, 20, 18 + oy, 8, 14, hc); line(head, [(25, 14 + oy), (25, 28 + oy)], hh)
    if st == "ponytail":
        poly(head, [(26, 7 + oy), (31, 10 + oy), (30, 21 + oy), (27, 16 + oy)], hc)
        rect(head, 26, 8 + oy, 1, 3, "blue2")
    if st == "bun":
        ellipse(head, 21, 1 + oy, 28, 7 + oy, hc)


def _hair_back(head, s, oy):
    st = s.get("hair_style", "short")
    hc, hh = s.get("hair", ("ink2", "grey1"))
    if st == "bald":
        rect(head, 6, 13 + oy, 20, 4, hc); return
    low = {"bob": 23, "long": 24}.get(st, 19)
    t = new(FW, FH)
    ellipse(t, 4, (0 if st == "messy" else 1) + oy, 27, 24 + oy, hc)
    _erase(t, 0, low + oy, 32, 40)
    head.alpha_composite(t)
    if st == "cap":
        kc, ks = s.get("hat", ("red2", "red1"))
        t = new(FW, FH); ellipse(t, 4, 1 + oy, 27, 15 + oy, kc); _erase(t, 0, 11 + oy, 32, 40)
        head.alpha_composite(t)
        rect(head, 13, 9 + oy, 6, 2, ks)
    else:
        line(head, [(9, 6 + oy), (21, 6 + oy)], hh); line(head, [(7, 9 + oy), (10, 9 + oy)], hh)
    if st == "messy":
        poly(head, [(6, 4 + oy), (8, 0 + oy), (11, 3 + oy)], hc)
        poly(head, [(20, 3 + oy), (24, 0 + oy), (25, 5 + oy)], hc)
    if st == "bob":
        rect(head, 3, 9 + oy, 26, 13, hc); line(head, [(8, 12 + oy), (8, 19 + oy)], hh)
    if st == "long":
        rect(head, 3, 9 + oy, 26, 23, hc); line(head, [(8, 12 + oy), (8, 28 + oy)], hh)
        line(head, [(20, 14 + oy), (20, 30 + oy)], hh)
    if st == "ponytail":
        rect(head, 14, 9 + oy, 4, 17, hc); rect(head, 14, 9 + oy, 4, 2, "blue2")
        line(head, [(15, 12 + oy), (15, 23 + oy)], hh)
    if st == "bun":
        ellipse(head, 12, 1 + oy, 19, 6 + oy, hc)


# ------------------------------------------------------------------- face
def _face_front(head, s, expr, oy):
    sk, ss = s.get("skin", ("skin2", "skin1"))
    ey = 14 + oy
    line(head, [(8, 10 + oy), (23, 10 + oy)], ss)          # shadow under fringe
    line(head, [(25, 12 + oy), (25, 17 + oy)], ss)
    for ex in (10, 20):
        if expr == "tired":
            line(head, [(ex - 1, ey), (ex + 2, ey)], "ink")
            rect(head, ex, ey + 1, 2, 2, "ink")
            line(head, [(ex, ey + 4), (ex + 1, ey + 4)], ss)
        elif expr == "scared":
            rect(head, ex - 1, ey - 2, 4, 6, "white", "ink")
            px(head, ex + (1 if ex == 10 else 0), ey + 1, "ink")
        elif expr == "smile":
            px(head, ex - 1, ey + 1, "ink"); px(head, ex, ey, "ink")
            px(head, ex + 1, ey, "ink"); px(head, ex + 2, ey + 1, "ink")
        elif expr == "creepy":
            rect(head, ex - 1, ey - 1, 4, 4, "ink")
            px(head, ex + (1 if ex == 10 else 0), ey + 1, "red3")
        elif expr == "dead":
            for k in range(3):
                px(head, ex - 1 + k, ey - 1 + k, "ink"); px(head, ex + 1 - k, ey - 1 + k, "ink")
        else:
            rect(head, ex, ey, 2, 3, "ink"); px(head, ex, ey, "white")
    by = ey - 3
    if expr == "angry":
        line(head, [(9, by), (12, by + 1)], "ink"); line(head, [(19, by + 1), (22, by)], "ink")
    elif expr == "scared":
        line(head, [(9, by - 1), (12, by - 2)], "ink"); line(head, [(19, by - 2), (22, by - 1)], "ink")
    elif expr not in ("creepy",):
        line(head, [(9, by), (12, by)], "ink2"); line(head, [(19, by), (22, by)], "ink2")
    my = ey + 5
    if expr == "scared":
        rect(head, 14, my - 1, 4, 3, "red0", "ink"); px(head, 15, my, "red3"); px(head, 16, my, "red3")
        px(head, 24, 9 + oy, "blue3"); px(head, 24, 10 + oy, "blue3")   # sweat
    elif expr == "smile":
        line(head, [(13, my), (18, my)], "ink"); px(head, 12, my - 1, "ink"); px(head, 19, my - 1, "ink")
    elif expr == "creepy":
        rect(head, 10, my - 1, 12, 3, "white", "ink")
        for x in (12, 14, 16, 18, 20):
            px(head, x, my, "ink")
    elif expr == "dead":
        rect(head, 14, my, 4, 2, "ink"); px(head, 16, my + 1, "red3")
    elif expr == "angry":
        line(head, [(14, my), (17, my)], "ink")
    else:
        line(head, [(15, my), (16, my)], "skin0")
    if s.get("glasses"):
        g = "ink2"
        draw(head).rectangle([8, ey - 1, 13, ey + 3], outline=col(g))
        draw(head).rectangle([18, ey - 1, 23, ey + 3], outline=col(g))
        line(head, [(14, ey), (17, ey)], g)
    if s.get("blush"):
        for x in (8, 9, 22, 23):
            px(head, x, ey + 4, "red4")


def _face_side(head, s, expr, oy):
    sk, ss = s.get("skin", ("skin2", "skin1"))
    ey = 14 + oy
    line(head, [(7, 10 + oy), (17, 10 + oy)], ss)
    rect(head, 17, 13 + oy, 2, 3, ss)                       # ear
    px(head, 4, ey + 3, sk); px(head, 4, ey + 2, sk)        # nose bump
    if expr == "scared":
        rect(head, 7, ey - 2, 3, 6, "white", "ink"); px(head, 8, ey + 1, "ink")
        rect(head, 6, ey + 5, 3, 3, "red0", "ink")
    elif expr == "creepy":
        rect(head, 7, ey - 1, 3, 4, "ink"); px(head, 8, ey + 1, "red3")
        rect(head, 6, ey + 4, 8, 3, "white", "ink")
    elif expr == "smile":
        px(head, 7, ey + 1, "ink"); px(head, 8, ey, "ink"); px(head, 9, ey + 1, "ink")
        line(head, [(7, ey + 5), (10, ey + 5)], "ink")
    elif expr == "tired":
        line(head, [(7, ey), (10, ey)], "ink"); rect(head, 8, ey + 1, 2, 2, "ink")
    else:
        rect(head, 8, ey, 2, 3, "ink"); px(head, 8, ey, "white")
        line(head, [(7, ey + 5), (8, ey + 5)], "skin0")
    if expr not in ("creepy",):
        line(head, [(7, ey - 3), (10, ey - 3)], "ink2")
    if s.get("glasses"):
        draw(head).rectangle([6, ey - 1, 11, ey + 3], outline=col("ink2"))
        line(head, [(12, ey), (17, ey)], "ink2")


# ------------------------------------------------------------------- body
def _outfit_front(t, s, oy, back=False):
    kind = s.get("outfit", "tee")
    tc, ts = s["top"]
    y = 24 + oy
    if kind == "hoodie":
        line(t, [(12, y + 1), (19, y + 1)], ts)
        if not back:
            px(t, 14, y + 2, "white"); px(t, 14, y + 3, "white"); px(t, 17, y + 2, "white"); px(t, 17, y + 3, "white")
            rect(t, 12, 31, 8, 3, ts)
        else:
            rect(t, 12, y, 8, 4, ts)
    elif kind == "vest":
        vc, vs = s.get("vest", ("green1", "green0"))
        if back:
            rect(t, 10, y, 12, 12 - oy, vc); rect(t, 20, y, 2, 12 - oy, vs)
        else:
            rect(t, 10, y, 4, 12 - oy, vc); rect(t, 18, y, 4, 12 - oy, vc); rect(t, 20, y, 2, 12 - oy, vs)
            px(t, 18, y + 3, "white"); px(t, 19, y + 3, "white")
    elif kind == "apron" and not back:
        ac, as_ = s.get("apron", ("white", "grey4"))
        rect(t, 12, y + 3, 8, 9 - oy, ac); rect(t, 12, y, 1, 3, ac); rect(t, 19, y, 1, 3, ac)
        line(t, [(13, y + 6), (18, y + 6)], as_)
    elif kind == "suit":
        if not back:
            poly(t, [(13, y), (18, y), (16, y + 6), (15, y + 6)], "white")
            rect(t, 15, y + 1, 2, 6, s.get("tie", "red2"))
            line(t, [(12, y), (14, y + 6)], ts); line(t, [(19, y), (17, y + 6)], ts)
            px(t, 15, y + 9, ts); px(t, 15, y + 11 - oy, ts)
    elif kind == "track":
        line(t, [(11, y), (11, 35)], "white"); line(t, [(20, y), (20, 35)], "white")
        if not back:
            line(t, [(15, y), (15, 35)], ts)
    elif kind == "floral":
        fc = s.get("pattern", "red4")
        for (x, yy) in [(11, 26), (14, 28), (18, 26), (20, 30), (12, 32), (16, 33), (19, 34), (15, 25)]:
            px(t, x, yy + oy if yy + oy < 36 else yy, fc)
    elif kind == "coat":
        if not back:
            line(t, [(15, y), (15, 41)], ts)
            for yy in (27, 31, 35, 39):
                px(t, 17, yy, s.get("button", "yellow"))


def _body_down(s, pose, frame, oy, back=False):
    tc, ts = s["top"]; pc, ps = s["pants"]; sh = s.get("shoes", "white")
    sk, ss = s.get("skin", ("skin2", "skin1"))
    sl = s.get("sleeve", tc)
    coat = s.get("outfit") == "coat"
    out = new(FW, FH)
    # legs
    ll = 2 if pose == "walk" and frame == 1 else 0
    lr = 2 if pose == "walk" and frame == 3 else 0
    legs = new(FW, FH)
    rect(legs, 11, 35, 4, 9 - ll, pc); rect(legs, 14, 35, 1, 9 - ll, ps); rect(legs, 10, 44 - ll, 5, 2, sh)
    rect(legs, 17, 35, 4, 9 - lr, pc); rect(legs, 20, 35, 1, 9 - lr, ps); rect(legs, 17, 44 - lr, 5, 2, sh)
    out.alpha_composite(outline(legs))
    # torso
    t = new(FW, FH)
    if coat:
        rect(t, 9, 24 + oy, 14, 18 - oy, tc); rect(t, 21, 24 + oy, 2, 18 - oy, ts)
    else:
        rect(t, 10, 24 + oy, 12, 12 - oy, tc); rect(t, 20, 24 + oy, 2, 12 - oy, ts)
    _outfit_front(t, s, oy, back)
    out.alpha_composite(outline(t))
    # arms
    a = new(FW, FH)
    if pose == "scared":
        j = frame % 2
        poly(a, [(8, 27 + oy), (10, 27 + oy), (5, 18 + j), (3, 19 + j)], sl)
        rect(a, 2, 15 + j, 3, 3, sk)
        poly(a, [(21, 27 + oy), (23, 27 + oy), (28, 19 + j), (26, 18 + j)], sl)
        rect(a, 27, 15 + j, 3, 3, sk)
    else:
        swl = -1 if pose == "walk" and frame == 3 else 0
        swr = -1 if pose == "walk" and frame == 1 else 0
        ax = 6 if coat else 7
        rect(a, ax, 25 + oy + swl, 3, 8, sl); rect(a, ax, 33 + oy + swl, 3, 2, sk)
        if pose == "work":
            wy = 27 - 2 * (frame % 2)
            rect(a, 22, wy + oy, 6, 3, sl); rect(a, 28, wy + oy, 2, 3, sk)
        else:
            bx = 23 if coat else 22
            rect(a, bx, 25 + oy + swr, 3, 8, sl); rect(a, bx, 33 + oy + swr, 3, 2, sk)
    out.alpha_composite(outline(a))
    return out


def _body_side(s, pose, frame, oy):
    tc, ts = s["top"]; pc, ps = s["pants"]; sh = s.get("shoes", "white")
    sk, ss = s.get("skin", ("skin2", "skin1"))
    sl = s.get("sleeve", tc)
    coat = s.get("outfit") == "coat"
    out = new(FW, FH)
    fx, bx = 14, 14
    if pose == "walk":
        fx, bx = {0: (14, 14), 1: (10, 17), 2: (14, 14), 3: (17, 10)}[frame % 4]
    back = new(FW, FH)
    rect(back, bx, 35, 4, 9, ps); rect(back, bx - 1, 44, 5, 2, sh)
    out.alpha_composite(outline(back))
    front = new(FW, FH)
    rect(front, fx, 35, 4, 9, pc); rect(front, fx - 1, 44, 5, 2, sh)
    out.alpha_composite(outline(front))
    t = new(FW, FH)
    hgt = (18 if coat else 12) - oy
    rect(t, 11, 24 + oy, 10, hgt, tc); rect(t, 19, 24 + oy, 2, hgt, ts)
    kind = s.get("outfit")
    if kind == "vest":
        vc, vs = s.get("vest", ("green1", "green0"))
        rect(t, 15, 24 + oy, 6, hgt, vc); rect(t, 19, 24 + oy, 2, hgt, vs)
    if kind == "track":
        line(t, [(15, 24 + oy), (15, 35)], "white")
    if kind == "hoodie":
        rect(t, 18, 24 + oy, 3, 4, ts)
    out.alpha_composite(outline(t))
    a = new(FW, FH)
    if pose == "scared":
        j = frame % 2
        poly(a, [(13, 27 + oy), (15, 27 + oy), (8, 19 + j), (6, 20 + j)], sl); rect(a, 4, 17 + j, 3, 3, sk)
    elif pose == "work":
        wy = 27 - 2 * (frame % 2)
        rect(a, 7, wy + oy, 8, 3, sl); rect(a, 5, wy + oy, 2, 3, sk)
    else:
        sw = {1: 2, 3: -2}.get(frame % 4, 0) if pose == "walk" else 0
        rect(a, 14 + sw, 26 + oy, 3, 7, sl); rect(a, 14 + sw, 33 + oy, 3, 2, sk)
        out.alpha_composite(outline(a, ts if ts != tc else "ink2"))
        return out
    out.alpha_composite(outline(a))
    return out


# ------------------------------------------------------------------- main
def chibi(spec, dir="down", pose="idle", frame=0, expr=None):
    s = spec
    expr = expr or ("scared" if pose == "scared" else s.get("expr", "neutral"))
    sk, ss = s.get("skin", ("skin2", "skin1"))
    oy = 1 if (frame % 2 == 1 and pose in ("idle", "walk", "work")) else 0
    jx = 1 if (pose == "scared" and frame % 2 == 1) else 0
    img = new(FW, FH)
    if dir == "side":
        img.alpha_composite(_body_side(s, pose, frame, oy))
    else:
        img.alpha_composite(_body_down(s, pose, frame, oy, back=(dir == "up")))
    head = new(FW, FH)
    ellipse(head, 5, 3 + oy, 26, 23 + oy, sk)
    if dir == "down":
        rect(head, 4, 13 + oy, 1, 3, sk); rect(head, 27, 13 + oy, 1, 3, sk)
        _face_front(head, s, expr, oy)
        _hair_front(head, s, oy)
    elif dir == "side":
        _face_side(head, s, expr, oy)
        _hair_side(head, s, oy)
    else:
        rect(head, 4, 13 + oy, 1, 3, sk); rect(head, 27, 13 + oy, 1, 3, sk)
        _hair_back(head, s, oy)
    img.alpha_composite(outline(head))
    if jx:
        sh = new(FW, FH); sh.paste(img, (1, 0)); img = sh
    return img


def lying(spec, expr="dead"):
    """48x32 collapsed sprite (rotated front view) for death / knocked-out."""
    f = chibi(spec, "down", "idle", 0, expr)
    r = f.rotate(90, expand=True)
    out = new(48, 32)
    out.paste(r, (0, 0))
    return out

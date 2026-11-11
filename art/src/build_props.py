import sys, os, random, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *

OUT = []   # relpaths of every png produced (for the contact sheet)

LEG = {
    'k': 'ink', 'K': 'ink2', '1': 'grey1', '2': 'grey2', '3': 'grey3', '4': 'grey4', 'w': 'white',
    'r': 'red2', 'R': 'red1', 'Q': 'red0', 'p': 'red3', 'P': 'red4',
    'o': 'orange2', 'O': 'orange1', 'E': 'orange0', 'e': 'orange3', 'f': 'orange4',
    'y': 'yellow', 'Y': 'yellow2',
    'g': 'green1', 'G': 'green2', 't': 'green0', 'h': 'green3',
    'b': 'blue2', 'B': 'blue1', 'd': 'blue0', 'c': 'blue3', 'C': 'blue4',
    'u': 'purple1', 'U': 'purple2', 'V': 'purple0',
    'n': 'brown2', 'N': 'brown1', 'M': 'brown0', 'm': 'brown3',
    's': 'skin2', 'S': 'skin1', 'a': 'skin3',
    'z': 'wall3', 'l': 'wall4', 'x': 'wall1', 'j': 'wall2', 'H': 'pale1', 'I': 'pale2',
}


def art(rows, w=None, h=None, bottom=False):
    ww = max(len(r) for r in rows)
    hh = len(rows)
    w = w or ww
    h = h or hh
    im = new(w, h)
    ox = (w - ww) // 2
    oy = (h - hh) if bottom else (h - hh) // 2
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                px(im, ox + x, oy + y, LEG[ch])
    return im


def thr2(x, y):
    return ([[0, 2], [3, 1]][y % 2][x % 2] + 0.5) / 4


def S(im, name):
    bad = off_palette(im)
    assert not bad, (name, bad)
    save(im, f"props/{name}.png")
    OUT.append(f"props/{name}.png")
    return im


def SH(frames, name, names, cols=None):
    for f in frames:
        bad = off_palette(f)
        assert not bad, (name, bad)
    sheet(frames, f"props/{name}", names, cols=cols)
    OUT.append(f"props/{name}.png")


def bx(img, x0, y0, x1, y1, base, hi=None, sh=None):
    rect(img, x0, y0, x1 - x0 + 1, y1 - y0 + 1, base)
    if hi:
        line(img, [(x0, y0), (x1, y0)], hi)
        line(img, [(x0, y0), (x0, y1)], hi)
    if sh:
        line(img, [(x0, y1), (x1, y1)], sh)
        line(img, [(x1, y0 + 1), (x1, y1)], sh)


def ol(img):
    return outline(img, "ink")


# ================================================================ products
PRODUCT_ROWS = [
    # 0 cereal box
    ["kkkkkkkk", "kprrrrRk", "kpwwwwRk", "kpwbbwRk", "kpwwwwRk", "kprryyRk", "kprryyRk", "kprrrrRk", "kRRRRRRk", "kkkkkkkk"],
    # 1 milk carton
    ["..kkkk..", ".kwwwck.", "kkkkkkkk", "kwwwwwck", "kwbbbwck", "kwbwbwck", "kwbbbwck", "kwwwwwck", "kcccccck", "kkkkkkkk"],
    # 2 soda can
    [".kkkkkk.", ".k4334k.", ".kGggtk.", ".kGyytk.", ".kGyytk.", ".kGggtk.", ".kGggtk.", ".kGggtk.", ".k3223k.", ".kkkkkk."],
    # 3 snack bag
    ["kkkkkkkk", "kOeOeOek", "keooooOk", "keoyyoOk", "keyYyyOk", "keoyyoOk", "keooooOk", "keooooOk", "kOOOOOOk", "kkkkkkkk"],
    # 4 water bottle
    ["...kk...", "..kbbk..", "..kccK..", "..kcck..", ".kcCccK.", ".kcCccK.", ".kcwwcK.", ".kccccK.", ".kccccK.", "..kkkk.."],
    # 5 noodle packet
    ["kkkkkkkk", "kprprprk", "kpyyyyRk", "kpyrryRk", "kpyrryRk", "kpyyyyRk", "kprrrrRk", "kprwwrRk", "kRRRRRRk", "kkkkkkkk"],
    # 6 tuna tin
    ["........", "........", "........", "........", "........", "kkkkkkkk", "k444433k", "kbbwwbBk", "kbwwwwBk", "kkkkkkkk"],
    # 7 juice box
    ["kkkkkkkk", "kUUuuuVk", "kUoeeuVk", "kUoeeuVk", "kUuoouVk", "kUuuuuVk", "kUuwwuVk", "kUuuuuVk", "kVVVVVVk", "kkkkkkkk"],
    # 8 jam jar
    ["..kkkk..", ".kmnnNk.", ".kkkkkk.", "kCoeooEk", "kcowwoEk", "kcowwoEk", "kcooooEk", "kcooooEk", "kcOOOOEk", "kkkkkkkk"],
    # 9 chips tube
    [".kkkkkk.", ".kyYyyk.", ".kkkkkk.", ".kUeeVk.", ".kUeeVk.", ".kUuuVk.", ".kUwwVk.", ".kUuuVk.", ".kVVVVk.", ".kkkkkk."],
    # 10 tissue box
    ["..kkkk..", ".kwwwwk.", "kkkkkkkk", "kCzzzzbk", "kCzwwzbk", "kCzwwzbk", "kCzzzzbk", "kCzzzzbk", "kbbbbbbk", "kkkkkkkk"],
    # 11 green bottle
    ["..kkkk..", "..k44k..", "..kgGk..", "..kgGk..", ".kgGGtk.", ".kgwwtk.", ".kgwwtk.", ".kgGGtk.", ".kgggtk.", ".kkkkkk."],
]
PRODUCT_NAMES = ["cereal", "milk", "soda", "snack", "water", "noodle_pack", "tuna", "juice", "jam", "chips", "tissue", "green_bottle"]
PRODUCTS = [art(r) for r in PRODUCT_ROWS]


def build_products():
    SH(PRODUCTS, "products", PRODUCT_NAMES, cols=6)


# ================================================================ shelves
def shelf(stocked):
    im = new(48, 56)
    bx(im, 1, 1, 46, 54, "grey3")
    comps = [(2, 12), (15, 25), (28, 38), (41, 51)]
    boards = [13, 26, 39, 52]
    for a, b in comps:
        rect(im, 3, a, 42, b - a + 1, "ink2")
        dither_grad(im, (3, a, 45, b + 1), "ink2", "grey1", "y", 4, 0.0, 0.55)
    for y in boards:
        rect(im, 3, y, 42, 1, "grey4")
        rect(im, 3, y + 1, 42, 1, "grey2")
        for tx, tc in ((6, "yellow"), (19, "red2"), (31, "white"), (39, "yellow")):
            rect(im, tx, y + 1, 3, 1, tc)
    # posts
    rect(im, 1, 1, 2, 54, "grey3"); line(im, [(1, 1), (1, 54)], "grey4")
    rect(im, 45, 1, 2, 54, "grey3"); line(im, [(46, 1), (46, 54)], "grey2")
    line(im, [(1, 1), (46, 1)], "grey4")
    line(im, [(1, 54), (46, 54)], "grey1")
    if stocked:
        layout = [[0, 0, 1, None, 9], [3, 3, 5, 4, None],
                  [2, 2, 2, 10, 10], [7, 8, 6, 11, 11]]
        for r, row in enumerate(layout):
            for i, p in enumerate(row):
                if p is None:
                    continue
                paste(im, PRODUCTS[p], 4 + i * 8, boards[r] - 10)
    return ol(im)


# ================================================================ drinks
DR = [("red3", "red2", "red1"), ("blue3", "blue2", "blue1"), ("green2", "green1", "green0"),
      ("orange3", "orange2", "orange1"), ("yellow2", "yellow", "orange2"),
      ("purple2", "purple1", "purple0"), ("wall4", "skin1", "red1")]


def drink(im, x, yb, kind, c):
    hi, base, sh = c
    if kind == "can":
        bx(im, x, yb - 7, x + 3, yb, base, hi, sh)
        line(im, [(x, yb - 7), (x + 3, yb - 7)], "grey3")
        px(im, x + 1, yb - 4, "white"); px(im, x + 2, yb - 4, "white")
    else:
        bx(im, x, yb - 7, x + 3, yb, base, hi, sh)
        rect(im, x + 1, yb - 9, 2, 2, base)
        px(im, x + 1, yb - 9, hi)
        rect(im, x + 1, yb - 10, 2, 1, "white")
        px(im, x + 1, yb - 4, "white"); px(im, x + 2, yb - 4, "white")


def drinks_fill(im, x0, x1, ybs, seed):
    rng = random.Random(seed)
    for yb in ybs:
        x = x0
        while x + 4 <= x1:
            drink(im, x, yb - 1, rng.choice(["can", "can", "bottle"]), rng.choice(DR))
            x += 5
        line(im, [(x0 - 2, yb), (x1 + 2, yb)], "grey3")
        line(im, [(x0 - 2, yb + 1), (x1 + 2, yb + 1)], "ink2")


def fridge(opened):
    im = new(40, 60)
    ybs = (23, 37, 51)
    if not opened:
        bx(im, 1, 1, 38, 58, "grey3", "grey4", "grey2")
        # header sign
        bx(im, 3, 2, 36, 7, "blue2", "blue3", "blue1")
        for a, b in ((5, 9), (11, 13), (15, 20), (24, 27)):
            rect(im, a, 4, b - a + 1, 2, "white")
        rect(im, 30, 4, 4, 2, "yellow")
        # glass
        dither_grad(im, (4, 10, 33, 53), "blue1", "blue0", "y", 4)
        drinks_fill(im, 6, 31, ybs, 11)
        for y in range(10, 53):
            for x in range(4, 33):
                k = (x + y) % 22
                if k in (0, 1) and (x + y) % 2 == 0 and y < 46:
                    px(im, x, y, "blue4")
                elif k in (5, 6) and (x + y) % 2 == 1 and y < 30:
                    px(im, x, y, "blue3")
        rect(im, 3, 9, 31, 45, outline="ink")
        # handle
        rect(im, 34, 17, 4, 27, "ink")
        bx(im, 35, 18, 36, 42, "grey4", "white", "grey2")
        # kick plate
        bx(im, 1, 54, 38, 58, "grey1", "grey2", "ink2")
        for x in range(6, 34, 4):
            line(im, [(x, 56), (x + 2, 56)], "ink")
        return ol(im)
    # open version
    bx(im, 11, 1, 38, 58, "grey3", "grey4", "grey2")
    dither_grad(im, (13, 3, 37, 54), "blue2", "blue1", "y", 4, 0.0, 0.8)
    drinks_fill(im, 15, 33, ybs, 23)
    for y in range(3, 54):          # cold mist
        for x in range(13, 37):
            if y > 44 and (1 - (y - 44) / 10) < ((x % 4) * 4 + (y % 4) + 0.5) / 16 and (x + y) % 2 == 0:
                px(im, x, y, "blue4")
    rect(im, 12, 2, 26, 52, outline="ink")
    bx(im, 11, 54, 38, 58, "grey1", "grey2", "ink2")
    # door leaf swung out on the left
    poly(im, [(1, 6), (10, 2), (10, 57), (1, 54)], "grey3", "grey4")
    poly(im, [(3, 10), (8, 8), (8, 50), (3, 52)], "blue0")
    for y in range(8, 52):
        for x in range(3, 9):
            if (x + y) % 6 in (0, 1) and (x + y) % 2 == 0:
                px(im, x, y, "blue4")
    line(im, [(1, 6), (1, 54)], "grey4")
    line(im, [(10, 2), (10, 57)], "grey2")
    return ol(im)


# ================================================================ counter / register
def counter():
    im = new(64, 30)
    bx(im, 1, 1, 62, 3, "white", "white", "grey4")
    bx(im, 1, 4, 62, 6, "grey3", "grey4", "grey2")
    for x in range(2, 62, 2):                       # surface sparkle dither
        px(im, x, 2, "grey4")
    bx(im, 2, 7, 61, 28, "wall3", "grey4", "grey3")
    dither_grad(im, (3, 17, 61, 25), "wall3", "grey3", "y", 4, 0.0, 0.9)
    for x in (21, 42):
        line(im, [(x, 7), (x, 24)], "grey2")
        line(im, [(x + 1, 7), (x + 1, 24)], "grey4")
    bx(im, 2, 25, 61, 28, "ink2", "grey1", "ink")
    line(im, [(2, 25), (61, 25)], "grey1")
    # sticker on left panel
    bx(im, 6, 11, 15, 16, "yellow2", "white", "orange3")
    rect(im, 8, 13, 3, 2, "red2"); rect(im, 12, 13, 2, 2, "red1")
    # drawer pulls on right
    for y in (11, 18):
        rect(im, 47, y, 8, 2, "grey2"); rect(im, 47, y, 8, 1, "grey4")
    # middle: tiny card slot plaque
    bx(im, 28, 12, 35, 17, "grey3", "grey4", "grey2")
    rect(im, 30, 14, 4, 1, "ink")
    return ol(im)


def register():
    im = new(22, 20)
    # screen housing
    bx(im, 5, 1, 17, 8, "grey3", "grey4", "grey2")
    rect(im, 7, 2, 9, 5, "ink")
    rect(im, 8, 3, 7, 3, "green1")
    for x, w in ((8, 3), (12, 2)):
        rect(im, x, 3, w, 1, "green3")
    rect(im, 8, 5, 4, 1, "green2")
    rect(im, 9, 9, 4, 1, "grey2")           # neck
    # body
    bx(im, 1, 10, 20, 18, "grey3", "grey4", "grey2")
    for ky in (11, 13):
        for kx in range(3, 12, 3):
            rect(im, kx, ky, 2, 1, "white")
            px(im, kx, ky + 1 - 1, "white")
    rect(im, 14, 11, 4, 3, "orange2"); rect(im, 14, 11, 4, 1, "orange3")
    rect(im, 3, 15, 16, 2, "grey1"); rect(im, 3, 15, 16, 1, "ink2")
    rect(im, 8, 16, 6, 1, "grey3")
    return ol(im)


# ================================================================ boxes
def cbox(im, x, y, w, h, th=4, label=True, tape=True):
    rect(im, x, y, w, h, outline="ink")
    # top face
    rect(im, x + 1, y + 1, w - 2, th - 1, "brown3")
    line(im, [(x + 1, y + 1), (x + w - 2, y + 1)], "orange4")
    rect(im, x + w - 3, y + 2, 2, th - 2, "brown2")
    line(im, [(x + 1, y + th), (x + w - 2, y + th)], "brown1")
    # front
    bx(im, x + 1, y + th + 1, x + w - 2, y + h - 2, "brown2", "brown3", "brown1")
    dither_grad(im, (x + w - 5, y + th + 1, x + w - 1, y + h - 1), "brown2", "brown1", "x", 2, 0.4, 0.4)
    px(im, x + w - 2, y + th + 1, "brown1")
    if tape:
        tx = x + w // 2 - 1
        rect(im, tx, y + 1, 3, th - 1, "wall1")
        rect(im, tx, y + th + 1, 3, max(2, (h - th) // 3), "wall1")
        line(im, [(tx + 2, y + th + 1), (tx + 2, y + th + max(2, (h - th) // 3))], "grey3")
    if label and w >= 16 and h >= 12:
        lx, ly = x + 2, y + h - 6
        rect(im, lx, ly, 6, 4, "white")
        for k in range(0, 5, 2):
            line(im, [(lx + 1 + k, ly + 1), (lx + 1 + k, ly + 2)], "ink2")
        px(im, lx + 5, ly, "red2")


def box_closed():
    im = new(20, 16)
    cbox(im, 1, 1, 18, 14, 5)
    return im


def box_open():
    im = new(20, 16)
    # flaps standing open (left tilts out, right tilts out)
    poly(im, [(1, 7), (3, 1), (6, 1), (5, 7)], "brown3")
    line(im, [(3, 2), (5, 6)], "orange4")
    poly(im, [(18, 7), (16, 1), (13, 1), (14, 7)], "brown2")
    line(im, [(14, 7), (13, 2)], "brown1")
    # dark interior
    rect(im, 4, 5, 12, 4, "brown0")
    dither_grad(im, (5, 5, 15, 9), "brown0", "brown1", "y", 2, 0.0, 0.5)
    px(im, 8, 5, "brown3"); px(im, 9, 4, "brown3"); px(im, 10, 4, "brown3")   # contents peeking
    # front body
    rect(im, 1, 8, 18, 7, outline="ink")
    bx(im, 2, 9, 17, 13, "brown2", "brown3", "brown1")
    dither_grad(im, (14, 9, 18, 14), "brown2", "brown1", "x", 2, 0.4, 0.4)
    rect(im, 3, 10, 6, 3, "white")
    px(im, 4, 11, "ink2"); px(im, 6, 11, "ink2"); px(im, 7, 10, "red2")
    line(im, [(2, 9), (17, 9)], "brown3")
    return ol(im)


def box_stack():
    im = new(24, 40)
    cbox(im, 0, 24, 24, 16, 5)
    cbox(im, 2, 11, 19, 14, 4, label=True, tape=True)
    cbox(im, 4, 1, 14, 11, 3, label=False)
    return im


# ================================================================ cleaning bits
def mop_bucket():
    im = new(20, 26)
    # mop handle
    line(im, [(11, 12), (16, 1)], "brown3", 2)
    line(im, [(12, 12), (17, 1)], "brown1")
    # strands draped over rim
    for i, (x, y1) in enumerate(((3, 14), (5, 15), (7, 14), (9, 13))):
        line(im, [(x + 1, 8), (x, y1)], "white")
        line(im, [(x + 2, 8), (x + 1, y1 - 1)], "grey3")
    # bucket
    poly(im, [(2, 11), (17, 11), (15, 24), (4, 24)], "yellow")
    for y in range(11, 25):                                  # left highlight & right shade
        xl = 2 + (y - 11) * 2 / 13
        xr = 17 - (y - 11) * 2 / 13
        px(im, int(xl + 1), y, "yellow2")
        px(im, int(xr), y, "orange2"); px(im, int(xr) - 1, y, "orange2")
    dither_grad(im, (5, 19, 15, 24), "yellow", "orange2", "y", 4, 0.0, 0.9)
    # rim
    bx(im, 1, 9, 18, 11, "orange3", "yellow2", "orange2")
    # water band + mark
    rect(im, 3, 9, 14, 2, "blue3")
    for x in range(3, 17, 2):
        px(im, x, 9, "blue4")
    rect(im, 7, 15, 6, 3, "red2"); rect(im, 8, 16, 4, 1, "white")
    line(im, [(4, 24), (15, 24)], "orange1")
    return ol(im)


def wet_sign():
    im = new(14, 20)
    poly(im, [(5, 1), (8, 1), (12, 18), (1, 18)], "yellow")
    for y in range(2, 18):                                   # highlight / shade columns
        xl = 5 - (y - 1) * 4 / 17
        xr = 8 + (y - 1) * 4 / 17
        px(im, int(round(xl)) + 1, y, "yellow2")
        px(im, int(round(xr)) - 1, y, "orange2")
    dither_grad(im, (2, 14, 12, 18), "yellow", "orange2", "y", 4, 0.0, 0.8)
    rect(im, 6, 4, 2, 6, "ink"); rect(im, 6, 12, 2, 2, "ink")
    line(im, [(0, 18), (13, 18)], "orange1")
    return ol(im)


def trash_bag():
    im = new(16, 16)
    ellipse(im, 1, 5, 14, 14, "ink2")
    poly(im, [(5, 6), (4, 2), (7, 4), (8, 2), (9, 4), (12, 2), (11, 6)], "ink2")
    rect(im, 6, 5, 4, 1, "grey1")                            # tie
    line(im, [(7, 4), (8, 4)], "grey1")
    # glossy highlights from top-left
    line(im, [(3, 8), (3, 11)], "grey2")
    line(im, [(4, 7), (6, 7)], "grey2")
    px(im, 4, 12, "grey1"); px(im, 5, 13, "grey1")
    for y, x in ((9, 8), (11, 10), (10, 12), (8, 11)):
        px(im, x, y, "grey1")
    line(im, [(7, 7), (6, 9)], "grey1")
    # cell shadow on right
    for y in range(8, 13):
        px(im, 13, y, "ink")
    return ol(im)


def hand_truck():
    im = new(20, 34)
    # frame rail + top handle bending right
    bx(im, 4, 3, 6, 29, "blue2", "blue3", "blue1")
    bx(im, 4, 1, 11, 3, "blue2", "blue3", "blue1")
    bx(im, 10, 1, 12, 6, "blue2", "blue3", "blue1")
    # brace
    line(im, [(7, 14), (7, 25)], "grey2")
    line(im, [(7, 25), (10, 29)], "grey2")
    # nose plate
    bx(im, 4, 29, 17, 31, "grey3", "grey4", "grey2")
    # wheel
    ellipse(im, 6, 25, 14, 33, "ink2")
    ellipse(im, 8, 27, 12, 31, "grey1")
    rect(im, 9, 28, 2, 2, "grey3")
    return ol(im)


# ================================================================ staff door
def door(ajar):
    im = new(30, 52)
    bx(im, 1, 1, 28, 50, "grey3", "grey4", "grey2")             # frame
    if not ajar:
        bx(im, 3, 3, 26, 50, "wall3", "grey4", "grey3")
        dither_grad(im, (4, 24, 26, 50), "wall3", "grey3", "y", 4, 0.0, 0.8)
        for x in (24, 25):
            line(im, [(x, 4), (x, 49)], "grey3")
        # staff plaque
        bx(im, 8, 8, 21, 14, "white", "white", "grey3")
        rect(im, 10, 10, 6, 2, "red2"); rect(im, 17, 10, 3, 2, "ink2")
        # panel lines
        rect(im, 6, 18, 18, 22, outline="grey2")
        # lever handle
        bx(im, 20, 29, 25, 31, "grey4", "white", "grey2")
        rect(im, 22, 33, 2, 2, "ink2")
        # kick plate
        bx(im, 4, 42, 25, 49, "grey3", "grey4", "grey2")
        for x in (6, 23):
            px(im, x, 44, "grey1"); px(im, x, 47, "grey1")
        for y in (20, 36):
            rect(im, 3, y, 2, 3, "grey2")                       # hinges
        return ol(im)
    # ajar: dark gap with red glow, door leaf narrowed on hinge side
    rect(im, 3, 3, 24, 48, "ink")
    dither_grad(im, (3, 3, 27, 51), "red1", "red3", "x", 2, 0.0, 1.0)
    dither_grad(im, (3, 3, 27, 51), "red0", "red1", "y", 2, 0.0, 0.8,
                mask=None) if False else None
    for y in range(3, 51):                                       # glow strongest mid-height
        for x in range(17, 27):
            d = abs(y - 27) / 24
            if (1 - d) * (x - 16) / 10 > ((x % 2) * 2 + (y % 2) + 0.5) / 4 * 0.9:
                px(im, x, y, "red4" if (x + y) % 2 == 0 and x > 22 else "red3")
    poly(im, [(3, 3), (18, 6), (18, 48), (3, 50)], "wall3")
    poly(im, [(3, 3), (18, 6), (18, 48), (3, 50)], None, "grey4")
    dither_grad(im, (4, 30, 18, 49), "wall3", "grey3", "y", 4, 0.0, 0.8,
                mask=None) if False else None
    for y in range(6, 49):
        px(im, 17, y, "grey3"); px(im, 16, y, "grey3")
    bx(im, 6, 9, 14, 14, "white", "white", "grey3")
    rect(im, 7, 10, 4, 2, "red2")
    bx(im, 13, 29, 16, 31, "grey4", "white", "grey2")
    line(im, [(18, 6), (18, 48)], "grey2")
    return ol(im)


# ================================================================ time clock / cctv
def time_clock():
    im = new(20, 28)
    bx(im, 1, 1, 18, 26, "grey3", "grey4", "grey2")
    rect(im, 3, 3, 14, 6, "ink")
    rect(im, 4, 4, 12, 4, "green0")
    for x in (5, 8, 11, 14):                                  # digits
        rect(im, x, 5, 2, 2, "green3")
    px(im, 10, 5, "green3"); px(im, 10, 7, "green3")
    # card slot with card
    rect(im, 5, 13, 10, 3, "ink")
    bx(im, 7, 8 + 2, 12, 14, "white", "white", "grey4")
    rect(im, 8, 11, 3, 1, "grey2"); rect(im, 8, 13, 2, 1, "red2")
    rect(im, 5, 14, 10, 2, "ink")
    # buttons
    rect(im, 4, 19, 4, 3, "green1"); rect(im, 4, 19, 4, 1, "green2")
    rect(im, 12, 19, 4, 3, "red2"); rect(im, 12, 19, 4, 1, "red3")
    rect(im, 3, 24, 14, 2, "grey1")
    return ol(im)


def cctv_frame(i):
    im = new(28, 22)
    bx(im, 1, 1, 26, 16, "grey3", "grey4", "grey2")
    rect(im, 3, 3, 22, 12, "ink")
    rng = random.Random(40 + i * 7)
    # scene: room with doorway
    rect(im, 4, 4, 20, 10, "grey1")
    rect(im, 4, 11, 20, 3, "grey2")
    rect(im, 15, 5, 6, 6, "ink2")
    for y in range(4, 14):
        for x in range(4, 24):
            if (x + y + i) % 2 == 0 and rng.random() < 0.32:
                px(im, x, y, rng.choice(["grey2", "ink2", "grey3"]))
    for y in range(4 + (i * 3) % 4, 14, 4):                    # rolling scan band
        for x in range(4, 24):
            if (x + y) % 2 == 0:
                px(im, x, y, "grey3")
    if i == 2:                                                 # ink figure
        rect(im, 9, 7, 2, 2, "ink"); rect(im, 8, 9, 4, 4, "ink")
        px(im, 8, 13, "ink"); px(im, 11, 13, "ink")
        px(im, 9, 7, "ink2")
    if i in (0, 2):
        px(im, 22, 5, "red3")
    # stand
    bx(im, 11, 17, 16, 18, "grey2", "grey3", "grey1")
    bx(im, 7, 19, 20, 20, "grey3", "grey4", "grey1")
    px(im, 23, 16, "green2")
    return ol(im)


# ================================================================ lights / clock
def ceiling_light(on):
    im = new(40, 8)
    bx(im, 1, 1, 38, 2, "grey3", "grey4", "grey2")
    if on:
        bx(im, 3, 3, 36, 5, "white", "white", "yellow2")
        rect(im, 3, 3, 2, 3, "grey3"); rect(im, 35, 3, 2, 3, "grey3")
        for x in range(4, 36, 2):
            px(im, x, 6, "yellow2")
        dither_grad(im, (2, 6, 38, 7), "yellow2", "yellow2", "y", 4, 0.0, 0.0)
        for x in range(2, 38):
            if x % 2 == 1:
                px(im, x, 6, "yellow2")
    else:
        bx(im, 3, 3, 36, 5, "grey3", "grey4", "grey2")
        rect(im, 3, 3, 2, 3, "grey1"); rect(im, 35, 3, 2, 3, "grey1")
        for x in range(8, 33, 6):
            px(im, x, 4, "grey2")
    return ol(im) if not on else im.copy() and ol(im)


def wall_clock():
    im = new(16, 16)
    ellipse(im, 1, 1, 14, 14, "grey4")
    ellipse(im, 3, 3, 12, 12, "white")
    for (a, b) in ((7, 3), (12, 7), (7, 12), (3, 7)):
        rect(im, a, b, 2, 2, "ink2") if False else None
    for (a, b) in ((7, 3), (8, 3), (12, 7), (12, 8), (7, 12), (8, 12), (3, 7), (3, 8)):
        px(im, a, b, "ink2")
    line(im, [(8, 8), (8, 5)], "ink")
    line(im, [(8, 8), (10, 9)], "ink")
    px(im, 7, 8, "ink"); px(im, 8, 8, "red2")
    for (a, b) in ((13, 9), (13, 10), (12, 11), (11, 12), (10, 13), (9, 13)):
        px(im, a, b, "grey3")
    px(im, 2, 5, "white"); px(im, 3, 3, "white")
    return ol(im)


# ================================================================ phone
def phone(frame=None, w=12):
    off = 0 if w == 12 else 2
    im = new(w, 20)
    dx = off
    if frame == 0:
        dx -= 1
    elif frame == 1:
        dx += 1
    bx(im, dx + 1, 1, dx + 10, 18, "ink2", "grey1", "ink")
    rect(im, dx + 2, 3, 8, 13, "blue2")
    dither_grad(im, (dx + 2, 3, dx + 10, 16), "blue3", "blue2", "y", 4)
    for k in range(0, 8):
        if (k % 4) < 1:
            px(im, dx + 2 + k, 3, "blue4")
    rect(im, dx + 4, 5, 4, 4, "white")                          # caller avatar
    rect(im, dx + 5, 6, 2, 2, "skin2")
    rect(im, dx + 3, 12, 3, 3, "green2")
    px(im, dx + 4, 13, "white")
    rect(im, dx + 7, 12, 2, 3, "red2")
    if frame == 1:
        rect(im, dx + 4, 10, 4, 1, "yellow")
    px(im, dx + 5, 2, "grey2"); px(im, dx + 6, 2, "grey2")
    rect(im, dx + 5, 17, 2, 1, "grey2")
    if frame is not None:
        for xx in (0, w - 1):
            rect(im, xx, 7, 1, 3, "yellow")
    return ol(im)


# ================================================================ items
def coin_img(wd, back=False):
    im = new(16, 16)
    x0 = 8 - wd // 2
    x1 = x0 + wd - 1
    if wd <= 3:
        rect(im, x0, 2, wd, 12, "yellow")
        line(im, [(x1, 2), (x1, 13)], "orange2")
        return ol(im)
    ellipse(im, x0, 2, x1, 13, "orange2")
    ellipse(im, x0, 2, x1 - 1, 12, "yellow")
    if wd >= 8:
        ellipse(im, x0 + 2, 4, x1 - 2, 11, None, "orange2")
        if not back:
            line(im, [(8, 5), (8, 10)], "orange1")
            line(im, [(7, 6), (9, 6)], "orange1")
            line(im, [(7, 8), (9, 8)], "orange1")
        else:
            rect(im, 7, 6, 3, 4, "orange2")
        px(im, x0 + 2, 4, "yellow2")
        px(im, x0 + 1, 5, "yellow2")
    else:
        line(im, [(8 + (1 if back else 0), 5), (8 + (1 if back else 0), 10)], "orange1")
        px(im, x0 + 1, 3, "yellow2")
    return ol(im)


def banknote():
    im = new(16, 16)
    bx(im, 1, 3, 14, 12, "green2", "green3", "green1")
    rect(im, 3, 5, 10, 6, outline="green1")
    rect(im, 6, 6, 4, 4, "green3")
    rect(im, 7, 7, 2, 2, "green1")
    for p in ((4, 6), (11, 6), (4, 9), (11, 9)):
        px(im, *p, "green1")
    dither_grad(im, (2, 10, 14, 12), "green2", "green1", "y", 2, 0.5, 0.5)
    return ol(im)


def time_card():
    im = new(16, 16)
    bx(im, 4, 1, 11, 14, "white", "white", "grey3")
    rect(im, 5, 2, 6, 3, "orange2"); rect(im, 5, 2, 6, 1, "orange3")
    for y in (6, 8, 10):
        line(im, [(5, y), (9, y)], "grey2")
    px(im, 10, 6, "grey3"); px(im, 10, 8, "grey3")
    rect(im, 8, 11, 3, 2, "red2"); px(im, 8, 11, "red3")
    return ol(im)


def receipt():
    im = new(16, 16)
    bx(im, 4, 1, 11, 14, "white", "white", "grey4")
    for x in (4, 6, 8, 10):
        px(im, x, 14, "ink") if False else None
    for x in (5, 7, 9, 11):
        im.putpixel((x, 14), (0, 0, 0, 0))
    rect(im, 5, 2, 4, 2, "ink2")
    for y in (5, 7, 9):
        line(im, [(5, y), (10, y)], "grey2")
    line(im, [(5, 11), (8, 11)], "red2")
    return ol(im)


def keyring():
    im = new(16, 16)
    ellipse(im, 4, 1, 10, 7, "ink2", "grey3")
    px(im, 5, 2, "grey4"); px(im, 6, 1, "grey4")
    # key 1 (gold) hanging left
    ellipse(im, 1, 7, 5, 11, "yellow", "yellow")
    px(im, 3, 9, "ink2"); px(im, 2, 8, "yellow2")
    rect(im, 3, 11, 2, 4, "yellow"); px(im, 5, 13, "orange2"); px(im, 5, 14, "orange2"); px(im, 4, 14, "orange2")
    # key 2 (steel) hanging right
    bx(im, 9, 7, 13, 10, "grey3", "grey4", "grey2"); px(im, 11, 8, "ink2")
    rect(im, 10, 11, 2, 4, "grey3"); px(im, 12, 12, "grey2"); px(im, 12, 14, "grey2")
    return ol(im)


def flashlight():
    im = new(16, 16)
    bx(im, 2, 6, 9, 10, "red2", "red3", "red1")
    for x in (4, 6, 8):
        px(im, x, 8, "red1")
    bx(im, 9, 4, 12, 12, "grey3", "grey4", "grey2")
    rect(im, 12, 3, 2, 10, "grey2"); rect(im, 12, 3, 2, 1, "grey3")
    rect(im, 13, 5, 1, 6, "yellow2")
    px(im, 4, 5, "grey3")                         # switch
    rect(im, 5, 4, 2, 1, "grey2")
    return ol(im)


def scanner():
    im = new(16, 16)
    bx(im, 2, 2, 13, 7, "grey4", "white", "grey2")
    rect(im, 3, 3, 5, 3, "green0"); rect(im, 4, 4, 3, 1, "green3")
    rect(im, 12, 3, 2, 4, "red2"); px(im, 12, 3, "red4")
    bx(im, 4, 8, 8, 14, "grey1", "grey2", "ink2")
    rect(im, 9, 8, 2, 2, "grey2")
    px(im, 6, 11, "grey3")
    return ol(im)


def name_badge():
    im = new(16, 16)
    bx(im, 6, 1, 9, 3, "grey3", "grey4", "grey2"); px(im, 7, 2, "ink2")
    bx(im, 2, 4, 13, 14, "white", "white", "grey3")
    rect(im, 3, 5, 10, 2, "blue2")
    rect(im, 4, 8, 3, 4, "skin2"); px(im, 4, 8, "brown1"); px(im, 5, 8, "brown1"); px(im, 6, 8, "brown1")
    for y, e in ((8, 11), (10, 11), (12, 9)):
        line(im, [(8, y), (e, y)], "grey2")
    return ol(im)


def kimbap():
    im = new(16, 16)
    poly(im, [(8, 1), (14, 13), (2, 13)], "white")
    for y in range(2, 14):                              # shade right edge
        xr = 8 + (y - 1) * 6 / 12
        px(im, int(round(xr)) - 1, y, "grey3")
    for y in range(8, 14):
        for x in range(5, 12):
            if im.getpixel((x, y))[3]:
                px(im, x, y, "ink2")
    for x in range(5, 12, 2):
        px(im, x, 9, "grey1")
    px(im, 6, 8, "grey1")
    rect(im, 7, 4, 3, 3, "red2"); px(im, 7, 4, "red3"); px(im, 8, 5, "yellow")
    line(im, [(2, 13), (13, 13)], "grey3")
    return ol(im)


def canned_coffee():
    im = new(16, 16)
    bx(im, 5, 2, 10, 14, "brown2", "brown3", "brown1")
    line(im, [(5, 2), (10, 2)], "grey3"); line(im, [(5, 3), (10, 3)], "grey2")
    rect(im, 5, 6, 6, 5, "wall1")
    rect(im, 5, 6, 1, 5, "white")
    rect(im, 7, 7, 2, 3, "brown1"); px(im, 8, 8, "wall1")
    line(im, [(5, 14), (10, 14)], "grey2")
    return ol(im)


def cup_noodle():
    im = new(16, 16)
    poly(im, [(2, 5), (13, 5), (11, 14), (4, 14)], "red2")
    for y in range(5, 15):
        px(im, 2 + (y - 5) * 2 // 9 + 1, y, "red3")
        px(im, 13 - (y - 5) * 2 // 9, y, "red1"); px(im, 12 - (y - 5) * 2 // 9, y, "red1")
    rect(im, 3, 8, 10, 3, "yellow")
    for x in range(4, 12, 3):
        px(im, x, 9, "red2")
    bx(im, 1, 3, 14, 5, "white", "white", "grey3")
    poly(im, [(11, 1), (14, 1), (14, 3)], "white")
    dither_grad(im, (8, 11, 12, 14), "red2", "red1", "x", 2, 0.5, 0.5)
    return ol(im)


def milk():
    im = new(16, 16)
    bx(im, 4, 5, 11, 14, "white", "white", "grey3")
    poly(im, [(4, 5), (6, 2), (9, 2), (11, 5)], "grey4")
    rect(im, 6, 1, 4, 2, "grey3")
    rect(im, 5, 8, 6, 4, "blue2"); rect(im, 5, 8, 6, 1, "blue3")
    rect(im, 7, 9, 2, 2, "white")
    line(im, [(4, 5), (11, 5)], "grey3")
    return ol(im)


def energy():
    im = new(16, 16)
    bx(im, 5, 1, 10, 14, "blue0", "blue1", "ink2")
    line(im, [(5, 1), (10, 1)], "grey3"); line(im, [(5, 14), (10, 14)], "grey2")
    for p in ((8, 4), (7, 5), (6, 6), (7, 7), (8, 7), (7, 8), (7, 9), (6, 10)):
        px(im, *p, "yellow")
    px(im, 9, 4, "yellow"); px(im, 9, 7, "yellow")
    return ol(im)


def lottery():
    im = new(16, 16)
    bx(im, 1, 3, 14, 12, "yellow2", "white", "orange3")
    rect(im, 2, 4, 12, 2, "green1")
    for x in (3, 7, 11):
        rect(im, x, 7, 3, 3, "grey3"); px(im, x, 7, "grey4")
    px(im, 12, 11, "red2"); px(im, 13, 11, "red2"); px(im, 3, 11, "orange2"); px(im, 4, 11, "orange2")
    return ol(im)


def envelope():
    im = new(16, 16)
    bx(im, 1, 3, 14, 12, "wall1", "white", "grey3")
    line(im, [(2, 4), (7, 8)], "grey3"); line(im, [(13, 4), (8, 8)], "grey3")
    rect(im, 7, 8, 2, 2, "red2"); px(im, 7, 8, "red3")
    rect(im, 3, 10, 3, 1, "grey3")
    return ol(im)


def charm():
    im = new(16, 16)
    bx(im, 4, 1, 11, 14, "orange4", "yellow2", "orange3")
    for x in (5, 7, 9):
        im.putpixel((x, 14), (0, 0, 0, 0))
    rect(im, 5, 2, 6, 2, "red2")
    px(im, 8, 4, "red2")
    # invented marks
    for p in ((6, 6), (7, 6), (8, 6), (9, 6), (7, 7), (8, 7), (6, 8), (9, 8), (7, 9), (8, 9)):
        px(im, *p, "red2")
    for p in ((6, 11), (7, 11), (8, 12), (9, 11), (9, 12)):
        px(im, *p, "red1")
    px(im, 8, 11, "red2")
    return ol(im)


ITEM_FUNCS = [("coin", lambda: coin_img(12)), ("banknote", banknote), ("time_card", time_card),
              ("receipt", receipt), ("keyring", keyring), ("flashlight", flashlight),
              ("barcode_scanner", scanner), ("name_badge", name_badge),
              ("triangle_kimbap", kimbap), ("canned_coffee", canned_coffee),
              ("cup_noodle", cup_noodle), ("milk_carton", milk), ("energy_drink", energy),
              ("lottery_ticket", lottery), ("envelope", envelope), ("charm", charm)]


# ================================================================ icons
def icon_from(fn):
    im = new(12, 12)
    fn(im)
    return ol(im)


def i_rule(im):
    bx(im, 2, 1, 9, 10, "white", "white", "grey3")
    rect(im, 3, 2, 6, 2, "red2")
    for y, e in ((5, 8), (7, 8), (9, 6)):
        line(im, [(3, y), (e, y)], "grey2")


def i_timer(im):
    ellipse(im, 1, 2, 10, 11, "white", "grey3")
    rect(im, 5, 0, 2, 2, "grey3")
    line(im, [(6, 6), (6, 4)], "ink"); line(im, [(6, 7), (8, 7)], "ink")
    px(im, 3, 4, "grey3")


def i_pay(im):
    ellipse(im, 1, 1, 10, 10, "orange2")
    ellipse(im, 1, 1, 9, 9, "yellow")
    px(im, 3, 3, "yellow2")
    line(im, [(5, 3), (5, 8)], "orange1")
    line(im, [(3, 5), (8, 5)], "orange1"); line(im, [(3, 7), (8, 7)], "orange1")


def i_debt(im):
    ellipse(im, 1, 1, 10, 10, "red1")
    ellipse(im, 1, 1, 9, 9, "red2")
    px(im, 3, 3, "red4")
    rect(im, 3, 5, 6, 2, "white")


def i_warn(im):
    poly(im, [(6, 1), (11, 10), (1, 10)], "yellow")
    line(im, [(6, 2), (2, 9)], "yellow2")
    line(im, [(10, 10), (3, 10)], "orange2")
    rect(im, 5, 4, 2, 3, "ink"); rect(im, 5, 8, 2, 1, "ink")


def i_eye(im):
    poly(im, [(0, 6), (3, 3), (8, 3), (11, 6), (8, 9), (3, 9)], "white")
    ellipse(im, 4, 3, 7, 8, "red2")
    rect(im, 5, 5, 2, 2, "ink")
    px(im, 4, 4, "red4")


def i_heart(im):
    h = art([".rrr.rrr.", "rPPrrrrrR", "rPrrrrrrR", "rrrrrrrrR", ".rrrrrrR.", "..rrrrR..", "...rrR...", "....R...."])
    paste(im, h, 1, 2)


def i_skull(im):
    s = art([".wwwww.", "wwwwwww", "wkkwkkw", "wkkwkkw", "wwwkwww", ".wwwww.", ".wkwkw.", ".wwwww."])
    s.putpixel((0, 1), col("grey4"));
    paste(im, s, 2, 1)
    line(im, [(3, 3), (3, 3)], "white")


def i_lock(im):
    s = art(["..3333..", ".32..23.", ".3....3.", ".3....3.", "yyyyyyyy", "yYyyyyoy", "yyykkyoy", "yyykkyoy", "yyyyyyoy", "oooooooo"])
    paste(im, s, 2, 1)


def i_check(im):
    s = art(["........gg", "......ggG.", "gg...ggG..", "Ggg.ggG...", ".GggggG...", "..GggG....", "...GG....."])
    paste(im, s, 1, 3)


def i_cross(im):
    s = art(["rr....rr", "rrr..rrr", ".rrrrrr.", "..rrrr..", "..rrrr..", ".rrrrrr.", "rrr..rrr", "rr....rr"])
    paste(im, s, 2, 2)


def speaker(im):
    s = art(["...3", "..33", "3333", "3333", "3333", "..33", "...3"])
    paste(im, s, 1, 3)
    px(im, 1, 4, "grey4"); px(im, 2, 3, "grey4")


def i_son(im):
    speaker(im)
    for p in ((7, 4), (8, 5), (8, 6), (8, 7), (7, 8), (9, 3), (10, 4), (10, 5), (10, 6), (10, 7), (9, 8)):
        px(im, *p, "white")


def i_soff(im):
    speaker(im)
    for k in range(4):
        px(im, 7 + k, 4 + k, "red3"); px(im, 10 - k, 4 + k, "red3")


def i_share(im):
    line(im, [(3, 6), (9, 3)], "grey3"); line(im, [(3, 6), (9, 9)], "grey3")
    for (x, y) in ((1, 4), (7, 1), (7, 7)):
        rect(im, x, y, 4, 4, "white")
        px(im, x, y, "grey4"); px(im, x + 3, y + 3, "grey3")
        rect(im, x + 1, y + 1, 2, 2, "blue2")


ICONS = [("rule", i_rule), ("timer", i_timer), ("pay", i_pay), ("debt", i_debt), ("warning", i_warn),
         ("eye", i_eye), ("heart", i_heart), ("skull", i_skull), ("lock", i_lock), ("check", i_check),
         ("cross", i_cross), ("sound_on", i_son), ("sound_off", i_soff), ("share", i_share)]


# ================================================================ effects
def exclaim(f):
    im = new(16, 16)
    dy = 0 if f == 0 else -1
    wdt = 0 if f == 0 else 1
    bx(im, 2 - wdt, 2 + dy, 13 + wdt, 11 + dy, "yellow", "yellow2", "orange2")
    for p in ((2 - wdt, 2 + dy), (13 + wdt, 2 + dy), (2 - wdt, 11 + dy), (13 + wdt, 11 + dy)):
        im.putpixel(p, (0, 0, 0, 0))
    poly(im, [(5, 11 + dy), (8, 11 + dy), (5, 14)], "yellow")
    px(im, 5, 14, "orange2") if False else None
    rect(im, 7, 4 + dy, 2, 4, "ink"); rect(im, 7, 9 + dy, 2, 2, "ink")
    return ol(im)


def sweat(f):
    im = new(8, 8)
    d = art([".b.", "bcb", "bcb", ".b."])
    if f == 2:
        d = art(["...", ".b.", "bcb", ".b."])
    paste(im, d, 2, 0 + f * 2 if f < 2 else 3)
    return ol(im)


def dust(f):
    im = new(16, 16)
    r = [3, 4, 5, 6][f]
    cs = [(8, 11 - f // 2, r), (8 - r, 12, r - 1), (8 + r - 1, 12, r - 1)] if f else [(8, 12, 3), (5, 12, 2), (11, 12, 2)]
    for (cx, cy, rr) in cs:
        ellipse(im, cx - rr, cy - rr, cx + rr, cy + rr, "grey4")
    for (cx, cy, rr) in cs:
        for y in range(cy - rr, cy + rr + 1):
            for x in range(cx - rr, cx + rr + 1):
                if 0 <= x < 16 and 0 <= y < 16 and im.getpixel((x, y))[3] and y > cy + rr // 2 and (x + y) % 2 == 0:
                    px(im, x, y, "grey3")
    # clip to canvas
    im = ol(im)
    if f >= 2:                                       # fade: punch out dither holes
        lvl = {2: 0.2, 3: 0.5}[f]
        for y in range(16):
            for x in range(16):
                if im.getpixel((x, y))[3] and lvl > thr2(x, y):
                    im.putpixel((x, y), (0, 0, 0, 0))
    return im


def red_eyes(f):
    im = new(16, 8)
    for ex in (2, 10):
        if f == 0:
            rect(im, ex, 3, 4, 3, "red3"); rect(im, ex + 1, 3, 2, 2, "red4")
            px(im, ex, 3, "red1"); px(im, ex + 3, 3, "red1")
            px(im, ex + 2, 4, "ink") if False else None
        else:
            rect(im, ex, 4, 4, 1, "red3"); rect(im, ex + 1, 4, 2, 1, "red4")
    for y in range(8):                               # dither glow
        for x in range(16):
            if im.getpixel((x, y))[3]:
                continue
            for ex in (4, 12):
                d = ((x - ex) ** 2 + (y - 4) ** 2 * 2.2) ** 0.5
                if d < 4 and (1 - d / 4) > thr2(x, y) * 1.1 and (x + y) % 2 == 0:
                    px(im, x, y, "red1")
    return im


def shadow_blob():
    im = new(24, 8)
    for y in range(8):
        for x in range(24):
            d = ((x - 11.5) / 12) ** 2 + ((y - 3.5) / 4) ** 2
            if d <= 1:
                if d < 0.45 or (x + y) % 2 == 0 and d < 0.8:
                    if (x + y) % 2 == 0 or d < 0.45 and False:
                        px(im, x, y, "ink")
                elif d < 0.75 and (x + y) % 2 == 0:
                    px(im, x, y, "ink")
    return im


def static_frame(f):
    rng = random.Random(900 + f)
    im = new(64, 64)
    for y in range(64):
        dens = 0.5 + 0.3 * math.sin(2 * math.pi * (2 * y / 64 + f / 4.0))
        for x in range(64):
            if (x + y + f) % 2 == 0 and rng.random() < dens:
                r = rng.random()
                px(im, x, y, "ink" if r < 0.45 else ("red1" if r < 0.8 else ("red0" if r < 0.93 else "red3")))
    return im


# ================================================================ main
def build():
    build_products()
    S(shelf(True), "shelf_unit")
    S(shelf(False), "shelf_empty")
    S(fridge(False), "fridge_door")
    S(fridge(True), "fridge_door_open")
    S(counter(), "counter")
    S(register(), "register")
    S(box_closed(), "box_closed")
    S(box_open(), "box_open")
    S(box_stack(), "box_stack")
    S(mop_bucket(), "mop_bucket")
    S(wet_sign(), "wet_floor_sign")
    S(trash_bag(), "trash_bag")
    S(hand_truck(), "hand_truck")
    S(door(False), "door_staff")
    S(door(True), "door_staff_ajar")
    S(time_clock(), "time_clock")
    SH([cctv_frame(i) for i in range(4)], "cctv", [f"cctv_{i}" for i in range(4)])
    S(ceiling_light(True), "ceiling_light_on")
    S(ceiling_light(False), "ceiling_light_off")
    S(wall_clock(), "wall_clock")
    S(phone(), "phone")
    SH([phone(0, 16), phone(1, 16)], "phone_ring", ["ring_0", "ring_1"])
    SH([fn() for _, fn in ITEM_FUNCS], "items", [n for n, _ in ITEM_FUNCS], cols=8)
    SH([coin_img(w, b) for w, b in ((12, 0), (9, 0), (5, 0), (2, 0), (5, 1), (9, 1))], "coin_spin",
       [f"coin_{i}" for i in range(6)], cols=6)
    SH([icon_from(fn) for _, fn in ICONS], "icons", [n for n, _ in ICONS], cols=7)
    SH([exclaim(0), exclaim(1)], "exclaim", ["exclaim_0", "exclaim_1"])
    SH([sweat(i) for i in range(3)], "sweat", [f"sweat_{i}" for i in range(3)])
    SH([dust(i) for i in range(4)], "dust_puff", [f"dust_{i}" for i in range(4)])
    SH([red_eyes(0), red_eyes(1)], "red_eyes", ["eyes_open", "eyes_blink"])
    SH([shadow_blob()], "shadow_blob", ["shadow_blob"])
    SH([static_frame(i) for i in range(4)], "static_overlay", [f"static_{i}" for i in range(4)])
    small = [p for p in OUT if "static_overlay" not in p]
    contact(small, "_contact/props.png", cols=8, scale=3)
    contact(OUT, "_contact/props_all.png", cols=4, scale=2)


if __name__ == "__main__":
    build()
    print(len(OUT), "files")

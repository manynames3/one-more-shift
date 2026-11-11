import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *
from PIL import Image

def A(p): return Image.open(os.path.join(ASSETS, p)).convert("RGBA")
def frame(sheet_path, name):
    j = json.load(open(os.path.join(ASSETS, sheet_path + ".json")))["frames"][name]["frame"]
    return A(sheet_path + ".png").crop((j["x"], j["y"], j["x"] + j["w"], j["y"] + j["h"]))

# ---- hand cursor redraw (12x12)
HAND = ["....##......",
        "...#oo#.....",
        "...#oo#.....",
        "...#oo###...",
        "...#oo#oo##.",
        ".###oo#oo#o#",
        "#oo#oooooooo"[:12],
        "#oooooooooo#",
        ".#ooooooooo#",
        "..#oooooooo#",
        "..#ooooooo#.",
        "...#######.."]
h = new(12, 12)
for y, r in enumerate(HAND):
    for x, ch in enumerate(r):
        if ch == "#": px(h, x, y, "ink")
        elif ch == "o": px(h, x, y, "white")
px(h, 11, 6, "ink")
save(h, "ui/cursor_hand.png", 12)

# ---- mock frames: do the pieces hold together in a real screen?
def hud(img, rule, t, pay):
    paste(img, A("ui/rule_banner.png"), 0, 0)
    paste(img, frame("props/icons", list(json.load(open(os.path.join(ASSETS, "props/icons.json")))["frames"])[0]), 37, 5)
    text(img, 60, 5, rule, "yellow", 11)
    paste(img, A("ui/hud_bottom.png"), 0, H - BAR)
    text(img, 48, H - BAR + 7, t, "white", 7)
    text(img, 129, H - BAR + 6, pay, "yellow", 9)
    paste(img, A("ui/debt_meter_fill.png").crop((0, 0, 41, 4)), 226, H - BAR + 9)

def shadow(img, x, y): paste(img, A("props/shadow_blob.png"), x + 4, y + 43)

m1 = A("bg/store_day.png")
for key, fr, x, y in [("deokgu", "left_work_0", 222, 78), ("halmae", "right_walk_1", 96, 96), ("sora", "down_idle_0", 150, 104)]:
    shadow(m1, x, y); paste(m1, frame("characters/" + key, fr), x, y)
paste(m1, A("ui/exclaim.png").crop((0, 0, 16, 16)) if os.path.exists(os.path.join(ASSETS, "ui/exclaim.png")) else frame("props/exclaim", "0") if "0" in json.load(open(os.path.join(ASSETS, "props/exclaim.json")))["frames"] else new(1, 1), 158, 90)
paste(m1, A("bg/store_fg.png"))
hud(m1, "규칙: 문 쪽을 등지지 마시오", "03:33", "₩37,200")
save(m1, "../previews/_mock/mock_store_day.png", 1)

m2 = A("bg/store_wrong.png")
shadow(m2, 150, 104); paste(m2, frame("characters/sora", "scared_0"), 150, 104)
paste(m2, tint_dither(frame("characters/regular", "down_idle_0"), "ink", 0.25), 150, 62)
paste(m2, A("bg/store_fg_wrong.png")); paste(m2, A("ui/vignette_red.png"))
hud(m2, "규칙: 문 쪽을 등지지 마시오", "03:33", "₩37,200")
save(m2, "../previews/_mock/mock_store_wrong.png", 1)

m3 = A("bg/agency_office.png")
paste(m3, frame("characters/kwak", "down_idle_0"), 144, 70); paste(m3, A("bg/agency_desk_fg.png"))
paste(m3, frame("characters/sora", "up_walk_0"), 150, 108)
paste(m3, A("portraits/kwak_sly.png").crop((2, 10, 62, 46)), 14, 116)
paste(m3, A("ui/dialog_box.png"), 10, 112)
text(m3, 80, 118, "일당은 넉넉하게. 규칙은 딱 하나.", "white", 11)
text(m3, 80, 134, "어때, 한 번만 더?", "yellow", 11)
letterbox_top = new(W, BAR, "ink"); paste(m3, letterbox_top, 0, 0)
save(m3, "../previews/_mock/mock_agency.png", 1)

m4 = A("bg/title_bg.png")
lg = A("ui/logo.png"); paste(m4, lg, (W - lg.width) // 2, 34)
text(m4, W // 2, 164, "PRESS START  ·  아무 키나 누르세요", "white", 9, align="center")
save(m4, "../previews/_mock/mock_title.png", 1)

ms = [m1, m2, m3, m4]
sh = new(W * 2 + 6, H * 2 + 6, "ink2")
for i, m in enumerate(ms): sh.paste(m, ((i % 2) * (W + 6), (i // 2) * (H + 6)))
sh = sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST)
sh.save(os.path.join(PREVIEWS, "_mock", "mock_screens.png"))

bad = {p: off_palette(Image.open(p).convert("RGBA")) for p in glob.glob(os.path.join(ASSETS, "**/*.png"), recursive=True)}
bad = {k: v for k, v in bad.items() if v}
print("off-palette files:", len(bad), list(bad)[:5])

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import *
from chibi import chibi, lying, FW, FH

CAST = {
    # player: night-shift part-timer
    "sora": dict(name_ko="소라", role="player", hair_style="bob", hair=("purple0", "purple1"),
                 top=("orange3", "orange2"), outfit="hoodie", pants=("blue1", "blue0"), shoes="white"),
    # agency manager who hands out the gigs
    "kwak": dict(name_ko="곽 실장", role="agency manager", hair_style="slick", hair=("grey1", "grey3"),
                 glasses=True, top=("green0", "ink2"), outfit="suit", tie="yellow",
                 pants=("green0", "ink2"), shoes="brown0", expr="smile"),
    # veteran coworker at the store
    "deokgu": dict(name_ko="덕구", role="coworker", hair_style="cap", hair=("brown0", "brown1"),
                   hat=("blue1", "blue0"), top=("white", "grey4"), outfit="vest",
                   vest=("blue2", "blue1"), pants=("grey1", "ink2"), shoes="ink2", expr="tired"),
    "halmae": dict(name_ko="할매", role="customer", hair_style="bun", hair=("grey3", "white"),
                   top=("purple1", "purple0"), outfit="floral", pattern="yellow",
                   pants=("brown1", "brown0"), shoes="red1", expr="smile"),
    "daeri": dict(name_ko="박 대리", role="customer", hair_style="short", hair=("ink2", "grey1"),
                  top=("blue0", "ink2"), outfit="suit", tie="red2", pants=("blue0", "ink2"),
                  shoes="ink", expr="tired"),
    "jisu": dict(name_ko="지수", role="customer", hair_style="ponytail", hair=("brown1", "brown2"),
                 top=("red2", "red1"), outfit="track", pants=("red2", "red1"), shoes="white", blush=True),
    # the thing that keeps coming back
    "regular": dict(name_ko="단골", role="entity", hair_style="long", hair=("ink", "ink2"),
                    skin=("pale2", "pale1"), top=("ink2", "ink"), outfit="coat", button="red3",
                    pants=("ink", "ink"), shoes="ink", expr="creepy"),
}


def build(key, spec):
    frames, names = [], []
    def add(n, im):
        names.append(n); frames.append(im)
    for i in range(2): add(f"down_idle_{i}", chibi(spec, "down", "idle", i))
    for i in range(4): add(f"down_walk_{i}", chibi(spec, "down", "walk", i))
    for i in range(4): add(f"left_walk_{i}", chibi(spec, "side", "walk", i))
    for i in range(4): add(f"right_walk_{i}", flip(chibi(spec, "side", "walk", i)))
    for i in range(4): add(f"up_walk_{i}", chibi(spec, "up", "walk", i))
    if spec["role"] != "entity":
        for i in range(2): add(f"scared_{i}", chibi(spec, "down", "scared", i))
        for i in range(2): add(f"left_scared_{i}", chibi(spec, "side", "scared", i))
    if spec["role"] in ("player", "coworker"):
        for i in range(2): add(f"work_{i}", chibi(spec, "down", "work", i))
        for i in range(2): add(f"left_work_{i}", chibi(spec, "side", "work", i))
        for i in range(2): add(f"right_work_{i}", flip(chibi(spec, "side", "work", i)))
    for e in ("neutral", "tired", "smile", "angry", "scared", "dead"):
        add(f"face_{e}", chibi(spec, "down", "idle", 0, e))
    sheet(frames, f"characters/{key}", names, cols=8)
    save(lying(spec, "dead" if spec["role"] != "entity" else "creepy"), f"characters/{key}_down.png")


if __name__ == "__main__":
    for k, s in CAST.items():
        build(k, s)
    with open(os.path.join(ASSETS, "characters", "cast.json"), "w") as f:
        json.dump({k: {"name_ko": s["name_ko"], "role": s["role"]} for k, s in CAST.items()}, f, ensure_ascii=False, indent=1)
    contact([f"characters/{k}.png" for k in CAST], "_contact/characters.png", cols=2, scale=3)
    print("ok")

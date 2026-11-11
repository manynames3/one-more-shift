"""Subset the Galmuri fonts to the characters the game's code actually draws.
Run after changing any on-screen string:  python3 art/subset_fonts.py"""
import glob, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chars = set(chr(c) for c in range(0x20, 0x7f)) | set("₩·…—×▼▲◀▶·")
for f in glob.glob(os.path.join(ROOT, "src", "**", "*.js"), recursive=True) + [os.path.join(ROOT, "index.html")]:
    chars |= set(open(f, encoding="utf-8").read())
chars = "".join(sorted(c for c in chars if c >= " "))
os.makedirs(os.path.join(ROOT, "public", "fonts"), exist_ok=True)
for name in ("Galmuri11", "Galmuri9"):
    out = os.path.join(ROOT, "public", "fonts", name + ".woff2")
    subprocess.check_call([sys.executable, "-m", "fontTools.subset", os.path.join(ROOT, "art", "tools", "fonts", name + ".ttf"),
                           "--text=" + chars, "--flavor=woff2", "--output-file=" + out, "--layout-features=*", "--no-hinting"])
    print(name, os.path.getsize(out), "bytes,", len(chars), "chars")

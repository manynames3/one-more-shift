"""Cut the checkout counter out of the store backgrounds so the cashier can stand behind it.
Writes bg/store_counter.png and bg/store_counter_wrong.png (320x180, transparent elsewhere)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from pxkit import ASSETS
from PIL import Image

BOX = (222, 89, 300, 143)   # counter top edge at y=89, from the left face to the wall

for src, dst in (("store_day", "store_counter"), ("store_wrong", "store_counter_wrong")):
    im = Image.open(os.path.join(ASSETS, "bg", src + ".png")).convert("RGBA")
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.crop(BOX), BOX[:2])
    out.save(os.path.join(ASSETS, "bg", dst + ".png"))
    print(dst, out.getbbox())

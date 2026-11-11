# ONE MORE SHIFT (한 번만 더) — art direction

Original rules-horror web game about a night-shift part-timer. Look: 16-bit console / PC-98 era pixel
art, framed like cinema. Mundane scenes are washed-out pastel; when things go wrong the screen turns
saturated red/orange with heavy dithering.

## Hard rules (every asset)
1. Draw ONLY through `tools/pxkit.py`. Colours come from `PAL` by name. Never invent a colour.
   `save()` snaps to the palette anyway; `off_palette(img)` must be empty before saving.
2. No anti-aliasing, no blur, no alpha other than 0/255, no smooth gradients. Every gradient is
   ordered dither: `dither_grad`, `dither_ramp`, `dither_flat`, `dither_radial`.
   `m=2` = coarse checkerboard (big flat areas, tension backdrops), `m=4` = fine dots (skies, glows).
3. Outlines: 1px `ink` around every object and character. Interior lines `ink` or the ramp's darkest
   step. Straight-on, hard edges, chunky readable shapes. Nothing thinner than 1px, no stray pixels.
4. Shading is cel-style: base + one shadow step + (optional) one highlight step from the same ramp.
   Light comes from top-left. Large surfaces get dither between two neighbouring ramp steps.
5. Text is Galmuri via `text()`. Body 11, small labels 9 (Hangul needs 9+), 7 for Latin/digits only.
   Accent text = `c="yellow", edge="ink", shadow="ink"`.
6. Canvas for full scenes is 320x180 with black letterbox bars (`letterbox(img)`): the picture lives in
   y 22..157 (136px). Floor line for walking characters is around y=150. Characters are 32x48.
7. Mood palettes:
   - mundane/day: wall1-4, grey3/4, blue3/4, pastel + small saturated product colours
   - warm interior: orange0-4, brown0-3, yellow2
   - WRONG/tension: red0-3 backdrop in m=2 dither, ink silhouettes, orange highlights, pale1/2 for the uncanny
8. Originality: everything is invented for this game. No characters, logos, titles, signage or scenes
   from any existing show, film, game or brand. No real brand names (invent Korean shop/product names).
   No real people. The cast is defined in `src/build_characters.py` (sheets in `assets/characters/`).

## Workflow
- Write one script `src/build_<area>.py` (starts with
  `sys.path.insert(0, <repo>/tools); from pxkit import *`). It must regenerate all your files when run.
- Save with `save(img, "<area>/<name>.png")` (1x into assets/, 4x into previews/). Sprite sets:
  `sheet(frames, "<area>/<name>", names)` writes PNG + atlas JSON.
- LOOK at your work: Read the file in `previews/` (4x), compare with `assets/characters/` previews for
  consistency, and iterate at least twice. Fix muddy shapes, unreadable silhouettes, missing outlines,
  areas that are flat where the style wants dither, and areas that are noisy where it wants flat.
- Finish with `contact([...], "_contact/<area>.png")` and report: files made, sizes, anything weak.

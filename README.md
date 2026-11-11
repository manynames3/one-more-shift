# ONE MORE SHIFT · 한 번만 더

A 16-bit rules-horror web game. You work the night shift at a convenience store. Each shift adds one
strange rule. Break a rule and you never clock out.

![screens](docs/art-mock.png)

## Play

- Move: arrow keys / WASD, or tap the floor
- Work: Space near a job, or tap the customer, shelf or fridge
- `L` language (한국어 / English), `M` mute

Rules stack by shift:

1. Never turn your back to the door (walking toward the camera while it watches ends the run)
2. Do not move at 03:33
3. Never ring up the Regular

Three customer complaints gets you fired. Clear the ₩500,000 debt to win.

## Develop

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static site in dist/
```

Stack: Phaser 3 + Vite, plain ES modules. No backend.

- `src/scenes/` Boot, Title, Agency (briefing), Shift (the game), Result (pay stub)
- `src/state.js` run state, translations · `src/audio.js` WebAudio chiptune and effects · `src/share.js` pay stub PNG
- `public/assets/` the art pack with `manifest.json`
- `art/` the Python scripts that draw every asset (`python3 art/src/build_<area>.py`), the style guide
  (`art/STYLE.md`), and `art/subset_fonts.py` (re-run it after changing any on-screen text)

## Deploy (Cloudflare Pages)

Build command `npm run build`, output directory `dist`.

## Credits

Original characters and art. Font: [Galmuri](https://github.com/quiple/galmuri) (SIL Open Font License).

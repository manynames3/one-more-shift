# ONE MORE SHIFT · 한 번만 더

**A 16-bit horror game you can play in a browser tab in under 10 seconds. No install, no login, no backend.**

You owe ₩40,000,000 and a night-shift agency has work for you: seven gigs, from a convenience store to a shut-down amusement park. Every night adds one strange rule. Break a rule and you never clock out.

**▶ Play it: [one-more-shift.pages.dev](https://one-more-shift.pages.dev)**

![Four screens from the game: the store shift, a broken rule, the briefing and the title](docs/art-mock.png)

---

## The problem I set out to solve

Most web games lose the player before the first interaction: a loading bar, a menu, a tutorial. I wanted a game
that is playable within one tap, readable on a phone, and gives the player something worth sharing when they lose.

## What I built

| | |
|---|---|
| **Game** | Seven gigs in a row (store, night event, dawn milk run, cinema, clinical trial, construction site, amusement park), 21 rules, a boss with two phases at the end of each gig, a story told in portrait scenes, three endings and six hidden notes. |
| **Art** | 121 original pixel-art assets, all generated from code on a single locked 45-colour palette. |
| **Audio** | Music, sound effects, a room tone for every location (wind, a ward's heart monitor, a projector through the wall, a stairwell drone) and a dread drone that builds through each night, all synthesized in the browser. Zero audio files. |
| **Scares** | Once or twice a night something no rule covers happens: Sora's double at the edge of the frame, a blackout, a whisper, the clock reading 04:44, her heartbeat. They never punish you and never fake a real rule's trigger. |
| **Accessibility** | A "Flashes: off" switch on the title screen drops camera flashes, softens shakes and replaces strobes with a steady dim. |
| **Learning curve** | Each death screen gives a one-line tip for that exact cause. First nights introduce jobs one at a time, and hints wait until nothing covers them. P, Esc or the on-screen ‖ pauses, and the game pauses itself when the tab loses focus. |
| **Languages** | Korean and English, switchable in game. |
| **Input** | Keyboard, mouse and touch from the same code path, plus an on-screen d-pad whose action button names what it will do. |
| **Sharing** | The end-of-run pay stub renders to a 720×960 PNG; a death also shares a 4-second GIF replay of the scare, recorded from the canvas and encoded in the browser. |
| **Hosting** | Static site on Cloudflare Pages. Every push to `main` deploys. |

## Results

- **12 KB of fonts instead of 930 KB.** The Korean pixel font is subset at build time to only the characters the game draws.
- **60 asset requests instead of 151.** The loader pulls only the files the current build uses.
- **About 415 KB gzipped JavaScript, 3.2 MB total site (about 1.2 MB over the wire).** It loads on a phone connection.
- **Every rule, every ending, the share flow and touch input pass an automated browser run** (headless Chromium via Playwright) with no console errors.
- **One command rebuilds any asset.** A palette change is a one-line edit, not a redraw.

## How it works

**The store is three areas.** The shop floor, the stockroom behind the staff door (restocking means fetching a box
from here), and the street out front (trash goes to the bins). Customers, the clock and the debt keep running while
you're away from the till, so every trip is a risk.

**The rules are the game.** One new rule each shift:

1. **When it comes, face the door.** Something appears in the doorway. Stop and look at it while the queue waits.
2. **If the steel door knocks, leave the stockroom.** You have about three seconds, and a box slows you down.
3. **Do not move at 03:33.** The clock stalls, the phone rings, a ₩10,000 note lands at your feet, customers keep waiting.
4. **Never ring up the Regular.** It queues like a customer and blocks the line.
5. **Don't look at what stands under the streetlamp.** Out front, the way back to the door is towards it.
6. **The Regular wears other faces.** The tell is a missing shadow.
7. **Don't open the fridge after 03:40.** After 03:40 the fridge job pays triple.

**The coworker.** 덕구 works shifts 1–3 with you and gives advice. On shift 3 he gets hungry and loses his shadow; at
03:45 the customers run and he turns into the Rat King. It spawns rats, rears up and lunges along a red line it shows
you first; after a lunge it's dazed, and that's the only time the mop hurts it. Three hits and you're done, five on it
and you finish the shift with hazard pay.

Every shift has a pay quota, so you can't hide at the register. Miss it or collect three customer complaints and you're
fired.

Each new rule gets a one-time on-screen hint until you survive it once. Die and you can continue from the same shift
twice per run, for a cleanup fee added to your debt.

**Then six more gigs, in the order the show's jobs come.** Each runs three nights with one new rule a night, one
skill check of its own and a two-phase boss on night three:

| Gig | Pay | Its own skill check | Boss |
|---|---|---|---|
| Night event, mascot handler | 75× minimum wage | fill balloons from the helium tank | the empty suit: tie five balloons on it while it's dazed |
| Dawn milk run | 200× | hop road cones on the moped | the Resident: a chase up a scissor stairwell, read the flickering bulb |
| Cinema | 100× | thread the reel on the beat | the Usher: it only exists in the projector beam |
| Clinical trial | 150× | hold still for the needle | subject 3 at the door: move only while its back is turned |
| Construction site | 500× | set the brick stack square | the Foreman: lure him under the crane hook |
| Amusement park | the rest of the debt | every kind of rule at once | 곽 실장's offer: sign, refuse and survive him, or hand over the six notes |

Your debt and earnings carry from gig to gig, and each gig's clue points at 준호, the brother who never clocked out.

**Balance is tested with bots.** A bot that never leaves the register used to win every run; now it misses the quota by
shift 2–3, while a bot that serves first and does side jobs when the till is clear survives. Bot testing also surfaced
a movement bug on low frame rates that would have hit players on slower phones.

**The art is a build artifact.** `art/tools/pxkit.py` holds the palette, ordered-dither functions, outline pass and
sprite-sheet packer. `art/src/build_*.py` draw every background, character, prop and UI element through it, so
nothing can drift off-style. `art/STYLE.md` is the rulebook.

## Skills this project shows

- **Shipping end to end:** concept, art pipeline, game code, testing and deployment, in one repo.
- **Front-end engineering:** Phaser 3, Vite, ES modules, WebAudio, Canvas, the Web Share API.
- **Performance work with measured outcomes:** font subsetting, selective asset loading, integer-pixel scaling on any screen.
- **Automation:** code-generated assets, scripted browser tests, push-to-deploy.
- **Localization:** two languages from day one, including a Korean bitmap font pipeline.

## Run it locally

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static site in dist/
```

Controls: arrow keys or WASD to move, Space to work. On touch, use the on-screen d-pad and action button, or tap
where to go. `L` switches language, `M` mutes.

## Project layout

```
src/scenes/     Boot, Title, Board (job board), Agency (briefing), Shift (the store), Event, Delivery, Cinema,
                Ward, Site, Park (the other gigs), gig.js (shared HUD, dialogue, skill checks), Result, Ending
src/state.js    run state and translations
src/audio.js    WebAudio music and effects
src/share.js    pay-stub PNG renderer
public/assets/  the art pack and manifest.json
art/            Python scripts that draw every asset, the style guide, the font subsetter
```

After changing any on-screen text, run `python3 art/subset_fonts.py` so the font includes the new characters.

## Deploy

Cloudflare Pages: build command `npm run build`, output directory `dist`.

## What's next

- Hand playtests on phones to tune each gig's pay target (pay targets are currently tuned by a human-speed bot).
- A unique death animation per rule.
- Launch posts for Korean and English communities.

## Credits

Original characters, art and code, built in collaboration with Claude (Anthropic).
Font: [Galmuri](https://github.com/quiple/galmuri), SIL Open Font License.

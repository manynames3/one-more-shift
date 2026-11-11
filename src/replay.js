// Death replay: keeps the last few seconds of the canvas and turns them into a shareable GIF.
//
// startReplay(game)  begin recording (a rolling buffer, ~10 fps)
// endReplay(ms)      keep recording for ms more (to catch the scare), then stop
// cancelReplay()     drop everything (clocked out, fired, quit)
// replayGif()        Promise<Blob|null>, a 640x360 looping GIF of the death

const STEP_MS = 100;    // capture every 100 ms
const KEEP = 40;        // 4 seconds
const W = 320, H = 180;

let game = null, cv = null, ctx = null;
let frames = [], recording = false, last = 0, stopAt = 0;

function onPostRender() {
  if (!recording) return;
  const now = performance.now();
  if (now - last < STEP_MS) return;
  last = now;
  // WebGL's drawing buffer is still valid right after render, so copy it now.
  ctx.drawImage(game.canvas, 0, 0, W, H);
  frames.push(ctx.getImageData(0, 0, W, H));
  if (frames.length > KEEP) frames.shift();
  if (stopAt && now >= stopAt) stop();
}

function stop() {
  recording = false; stopAt = 0;
  if (game) game.events.off("postrender", onPostRender);
}

export function startReplay(g) {
  game = g;
  if (!cv) {
    cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    ctx = cv.getContext("2d", { willReadFrequently: true });
  }
  frames = []; last = 0; stopAt = 0; recording = true;
  game.events.off("postrender", onPostRender);
  game.events.on("postrender", onPostRender);
}

export function endReplay(ms) { if (recording) stopAt = performance.now() + ms; }

export function cancelReplay() { stop(); frames = []; }

export function hasReplay() { return !recording && frames.length > 8; }

/** Encode the buffered frames as a 2x nearest-neighbour GIF. */
export async function replayGif(scale = 2) {
  if (!hasReplay()) return null;
  const { GIFEncoder, quantize, applyPalette } = await import("gifenc");
  const OW = W * scale, OH = H * scale;
  const up = new Uint8ClampedArray(OW * OH * 4);
  // one shared palette from a sample of frames keeps colours stable between frames
  const sample = new Uint8ClampedArray(W * H * 4 * 4);
  [0, 0.33, 0.66, 1].forEach((f, i) => sample.set(frames[Math.round(f * (frames.length - 1))].data, i * W * H * 4));
  const palette = quantize(sample, 256, { format: "rgb565" });
  const gif = GIFEncoder();
  for (let i = 0; i < frames.length; i++) {
    const src = frames[i].data;
    for (let y = 0; y < OH; y++) {
      const sy = (y / scale) | 0;
      for (let x = 0; x < OW; x++) {
        const s = (sy * W + ((x / scale) | 0)) * 4, d = (y * OW + x) * 4;
        up[d] = src[s]; up[d + 1] = src[s + 1]; up[d + 2] = src[s + 2]; up[d + 3] = 255;
      }
    }
    const index = applyPalette(up, palette, "rgb565");
    const last = i === frames.length - 1;
    gif.writeFrame(index, OW, OH, { palette: i === 0 ? palette : undefined, delay: last ? 1500 : STEP_MS, repeat: 0 });
    if (i % 6 === 5) await new Promise(r => setTimeout(r, 0));   // keep the page responsive
  }
  gif.finish();
  return new Blob([gif.bytes()], { type: "image/gif" });
}

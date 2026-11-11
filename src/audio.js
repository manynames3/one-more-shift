// Tiny WebAudio chiptune + sound effects. No audio files.
import { S } from "./state.js";

let ctx = null, master = null, musicGain = null, timer = null;
let step = 0, nextT = 0, mood = "off";

const LEAD = [69, 0, 72, 76, 0, 72, 69, 0, 67, 0, 71, 74, 0, 71, 67, 0, 65, 0, 69, 72, 0, 69, 65, 0, 64, 0, 68, 71, 0, 76, 74, 72];
const BASS = [45, 45, 43, 43, 41, 41, 40, 40];
const hz = n => 440 * Math.pow(2, (n - 69) / 12);

export function init() {
  if (ctx) { if (ctx.state === "suspended") ctx.resume(); return; }
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  ctx = new AC();
  master = ctx.createGain(); master.gain.value = S.muted ? 0 : 0.5; master.connect(ctx.destination);
  musicGain = ctx.createGain(); musicGain.gain.value = 0.5; musicGain.connect(master);
}

export function setMuted(m) { if (master) master.gain.value = m ? 0 : 0.5; }

function tone(freq, dur, { type = "square", vol = 0.2, at = 0, slide = 0, dest = null, detune = 0 } = {}) {
  if (!ctx) return;
  const t0 = ctx.currentTime + at;
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, t0); o.detune.value = detune;
  if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(20, freq * slide), t0 + dur);
  g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.0008, t0 + dur);
  o.connect(g); g.connect(dest || master); o.start(t0); o.stop(t0 + dur + 0.02);
}

function noise(dur, vol = 0.2, at = 0) {
  if (!ctx) return;
  const n = Math.floor(ctx.sampleRate * dur), buf = ctx.createBuffer(1, n, ctx.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
  const s = ctx.createBufferSource(), g = ctx.createGain();
  s.buffer = buf; g.gain.value = vol; s.connect(g); g.connect(master); s.start(ctx.currentTime + at);
}

const SFX = {
  ui: () => tone(660, 0.06, { vol: 0.15 }),
  type: () => tone(520, 0.02, { vol: 0.05 }),
  coin: () => { tone(988, 0.07, { vol: 0.16 }); tone(1319, 0.18, { vol: 0.16, at: 0.07 }); },
  serve: () => { tone(1568, 0.05, { vol: 0.12 }); tone(1047, 0.05, { vol: 0.12, at: 0.06 }); tone(1568, 0.16, { vol: 0.12, at: 0.12 }); },
  work: () => tone(196, 0.05, { type: "triangle", vol: 0.2 }),
  door: () => { tone(784, 0.22, { type: "sine", vol: 0.22 }); tone(622, 0.4, { type: "sine", vol: 0.22, at: 0.22 }); },
  warn: () => { tone(110, 0.5, { type: "sawtooth", vol: 0.16, slide: 0.7 }); tone(116, 0.5, { type: "sawtooth", vol: 0.12, slide: 0.7 }); },
  tick: () => tone(1800, 0.03, { vol: 0.1 }),
  bell: () => { tone(330, 1.6, { type: "sine", vol: 0.28 }); tone(332, 1.6, { type: "triangle", vol: 0.14 }); },
  strike: () => { tone(220, 0.12, { vol: 0.2 }); tone(165, 0.25, { vol: 0.2, at: 0.12 }); },
  stamp: () => { noise(0.12, 0.35); tone(90, 0.2, { type: "triangle", vol: 0.4 }); },
  win: () => [523, 659, 784, 1047].forEach((f, i) => tone(f, 0.22, { vol: 0.16, at: i * 0.11 })),
  fail: () => { noise(0.9, 0.4); tone(440, 1.2, { type: "sawtooth", vol: 0.3, slide: 0.12 }); tone(466, 1.2, { type: "square", vol: 0.2, slide: 0.1 }); },
};

export function sfx(name) { if (ctx && SFX[name]) SFX[name](); }

function schedule() {
  if (!ctx || mood === "off") return;
  const wrong = mood === "watch";
  const spb = wrong ? 0.21 : 0.15;
  while (nextT < ctx.currentTime + 0.25) {
    const at = Math.max(0, nextT - ctx.currentTime);
    const n = LEAD[step % LEAD.length];
    if (n) tone(hz(n + (wrong ? -1 : 0)), spb * 0.9, { vol: wrong ? 0.05 : 0.07, at, dest: musicGain, detune: wrong ? -45 : 0 });
    if (step % 4 === 0) tone(hz(BASS[(step / 4) % BASS.length | 0] + (wrong ? -6 : 0)), spb * 3.2, { type: "triangle", vol: 0.16, at, dest: musicGain });
    step++; nextT += spb;
  }
}

// mood: "off" | "normal" | "watch"
export function music(m) {
  mood = m;
  if (!ctx) return;
  if (m === "off") { if (timer) { clearInterval(timer); timer = null; } return; }
  if (!timer) { nextT = ctx.currentTime + 0.05; timer = setInterval(schedule, 80); }
}

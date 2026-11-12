// Chiptune music and sound effects, synthesized with WebAudio. No audio files.
//
// music(name)   "title" | "office" | "store" | "watch" | "result" | "off"
// jingle(name)  one-shot cues: "clockout" | "gameover" | "debtfree"
// ambience(on)  fluorescent hum under the store scenes
// sfx(name)     see SFX below
import { S } from "./state.js";

let ctx = null, master = null, comp = null, musicBus = null, sfxBus = null, ambBus = null;
let noiseBuf = null;
const waves = {};
let song = null;          // { def, gain, step, nextT }
let timer = null, ambNodes = null, unlocked = false;

const MASTER = 0.9;

// ------------------------------------------------------------------ setup
function build(c, dest) {
  ctx = c;
  comp = c.createDynamicsCompressor();
  comp.threshold.value = -16; comp.knee.value = 10; comp.ratio.value = 4; comp.attack.value = 0.004; comp.release.value = 0.2;
  master = c.createGain(); master.gain.value = S.muted ? 0 : MASTER;
  comp.connect(master); if (dest) master.connect(dest);
  musicBus = c.createGain(); musicBus.gain.value = 0.55; musicBus.connect(comp);
  sfxBus = c.createGain(); sfxBus.gain.value = 0.9; sfxBus.connect(comp);
  ambBus = c.createGain(); ambBus.gain.value = 1; ambBus.connect(comp);
  const n = c.sampleRate;
  noiseBuf = c.createBuffer(1, n, n);
  const d = noiseBuf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
  for (const k in waves) delete waves[k];
}

export function init() {
  if (ctx && !(ctx instanceof OfflineAudioContext)) {
    if (ctx.state === "suspended") ctx.resume();
    return;
  }
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  // iOS: play through the silent switch like a game should
  try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch { /* older Safari */ }
  const c = new AC({ latencyHint: "interactive" });
  build(c, c.destination);
  unlocked = true;
  document.addEventListener("visibilitychange", () => {
    if (!ctx) return;
    if (document.hidden) ctx.suspend(); else ctx.resume();
  });
  if (pending) { const p = pending; pending = null; music(p); }
}

/** Turn the music down (stockroom, outside) or back up. */
export function duck(level) { if (musicBus) musicBus.gain.setTargetAtTime(0.55 * level, ctx.currentTime, 0.12); }

export function setMuted(m) { if (master) master.gain.setTargetAtTime(m ? 0 : MASTER, ctx.currentTime, 0.02); }

// ------------------------------------------------------------ instruments
const NOTE = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };
function midi(name) {
  const m = /^([A-G][#b]?)(-?\d)$/.exec(name);
  return 12 * (+m[2] + 1) + NOTE[m[1]];
}
const hz = m => 440 * Math.pow(2, (m - 69) / 12);

function wave(type) {
  if (["sine", "square", "sawtooth", "triangle"].includes(type)) return null;
  if (waves[type]) return waves[type];
  const duty = { p12: 0.125, p25: 0.25, p50: 0.5 }[type];
  const N = 48, re = new Float32Array(N), im = new Float32Array(N);
  for (let k = 1; k < N; k++) im[k] = (2 / (k * Math.PI)) * Math.sin(k * Math.PI * duty);
  return (waves[type] = ctx.createPeriodicWave(re, im));
}

function osc(type, f, t) {
  const o = ctx.createOscillator();
  const w = wave(type);
  if (w) o.setPeriodicWave(w); else o.type = type;
  o.frequency.setValueAtTime(f, t);
  return o;
}

/** A pitched note with an ADSR envelope. */
function tone(dest, { type = "p50", f, t, dur, vol = 0.2, a = 0.004, d = 0.08, s = 0.6, r = 0.06, vib = 0, slide = 0, detune = 0 }) {
  const o = osc(type, f, t), g = ctx.createGain();
  o.detune.value = detune;
  if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(20, f * slide), t + dur);
  if (vib) {
    const l = ctx.createOscillator(), lg = ctx.createGain();
    l.frequency.value = 5.6; lg.gain.setValueAtTime(0, t); lg.gain.linearRampToValueAtTime(f * vib, t + Math.min(0.25, dur));
    l.connect(lg); lg.connect(o.frequency); l.start(t); l.stop(t + dur + r + 0.05);
  }
  const end = t + Math.max(dur, a + 0.01);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(vol, t + a);
  g.gain.linearRampToValueAtTime(vol * s, t + a + d);
  g.gain.setValueAtTime(vol * s, end);
  g.gain.exponentialRampToValueAtTime(0.0001, end + r);
  o.connect(g); g.connect(dest);
  o.start(t); o.stop(end + r + 0.02);
}

/** Filtered noise burst. */
function noise(dest, { t, dur, vol = 0.2, type = "highpass", f = 1000, q = 0.7, a = 0.001, sweep = 0 }) {
  const s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), g = ctx.createGain();
  s.buffer = noiseBuf; s.loop = true;
  fl.type = type; fl.frequency.setValueAtTime(f, t); fl.Q.value = q;
  if (sweep) fl.frequency.exponentialRampToValueAtTime(Math.max(40, f * sweep), t + dur);
  g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(vol, t + a);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(fl); fl.connect(g); g.connect(dest);
  s.start(t, Math.random() * 0.9); s.stop(t + dur + 0.02);
}

const DRUM = {
  k: (d, t, v = 1) => tone(d, { type: "sine", f: 150, slide: 0.28, t, dur: 0.13, vol: 0.9 * v, a: 0.001, d: 0.02, s: 0.7, r: 0.05 }),
  s: (d, t, v = 1) => { noise(d, { t, dur: 0.16, vol: 0.32 * v, f: 1800 }); tone(d, { type: "triangle", f: 190, slide: 0.6, t, dur: 0.06, vol: 0.3 * v }); },
  h: (d, t, v = 1) => noise(d, { t, dur: 0.035, vol: 0.12 * v, f: 7500 }),
  o: (d, t, v = 1) => noise(d, { t, dur: 0.18, vol: 0.1 * v, f: 6500 }),
  r: (d, t, v = 1) => { tone(d, { type: "square", f: 820, t, dur: 0.012, vol: 0.12 * v, r: 0.02 }); noise(d, { t, dur: 0.03, vol: 0.12 * v, f: 3000, type: "bandpass", q: 2 }); },
  b: (d, t, v = 1) => noise(d, { t, dur: 0.22, vol: 0.06 * v, f: 5000, a: 0.04 }),                         // brush
  H: (d, t, v = 1) => { tone(d, { type: "sine", f: 62, slide: 0.7, t, dur: 0.14, vol: 0.95 * v, a: 0.006, d: 0.03, s: 0.6 }); }, // heartbeat
  x: (d, t, v = 1) => noise(d, { t, dur: 0.6, vol: 0.12 * v, f: 9000, a: 0.002 }),                            // crash
};

// --------------------------------------------------------------- the songs
// Each channel is a string with one token per 16th note:
//   note name (A4, C#5) = note on,  "-" = hold,  "." = rest.
// Drum channels use the DRUM letters above. Bars are separated by "|".
const SONGS = {
  // Title: moody A minor, slow lead with vibrato over a pulsing arp.
  title: {
    bpm: 96, swing: 0,
    ch: {
      lead: { type: "p25", vol: 0.13, vib: 0.012, r: 0.12, s: 0.75, notes:
        "A4 - - - - - C5 - E5 - - - D5 - C5 - | C5 - - - - - - - A4 - - - - - - - | G4 - - - C5 - - - E5 - - - G5 - - - | B4 - - - - - - - D5 - - - B4 - G4 - |" +
        "A5 - - - G5 - - - E5 - - - C5 - D5 - | E5 - - - - - - - C5 - - - A4 - - - | D5 - - - F5 - - - A5 - - - G5 - F5 - | E5 - - - - - - - G#5 - - - B5 - - - |" },
      echo: { type: "p25", vol: 0.04, vib: 0.012, r: 0.1, s: 0.7, delay: 3, detune: 7, from: "lead" },
      arp: { type: "p12", vol: 0.055, d: 0.05, s: 0.3, r: 0.03, arp: ["A3 C4 E4", "F3 A3 C4", "C4 E4 G4", "G3 B3 D4", "A3 C4 E4", "F3 A3 C4", "D4 F4 A4", "E4 G#4 B4"], pattern: [0, 1, 2, 3, 2, 1] },
      bass: { type: "triangle", vol: 0.32, s: 0.8, r: 0.05, roots: ["A2", "F2", "C3", "G2", "A2", "F2", "D3", "E2"], pattern: "R - - - - - R - . . R - - - R2 -" },
      drums: { notes: "k . . . h . . . s . . . h . k . | k . . . h . . . s . . . h . h h |" },
    },
  },
  // Agency office: lazy swung ii-V-I with a walking bass. The manager is up to something.
  office: {
    bpm: 84, swing: 0.32,
    ch: {
      lead: { type: "p25", vol: 0.09, vib: 0.008, r: 0.1, s: 0.6, notes:
        ". . . . A4 - C5 - . . E5 - D5 - . . | B4 - - - - - . . F5 - E5 - D5 - . . | E5 - - - - - - - . . . . G4 - B4 - | C#5 - - - E5 - - - G5 - - - . . . . |" +
        ". . F5 - E5 - D5 - C5 - - - A4 - . . | . . G4 - B4 - D5 - F5 - - - E5 - . . | E5 - - - - - - - D5 - C5 - B4 - - - | A4 - - - - - - - . . . . . . . . |" },
      chords: { type: "p12", vol: 0.035, s: 0.5, r: 0.05, stab: ["D4 F4 A4 C5", "B3 D4 F4 G4", "C4 E4 G4 B4", "C#4 E4 G4 A4"], pattern: ". . . . . . X - . . . . . . X -" },
      bass: { type: "triangle", vol: 0.36, s: 0.9, r: 0.03, notes:
        "D3 - - - F3 - - - A3 - - - C4 - - - | G2 - - - B2 - - - D3 - - - F3 - - - | C3 - - - E3 - - - G3 - - - B3 - - - | A2 - - - C#3 - - - E3 - - - G3 - - - |" },
      drums: { notes: "k . h . r . h . k . h k r . h . | k . h . r . h . k . h . r . h h |" },
    },
  },
  // Convenience store: bright, bouncy, a little too cheerful.
  store: {
    bpm: 126, swing: 0,
    ch: {
      lead: { type: "p50", vol: 0.09, vib: 0.006, r: 0.05, s: 0.55, notes:
        "E5 - G5 - C6 - - - B5 - G5 - E5 - - - | A5 - - - G5 - E5 - C5 - D5 - E5 - - - | F5 - A5 - C6 - A5 - G5 - F5 - E5 - D5 - | D5 - - - G5 - - - B4 - D5 - G5 - - - |" +
        "E5 - G5 - C6 - - - B5 - G5 - E5 - - - | A5 - C6 - E6 - D6 - C6 - B5 - A5 - - - | F5 - E5 - D5 - F5 - B5 - A5 - G5 - D5 - | C6 - - - G5 - E5 - C5 - - - . . . . |" },
      harm: { type: "p25", vol: 0.035, r: 0.04, s: 0.5, delay: 0, detune: 0, from: "lead", interval: -4 },
      arp: { type: "p12", vol: 0.04, d: 0.04, s: 0.25, r: 0.02, arp: ["C4 E4 G4", "A3 C4 E4", "F3 A3 C4", "G3 B3 D4", "C4 E4 G4", "A3 C4 E4", "D4 F4 A4", "C4 E4 G4"], pattern: [0, 2, 1, 2] },
      bass: { type: "triangle", vol: 0.34, s: 0.7, r: 0.03, roots: ["C3", "A2", "F2", "G2", "C3", "A2", "D3", "C3"], pattern: "R . R2 . R . R2 . R . R2 . R . R2 ." },
      drums: { notes: "k . h . s . h . k . h k s . h h | k . h . s . h . k k h . s . o . |" },
    },
  },
  // Act 2, the event: a carnival oom-pah in E minor that never quite resolves.
  event: {
    bpm: 132, swing: 0,
    ch: {
      lead: { type: "p50", vol: 0.08, vib: 0.01, r: 0.05, s: 0.55, notes:
        "E5 - - - B4 - E5 - G5 - - - F#5 - E5 - | D#5 - - - F#5 - B5 - A5 - G5 - F#5 - - - | E5 - - - G5 - B5 - C6 - B5 - A5 - G5 - | F#5 - D#5 - B4 - - - E5 - - - . . . . |" },
      arp: { type: "p12", vol: 0.04, d: 0.04, s: 0.25, r: 0.02, arp: ["E4 G4 B4", "B3 D#4 F#4", "C4 E4 G4", "B3 D#4 F#4"], pattern: [0, 2, 1, 2] },
      bass: { type: "triangle", vol: 0.32, s: 0.7, r: 0.03, roots: ["E2", "B2", "C3", "B2"], pattern: "R . . . R2 . . . R . . . R2 . . ." },
      drums: { notes: "k . . . h . h . k . . . h . h . | k . . . h . h . k . s . h . h . |" },
    },
  },
  // Act 3, the dawn milk run: a sleepy lo-fi pulse.
  milk: {
    bpm: 100, swing: 0.2,
    ch: {
      lead: { type: "p25", vol: 0.08, vib: 0.01, r: 0.1, s: 0.6, notes:
        "D5 - - - F5 - - - A5 - - - G5 - F5 - | E5 - - - - - - - C5 - - - D5 - - - | A4 - - - D5 - - - F5 - E5 - D5 - C5 - | D5 - - - - - - - . . . . . . . . |" },
      arp: { type: "p12", vol: 0.04, d: 0.06, s: 0.3, r: 0.05, arp: ["D4 F4 A4", "C4 E4 G4", "Bb3 D4 F4", "A3 C#4 E4"], pattern: [0, 1, 2, 1] },
      bass: { type: "triangle", vol: 0.32, s: 0.8, r: 0.04, roots: ["D3", "C3", "Bb2", "A2"], pattern: "R . . R . . R . R . . R . . R2 ." },
      drums: { notes: "k . h . s . h h k . h . s . h . | k . h . s . h h k k h . s . o . |" },
    },
  },
  // Act 4, the cinema: a slow organ-ish waltz in G minor, like an old intermission reel.
  cinema: {
    bpm: 88, swing: 0,
    ch: {
      lead: { type: "p25", vol: 0.09, vib: 0.018, r: 0.2, s: 0.75, notes:
        "G4 - - - Bb4 - - - D5 - - - - - - - | Eb5 - - - D5 - - - C5 - - - Bb4 - - - | A4 - - - C5 - - - F#5 - - - - - - - | G5 - - - D5 - - - Bb4 - - - . . . . |" },
      echo: { type: "p25", vol: 0.03, vib: 0.018, r: 0.2, s: 0.7, delay: 2, detune: 9, from: "lead" },
      arp: { type: "p12", vol: 0.035, d: 0.08, s: 0.3, r: 0.1, arp: ["G3 Bb3 D4", "Eb3 G3 Bb3", "D3 F#3 A3", "G3 Bb3 D4"], pattern: [0, 1, 2] },
      bass: { type: "triangle", vol: 0.3, s: 0.9, r: 0.2, roots: ["G2", "Eb2", "D2", "G2"], pattern: "R - - - - - - - R2 - - - - - - -" },
      drums: { notes: "b . . . . . . . r . . . . . . . | b . . . . . . . r . . . r . . . |" },
    },
  },
  // Act 5, the ward: a heart monitor and a held breath.
  ward: {
    bpm: 70, swing: 0,
    ch: {
      beep: { type: "p12", vol: 0.04, d: 0.05, s: 0.2, r: 0.05, notes: "C6 . . . . . . . . . . . . . . . | C6 . . . . . . . . . . . . . . . |" },
      pad: { type: "triangle", vol: 0.12, a: 0.3, s: 1, r: 0.4, notes: "C4 - - - - - - - Eb4 - - - - - - - | Ab3 - - - - - - - G3 - - - - - - - |" },
      bass: { type: "triangle", vol: 0.24, s: 0.9, r: 0.3, roots: ["C2", "Ab1"], pattern: "R - - - - - - - - - - - - - - -" },
      drums: { notes: "H . . . . . . . H . . . . . . . | H . . . . . . . H . . . . . . . |" },
    },
  },
  // Act 6, the site: clanking, heavy, E minor.
  site: {
    bpm: 118, swing: 0,
    ch: {
      lead: { type: "p50", vol: 0.08, vib: 0.004, r: 0.04, s: 0.6, notes:
        "E4 - E4 - G4 - E4 - D4 - - - B3 - - - | E4 - E4 - G4 - A4 - B4 - - - G4 - - - | C5 - B4 - A4 - G4 - F#4 - - - D4 - - - | E4 - - - - - - - . . . . . . . . |" },
      bass: { type: "triangle", vol: 0.38, s: 0.7, r: 0.03, roots: ["E2", "E2", "C2", "B1"], pattern: "R R . R R . R . R R . R R . R2 ." },
      drums: { notes: "k . x . s . k . k . x . s . h h | k . x . s . k k k . x . s s x . |" },
    },
  },
  // Act 7, the park: a music box, slightly out of tune.
  park: {
    bpm: 104, swing: 0,
    ch: {
      lead: { type: "p12", vol: 0.08, vib: 0.02, d: 0.1, s: 0.3, r: 0.25, notes:
        "C6 - E6 - G6 - E6 - C6 - G5 - E5 - G5 - | F5 - A5 - C6 - A5 - F5 - - - . . . . | E5 - G5 - C6 - G5 - Eb5 - - - D5 - - - | C5 - - - G5 - - - C5 - - - . . . . |" },
      echo: { type: "p12", vol: 0.03, vib: 0.02, d: 0.1, s: 0.3, r: 0.25, delay: 3, detune: -14, from: "lead" },
      bass: { type: "triangle", vol: 0.26, s: 0.7, r: 0.1, roots: ["C3", "F2", "C3", "G2"], pattern: "R . . . R2 . . . R . . . R2 . . ." },
      drums: { notes: "h . . . h . . . h . . . h . . . | h . . . h . . . h . . . h . h . |" },
    },
  },
  // The Rat King: fast, driving, A minor.
  boss: {
    bpm: 150, swing: 0,
    ch: {
      lead: { type: "p50", vol: 0.085, vib: 0.006, r: 0.04, s: 0.6, notes:
        "A4 - C5 - E5 - A5 - G5 - E5 - C5 - D5 - | E5 - - - D5 - C5 - B4 - G4 - B4 - - - | A4 - C5 - E5 - A5 - B5 - A5 - G5 - E5 - | F5 - E5 - D5 - C5 - B4 - - - G#4 - - - |" },
      arp: { type: "p12", vol: 0.045, d: 0.04, s: 0.25, r: 0.02, arp: ["A3 C4 E4", "G3 B3 D4", "F3 A3 C4", "E3 G#3 B3"], pattern: [0, 1, 2, 1] },
      bass: { type: "triangle", vol: 0.38, s: 0.7, r: 0.03, roots: ["A2", "G2", "F2", "E2"], pattern: "R . R2 . R . R2 . R . R2 . R R2 R R2" },
      drums: { notes: "k . h k s . h . k k h . s . h s | k . h k s . h . k . h k s s s s |" },
    },
  },
  // Something is in the doorway. Heartbeat, a low drone and a wrong-sounding arp.
  watch: {
    bpm: 66, swing: 0,
    ch: {
      drone: { type: "triangle", vol: 0.22, a: 0.3, s: 1, r: 0.4, notes: "A1 - - - - - - - - - - - - - - - | A1 - - - - - - - - - - - - - - - |" },
      drone2: { type: "p12", vol: 0.035, a: 0.4, s: 1, r: 0.4, detune: -18, notes: "D#2 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |" },
      arp: { type: "p25", vol: 0.045, d: 0.2, s: 0.2, r: 0.3, vib: 0.02, notes: "A4 . . . Bb4 . . . D#5 . . . . . E5 . | A4 . . . Bb4 . . . . . F5 . . . D#5 . |" },
      drums: { notes: "H . H . . . . . . . . . . . . . | H . H . . . . . . . . . . . . . |" },
    },
  },
  // Pay stub / game over: slow and sorry for you.
  result: {
    bpm: 72, swing: 0,
    ch: {
      lead: { type: "p25", vol: 0.11, vib: 0.014, r: 0.25, s: 0.7, notes:
        "E5 - - - D5 - - - C5 - - - B4 - - - | A4 - - - - - - - - - - - . . . . | C5 - - - B4 - - - A4 - - - G#4 - - - | A4 - - - - - - - - - - - . . . . |" },
      arp: { type: "p12", vol: 0.045, d: 0.08, s: 0.3, r: 0.1, arp: ["A3 C4 E4", "F3 A3 C4", "D3 F3 A3", "E3 G#3 B3"], pattern: [0, 1, 2, 1] , every: 2 },
      bass: { type: "triangle", vol: 0.3, s: 0.9, r: 0.2, roots: ["A2", "F2", "D2", "E2"], pattern: "R - - - - - - - R - - - - - - -" },
      drums: { notes: "k . . . . . . . b . . . . . . . | k . . . . . . . b . . . . . . . |" },
    },
  },
};

const JINGLES = {
  clockout: { bpm: 150, notes: "C5 E5 G5 C6 - - E6 - G6 - - - - - - -", bass: "C3 - - - - - G3 - C4 - - - - - - -", drums: "k . . . k . s . x . . . . . . ." },
  debtfree: { bpm: 140, notes: "G5 - G5 - G5 - E5 - . . A5 - G5 - E5 - | C6 - - - - - - - E6 - - - G6 - - - - - - - - - - -", bass: "C3 - - - C3 - - - F3 - - - G3 - - - | C3 - - - - - - - - - - - - - - - - - - - - - - -", drums: "k . h . k . h . k . h . s . s . | x . . . . . . . . . . . . . . . . . . . . . . ." },
  gameover: { bpm: 90, notes: "E5 - D#5 - D5 - C#5 - - - - - - - - -", bass: "A2 - G#2 - G2 - F#2 - - - - - - - - -", drums: ". . . . . . . . x . . . . . . ." },
};

// ----------------------------------------------------------- compile songs
function tokens(str) { return str.replace(/\|/g, " ").trim().split(/\s+/); }

/** Turn token strings into [{step, len, midi}] plus total steps. */
function parse(str, transpose = 0) {
  const tk = tokens(str), ev = [];
  tk.forEach((x, i) => {
    if (x === "-" || x === ".") return;
    let len = 1;
    while (tk[i + len] === "-") len++;
    ev.push({ step: i, len, m: midi(x) + transpose, tok: x });
  });
  return { ev, steps: tk.length };
}

function compile(def) {
  const out = { bpm: def.bpm, swing: def.swing || 0, chans: [], steps: 0 };
  for (const [name, c] of Object.entries(def.ch)) {
    let ev = [], steps = 0;
    if (name === "drums") {
      const tk = tokens(c.notes); steps = tk.length;
      tk.forEach((x, i) => { if (DRUM[x]) ev.push({ step: i, drum: x }); });
    } else if (c.from) {
      const src = def.ch[c.from];
      const p = parse(src.notes, 0); steps = p.steps;
      ev = p.ev.map(e => ({ ...e, step: (e.step + (c.delay || 0)) % p.steps, m: e.m + (c.interval || 0) }));
    } else if (c.notes) {
      const p = parse(c.notes); ev = p.ev; steps = p.steps;
    } else if (c.roots) {
      const pat = tokens(c.pattern); steps = c.roots.length * 16;
      c.roots.forEach((r, b) => pat.forEach((x, i) => {
        if (x === "-" || x === ".") return;
        let len = 1; while (pat[i + len] === "-") len++;
        const m = midi(r) + (x === "R2" ? 12 : x === "R5" ? 7 : 0);
        ev.push({ step: b * 16 + i, len, m });
      }));
    } else if (c.arp) {
      steps = c.arp.length * 16;
      const every = c.every || 1;
      c.arp.forEach((ch, b) => {
        const ns = ch.split(" ").map(midi);
        for (let i = 0; i < 16; i += every) ev.push({ step: b * 16 + i, len: 1, m: ns[c.pattern[(i / every) % c.pattern.length] % ns.length] + 12 });
      });
    } else if (c.stab) {
      const pat = tokens(c.pattern); steps = c.stab.length * 16;
      c.stab.forEach((ch, b) => pat.forEach((x, i) => {
        if (x !== "X") return;
        let len = 1; while (pat[i + len] === "-") len++;
        ch.split(" ").forEach(n => ev.push({ step: b * 16 + i, len, m: midi(n) }));
      }));
    }
    out.steps = Math.max(out.steps, steps);
    out.chans.push({ name, c, ev, steps });
  }
  // index events by step for the scheduler
  for (const ch of out.chans) {
    ch.at = new Map();
    for (const e of ch.ev) { if (!ch.at.has(e.step)) ch.at.set(e.step, []); ch.at.get(e.step).push(e); }
  }
  return out;
}
const COMPILED = Object.fromEntries(Object.entries(SONGS).map(([k, v]) => [k, compile(v)]));

function playStep(sg, step, t, dest) {
  const spb = 60 / sg.def.bpm / 4;
  for (const ch of sg.def.chans) {
    const list = ch.at.get(step % ch.steps);
    if (!list) continue;
    for (const e of list) {
      if (e.drum) { DRUM[e.drum](dest, t); continue; }
      const c = ch.c;
      tone(dest, {
        type: c.type, f: hz(e.m), t, dur: e.len * spb * 0.92, vol: c.vol, a: c.a ?? 0.004, d: c.d ?? 0.08,
        s: c.s ?? 0.6, r: c.r ?? 0.05, vib: c.vib || 0, detune: c.detune || 0,
      });
    }
  }
}

function stepTime(sg, step) {
  const spb = 60 / sg.def.bpm / 4;
  return (step % 4 === 2 ? sg.def.swing * spb : 0);
}

function tick() {
  if (!ctx || !song) return;
  const sg = song, spb = 60 / sg.def.bpm / 4;
  while (sg.nextT < ctx.currentTime + 0.2) {
    playStep(sg, sg.step % sg.def.steps, sg.nextT + stepTime(sg, sg.step), sg.gain);
    sg.step++; sg.nextT += spb;
  }
}

let pending = null;
let current = "off";

/** Switch the background track with a short crossfade. */
export function music(name) {
  if (name === "normal") name = "store";
  if (!ctx || ctx instanceof OfflineAudioContext) { pending = name; return; }
  if (name === current) return;
  current = name;
  const now = ctx.currentTime;
  if (song) {
    const old = song.gain;
    old.gain.cancelScheduledValues(now);
    old.gain.setValueAtTime(old.gain.value, now);
    old.gain.linearRampToValueAtTime(0, now + 0.35);
    setTimeout(() => old.disconnect(), 800);
    song = null;
  }
  if (name === "off" || !COMPILED[name]) return;
  const gain = ctx.createGain();
  gain.gain.setValueAtTime(0, now); gain.gain.linearRampToValueAtTime(1, now + 0.25);
  gain.connect(musicBus);
  song = { def: COMPILED[name], gain, step: 0, nextT: now + 0.08 };
  if (!timer) timer = setInterval(tick, 25);
  tick();
}

/** Short musical stinger played over (and briefly ducking) the music. */
export function jingle(name, dest = null, t0 = null) {
  if (!ctx) return;
  const j = JINGLES[name]; if (!j) return;
  const out = dest || musicBus;
  const t = t0 ?? ctx.currentTime + 0.02, spb = 60 / j.bpm / 4;
  const lead = parse(j.notes), bass = parse(j.bass);
  lead.ev.forEach(e => { tone(out, { type: "p50", f: hz(e.m), t: t + e.step * spb, dur: e.len * spb, vol: 0.13, vib: 0.008, s: 0.7, r: 0.1 }); tone(out, { type: "p25", f: hz(e.m - 12), t: t + e.step * spb, dur: e.len * spb, vol: 0.05, s: 0.6 }); });
  bass.ev.forEach(e => tone(out, { type: "triangle", f: hz(e.m), t: t + e.step * spb, dur: e.len * spb, vol: 0.32, s: 0.85 }));
  tokens(j.drums).forEach((x, i) => DRUM[x] && DRUM[x](out, t + i * spb));
  if (!dest && song) {
    const g = song.gain.gain, now = ctx.currentTime, len = lead.steps * spb;
    g.cancelScheduledValues(now); g.setValueAtTime(g.value, now);
    g.linearRampToValueAtTime(0.15, now + 0.05); g.setValueAtTime(0.15, now + len); g.linearRampToValueAtTime(1, now + len + 0.4);
  }
}

/** Fluorescent hum + fridge drone under the store. */
export function ambience(on) {
  if (!ctx) return;
  if (!on) {
    if (ambNodes) { const g = ambNodes.g; g.gain.setTargetAtTime(0, ctx.currentTime, 0.1); const n = ambNodes; ambNodes = null; setTimeout(() => n.stop(), 600); }
    return;
  }
  if (ambNodes) return;
  const t = ctx.currentTime;
  const g = ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(1, t + 0.6); g.connect(ambBus);
  const hum = osc("sawtooth", 120, t), hl = ctx.createBiquadFilter(), hg = ctx.createGain();
  hl.type = "lowpass"; hl.frequency.value = 380; hg.gain.value = 0.02;
  hum.connect(hl); hl.connect(hg); hg.connect(g);
  const buzz = ctx.createBufferSource(), bf = ctx.createBiquadFilter(), bg = ctx.createGain();
  buzz.buffer = noiseBuf; buzz.loop = true; bf.type = "bandpass"; bf.frequency.value = 2400; bf.Q.value = 3; bg.gain.value = 0.006;
  buzz.connect(bf); bf.connect(bg); bg.connect(g);
  hum.start(t); buzz.start(t);
  ambNodes = { g, stop: () => { try { hum.stop(); buzz.stop(); } catch { /* stopped */ } g.disconnect(); } };
}

// ------------------------------------------------------------------ sfx
let stepAlt = 0;
const SFX = {
  ui: (d, t) => tone(d, { type: "p25", f: 880, t, dur: 0.04, vol: 0.12, r: 0.03 }),
  hover: (d, t) => tone(d, { type: "p12", f: 1320, t, dur: 0.02, vol: 0.05 }),
  type: (d, t) => tone(d, { type: "p25", f: 420 + Math.random() * 120, t, dur: 0.018, vol: 0.06, r: 0.01 }),
  start: (d, t) => { [523, 784, 1047].forEach((f, i) => tone(d, { type: "p50", f, t: t + i * 0.06, dur: 0.08, vol: 0.12 })); DRUM.x(d, t + 0.18, 0.6); },
  coin: (d, t) => { tone(d, { type: "p50", f: 988, t, dur: 0.06, vol: 0.13 }); tone(d, { type: "p50", f: 1319, t: t + 0.06, dur: 0.22, vol: 0.13, s: 0.5, r: 0.15 }); },
  cash: (d, t) => { tone(d, { type: "p25", f: 2093, t, dur: 0.05, vol: 0.1 }); tone(d, { type: "p25", f: 2637, t: t + 0.05, dur: 0.12, vol: 0.1, r: 0.12 }); noise(d, { t: t + 0.04, dur: 0.18, vol: 0.12, f: 5000, type: "bandpass", q: 1.5 }); },
  // register: scanner beep, drawer, coins
  serve: (d, t) => { tone(d, { type: "square", f: 1760, t, dur: 0.07, vol: 0.08, r: 0.01 }); noise(d, { t: t + 0.1, dur: 0.12, vol: 0.18, f: 900, type: "lowpass" }); SFX.cash(d, t + 0.16); },
  scan: (d, t) => tone(d, { type: "square", f: 1760, t, dur: 0.06, vol: 0.07, r: 0.01 }),
  work: (d, t) => { noise(d, { t, dur: 0.07, vol: 0.18, f: 700, type: "lowpass" }); tone(d, { type: "triangle", f: 160, slide: 0.7, t, dur: 0.05, vol: 0.18 }); },
  stock: (d, t) => { [0, 0.09, 0.18].forEach((o, i) => { noise(d, { t: t + o, dur: 0.05, vol: 0.14, f: 1100 + i * 200, type: "bandpass", q: 2 }); tone(d, { type: "triangle", f: 220 + i * 40, t: t + o, dur: 0.04, vol: 0.12 }); }); },
  step: (d, t) => { stepAlt ^= 1; noise(d, { t, dur: 0.045, vol: 0.07, f: stepAlt ? 520 : 440, type: "lowpass", q: 1.5 }); },
  // door chime: the two-tone "ding-dong" of a Korean convenience store
  door: (d, t) => { tone(d, { type: "sine", f: 1319, t, dur: 0.35, vol: 0.16, s: 0.4, r: 0.3 }); tone(d, { type: "sine", f: 1047, t: t + 0.32, dur: 0.6, vol: 0.16, s: 0.4, r: 0.5 }); tone(d, { type: "triangle", f: 2638, t, dur: 0.1, vol: 0.03 }); },
  // the Regular walks in: the chime plays wrong
  door_wrong: (d, t) => { tone(d, { type: "sine", f: 1319, t, dur: 0.4, vol: 0.16, s: 0.4, r: 0.3, detune: -60 }); tone(d, { type: "sine", f: 988, t: t + 0.45, dur: 0.9, vol: 0.16, s: 0.4, r: 0.8, slide: 0.94 }); tone(d, { type: "triangle", f: 55, t, dur: 1.2, vol: 0.18, s: 0.8, r: 0.5 }); },
  task: (d, t) => { tone(d, { type: "p25", f: 1568, t, dur: 0.04, vol: 0.08 }); tone(d, { type: "p25", f: 1568, t: t + 0.08, dur: 0.04, vol: 0.08 }); },
  // eyes in the doorway: low stinger + rising noise
  warn: (d, t) => { tone(d, { type: "sawtooth", f: 82, t, dur: 0.9, vol: 0.14, slide: 0.85, s: 0.9, r: 0.3 }); tone(d, { type: "p12", f: 1245, t, dur: 0.7, vol: 0.05, vib: 0.03, s: 0.8, r: 0.3 }); noise(d, { t, dur: 0.95, vol: 0.12, f: 400, sweep: 10, type: "bandpass", q: 4, a: 0.6 }); },
  appear: (d, t) => { noise(d, { t, dur: 0.25, vol: 0.18, f: 3000, type: "highpass" }); tone(d, { type: "square", f: 98, t, dur: 0.3, vol: 0.12, slide: 0.5 }); },
  leave: (d, t) => noise(d, { t, dur: 0.6, vol: 0.08, f: 3000, sweep: 0.1, type: "bandpass", q: 2, a: 0.05 }),
  tick: (d, t) => { tone(d, { type: "square", f: 2200, t, dur: 0.012, vol: 0.09, r: 0.01 }); noise(d, { t, dur: 0.02, vol: 0.06, f: 4000 }); },
  tock: (d, t) => { tone(d, { type: "square", f: 1500, t, dur: 0.012, vol: 0.09, r: 0.01 }); noise(d, { t, dur: 0.02, vol: 0.06, f: 3000 }); },
  bell: (d, t) => { [330, 332, 661, 993].forEach((f, i) => tone(d, { type: i ? "sine" : "triangle", f, t, dur: 2.2, vol: [0.26, 0.18, 0.06, 0.03][i], a: 0.002, d: 0.3, s: 0.35, r: 1.2 })); },
  heart: (d, t) => { DRUM.H(d, t, 0.8); DRUM.H(d, t + 0.22, 0.55); },
  strike: (d, t) => { tone(d, { type: "p50", f: 233, t, dur: 0.12, vol: 0.18 }); tone(d, { type: "p50", f: 175, t: t + 0.13, dur: 0.3, vol: 0.18, slide: 0.9 }); },
  grumble: (d, t) => { tone(d, { type: "sawtooth", f: 140, t, dur: 0.35, vol: 0.06, vib: 0.08, slide: 0.8 }); },
  stamp: (d, t) => { noise(d, { t, dur: 0.14, vol: 0.4, f: 1800, type: "lowpass" }); tone(d, { type: "triangle", f: 95, slide: 0.6, t, dur: 0.18, vol: 0.5 }); },
  print: (d, t) => { for (let i = 0; i < 18; i++) noise(d, { t: t + i * 0.05, dur: 0.03, vol: 0.09, f: 2600 + (i % 3) * 400, type: "bandpass", q: 3 }); },
  // the cut to red: static + a detuned scream
  fail: (d, t) => {
    noise(d, { t, dur: 1.4, vol: 0.45, f: 3000, type: "highpass", a: 0.001 });
    [440, 466, 622].forEach((f, i) => tone(d, { type: i ? "sawtooth" : "square", f, t, dur: 1.1, vol: 0.14, slide: 0.18, vib: 0.05, s: 0.9, r: 0.3 }));
    tone(d, { type: "sine", f: 55, t, dur: 1.4, vol: 0.5, slide: 0.6, s: 0.9 });
  },
  static: (d, t) => noise(d, { t, dur: 1.6, vol: 0.12, f: 5000, type: "bandpass", q: 0.5, a: 0.01 }),
  win: (d, t) => jingle("clockout", d, t),
  swing: (d, t) => noise(d, { t, dur: 0.14, vol: 0.2, f: 900, sweep: 4, type: "bandpass", q: 1.2, a: 0.01 }),
  hitboss: (d, t) => { noise(d, { t, dur: 0.12, vol: 0.4, f: 700, type: "lowpass" }); tone(d, { type: "square", f: 220, slide: 0.5, t, dur: 0.12, vol: 0.18 }); tone(d, { type: "p25", f: 1900, slide: 1.3, t: t + 0.05, dur: 0.1, vol: 0.08 }); },
  squeak: (d, t) => tone(d, { type: "p25", f: 2400 + Math.random() * 600, slide: 1.25, t, dur: 0.07, vol: 0.05 }),
  roar: (d, t) => { tone(d, { type: "sawtooth", f: 70, t, dur: 0.9, vol: 0.2, vib: 0.08, s: 0.9 }); noise(d, { t, dur: 0.9, vol: 0.2, f: 500, type: "bandpass", q: 1.5, a: 0.05 }); for (let i = 0; i < 6; i++) tone(d, { type: "p25", f: 2200 + i * 150, slide: 1.2, t: t + i * 0.09, dur: 0.06, vol: 0.04 }); },
  clang: (d, t) => { tone(d, { type: "square", f: 1300, t, dur: 0.04, vol: 0.08 }); tone(d, { type: "triangle", f: 880, t, dur: 0.2, vol: 0.1, s: 0.3 }); },
  dash: (d, t) => noise(d, { t, dur: 0.35, vol: 0.18, f: 300, sweep: 6, type: "bandpass", q: 1, a: 0.02 }),
  // three heavy knocks on a steel door
  knock: (d, t) => { for (let i = 0; i < 3; i++) { tone(d, { type: "sine", f: 70, slide: 0.6, t: t + i * 0.16, dur: 0.12, vol: 0.7, a: 0.002 }); noise(d, { t: t + i * 0.16, dur: 0.08, vol: 0.25, f: 400, type: "lowpass" }); } },
  creak: (d, t) => { tone(d, { type: "sawtooth", f: 180, slide: 1.6, t, dur: 0.3, vol: 0.04, vib: 0.05 }); noise(d, { t: t + 0.25, dur: 0.06, vol: 0.12, f: 600, type: "lowpass" }); },
  buzz: (d, t) => { for (let i = 0; i < 5; i++) tone(d, { type: "sawtooth", f: 120, t: t + i * 0.13, dur: 0.07, vol: 0.06 }); },
  // the store phone, at the worst possible time
  ring: (d, t) => { for (let k = 0; k < 2; k++) for (let i = 0; i < 8; i++) tone(d, { type: "p25", f: i % 2 ? 1397 : 1175, t: t + k * 0.9 + i * 0.05, dur: 0.045, vol: 0.08, r: 0.01 }); },
  moped: (d, t) => { tone(d, { type: "sawtooth", f: 62, slide: 1.9, t, dur: 1.2, vol: 0.07, vib: 0.06, s: 0.9, r: 0.3 }); noise(d, { t, dur: 1.2, vol: 0.05, f: 300, type: "lowpass", a: 0.1 }); },
  ding: (d, t) => { tone(d, { type: "sine", f: 1568, t, dur: 0.5, vol: 0.12, s: 0.4, r: 0.4 }); tone(d, { type: "sine", f: 1175, t: t + 0.25, dur: 0.7, vol: 0.12, s: 0.4, r: 0.5 }); },
  slide: (d, t) => noise(d, { t, dur: 0.5, vol: 0.08, f: 1200, sweep: 0.5, type: "bandpass", q: 1.5, a: 0.08 }),
  hop: (d, t) => { tone(d, { type: "p25", f: 330, slide: 2.2, t, dur: 0.14, vol: 0.1 }); noise(d, { t: t + 0.26, dur: 0.06, vol: 0.12, f: 500, type: "lowpass" }); },
};

export function sfx(name, delay = 0) {
  if (!ctx || !SFX[name]) return;
  SFX[name](sfxBus, ctx.currentTime + 0.005 + delay);
}

// ----------------------------------------------------- offline previews
/** Render a track (or sfx list) to an AudioBuffer. Used to make listening previews. */
export async function renderOffline(kind, name, seconds) {
  const sr = 44100, oc = new OfflineAudioContext(2, Math.ceil(sr * seconds), sr);
  const keep = { ctx, master, comp, musicBus, sfxBus, ambBus, noiseBuf, song };
  build(oc, oc.destination);
  master.gain.value = MASTER;
  if (kind === "music") {
    const sg = { def: COMPILED[name], gain: musicBus, step: 0, nextT: 0.05 };
    const spb = 60 / sg.def.bpm / 4;
    while (sg.nextT < seconds - 0.5) { playStep(sg, sg.step % sg.def.steps, sg.nextT + stepTime(sg, sg.step), musicBus); sg.step++; sg.nextT += spb; }
  } else if (kind === "jingle") {
    jingle(name, musicBus, 0.05);
  } else {
    name.forEach((n, i) => SFX[n](sfxBus, 0.1 + i * 1.1));
  }
  const buf = await oc.startRendering();
  ({ ctx, master, comp, musicBus, sfxBus, ambBus, noiseBuf, song } = keep);
  for (const k in waves) delete waves[k];
  return buf;
}

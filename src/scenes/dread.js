// Things that go wrong for no reason. A night or two in, the rules start to feel learnable, so
// once or twice a night something happens that no rule covers: Sora's double standing at the edge
// of the frame, a blackout, a whisper, the clock showing a time it shouldn't, her own heartbeat.
// None of it can hurt you. All of it is drawn from what's already on screen.
// The dread drone (audio) also climbs through the night and spikes with each event.
import Phaser from "phaser";
import { W, H, BAR, C, txt } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";
import { CALM } from "../calm.js";

const KINDS = ["double", "blackout", "whisper", "clock", "heart"];
const WHISPERS = 8;
let lastKinds = [];        // across nights, so the same trick doesn't land twice in a row
let lastLine = -1;

export const DreadMixin = {
  initDread() {
    const n = this.run?.shift || 1;
    // night 1: one late event; nights 2-3: two. Keep clear of the night-3 bosses (they come at ~40-45).
    const slots = n === 1 ? [[30, 50]] : n >= 3 ? [[10, 22], [26, 36]] : [[14, 30], [36, 54]];
    this.dread = { at: slots.map(([a, b]) => Phaser.Math.Between(a, b)), fx: 0, lvl: 0, busy: false };
  },

  dreadBlocked() {
    return this.over || this.boss || this.meterState || this.talking || this.riding || this.busy || this.choosing
      || this.chosen || this.place === "ride" || (this.flick && this.flick.alpha > 0.05) || this.dread.busy;
  },

  tickDread(dt) {
    if (!this.dread) this.initDread();
    const d = this.dread;
    // the drone: rises with the clock, swells during an event, gone when the shift ends
    const target = this.over ? 0 : Math.min(1, (this.min || 0) / 60) * 0.45 + d.fx;
    d.lvl += (target - d.lvl) * Math.min(1, dt * 2);
    d.fx = Math.max(0, d.fx - dt * 0.25);
    snd.dread(d.lvl);
    if (!d.at.length || (this.min || 0) < d.at[0] || this.dreadBlocked()) return;
    d.at.shift();
    let pool = KINDS.filter(k => !lastKinds.includes(k));
    // never fake something a rule in this scene reacts to (the ward and store have lights rules, the store a clock rule)
    const skip = { Ward: ["blackout"], Shift: ["blackout", "clock"] }[this.scene.key] || [];
    pool = pool.filter(k => !skip.includes(k) && (k !== "clock" || this.hudClock));
    if (!pool.length) pool = KINDS.filter(k => !skip.includes(k));
    const kind = Phaser.Utils.Array.GetRandom(pool);
    lastKinds = [kind, ...lastKinds].slice(0, 2);
    d.busy = true; d.fx = 0.55;
    this["dread_" + kind]();
    this.time.delayedCall(2600, () => { if (this.dread) this.dread.busy = false; });
  },

  /** Her double, standing still at the far side of the screen, facing her. Gone in a flicker. */
  dread_double() {
    const p = this.p, left = p.x > W / 2, x = left ? 26 : W - 26;
    let frame = p.frame.name;
    const dir = left ? "right" : "left";
    if (this.textures.get(p.texture.key).has(dir + "_walk_0")) frame = dir + "_walk_0";
    const g = this.add.sprite(x, p.y, p.texture.key, frame).setOrigin(p.originX, p.originY)
      .setScale(p.scaleX, p.scaleY).setTintFill(0x0c0910).setAlpha(0).setDepth(p.depth - 1);
    const top = p.y - p.displayHeight * p.originY, ey = top + p.displayHeight * 0.3;
    const eyes = [-2, 2].map(o => this.add.rectangle(x + o + (left ? 1 : -1), ey, 1, 1, 0xff3040).setAlpha(0).setDepth(p.depth - 1));
    snd.sfx("leave");
    this.tweens.add({ targets: [g, ...eyes], alpha: { from: 0, to: 0.92 }, duration: 600 });
    this.time.delayedCall(1700, () => {
      snd.sfx("appear");
      this.cameras.main.flash(90, 20, 16, 26);
      g.destroy(); eyes.forEach(e => e.destroy());
    });
  },

  /** The lights die for a beat. When they come back, everything is where it was. Probably. */
  dread_blackout() {
    const r = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x07050a).setOrigin(0).setDepth(890).setAlpha(0);
    snd.sfx("buzz");
    const seq = CALM.on ? [0.3, 0.6, 0.85, 0.9, 0.95] : [0.9, 0, 0.85, 0, 0.97];
    seq.forEach((a, i) => this.time.delayedCall(i * 90, () => r.setAlpha(a)));
    this.time.delayedCall(seq.length * 90, () => snd.duck(0.15));
    this.time.delayedCall(seq.length * 90 + 900, () => {
      snd.sfx("creak"); snd.duck(1);
      this.tweens.add({ targets: r, alpha: 0, duration: 220, onComplete: () => r.destroy() });
    });
  },

  /** Something says something, just under the HUD. */
  dread_whisper() {
    let i; do i = Phaser.Math.Between(1, WHISPERS); while (i === lastLine);
    lastLine = i;
    const w = txt(this, W / 2, H - BAR - 14, t("dread_" + i), { ox: 0.5, size: 9, color: C.red, depth: 905 }).setAlpha(0);
    snd.sfx("whisper"); snd.duck(0.4);
    this.tweens.add({ targets: w, alpha: 0.85, duration: 500, yoyo: true, hold: 1100, onComplete: () => { w.destroy(); snd.duck(1); } });
    this.tweens.add({ targets: w, x: W / 2 + 2, duration: 70, yoyo: true, repeat: 8 });
  },

  /** The clock shows 04:44 for a second, and the picture tears. */
  dread_clock() {
    const c = this.hudClock;
    const fake = txt(this, c.x, c.y, "04:44", { size: 9, ox: c.originX, color: C.red, depth: c.depth + 1 }).setBackgroundColor("#14101a");
    snd.sfx("glitch");
    const bars = [];
    for (let i = 0; i < 4; i++) {
      const y = Phaser.Math.Between(BAR + 6, H - BAR - 10);
      bars.push(this.add.rectangle(Phaser.Math.Between(-20, 40), y, W, Phaser.Math.Between(1, 3), 0xf6f1e7, 0.35).setOrigin(0).setDepth(895));
    }
    this.cameras.main.shake(160, 0.004);
    this.time.delayedCall(180, () => bars.forEach(b => b.destroy()));
    this.time.delayedCall(1100, () => fake.destroy());
  },

  /** Her heartbeat, loud, and the edges of the picture close in. */
  dread_heart() {
    const g = this.add.graphics().setDepth(890);
    const draw = k => {
      g.clear();
      for (let i = 0; i < 6; i++) {
        const m = Math.round(4 + i * 5 * k);
        g.fillStyle(0x07050a, 0.16).fillRect(0, BAR, W, m).fillRect(0, H - BAR - m, W, m).fillRect(0, BAR, m, H - 2 * BAR).fillRect(W - m, BAR, m, H - 2 * BAR);
      }
    };
    const o = { k: 0 };
    snd.duck(0.3);
    [0, 0.75, 1.5].forEach(s => this.time.delayedCall(s * 1000, () => snd.sfx("heart")));
    this.tweens.add({ targets: o, k: 1, duration: 420, yoyo: true, repeat: 2, onUpdate: () => draw(o.k),
      onComplete: () => { g.destroy(); snd.duck(1); } });
  },
};

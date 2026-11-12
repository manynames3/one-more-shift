// Act 4 boss: the Usher. At 02:45 on the third cinema night, the projector comes on by itself in Hall 3
// and something in a usher's uniform walks out of the film. It only exists in the beam: while the lamp is
// on it can't be touched, and it comes for you. Cut the lamp (Space) and for a moment it's just a shape
// in the dark, standing still. Get to it and hit it before the light comes back. Four hits.
import Phaser from "phaser";
import { W, C, txt } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";

const FY = 150, LIVES = 3, HP = 4, DARK_SECS = 2.2, COOL = 2.6;
export const USHER_NIGHT = 3, USHER_MIN = 45;

export const UsherMixin = {
  bossActive() { return !!this.boss && this.boss.phase !== "done"; },

  startBoss() {
    this.clearHints(); if (this.working) this.cancelWork();
    this.queue.forEach(c => { c.spr.destroy(); c.sh.destroy(); }); this.queue = [];
    this.reel.need = false; this.hall.lockBy = 0;
    snd.music("boss"); snd.sfx("bell"); snd.sfx("static", 0.3);
    this.cut(() => {
      this.enter("hall", 250);
      const b = this.boss = { phase: "lit", x: 40, hp: HP, hits: 0, dark: 0, cool: 0, iframe: 0, lunge: 0 };
      this.screen.setVisible(true).setFrame("cctv_0");
      b.beam = this.add.image(W - 6, 40, "props_beam").setOrigin(1, 0).setDepth(55);
      b.spr = this.add.sprite(40, FY, "props_usher", "idle_0").setOrigin(0.5, 1).setDepth(95);
      b.hpTxt = txt(this, W / 2, 34, "", { ox: 0.5, size: 9, color: C.yellow, depth: 895 }).setBackgroundColor("#14101a").setPadding(2, 0, 2, 0);
      b.lives = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
      this.drawUsher();
      this.caption(t("usherStart"), 2.6);
      this.time.delayedCall(2700, () => { if (!this.over && this.boss.phase === "lit") this.hint("lamp", W / 2, 66); });
    }, 300);
  },

  drawUsher() {
    const b = this.boss;
    b.hpTxt.setText(t("usherHp", b.hp));
    b.lives.setText("♥".repeat(Math.max(0, LIVES - b.hits)) + "♡".repeat(Math.min(LIVES, b.hits)));
  },

  /** Space in the fight: hit it if it's dark and close, otherwise cut the lamp. */
  bossAct() {
    const b = this.boss;
    if (b.phase === "dark" && Math.abs(this.p.x - b.x) < 22) return this.hitUsher();
    if (b.phase === "lit" && b.cool <= 0) {
      b.phase = "dark"; b.dark = b.hp <= 2 ? DARK_SECS - 0.7 : DARK_SECS;
      this.dark.setAlpha(0.72); b.beam.setVisible(false); this.screen.setFrame("off_0");
      b.spr.setFrame("dark_0"); snd.sfx("clang"); this.unhint("lamp");
      this.hint("hit", Math.round(b.x), 60);
    }
  },

  hitUsher() {
    const b = this.boss;
    b.hp--; snd.sfx("hitboss"); this.cameras.main.shake(120, 0.006);
    b.spr.setFrame("hurt_0"); this.unhint("hit");
    this.drawUsher();
    if (b.hp <= 0) return this.winUsher();
    if (b.hp === 2) { this.caption(t("usherPhase2"), 2); snd.sfx("roar"); }
    this.lightsOn();
    b.x = b.x < W / 2 ? W - 40 : 40;    // it reappears at the far end of the beam
  },

  lightsOn() {
    const b = this.boss;
    b.phase = "lit"; b.cool = COOL; b.lunge = 0;
    this.dark.setAlpha(0); b.beam.setVisible(true); this.screen.setFrame("cctv_0");
    snd.sfx("buzz");
  },

  tickBoss(dt) {
    const b = this.boss, s = b.spr, p = this.p;
    if (!s) return;
    b.cool -= dt; b.iframe -= dt;
    if (b.phase === "dark") {
      b.dark -= dt;
      if (b.dark <= 0) { this.unhint("hit"); this.lightsOn(); }
    } else if (b.phase === "lit") {
      this.screen.setFrame("cctv_" + (Math.floor(this.time.now / 300) % 2));
      const dx = p.x - b.x, dir = Math.sign(dx) || 1;
      if (b.lunge > 0) {
        b.lunge -= dt; s.setFrame("lunge_0");
        b.x += dir * 120 * dt;
      } else {
        b.x += dir * Math.min(Math.abs(dx), (30 + (b.hp <= 2 ? 22 : 8) * (HP - b.hp)) * dt);
        s.setFrame("walk_" + (Math.floor(this.time.now / 140) % 4));
        if (Math.abs(dx) < 46 && Math.random() < dt * 1.2) { b.lunge = 0.45; snd.sfx("dash"); }
      }
      s.setFlipX(dx > 0);
      if (Math.abs(p.x - b.x) < 12 && b.iframe <= 0) this.usherHit();
      if (b.cool <= 0 && !this.hints.lamp && this.time.now > (b.hintAfter ||= this.time.now + 2700)) this.hint("lamp", W / 2, 66);
    }
    s.x = Math.round(Phaser.Math.Clamp(b.x, 14, W - 14));
  },

  usherHit() {
    const b = this.boss, p = this.p;
    b.hits++; b.iframe = 1.2;
    snd.sfx("hitboss"); this.cameras.main.flash(120, 239, 59, 74); this.cameras.main.shake(200, 0.01);
    p.x = Phaser.Math.Clamp(p.x + (p.x > b.x ? 30 : -30), 12, W - 12);
    this.tweens.add({ targets: p, alpha: 0.3, duration: 100, yoyo: true, repeat: 4 });
    this.drawUsher();
    if (b.hits >= LIVES) this.fail("usher");
  },

  winUsher() {
    const b = this.boss;
    b.phase = "done"; this.bossDone = true;
    this.dark.setAlpha(0); b.beam.setVisible(false); this.clearHints();
    this.tweens.add({ targets: b.spr, alpha: 0, duration: 900 });
    snd.music("off"); snd.jingle("clockout");
    b.hpTxt.setVisible(false); b.lives.setVisible(false);
    this.screen.setFrame("cctv_1");
    this.time.delayedCall(1400, () => this.talk("talk_cctv", () => this.clockOut()));
  },

  endBossFx() { if (this.boss?.hpTxt) { this.boss.hpTxt.setVisible(false); this.boss.lives.setVisible(false); } },
};

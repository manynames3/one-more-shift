// Act 2 boss: the empty suit. At 00:45 on the third event night the mascot's head drops and the body
// keeps going without it. It walks at Sora, crouches (the tell), then lunges. A lunge that misses leaves
// it dazed for a moment: that's when you tie a balloon to it. Five balloons and it floats away into the
// glass ceiling. Three lunges that connect and it has you.
import Phaser from "phaser";
import { W, H, C, txt } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";

const FY = 150, STAGE = 62, STAGE_Y = 128;
export const SUIT_NIGHT = 3, SUIT_MIN = 45;
const TIES = 5, LIVES = 3;

export const SuitMixin = {
  bossActive() { return !!this.boss && this.boss.phase !== "done"; },

  startBoss() {
    const b = this.boss = { phase: "rise", t: 1.4, x: STAGE, ties: 0, hits: 0, iframe: 0, dir: -1, target: 0 };
    // everyone else gets out
    this.guests.slice().forEach(g => this.leaveQueue(g, false));
    this.guestT = 999;
    this.fan.need = false; this.fanMark.setVisible(false); this.call.on = false; this.bubble.setVisible(false);
    this.head.off = false; this.clearHints(); if (this.working) this.cancelWork();
    this.mascot.setFrame("headoff_1");
    snd.music("boss"); snd.sfx("clang"); snd.sfx("roar", 0.4);
    this.cameras.main.shake(300, 0.008);
    this.caption(t("suitTurn"), 2.5);
    b.spr = this.add.sprite(STAGE, STAGE_Y, "props_suit_boss", "idle_0").setOrigin(0.5, 1).setDepth(95).setVisible(false);
    b.tiesTxt = txt(this, W / 2, 34, "", { ox: 0.5, size: 9, color: C.yellow, depth: 895 });
    b.hpTxt = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
    this.drawBossHud();
    this.hint("tie", W / 2, 52);
  },

  drawBossHud() {
    const b = this.boss;
    b.tiesTxt.setText(t("suitTies", b.ties, TIES));
    b.hpTxt.setText("♥".repeat(LIVES - b.hits) + "♡".repeat(b.hits));
  },

  tickBoss(dt) {
    const b = this.boss, s = b.spr, p = this.p;
    b.t -= dt; b.iframe -= dt;
    if (b.phase === "rise") {
      // the body steps down off the stage, the head stays behind
      if (b.t < 0.8 && !s.visible) { this.mascot.setVisible(false); s.setVisible(true); snd.sfx("hop"); this.tweens.add({ targets: s, y: FY, x: STAGE + 30, duration: 500, ease: "Quad.easeIn" }); }
      if (b.t <= 0) { b.phase = "walk"; b.x = STAGE + 30; b.t = 0; }
      return;
    }
    if (b.phase === "walk") {
      const dx = p.x - b.x;
      b.dir = Math.sign(dx) || -1;
      b.x += b.dir * Math.min(Math.abs(dx), (34 + 6 * b.ties) * dt);
      s.setFrame("idle_" + (Math.floor(this.time.now / 300) % 2)).setFlipX(b.dir > 0);
      if (Math.abs(dx) < 90 && b.t <= 0) { b.phase = "crouch"; b.t = Math.max(0.5, 0.85 - 0.06 * b.ties); s.setFrame("crouch_0"); snd.sfx("warn"); }
    } else if (b.phase === "crouch") {
      s.setFrame("crouch_0");
      if (b.t <= 0) { b.phase = "dash"; b.target = Phaser.Math.Clamp(p.x + Math.sign(p.x - b.x) * 40, 20, W - 20); snd.sfx("dash"); }
    } else if (b.phase === "dash") {
      const dx = b.target - b.x, step = 250 * dt;
      s.setFrame("dash_" + (Math.floor(this.time.now / 80) % 2)).setFlipX(dx > 0);
      if (Math.abs(dx) <= step) { b.x = b.target; b.phase = "stun"; b.t = 1.7; snd.sfx("clang"); this.cameras.main.shake(100, 0.004); }
      else b.x += Math.sign(dx) * step;
      if (Math.abs(p.x - b.x) < 14 && b.iframe <= 0) this.suitHit();
    } else if (b.phase === "stun") {
      s.setFrame("stun_" + (Math.floor(this.time.now / 200) % 2));
      if (b.t <= 0) { b.phase = "walk"; b.t = 0.6; }
    }
    s.x = Math.round(b.x);
    if (this.over) return;
    if (b.phase === "stun") this.hint("tieNow", Math.round(b.x), 60); else this.unhint("tieNow");
  },

  suitHit() {
    const b = this.boss, p = this.p;
    b.hits++; b.iframe = 1.2;
    snd.sfx("hitboss"); snd.sfx("strike", 0.05);
    this.cameras.main.shake(200, 0.01); this.cameras.main.flash(120, 239, 59, 74);
    p.x = Phaser.Math.Clamp(p.x + (p.x > b.x ? 26 : -26), 12, W - 12);
    this.tweens.add({ targets: p, alpha: 0.3, duration: 100, yoyo: true, repeat: 4 });
    this.drawBossHud();
    if (b.hits >= LIVES) this.fail("suit");
  },

  /** Space near the dazed suit while holding a balloon: tie it on. */
  tryTie() {
    const b = this.boss;
    if (b.phase !== "stun" || !this.carry || Math.abs(this.p.x - b.x) > 22) return false;
    this.carry = false; b.ties++;
    snd.sfx("stock"); snd.sfx("squeak", 0.1);
    this.drawBossHud(); this.unhint("tie");
    const bl = this.add.image(b.x + Phaser.Math.Between(-8, 8), FY - 60, b.ties % 2 ? "props_balloon" : "props_balloon_b").setOrigin(0.5, 1).setDepth(96);
    (b.balloons ||= []).push(bl);
    if (b.ties >= TIES) this.winBoss();
    else { b.phase = "walk"; b.t = 0.9; }
    return true;
  },

  winBoss() {
    const b = this.boss;
    b.phase = "done";
    b.spr.setFrame("float_0");
    b.balloons.forEach(bl => bl.destroy());
    snd.music("off"); snd.jingle("clockout");
    this.unhint("tieNow"); this.unhint("tie");
    this.tweens.add({ targets: b.spr, y: -40, duration: 3000, ease: "Quad.easeIn",
      onUpdate: () => b.spr.setFrame("float_" + (Math.floor(this.time.now / 250) % 2)) });
    b.tiesTxt.setVisible(false); b.hpTxt.setVisible(false);
    this.bossDone = true;
    // the clue: a laundry tag inside the head left on the stage
    this.time.delayedCall(2600, () => this.caption(t("clue_suit"), 3.5));
    this.time.delayedCall(6500, () => { if (!this.over) this.clockOut(); });
  },

  endBossFx() { if (this.boss?.tiesTxt) { this.boss.tiesTxt.setVisible(false); this.boss.hpTxt.setVisible(false); } },
};

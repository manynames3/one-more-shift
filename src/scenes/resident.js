// Act 3 boss: the Resident. At 02:15 on the third milk run, something starts down the stairs.
// The officetel has a scissor stairwell: every landing has two flights up, left and right.
// The bulb over the flight it's coming down flickers and an eye shows at the top: take the other one.
// Wrong flight, or standing still too long, and it reaches you. Three times and it keeps you.
// Make it to the roof (floor 6) and there's a phone on the ledge.
import Phaser from "phaser";
import { W, C, txt } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";

const FY = 150, ROOF = 6, LIVES = 3;
export const CHASE_NIGHT = 3, CHASE_MIN = 45;
const BULB = { L: { x: 57, y: 40 }, R: { x: 263, y: 40 } };
const PEEK = { L: { x: 24, y: 92 }, R: { x: 296, y: 92 } };
const PHONE = 250;

export const ResidentMixin = {
  bossActive() { return !!this.boss && this.boss.phase !== "done"; },

  startBoss() {
    this.boss = { phase: "landing", hits: 0, side: "L", wait: 0, lim: 3.6 };
    this.busy = true; this.clearHints(); if (this.working) this.cancelWork();
    this.order = null; this.bag.setVisible(false);
    snd.music("boss"); snd.sfx("warn"); snd.sfx("knock", 0.3);
    this.cameras.main.shake(250, 0.006);
    const b = this.boss;
    b.glow = this.add.rectangle(0, 0, 22, 14, 0xef3b4a).setDepth(4).setAlpha(0);
    b.peek = this.add.sprite(0, 0, "props_resident", "peek_0").setOrigin(0.5, 1).setDepth(5).setVisible(false);
    b.hp = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
    b.floorTxt = txt(this, 6, 34, "", { size: 9, color: C.yellow, depth: 895 });
    this.cut(() => {
      this.floor = Math.max(1, Math.min(this.floor, 5));
      this.toLanding(160);
      this.caption(t("chaseStart"), 2.6);
    }, 260);
  },

  /** Arrive on a landing of the scissor stairwell; pick the side it's coming down. */
  toLanding(x) {
    const b = this.boss;
    this.place = "chase";
    this.bg.setTexture("bg_stairwell_scissor").clearTint(); this.dim.setAlpha(0);
    this.floorTxt.setText(""); this.plates.forEach(p => p.setVisible(false)); this.navL.setText("▲"); this.navR.setText("▲");
    this.elevOpen.setVisible(false); this.doorOpen.setVisible(false);
    this.bigFloor.setText(`${this.floor}F`).setColor(C.grey);
    this.p.x = x; this.p.y = FY; this.p.setVisible(true); this.target = null; this.intent = null;
    b.side = Math.random() < 0.5 ? "L" : "R"; b.wait = 0; b.lim = Math.max(1.8, 3.6 - 0.35 * (this.floor - 1));
    b.glow.setPosition(BULB[b.side].x, BULB[b.side].y);
    b.peek.setPosition(PEEK[b.side].x, PEEK[b.side].y).setFlipX(b.side === "R").setVisible(true).setAlpha(0);
    this.tweens.add({ targets: b.peek, alpha: 1, delay: 250, duration: 300 });
    b.hp.setText("♥".repeat(LIVES - b.hits) + "♡".repeat(b.hits));
    b.floorTxt.setText(`${this.floor}F → ${t("roofF")}`);
    this.hint("flight", W / 2, 96);
  },

  tickBoss(dt) {
    const b = this.boss;
    if (b.phase === "roof") return this.tickRoof(dt);
    if (this.busy) return;
    b.wait += dt;
    b.glow.setAlpha(Math.floor(this.time.now / 90) % 3 ? 0.55 : 0);
    // too slow: it comes down anyway
    if (b.wait >= b.lim) return this.residentHit(b.side);
    const p = this.p;
    if (p.x <= 14) return this.takeFlight("L");
    if (p.x >= 306) return this.takeFlight("R");
  },

  takeFlight(side) {
    const b = this.boss;
    if (side === b.side) return this.residentHit(side);
    this.unhint("flight");
    this.busy = true; this.p.anims.stop();
    snd.sfx("step"); this.time.delayedCall(110, () => snd.sfx("step")); this.time.delayedCall(220, () => snd.sfx("step"));
    this.tweens.add({ targets: this.p, y: FY - 12, duration: 200 });
    b.peek.setVisible(false); b.glow.setAlpha(0);
    this.cut(() => {
      this.floor++;
      if (this.floor >= ROOF) return this.toRoof();
      this.toLanding(side === "L" ? 40 : 280);
    }, 180);
  },

  residentHit(side) {
    const b = this.boss, p = this.p;
    if (this.over) return;
    b.hits++; this.busy = true;
    snd.sfx("hitboss"); snd.sfx("roar", 0.05);
    b.peek.setFrame("peek_0").setVisible(false);
    const r = this.stalker;
    r.setTexture("props_resident", "reach_0").clearTint().setOrigin(0.5, 1).setScale(1).setDepth(101).setFlipX(p.x > W / 2)
      .setPosition(Phaser.Math.Clamp(p.x + (p.x > W / 2 ? 18 : -18), 16, W - 16), FY + 1).setVisible(true);
    this.cameras.main.shake(260, 0.012); this.cameras.main.flash(140, 239, 59, 74);
    b.hp.setText("♥".repeat(Math.max(0, LIVES - b.hits)) + "♡".repeat(Math.min(LIVES, b.hits)));
    if (b.hits >= LIVES) return this.fail("resident");
    this.time.delayedCall(700, () => {
      if (this.over) return;
      r.setVisible(false);
      this.cut(() => { this.toLanding(160); }, 200);
    });
  },

  toRoof() {
    const b = this.boss;
    b.phase = "roof";
    this.place = "roof"; this.busy = false;
    this.bg.setTexture("bg_roof"); this.bigFloor.setText(""); this.navL.setText(""); this.navR.setText("");
    b.peek.setVisible(false); b.glow.setPosition(PHONE, 139).setSize(14, 8).setFillStyle(0x9ccdf2).setAlpha(0.6);
    b.floorTxt.setText(t("roofF"));
    this.p.x = 50; this.p.y = FY;
    snd.music("off"); snd.sfx("ring");
    this.ringEv = this.time.addEvent({ delay: 2600, loop: true, callback: () => snd.sfx("ring") });
    this.hint("phone", PHONE, 110);
  },

  tickRoof() {
    const b = this.boss;
    b.glow.setAlpha(Math.floor(this.time.now / 400) % 2 ? 0.7 : 0.3);
  },

  /** On the roof: Space at the phone. */
  pickPhone() {
    const b = this.boss;
    if (b.phase !== "roof" || Math.abs(this.p.x - PHONE) > 18) return false;
    b.phase = "done"; this.bossDone = true;
    this.ringEv?.remove(); b.glow.setAlpha(0); this.unhint("phone");
    snd.sfx("ui"); snd.jingle("clockout");
    this.caption(t("clue_phone"), 4.5);
    b.hp.setVisible(false); b.floorTxt.setVisible(false);
    this.time.delayedCall(5200, () => { if (!this.over) this.clockOut(); });
    return true;
  },

  endBossFx() { if (this.boss?.hp) { this.boss.hp.setVisible(false); this.boss.floorTxt.setVisible(false); this.ringEv?.remove(); } },
};

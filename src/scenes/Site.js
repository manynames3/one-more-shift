import Phaser from "phaser";
import { W, H, BAR, C, txt, rand } from "../ui.js";
import { S, t, won, recordBest, srulesFor } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";
import { GigMixin } from "./gig.js";

// Act 6: a night construction site. One screen:
//   the brick pile (left), the site office with the roll-call board, the formwork pit (centre, crossed on
//   a steel plate), the hoist (right). Carry bricks from the pile to the hoist.
// Rules, one per night: don't load a hoist that came down with someone in it (1); during a pour, stay off
// the pit plate (2); if the roll call shows one more than the crew list, flip the board (3).
// Boss, night 3 at 03:45: the Foreman. Lure him under the crane hook and signal the drop (Space).
const FY = 150, SPEED = 76, MINLEN = 1.15, FEET = 46 / 48;
const P = "characters_sora";
const PILE = 40, BOARD = 107, PIT0 = 150, PIT1 = 210, HOIST = 275, HOOK = 180;
const LIVES = 3, FOREMAN_HP = 3;
export const FOREMAN_NIGHT = 3, FOREMAN_MIN = 45;

/** Pay you must earn on a site night. */
export const sQuotaFor = shift => 30000 + 5000 * (shift - 1);

export default class Site extends Phaser.Scene {
  constructor() { super("Site"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = srulesFor(run.shift);
    this.d = run.shift - 1;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = sQuotaFor(run.shift);
    this.min = 0; this.minT = 0; this.clockBase = 180; this.hintPre = "s_";
    this.hintsShown = new Set(); this.hints = {};
    this.busy = false; this.target = null; this.intent = null; this.working = null;
    this.face = "right"; this.stepT = 0; this.carry = false;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    this.bg = this.add.image(0, 0, "bg_site").setOrigin(0);
    this.cage = this.add.image(254, 86, "props_hoist_closed").setOrigin(0).setDepth(30).setVisible(false);
    this.boardTxt = txt(this, BOARD, 98, "", { ox: 0.5, size: 9, color: C.ink, shadow: false, depth: 31, spacing: 1 });
    this.pitGlow = this.add.rectangle(PIT0, 138, PIT1 - PIT0, 12, 0x7b7689).setOrigin(0).setDepth(32).setAlpha(0);
    this.load_ = this.add.image(HOOK, 70, "props_load").setOrigin(0.5, 0).setDepth(96).setVisible(false);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(PILE + 20, FY, P, "right_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.brick = this.add.image(0, 0, "props_brick").setDepth(101).setVisible(false);
    this.workBar = this.add.graphics().setDepth(620);

    this.hoist = { state: "down", t: 0, rider: false };
    this.pour = { state: "idle", t: rand(14, 20) };
    this.roll = { state: "idle", t: rand(12, 18), extra: false, left: 0 };
    this.crew = 4;
    this.drawBoard();

    this.buildHud();
    this.initNote(230);
    this.bindInput();
    startReplay(this.game);
    snd.music("store"); snd.ambience(true);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
    if (run.shift === 1) this.hint("pile", PILE, 96);
  }

  has(rule) { return this.rules.includes(rule); }
  onPit() { return this.p.x > PIT0 && this.p.x < PIT1; }

  drawBoard() {
    const r = this.roll;
    this.boardTxt.setText(r.state === "on" ? t("rollBoard", this.crew + (r.extra ? 1 : 0), this.crew) : "");
  }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  spots() { return [[PILE, 18, "pile"], [BOARD, 16, "board"], [HOIST, 20, "hoist"]]; }

  act() {
    if (this.over || this.busy || this.working) return;
    if (this.bossActive?.()) return this.signal();
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.over || this.busy || y < BAR || y > H - BAR) return;
    if (this.bossActive?.()) { if (y < 80) return this.signal(); this.target = Phaser.Math.Clamp(x, 10, W - 10); return; }
    if (this.working) this.cancelWork();
    const s = this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 60);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 10, W - 10);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (what === "pile") { if (!this.carry) { this.working = { kind: "pick", t: 0.6, dur: 0.6 }; this.face = "up"; snd.sfx("work"); this.unhint("pile"); } return; }
    if (what === "board") { if (this.roll.state === "on") this.flipBoard(); return; }
    if (what === "hoist") {
      if (!this.carry || this.hoist.state !== "down") return;
      // night 1: it came down with someone already in it. Loading it means riding with them.
      if (this.hoist.rider) return this.fail("hoist");
      this.working = { kind: "load", t: 0.8, dur: 0.8 }; this.face = "up"; snd.sfx("work");
    }
  }

  // ---- the hoist --------------------------------------------------------------------
  sendHoist() {
    const h = this.hoist;
    h.state = "up"; h.t = 3.5 - 0.3 * this.d; h.rider = false;
    this.cage.setTexture("props_hoist_closed").setVisible(true); snd.sfx("clang"); snd.sfx("buzz", 0.2);
  }

  tickHoist(dt) {
    const h = this.hoist;
    if (h.state === "up") {
      h.t -= dt;
      this.cage.setAlpha(Math.floor(this.time.now / 200) % 2 ? 1 : 0.85);
      if (h.t <= 0) {
        h.state = "down"; this.cage.setAlpha(1);
        h.rider = this.has("hoist") && Math.random() < 0.3 + 0.03 * this.d;
        if (h.rider) { this.cage.setTexture("props_hoist_rider").setVisible(true); h.riderT = rand(5, 7); this.hint("rider", HOIST - 10, 64); snd.sfx("appear"); }
        else this.cage.setVisible(false);
        snd.sfx("ding");
      }
    } else if (h.rider) {
      h.riderT -= dt;
      if (h.riderT <= 0) { this.unhint("rider"); h.state = "up"; h.t = 2.5; h.rider = false; this.cage.setTexture("props_hoist_closed"); snd.sfx("clang"); }
    }
  }

  // ---- night 2: the pour -------------------------------------------------------------
  tickPour(dt) {
    if (!this.has("pit")) return;
    const p = this.pour;
    p.t -= dt;
    if (p.state === "idle" && p.t <= 0) { p.state = "warn"; p.t = 2.2; snd.sfx("warn"); this.hint("pour", (PIT0 + PIT1) / 2, 104); }
    else if (p.state === "warn") {
      this.pitGlow.setAlpha(Math.floor(this.time.now / 150) % 2 ? 0.5 : 0);
      if (p.t <= 0) { p.state = "pour"; p.t = 5.5; snd.sfx("dash"); snd.sfx("static", 0.1); }
    } else if (p.state === "pour") {
      this.pitGlow.setAlpha(0.7).setFillStyle(0x4a4458);
      if (this.onPit()) return this.fail("pit");
      if (p.t <= 0) { p.state = "idle"; p.t = rand(15, 21) - this.d; this.pitGlow.setAlpha(0).setFillStyle(0x7b7689); this.unhint("pour"); }
    }
  }

  // ---- night 3: roll call --------------------------------------------------------------
  tickRoll(dt) {
    if (!this.has("rollcall")) return;
    const r = this.roll;
    r.t -= dt;
    if (r.state === "idle" && r.t <= 0) {
      r.state = "on"; r.extra = Math.random() < 0.5; r.left = 7;
      this.drawBoard(); snd.sfx("bell");
      if (r.extra) this.hint("roll", BOARD + 30, 76);
    } else if (r.state === "on") {
      r.left -= dt;
      if (r.left <= 0) {
        if (r.extra) return this.fail("rollcall");
        this.endRoll();
      }
    }
  }

  flipBoard() {
    const r = this.roll;
    // flipping it when the count was right is a complaint from the crew
    if (!r.extra) this.strike(BOARD, t("strike"));
    else { this.earn(7000 + 1000 * this.d, BOARD, 80); snd.sfx("clang"); }
    this.endRoll();
  }

  endRoll() { const r = this.roll; r.state = "idle"; r.t = rand(14, 20); r.extra = false; this.drawBoard(); this.unhint("roll"); }

  // ---- boss: the Foreman ----------------------------------------------------------------
  bossActive() { return !!this.boss && this.boss.phase !== "done"; }

  startBoss() {
    this.clearHints(); if (this.working) this.cancelWork();
    this.endRoll(); this.pour.state = "idle"; this.pitGlow.setAlpha(0);
    this.carry = false; this.brick.setVisible(false);
    snd.music("boss"); snd.sfx("roar"); this.cameras.main.shake(300, 0.008);
    const b = this.boss = { phase: "walk", x: W + 30, t: 1, hp: FOREMAN_HP, hits: 0, iframe: 0, cool: 0, dropT: 0 };
    b.spr = this.add.sprite(b.x, FY, "props_foreman", "idle_0").setOrigin(0.5, 1).setDepth(95);
    b.hpTxt = txt(this, W / 2, 34, "", { ox: 0.5, size: 9, color: C.yellow, depth: 895 });
    b.lives = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
    this.load_.setVisible(true).setPosition(HOOK, 46);
    this.drawForeman();
    this.caption(t("foremanStart"), 2.8);
    this.hint("crane", HOOK, 100);
  }

  drawForeman() {
    const b = this.boss;
    b.hpTxt.setText(t("foremanHp", b.hp));
    b.lives.setText("♥".repeat(LIVES - b.hits) + "♡".repeat(b.hits));
  }

  /** Space during the fight: signal the crane to drop its load at the hook. */
  signal() {
    const b = this.boss;
    if (b.cool > 0 || b.dropT > 0) return;
    b.dropT = 0.65; snd.sfx("ding"); this.unhint("crane");
    this.load_.setPosition(HOOK, 46);
  }

  tickBoss(dt) {
    const b = this.boss, s = b.spr, p = this.p;
    b.t -= dt; b.iframe -= dt; b.cool -= dt;
    // the load
    if (b.dropT > 0) {
      b.dropT -= dt;
      this.load_.y = 46 + (1 - Math.max(0, b.dropT) / 0.65) * (FY - 24 - 46);
      if (b.dropT <= 0) {
        snd.sfx("hitboss"); snd.sfx("stamp"); this.cameras.main.shake(200, 0.01);
        if (Math.abs(b.x - HOOK) < 24) return this.foremanHurt();
        if (Math.abs(p.x - HOOK) < 18 && b.iframe <= 0) this.foremanHit();
        b.cool = 1.2;
        this.time.delayedCall(700, () => { if (this.boss && this.boss.phase !== "done") this.load_.setPosition(HOOK, 46); });
      }
    }
    const dx = p.x - b.x, dir = Math.sign(dx) || -1;
    if (b.phase === "walk") {
      b.x += dir * Math.min(Math.abs(dx), (32 + 6 * (FOREMAN_HP - b.hp)) * dt);
      s.setFrame("walk_" + (Math.floor(this.time.now / 260) % 2)).setFlipX(dir > 0);
      if (Math.abs(dx) < 34 && b.t <= 0) { b.phase = "wind"; b.t = 0.7; s.setFrame("wind_0"); snd.sfx("warn"); }
    } else if (b.phase === "wind" && b.t <= 0) {
      b.phase = "slam"; b.t = 0.5; s.setFrame("slam_0"); snd.sfx("stamp"); this.cameras.main.shake(150, 0.008);
      const reach = b.x + (s.flipX ? 22 : -22);
      if (Math.abs(p.x - reach) < 22 && b.iframe <= 0) this.foremanHit();
    } else if (b.phase === "slam" && b.t <= 0) { b.phase = "walk"; b.t = 0.8; }
    else if (b.phase === "hurt" && b.t <= 0) { b.phase = "walk"; b.t = 1; }
    s.x = Math.round(Phaser.Math.Clamp(b.x, 16, W - 16));
  }

  foremanHit() {
    const b = this.boss, p = this.p;
    b.hits++; b.iframe = 1.2;
    snd.sfx("strike"); this.cameras.main.flash(120, 239, 59, 74);
    p.x = Phaser.Math.Clamp(p.x + (p.x > b.x ? 30 : -30), 12, W - 12);
    this.tweens.add({ targets: p, alpha: 0.3, duration: 100, yoyo: true, repeat: 4 });
    this.drawForeman();
    if (b.hits >= LIVES) this.fail("foreman");
  }

  foremanHurt() {
    const b = this.boss;
    b.hp--; b.phase = "hurt"; b.t = 1.4; b.spr.setFrame("hurt_0"); b.cool = 1.6;
    this.drawForeman();
    if (b.hp <= 0) return this.winForeman();
    this.time.delayedCall(900, () => { if (this.boss.phase !== "done") this.load_.setPosition(HOOK, 46); });
  }

  winForeman() {
    const b = this.boss;
    b.phase = "done"; this.bossDone = true; this.clearHints();
    b.hpTxt.setVisible(false); b.lives.setVisible(false);
    snd.music("off"); snd.jingle("clockout");
    this.time.delayedCall(1200, () => this.caption(t("clue_site"), 4));
    this.time.delayedCall(5600, () => { if (!this.over) this.clockOut(); });
  }

  endBossFx() { if (this.boss?.hpTxt) { this.boss.hpTxt.setVisible(false); this.boss.lives.setVisible(false); } }

  // ---- HUD hooks ------------------------------------------------------------------------
  hotRule() {
    if (this.boss) return "boss6";
    if (this.hoist.rider) return "hoist";
    if (this.pour.state !== "idle") return "pit";
    if (this.roll.state === "on" && this.roll.extra) return "rollcall";
    return null;
  }
  tickSlip() { this.slip.setText(this.carry ? t("holdBrick") : t("emptyHand")).setColor(C.ink); }

  // ---- player ------------------------------------------------------------------------
  cancelWork() { this.working = null; this.workBar.clear(); }

  tickPlayer(dt) {
    const k = this.keys, p = this.p;
    if (this.busy) return;
    let vx = (k.RIGHT.isDown || k.D.isDown ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
    if (vx) { this.target = null; this.intent = null; if (this.working) this.cancelWork(); }
    else if (this.target !== null && !this.working) {
      const dx = this.target - p.x;
      if (Math.abs(dx) < 1) { p.x = this.target; this.target = null; if (this.intent) { this.use(this.intent); if (this.over) return; } }
      else vx = Math.sign(dx);
    }
    const moving = !!vx;
    if (moving) {
      this.face = vx < 0 ? "left" : "right";
      let step = SPEED * (this.carry ? 0.8 : 1) * dt;
      if (this.target !== null) step = Math.min(step, Math.abs(this.target - p.x));
      p.x = Phaser.Math.Clamp(p.x + vx * step, 10, W - 10);
      this.stepT -= dt; if (this.stepT <= 0) { snd.sfx("step"); this.stepT = 0.2; }
    } else this.stepT = 0;
    if (this.working) {
      const w = this.working;
      w.t -= dt;
      this.workBar.clear().fillStyle(0x14101a).fillRect(p.x - 9, FY - 53, 18, 4)
        .fillStyle(0xffd42a).fillRect(p.x - 8, FY - 52, Math.round(16 * (1 - w.t / w.dur)), 2);
      if (w.t <= 0) {
        this.cancelWork();
        if (w.kind === "pick") { this.carry = true; snd.sfx("stock"); this.hint("hoistGo", HOIST, 70); }
        else if (w.kind === "load") { this.carry = false; this.unhint("hoistGo"); this.earn(5000 + 1000 * this.d, HOIST, 76); snd.sfx("stock"); this.sendHoist(); }
        this.face = "right";
      }
    }
    const key = this.working ? "work" : moving ? this.face + "_walk" : null;
    if (key) p.play(`${P}_${key}`, true);
    else { p.anims.stop(); p.setFrame(`${this.face === "up" ? "up" : this.face}_walk_0`); }
    this.sh.setPosition(Math.round(p.x), FY - 1);
    this.brick.setVisible(this.carry).setPosition(Math.round(p.x), FY - 50);
  }

  // ---- losing --------------------------------------------------------------------------
  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTint(0xff5a5a); this.vigRed.setVisible(true); this.staticTile.setVisible(true);
    this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    const p = this.p;
    p.setVisible(true); p.play(P + "_scared");
    const f = this.boss?.spr || this.add.sprite(0, FY, "props_foreman", "wind_0").setOrigin(0.5, 1).setDepth(99);
    f.setFrame("wind_0").setPosition(p.x + (this.face === "left" ? -22 : 22), FY + 2).setFlipX(this.face === "left");
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }

  update(time, ms) {
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over) return;
    const dt = Math.min(ms, 50) / 1000 * (window.__speed || 1);
    if (this.boss) {
      this.tickPlayer(dt);
      if (this.over) return;
      if (this.bossActive()) this.tickBoss(dt);
      if (this.over) return;
      return this.tickHud(dt);
    }
    this.minT += dt;
    while (this.minT >= MINLEN) { this.minT -= MINLEN; this.min++; if (this.min >= 60) return this.clockOut(); }
    if (this.run.shift === FOREMAN_NIGHT && this.min >= FOREMAN_MIN && !this.working) return this.startBoss();
    this.tickPlayer(dt);
    if (this.over) return;
    this.tickHoist(dt);
    if (this.over) return;
    this.tickPour(dt);
    if (this.over) return;
    this.tickRoll(dt);
    if (this.over) return;
    this.tickHud(dt);
  }
}

Object.assign(Site.prototype, GigMixin);

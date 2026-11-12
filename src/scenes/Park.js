import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, button } from "../ui.js";
import { S, t, recordBest, notesFound } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";
import { GigMixin } from "./gig.js";

// Act 7, the finale: the night parade at 달빛랜드, a park that closed years ago. One night, 04:00 -> 05:00.
// Sora hands light sticks to kids from the staff booth while floats roll past behind her, and every
// kind of rule she has learned comes back: a float lit wrong (don't look at it), her name called
// (don't answer), the lights going out (don't move). 준호 is here.
// At 04:45 곽 실장 makes the offer: sign and the debt is gone, forever at the front desk. Refuse and
// survive him until 05:00. Or, with all six of the Regular's notes, hand them over.
const FY = 150, SPEED = 80, MINLEN = 1.15, FEET = 46 / 48;
const P = "characters_sora";
const BOOTH = 281, FRONT = 236, SLOTS = [236, 212, 188], JUNHO = 60, CAROUSEL = 56;
const OFFER_MIN = 45, LIVES = 3;

export default class Park extends Phaser.Scene {
  constructor() { super("Park"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = ["float", "answer", "still"];
    this.d = 2;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = 0;
    this.min = 0; this.minT = 0; this.clockBase = 240; this.hintPre = "p_";
    this.hintsShown = new Set(); this.hints = {};
    this.busy = false; this.target = null; this.intent = null; this.working = null;
    this.face = "left"; this.stepT = 0; this.carry = false; this.moving = false;
    this.cameras.main.fadeIn(400, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    this.bg = this.add.image(0, 0, "bg_park").setOrigin(0);
    this.float = this.add.sprite(-60, 140, "props_float", "f_0").setOrigin(0.5, 1).setDepth(20).setVisible(false);
    this.junho = this.add.sprite(JUNHO, FY, "characters_junho", "sit_0").setOrigin(0.5, FEET).setDepth(60).setVisible(false);
    this.kwak = this.add.sprite(W + 20, FY, "characters_kwak", "left_walk_0").setOrigin(0.5, FEET).setDepth(90).setVisible(false);
    this.bubble = txt(this, CAROUSEL, 70, "", { ox: 0.5, size: 9, color: C.ink, shadow: false, depth: 630 })
      .setBackgroundColor("#f6f1e7").setPadding(3, 1, 3, 1).setVisible(false);
    this.dark = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x0b1020).setOrigin(0).setDepth(600).setAlpha(0);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(BOOTH - 30, FY, P, "left_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.held = this.add.image(0, 0, "props_balloon_b").setOrigin(0.5, 1).setDepth(101).setVisible(false);
    this.workBar = this.add.graphics().setDepth(620);

    this.kids = []; this.kidT = 2;
    this.ev = { kind: null, t: rand(7, 9), left: 0, grace: 0 };
    this.floatT = rand(3, 5);
    this.found = false;

    this.buildHud();
    this.bindInput();
    startReplay(this.game);
    snd.music("park"); snd.ambience(false);
    this.caption(t("parkStart"), 3.5);
  }

  has() { return true; }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  spots() { return [[BOOTH, 16, "booth"], [FRONT, 14, "front"], [JUNHO, 18, "junho"]]; }

  act() {
    if (this.talking) return;
    if (this.over || this.busy || this.working || this.choosing) return;
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.talking) return;
    if (this.over || this.busy || this.choosing || y < BAR || y > H - BAR) return;
    if (this.working) this.cancelWork();
    const s = this.boss ? null : this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 60);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 10, W - 10);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (this.boss) return;
    if (this.ev.kind === "call") return this.fail("answer");
    if (what === "booth" && !this.carry) { this.carry = true; snd.sfx("work"); return; }
    if (what === "front") {
      const k = this.kids[0];
      if (!k || !k.atSlot || !this.carry) return;
      this.carry = false; this.kids.shift();
      this.earn(10000, k.spr.x, 76); snd.sfx("serve");
      k.spr.setFrame("happy_0");
      this.tweens.add({ targets: k.spr, x: -20, duration: 2600, delay: 300, onStart: () => k.spr.setFlipX(false), onComplete: () => k.spr.destroy() });
      return;
    }
    if (what === "junho" && this.junho.visible && !this.found) {
      this.found = true; this.unhint("junho");
      snd.sfx("bell");
      this.talk("talk_junho");
      this.junho.setFrame("down_idle_0");
    }
  }

  // ---- kids at the booth ---------------------------------------------------------------
  tickKids(dt) {
    this.kidT -= dt;
    if (this.kidT <= 0 && this.kids.length < SLOTS.length) {
      const spr = this.add.sprite(-16, FY, "props_kid", "left_walk_0").setOrigin(0.5, 1).setFlipX(true).setDepth(90);
      this.kids.push({ spr, atSlot: false });
      this.kidT = rand(5, 7);
    }
    this.kids.forEach((k, i) => {
      const tx = SLOTS[i], s = k.spr;
      if (Math.abs(s.x - tx) > 1) { s.x += Math.sign(tx - s.x) * Math.min(Math.abs(tx - s.x), 40 * dt); s.setFrame("left_walk_" + (Math.floor(this.time.now / 140) % 4)); k.atSlot = false; }
      else { s.x = tx; k.atSlot = true; s.setFrame("down_idle_" + (Math.floor(this.time.now / 500) % 2)); }
    });
  }

  // ---- the parade and the rules coming back ----------------------------------------------
  tickParade(dt) {
    // floats roll past in the back lane
    if (!this.float.visible) {
      this.floatT -= dt;
      if (this.floatT <= 0 && !this.ev.kind) {
        const wrong = Math.random() < 0.45;
        this.float.setVisible(true).setX(-60).setFrame(wrong ? "f_wrong_0" : "f_0");
        this.floatWrong = wrong;
        if (wrong) { this.ev.kind = "float"; snd.sfx("warn"); this.hint("float", W / 2, 52); }
        else snd.sfx("bell");
      }
    } else {
      this.float.x += 38 * dt;
      if (!this.floatWrong) this.float.setFrame("f_" + (Math.floor(this.time.now / 400) % 2));
      // a wrong float: don't be facing it
      if (this.floatWrong) {
        const toward = this.float.x < this.p.x ? "left" : "right";
        if (this.float.x > -20 && this.float.x < W + 20 && this.face === toward) return this.fail("float");
      }
      if (this.float.x > W + 60) {
        this.float.setVisible(false); this.floatT = rand(5, 8);
        if (this.floatWrong) { this.ev.kind = null; this.ev.t = rand(4, 6); this.unhint("float"); }
        this.floatWrong = false;
      }
    }
    // her name from the carousel; the lights going out
    const e = this.ev;
    if (e.kind === "call") {
      e.left -= dt;
      if (e.left <= 0) { e.kind = null; e.t = rand(6, 9); this.bubble.setVisible(false); this.unhint("quiet"); }
    } else if (e.kind === "dark") {
      e.left -= dt; e.grace -= dt;
      if (e.grace <= 0) { this.dark.setAlpha(0.72); if (this.moving) return this.fail("still"); }
      if (e.left <= 0) { e.kind = null; e.t = rand(6, 9); this.dark.setAlpha(0); this.unhint("still"); snd.sfx("hop"); }
    } else if (!e.kind) {
      e.t -= dt;
      if (e.t <= 0 && !this.float.visible) {
        if (Math.random() < 0.5) { e.kind = "call"; e.left = 3.2; this.bubble.setText(t("call")).setVisible(true); snd.sfx("appear"); this.hint("quiet", W / 2, 52); if (this.working) this.cancelWork(); }
        else { e.kind = "dark"; e.left = 4.5; e.grace = 1; snd.sfx("buzz"); this.dark.setAlpha(0.3); this.hint("still", W / 2, 52); }
      }
    }
  }

  // ---- the offer ----------------------------------------------------------------------
  startOffer() {
    this.choosing = true; this.clearHints(); if (this.working) this.cancelWork();
    this.ev.kind = null; this.bubble.setVisible(false); this.dark.setAlpha(0); this.float.setVisible(false);
    this.kids.forEach(k => k.spr.destroy()); this.kids = [];
    snd.music("office");
    this.kwak.setVisible(true).play("characters_kwak_left_walk");
    this.tweens.add({ targets: this.kwak, x: this.p.x + 40, duration: 1600, onComplete: () => {
      this.kwak.play("characters_kwak_down_idle");
      this.talk("talk_offer", () => { this.choosing = true; this.showChoices(); });
    } });
  }

  /** Kwak talks: a line at a time in a box at the bottom. */
  offerLines(lines, done) {
    let i = 0;
    const box = this.add.rectangle(W / 2, H - BAR - 22, W - 20, 30, 0x14101a, 0.92).setStrokeStyle(1, 0xffd42a).setDepth(940);
    const line = txt(this, 18, H - BAR - 33, "", { size: 9, color: C.white, depth: 941, wrap: W - 40 });
    const next = () => {
      if (i >= lines.length) { box.destroy(); line.destroy(); this.input.keyboard.off("keydown-SPACE", next); this.input.off("pointerdown", next); return done(); }
      line.setText(lines[i++]); snd.sfx("type");
    };
    this.input.keyboard.on("keydown-SPACE", next);
    this.input.on("pointerdown", next);
    next();
  }

  showChoices() {
    const opts = [["sign", t("choiceSign"), "ui_btn_danger"], ["refuse", t("choiceRefuse"), "ui_btn_primary"]];
    if (notesFound() >= 6) opts.push(["note", t("choiceNote"), "ui_btn_secondary"]);
    const y0 = 70;
    this.choiceBtns = opts.map(([k, label, key], i) => button(this, W / 2, y0 + i * 24, key, label, () => this.choose(k), 960));
    this.input.keyboard.once("keydown-ONE", () => this.choose("sign"));
    this.input.keyboard.once("keydown-TWO", () => this.choose("refuse"));
    if (opts.length > 2) this.input.keyboard.once("keydown-THREE", () => this.choose("note"));
  }

  choose(k) {
    if (this.chosen) return;
    this.chosen = k;
    this.choiceBtns?.forEach(b => b.destroy());
    if (k === "refuse") { this.choosing = false; return this.startBoss(); }
    this.endWith(k);
  }

  endWith(ending) {
    this.over = true;
    this.freeze?.();
    this.time.delayedCall(600, () => this.cameras.main.fadeOut(600, 20, 16, 26));
    this.time.delayedCall(1250, () => this.scene.start("Ending", { ending }));
  }

  // ---- refused: 곽 실장's final form, until 05:00 -----------------------------------------
  startBoss() {
    snd.music("boss"); snd.sfx("roar"); this.cameras.main.shake(400, 0.01);
    this.kwak.setVisible(false);
    const b = this.boss = { phase: "idle", x: this.kwak.x, t: 1.2, hits: 0, iframe: 0, target: 0 };
    b.spr = this.add.sprite(b.x, FY + 2, "props_kwak_boss", "idle_0").setOrigin(0.5, 1).setDepth(95);
    b.lives = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
    this.drawLives();
    this.caption(t("kwakTurn"), 2.5);
    this.hint("survive", W / 2, 60);
  }

  drawLives() { this.boss.lives.setText("♥".repeat(LIVES - this.boss.hits) + "♡".repeat(this.boss.hits)); }

  tickBoss(dt) {
    const b = this.boss, s = b.spr, p = this.p;
    b.t -= dt; b.iframe -= dt;
    if (!b.p2 && this.min >= 52) { b.p2 = true; this.caption(t("kwakPhase2"), 2); snd.sfx("roar"); this.cameras.main.shake(300, 0.01); }
    if (b.phase === "idle") {
      s.setFrame((b.p2 ? "phase2_" : "idle_") + (Math.floor(this.time.now / 300) % 2));
      b.x += Math.sign(p.x - b.x) * Math.min(Math.abs(p.x - b.x), 26 * dt);
      if (b.t <= 0) { b.phase = "tell"; b.t = 0.6; s.setFrame("tell_0"); snd.sfx("warn"); }
    } else if (b.phase === "tell" && b.t <= 0) {
      b.phase = "lunge"; b.target = Phaser.Math.Clamp(p.x, 20, W - 20); s.setFrame("lunge_0"); snd.sfx("dash");
    } else if (b.phase === "lunge") {
      const dx = b.target - b.x, step = (b.p2 ? 380 : 300) * dt;
      if (Math.abs(dx) <= step) { b.x = b.target; b.phase = "idle"; b.t = b.p2 ? rand(0.45, 0.8) : rand(0.9, 1.5); snd.sfx("clang"); }
      else b.x += Math.sign(dx) * step;
      if (Math.abs(p.x - b.x) < 16 && b.iframe <= 0) {
        b.hits++; b.iframe = 1.2; this.drawLives();
        snd.sfx("hitboss"); this.cameras.main.flash(120, 239, 59, 74); this.cameras.main.shake(200, 0.01);
        p.x = Phaser.Math.Clamp(p.x + (p.x > b.x ? 30 : -30), 12, W - 12);
        if (b.hits >= LIVES) return this.fail("kwak");
      }
    }
    s.x = Math.round(b.x);
  }

  bossActive() { return !!this.boss && this.boss.phase !== "done"; }
  endBossFx() { if (this.boss?.lives) this.boss.lives.setVisible(false); }

  // ---- HUD hooks ---------------------------------------------------------------------
  hotRule() {
    if (this.boss) return "boss7";
    if (this.floatWrong) return "float";
    if (this.ev.kind === "call") return "answer";
    if (this.ev.kind === "dark") return "still";
    return null;
  }
  tickSlip() { this.slip.setText(t("notesSlip", notesFound())).setColor(C.ink); }

  // ---- player --------------------------------------------------------------------
  cancelWork() { this.working = null; this.workBar.clear(); }

  tickPlayer(dt) {
    const k = this.keys, p = this.p;
    this.moving = false;
    if (this.busy || this.choosing) { p.anims.stop(); return; }
    let vx = (k.RIGHT.isDown || k.D.isDown ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
    if (vx) { this.target = null; this.intent = null; }
    else if (this.target !== null) {
      const dx = this.target - p.x;
      if (Math.abs(dx) < 1) { p.x = this.target; this.target = null; if (this.intent) { this.use(this.intent); if (this.over) return; } }
      else vx = Math.sign(dx);
    }
    this.moving = !!vx;
    if (this.moving) {
      this.face = vx < 0 ? "left" : "right";
      let step = SPEED * dt;
      if (this.target !== null) step = Math.min(step, Math.abs(this.target - p.x));
      p.x = Phaser.Math.Clamp(p.x + vx * step, 10, W - 10);
      this.stepT -= dt; if (this.stepT <= 0) { snd.sfx("step"); this.stepT = 0.2; }
      p.play(`${P}_${this.face}_walk`, true);
    } else { this.stepT = 0; p.anims.stop(); p.setFrame(`${this.face}_walk_0`); }
    this.sh.setPosition(Math.round(p.x), FY - 1);
    this.held.setVisible(this.carry).setPosition(Math.round(p.x) + (this.face === "left" ? -9 : 9), FY - 14);
    if (this.junho.visible && !this.found && Math.abs(p.x - JUNHO) < 40) this.hint("junho", JUNHO, 92);
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
    const k = this.boss?.spr || this.add.sprite(0, FY + 2, "props_kwak_boss", "lunge_0").setOrigin(0.5, 1).setDepth(99);
    k.setFrame("lunge_0").setPosition(p.x + (this.face === "left" ? -20 : 20), FY + 2);
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }

  update(time, ms) {
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over || this.talking) return;
    const dt = Math.min(ms, 50) / 1000 * (window.__speed || 1);
    if (this.choosing) return this.tickHud(dt);
    // the clock runs in the fight too: it ends at 05:00
    this.minT += dt;
    while (this.minT >= MINLEN) {
      this.minT -= MINLEN; this.min++;
      if (this.min === 20) { this.junho.setVisible(true); this.caption(t("junhoSeen"), 3); snd.sfx("bell"); }
      if (this.min >= 60) {
        if (this.boss) { this.boss.phase = "done"; return this.endWith("walk"); }
        this.min = 59;
      }
    }
    if (!this.boss && !this.chosen && this.min >= OFFER_MIN && !this.ev.kind && !this.float.visible) return this.startOffer();
    this.tickPlayer(dt);
    if (this.over) return;
    if (this.boss) { this.tickBoss(dt); if (this.over) return; return this.tickHud(dt); }
    this.tickKids(dt);
    this.tickParade(dt);
    if (this.over) return;
    this.tickHud(dt);
  }
}

Object.assign(Park.prototype, GigMixin);

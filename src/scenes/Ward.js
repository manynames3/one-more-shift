import Phaser from "phaser";
import { W, H, BAR, C, txt, rand } from "../ui.js";
import { S, t, won, recordBest, wrulesFor } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";
import { GigMixin } from "./gig.js";

// Act 5: a paid clinical trial. Sora is test subject No. 9 on a night ward. One screen:
//   the nurse hatch (far left) hands out pills, Sora's bed (middle) is where she writes her diary and
//   gives blood, the ward door (right).
// Rules, one per night: take only blue pills (1); after lights-out, stay in bed (2);
// a nurse without a name tag doesn't get your arm (3).
// Boss, night 3 at 00:45+30: the subject in bed 3 gets up and stands at the door. Get out past it,
// but only move while its back is turned.
const FY = 150, SPEED = 78, MINLEN = 1.15, FEET = 46 / 48;
const P = "characters_sora";
const HATCH = 16, BED = 160, BED3 = 260, DOOR = 306;
const LIVES = 3;
export const SUBJECT_NIGHT = 3, SUBJECT_MIN = 45;

/** Pay you must earn on a trial night. */
export const wQuotaFor = shift => 30000 + 5000 * (shift - 1);

export default class Ward extends Phaser.Scene {
  constructor() { super("Ward"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = wrulesFor(run.shift);
    this.d = run.shift - 1;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = wQuotaFor(run.shift);
    this.min = 0; this.minT = 0; this.clockBase = 30; this.hintPre = "w_";
    this.hintsShown = new Set(); this.hints = {};
    this.busy = false; this.target = null; this.intent = null; this.working = null;
    this.face = "left"; this.stepT = 0;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    this.bg = this.add.image(0, 0, "bg_ward").setOrigin(0);
    this.other1 = this.add.sprite(60, 128, "props_subject", "lie_0").setOrigin(0.5, 1).setDepth(40);
    this.other3 = this.add.sprite(BED3, 128, "props_subject", "lie_0").setOrigin(0.5, 1).setDepth(40);
    this.dark = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x0b1020).setOrigin(0).setDepth(600).setAlpha(0);
    this.hatchMark = this.add.sprite(HATCH + 6, 62, "props_exclaim", "exclaim_0").setDepth(610).setVisible(false).play("props_exclaim_exclaim");
    this.diaryMark = this.add.sprite(BED + 16, 96, "props_exclaim", "exclaim_0").setDepth(610).setVisible(false).play("props_exclaim_exclaim");
    this.pill = this.add.image(HATCH + 8, 104, "props_pill", "blue_0").setDepth(50).setVisible(false).setScale(1.5);
    this.nurse = this.add.sprite(W + 20, FY, "props_nurse", "left_walk_0").setOrigin(0.5, FEET).setDepth(90).setVisible(false);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(BED, FY, P, "left_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.workBar = this.add.graphics().setDepth(620);

    this.hatch = { open: false, t: rand(4, 6), left: 0, red: false };
    this.diary = { need: false, t: rand(8, 12), left: 0 };
    this.visit = { state: "away", t: rand(12, 16), left: 0, notag: false };
    this.lights = { state: "on", t: rand(14, 20), left: 0 };

    this.buildHud();
    this.initNote(220);
    this.bindInput();
    startReplay(this.game);
    snd.music("store"); snd.ambience(false);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
  }

  has(rule) { return this.rules.includes(rule); }
  atBed() { return Math.abs(this.p.x - BED) <= 16; }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  spots() { return [[HATCH, 16, "hatch"], [BED, 16, "bed"], [DOOR, 16, "door"]]; }

  act() {
    if (this.over || this.busy || this.working) return;
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.over || this.busy || y < BAR || y > H - BAR) return;
    if (this.working) this.cancelWork();
    const s = this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 60);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 10, W - 10);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (this.boss) { if (what === "door") this.escape(); return; }
    if (what === "hatch") {
      if (!this.hatch.open) return;
      // night 1: a red one. Swallow it and that's the trial over.
      if (this.hatch.red) return this.fail("pill");
      this.closeHatch(); this.earn(5000 + 1000 * this.d, HATCH + 10, 80); snd.sfx("serve");
      return;
    }
    if (what === "bed") {
      const v = this.visit;
      if (v.state === "here") {
        // night 3: no name tag. Don't hold your arm out.
        if (v.notag) return this.fail("nurse");
        this.working = { kind: "blood", t: 1.2, dur: 1.2 }; this.face = "right"; snd.sfx("work");
        return;
      }
      if (this.diary.need) { this.working = { kind: "diary", t: 1.3, dur: 1.3 }; this.face = "up"; snd.sfx("work"); }
    }
  }

  // ---- the pill hatch --------------------------------------------------------------
  tickHatch(dt) {
    const h = this.hatch;
    if (!h.open) {
      h.t -= dt;
      if (h.t <= 0 && this.lights.state === "on") {
        h.open = true; h.left = 6;
        h.red = this.has("pill") && Math.random() < 0.3 + 0.03 * this.d;
        this.pill.setFrame(h.red ? "red_0" : "blue_0").setVisible(true); this.hatchMark.setVisible(true);
        snd.sfx("task");
        this.hint(h.red ? "red" : "pill", 60, 60);
      }
    } else {
      h.left -= dt;
      if (h.left <= 0) {
        // walking away from a blue one is a missed dose
        const missed = !h.red;
        this.closeHatch();
        if (missed) this.strike(HATCH + 20, t("missedDose"));
      }
    }
  }

  closeHatch() {
    const h = this.hatch;
    h.open = false; h.t = rand(9, 13) - 0.5 * this.d;
    this.pill.setVisible(false); this.hatchMark.setVisible(false); this.unhint("pill"); this.unhint("red");
  }

  // ---- the diary ----------------------------------------------------------------
  tickDiary(dt) {
    const d = this.diary;
    if (!d.need) { d.t -= dt; if (d.t <= 0) { d.need = true; d.left = 12; this.diaryMark.setVisible(true); snd.sfx("task"); } }
    else { d.left -= dt; if (d.left <= 0) { d.need = false; d.t = rand(10, 14); this.diaryMark.setVisible(false); this.strike(BED, t("strike")); } }
  }

  // ---- the nurse's visit: blood draws ----------------------------------------------
  tickVisit(dt) {
    const v = this.visit, n = this.nurse;
    if (v.state === "away") {
      v.t -= dt;
      if (v.t <= 0 && this.lights.state === "on") {
        v.state = "coming"; v.notag = this.has("nurse") && Math.random() < 0.4;
        n.setTexture(v.notag ? "props_nurse_notag" : "props_nurse", "left_walk_0").setVisible(true).setX(W + 20).setFlipX(false);
        snd.sfx("door");
      }
    } else if (v.state === "coming") {
      n.x -= 46 * dt; n.setFrame("left_walk_" + (Math.floor(this.time.now / 150) % 4));
      if (n.x <= BED + 26) { n.x = BED + 26; v.state = "here"; v.left = 7; n.setFrame("give_0"); this.hint(v.notag ? "notag" : "arm", BED + 20, 56); }
    } else if (v.state === "here") {
      v.left -= dt;
      if (v.left <= 0) {
        if (!v.notag) this.strike(BED + 26, t("strike"));
        this.nurseLeave();
      }
    } else if (v.state === "going") {
      n.x += 46 * dt; n.setFrame("right_walk_" + (Math.floor(this.time.now / 150) % 4));
      if (n.x > W + 20) { n.setVisible(false); v.state = "away"; v.t = rand(12, 17) - this.d; }
    }
  }

  nurseLeave() { this.visit.state = "going"; this.unhint("arm"); this.unhint("notag"); }

  // ---- night 2: lights-out --------------------------------------------------------
  tickLights(dt) {
    const L = this.lights;
    if (!this.has("bed")) return;
    L.t -= dt;
    if (L.state === "on" && L.t <= 0) { L.state = "warn"; L.t = 2.2; snd.sfx("buzz"); this.hint("bed", W / 2, 52); }
    else if (L.state === "warn") {
      this.dark.setAlpha(Math.floor(this.time.now / 120) % 2 ? 0.25 : 0);
      if (L.t <= 0) { L.state = "out"; L.t = 6; this.dark.setAlpha(0.7); snd.sfx("clang"); }
    } else if (L.state === "out") {
      if (!this.atBed() || this.moving) return this.fail("bed");
      this.p.setFrame("down_idle_0");
      if (L.t <= 0) { L.state = "on"; L.t = rand(16, 22); this.dark.setAlpha(0); this.unhint("bed"); snd.sfx("hop"); }
    }
  }

  // ---- boss: the subject in bed 3 ---------------------------------------------------
  startBoss() {
    this.clearHints(); if (this.working) this.cancelWork();
    this.closeHatch(); this.diary.need = false; this.diaryMark.setVisible(false);
    if (this.visit.state !== "away") { this.nurse.setVisible(false); this.visit.state = "away"; }
    this.lights.state = "on"; this.dark.setAlpha(0.45);
    snd.music("boss"); snd.sfx("creak"); snd.sfx("warn", 0.3);
    const b = this.boss = { phase: "back", t: rand(2, 3), hits: 0 };
    this.other3.setVisible(false);
    b.spr = this.add.sprite(DOOR - 18, FY, "props_subject", "back_0").setOrigin(0.5, FEET).setDepth(95);
    b.lives = txt(this, W - 6, 34, "", { ox: 1, size: 9, color: C.red, depth: 895 });
    this.p.x = BED; this.drawLives();
    this.caption(t("subjectStart"), 3);
    this.hint("sneak", W / 2, 60);
  }

  drawLives() { this.boss.lives.setText("♥".repeat(LIVES - this.boss.hits) + "♡".repeat(this.boss.hits)); }

  tickBoss(dt) {
    const b = this.boss;
    b.t -= dt;
    if (b.phase === "back" && b.t <= 0) { b.phase = "tell"; b.t = 0.55; snd.sfx("creak"); b.spr.setTint(0xd3e0d6); }
    else if (b.phase === "tell" && b.t <= 0) { b.phase = "look"; b.t = rand(1.4, 2.4); b.spr.clearTint().setFrame("turn_0"); snd.sfx("heart"); }
    else if (b.phase === "look") {
      if (this.moving) return this.subjectHit();
      if (b.t <= 0) { b.phase = "back"; b.t = rand(1.6, 3); b.spr.setFrame("back_0"); }
    }
  }

  subjectHit() {
    const b = this.boss;
    b.hits++; this.drawLives();
    snd.sfx("hitboss"); this.cameras.main.flash(140, 239, 59, 74); this.cameras.main.shake(220, 0.01);
    if (b.hits >= LIVES) return this.fail("subject");
    // dragged back to bed
    this.busy = true; this.target = null;
    this.tweens.add({ targets: this.p, x: BED, duration: 500, ease: "Quad.easeOut", onComplete: () => { this.busy = false; } });
    b.phase = "back"; b.t = rand(1.6, 2.6); b.spr.setFrame("back_0");
  }

  escape() {
    const b = this.boss;
    if (!b || b.phase === "done" || b.phase === "look") return;
    b.phase = "done"; this.bossDone = true;
    this.clearHints(); b.lives.setVisible(false);
    snd.music("off"); snd.jingle("clockout");
    this.p.setVisible(false); this.dark.setAlpha(0);
    this.caption(t("clue_trial"), 4);
    this.time.delayedCall(4800, () => { if (!this.over) this.clockOut(); });
  }

  // ---- HUD hooks ---------------------------------------------------------------------
  hotRule() {
    if (this.boss) return "boss5";
    if (this.lights.state !== "on") return "bed";
    if (this.visit.state === "here" && this.visit.notag) return "nurse";
    if (this.hatch.open && this.hatch.red) return "pill";
    return null;
  }
  tickSlip() { this.slip.setText(t("subjectNo")).setColor(C.ink); }

  // ---- player --------------------------------------------------------------------
  cancelWork() { this.working = null; this.workBar.clear(); }

  tickPlayer(dt) {
    const k = this.keys, p = this.p;
    this.moving = false;
    if (this.busy) return;
    let vx = (k.RIGHT.isDown || k.D.isDown ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
    if (vx) { this.target = null; this.intent = null; if (this.working) this.cancelWork(); }
    else if (this.target !== null && !this.working) {
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
    } else this.stepT = 0;
    if (this.working) {
      const w = this.working;
      w.t -= dt;
      this.workBar.clear().fillStyle(0x14101a).fillRect(p.x - 9, FY - 53, 18, 4)
        .fillStyle(0xffd42a).fillRect(p.x - 8, FY - 52, Math.round(16 * (1 - w.t / w.dur)), 2);
      if (w.t <= 0) {
        this.cancelWork();
        if (w.kind === "diary") { this.diary.need = false; this.diary.t = rand(10, 14) - this.d; this.diaryMark.setVisible(false); this.earn(5000 + 1000 * this.d, BED, 80); snd.sfx("stock"); }
        else if (w.kind === "blood") { this.earn(7000 + 1000 * this.d, BED + 20, 70); snd.sfx("serve"); this.nurseLeave(); }
        this.face = "left";
      }
    }
    const key = this.working ? "work" : this.moving ? this.face + "_walk" : null;
    if (key) p.play(`${P}_${key}`, true);
    else if (this.lights.state !== "out") { p.anims.stop(); p.setFrame(`${this.face === "up" ? "up" : this.face}_walk_0`); }
    this.sh.setPosition(Math.round(p.x), FY - 1);
  }

  // ---- losing ------------------------------------------------------------------------
  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTint(0xff5a5a); this.vigRed.setVisible(true); this.staticTile.setVisible(true); this.dark.setAlpha(0.2);
    this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    const p = this.p;
    p.setVisible(true); p.play(P + "_scared");
    // the subject from bed 3, right behind you
    const s = this.boss?.spr || this.add.sprite(0, FY, "props_subject", "turn_0").setOrigin(0.5, FEET).setDepth(99);
    this.other3.setVisible(false);
    s.setFrame("turn_0").setPosition(p.x + (this.face === "left" ? 16 : -16), FY + 2).setScale(1.3).setDepth(99);
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
    if (this.run.shift === SUBJECT_NIGHT && this.min >= SUBJECT_MIN && !this.working && this.lights.state === "on") return this.startBoss();
    this.tickPlayer(dt);
    if (this.over) return;
    this.tickHatch(dt);
    this.tickDiary(dt);
    this.tickVisit(dt);
    if (this.over) return;
    this.tickLights(dt);
    if (this.over) return;
    this.tickHud(dt);
  }

  bossActive() { return !!this.boss && this.boss.phase !== "done"; }
  endBossFx() { if (this.boss?.lives) this.boss.lives.setVisible(false); }
}

Object.assign(Ward.prototype, GigMixin);

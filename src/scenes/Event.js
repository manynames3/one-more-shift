import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, pick } from "../ui.js";
import { S, t, won, recordBest, erulesFor } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";
import { GigMixin } from "./gig.js";
import { SuitMixin, SUIT_NIGHT, SUIT_MIN } from "./suit.js";

// Act 2: the night event. A grand opening in a shut mall at midnight; Sora handles the mascot.
// Side view, one screen: the stage (left), the balloon cart (middle), the guest queue (right).
//   Kids want balloons: grab one at the cart, hand it over at the front of the queue.
//   The suit overheats now and then: fan it at the stage.
// Rules, one per night: balloons for kids only (1), when its head comes off don't look at the stage (2),
// when it calls your name don't answer (3).
const FY = 150, STAGE_Y = 128;
const SPEED = 80;
const MINLEN = 1.15;            // real seconds per in-game minute (00:00 -> 01:00)
const FEET = 46 / 48;
const P = "characters_sora";
const STAGE = 62, CART = 170, FRONT = 228;
const SLOTS = [228, 254, 280, 306];
const ADULTS = ["halmae", "daeri", "jisu"];

/** Pay you must earn on an event night. */
export const eQuotaFor = shift => 52000 + 6000 * (shift - 1);

export default class Event extends Phaser.Scene {
  constructor() { super("Event"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = erulesFor(run.shift);
    this.d = run.shift - 1;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = eQuotaFor(run.shift);
    this.min = 0; this.minT = 0; this.clockBase = 0; this.hintPre = "e_";
    this.hintsShown = new Set(); this.hints = {};
    this.busy = false; this.target = null; this.intent = null; this.working = null;
    this.face = "left"; this.stepT = 0; this.carry = false;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    // world
    this.bg = this.add.image(0, 0, "bg_event_plaza").setOrigin(0);
    txt(this, 63, 43, t("banner"), { ox: 0.5, size: 9, color: C.red2, shadow: false, depth: 2 });
    this.mascot = this.add.sprite(STAGE, STAGE_Y, "props_mascot", "idle_0").setOrigin(0.5, 1).setDepth(50);
    this.mT = 0;
    this.bubble = txt(this, STAGE, STAGE_Y - 74, "", { ox: 0.5, size: 9, color: C.ink, shadow: false, depth: 630 })
      .setBackgroundColor("#f6f1e7").setPadding(3, 1, 3, 1).setVisible(false);
    this.fanMark = this.add.sprite(STAGE + 18, STAGE_Y - 70, "props_exclaim", "exclaim_0").setDepth(610).setVisible(false);
    this.fanMark.play("props_exclaim_exclaim");
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    // player and what she holds
    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(CART + 10, FY, P, "left_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.held = this.add.image(0, 0, "props_balloon").setOrigin(0.5, 1).setDepth(101).setVisible(false);
    this.workBar = this.add.graphics().setDepth(620);

    // guests, the suit, and the two rule events
    this.guests = []; this.guestT = 1.5;
    this.fan = { need: false, t: rand(10, 14), left: 0 };
    this.head = { off: false, t: rand(12, 18), left: 0, grace: 0 };
    this.call = { on: false, t: rand(14, 20), left: 0 };

    this.buildHud();
    this.initNote(120);
    if (this.run.shift === 1) this.time.delayedCall(2900, () => { if (!this.over) this.caption(t("how2"), 5); });
    this.bindInput();
    startReplay(this.game);
    snd.music("event"); snd.ambience(false);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
    if (run.shift === 1) {
      const hint = txt(this, W / 2, H - BAR - 14, t("dHint"), { ox: 0.5, size: 9, depth: 880 });
      this.tweens.add({ targets: hint, alpha: 0, delay: 5000, duration: 500, onComplete: () => hint.destroy() });
      this.hint("take", CART, 62);
    }
  }

  has(rule) { return this.rules.includes(rule); }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  spots() { return [[STAGE, 22, "stage"], [CART, 16, "cart"], [FRONT, 16, "front"]]; }

  act() {
    if (this.talking) return;
    if (this.meterPress()) return;
    if (this.over || this.busy || this.working) return;
    if (this.bossActive() && this.tryTie()) return;
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.talking) return;
    if (this.meterState) { if (y > BAR && y < H - BAR) this.meterPress(); return; }
    if (this.over || this.busy || y < BAR || y > H - BAR) return;
    if (this.working) this.cancelWork();
    const s = this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 60);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 10, W - 10);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (this.bossActive()) {
      if (this.tryTie()) return;
      if (what === "cart" && !this.carry) { this.carry = true; snd.sfx("work"); }
      return;
    }
    // night 3: while it's calling, doing anything at all counts as answering
    if (this.call.on) return this.fail("answer");
    if (what === "cart") {
      if (this.carry) return;
      // fill it from the helium tank: let go in the green, too much and it pops
      this.unhint("take"); this.face = "up";
      this.hint("pump", CART, 62);
      this.meter({ mode: "hold", zone: [0.6, 0.9], speed: 0.85, label: t("m_pump"), done: ok => {
        this.unhint("pump");
        if (ok) { this.carry = true; snd.sfx("squeak"); }
        else { snd.sfx("hitboss"); this.pop(t("popped"), CART, 70, C.red); }
      } });
      return;
    }
    if (what === "stage") {
      if (!this.fan.need || this.head.off) return;
      this.working = { kind: "fan", t: 1.4, dur: 1.4 }; this.face = "up"; snd.sfx("work");
      return;
    }
    if (what === "front") return this.serve();
  }

  // ---- the queue -----------------------------------------------------------------
  front() { const g = this.guests[0]; return g && g.atSlot && !g.out ? g : null; }

  serve() {
    const g = this.front();
    if (!g) return;
    if (g.kid) {
      if (!this.carry) return;
      this.carry = false; this.unhint("give");
      this.leaveQueue(g, true);
      this.earn(6000 + 1000 * this.d, g.spr.x, 70); snd.sfx("serve");
      return;
    }
    // a grown-up asking for a balloon: hand it over and it's over
    if (this.carry) return this.fail("balloon");
    this.unhint("adult");
    this.pop(t("refused"), g.spr.x, 72, C.grey); snd.sfx("grumble");
    this.leaveQueue(g, false);
  }

  spawnGuest() {
    const kid = Math.random() > 0.28 + 0.03 * this.d;
    const key = kid ? "props_kid" : "characters_" + pick(ADULTS);
    const spr = this.add.sprite(W + 16, FY, key, "left_walk_0").setOrigin(0.5, kid ? 1 : FEET);
    const sh = this.add.image(spr.x, FY - 1, "props_shadow_blob").setAlpha(0.5).setScale(kid ? 0.7 : 1);
    const bar = this.add.graphics().setDepth(620);
    const ask = txt(this, 0, 0, kid ? "!" : t("adultAsk"), { ox: 0.5, size: 9, color: C.ink, shadow: false, depth: 615 })
      .setBackgroundColor("#f6f1e7").setPadding(2, 0, 2, 0).setVisible(false);
    this.guests.push({ spr, sh, bar, ask, kid, key, wait: 0, atSlot: false, out: false, happy: false });
  }

  leaveQueue(g, happy) {
    g.out = true; g.happy = happy; g.bar.clear(); g.ask.setVisible(false);
    this.guests = this.guests.filter(x => x !== g);
    if (happy && g.kid) g.spr.setFrame("happy_0");
    this.tweens.add({ targets: g.spr, x: W + 20, duration: 1600, delay: happy ? 350 : 0,
      onUpdate: () => g.sh.setPosition(g.spr.x, FY - 1),
      onComplete: () => { g.spr.destroy(); g.sh.destroy(); g.bar.destroy(); g.ask.destroy(); } });
    if (g.kid) g.spr.setFlipX(true);
    else g.spr.play(g.key + "_right_walk", true);
  }

  tickGuests(dt) {
    this.guestT -= dt;
    if (this.guestT <= 0 && this.guests.length < SLOTS.length) { this.spawnGuest(); this.guestT = rand(4, 6) - 0.4 * this.d; }
    this.guests.forEach((g, i) => {
      const tx = SLOTS[i], s = g.spr;
      if (Math.abs(s.x - tx) > 1) {
        s.x += Math.sign(tx - s.x) * Math.min(Math.abs(tx - s.x), 40 * dt);
        if (g.key === "props_kid") s.setFrame("left_walk_" + (Math.floor(this.time.now / 140) % 4)); else s.play(g.key + "_left_walk", true);
        g.atSlot = false;
      } else {
        s.x = tx; g.atSlot = true;
        if (g.key === "props_kid") s.setFrame("down_idle_" + (Math.floor(this.time.now / 500) % 2)); else s.play(g.key + "_down_idle", true);
      }
      s.setDepth(90 + i * 0.1); g.sh.setPosition(s.x, FY - 1).setDepth(89);
      const isFront = i === 0 && g.atSlot;
      g.ask.setVisible(isFront).setPosition(s.x, s.y - (g.kid ? 38 : 52));
      if (isFront) {
        if (!g.kid) {
          this.hint("adult", FRONT, 52);
          // a grown-up who gets no answer gives up after a while (no complaint), so a held balloon never jams the queue
          g.wait += dt;
          if (g.wait > 7) { this.unhint("adult"); this.leaveQueue(g, false); snd.sfx("grumble"); return; }
        }
        else if (this.carry) this.hint("give", FRONT, 52);
        // kids only wait so long at the front
        if (g.kid) {
          g.wait += dt;
          const lim = 13 - this.d;
          g.bar.clear().fillStyle(0x14101a).fillRect(s.x - 9, s.y - 46, 18, 4)
            .fillStyle(g.wait > lim * 0.7 ? 0xef3b4a : 0x7fc77a).fillRect(s.x - 8, s.y - 45, Math.round(16 * (1 - g.wait / lim)), 2);
          if (g.wait >= lim) { this.leaveQueue(g, false); this.strike(s.x, t("strike")); }
        }
      }
    });
  }

  // ---- the suit: overheating, its head, its voice ---------------------------------
  tickMascot(dt) {
    const m = this.mascot;
    this.mT += dt;
    if (!this.head.off) m.setFrame(this.call.on ? "wave_" + (Math.floor(this.mT * 4) % 2) : "idle_" + (Math.floor(this.mT * 2) % 2));

    // fanning
    const f = this.fan;
    if (!f.need) { f.t -= dt; if (f.t <= 0 && !this.head.off) { f.need = true; f.left = 11; this.fanMark.setVisible(true); snd.sfx("task"); this.hint("fan", STAGE, 50); } }
    else {
      f.left -= dt;
      if (f.left <= 0) { f.need = false; f.t = rand(10, 15); this.fanMark.setVisible(false); this.unhint("fan"); this.strike(STAGE, t("strike")); }
    }

    // night 2: the head comes off. Face away (right) until it's back on.
    const h = this.head;
    if (this.has("head")) {
      if (!h.off) {
        h.t -= dt;
        if (h.t <= 0 && !this.call.on) {
          h.off = true; h.left = 4.2; h.grace = 1.1;
          m.setFrame("headoff_0"); snd.sfx("clang"); snd.sfx("warn", 0.1);
          this.cameras.main.shake(140, 0.004);
          this.hint("turn", W / 2 + 40, 52);
          this.fanMark.setVisible(false);
        }
      } else {
        h.left -= dt; h.grace -= dt;
        m.setFrame(h.left < 2 ? "headoff_1" : "headoff_0");
        if (h.grace <= 0 && this.face !== "right") return this.fail("head");
        if (h.left <= 0) {
          h.off = false; h.t = rand(13, 20) - this.d; this.unhint("turn"); snd.sfx("hop");
          if (this.fan.need) this.fanMark.setVisible(true);
        }
      }
    }

    // night 3: it calls Sora's name. Don't do anything until it stops.
    const c = this.call;
    if (this.has("answer")) {
      if (!c.on) {
        c.t -= dt;
        if (c.t <= 0 && !h.off) {
          c.on = true; c.left = 3.2;
          this.bubble.setText(t("call")).setVisible(true); snd.sfx("appear");
          this.hint("quiet", W / 2, 52);
          if (this.working) this.cancelWork();
        }
      } else {
        c.left -= dt;
        this.bubble.setAlpha(Math.floor(c.left * 6) % 2 ? 1 : 0.6);
        if (c.left <= 0) { c.on = false; c.t = rand(14, 20); this.bubble.setVisible(false); this.unhint("quiet"); }
      }
    }
  }

  // ---- HUD bits used by the shared HUD -------------------------------------------
  hotRule() {
    if (this.boss) return "boss2";
    if (this.head.off) return "head";
    if (this.call.on) return "answer";
    const g = this.front();
    if (g && !g.kid) return "balloon";
    return null;
  }
  tickSlip() { this.slip.setText(this.carry ? t("holdBalloon") : t("emptyHand")).setColor(C.ink); }

  // ---- player --------------------------------------------------------------------
  cancelWork() { this.working = null; this.workBar.clear(); }

  tickPlayer(dt) {
    const k = this.keys, p = this.p;
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
      let step = SPEED * dt;
      if (this.target !== null) step = Math.min(step, Math.abs(this.target - p.x));
      p.x = Phaser.Math.Clamp(p.x + vx * step, 12, W - 12);
      this.stepT -= dt; if (this.stepT <= 0) { snd.sfx("step"); this.stepT = 0.2; }
    } else this.stepT = 0;

    if (this.working) {
      const w = this.working;
      w.t -= dt;
      this.workBar.clear().fillStyle(0x14101a).fillRect(p.x - 9, FY - 53, 18, 4)
        .fillStyle(0xffd42a).fillRect(p.x - 8, FY - 52, Math.round(16 * (1 - w.t / w.dur)), 2);
      if (w.t <= 0) {
        this.cancelWork();
        this.fan.need = false; this.fan.t = rand(10, 15) - this.d; this.fanMark.setVisible(false); this.unhint("fan");
        this.earn(6000 + 1000 * this.d, STAGE, 66); snd.sfx("stock");
      }
    }
    const key = this.working ? "work" : moving ? this.face + "_walk" : null;
    if (key) p.play(`${P}_${key}`, true);
    else { p.anims.stop(); p.setFrame(`${this.face}_walk_0`); }
    this.sh.setPosition(Math.round(p.x), FY - 1);
    this.held.setVisible(this.carry).setPosition(Math.round(p.x) + (this.face === "left" ? -9 : 9), FY - 14);
  }

  // ---- losing --------------------------------------------------------------------
  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTint(0xff5a5a); this.vigRed.setVisible(true); this.staticTile.setVisible(true);
    this.bubble.setVisible(false); this.fanMark.setVisible(false);
    this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    this.guests.forEach(g => { g.bar.clear(); g.ask.setVisible(false); g.spr.setTint(0x8c1526); });
    const p = this.p;
    p.play(P + "_scared");
    // the empty suit steps off the stage and stands over her
    const m = this.boss?.spr?.visible ? this.boss.spr : this.mascot;
    if (m === this.mascot) m.setFrame("headoff_1");
    m.setDepth(101);
    this.tweens.add({ targets: m, x: p.x - (this.face === "left" ? 18 : -18), y: FY + 2, scale: 1.25, duration: 500, ease: "Quad.easeIn" });
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }

  update(time, ms) {
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over || this.talking) return;
    const dt = Math.min(ms, 50) / 1000 * (window.__speed || 1);
    if (this.bossActive() || this.bossDone) {
      this.tickPlayer(dt);
      if (this.over) return;
      if (this.bossActive()) this.tickBoss(dt);
      if (this.over) return;
      return this.tickHud(dt);
    }
    this.minT += dt;
    while (this.minT >= MINLEN) { this.minT -= MINLEN; this.min++; if (this.min >= 60) return this.clockOut(); }
    if (this.run.shift === SUIT_NIGHT && this.min >= SUIT_MIN && !this.boss) return this.startBoss();
    this.tickPlayer(dt);
    if (this.over) return;
    this.tickMascot(dt);
    if (this.over) return;
    this.tickGuests(dt);
    if (this.over) return;
    this.tickHud(dt);
  }
}

Object.assign(Event.prototype, GigMixin, SuitMixin);

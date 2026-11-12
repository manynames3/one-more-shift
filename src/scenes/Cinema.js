import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, pick } from "../ui.js";
import { S, t, won, recordBest, crulesFor } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";
import { GigMixin } from "./gig.js";
import { UsherMixin, USHER_NIGHT, USHER_MIN } from "./usher.js";

// Act 4: the night shift at 별빛극장, a 24-hour cinema. Side view, three places:
//   lobby  sell tickets at the window (left), Hall 3's door (middle), stairs up to the booth (right)
//   hall   inside Hall 3: the screen on the left wall, litter to pick up between screenings, exit right
//   booth  the projector: change the reel when it runs out
// Hall 3 runs a loop: a screening, then a break while the audience leaves.
// Rules, one per night: don't watch the screen for more than 3 s (1); if more leave Hall 3 than went in,
// lock it (2); if a film that isn't on the schedule starts, stay out of the booth (3).
const FY = 150, SPEED = 82, MINLEN = 1.2, FEET = 46 / 48;
const P = "characters_sora";
const LOBBY = { window: 70, hall3: 246, booth: 306, slots: [112, 136, 160, 184] };
const HALL = { exit: 297, trash: [150, 182, 214, 246] };
const BOOTH = { proj: 165, door: 21 };
const ADULTS = ["halmae", "daeri", "jisu"];
const SCREEN_SECS = 26, BREAK_SECS = 12, WATCH_MAX = 3;

/** Pay you must earn on a cinema night. */
export const cQuotaFor = shift => 32000 + 5000 * (shift - 1);

export default class Cinema extends Phaser.Scene {
  constructor() { super("Cinema"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = crulesFor(run.shift);
    this.d = run.shift - 1;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = cQuotaFor(run.shift);
    this.min = 0; this.minT = 0; this.clockBase = 120; this.hintPre = "c_";
    this.hintsShown = new Set(); this.hints = {};
    this.busy = false; this.target = null; this.intent = null; this.working = null;
    this.face = "right"; this.stepT = 0; this.watchT = 0;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    this.bg = this.add.image(0, 0, "bg_cinema_lobby").setOrigin(0);
    this.screen = this.add.sprite(6, 34, "props_screen_film", "film_0").setOrigin(0).setDepth(2).setVisible(false);
    this.sign3 = this.add.rectangle(246, 80, 26, 10, 0xef3b4a).setDepth(3).setAlpha(0);
    this.reelMark = this.add.sprite(0, 0, "props_exclaim", "exclaim_0").setDepth(610).setVisible(false);
    this.reelMark.play("props_exclaim_exclaim");
    this.trashSpr = HALL.trash.map((x, i) => this.add.image(x, FY - 2, "props_items", ["cup_noodle", "receipt", "canned_coffee", "envelope"][i]).setOrigin(0.5, 1).setDepth(60).setVisible(false));
    this.navL = txt(this, 6, FY - 26, "", { size: 9, color: C.yellow, depth: 630 });
    this.navR = txt(this, W - 6, FY - 26, "", { ox: 1, size: 9, color: C.yellow, depth: 630 });
    this.dark = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setDepth(600).setAlpha(0);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(LOBBY.window, FY, P, "right_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.workBar = this.add.graphics().setDepth(620);

    // Hall 3's loop, the ticket queue, the booth
    this.hall = { phase: "break", t: 6, inside: 0, out: 0, toExit: 0, exitT: 0, trap: false, lockBy: 0, film: "film", locked: false };
    this.trash = HALL.trash.map(() => false);
    this.queue = []; this.custT = 1.5;
    this.reel = { need: false, t: rand(8, 12), left: 0 };
    this.walkers = [];

    this.buildHud();
    this.initNote(200, "lobby");
    this.bindInput();
    this.enter("lobby", LOBBY.window);
    startReplay(this.game);
    snd.music("store"); snd.ambience(false);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
  }

  has(rule) { return this.rules.includes(rule); }

  // ---- places ----------------------------------------------------------------
  enter(place, x) {
    this.place = place; this.target = null; this.intent = null; this.watchT = 0;
    this.clearHints();
    this.bg.setTexture({ lobby: "bg_cinema_lobby", hall: "bg_cinema_hall", booth: "bg_cinema_booth" }[place]).clearTint();
    this.navL.setText(place === "hall" ? "" : place === "booth" ? "◀" : "");
    this.navR.setText(place === "lobby" ? "▲" : place === "hall" ? "▶" : "");
    this.p.x = x; this.p.setVisible(true);
    this.walkers.forEach(w => w.spr.setVisible(w.place === place));
    this.queue.forEach(q => { q.spr.setVisible(place === "lobby"); q.sh.setVisible(place === "lobby"); });
    this.syncPlace();
    this.syncP();
  }

  /** Things whose visibility depends on where Sora is. */
  syncPlace() {
    const pl = this.place, h = this.hall;
    this.screen.setVisible(pl === "hall");
    this.trashSpr.forEach((s, i) => s.setVisible(pl === "hall" && this.trash[i]));
    this.sign3.setVisible(pl === "lobby");
    this.reelMark.setVisible(this.reel.need && (pl === "booth" || pl === "lobby"))
      .setPosition(pl === "booth" ? BOOTH.proj : LOBBY.booth - 4, pl === "booth" ? 70 : 92);
    if (pl === "hall") this.screen.setFrame(h.phase === "screen" ? `${h.film}_${Math.floor(this.time.now / 300) % 2}` : "off_0");
  }

  cut(fn, ms = 200) {
    this.busy = true;
    this.cameras.main.fadeOut(ms, 20, 16, 26);
    this.time.delayedCall(ms + 20, () => {
      if (this.over) return;
      fn();
      this.cameras.main.fadeIn(ms, 20, 16, 26);
      this.time.delayedCall(ms, () => { this.busy = false; });
    });
  }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  spots() {
    if (this.place === "lobby") return [[LOBBY.window, 16, "window"], [LOBBY.hall3, 16, "hall3"], [LOBBY.booth, 16, "booth"]];
    if (this.place === "hall") return [...HALL.trash.map((x, i) => [x, 10, "trash" + i]), [HALL.exit, 16, "exit"]];
    return [[BOOTH.proj, 22, "proj"], [BOOTH.door, 16, "down"]];
  }

  act() {
    if (this.talking) return;
    if (this.meterPress()) return;
    if (this.over || this.busy || this.working) return;
    if (this.bossActive?.()) return this.bossAct();
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.talking) return;
    if (this.meterState) { if (y > BAR && y < H - BAR) this.meterPress(); return; }
    if (this.over || this.busy || y < BAR || y > H - BAR) return;
    if (this.bossActive?.()) { if (Math.abs(x - this.p.x) < 20) return this.bossAct(); this.target = Phaser.Math.Clamp(x, 10, W - 10); return; }
    if (this.working) this.cancelWork();
    const s = this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 60);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 10, W - 10);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (what === "window") return this.sell();
    if (what === "hall3") {
      // night 2: after the audience leaves, Hall 3's door is where you lock it
      if (this.hall.lockBy > 0) return this.lockHall();
      return this.cut(() => this.enter("hall", HALL.exit - 8));
    }
    if (what === "booth") {
      // night 3: an unscheduled film is running. Going up there is what it wants.
      if (this.hall.film === "cctv" && this.hall.phase === "screen") return this.fail("booth");
      return this.cut(() => this.enter("booth", BOOTH.door + 12));
    }
    if (what === "exit") return this.cut(() => this.enter("lobby", LOBBY.hall3));
    if (what === "down") return this.cut(() => this.enter("lobby", LOBBY.booth - 14));
    if (what === "proj") {
      if (!this.reel.need) return;
      // thread the new reel: catch the sprocket three times
      this.face = "up"; snd.sfx("work");
      this.meter({ mode: "tap", zone: [0.42, 0.6], speed: 1.3, presses: 3, label: t("m_reel"), done: ok => {
        if (!ok) return;
        this.reel.need = false; this.reel.t = rand(12, 18) - this.d; this.syncPlace(); this.earn(6000 + 1000 * this.d, BOOTH.proj, 60); snd.sfx("stock");
      } });
      return;
    }
    if (what.startsWith("trash")) {
      const i = +what[5];
      if (!this.trash[i]) return;
      this.working = { kind: "trash", i, t: 0.7, dur: 0.7 }; this.face = "up"; snd.sfx("work");
    }
  }

  // ---- the ticket window ----------------------------------------------------------
  sell() {
    const c = this.queue[0];
    if (!c || !c.atSlot) return;
    this.working = { kind: "sell", t: 0.6, dur: 0.6 }; this.face = "right"; snd.sfx("scan");
  }

  finishSell() {
    const c = this.queue.shift();
    if (!c) return;
    this.earn(4000 + 1000 * this.d, c.spr.x, 70); snd.sfx("serve");
    this.hall.inside++;
    // they walk into Hall 3
    this.tweens.add({ targets: [c.spr], x: LOBBY.hall3, duration: Math.abs(c.spr.x - LOBBY.hall3) * 30 + 200,
      onStart: () => c.spr.play(c.key + "_right_walk", true),
      onUpdate: () => c.sh.setPosition(c.spr.x, FY - 1),
      onComplete: () => { snd.sfx("door"); c.spr.destroy(); c.sh.destroy(); } });
  }

  tickQueue(dt) {
    this.custT -= dt;
    if (this.custT <= 0 && this.queue.length < LOBBY.slots.length) {
      const key = "characters_" + pick(ADULTS);
      const spr = this.add.sprite(W + 16, FY, key, "left_walk_0").setOrigin(0.5, FEET).setDepth(90).setVisible(this.place === "lobby");
      const sh = this.add.image(spr.x, FY - 1, "props_shadow_blob").setAlpha(0.5).setDepth(89).setVisible(this.place === "lobby");
      this.queue.push({ spr, sh, key, wait: 0, atSlot: false });
      this.custT = rand(4.5, 7) - 0.4 * this.d;
    }
    this.queue.forEach((c, i) => {
      const tx = LOBBY.slots[i], s = c.spr;
      if (Math.abs(s.x - tx) > 1) { s.x += Math.sign(tx - s.x) * Math.min(Math.abs(tx - s.x), 40 * dt); s.play(c.key + "_left_walk", true); c.atSlot = false; }
      else { s.x = tx; c.atSlot = true; s.play(c.key + "_down_idle", true); }
      c.sh.setPosition(s.x, FY - 1);
      if (i === 0 && c.atSlot) {
        c.wait += dt;
        if (c.wait > 16) { this.queue.shift(); s.destroy(); c.sh.destroy(); this.strike(LOBBY.window + 40, t("strike")); }
      }
    });
  }

  // ---- Hall 3: screenings, the audience leaving, locking it ---------------------
  tickHall(dt) {
    const h = this.hall;
    h.t -= dt;
    if (h.phase === "break" && h.t <= 0) {
      // the next screening starts; on night 3 some of them aren't on the schedule
      h.phase = "screen"; h.t = SCREEN_SECS;
      h.film = this.has("unscheduled") && Math.random() < 0.45 ? "cctv" : "film";
      h.trap = this.has("count") && h.inside > 0 && Math.random() < 0.45;
      if (h.film === "cctv") { snd.sfx("static"); if (this.place !== "hall") this.hint("cctv", W / 2, 52); }
      snd.sfx("bell");
    } else if (h.phase === "screen" && h.t <= 0) {
      h.phase = "exit"; h.toExit = h.inside + (h.trap ? 1 : 0); h.out = 0; h.exitT = 0.4;
      this.unhint("cctv");
    } else if (h.phase === "exit") {
      h.exitT -= dt;
      if (h.toExit > 0 && h.exitT <= 0) { this.spawnLeaver(); h.toExit--; h.out++; h.exitT = 1.1; }
      if (h.toExit <= 0 && h.exitT <= 0) {
        // night 2: one more came out than went in. You have a few seconds to lock the door.
        if (h.trap) { h.lockBy = 7; this.hint("lock", 190, 60); }
        h.phase = "break"; h.t = BREAK_SECS; h.inside = 0; h.film = "film";
        this.trash = this.trash.map(() => Math.random() < 0.7); this.syncPlace();
      }
    }
    if (h.lockBy > 0) {
      h.lockBy -= dt;
      this.sign3.setAlpha(Math.floor(this.time.now / 120) % 2 ? 0.7 : 0.2);
      if (h.lockBy <= 0) return this.fail("count");
    } else this.sign3.setAlpha(h.film === "cctv" && h.phase === "screen" ? (Math.floor(this.time.now / 200) % 2 ? 0.5 : 0) : 0);
    if (this.place === "hall") this.screen.setFrame(h.phase === "screen" ? `${h.film}_${Math.floor(this.time.now / 300) % 2}` : "off_0");
  }

  lockHall() {
    const h = this.hall;
    this.unhint("lock"); h.lockBy = 0; h.trap = false;
    snd.sfx("clang"); snd.sfx("knock", 0.2);
    this.earn(8000 + 1000 * this.d, LOBBY.hall3, 70);
  }

  /** One of the audience walks out (shown wherever Sora is). */
  spawnLeaver() {
    const key = "characters_" + pick(ADULTS), inLobby = this.place === "lobby";
    const x0 = inLobby ? LOBBY.hall3 : 140, x1 = inLobby ? W + 20 : HALL.exit;
    const spr = this.add.sprite(x0, FY, key, "right_walk_0").setOrigin(0.5, FEET).setDepth(88).play(key + "_right_walk");
    const w = { spr, place: this.place };
    this.walkers.push(w);
    snd.sfx(inLobby ? "door" : "step");
    this.tweens.add({ targets: spr, x: x1, duration: Math.abs(x1 - x0) * 28,
      onComplete: () => { spr.destroy(); this.walkers = this.walkers.filter(v => v !== w); } });
  }

  // ---- the booth -------------------------------------------------------------------
  tickReel(dt) {
    const r = this.reel;
    if (!r.need) {
      r.t -= dt;
      if (r.t <= 0 && this.hall.phase === "screen") { r.need = true; r.left = 14; snd.sfx("task"); this.syncPlace(); }
    } else {
      r.left -= dt;
      if (r.left <= 0) { r.need = false; r.t = rand(12, 18); this.syncPlace(); this.strike(W / 2, t("filmBroke")); }
    }
  }

  // ---- night 1: the screen ---------------------------------------------------------
  tickWatch(dt) {
    if (!this.has("screen") || this.place !== "hall" || this.hall.phase !== "screen") { this.watchT = 0; this.unhint("look"); return; }
    if (this.face === "left") {
      this.watchT += dt;
      this.hint("look", W / 2, 128);
      this.flick.setAlpha(Math.min(0.3, this.watchT * 0.1));
      if (this.watchT >= WATCH_MAX) return this.fail("screen");
    } else { this.watchT = 0; this.unhint("look"); this.flick.setAlpha(0); }
  }

  // ---- HUD hooks --------------------------------------------------------------------
  hotRule() {
    if (this.boss) return "boss4";
    if (this.hall.lockBy > 0) return "count";
    if (this.hall.film === "cctv" && this.hall.phase === "screen") return "unscheduled";
    if (this.watchT > 0) return "screen";
    return null;
  }
  tickSlip() {
    const h = this.hall;
    this.slip.setText(t("hallIn", h.inside) + "  " + t(h.phase === "screen" ? "nowShowing" : "intermission")).setColor(C.ink);
  }

  // ---- player ----------------------------------------------------------------------
  cancelWork() { this.working = null; this.workBar.clear(); }

  syncP() { this.sh.setPosition(Math.round(this.p.x), FY - 1); }

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
        if (w.kind === "sell") this.finishSell();
        else if (w.kind === "trash") { this.trash[w.i] = false; this.syncPlace(); this.earn(3000 + 500 * this.d, HALL.trash[w.i], 90); snd.sfx("stock"); }
        else if (w.kind === "reel") { this.reel.need = false; this.reel.t = rand(12, 18) - this.d; this.syncPlace(); this.earn(6000 + 1000 * this.d, BOOTH.proj, 60); snd.sfx("stock"); }
        this.face = "right";
      }
    }
    const key = this.working ? "work" : moving ? this.face + "_walk" : null;
    if (key) p.play(`${P}_${key}`, true);
    else { p.anims.stop(); p.setFrame(`${this.face === "up" ? "up" : this.face}_walk_0`); }
    this.syncP();
  }

  // ---- losing ------------------------------------------------------------------------
  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTint(0xff5a5a); this.vigRed.setVisible(true); this.staticTile.setVisible(true);
    this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    const p = this.p;
    p.setVisible(true); p.play(P + "_scared");
    // the usher, always behind you
    if (!this.boss?.spr?.visible) {
      const u = this.add.sprite(p.x + (this.face === "left" ? 16 : -16), FY + 2, "props_usher", "lunge_0").setOrigin(0.5, 1).setDepth(99).setFlipX(this.face === "left").setScale(1.3);
      u.setAlpha(0); this.tweens.add({ targets: u, alpha: 1, duration: 200 });
    }
    if (cause === "screen" || cause === "booth") { this.screen.setVisible(this.place === "hall").setFrame("cctv_1"); }
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }

  update(time, ms) {
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over || this.talking) return;
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
    if (this.run.shift === USHER_NIGHT && this.min >= USHER_MIN && !this.busy && !this.working) return this.startBoss();
    this.tickPlayer(dt);
    if (this.over) return;
    this.tickQueue(dt);
    this.tickHall(dt);
    if (this.over) return;
    this.tickReel(dt);
    this.tickWatch(dt);
    if (this.over) return;
    this.tickHud(dt);
  }
}

Object.assign(Cinema.prototype, GigMixin, UsherMixin);

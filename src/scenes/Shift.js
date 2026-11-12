import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, pick, soundToggle } from "../ui.js";
import { S, t, rulesFor, won, START_DEBT, recordBest, markSeen, seeded, saveDaily, clearAct, hourly, saveNote } from "../state.js";
import * as snd from "../audio.js";
import { startReplay, endReplay, cancelReplay } from "../replay.js";
import { RoomMixin, ROOM } from "./rooms.js";
import { BossMixin, BOSS_SHIFT, BOSS_MIN } from "./boss.js";

// ---- store geometry (feet positions, in canvas pixels) ---------------------
const TOP = 118, BOT = 154;
const xl = y => 100 - (y - TOP) * 1.45;                 // left bound: shelf edge
const xr = y => Math.min(240, 213 + (y - TOP) * 1.3);   // right bound: counter edge
const DOOR = { x: 161, y: 117 };
const SLOTS = [{ x: 212, y: 124 }, { x: 192, y: 128 }, { x: 172, y: 131 }];
const SPOT = {
  serve: { x: 266, y: 95, face: "left", dur: 0.9 },      // behind the counter, at the register
  shelf: { x: 66, y: 146, face: "left", dur: 1.5, pay: 6000, mark: { x: 54, y: 102 } },
  fridge: { x: 108, y: 119, face: "up", dur: 1.5, pay: 6000, mark: { x: 106, y: 54 } },
};
const GATE = { x: 236, y: 140 };   // where you vault over the counter
const BEHIND_DEPTH = 95, COUNTER_DEPTH = 105;
const SPEED = 66;        // player px/s
const MINLEN = 1.15;     // real seconds per in-game minute (03:00 -> 04:00)
const FEET = 46 / 48;    // sprite origin so y is the feet line
const P = "characters_sora";
const NORMALS = ["halmae", "daeri", "jisu"];   // 덕구 is staff, not a customer
const DOOR_TAP = { x0: 130, x1: 195, y0: 30, y1: 117 };   // tap here to look at the door

/** Pay you must earn in a shift or you are fired at 04:00. */
export const quotaFor = shift => 42000 + 5000 * (shift - 1);

export default class Shift extends Phaser.Scene {
  constructor() { super("Shift"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = rulesFor(run.shift);
    this.d = run.shift - 1;                      // difficulty step
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = quotaFor(run.shift);
    this.watchesSeen = 0; this.lure = null;
    this.hintsShown = new Set(); this.hints = {};
    this.disguiseTwist = run.shift >= 6;
    this.min = 0; this.minT = 0; this.stall = 0; this.stallGrace = 0;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    // daily: everyone gets the same night (same customers, same timings) from the date
    if (run.daily) {
      const realRandom = Math.random;
      Math.random = seeded(run.daily * 7919);
      this.events.once("shutdown", () => { Math.random = realRandom; });
    }
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }   // bot test hook

    // world
    this.bg = this.add.image(0, 0, "bg_store_day").setOrigin(0);
    this.counter = this.add.image(0, 0, "bg_store_counter").setOrigin(0).setDepth(COUNTER_DEPTH);
    this.add.rectangle(159, 43, 34, 13, 0x14101a).setOrigin(0).setDepth(1);
    this.clockTxt = txt(this, 176, 44, "03:00", { size: 9, color: C.red, ox: 0.5, shadow: false, depth: 2 });
    this.eyes = this.add.sprite(161, 84, "props_red_eyes", "eyes_open").setDepth(3).setVisible(false);
    this.ent = this.add.sprite(DOOR.x, DOOR.y - 1, "characters_regular", "down_idle_0").setOrigin(0.5, FEET).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);
    this.staticFx = this.add.sprite(0, 0, "props_static_overlay", "static_0").setVisible(false);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigDark = this.add.image(0, 0, "ui_vignette_dark").setOrigin(0).setDepth(700).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);

    // player
    this.p = this.makeChar("sora", 160, 142);
    this.face = "up"; this.moving = false; this.target = null; this.intent = null; this.working = null;
    this.behind = false; this.vaulting = false; this.stepT = 0; this.scanT = 0;
    this.bang = this.add.sprite(0, 0, "props_exclaim", "exclaim_0").setDepth(620).setVisible(false);
    this.workBar = this.add.graphics().setDepth(620);

    // customers, tasks, pickups
    this.customers = []; this.queue = []; this.custT = 2; this.regularHere = false; this.sinceReg = 9;
    this.tasks = {};
    ["shelf", "fridge"].forEach((k, i) => {
      const m = this.add.sprite(SPOT[k].mark.x, SPOT[k].mark.y, "props_exclaim", "exclaim_0").setDepth(610).setVisible(false);
      m.play("props_exclaim_exclaim");
      this.tasks[k] = { active: false, t: rand(5, 9) + i * 5, mark: m };
    });
    this.items = []; this.itemT = rand(3, 5);

    // the thing at the door
    this.watch = { state: "idle", t: rand(6, 8), back: 0 };

    this.buildHud();
    this.initRooms();
    this.initBoss();
    // the Regular's first note, on the shop floor on the second night
    if (run.shift === 2 && !S.notes[1] && !run.daily) {
      this.note = this.add.image(128, 150, "props_note").setDepth(149);
      this.tweens.add({ targets: this.note, y: 147, duration: 600, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    }
    this.bindInput();
    startReplay(this.game);
    snd.music("store"); snd.ambience(true);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
    if (run.shift === 1 && S.runs <= 3) {
      const hint = txt(this, W / 2, H - BAR - 14, t("hint"), { ox: 0.5, size: 9, depth: 880 });
      this.tweens.add({ targets: hint, alpha: 0, delay: 5000, duration: 500, onComplete: () => hint.destroy() });
    }
  }

  has(rule) { return this.rules.includes(rule); }

  /** One-time teaching hint, shown until the player survives a shift with it. */
  hint(key, x, y) {
    if (S.seen[key] || this.hints[key]) return null;
    this.hintsShown.add(key);
    const h = txt(this, x, y, t("hint_" + key), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    h.setBackgroundColor("#14101a").setPadding(2, 1, 2, 1);
    this.tweens.add({ targets: h, alpha: 0.4, duration: 300, yoyo: true, repeat: -1 });
    this.hints[key] = h;
    return h;
  }

  unhint(key) { if (this.hints[key]) { this.hints[key].destroy(); this.hints[key] = null; } }

  /** After 03:40 on fridge shifts the fridge pays triple and opening it is fatal. */
  fridgeCursed() { return this.has("fridge") && this.min >= 40; }

  makeChar(key, x, y) {
    const sh = this.add.image(x, y - 1, "props_shadow_blob").setAlpha(0.6);
    const spr = this.add.sprite(x, y, "characters_" + key, "down_idle_0").setOrigin(0.5, FEET);
    spr.sh = sh; spr.key = "characters_" + key;
    return spr;
  }

  syncChar(spr) {
    if (spr === this.p && (this.behind || this.vaulting)) {
      spr.setDepth(this.vaulting ? this.vaultDepth : BEHIND_DEPTH); spr.sh.setVisible(false); return;
    }
    if (spr === this.p) spr.sh.setVisible(true);
    const ly = spr.y - (spr === this.p ? this.oy : 0);    // depth sorts by the feet line within a room
    spr.setDepth(ly); spr.sh.setPosition(Math.round(spr.x), Math.round(spr.y) - 1).setDepth(ly - 0.5); }

  spot(kind) { return SPOT[kind]; }

  // ---- HUD ----------------------------------------------------------------
  buildHud() {
    this.add.image(0, 0, "ui_rule_banner").setOrigin(0).setDepth(900);
    this.ruleIcon = this.add.image(43, 11, "props_icons", "rule").setDepth(910);
    this.ruleTxt = txt(this, 60, 5, "", { color: C.yellow, depth: 910 });
    this.add.image(0, H - BAR, "ui_hud_bottom").setOrigin(0).setDepth(900);
    this.hudClock = txt(this, 64, H - BAR + 6, "03:00", { size: 9, ox: 0.5, depth: 910 });
    this.hudPay = txt(this, 129, H - BAR + 6, "", { size: 9, color: C.yellow, depth: 910 });
    this.debtFill = this.add.image(226, H - BAR + 9, "ui_debt_meter_fill").setOrigin(0).setDepth(910);
    this.quotaBar = this.add.graphics().setDepth(911);
    this.strikeIcons = [0, 1, 2].map(i => this.add.image(W - 11 - i * 13, BAR + 9, "props_icons", "cross").setDepth(890).setAlpha(0.18));
    soundToggle(this);
    this.ruleIdx = 0; this.ruleT = 0; this.ruleShown = null; this.blink = 0;
    this.drawMoney();
  }

  drawMoney() {
    this.hudPay.setText(won(this.run.earned + this.pay));
    // quota progress: a thin bar under the pay slot, green once tonight's target is met
    const q = Phaser.Math.Clamp(this.pay / this.quota, 0, 1);
    this.quotaBar.clear().fillStyle(0x2a2233).fillRect(127, H - BAR + 17, 56, 2)
      .fillStyle(q >= 1 ? 0x7fc77a : 0xffd42a).fillRect(127, H - BAR + 17, Math.round(56 * q), 2);
    this.hudPay.setColor(q >= 1 ? C.green : C.yellow);
    const f = Phaser.Math.Clamp((this.run.debt - this.pay) / START_DEBT, 0, 1);
    this.debtFill.setCrop(0, 0, Math.round(60 * f), 4);
  }

  hotRule() {
    if (this.bossActive()) return "boss";
    const room = this.hotRoomRule();
    if (room) return room;
    if (this.watch.state !== "idle") return "door";
    if (this.has("clock") && (this.stall > 0 || (this.min >= 30 && this.min < 33))) return "clock";
    if (this.regularHere && !this.regDisguised) return "regular";
    if (this.has("fridge") && this.min >= 38) return "fridge";
    return null;
  }

  tickHud(dt) {
    if (this.note && this.room === "floor" && Phaser.Math.Distance.Between(this.p.x, this.p.y, this.note.x, 150) < 12) {
      this.note.destroy(); this.note = null; saveNote(1); snd.sfx("coin");
      const c = txt(this, W / 2, 40, t("note1"), { ox: 0.5, size: 9, depth: 960, wrap: W - 40 }).setBackgroundColor("#14101a").setPadding(4, 2, 4, 2);
      this.tweens.add({ targets: c, alpha: 0, delay: 4000, duration: 500, onComplete: () => c.destroy() });
    }
    if (this.note) this.note.setVisible(this.room === "floor");
    this.blink += dt;
    const on = Math.floor(this.blink * 6) % 2 === 0;
    const hot = this.hotRule();
    if (!hot) { this.ruleT += dt; if (this.ruleT > 3.5) { this.ruleT = 0; this.ruleIdx = (this.ruleIdx + 1) % this.rules.length; } }
    const here = this.room === "stock" && this.has("knock") ? "knock" : this.room === "out" && this.has("lamp") ? "lamp" : null;
    const rule = hot || here || this.rules[this.ruleIdx];
    const sig = rule + (hot ? "!" : "");
    if (sig !== this.ruleShown) {
      this.ruleShown = sig;
      this.ruleTxt.setText(t("rulePre") + t("rule_" + rule)).setColor(hot ? C.red : C.yellow);
      this.ruleIcon.setFrame(hot ? "warning" : "rule");
    }
    this.ruleTxt.setAlpha(hot && !on ? 0.35 : 1);

    const m = Math.min(this.min, 60);
    const s = `0${3 + Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}`;
    const clockHot = hot === "clock";
    this.clockTxt.setText(s).setAlpha(clockHot && !on ? 0.2 : 1);
    this.hudClock.setText(s).setColor(clockHot ? C.red : C.white);
  }

  // ---- input --------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("UP,DOWN,LEFT,RIGHT,W,A,S,D");
    ["SPACE", "Z", "ENTER"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  available(kind) {
    if (kind === "serve") return !!this.front();
    if (kind === "shelf") return this.tasks.shelf.active && this.carry === "box";
    return this.tasks[kind].active;
  }

  front() { const c = this.queue[0]; return c && c.atSlot && !c.out ? c : null; }

  near(kind, r = 5) {
    if (kind === "serve") return this.behind;
    return Phaser.Math.Distance.Between(this.p.x, this.p.y, SPOT[kind].x, SPOT[kind].y) <= r;
  }

  // go and do a job: serving means getting behind the counter first
  goDo(kind) {
    if (this.working && this.working.kind !== kind) this.cancelWork();
    this.intent = kind; this.target = null;
  }

  /** Hop over the counter. Arc from the gate to the register (or back). */
  vault(toBehind, then) {
    if (this.vaulting) return;
    this.cancelWork();
    this.vaulting = true; this.vaultDepth = COUNTER_DEPTH + 5;
    const p = this.p, a = { x: p.x, y: p.y }, b = toBehind ? { x: SPOT.serve.x, y: SPOT.serve.y } : { ...GATE };
    this.face = toBehind ? "up" : "left";
    p.play(`${P}_${this.face}_walk`, true); p.anims.pause();
    snd.sfx("hop");
    this.tweens.addCounter({
      from: 0, to: 1, duration: 340,
      onUpdate: tw => {
        const v = tw.getValue();
        p.setPosition(Math.round(a.x + (b.x - a.x) * v), Math.round(a.y + (b.y - a.y) * v - Math.sin(v * Math.PI) * 16));
        if (toBehind && v > 0.75) this.vaultDepth = BEHIND_DEPTH;
      },
      onComplete: () => {
        this.vaulting = false; this.behind = toBehind; this.face = "left";
        p.anims.resume();
        if (then) then();
      },
    });
  }

  vaultOut(next) {
    this.vault(false, () => { this.target = next || null; });
  }

  /** Stop everything and look at the door. */
  look() {
    if (this.vaulting) return;
    this.cancelWork(); this.target = null; this.intent = null; this.face = "up";
  }

  /** At 03:33 any action counts as moving. */
  frozenNow() {
    if (this.stall > 0 && this.stallGrace <= 0) { this.fail("clock"); return true; }
    return this.stall > 0;
  }

  // keyboard action: do whatever job is within reach
  act() {
    if (this.bossActive()) return this.swing();
    if (this.over || this.working || this.frozenNow()) return;
    if (this.roomAct()) return;
    // Space does the closest waiting job: a customer at the till wins unless a task is right next to you
    const where = { serve: GATE, shelf: SPOT.shelf, fridge: SPOT.fridge, box: GATE, bins: DOOR, trash: this.trash ? { x: this.trash.x, y: this.trash.fy } : GATE };
    const d = k => Phaser.Math.Distance.Between(this.p.x, this.p.y, where[k].x, where[k].y);
    const jobs = [];
    if (this.carry === "trash") jobs.push("bins");
    if (this.tasks.shelf.active) jobs.push(this.carry === "box" ? "shelf" : "box");
    if (this.available("fridge")) jobs.push("fridge");
    if (this.trash && !this.carry) jobs.push("trash");
    const task = jobs.sort((a, b) => d(a) - d(b))[0];
    if (this.available("serve") && (this.behind || !task || d(task) > 24)) return this.goDo("serve");
    if (task) this.goDo(task);
  }

  // touch / mouse: tap a job to walk there and do it, tap the floor to walk
  tap(x, y) {
    if (this.over || y < BAR || y > H - BAR) return;
    if (this.bossActive()) return this.fightTap(x, y);
    if (this.frozenNow()) return;
    if (this.roomTap(x, y)) return;          // x, y are screen = room-local coordinates
    let kind = null;
    if (this.room === "floor") {
      if (x >= DOOR_TAP.x0 && x <= DOOR_TAP.x1 && y >= DOOR_TAP.y0 && y <= DOOR_TAP.y1) return this.look();
      const f = this.queue[0];
      if (f && ((Math.abs(x - f.spr.x) < 16 && y > f.spr.y - 48 && y < f.spr.y + 6) || (x > 232 && y > 84 && y < 146))) kind = "serve";
      else if (this.tasks.shelf.active && x < 96 && y > 40) kind = this.carry === "box" ? "shelf" : "box";
      else if (this.tasks.fridge.active && x > 86 && x < 126 && y > 44 && y < 122) kind = "fridge";
    }
    if (kind) return this.goDo(kind);
    if (this.vaulting) return;
    const B = this.B, ty = Phaser.Math.Clamp(y, B.top, B.bot);
    const dest = { x: Phaser.Math.Clamp(x, B.xl(ty), B.xr(ty)), y: ty + this.oy };
    this.intent = null;
    if (this.working) this.cancelWork();
    if (this.behind) return this.vaultOut(dest);
    this.target = dest;
  }

  // ---- player -------------------------------------------------------------
  tickPlayer(dt) {
    const k = this.keys, p = this.p;
    if (this.vaulting) { this.moving = false; this.syncChar(p); return; }
    let vx = (k.RIGHT.isDown || k.D.isDown ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
    let vy = (k.DOWN.isDown || k.S.isDown ? 1 : 0) - (k.UP.isDown || k.W.isDown ? 1 : 0);
    const kvx = vx, kvy = vy;
    if (this.behind) {
      // at the register: left or down hops back over the counter, right goes through the staff door, up looks at the door
      if (vx < 0 || vy > 0) { this.intent = null; this.vaultOut(null); this.syncChar(p); return; }
      if (vx > 0) { this.intent = null; this.enterRoom("stock", ROOM.stock.enter, { face: "up" }); return; }
      if (vy < 0) this.look();
      vx = 0; vy = 0;
    }
    if (vx || vy) { this.target = null; this.intent = null; if (this.working) this.cancelWork(); }
    let maxStep = Infinity;
    if (!(vx || vy) && this.target && !this.working) {
      const dx = this.target.x - p.x, dy = this.target.y - p.y, dist = Math.hypot(dx, dy);
      if (dist < 1.2) { p.setPosition(this.target.x, this.target.y); this.target = null; }
      else { vx = dx / dist; vy = dy / dist; maxStep = dist; }   // never overshoot on a slow frame
    }

    this.moving = !!(vx || vy);
    if (this.moving) {
      const n = Math.hypot(vx, vy) || 1;
      vx /= n; vy /= n;
      if (vy > 0 && vy >= 0.5 * Math.abs(vx)) this.face = "down";
      else if (vy < 0 && -vy >= Math.abs(vx)) this.face = "up";
      else this.face = vx < 0 ? "left" : "right";
      const speed = SPEED * (this.carry ? 0.8 : 1);
      const step = Math.min(speed * dt, maxStep), ox = p.x, oy = p.y;
      const B = this.B, ny = Phaser.Math.Clamp(p.y - this.oy + vy * step, B.top, B.bot);
      p.setPosition(Phaser.Math.Clamp(p.x + vx * step, B.xl(ny), B.xr(ny)), ny + this.oy);
      if (this.target && Math.hypot(this.target.x - p.x, this.target.y - p.y) < 1.2) { p.setPosition(this.target.x, this.target.y); this.target = null; }
      else if (this.target && Math.hypot(p.x - ox, p.y - oy) < 0.01) this.target = null;   // blocked by a wall: give up
    }

    if (this.moving) { this.stepT -= dt; if (this.stepT <= 0) { snd.sfx("step"); this.stepT = 0.21; } } else this.stepT = 0;

    if (this.roomEdges(kvx, kvy)) return;
    // standing still with something to do: take the next leg (walk, vault, change room, start the job)
    if (!this.working && !this.vaulting && this.intent && !this.moving && !this.target) this.stepIntent();
    if (this.over || this.vaulting) return;

    if (this.working) {
      const w = this.working;
      w.t -= dt;
      this.workBar.clear().fillStyle(0x14101a).fillRect(p.x - 9, p.y - 53, 18, 4)
        .fillStyle(0xffd42a).fillRect(p.x - 8, p.y - 52, Math.round(16 * (1 - w.t / w.dur)), 2);
      if (w.kind === "serve") { this.scanT -= dt; if (this.scanT <= 0) { snd.sfx("scan"); this.scanT = 0.3; } }
      if (w.t <= 0) this.finishWork();
    }

    const key = this.working
      ? { serve: "left_work", shelf: "left_work", fridge: "up_walk" }[this.working.kind]
      : this.moving ? this.face + "_walk" : this.face === "down" ? "down_idle" : null;
    if (key) p.play(`${P}_${key}`, true);
    else { p.anims.stop(); p.setFrame(`${this.face}_walk_0`); }
    this.syncChar(p);
    this.bang.setPosition(Math.round(p.x), Math.round(p.y) - 56);
  }

  startWork(kind) {
    this.intent = null; this.target = null;
    if (kind === "serve" && this.front().isReg) return this.fail("regular");
    if (kind === "fridge" && this.fridgeCursed()) return this.fail("fridge");
    this.working = { kind, t: SPOT[kind].dur, dur: SPOT[kind].dur };
    this.face = SPOT[kind].face; this.scanT = 0;
    if (kind !== "serve") snd.sfx("work");
  }

  cancelWork() { this.working = null; this.workBar.clear(); }

  finishWork() {
    const kind = this.working.kind;
    this.cancelWork();
    if (kind === "serve") {
      const c = this.front();
      if (!c) return;
      this.queue.shift(); c.out = true; c.bar.clear();
      this.earn(c.pay, c.spr.x, c.spr.y - 50); snd.sfx("serve");
    } else {
      const task = this.tasks[kind];
      task.active = false; task.t = rand(9, 14) - this.d; task.mark.setVisible(false);
      if (kind === "shelf") { this.carry = null; this.carrySpr.setVisible(false); }
      this.earn(SPOT[kind].pay + 1000 * this.d, this.p.x, this.p.y - 50); snd.sfx("stock"); snd.sfx("coin", 0.25);
    }
  }

  earn(n, x, y) {
    this.pay += n; this.drawMoney();
    const pop = txt(this, x, y, "+" + won(n), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    this.tweens.add({ targets: pop, y: y - 14, alpha: 0, duration: 800, onComplete: () => pop.destroy() });
  }

  // ---- customers ----------------------------------------------------------
  walk(spr, tx, ty, speed, dt) {
    const dx = tx - spr.x, dy = ty - spr.y, dist = Math.hypot(dx, dy);
    if (dist < 1) { spr.setPosition(tx, ty); return true; }
    const step = Math.min(dist, speed * dt);
    spr.setPosition(spr.x + dx / dist * step, spr.y + dy / dist * step);
    const dir = Math.abs(dx) >= Math.abs(dy) ? (dx < 0 ? "left" : "right") : (dy < 0 ? "up" : "down");
    spr.play(`${spr.key}_${dir}_walk`, true);
    return false;
  }

  spawnCustomer() {
    const isReg = this.has("regular") && !this.regularHere && this.watch.state === "idle" && this.sinceReg >= 2 && Math.random() < 0.34;
    const inStore = this.customers.map(c => c.name);
    const free = NORMALS.filter(n => !inStore.includes(n));
    // From shift 4 the Regular wears someone else's face. Tells: no shadow, a flicker, the wrong door chime.
    const disguised = isReg && this.run.shift >= 4 && free.length > 0 && Math.random() < 0.7;
    const name = isReg && !disguised ? "regular" : pick(free);
    if (!name) return;
    const spr = this.makeChar(name, DOOR.x, DOOR.y);
    if (disguised) spr.sh.setVisible(false);
    const max = isReg ? 6.5 : Math.max(11, 19 - this.d);
    const c = { spr, name, isReg, disguised, max, pat: max, arrived: false, atSlot: false, out: false, glitchT: rand(1, 2.5),
      pay: 3000 + 500 * Math.floor(rand(0, 7)), bar: this.add.graphics().setDepth(600) };
    this.customers.push(c); this.queue.push(c);
    if (isReg) {
      this.regularHere = true; this.regDisguised = disguised; this.sinceReg = 0; snd.sfx("door_wrong");
      c.hintKey = disguised ? "disguise" : "regular";
      c.hint = this.hint(c.hintKey, spr.x, spr.y - 64);
    }
    else { this.sinceReg++; snd.sfx("door"); }
  }

  tickCustomers(dt) {
    this.custT -= dt;
    if (this.custT <= 0 && this.queue.length < 3 && !this.bossActive()) { this.spawnCustomer(); this.custT = Math.max(3, rand(5, 8) - this.d * 0.5); }

    for (const c of [...this.customers]) {
      const spr = c.spr;
      if (c.out) {
        if (this.walk(spr, DOOR.x, DOOR.y, 60, dt)) {
          if (c.isReg) { this.regularHere = false; if (c.hint) this.unhint(c.hintKey); }
          spr.sh.destroy(); spr.destroy(); c.bar.destroy();
          this.customers.splice(this.customers.indexOf(c), 1);
          continue;
        }
      } else {
        const slot = SLOTS[this.queue.indexOf(c)];
        c.atSlot = this.walk(spr, slot.x, slot.y, 46, dt);
        if (c.atSlot) { spr.anims.stop(); spr.setFrame("right_walk_0"); c.arrived = true; }
        if (c.arrived) this.drain(c, dt, 1);
      }
      if (c.hint && c.hint.active) c.hint.setPosition(Math.round(spr.x), Math.round(spr.y) - 64);
      if (c.disguised && !c.out) {
        c.glitchT -= dt;
        if (c.glitchT <= 0) {
          c.glitchT = rand(1.2, 2.6);
          spr.setTexture("characters_regular", spr.frame.name);
          this.time.delayedCall(90, () => { if (spr.active) spr.setTexture(spr.key, spr.frame.name); });
        }
      }
      this.syncChar(spr);
    }
  }

  /** Customers lose patience while waiting at the till. */
  drain(c, dt, mult) {
    if (c.out) return;
    const spr = c.spr;
    c.pat -= dt * mult;
    const f = Math.max(0, c.pat / c.max);
    c.bar.clear().fillStyle(0x14101a).fillRect(spr.x - 9, spr.y - 52, 18, 4)
      .fillStyle(c.isReg && !c.disguised ? 0xc8202f : f > 0.4 ? 0x7fc77a : 0xef3b4a).fillRect(spr.x - 8, spr.y - 51, Math.round(16 * f), 2);
    if (c.pat <= 0) {
      this.queue.splice(this.queue.indexOf(c), 1); c.out = true; c.bar.clear();
      if (this.working?.kind === "serve" && !this.front()) this.cancelWork();
      if (!c.isReg) this.strike(spr.x, spr.y - 50);
    }
  }

  strike(x, y) {
    this.strikes++;
    snd.sfx("strike"); snd.sfx("grumble", 0.05);
    this.strikeIcons.forEach((ic, i) => ic.setAlpha(i < this.strikes ? 1 : 0.18));
    const pop = txt(this, x, y, t("strike"), { ox: 0.5, size: 9, color: C.red, depth: 630 });
    this.tweens.add({ targets: pop, y: y - 14, alpha: 0, duration: 900, onComplete: () => pop.destroy() });
    this.cameras.main.shake(120, 0.004);
    if (this.strikes >= 3) this.fired();
  }

  // ---- side jobs + pickups ------------------------------------------------
  tickTasks(dt) {
    if (this.fridgeCursed()) {
      const f = this.tasks.fridge;
      if (!f.cursed) {
        f.cursed = true; f.active = true;
        // don't let a walk you started at 03:39 kill you: 03:40 cancels any trip to the fridge
        if (this.intent === "fridge") { this.intent = null; this.target = null; }
        if (this.working?.kind === "fridge") this.cancelWork();
        f.mark.setVisible(true).setTint(0xef3b4a);
        f.x3 = txt(this, SPOT.fridge.mark.x + 12, SPOT.fridge.mark.y - 6, t("x3"), { size: 9, color: C.yellow, depth: 611 });
        snd.sfx("task");
      }
    }
    for (const k of ["shelf", "fridge"]) {
      const task = this.tasks[k];
      if (!task.active) { task.t -= dt; if (task.t <= 0) { task.active = true; task.mark.setVisible(true); snd.sfx("task"); } }
    }
    this.itemT -= dt;
    if (this.itemT <= 0 && this.items.length < 2) {
      this.itemT = rand(5, 8);
      const y = rand(134, BOT - 1), x = rand(xl(y) + 8, Math.min(xr(y), 205));
      const kind = Math.random() < 0.3 ? "banknote" : "coin";
      const it = this.add.sprite(x, y - 4, kind === "coin" ? "props_coin_spin" : "props_items", kind === "coin" ? "coin_0" : "banknote").setDepth(y - 1);
      if (kind === "coin") it.play("props_coin_spin_coin");
      it.value = kind === "coin" ? 500 : 1000; it.fy = y;
      this.items.push(it);
    }
    for (const it of [...this.items]) {
      if (Phaser.Math.Distance.Between(this.p.x, this.p.y, it.x, it.fy) < 9) {
        this.items.splice(this.items.indexOf(it), 1); it.destroy();
        this.earn(it.value, this.p.x, this.p.y - 50); snd.sfx("coin");
      }
    }
  }

  // ---- rule: never turn your back to the door -----------------------------
  tickWatch(dt) {
    const w = this.watch;
    if (w.state === "idle") {
      if (this.regularHere) return;
      w.t -= dt;
      if (w.t <= 0) {
        w.state = "warn"; w.t = Math.max(0.75, 1.1 - this.d * 0.05);
        this.eyes.setVisible(true); this.bang.setVisible(true).play("props_exclaim_exclaim");
        snd.sfx("warn");
        this.watchesSeen++;
        // the first couple of times in a player's first runs, point at the door
        if (!S.seen.door && this.watchesSeen <= 2) {
          this.hintsShown.add("door");
          this.lookHint = txt(this, DOOR.x, 96, t("lookHint"), { ox: 0.5, color: C.yellow, depth: 630 });
          this.tweens.add({ targets: this.lookHint, y: 92, duration: 260, yoyo: true, repeat: -1 });
        }
      }
    } else if (w.state === "warn") {
      w.t -= dt;
      this.flick.setAlpha(Math.floor(w.t * 14) % 2 ? 0.32 : 0);
      if (w.t <= 0) {
        w.state = "watch"; w.t = rand(2.2, 3.4) + Math.min(1.5, this.d * 0.25); w.back = 0;
        w.limit = Math.max(0.3, 0.6 - this.d * 0.05);   // time to turn around once it is in the doorway
        w.faced = false;
        this.eyes.setVisible(false); this.bang.setVisible(false);
        this.ent.setVisible(true).setDepth(DOOR.y - 2).play("characters_regular_down_idle");
        this.flick.setAlpha(0.2); this.vigDark.setVisible(true);
        snd.sfx("appear"); snd.music("watch");
      }
    } else {
      // It must see your face. Look anywhere else for too long and you're done.
      if (this.face === "up" && !this.working?.kind?.match(/serve|shelf/)) { w.back = 0; w.faced = true; }
      else { w.back += dt; if (w.back > (w.faced ? 0.25 : w.limit)) return this.fail("door"); }
      w.t -= dt;
      if (w.t <= 0) {
        w.state = "idle"; w.t = Math.max(4, rand(7, 11) - this.d * 0.8);
        if (this.lookHint) { this.lookHint.destroy(); this.lookHint = null; }
        this.ent.setVisible(false); this.flick.setAlpha(0); this.vigDark.setVisible(false);
        snd.sfx("leave"); snd.music("store");
      }
    }
  }

  // ---- rule: do not move at 03:33 -----------------------------------------
  tickClock(dt) {
    if (this.stall > 0) {
      this.stall -= dt; this.stallGrace -= dt;
      if (this.stallGrace <= 0 && this.moving) return this.fail("clock");
      // customers don't care what time it is
      for (const c of [...this.queue]) if (c.arrived) this.drain(c, dt, 1.25);
      if (this.over) return;
      if (this.stall <= 0) {
        this.flick.setAlpha(0); snd.ambience(true); snd.music(this.watch.state === "watch" ? "watch" : "store");
        this.customers.forEach(c => c.spr.anims.resume());
        this.unhint("clock");
        if (this.lure) { const l = this.lure; this.lure = null; this.tweens.add({ targets: l, alpha: 0, x: l.x - 40, duration: 500, onComplete: () => l.destroy() }); }
      }
      else { this.tickT = (this.tickT || 0) - dt; if (this.tickT <= 0) { snd.sfx(this.tock ? "tock" : "tick"); this.tock = !this.tock; this.tickT = 0.5; } }
      return;
    }
    if (this.bossActive()) return;           // time stands still while you fight
    this.minT += dt;
    if (this.minT < MINLEN) return;
    this.minT -= MINLEN; this.min++;
    if (this.deokgu && this.run.shift === BOSS_SHIFT && this.min === BOSS_MIN) return this.startBoss();
    if (this.has("fridge") && this.min === 37) this.hint("fridge", SPOT.fridge.mark.x, SPOT.fridge.mark.y - 20);
    if (this.has("fridge") && this.min === 44) this.unhint("fridge");
    if (this.has("clock")) {
      if (this.min === 30) this.hint("clock", 176, 62);
      if (this.min >= 30 && this.min < 33) snd.sfx(this.min % 2 ? "tock" : "tick");
      if (this.min === 33) {
        this.stall = rand(3, 3.8); this.stallGrace = 0.45;
        this.cancelWork(); this.target = null; this.intent = null;
        snd.music("off"); snd.ambience(false); snd.sfx("bell"); this.flick.setAlpha(0.3); this.tickT = 1.2;
        snd.sfx("ring", 1.0);
        this.customers.forEach(c => c.spr.anims.pause());
        // a ₩10,000 note lands right by your feet
        const ply = this.p.y - this.oy;
        const lx = this.behind ? GATE.x - 30 : Phaser.Math.Clamp(this.p.x + (this.p.x > 160 ? -26 : 26), this.B.xl(ply) + 6, this.B.xr(ply) - 6);
        const ly = (this.behind ? GATE.y : ply);
        this.lure = this.add.container(lx, ly + this.oy - 6, [
          this.add.image(0, 0, "props_items", "banknote"),
          txt(this, 0, -16, "₩10,000", { ox: 0.5, size: 9, color: C.yellow }),
        ]).setDepth(ly + 1);
      }
    }
    if (this.min >= 60) this.clockOut();
  }

  // ---- endings ------------------------------------------------------------
  bank(extra = 0) {
    const run = this.run, total = this.pay + extra;
    run.earned += total; run.debt = Math.max(0, run.debt - total);
    this.pay = 0;
  }

  freeze() {
    this.over = true;
    snd.music("off"); snd.ambience(false);
    this.workBar.clear(); this.bang.setVisible(false); this.eyes.setVisible(false);
    if (this.boss) this.endBossFx();
    if (this.lookHint) { this.lookHint.destroy(); this.lookHint = null; }
    Object.keys(this.hints).forEach(k => this.unhint(k));
    Object.values(this.tasks).forEach(k => k.mark.setVisible(false));
    this.customers.forEach(c => c.bar.clear());
  }

  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);   // the GIF ends on the scare
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTexture("bg_store_wrong"); this.counter.setTexture("bg_store_counter_wrong");
    if (this.room !== "floor") this.roomBg[this.room].setTint(0xff5a5a);
    this.flick.setAlpha(0); this.vigDark.setVisible(false); this.vigRed.setVisible(true);
    this.staticTile.setVisible(true);
    this.staticEv = this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    this.items.forEach(i => i.setVisible(false));
    this.customers.forEach(c => {
      if (c.isReg) { c.spr.setVisible(false); c.spr.sh.setVisible(false); return; }
      c.spr.setTint(0x8c1526); c.spr.play(c.spr.key + "_scared");
    });
    const p = this.p;
    p.play(P + "_scared");
    // it was behind you the whole time: twice your size, looming over your shoulder
    if (cause !== "ratking") this.ent.setVisible(true).setScale(2).setPosition(p.x, p.y + 2).setDepth(p.y - this.oy - 1).play("characters_regular_down_idle");
    else if (this.boss?.spr) { this.boss.spr.setFrame("tell"); this.rats.forEach(r => r.setTint(0x8c1526)); }
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }

  stamp(key) {
    // a paper slip so the stamp reads over the busy store
    this.add.rectangle(W / 2, H / 2, 164, 72, 0xf6f1e7).setStrokeStyle(1, 0x14101a).setDepth(955);
    const s = this.add.image(W / 2, H / 2, key).setDepth(960).setScale(3).setAlpha(0);
    this.tweens.add({ targets: s, scale: 2, alpha: 1, duration: 140, ease: "Quad.easeIn", onComplete: () => { snd.sfx("stamp"); this.cameras.main.shake(140, 0.008); } });
  }

  fired(cause = "fired") {
    if (this.over) return;
    cancelReplay();
    this.freeze(); this.bank(); recordBest();
    this.flick.setAlpha(0.45);
    snd.jingle("gameover");
    this.time.delayedCall(350, () => this.stamp("ui_stamp_fired"));
    if (cause === "quota") {
      const m = txt(this, W / 2, H / 2 + 40, t("cause_quota"), { ox: 0.5, color: C.red, depth: 960 });
      m.setAlpha(0); this.tweens.add({ targets: m, alpha: 1, delay: 500, duration: 200 });
    }
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => this.scene.start("Result", { cause }));
  }

  clockOut() {
    if (this.over) return;
    // beating the Rat King is the job tonight: no quota on top of that
    if (this.pay < this.quota && this.boss?.phase !== "done") return this.fired("quota");
    markSeen([...this.hintsShown]);
    cancelReplay();
    if (this.run.daily) return this.dailyDone();
    this.freeze();
    const bonus = hourly(1);      // one hour at the gig's minimum-wage multiple
    this.bank(bonus);
    this.run.cleared++; this.run.shift++; recordBest();
    this.drawMoney();
    this.ent.setVisible(false); this.vigDark.setVisible(false); this.flick.setAlpha(0.35);
    snd.jingle("clockout");
    this.stamp("ui_stamp_success");
    const b = txt(this, W / 2, H / 2 + 40, `${t("wagePaid")} +${won(bonus)}`, { ox: 0.5, color: C.yellow, depth: 960 });
    b.setAlpha(0); this.tweens.add({ targets: b, alpha: 1, delay: 300, duration: 200 });
    this.p.anims.stop(); this.p.setFrame("face_smile");
    const win = this.run.debt <= 0;
    const actDone = this.boss?.phase === "done";      // the Rat King is beaten: Act 1 is over
    if (actDone) clearAct(1, this.run);
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => win ? this.scene.start("Result", { cause: "win" })
      : actDone ? this.scene.start("Board", { context: "clear", act: 1 }) : this.scene.start("Agency", { context: "next" }));
  }

  dailyDone() {
    this.freeze(); this.bank();
    saveDaily({ done: true, ok: true, pay: this.run.earned });
    this.ent.setVisible(false); this.vigDark.setVisible(false); this.flick.setAlpha(0.35);
    snd.jingle("clockout"); this.stamp("ui_stamp_success");
    this.p.anims.stop(); this.p.setFrame("face_smile");
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => this.scene.start("Result", { cause: "daily" }));
  }

  update(time, ms) {
    // HUD and screen effects (depth 640+) stay put while the camera moves between areas
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over) return;
    const dt = Math.min(ms, 50) / 1000 * (window.__speed || 1);   // __speed: test hook for bots
    this.tickClock(dt);
    if (this.over) return;
    this.tickPlayer(dt);
    if (this.over) return;
    if (this.bossActive()) {
      this.tickCustomers(dt);              // they're running for the door
      this.tickBoss(dt);
      if (this.over) return;
      this.tickFightChase();
      this.tickHud(dt);
      return;
    }
    this.tickDeokgu(dt);
    if (this.stall <= 0) {
      // the door watch only runs on the shop floor; walking off the floor while it watches is turning your back
      if (this.room === "floor") this.tickWatch(dt);
      else if (this.watch.state !== "idle") return this.fail("door");
      if (this.over) return;
      this.tickRooms(dt);
      if (this.over) return;
      this.tickCustomers(dt);
      this.tickTasks(dt);
    }
    this.tickHud(dt);
  }
}

Object.assign(Shift.prototype, RoomMixin, BossMixin);

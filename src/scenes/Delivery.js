import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, pick, soundToggle } from "../ui.js";
import { S, t, won, recordBest, drulesFor } from "../state.js";
import { GigMixin } from "./gig.js";
import { ResidentMixin, CHASE_NIGHT, CHASE_MIN } from "./resident.js";
import * as snd from "../audio.js";
import { startReplay, endReplay } from "../replay.js";

// Act 2: night delivery at the 해달마을 apartments. Side view: Sora walks left/right on one floor line.
// Four places, one on screen at a time:
//   hub     pick up an order at the counter (hand back 4th-floor ones), ride out the door on the right
//   ride    the moped across the night street (costs clock time)
//   hall    a corridor on floor 1..5: elevator (left), three flats, stairwell door (right)
//   stairs  the stairwell: walk off the right edge to climb, the left edge to go down (out, from floor 1)
const FY = 150;                 // feet line
const SPEED = 82;
const MINLEN = 1.6;             // real seconds per in-game minute (01:30 -> 02:30)
const FEET = 46 / 48;
const P = "characters_sora";
const TOPF = 5;
const HUB = { counter: 170, exit: 290, arrive: 276 };
const HALL = { elev: 38, doors: [110, 170, 230], stair: 293 };
const STAIR = { door: 162, up: 306, down: 12 };
const RIDE_MIN = 3, CLIMB_MIN = 1;
const NO_ELEV_MIN = 30;         // 02:00

/** Pay you must earn in a delivery shift. */
export const dQuotaFor = shift => 20000 + 5000 * (shift - 1);

export default class Delivery extends Phaser.Scene {
  constructor() { super("Delivery"); }

  create() {
    const run = S.run;
    this.run = run;
    this.rules = drulesFor(run.shift);
    this.d = run.shift - 1;
    this.over = false; this.pay = 0; this.strikes = 0; this.quota = dQuotaFor(run.shift);
    this.min = 0; this.minT = 0;
    this.hintsShown = new Set(); this.hints = {};
    this.clockBase = 90; this.hintPre = "d_";
    this.order = null; this.busy = false; this.target = null; this.intent = null;
    this.place = "hub"; this.floor = 1; this.face = "right"; this.stepT = 0;
    this.openT = 0;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    if (window.__speed) { this.tweens.timeScale = window.__speed; this.time.timeScale = window.__speed; }

    // world: one background swapped per place, plus overlays
    this.bg = this.add.image(0, 0, "bg_milk_depot").setOrigin(0);
    this.elevOpen = this.add.image(18, 86, "props_elevator_open").setOrigin(0).setDepth(2).setVisible(false);
    this.doorOpen = this.add.image(0, 92, "props_officetel_door_open").setOrigin(0).setDepth(2).setVisible(false);
    this.floorTxt = txt(this, 38, 71, "", { ox: 0.5, size: 9, color: C.red, shadow: false, depth: 3 });
    this.plates = HALL.doors.map(x => txt(this, x, 79, "", { ox: 0.5, size: 9, color: C.ink, shadow: false, depth: 3 })
      .setBackgroundColor("#dcd7e0").setPadding(2, 0, 2, 0));
    this.bigFloor = txt(this, 86, 44, "", { ox: 0.5, color: C.grey, shadow: false, depth: 3 }).setScale(2);
    this.navL = txt(this, 6, FY - 26, "", { size: 9, color: C.yellow, depth: 630 });
    this.navR = txt(this, W - 6, FY - 26, "", { ox: 1, size: 9, color: C.yellow, depth: 630 });
    this.dim = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x4a0f1c).setOrigin(0).setDepth(600).setAlpha(0);
    this.moped = this.add.image(0, FY, "props_moped").setOrigin(0.5, 1).setDepth(140).setVisible(false);
    this.stalker = this.add.sprite(0, FY, "characters_regular", "down_idle_0").setOrigin(0.5, FEET).setTintFill(0x14101a).setDepth(80).setVisible(false);
    this.staticTile = this.add.tileSprite(0, BAR, W, H - 2 * BAR, "props_static_overlay", "static_0").setOrigin(0)
      .setDepth(690).setAlpha(0.28).setVisible(false);
    this.vigRed = this.add.image(0, 0, "ui_vignette_red").setOrigin(0).setDepth(700).setVisible(false);
    this.flick = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a).setOrigin(0).setAlpha(0).setDepth(650);

    // player and the bag she carries
    this.sh = this.add.image(0, FY - 1, "props_shadow_blob").setAlpha(0.6).setDepth(99);
    this.p = this.add.sprite(HUB.arrive - 40, FY, P, "right_walk_0").setOrigin(0.5, FEET).setDepth(100);
    this.bag = this.add.image(0, 0, "props_milk_carrier").setDepth(101).setVisible(false);
    this.workBar = this.add.graphics().setDepth(620);

    this.buildHud();
    this.initNote(40, "stairs");
    this.bindInput();
    this.enter("hub", HUB.arrive - 40);
    startReplay(this.game);
    snd.music("store"); snd.ambience(false);

    const plate = this.add.rectangle(W / 2, 70, 150, 34, 0x14101a, 0.85).setStrokeStyle(1, 0xffd42a).setDepth(879);
    const title = txt(this, W / 2, 56, t("shiftN", run.shift), { ox: 0.5, color: C.yellow, depth: 880 });
    const goal = txt(this, W / 2, 71, t("quotaLine", won(this.quota)), { ox: 0.5, size: 9, depth: 880 });
    this.tweens.add({ targets: [plate, title, goal], alpha: 0, delay: 2400, duration: 400, onComplete: () => { plate.destroy(); title.destroy(); goal.destroy(); } });
    if (run.shift === 1) {
      const hint = txt(this, W / 2, H - BAR - 14, t("dHint"), { ox: 0.5, size: 9, depth: 880 });
      this.tweens.add({ targets: hint, alpha: 0, delay: 5000, duration: 500, onComplete: () => hint.destroy() });
    }
  }

  has(rule) { return this.rules.includes(rule); }
  noElevator() { return this.has("elevator") && this.min >= NO_ELEV_MIN; }

  // ---- places ----------------------------------------------------------------
  /** Show a place. x = where Sora stands on arrival. */
  enter(place, x) {
    this.place = place; this.target = null; this.intent = null;
    this.clearHints();
    this.elevOpen.setVisible(false); this.doorOpen.setVisible(false);
    this.floorTxt.setText(""); this.plates.forEach(p => p.setText("").setVisible(false)); this.bigFloor.setText("");
    this.navL.setText(""); this.navR.setText("");
    this.bg.clearTint(); this.dim.setAlpha(0); this.stalker.setVisible(false);
    this.p.setVisible(true); this.p.x = x;
    const f4 = this.floor === 4;
    if (place === "hub") {
      this.bg.setTexture("bg_milk_depot");
      this.navR.setText(t("hint_out").slice(0, 1));
      if (!this.order) this.hint("pick", HUB.counter, 92);
    } else if (place === "hall") {
      this.bg.setTexture("bg_officetel_hall");
      this.floorTxt.setText(String(this.floor));
      HALL.doors.forEach((dx, i) => this.plates[i].setText(`${this.floor}0${i + 1}`).setVisible(true));
      if (f4) { this.bg.setTint(0xd9a0a0); this.dim.setAlpha(0.18); this.hint("f4", 170, 60); }
      this.opened = false;       // a door that opens first only does it once per visit
    } else if (place === "stairs") {
      this.bg.setTexture("bg_stairwell");
      this.bigFloor.setText(`${this.floor}F`).setColor(f4 ? C.red : C.grey).setX(86);
      this.navR.setText(this.floor < TOPF ? t("stairsUp") : "");
      this.navL.setText(this.floor > 1 ? t("stairsDown") : t("exitOut"));
      if (f4) { this.bg.setTint(0xd9a0a0); this.dim.setAlpha(0.12); }
      if (this.floor === 1 && !this.order) this.hint("back", 70, 60);
    }
    this.syncP();
  }

  /** Fade out, run fn (which changes place), fade in. */
  cut(fn, ms = 220) {
    this.busy = true;
    this.cameras.main.fadeOut(ms, 20, 16, 26);
    this.time.delayedCall(ms + 20, () => {
      if (this.over) return;
      fn();
      this.cameras.main.fadeIn(ms, 20, 16, 26);
      this.time.delayedCall(ms, () => { this.busy = false; });
    });
  }

  /** The moped ride between the hub and the apartments. */
  ride(toApts) {
    this.busy = true; this.clearHints();
    this.cameras.main.fadeOut(200, 20, 16, 26);
    this.time.delayedCall(220, () => {
      if (this.over) return;
      this.place = "ride";
      this.bg.setTexture("bg_street_night").clearTint(); this.dim.setAlpha(0);
      this.floorTxt.setText(""); this.plates.forEach(p => p.setText("").setVisible(false)); this.bigFloor.setText(""); this.navL.setText(""); this.navR.setText("");
      this.elevOpen.setVisible(false); this.doorOpen.setVisible(false);
      const dir = toApts ? 1 : -1;
      this.moped.setVisible(true).setFlipX(!toApts).setPosition(toApts ? -30 : W + 30, FY + 2);
      this.p.anims.stop(); this.p.setFrame(`${toApts ? "right" : "left"}_walk_0`);
      this.cameras.main.fadeIn(200, 20, 16, 26);
      snd.sfx("moped"); this.time.delayedCall(700, () => snd.sfx("moped"));
      let fr = 0;
      const spin = this.time.addEvent({ delay: 90, loop: true, callback: () => { fr ^= 1; this.moped.setTexture(fr ? "props_moped_b" : "props_moped"); } });
      this.tweens.add({
        targets: this.moped, x: toApts ? W + 30 : -30, duration: 1500,
        onUpdate: () => { this.p.setPosition(this.moped.x - dir * 4, this.moped.y - 12); this.sh.setVisible(false); this.bag.setPosition(this.moped.x - dir * 15, this.moped.y - 30); },
        onComplete: () => {
          spin.remove();
          this.addMin(RIDE_MIN);
          if (this.over) return;
          this.cut(() => {
            this.moped.setVisible(false); this.sh.setVisible(true);
            this.p.y = FY;
            if (toApts) { this.floor = 1; this.enter("hall", HALL.stair - 8); this.face = "left"; }
            else { this.enter("hub", HUB.arrive); this.face = "left"; }
          }, 180);
        },
      });
    });
  }

  addMin(n) {
    this.min += n;
    if (this.min >= 60) this.clockOut();
  }

  // ---- input -----------------------------------------------------------------
  bindInput() {
    const kb = this.input.keyboard;
    this.keys = kb.addKeys("LEFT,RIGHT,A,D,UP,W");
    ["SPACE", "Z", "ENTER", "UP", "W"].forEach(k => kb.on("keydown-" + k, () => this.act()));
    this.input.on("pointerdown", p => { snd.init(); this.tap(p.x, p.y); });
  }

  /** Interactive spots in the current place: [x, reach, what]. */
  spots() {
    if (this.place === "hub") return [[HUB.counter, 16, "counter"], [HUB.exit, 16, "exit"]];
    if (this.place === "hall") return [[HALL.elev, 16, "elev"], ...HALL.doors.map((x, i) => [x, 11, "door" + i]), [HALL.stair, 22, "stair"]];
    if (this.place === "stairs") return [[STAIR.door, 14, "hall"]];
    return [];
  }

  /** Do whatever is within reach. */
  act() {
    if (this.over || this.busy || this.working || this.place === "ride") return;
    if (this.place === "roof") { this.pickPhone(); return; }
    if (this.boss) return;
    const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
    if (s) this.use(s[2]);
  }

  tap(x, y) {
    if (this.over || this.busy || this.place === "ride" || y < BAR || y > H - BAR) return;
    if (this.place === "chase") { this.target = x < W / 2 ? 0 : W; this.intent = null; return; }
    if (this.place === "roof") { this.target = Phaser.Math.Clamp(x, 12, W - 12); this.intent = Math.abs(x - 250) < 24 ? "phone" : null; return; }
    if (this.working) this.cancelWork();
    // tapping an edge of the stairwell means "take the stairs"
    if (this.place === "stairs" && x > 280) { this.target = W + 10; this.intent = null; return; }
    if (this.place === "stairs" && x < 40) { this.target = -10; this.intent = null; return; }
    const s = this.spots().find(([sx, r]) => Math.abs(x - sx) <= Math.max(r, 24) && y > 70);
    this.target = Phaser.Math.Clamp(s ? s[0] : x, 6, W - 6);
    this.intent = s ? s[2] : null;
  }

  use(what) {
    this.intent = null; this.target = null;
    if (what === "phone") return this.pickPhone();
    if (what === "counter") return this.counter();
    if (what === "exit") return this.ride(true);
    if (what === "elev") return this.elevator();
    if (what === "stair") return this.cut(() => this.enter("stairs", STAIR.door));
    if (what === "hall") return this.cut(() => this.enter("hall", HALL.stair));
    if (what.startsWith("door")) return this.startWork("knock", +what[4]);
  }

  // ---- the hub counter: take an order, or hand back a 4th-floor one ----------
  counter() {
    if (this.order && this.order.floor === 4) {
      this.unhint("return");
      this.order = null; this.bag.setVisible(false);
      snd.sfx("print"); this.pop(t("returned"), HUB.counter, 96, C.grey);
      return;
    }
    if (this.order) return;
    this.unhint("pick");
    const four = this.has("floor4") && Math.random() < 0.28 + 0.04 * this.d;
    const floor = four ? 4 : pick([1, 2, 3, 5, 5, 3, 2]);
    const flat = Phaser.Math.Between(1, 3);
    // from the second night some doors open before you get to knock
    const trap = this.has("opendoor") && !four && Math.random() < 0.4;
    this.order = { floor, flat, num: `${floor}0${flat}`, at: this.min, trap };
    this.bag.setVisible(true);
    snd.sfx("print"); this.time.delayedCall(450, () => snd.sfx("task"));
    this.pop(t("order", this.order.num), HUB.counter, 96, C.yellow);
    if (four) this.hint("return", HUB.counter, 80);
    else this.hint("out", HUB.exit - 10, 80);
  }

  // ---- the elevator --------------------------------------------------------------
  elevator() {
    let goal = this.order ? this.order.floor : 1;
    if (goal === this.floor) goal = this.floor === 1 ? TOPF : 1;
    this.busy = true; this.face = "up";
    this.elevOpen.setVisible(true); snd.sfx("ding"); snd.sfx("slide", 0.1);
    this.tweens.add({ targets: this.p, x: HALL.elev, duration: 200 });
    if (this.noElevator()) {
      // after 02:00 the doors open on something else
      this.time.delayedCall(400, () => {
        this.stalker.setVisible(true).setPosition(HALL.elev, FY).setScale(1.5).setDepth(101);
        this.fail("elevator");
      });
      return;
    }
    this.time.delayedCall(450, () => {
      this.p.setVisible(false); this.elevOpen.setVisible(false); snd.sfx("slide");
      this.time.delayedCall(350, () => this.cut(() => {
        this.floor = goal;
        this.enter("hall", HALL.elev);
        this.elevOpen.setVisible(true); this.face = "right";
        this.time.delayedCall(400, () => { snd.sfx("ding"); });
        this.time.delayedCall(700, () => { if (this.place === "hall") this.elevOpen.setVisible(false); });
      }, 260));
    });
  }

  // ---- knocking and leaving the bag ---------------------------------------------
  startWork(kind, i) {
    const dur = 0.9;
    this.working = { kind, i, t: dur, dur };
    this.face = "up"; snd.sfx("knock");
  }

  cancelWork() { this.working = null; this.workBar.clear(); }

  finishKnock(i) {
    const num = `${this.floor}0${i + 1}`;
    if (this.floor === 4) return this.fail("floor4");
    if (this.opened && this.order?.trap && i === this.order.flat - 1) return this.fail("opendoor");
    if (this.order && this.order.num === num) {
      const took = this.min - this.order.at;
      const tip = Math.max(0, Math.round((5000 - Math.max(0, took - 7) * 600) / 500) * 500);
      const base = 8000 + 1000 * this.d;
      this.order = null; this.bag.setVisible(false);
      this.earn(base, HALL.doors[i], 70);
      if (tip > 0) this.time.delayedCall(300, () => this.earn(tip, HALL.doors[i], 82, t("tip") + " "));
      snd.sfx("serve");
      if (this.floor === 1) this.hint("back", 160, 60);
      return;
    }
    this.strike(HALL.doors[i]);
  }


  // ---- HUD -----------------------------------------------------------------------

  hotRule() {
    if (this.boss) return "boss3";
    if (this.opened && this.place === "hall" && this.order?.trap) return "opendoor";
    if (this.place === "hall" && this.floor === 4) return "floor4";
    if (this.order?.floor === 4) return "floor4";
    if (this.has("elevator") && this.min >= NO_ELEV_MIN - 3 && this.place === "hall") return "elevator";
    return null;
  }


  // ---- player --------------------------------------------------------------------
  syncP() {
    const p = this.p;
    this.sh.setPosition(Math.round(p.x), FY - 1);
    this.bag.setPosition(Math.round(p.x) + (this.face === "left" ? -8 : 8), FY - 18);
  }

  tickPlayer(dt) {
    const k = this.keys, p = this.p;
    if (this.busy || this.place === "ride") return;
    let vx = (k.RIGHT.isDown || k.D.isDown ? 1 : 0) - (k.LEFT.isDown || k.A.isDown ? 1 : 0);
    if (vx) { this.target = null; this.intent = null; if (this.working) this.cancelWork(); }
    else if (this.target !== null && !this.working) {
      const dx = this.target - p.x;
      if (Math.abs(dx) < 1) { p.x = this.target; this.target = null; if (this.intent) return this.use(this.intent); }
      else vx = Math.sign(dx);
    }
    const moving = !!vx;
    if (moving) {
      this.face = vx < 0 ? "left" : "right";
      let step = SPEED * dt;
      if (this.target !== null) step = Math.min(step, Math.abs(this.target - p.x));
      p.x += vx * step;
      this.stepT -= dt; if (this.stepT <= 0) { snd.sfx("step"); this.stepT = 0.2; }
      // the stairwell's edges are the stairs
      if (this.place === "stairs") {
        if (p.x >= STAIR.up && this.floor < TOPF) return this.climb(1);
        if (p.x <= STAIR.down) return this.floor > 1 ? this.climb(-1) : this.ride(false);
      }
      p.x = Phaser.Math.Clamp(p.x, 8, W - 8);
    } else this.stepT = 0;

    if (this.working) {
      const w = this.working;
      w.t -= dt;
      this.workBar.clear().fillStyle(0x14101a).fillRect(p.x - 9, FY - 53, 18, 4)
        .fillStyle(0xffd42a).fillRect(p.x - 8, FY - 52, Math.round(16 * (1 - w.t / w.dur)), 2);
      if (w.t <= 0) { this.cancelWork(); this.finishKnock(w.i); if (this.over) return; }
    }
    const key = this.working ? "work" : moving ? this.face + "_walk" : null;
    if (key) p.play(`${P}_${key}`, true);
    else { p.anims.stop(); p.setFrame(`${this.face === "up" ? "up" : this.face}_walk_0`); }
    this.syncP();
  }

  climb(dir) {
    this.busy = true; this.p.anims.stop();
    snd.sfx("step"); this.time.delayedCall(120, () => snd.sfx("step")); this.time.delayedCall(240, () => snd.sfx("step"));
    this.tweens.add({ targets: this.p, y: FY - dir * 10, duration: 220 });
    this.cut(() => {
      this.addMin(CLIMB_MIN);
      if (this.over) return;
      this.floor += dir; this.p.y = FY;
      this.enter("stairs", dir > 0 ? STAIR.up - 22 : STAIR.down + 22);
    }, 200);
  }

  // ---- the door that opens before you knock --------------------------------------
  tickDoor(dt) {
    if (this.place !== "hall" || !this.order?.trap || this.floor !== this.order.floor) return;
    const dx = HALL.doors[this.order.flat - 1];
    const dist = Math.abs(this.p.x - dx);
    if (!this.opened && dist < 60) {
      this.opened = true; this.openT = 0;
      this.doorOpen.setVisible(true).setPosition(dx - 14, 92);
      snd.sfx("creak"); snd.sfx("heart", 0.3);
      this.hint("open", dx, 58);
      this.cameras.main.shake(100, 0.003);
    }
    if (this.opened) {
      // standing right in front of it is what gets you
      if (dist < 34) { this.openT += dt; if (this.openT > 2.2) return this.fail("opendoor"); }
      else this.openT = Math.max(0, this.openT - dt * 0.5);
      this.flick.setAlpha(dist < 34 ? 0.15 + 0.1 * Math.sin(this.blink * 30) : 0);
    }
  }

  // ---- ending the shift ----------------------------------------------------------

  fail(cause) {
    if (this.over) return;
    this.freeze(); this.bank(); recordBest();
    endReplay(1700);
    snd.sfx("fail"); snd.sfx("static", 1.2);
    this.bg.setTint(0xff5a5a); this.vigRed.setVisible(true); this.staticTile.setVisible(true);
    this.time.addEvent({ delay: 70, loop: true, callback: () => this.staticTile.setFrame("static_" + Phaser.Math.Between(0, 3)) });
    const p = this.p;
    p.setVisible(true); p.play(P + "_scared");
    // the Resident: one tenant behind every door, a little taller on every floor
    if (!this.stalker.visible) {
      const sx = this.place === "hall" && cause === "opendoor" ? HALL.doors[this.order.flat - 1] : p.x + (this.face === "left" ? 14 : -14);
      this.stalker.setVisible(true).setPosition(sx, FY + 2).setScale(1.3 + 0.08 * this.floor).setDepth(99);
    }
    this.cameras.main.shake(450, 0.012);
    this.time.delayedCall(1700, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2050, () => this.scene.start("Result", { cause }));
  }


  clockHot() { return this.noElevator(); }
  tickSlip() {
    this.slip.setText(this.order ? t("order", this.order.num) : t("noOrder")).setColor(this.order?.floor === 4 ? C.red2 : C.ink);
  }

  update(time, ms) {
    for (const o of this.children.list) if (o.depth >= 640 && o.scrollFactorY !== 0) o.setScrollFactor(0);
    if (this.over) return;
    const dt = Math.min(ms, 50) / 1000 * (window.__speed || 1);
    if (this.boss) {
      this.tickPlayer(dt);
      if (this.over) return;
      this.tickBoss(dt);
      if (this.over) return;
      return this.tickHud(dt);
    }
    this.minT += dt;
    while (this.minT >= MINLEN) { this.minT -= MINLEN; this.addMin(1); if (this.over) return; }
    if (this.run.shift === CHASE_NIGHT && this.min >= CHASE_MIN && !this.busy && this.place !== "ride") return this.startBoss();
    if (this.noElevator() && this.place === "hall") this.hint("elev", 84, 60);
    this.tickPlayer(dt);
    if (this.over) return;
    this.tickDoor(dt);
    if (this.over) return;
    this.tickHud(dt);
  }
}

Object.assign(Delivery.prototype, GigMixin, ResidentMixin);

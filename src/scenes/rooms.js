// The store is three connected areas laid out on one map, one screen apart vertically:
//   floor  (y +0)     the shop: customers, counter, shelves, fridge
//   stock  (y +1000)  the stockroom behind the staff door: boxes for restocking, and a steel door that knocks
//   out    (y +2000)  the street in front of the store: trash bins, and something under the streetlamp
// The camera jumps between them. Everything keeps running while you are away from the floor.
import Phaser from "phaser";
import { W, H, BAR, C, txt, rand, pick } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";

export const FLOOR_TOP = 118, FLOOR_BOT = 154;
const floorXl = y => 100 - (y - FLOOR_TOP) * 1.45;
const floorXr = y => Math.min(240, 213 + (y - FLOOR_TOP) * 1.3);

export const ROOM = {
  floor: { oy: 0, bg: "bg_store_day", top: FLOOR_TOP, bot: FLOOR_BOT, xl: floorXl, xr: floorXr },
  stock: { oy: 1000, bg: "bg_backroom", top: 113, bot: 150,
    xl: y => 126 - (y - 113) * 2.0, xr: y => 194 + (y - 113) * 2.0,
    exit: { x: 160, y: 150 }, enter: { x: 160, y: 146 }, boxes: { x: 100, y: 144 }, door: { x: 160, y: 82 } },
  out: { oy: 2000, bg: "bg_street_night", top: 141, bot: 150, xl: () => 14, xr: () => 300,
    door: { x: 177, y: 144 }, bins: { x: 214, y: 147 }, lamp: { x: 52, y: 147 } },
};

const STAFF_DOOR = { x: 305, y: 96 };          // behind the counter, on the floor
const FLOOR_DOOR = { x: 161, y: 119 };         // the front door, from inside
const TRASH_SPOTS = [{ x: 206, y: 151 }, { x: 132, y: 152 }, { x: 178, y: 149 }];
const GATE = { x: 236, y: 140 };
const REGISTER = { x: 266, y: 95 };

export const RoomMixin = {
  initRooms() {
    this.room = "floor";
    this.roomBg = { floor: this.bg };
    for (const k of ["stock", "out"]) this.roomBg[k] = this.add.image(0, ROOM[k].oy, ROOM[k].bg).setOrigin(0).setDepth(0);
    this.B = ROOM.floor; this.oy = 0;
    this.carry = null;
    this.carrySpr = this.add.image(0, 0, "props_box_closed").setDepth(625).setVisible(false);

    // floor: the staff door behind the counter, and trash to take out
    this.staffDoor = this.add.image(STAFF_DOOR.x, STAFF_DOOR.y, "props_door_staff").setOrigin(0.5, 1).setDepth(90);
    this.trash = null; this.trashT = rand(10, 16);

    // stockroom: the box pile, and the steel door
    const s = ROOM.stock;
    this.add.image(s.boxes.x - 18, s.oy + s.boxes.y + 2, "props_box_stack").setOrigin(0.5, 1).setDepth(s.boxes.y - 2);
    this.stockExit = txt(this, s.exit.x, s.oy + 146, t("toFloor"), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    this.knockFx = this.add.rectangle(130, s.oy + 52, 60, 58, 0xef3b4a).setOrigin(0).setDepth(5).setAlpha(0);
    this.knockTxt = txt(this, s.door.x, s.oy + 40, "", { ox: 0.5, color: C.red, depth: 630 });
    this.knock = { active: false, t: rand(2.5, 5), left: 0 };

    // outside: the bins, and the lamp
    const o = ROOM.out;
    this.outDoor = txt(this, o.door.x, o.oy + 100, t("toStore"), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    this.lampMan = this.add.sprite(o.lamp.x, o.oy + o.lamp.y, "characters_regular", "down_idle_0")
      .setOrigin(0.5, 46 / 48).setTintFill(0x14101a).setDepth(o.lamp.y).setVisible(false);
    this.lampEyes = this.add.sprite(o.lamp.x, o.oy + o.lamp.y - 33, "props_red_eyes", "eyes_open").setDepth(o.lamp.y + 1).setVisible(false);
    this.lampFlick = this.add.rectangle(20, o.oy + 30, 64, 120, 0x14101a).setOrigin(0).setDepth(o.lamp.y + 2).setAlpha(0);
    this.lamp = { state: "idle", t: rand(1, 2.5), back: 0 };

    this.waitTxt = txt(this, W - 6, BAR + 18, "", { ox: 1, size: 9, color: C.white, depth: 895 });
  },

  /** Move the player (and camera) into another area. */
  enterRoom(name, at, opts = {}) {
    const from = this.room;
    this.room = name; this.B = ROOM[name]; this.oy = ROOM[name].oy;
    this.cameras.main.setScroll(0, this.oy);
    this.behind = !!opts.behind;
    this.p.setPosition(at.x, at.y + this.oy);
    this.target = null;
    this.face = opts.face || this.face;
    this.cancelWork();
    snd.sfx(name === "out" || from === "out" ? "door" : "creak");
    snd.duck(name === "floor" ? 1 : name === "stock" ? 0.35 : 0.2);
    snd.ambience(name === "floor");
    if (from === "stock") { this.knock = { active: false, t: rand(2.5, 5), left: 0 }; this.knockFx.setAlpha(0); this.knockTxt.setText(""); }
    if (from === "out") { this.lamp = { state: "idle", t: rand(1, 2.5), back: 0 }; this.lampMan.setVisible(false); this.lampEyes.setVisible(false); this.lampFlick.setAlpha(0); }
    if (name === "stock") this.hint("box", ROOM.stock.boxes.x, ROOM.stock.oy + 100);
    if (name === "out") this.hint("bins", ROOM.out.bins.x, ROOM.out.oy + 112);
    this.syncChar(this.p);
  },

  /** Local (room) position helpers. */
  at(pt, r = 2) { return Phaser.Math.Distance.Between(this.p.x, this.p.y, pt.x, pt.y + this.oy) < r; },
  goTo(pt) { this.target = { x: pt.x, y: pt.y + this.oy }; },

  /** Head back to the shop floor from the stockroom or the street. */
  exitRoom() {
    if (this.room === "stock") {
      if (this.at(ROOM.stock.exit, 3)) this.enterRoom("floor", REGISTER, { behind: true, face: "left" });
      else this.goTo(ROOM.stock.exit);
    } else if (this.room === "out") {
      if (this.at(ROOM.out.door, 3)) this.enterRoom("floor", FLOOR_DOOR, { face: "down" });
      else this.goTo(ROOM.out.door);
    }
  },

  /** Walk the player one leg closer to finishing this.intent. Called whenever she is standing still. */
  stepIntent() {
    const it = this.intent, r = this.room;
    if (!it) return;
    const viaGate = () => { if (this.at(GATE)) this.vault(true); else this.goTo(GATE); };
    const offCounter = () => { if (this.behind) { this.vaultOut(null); return true; } return false; };
    switch (it) {
      case "serve":
        if (r !== "floor") return this.exitRoom();
        if (this.behind) { if (this.available("serve")) this.startWork("serve"); else this.intent = null; }
        else viaGate();
        return;
      case "box":
      case "stock":
        if (r === "stock") {
          if (it === "stock") { this.intent = null; return; }
          if (this.at(ROOM.stock.boxes, 3)) return this.pickUp("box");
          return this.goTo(ROOM.stock.boxes);
        }
        if (r === "out") return this.exitRoom();
        if (this.behind) return this.enterRoom("stock", ROOM.stock.enter, { face: "up" });
        return viaGate();
      case "leave":
        if (r === "floor") { this.intent = null; return; }
        return this.exitRoom();
      case "shelf": case "fridge": {
        if (r !== "floor") return this.exitRoom();
        if (offCounter()) return;
        const sp = this.spot(it);
        if (this.at(sp, 2)) { if (this.available(it)) this.startWork(it); else this.intent = null; }
        else this.goTo(sp);
        return;
      }
      case "trash":
        if (r !== "floor") return this.exitRoom();
        if (offCounter()) return;
        if (!this.trash) { this.intent = null; return; }
        if (this.at({ x: this.trash.x, y: this.trash.fy }, 4)) return this.pickUp("trash");
        return this.goTo({ x: this.trash.x, y: this.trash.fy });
      case "bins":
        if (r === "stock") return this.exitRoom();
        if (r === "floor") {
          if (offCounter()) return;
          if (this.at(FLOOR_DOOR, 3)) return this.enterRoom("out", ROOM.out.door, { face: "right" });
          return this.goTo(FLOOR_DOOR);
        }
        if (this.at(ROOM.out.bins, 4)) return this.dropTrash();
        return this.goTo(ROOM.out.bins);
      case "in":
        if (r === "out") return this.exitRoom();
        this.intent = null;
        return;
      default:
        this.intent = null;
    }
  },

  pickUp(what) {
    this.carry = what;
    this.carrySpr.setTexture(what === "box" ? "props_box_closed" : "props_trash_bag").setVisible(true);
    snd.sfx("work");
    if (what === "box") { this.unhint("box"); this.intent = this.tasks.shelf.active ? "shelf" : null; }
    else { this.trash.destroy(); this.trash = null; this.unhint("trash"); this.intent = "bins"; }
  },

  dropTrash() {
    this.carry = null; this.carrySpr.setVisible(false); this.intent = null;
    this.unhint("bins");
    snd.sfx("stock");
    this.earn(7000 + 1000 * this.d, this.p.x, this.p.y - 50);
    snd.sfx("coin", 0.25);
  },

  /** Space in the stockroom or outside. Returns true if handled. */
  roomAct() {
    if (this.room === "stock") {
      this.goDo(this.carry !== "box" && this.tasks.shelf.active ? "box" : this.carry === "box" ? "shelf" : "leave");
      return true;
    }
    if (this.room === "out") { this.goDo(this.carry === "trash" ? "bins" : "in"); return true; }
    return false;
  },

  /** Taps outside the shop floor, and the floor's new hotspots. Returns true if handled. */
  roomTap(x, y) {
    if (this.room === "stock") {
      if (x < 128 && y > 104) return this.goDo("box"), true;
      if (y >= 144) return this.goDo("leave"), true;
      return false;
    }
    if (this.room === "out") {
      if (x > 196 && x < 236 && y > 118) return this.goDo("bins"), true;
      if (x > 156 && x < 198 && y > 96) return this.goDo("in"), true;
      return false;
    }
    // floor: staff door behind the counter, trash on the floor, the front door while carrying trash
    if (x >= 288 && y >= 40 && y <= 96) return this.goDo("stock"), true;
    if (this.trash && Math.abs(x - this.trash.x) < 12 && Math.abs(y - (this.trash.fy - 6)) < 12) return this.goDo("trash"), true;
    if (this.carry === "trash" && x > 128 && x < 196 && y > 30 && y < 120) return this.goDo("bins"), true;
    return false;
  },

  /** Keyboard walking between areas. */
  roomEdges(vx, vy) {
    const p = this.p, ly = p.y - this.oy;
    if (this.room === "stock" && vy > 0 && ly >= ROOM.stock.bot - 0.5) return this.enterRoom("floor", REGISTER, { behind: true, face: "left" }), true;
    if (this.room === "out" && vy < 0 && Math.abs(p.x - ROOM.out.door.x) < 12) return this.enterRoom("floor", FLOOR_DOOR, { face: "down" }), true;
    if (this.room === "floor" && this.carry === "trash" && vy < 0 && ly <= FLOOR_TOP + 0.5 && Math.abs(p.x - FLOOR_DOOR.x) < 16)
      return this.enterRoom("out", ROOM.out.door, { face: "right" }), true;
    if (this.room === "stock" && this.carry !== "box" && this.at(ROOM.stock.boxes, 6) && this.tasks.shelf.active) this.pickUp("box");
    if (this.room === "out" && this.carry === "trash" && this.at(ROOM.out.bins, 6)) this.dropTrash();
    return false;
  },

  // --------------------------------------------------------------- per frame
  tickRooms(dt) {
    // carried thing rides above your head
    if (this.carry) this.carrySpr.setPosition(Math.round(this.p.x), Math.round(this.p.y) - 52).setDepth(626);

    // trash appears on the shop floor now and then
    if (!this.trash && this.carry !== "trash") {
      this.trashT -= dt;
      if (this.trashT <= 0) {
        const sp = pick(TRASH_SPOTS);
        this.trash = this.add.image(sp.x, sp.y, "props_trash_bag").setOrigin(0.5, 1).setDepth(sp.y - 1);
        this.trash.fy = sp.y;
        this.trashT = rand(14, 22);
        this.hint("trash", sp.x, sp.y - 26);
      }
    }

    // who is waiting at the till while you're away
    if (this.room !== "floor") {
      const waiting = this.queue.filter(c => c.arrived && !c.out && !c.isReg);
      const low = waiting.some(c => c.pat < c.max * 0.4);
      this.waitTxt.setText(waiting.length ? t("waiting", waiting.length) : "").setColor(low ? C.red : C.white);
    } else this.waitTxt.setText("");

    this.tickKnock(dt);
    this.tickLamp(dt);
  },

  // Rule: when the steel door knocks, get out of the stockroom.
  tickKnock(dt) {
    if (this.room !== "stock" || !this.has("knock")) return;
    const k = this.knock;
    if (!k.active) {
      k.t -= dt;
      if (k.t <= 0) {
        k.active = true; k.left = Math.max(2.2, 3.2 - this.d * 0.1);
        snd.sfx("knock");
        this.hint("knock", ROOM.stock.door.x, ROOM.stock.oy + 58);
      }
      return;
    }
    k.left -= dt;
    this.knockFx.setAlpha(Math.floor(k.left * 8) % 2 ? 0.35 : 0.1);
    this.knockTxt.setText(String(Math.max(1, Math.ceil(k.left))));
    if (Math.floor((k.left + dt) * 1.4) !== Math.floor(k.left * 1.4)) snd.sfx("knock");
    if (k.left <= 0) this.fail("knock");
  },

  // Rule: don't look at what stands under the streetlamp.
  tickLamp(dt) {
    if (this.room !== "out" || !this.has("lamp")) return;
    const L = this.lamp;
    L.t -= dt;
    if (L.state === "idle" && L.t <= 0) {
      L.state = "warn"; L.t = 0.7; snd.sfx("buzz");
    } else if (L.state === "warn") {
      this.lampFlick.setAlpha(Math.floor(L.t * 16) % 2 ? 0.6 : 0);
      if (L.t <= 0) {
        L.state = "on"; L.t = rand(3, 4.5); L.back = 0;
        this.lampFlick.setAlpha(0); this.lampMan.setVisible(true); this.lampEyes.setVisible(true);
        snd.sfx("appear");
        this.hint("lamp", ROOM.out.lamp.x + 40, ROOM.out.oy + 80);
      }
    } else if (L.state === "on") {
      if (this.face === "left") { L.back += dt; if (L.back > 0.3) return this.fail("lamp"); } else L.back = 0;
      if (L.t <= 0) {
        L.state = "idle"; L.t = rand(2, 4);
        this.lampMan.setVisible(false); this.lampEyes.setVisible(false);
        snd.sfx("leave");
      }
    }
  },

  hotRoomRule() {
    if (this.room === "stock" && this.knock.active) return "knock";
    if (this.room === "out" && this.lamp.state !== "idle") return "lamp";
    return null;
  },
};

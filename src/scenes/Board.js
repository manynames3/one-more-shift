import Phaser from "phaser";
import { W, H, BAR, C, txt, soundToggle } from "../ui.js";
import { S, t, ACTS, actOpen, newRun, GIG } from "../state.js";
import * as snd from "../audio.js";
import { setActionLabel } from "../touchpad.js";

// The agency's job board: one card per act. Shown from the title once Act 1 is cleared,
// and right after beating the Rat King (context "clear"), where the store gets stamped.
const CW = 42, CH = 78, GAP = 3, X0 = (W - (CW * 7 + GAP * 6)) / 2, Y0 = BAR + 26;

export default class Board extends Phaser.Scene {
  constructor() { super("Board"); }

  create(data) {
    setActionLabel("");
    this.ctx = data?.context || "title";
    this.clearedAct = data?.act || 1;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    snd.ambience(false); snd.music("office");
    this.add.image(0, 0, "bg_street_night").setOrigin(0);
    this.add.rectangle(0, 0, W, H, 0x14101a, 0.72).setOrigin(0);
    this.add.rectangle(0, 0, W, BAR, 0x14101a).setOrigin(0);
    this.add.rectangle(0, H - BAR, W, BAR, 0x14101a).setOrigin(0);
    txt(this, W / 2, 6, t("board"), { ox: 0.5, size: 9, color: C.yellow });
    soundToggle(this);

    this.sel = 0;
    this.cards = ACTS.map((a, i) => this.makeCard(a, X0 + i * (CW + GAP), Y0, i));
    this.desc = txt(this, W / 2, Y0 + CH + 8, "", { ox: 0.5, size: 9, color: C.white });
    txt(this, W / 2, H - 15, t("board_keys"), { ox: 0.5, size: 9, color: C.dim });
    this.pick(0, true);

    this.locked = this.ctx === "clear";
    if (this.ctx === "clear") this.playClear();

    const kb = this.input.keyboard;
    kb.on("keydown-LEFT", () => this.pick(this.sel - 1));
    kb.on("keydown-RIGHT", () => this.pick(this.sel + 1));
    kb.on("keydown-A", () => this.pick(this.sel - 1));
    kb.on("keydown-D", () => this.pick(this.sel + 1));
    kb.on("keydown-SPACE", () => this.choose());
    kb.on("keydown-ENTER", () => this.choose());
    kb.on("keydown-ESC", () => this.leave("Title"));
  }

  /** One job card: act number, name, a status tag. Locked cards show a question mark. */
  makeCard(a, x, y, i) {
    const open = actOpen(a.n), clear = !!S.acts[a.n];
    const c = this.add.container(x, y);
    const frame = this.add.rectangle(0, 0, CW, CH, open ? 0x2a2233 : 0x1c1724).setOrigin(0).setStrokeStyle(1, 0x7b7689);
    c.add(frame);
    c.add(txt(this, CW / 2, 4, t("act", a.n), { ox: 0.5, size: 9, color: open ? C.grey : C.dim, shadow: false }));
    c.add(txt(this, CW / 2, 26, open ? "" : "?", { ox: 0.5, color: C.dim, shadow: false }));
    if (open) c.add(this.add.image(CW / 2, 42, ...this.icon(a.key)).setOrigin(0.5, 1));
    c.add(txt(this, CW / 2, 46, open ? t("job_" + a.key) : "???", { ox: 0.5, size: 9, color: open ? C.white : C.dim, shadow: false, wrap: CW - 4 }));
    const st = clear ? "st_clear" : !open ? "st_locked" : a.built ? "st_open" : "st_soon";
    const tag = txt(this, CW / 2, CH - 14, t(st), { ox: 0.5, size: 9, shadow: false,
      color: { st_clear: C.green, st_open: C.yellow, st_soon: C.orange, st_locked: C.dim }[st] });
    c.add(tag);
    c.frame = frame; c.tag = tag; c.act = a; c.open = open; c.baseY = y;
    frame.setInteractive({ useHandCursor: true }).on("pointerdown", () => { snd.init(); this.sel === i ? this.choose() : this.pick(i); });
    return c;
  }

  /** Small picture for each open job, borrowed from the existing props. */
  icon(key) {
    return {
      store: ["props_register"], event: ["props_balloon"], delivery: ["props_milk_carrier"], cinema: ["props_cctv", "cctv_0"],
      trial: ["props_pill", "blue_0"], site: ["props_brick"], park: ["props_note"],
    }[key];
  }

  pick(i, quiet) {
    i = Phaser.Math.Wrap(i, 0, this.cards.length);
    if (!quiet) snd.sfx("ui");
    this.cards.forEach((c, k) => {
      c.frame.setStrokeStyle(1, k === i ? 0xffd42a : 0x7b7689);
      this.tweens.killTweensOf(c); c.y = c.baseY;
    });
    this.sel = i;
    const c = this.cards[i];
    this.tweens.add({ targets: c, y: c.baseY - 3, duration: 380, yoyo: true, repeat: -1, ease: "Stepped", easeParams: [3] });
    const a = c.act;
    const key = !c.open ? "jd_locked" : !a.built ? "jd_soon" : a.n > 1 ? "jd_" + a.key : this.ctx === "clear" && this.clearedAct === 1 ? "jd_keep" : "jd_store";
    this.desc.setText(t(key)).setColor(!c.open ? C.dim : !a.built ? C.orange : C.white);
  }

  choose() {
    if (this.locked) return;
    const a = this.cards[this.sel].act;
    if (!this.cards[this.sel].open || !a.built) {
      snd.sfx("strike");
      this.cameras.main.shake(90, 0.004);
      return;
    }
    this.locked = true;
    snd.sfx("start");
    // the job you just finished: keep working it (endless nights, same run)
    if (this.ctx === "clear" && a.n === this.clearedAct) return this.leave("Agency", { context: "next" });
    if (a.n > 1) { newRun(a.n); return this.leave("Agency", { context: GIG[a.n].intro }); }
    newRun();
    this.leave("Agency", { context: S.runs > 1 ? "again" : "intro" });
  }

  leave(scene, data) {
    this.locked = true;
    this.cameras.main.fadeOut(250, 20, 16, 26);
    this.time.delayedCall(280, () => this.scene.start(scene, data));
  }

  /** Just beat the Rat King: the manager dodges the question, the store gets stamped, Act 2 opens. */
  playClear() {
    const n = this.clearedAct, store = this.cards[n - 1], next = this.cards[n];
    this.pick(n, true);
    if (next) next.setAlpha(0.35);
    const say = txt(this, W / 2, BAR + 8, t(n === 1 ? "board_clear" : "board_clear2"), { ox: 0.5, size: 9, color: C.white });
    say.setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
    this.time.delayedCall(900, () => {
      const s = txt(this, store.x + CW / 2, store.y + 30, t("st_clear"), { ox: 0.5, size: 9, color: C.green, depth: 20 });
      s.setBackgroundColor("#14101a").setPadding(2, 1, 2, 1).setScale(2).setAlpha(0);
      this.tweens.add({ targets: s, scale: 1, alpha: 1, duration: 180, ease: "Quad.easeIn" });
      snd.sfx("stamp"); this.cameras.main.shake(120, 0.006);
    });
    this.time.delayedCall(1800, () => {
      snd.sfx("ui");
      if (next) this.tweens.add({ targets: next, alpha: 1, duration: 300 });
      this.locked = false;
    });
  }
}

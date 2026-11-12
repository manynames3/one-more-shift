import Phaser from "phaser";
import { W, H, BAR, C, txt, onAdvance, button, artKey } from "../ui.js";
import { S, t, won, clearAct, saveEnding } from "../state.js";
import * as snd from "../audio.js";
import { setActionLabel, showPad } from "../touchpad.js";

// The three endings, then the credits.
//   sign  -> the front desk: the debt is gone and Sora hands the next worker a rule sheet
//   walk  -> walk out: Sora and 준호 leave at dawn, debt unpaid, the agency sign goes dark
//   note  -> the Regular's note: the Regular takes the desk instead
const BG = { sign: "bg_ending_desk", walk: "bg_ending_dawn", note: "bg_ending_note" };

export default class Ending extends Phaser.Scene {
  constructor() { super("Ending"); }

  create(data) {
    setActionLabel(""); showPad(false);
    this.rolling = false; this.leaving = false;
    const key = this.key = data?.ending || "walk";
    const run = S.run;
    if (key === "sign" && run) { run.earned += run.debt; run.debt = 0; }
    if (run) clearAct(7, run);
    saveEnding(key);
    snd.music("off"); snd.ambience(false);
    snd.jingle(key === "sign" ? "gameover" : "debtfree");
    this.cameras.main.fadeIn(800, 20, 16, 26);
    const CU = { sign: "cu_sora_desk", walk: "cu_sora_relief", note: "cu_regular" };
    this.add.image(0, 0, BG[key]).setOrigin(0);
    // the close-up comes in over the wide shot after the first line
    if (this.textures.exists(CU[key])) {
      const cu = this.add.image(0, 0, artKey(CU[key])).setOrigin(0).setAlpha(0).setDepth(5);
      this.tweens.add({ targets: cu, alpha: 1, delay: 2500, duration: 900 });
    }
    this.add.rectangle(0, 0, W, BAR, 0x14101a).setOrigin(0);
    this.add.rectangle(0, H - BAR, W, BAR, 0x14101a).setOrigin(0);
    txt(this, W / 2, 6, t("end_" + key), { ox: 0.5, size: 9, color: key === "sign" ? C.red : C.yellow });

    this.lines = t("endLines_" + key);
    this.i = 0;
    this.box = this.add.rectangle(W / 2, H - BAR - 18, W - 16, 30, 0x14101a, 0.9).setStrokeStyle(1, 0x7b7689).setDepth(10);
    this.line = txt(this, 14, H - BAR - 30, "", { size: 9, color: C.white, depth: 11, wrap: W - 30 });
    this.debt = txt(this, W - 8, BAR + 4, `${t("debt")} ${won(run?.debt ?? 0)}`, { ox: 1, size: 9, color: C.white, depth: 11 }).setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
    this.guard = this.time.now + 900;
    this.next();
    onAdvance(this, () => { if (this.time.now > this.guard) this.next(); });
  }

  next() {
    this.guard = this.time.now + 300;
    if (this.rolling) return this.toTitle();
    if (this.i < this.lines.length) { this.line.setText(this.lines[this.i++]); snd.sfx("type"); return; }
    this.credits();
  }

  credits() {
    this.rolling = true;
    this.box.destroy(); this.line.destroy();
    const pics = ["tc_store", "tc_event", "tc_milk", "tc_cinema", "tc_trial", "tc_site", "tc_park"].filter(k => this.textures.exists(k));
    pics.forEach((k, i) => {
      const im = this.add.image(0, 0, k).setOrigin(0).setDepth(19).setAlpha(0);
      this.tweens.add({ targets: im, alpha: 1, delay: 300 + i * 1200, duration: 500, yoyo: i < pics.length - 1, hold: 700 });
    });
    const shade = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a, pics.length ? 0.45 : 0.8).setOrigin(0).setDepth(20).setAlpha(0);
    this.tweens.add({ targets: shade, alpha: 1, duration: 600 });
    const roll = this.add.container(0, H).setDepth(21);
    t("credits").forEach((s, i) => roll.add(txt(this, W / 2, i * 16, s, { ox: 0.5, size: i === 0 ? 11 : 9, color: i === 0 ? C.yellow : C.white })));
    this.tweens.add({ targets: roll, y: BAR + 10, duration: 7000, ease: "Linear" });
    // share which ending you got
    this.time.delayedCall(1500, () => button(this, W / 2, H - BAR - 14, "ui_btn_secondary", t("share"), () => this.share(), 30));
    this.time.delayedCall(9000, () => this.toTitle());
  }

  async share() {
    this.guard = this.time.now + 600;
    const text = t("endShare", t("end_" + this.key)) + "\nhttps://one-more-shift.pages.dev";
    try { if (navigator.share) return await navigator.share({ text }); } catch { /* cancelled */ }
    try { await navigator.clipboard.writeText(text); } catch { /* no clipboard */ }
  }

  toTitle() {
    if (this.leaving) return;
    this.leaving = true;
    this.cameras.main.fadeOut(600, 20, 16, 26);
    this.time.delayedCall(650, () => this.scene.start("Title"));
  }
}

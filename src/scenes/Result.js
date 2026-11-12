import Phaser from "phaser";
import { W, H, BAR, C, txt, button, soundToggle } from "../ui.js";
import { S, t, won, hourly, newRun, MAX_CONTINUES, continueCost, saveDaily } from "../state.js";
import * as snd from "../audio.js";
import { sharePayStub } from "../share.js";
import { hasReplay, replayGif } from "../replay.js";

// End of a run: the pay stub prints, then retry or share.
export default class Result extends Phaser.Scene {
  constructor() { super("Result"); }

  create(data) {
    const run = S.run, cause = data.cause || "door";
    const daily = run.daily, dailyOk = cause === "daily";
    if (daily && !dailyOk) saveDaily({ done: true, ok: false, pay: run.earned, cause });
    const win = cause === "win" || dailyOk, fired = cause === "fired" || cause === "quota";
    this.cameras.main.fadeIn(300, 20, 16, 26);
    snd.ambience(false); snd.music("off");
    if (win) { snd.jingle("debtfree"); this.time.delayedCall(3400, () => snd.music("result")); }
    else this.time.delayedCall(400, () => snd.music("result"));
    this.add.image(0, 0, "bg_death_bg").setOrigin(0);

    const shiftNo = win ? run.cleared : run.cleared + 1;
    this.rows = [t(run.act === 2 ? "place2" : "place"), daily ? t("dailyRow", daily) : t("shiftRow", shiftNo), won(hourly(run.act || 1)), won(run.earned), t("cause_" + cause), daily ? "—" : won(run.debt)];
    this.stampKey = win ? "ui_stamp_success" : fired ? "ui_stamp_fired" : "ui_stamp_fail";

    // the stub (180x240) prints upward, then scrolls to show the bottom half
    const stub = this.add.container(14, H).setDepth(10);
    stub.add(this.add.image(0, 0, "ui_paystub").setOrigin(0));
    this.rows.forEach((v, i) => stub.add(txt(this, 66, 61 + 20 * i, v, {
      size: v.length > 13 ? 9 : 11, color: i === 4 || i === 5 ? C.red2 : C.ink, shadow: false,
    })));
    const stamp = this.add.container(100, 179, [
      this.add.rectangle(0, 0, 74, 28, 0xf6f1e7).setOrigin(0), this.add.image(0, 0, this.stampKey).setOrigin(0),
    ]).setVisible(false);
    stub.add(stamp);
    this.tweens.add({ targets: stub, y: BAR + 4, duration: 900, ease: "Stepped", easeParams: [18], onStart: () => snd.sfx("print") });
    this.tweens.add({ targets: stub, y: H - BAR - 244, delay: 2000, duration: 1400, ease: "Stepped", easeParams: [28] });
    this.time.delayedCall(3500, () => { stamp.setVisible(true); snd.sfx("stamp"); this.cameras.main.shake(120, 0.006); });

    // bars above the stub so it prints "through" the letterbox
    this.add.rectangle(0, 0, W, BAR, 0x14101a).setOrigin(0).setDepth(20);
    this.add.rectangle(0, H - BAR, W, BAR, 0x14101a).setOrigin(0).setDepth(20);

    const x = 256;
    txt(this, x, BAR + 12, t(dailyOk ? "over_daily" : win ? "over_win" : fired ? "over_fired" : "over_fail"), { ox: 0.5, color: win ? C.green : C.red, depth: 30 });
    txt(this, x, BAR + 30, t("cause_" + cause), { ox: 0.5, size: 9, depth: 30, wrap: 112 });
    txt(this, x, BAR + 48, daily ? won(run.earned) : t("survived", run.cleared), { ox: 0.5, size: daily ? 11 : 9, color: C.yellow, depth: 30 });
    if (!daily) txt(this, x, BAR + 60, `${t("debt")} ${won(run.debt)}`, { ox: 0.5, size: 9, color: C.grey, depth: 30 });

    this.locked = true;
    this.time.delayedCall(900, () => { this.locked = false; });
    // Continue from this shift for a cleanup fee (twice per run). Otherwise start over.
    this.canCont = !win && !daily && (run.continues || 0) < MAX_CONTINUES;
    if (this.canCont) {
      this.cost = continueCost(run.continues || 0);
      txt(this, x, BAR + 72, t("cont_cost", won(this.cost)), { ox: 0.5, size: 9, color: C.orange, depth: 30 });
      button(this, x, BAR + 92, "ui_btn_primary", t("cont_btn"), () => this.cont(), 30);
      button(this, x, BAR + 113, "ui_btn_danger", t("retry"), () => this.retry(), 30);
      this.shareBtn = button(this, x, BAR + 134, "ui_btn_secondary", t("share"), () => this.share(shiftNo, cause), 30);
      this.input.keyboard.on("keydown-C", () => this.cont());
    } else {
      button(this, x, BAR + 88, "ui_btn_primary", t("retry"), () => this.retry(), 30);
      this.shareBtn = button(this, x, BAR + 112, "ui_btn_secondary", t("share"), () => this.share(shiftNo, cause), 30);
    }
    soundToggle(this);
    this.input.keyboard.on("keydown-SPACE", () => this.canCont ? this.cont() : this.retry());
    this.input.keyboard.on("keydown-ENTER", () => this.canCont ? this.cont() : this.retry());
    this.input.keyboard.on("keydown-R", () => this.retry());
  }

  retry() {
    if (this.locked) return;
    this.locked = true;
    newRun(S.run.act || 1);
    this.cameras.main.fadeOut(220, 20, 16, 26);
    this.time.delayedCall(250, () => this.scene.start("Agency", { context: "again" }));
  }

  cont() {
    if (this.locked || !this.canCont) return;
    this.locked = true;
    const run = S.run;
    run.debt += this.cost; run.continues = (run.continues || 0) + 1;
    this.cameras.main.fadeOut(220, 20, 16, 26);
    this.time.delayedCall(250, () => this.scene.start("Agency", { context: "cont" }));
  }

  async share(shiftNo, cause) {
    const r = S.run;
    const text = r.daily ? t("dailyShare", r.daily, cause === "daily", won(r.earned), t("cause_" + cause)) : t("shareText", shiftNo, t("cause_" + cause));
    if (this.sharing) return;
    this.sharing = true;
    let gif = null;
    if (hasReplay()) {
      this.shareBtn.label.setText("...");
      try { gif = this.gif || (this.gif = await replayGif()); } catch { gif = null; }
      this.shareBtn.label.setText(t("share"));
    }
    const how = await sharePayStub(this, this.rows, this.stampKey, text, gif);
    this.sharing = false;
    if (how === "download") {
      this.shareBtn.label.setText(t("saved"));
      this.time.delayedCall(1500, () => this.shareBtn.label.setText(t("share")));
    }
  }
}

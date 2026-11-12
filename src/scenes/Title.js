import Phaser from "phaser";
import { W, H, C, txt, soundToggle } from "../ui.js";
import { S, t, saveSettings, newRun, newDailyRun, today, dailyRecord } from "../state.js";
import * as snd from "../audio.js";
import { setActionLabel } from "../touchpad.js";

export default class Title extends Phaser.Scene {
  constructor() { super("Title"); }

  create() {
    setActionLabel("");
    this.add.image(0, 0, "bg_title_bg").setOrigin(0);
    const logo = this.add.image(W / 2, 22, "ui_logo").setOrigin(0.5, 0);
    this.tweens.add({ targets: logo, y: 34, duration: 700, ease: "Bounce.easeOut" });

    this.prompt = txt(this, W / 2, H - 17, t("start"), { ox: 0.5 });
    this.tweens.add({ targets: this.prompt, alpha: 0.15, duration: 520, yoyo: true, repeat: -1, ease: "Stepped", easeParams: [2] });

    if (S.best > 0) txt(this, W / 2, 6, t("best", S.best + 1), { ox: 0.5, size: 9, color: C.yellow });

    this.lang = txt(this, 6, H - 16, "", { size: 9, color: C.grey }).setInteractive({ useHandCursor: true });
    this.lang.on("pointerdown", (p, x, y, ev) => { ev.stopPropagation(); this.flipLang(); });
    this.input.keyboard.on("keydown-L", () => this.flipLang());
    this.drawLang();
    soundToggle(this);

    // daily shift: same night for everyone, once a day
    this.daily = txt(this, W / 2, 112, t("daily", today()), { color: C.yellow, ox: 0.5 }).setInteractive({ useHandCursor: true });
    this.daily.setBackgroundColor("#14101a").setPadding(5, 2, 5, 2);
    this.daily.on("pointerdown", (p, x, y, ev) => { ev.stopPropagation(); this.startDaily(); });
    this.input.keyboard.on("keydown-D", () => this.startDaily());
    if (dailyRecord()?.done !== undefined) this.daily.setColor(C.dim);

    snd.music("title");   // starts on the first tap or key (browsers block sound before that)
    this.started = false;
    const go = () => {
      if (this.started) return;
      this.started = true;
      snd.init(); snd.sfx("start");
      this.cameras.main.fadeOut(250, 20, 16, 26);
      // once Act 1 is done, the job board comes first
      if (S.acts[1]) return this.time.delayedCall(280, () => this.scene.start("Board"));
      newRun();
      this.time.delayedCall(280, () => this.scene.start("Agency", { context: S.runs > 1 ? "again" : "intro" }));
    };
    this.input.keyboard.on("keydown", e => { if (!["KeyL", "KeyM", "KeyD"].includes(e.code)) go(); });
    this.input.on("pointerdown", go);
  }

  startDaily() {
    if (this.started) return;
    snd.init();
    if (dailyRecord()) {
      snd.sfx("strike");
      const m = txt(this, W / 2, 130, t("dailyDone"), { ox: 0.5, size: 9, color: C.orange });
      m.setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
      this.tweens.add({ targets: m, alpha: 0, delay: 1600, duration: 300, onComplete: () => m.destroy() });
      return;
    }
    this.started = true;
    snd.sfx("start");
    newDailyRun();
    this.cameras.main.fadeOut(250, 20, 16, 26);
    this.time.delayedCall(280, () => this.scene.start("Agency", { context: "dailyIntro" }));
  }

  flipLang() { S.lang = S.lang === "ko" ? "en" : "ko"; saveSettings(); snd.init(); snd.sfx("ui"); this.drawLang(); this.prompt.setText(t("start")); this.daily.setText(t("daily", today())); }
  drawLang() { this.lang.setText((S.lang === "ko" ? "[한국어]  EN" : "한국어  [EN]")); }
}

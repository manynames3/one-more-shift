import Phaser from "phaser";
import { W, H, C, txt, soundToggle } from "../ui.js";
import { S, t, saveSettings, newRun } from "../state.js";
import * as snd from "../audio.js";

export default class Title extends Phaser.Scene {
  constructor() { super("Title"); }

  create() {
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

    this.started = false;
    const go = () => {
      if (this.started) return;
      this.started = true;
      snd.init(); snd.sfx("coin");
      newRun();
      this.cameras.main.fadeOut(250, 20, 16, 26);
      this.time.delayedCall(280, () => this.scene.start("Agency", { context: S.runs > 1 ? "again" : "intro" }));
    };
    this.input.keyboard.on("keydown", e => { if (!["KeyL", "KeyM"].includes(e.code)) go(); });
    this.input.on("pointerdown", go);
  }

  flipLang() { S.lang = S.lang === "ko" ? "en" : "ko"; saveSettings(); snd.init(); snd.sfx("ui"); this.drawLang(); this.prompt.setText(t("start")); }
  drawLang() { this.lang.setText((S.lang === "ko" ? "[한국어]  EN" : "한국어  [EN]")); }
}

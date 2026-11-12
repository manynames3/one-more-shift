import Phaser from "phaser";
import { W, H, C, txt, button } from "../ui.js";
import { t } from "../state.js";
import * as snd from "../audio.js";
import { showPad } from "../touchpad.js";

// The shift scenes, which can be paused. Everything else is a menu or a story beat.
export const PLAY = ["Shift", "Event", "Delivery", "Cinema", "Ward", "Site", "Park"];

/** Pause whichever shift is running. Safe to call any time; does nothing outside play. */
export function pauseGame(game) {
  if (game.scene.isActive("Pause")) return;
  const s = PLAY.map(k => game.scene.getScene(k)).find(x => x && game.scene.isActive(x.scene.key));
  if (!s || s.over) return;
  s.scene.pause();
  game.scene.start("Pause", { from: s.scene.key });
}

/** P / Esc pause; leaving the tab or window pauses too, so a night isn't lost to a phone call. */
export function installPause(game) {
  window.addEventListener("keydown", e => {
    if (e.keyCode !== 80 && e.keyCode !== 27) return;
    if (game.scene.isActive("Pause")) game.scene.getScene("Pause").resume();
    else pauseGame(game);
  });
  window.addEventListener("blur", () => pauseGame(game));
  document.addEventListener("visibilitychange", () => { if (document.hidden) pauseGame(game); });
}

export default class Pause extends Phaser.Scene {
  constructor() { super("Pause"); }

  create(data) {
    this.from = data.from; this.leaving = false;
    this.scene.bringToTop();
    showPad(false);
    snd.hold(true);
    this.add.rectangle(0, 0, W, H, 0x07050a, 0.86).setOrigin(0).setInteractive();   // swallow taps behind
    this.add.rectangle(W / 2, 88, 132, 92, 0x14101a).setStrokeStyle(1, 0x4a4458);
    txt(this, W / 2, 50, t("paused"), { ox: 0.5, color: C.yellow });
    txt(this, W / 2, 64, t("pauseHint"), { ox: 0.5, size: 9, color: C.grey });
    button(this, W / 2, 96, "ui_btn_primary", t("resumeBtn"), () => this.resume());
    button(this, W / 2, 120, "ui_btn_secondary", t("quitTitle"), () => this.quit());
    this.input.keyboard.on("keydown-SPACE", () => this.resume());
    this.input.keyboard.on("keydown-ENTER", () => this.resume());
    this.input.keyboard.on("keydown-Q", () => this.quit());
  }

  resume() {
    if (this.leaving) return;
    this.leaving = true;
    snd.hold(false);
    const s = this.scene.get(this.from);
    s.input.keyboard.resetKeys();          // a key held when we paused would keep walking
    showPad(true);
    this.scene.stop();
    s.scene.resume();
  }

  quit() {
    if (this.leaving) return;
    this.leaving = true;
    snd.hold(false); snd.music("off"); snd.ambience(false);
    this.scene.stop(this.from);
    this.scene.start("Title");
  }
}

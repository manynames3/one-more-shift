import Phaser from "phaser";
import { W, H, C, txt, soundToggle } from "../ui.js";
import { CALM, setCalm } from "../calm.js";
import { S, t, saveSettings, newRun, newDailyRun, today, dailyRecord, notesFound, savedRun } from "../state.js";
import * as snd from "../audio.js";
import { setActionLabel, showPad } from "../touchpad.js";

export default class Title extends Phaser.Scene {
  constructor() { super("Title"); }

  create() {
    setActionLabel(""); showPad(false);
    this.add.image(0, 0, "bg_title_bg").setOrigin(0);
    const logo = this.add.image(W / 2, 22, "ui_logo").setOrigin(0.5, 0);
    this.tweens.add({ targets: logo, y: 34, duration: 700, ease: "Bounce.easeOut" });

    const saved = savedRun();
    this.resume = !S.acts[1] && saved && !saved.daily && (saved.act || 1) === 1 && saved.shift > 1 ? saved : null;
    this.prompt = txt(this, W / 2, H - 17, this.resume ? t("startCont", saved.shift) : t("start"), { ox: 0.5 });
    this.tweens.add({ targets: this.prompt, alpha: 0.15, duration: 520, yoyo: true, repeat: -1, ease: "Stepped", easeParams: [2] });

    if (S.best > 0) txt(this, 6, 6, t("best", S.best + 1), { size: 9, color: C.yellow });
    // story progress, once there is any
    const ends = Object.keys(S.endings || {}).length, notes = notesFound();
    if (ends || notes) txt(this, W - 6, 6, t("progress", ends, notes), { ox: 1, size: 9, color: C.grey });

    // settings look like buttons: a plate, a hover colour, and a key in brackets
    const asButton = o => o.setBackgroundColor("#2a2233").setPadding(4, 2, 4, 2).setInteractive({ useHandCursor: true })
      .on("pointerover", () => o.setColor(C.yellow)).on("pointerout", () => o.setColor(C.white));
    this.lang = asButton(txt(this, 4, H - 18, "", { size: 9, color: C.white, shadow: false }));
    this.lang.on("pointerdown", (p, x, y, ev) => { ev.stopPropagation(); this.flipLang(); });
    this.input.keyboard.on("keydown-L", () => this.flipLang());
    this.drawLang();
    soundToggle(this);
    this.calm = asButton(txt(this, W - 22, H - 18, "", { size: 9, color: C.white, ox: 1, shadow: false }));
    const flipCalm = () => { setCalm(!CALM.on); snd.init(); snd.sfx("ui"); this.drawCalm(); };
    this.calm.on("pointerdown", (p, x, y, ev) => { ev.stopPropagation(); flipCalm(); });
    this.input.keyboard.on("keydown-C", flipCalm);
    this.drawCalm();

    // daily challenge: a side mode, the same night for everyone, one try a day.
    // It only shows once Act 1 is done, so a new player sees one way in: press any key.
    this.daily = txt(this, W / 2, 110, t("daily", today()), { color: C.yellow, ox: 0.5 }).setInteractive({ useHandCursor: true });
    this.daily.setBackgroundColor("#14101a").setPadding(5, 2, 5, 2);
    this.dailySub = txt(this, W / 2, 126, t("dailySub"), { ox: 0.5, size: 9, color: C.white }).setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
    this.daily.on("pointerdown", (p, x, y, ev) => { ev.stopPropagation(); this.startDaily(); });
    if (dailyRecord()?.done !== undefined) this.daily.setColor(C.dim);
    const showDaily = !!S.acts[1];
    this.daily.setVisible(showDaily); this.dailySub.setVisible(showDaily);
    if (!showDaily) this.daily.disableInteractive();
    else this.input.keyboard.on("keydown-D", () => this.startDaily());

    snd.music("title");   // starts on the first tap or key (browsers block sound before that)
    this.started = false;
    const go = () => {
      if (this.started) return;
      this.started = true;
      snd.init(); snd.sfx("start");
      this.cameras.main.fadeOut(250, 20, 16, 26);
      // once Act 1 is done, the job board comes first
      if (S.acts[1]) return this.time.delayedCall(280, () => this.scene.start("Board"));
      // a night of Act 1 already under way: pick it up, don't start over
      if (this.resume) { S.run = this.resume; return this.time.delayedCall(280, () => this.scene.start("Agency", { context: "resume" })); }
      newRun();
      const ctx = S.runs > 1 ? "again" : "intro";
      // the very first night starts the way every gig does: on the phone
      this.time.delayedCall(280, () => S.runs > 1 ? this.scene.start("Agency", { context: ctx }) : this.scene.start("Offer", { act: 1, next: { scene: "Agency", data: { context: ctx } } }));
    };
    // setting keys (language, sound, daily, flashes, film, pause) don't start the game
    this.input.keyboard.on("keydown", e => { if (!["KeyL", "KeyM", "KeyC", "KeyF", "KeyP", "Escape", ...(S.acts[1] ? ["KeyD"] : [])].includes(e.code)) go(); });
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

  flipLang() { S.lang = S.lang === "ko" ? "en" : "ko"; saveSettings(); snd.init(); snd.sfx("ui"); this.drawLang(); this.drawCalm(); this.prompt.setText(this.resume ? t("startCont", this.resume.shift) : t("start")); this.daily.setText(t("daily", today())); this.dailySub.setText(t("dailySub")); }
  drawCalm() { this.calm.setText(t(CALM.on ? "flashOff" : "flashOn") + " (C)"); }
  drawLang() { this.lang.setText((S.lang === "ko" ? "[한국어] EN" : "한국어 [EN]") + " (L)"); }
}

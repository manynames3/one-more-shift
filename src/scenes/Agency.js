import Phaser from "phaser";
import { W, H, C, txt, soundToggle } from "../ui.js";
import { S, t, won, newRuleFor, MULT, hourly } from "../state.js";
import { quotaFor } from "./Shift.js";
import { dQuotaFor } from "./Delivery.js";
import * as snd from "../audio.js";

// Briefing: the manager talks, then hands over tonight's job card.
export default class Agency extends Phaser.Scene {
  constructor() { super("Agency"); }

  create(data) {
    const run = S.run;
    this.cameras.main.fadeIn(250, 20, 16, 26);
    snd.ambience(false);
    this.add.image(0, 0, "bg_agency_office").setOrigin(0);
    this.add.sprite(160, 118, "characters_kwak").setOrigin(0.5, 1).play("characters_kwak_down_idle");
    this.add.image(0, 0, "bg_agency_desk_fg").setOrigin(0);
    this.add.rectangle(0, 0, W, 22, 0x14101a).setOrigin(0);
    txt(this, 6, 6, run.daily ? t("dailyRow", run.daily) : t("shiftN", run.shift), { size: 9, color: C.yellow });
    soundToggle(this);

    this.newRule = newRuleFor(run.shift);
    const ctx = data?.context || "intro";
    snd.music(ctx === "intro" ? "title" : "office");
    this.act2 = run.act === 2;
    const brief = (this.act2 ? { 2: "d_brief2", 3: "d_brief3" } : { 2: "brief2", 3: "brief3", 4: "brief4", 5: "brief5", 6: "brief6", 7: "brief7" })[run.shift] || "same";
    this.lines = [...t(ctx === "next" ? brief : ctx)];
    this.face = ctx === "next" && brief !== "same" ? "sly" : ctx === "cont" ? "serious" : "smile";

    this.portrait = this.add.image(12, 106, "portraits_kwak", this.face).setOrigin(0).setCrop(2, 10, 60, 36);
    this.add.image(10, 112, "ui_dialog_box").setOrigin(0);
    this.l1 = txt(this, 80, 118, "");
    this.l2 = txt(this, 80, 134, "", { color: C.yellow });
    this.more = txt(this, 298, 142, "▼", { size: 9, color: C.grey }).setVisible(false);
    this.tweens.add({ targets: this.more, y: 144, duration: 300, yoyo: true, repeat: -1 });

    this.idx = 0; this.card = null; this.done = false;
    this.say();

    const adv = () => { snd.init(); this.advance(); };
    this.input.keyboard.on("keydown-SPACE", adv);
    this.input.keyboard.on("keydown-ENTER", adv);
    this.input.keyboard.on("keydown-Z", adv);
    this.input.on("pointerdown", adv);
  }

  // Type two lines at a time.
  say() {
    const a = this.lines[this.idx] || "", b = this.lines[this.idx + 1] || "";
    this.full = [a, b]; this.typed = 0; this.typing = true;
    this.l1.setText(""); this.l2.setText(""); this.more.setVisible(false);
    this.typer?.remove();
    this.typer = this.time.addEvent({
      delay: 28, loop: true, callback: () => {
        this.typed++;
        this.l1.setText(a.slice(0, this.typed));
        this.l2.setText(b.slice(0, Math.max(0, this.typed - a.length)));
        if (this.typed % 2 === 0) snd.sfx("type");
        if (this.typed >= a.length + b.length) this.endTyping();
      },
    });
  }

  endTyping() {
    this.typer?.remove(); this.typing = false;
    this.l1.setText(this.full[0]); this.l2.setText(this.full[1]); this.more.setVisible(true);
  }

  advance() {
    if (this.done) return;
    if (this.typing) return this.endTyping();
    if (this.card) return this.clockIn();
    this.idx += 2;
    if (this.idx < this.lines.length) return this.say();
    this.showCard();
  }

  showCard() {
    snd.sfx("stamp");
    const c = this.add.container(100, -100).setDepth(50);
    c.add(this.add.image(0, 0, "ui_job_card").setOrigin(0));
    c.add(txt(this, 32, 23, t(this.act2 ? "place2" : "place"), { size: 9, color: C.ink, shadow: false }));
    c.add(txt(this, 32, 37, t("wageLine", MULT[S.run.act || 1], hourly(S.run.act || 1)), { size: 9, color: C.ink, shadow: false }));
    c.add(txt(this, 13, 60, t("rule_" + this.newRule), { size: 9, color: C.red2, shadow: false, wrap: 94 }));
    this.card = c;
    this.tweens.add({ targets: c, y: 26, duration: 380, ease: "Back.easeOut" });
    this.l1.setText(t("rulePre") + t("rule_" + this.newRule));
    this.l1.setColor(C.red);
    this.l2.setText(t("quotaLine", won((this.act2 ? dQuotaFor : quotaFor)(S.run.shift))) + "   [ " + t("go") + " ]"); this.more.setVisible(false);
    this.tweens.add({ targets: this.l2, alpha: 0.3, duration: 400, yoyo: true, repeat: -1 });
    this.guard = this.time.now + 350;
  }

  clockIn() {
    if (this.time.now < this.guard) return;
    this.done = true;
    snd.sfx("start");
    this.cameras.main.fadeOut(250, 20, 16, 26);
    this.time.delayedCall(280, () => this.scene.start(this.act2 ? "Delivery" : "Shift"));
  }
}

import Phaser from "phaser";
import { W, H, C, txt, soundToggle, enCard } from "../ui.js";
import { S, t, won, newRuleFor, MULT, hourly, GIG, saveRun, hasStr } from "../state.js";
import { quotaFor } from "./Shift.js";
import { dQuotaFor } from "./Delivery.js";
import { eQuotaFor } from "./Event.js";
import { cQuotaFor } from "./Cinema.js";
import { wQuotaFor } from "./Ward.js";
import { sQuotaFor } from "./Site.js";
const QUOTA = { 1: quotaFor, 2: eQuotaFor, 3: dQuotaFor, 4: cQuotaFor, 5: wQuotaFor, 6: sQuotaFor, 7: () => 0 };
import * as snd from "../audio.js";
import { setActionLabel, showPad } from "../touchpad.js";

// Briefing: the manager talks, then hands over tonight's job card.
export default class Agency extends Phaser.Scene {
  constructor() { super("Agency"); }

  create(data) {
    setActionLabel(""); showPad(false);
    const run = S.run;
    saveRun(run);
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
    this.gig = GIG[run.act || 1];
    const brief = this.gig.briefs[run.shift] || "same";
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

  /** Split a rule for the job card: a short first line beside the badge, then one full-width line.
   *  Long rules use their card wording (rcard_*). Returns [first, second, fits]. */
  ruleLines(rule) {
    const s = t(hasStr("rcard_" + rule) ? "rcard_" + rule : "rule_" + rule);
    const words = s.split(" "), badge = S.lang === "ko" ? 24 : 26;
    const probe = txt(this, 0, 0, "", { size: 9, shadow: false });
    let first = "";
    while (words.length) { probe.setText(first ? first + " " + words[0] : words[0]); if (probe.width > 96 - badge && first) break; first = probe.text; words.shift(); }
    probe.setText(first); const w1 = probe.width;
    const second = words.join(" "); probe.setText(second); const w2 = probe.width;
    probe.destroy();
    return [first, second, w1 <= 96 - badge && w2 <= 96];
  }

  showCard() {
    snd.sfx("stamp");
    const c = this.add.container(100, -100).setDepth(50);
    c.add(this.add.image(0, 0, "ui_job_card").setOrigin(0));
    enCard(this, c);
    c.add(txt(this, 32, 23, t(this.gig.place), { size: 9, color: C.ink, shadow: false }));
    c.add(txt(this, 32, 37, (S.run.act === 7 ? t("wageAll") : t("wageLine", MULT[S.run.act || 1], hourly(S.run.act || 1))), { size: 9, color: C.ink, shadow: false }));
    // below the RULE badge, two tight lines inside the red box
    // the first line starts beside the RULE badge, so two lines fit inside the red box
    const [l1, l2] = this.ruleLines(this.newRule);
    c.add(txt(this, 13 + (S.lang === "ko" ? 24 : 26), 57, l1, { size: 9, color: C.red2, shadow: false }));
    if (l2) c.add(txt(this, 13, 68, l2, { size: 9, color: C.red2, shadow: false }));
    this.card = c;
    this.tweens.add({ targets: c, y: 26, duration: 380, ease: "Back.easeOut" });
    this.l1.setText(t("rulePre") + t("rule_" + this.newRule));
    // a long rule drops to the small font so it stays inside the box
    if (this.l1.width > 216) this.l1.setFontFamily("Galmuri9").setFontSize("10px");
    this.l1.setColor(C.red);
    this.l2.setText((S.run.act === 7 ? t("lastNight") : t("quotaLine", won(QUOTA[S.run.act || 1](S.run.shift)))) + "   [ " + t("go") + " ]"); this.more.setVisible(false);
    this.tweens.add({ targets: this.l2, alpha: 0.3, duration: 400, yoyo: true, repeat: -1 });
    this.guard = this.time.now + 350;
  }

  clockIn() {
    if (this.time.now < this.guard) return;
    this.done = true;
    snd.sfx("start");
    this.cameras.main.fadeOut(250, 20, 16, 26);
    this.time.delayedCall(280, () => this.scene.start(this.gig.scene));
  }
}

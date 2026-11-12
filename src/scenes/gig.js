// Shared by the side-view gigs (event, delivery): HUD, teaching hints, pay, and how a shift ends.
// A scene using it sets this.clockBase (minutes past midnight at 00 of the shift) and may define
// clockHot() (clock turns orange) and tickSlip() (update the top-left slip).
import Phaser from "phaser";
import { W, H, BAR, C, txt, soundToggle } from "../ui.js";
import { S, t, won, START_DEBT, recordBest, markSeen, hourly, clearAct, saveNote } from "../state.js";
import * as snd from "../audio.js";
import { cancelReplay } from "../replay.js";

export const GigMixin = {
  /** The Regular's note for this act: lies somewhere on the second night until you walk over it. */
  initNote(x, place = null) {
    const act = this.run.act;
    if (this.run.shift !== 2 || S.notes[act] || this.run.daily) return;
    const spr = this.add.image(x, 146, "props_note").setDepth(98);
    this.tweens.add({ targets: spr, y: 143, duration: 600, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    this.note = { spr, place, act, got: false };
  },

  tickNote() {
    const n = this.note;
    if (!n || n.got) return;
    const here = !n.place || this.place === n.place;
    n.spr.setVisible(here);
    if (here && Math.abs(this.p.x - n.spr.x) < 10) {
      n.got = true; n.spr.destroy(); saveNote(n.act);
      snd.sfx("coin"); this.caption(t("note" + n.act), 4);
    }
  },

  /** A line of story text across the top of the play area. */
  caption(line, secs = 4) {
    const c = txt(this, W / 2, 40, line, { ox: 0.5, size: 9, color: C.white, depth: 960, wrap: W - 40 });
    c.setBackgroundColor("#14101a").setPadding(4, 2, 4, 2);
    this.tweens.add({ targets: c, alpha: 0, delay: secs * 1000, duration: 500, onComplete: () => c.destroy() });
    return c;
  },

  hint(key, x, y) {
    const pre = this.hintPre || "";
    if (S.seen[pre + key] || this.hints[key]) return;
    this.hintsShown.add(pre + key);
    const h = txt(this, x, y, t("hint_" + key), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    h.setBackgroundColor("#14101a").setPadding(2, 1, 2, 1);
    this.tweens.add({ targets: h, alpha: 0.4, duration: 300, yoyo: true, repeat: -1 });
    this.hints[key] = h;
  },
  unhint(key) { if (this.hints[key]) { this.hints[key].destroy(); this.hints[key] = null; } },
  clearHints() { Object.keys(this.hints).forEach(k => this.unhint(k)); },

  strike(x, msg = t("wrongFlat")) {
    this.strikes++;
    snd.sfx("strike"); this.cameras.main.shake(120, 0.005);
    this.pop(msg, x, 66, C.red);
    this.strikeIcons.forEach((ic, k) => ic.setAlpha(k < this.strikes ? 1 : 0.18));
    if (this.strikes >= 3) this.fired("fired");
  },

  earn(n, x, y, pre = "") {
    this.pay += n; this.drawMoney();
    this.pop(pre + "+" + won(n), x, y, C.yellow);
  },

  pop(s, x, y, color) {
    const p = txt(this, x, y, s, { ox: 0.5, size: 9, color, depth: 630 });
    p.setBackgroundColor("#14101a").setPadding(2, 1, 2, 1);
    this.tweens.add({ targets: p, y: y - 12, alpha: 0, delay: 500, duration: 700, onComplete: () => p.destroy() });
  },

  buildHud() {
    this.add.image(0, 0, "ui_rule_banner").setOrigin(0).setDepth(900);
    this.ruleIcon = this.add.image(43, 11, "props_icons", "rule").setDepth(910);
    this.ruleTxt = txt(this, 60, 5, "", { color: C.yellow, depth: 910 });
    this.add.image(0, H - BAR, "ui_hud_bottom").setOrigin(0).setDepth(900);
    this.hudClock = txt(this, 64, H - BAR + 6, "", { size: 9, ox: 0.5, depth: 910 });
    this.hudPay = txt(this, 129, H - BAR + 6, "", { size: 9, color: C.yellow, depth: 910 });
    this.debtFill = this.add.image(226, H - BAR + 9, "ui_debt_meter_fill").setOrigin(0).setDepth(910);
    this.quotaBar = this.add.graphics().setDepth(911);
    this.strikeIcons = [0, 1, 2].map(i => this.add.image(W - 11 - i * 13, BAR + 9, "props_icons", "cross").setDepth(890).setAlpha(0.18));
    this.slip = txt(this, 6, BAR + 4, "", { size: 9, color: C.ink, shadow: false, depth: 890 });
    this.slip.setBackgroundColor("#f6f1e7").setPadding(3, 1, 3, 1);
    soundToggle(this);
    this.ruleIdx = 0; this.ruleT = 0; this.ruleShown = null; this.blink = 0;
    this.drawMoney();
  },

  drawMoney() {
    this.hudPay.setText(won(this.run.earned + this.pay));
    const q = Phaser.Math.Clamp(this.pay / this.quota, 0, 1);
    this.quotaBar.clear().fillStyle(0x2a2233).fillRect(127, H - BAR + 17, 56, 2)
      .fillStyle(q >= 1 ? 0x7fc77a : 0xffd42a).fillRect(127, H - BAR + 17, Math.round(56 * q), 2);
    this.hudPay.setColor(q >= 1 ? C.green : C.yellow);
    const f = Phaser.Math.Clamp((this.run.debt - this.pay) / START_DEBT, 0, 1);
    this.debtFill.setCrop(0, 0, Math.round(60 * f), 4);
  },

  tickHud(dt) {
    if (!this.over) this.tickNote();
    this.blink += dt;
    const on = Math.floor(this.blink * 6) % 2 === 0;
    const hot = this.hotRule();
    if (!hot) { this.ruleT += dt; if (this.ruleT > 3.5) { this.ruleT = 0; this.ruleIdx = (this.ruleIdx + 1) % this.rules.length; } }
    const rule = hot || this.rules[this.ruleIdx];
    const sig = rule + (hot ? "!" : "");
    if (sig !== this.ruleShown) {
      this.ruleShown = sig;
      this.ruleTxt.setText(t("rulePre") + t("rule_" + rule)).setColor(hot ? C.red : C.yellow);
      this.ruleIcon.setFrame(hot ? "warning" : "rule");
    }
    this.ruleTxt.setAlpha(hot && !on ? 0.35 : 1);
    const m = Math.min(this.min, 60), tot = this.clockBase + m;
    this.hudClock.setText(`${String(Math.floor(tot / 60) % 24).padStart(2, "0")}:${String(tot % 60).padStart(2, "0")}`)
      .setColor(this.clockHot?.() ? C.orange : C.white);
    this.tickSlip?.();
  },

  bank(extra = 0) {
    const run = this.run, total = this.pay + extra;
    run.earned += total; run.debt = Math.max(0, run.debt - total);
    this.pay = 0;
  },

  freeze() {
    this.endBossFx?.();
    this.over = true; this.busy = true;
    snd.music("off"); snd.ambience(false);
    this.workBar.clear(); this.clearHints(); this.flick.setAlpha(0);
  },

  stamp(key) {
    this.add.rectangle(W / 2, H / 2, 164, 72, 0xf6f1e7).setStrokeStyle(1, 0x14101a).setDepth(955);
    const s = this.add.image(W / 2, H / 2, key).setDepth(960).setScale(3).setAlpha(0);
    this.tweens.add({ targets: s, scale: 2, alpha: 1, duration: 140, ease: "Quad.easeIn", onComplete: () => { snd.sfx("stamp"); this.cameras.main.shake(140, 0.008); } });
  },

  fired(cause = "fired") {
    if (this.over) return;
    cancelReplay();
    this.freeze(); this.bank(); recordBest();
    this.flick.setAlpha(0.45);
    snd.jingle("gameover");
    this.time.delayedCall(350, () => this.stamp("ui_stamp_fired"));
    if (cause === "quota") {
      const m = txt(this, W / 2, H / 2 + 40, t("cause_quota"), { ox: 0.5, color: C.red, depth: 960 });
      m.setAlpha(0); this.tweens.add({ targets: m, alpha: 1, delay: 500, duration: 200 });
    }
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => this.scene.start("Result", { cause }));
  },

  clockOut() {
    if (this.over) return;
    if (this.pay < this.quota && !this.bossDone) return this.fired("quota");
    markSeen([...this.hintsShown]);
    cancelReplay();
    this.freeze();
    const bonus = hourly(this.run.act);      // one hour at the gig's minimum-wage multiple
    this.bank(bonus);
    this.run.cleared++; this.run.shift++; recordBest();
    this.drawMoney();
    this.flick.setAlpha(0.35);
    snd.jingle("clockout");
    this.stamp("ui_stamp_success");
    const b = txt(this, W / 2, H / 2 + 40, `${t("wagePaid")} +${won(bonus)}`, { ox: 0.5, color: C.yellow, depth: 960 });
    b.setAlpha(0); this.tweens.add({ targets: b, alpha: 1, delay: 300, duration: 200 });
    this.p.setVisible(true); this.p.anims.stop(); this.p.setFrame("face_smile");
    const win = this.run.debt <= 0;
    // until this gig's boss is built, surviving its third night clears the act
    const act = this.run.act, actDone = this.run.shift === 4 && !S.acts[act];
    if (actDone) clearAct(act, this.run);
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => win ? this.scene.start("Result", { cause: "win" })
      : actDone ? this.scene.start("Board", { context: "clear", act }) : this.scene.start("Agency", { context: "next" }));
  },
};

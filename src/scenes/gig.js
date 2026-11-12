// Shared by the side-view gigs (event, delivery): HUD, teaching hints, pay, and how a shift ends.
// A scene using it sets this.clockBase (minutes past midnight at 00 of the shift) and may define
// clockHot() (clock turns orange) and tickSlip() (update the top-left slip).
import Phaser from "phaser";
import { W, H, BAR, C, txt, soundToggle, enHud, stampKey, artKey } from "../ui.js";
import { S, t, won, START_DEBT, recordBest, markSeen, hourly, clearAct, saveNote } from "../state.js";
import * as snd from "../audio.js";
import { cancelReplay } from "../replay.js";
import { setActionLabel, showPad } from "../touchpad.js";
import { DreadMixin } from "./dread.js";

export const GigMixin = {
  ...DreadMixin,
  /** Phaser reuses scene objects: clear everything a previous night left on `this`. */
  resetGig() {
    showPad(true);
    this.boss = null; this.bossDone = false; this.note = null; this.meterState = null; this.meterEnd = null;
    this.talking = false; this.riding = null; this.chosen = null; this.choosing = false; this.opened = false;
    this.working = null; this.carry = false; this.order = null; this.floatWrong = false; this.moving = false;
    this.dread = null; this.capObj = null;
  },

  /** Tell the on-screen A button what it would do here. */
  padLabel() {
    let k = null;
    if (this.meterState) k = this.meterState.mode === "hold" ? "hold" : "tap";
    else if (this.riding) k = "hop";
    else if (this.bossActive?.()) k = "boss";
    else if (!this.over && !this.talking && this.spots) {
      const s = this.spots().find(([x, r]) => Math.abs(this.p.x - x) <= r);
      if (s) k = s[2].replace(/[0-9]/g, "");
    }
    setActionLabel(k ? t("pad_" + k) : "");
  },

  /**
   * A small skill check above Sora's head.
   *   mode "hold": the bar fills while Space / A / a finger is held; let go inside the zone.
   *   mode "tap":  a marker swings back and forth; press while it's inside the zone, `presses` times.
   * Walking away cancels it. done(true | false | null) - null means cancelled.
   */
  meter({ mode = "tap", zone = [0.4, 0.6], speed = 1.2, presses = 1, label = "", done }) {
    this.meterEnd?.(null);
    const D = 625, x0 = Math.round(this.p.x) - 22, y0 = 92;
    const g = this.add.graphics().setDepth(D);
    const lab = txt(this, x0 + 22, y0 - 14, label, { ox: 0.5, size: 9, color: C.yellow, depth: D + 1 }).setBackgroundColor("#14101a").setPadding(2, 0, 2, 0);
    const m = this.meterState = { mode, zone, speed, presses, hits: 0, v: 0, dir: 1, held: mode === "hold", g, lab, done, flash: 0, flashC: 0 };
    const draw = () => {
      g.clear().fillStyle(0x14101a).fillRect(x0 - 1, y0 - 1, 46, 7).fillStyle(0x4a4458).fillRect(x0, y0, 44, 5)
        .fillStyle(0x7fc77a).fillRect(x0 + Math.round(44 * zone[0]), y0, Math.round(44 * (zone[1] - zone[0])), 5);
      if (mode === "hold") g.fillStyle(0xffd42a).fillRect(x0, y0 + 1, Math.round(44 * Math.min(1, m.v)), 3);
      else g.fillStyle(0xf6f1e7).fillRect(x0 + Math.round(43 * m.v), y0 - 2, 2, 9);
      for (let i = 0; i < presses && presses > 1; i++) g.fillStyle(i < m.hits ? 0x7fc77a : 0x4a4458).fillRect(x0 + 16 + i * 5, y0 + 8, 3, 3);
      if (m.flash > 0) g.lineStyle(1, m.flashC).strokeRect(x0 - 2, y0 - 2, 48, 9);
    };
    m.draw = draw;
    this.meterEnd = res => {
      if (!this.meterState) return;
      g.destroy(); lab.destroy(); this.meterState = null; this.meterEnd = null;
      if (res !== null) done?.(res);
    };
    draw();
  },

  /** Space / A / tap while a meter is up. Returns true if it took the press. */
  meterPress() {
    const m = this.meterState;
    if (!m) return false;
    if (m.mode === "hold") return true;          // holding is handled in meterTick
    const ok = m.v >= m.zone[0] && m.v <= m.zone[1];
    m.flash = 0.2; m.flashC = ok ? 0x7fc77a : 0xef3b4a;
    if (ok) { m.hits++; snd.sfx("tick"); if (m.hits >= m.presses) { this.meterEnd(true); return true; } }
    else { snd.sfx("strike"); if (m.presses === 1) { this.meterEnd(false); return true; } }
    return true;
  },

  meterTick(dt) {
    const m = this.meterState;
    if (!m) return;
    const k = this.keys;
    if ((k.LEFT && k.LEFT.isDown) || (k.RIGHT && k.RIGHT.isDown) || (k.A && k.A.isDown) || (k.D && k.D.isDown)) return this.meterEnd(null);
    m.flash -= dt;
    if (m.mode === "hold") {
      const space = this.spaceKey?.isDown;
      const holding = space || this.input.activePointer.isDown;
      if (holding) { m.v += m.speed * dt; if (Math.floor(m.v * 10) !== Math.floor((m.v - m.speed * dt) * 10)) snd.sfx("tick"); }
      if (m.v > 1.12) return this.meterEnd(false);
      if (!holding && m.v > 0.04) return this.meterEnd(m.v >= m.zone[0] && m.v <= m.zone[1]);
    } else {
      m.v += m.dir * m.speed * dt;
      if (m.v >= 1) { m.v = 1; m.dir = -1; } else if (m.v <= 0) { m.v = 0; m.dir = 1; }
    }
    m.draw();
  },

  /**
   * A short scene: portrait, speaker, typed line, one line per press. Gameplay pauses until it ends.
   * key names a list of [who, face, text] in the strings table.
   */
  talk(key, done, closeup) {
    const lines = t(key);
    this.talking = true; this.target = null; this.intent = null;
    const D = 940;
    const shade = this.add.rectangle(0, BAR, W, H - 2 * BAR, 0x14101a, 0.35).setOrigin(0).setDepth(D).setScrollFactor(0);
    // a big close-up behind the dialogue for the moments that matter
    const cu = closeup && this.textures.exists(closeup)
      ? this.add.image(0, 0, artKey(closeup)).setOrigin(0).setDepth(D).setScrollFactor(0).setAlpha(0) : null;
    if (cu) this.tweens.add({ targets: cu, alpha: 1, duration: 400 });
    const pic = this.add.image(12, 106, "portraits_sora", "neutral").setOrigin(0).setDepth(D + 2).setScrollFactor(0).setCrop(2, 10, 60, 36);
    const box = this.add.image(10, 112, "ui_dialog_box").setOrigin(0).setDepth(D + 1).setScrollFactor(0);
    const name = txt(this, 80, 116, "", { size: 9, color: C.yellow, depth: D + 3 }).setScrollFactor(0);
    const body = txt(this, 80, 129, "", { size: 9, color: C.white, depth: D + 3, wrap: 222 }).setScrollFactor(0);
    const more = txt(this, 298, 142, "▼", { size: 9, color: C.grey, depth: D + 3 }).setScrollFactor(0);
    this.tweens.add({ targets: more, y: 144, duration: 300, yoyo: true, repeat: -1 });
    let i = 0, typing = null, full = "", guard = 0;
    const show = () => {
      const [who, face, text] = lines[i++];
      const tex = "portraits_" + who;
      if (this.textures.exists(tex)) pic.setTexture(tex, this.textures.get(tex).has(face) ? face : undefined).setVisible(true).setCrop(2, 10, 60, 36);
      else pic.setVisible(false);
      name.setText(t("who_" + who)); full = text; body.setText("");
      let n = 0;
      typing?.remove();
      typing = this.time.addEvent({ delay: 26, loop: true, callback: () => {
        n++; body.setText(full.slice(0, n)); if (n % 2 === 0) snd.sfx("type");
        if (n >= full.length) { typing.remove(); typing = null; }
      } });
    };
    const adv = () => {
      if (this.time.now < guard) return;
      guard = this.time.now + 180;
      snd.init();
      if (typing) { typing.remove(); typing = null; body.setText(full); return; }
      if (i < lines.length) return show();
      kb.off("keydown-SPACE", adv); kb.off("keydown-ENTER", adv); kb.off("keydown-Z", adv); this.input.off("pointerdown", adv);
      [shade, pic, box, name, body, more, cu].forEach(o => o?.destroy());
      this.talking = false;
      done?.();
    };
    const kb = this.input.keyboard;
    this.time.delayedCall(250, () => { kb.on("keydown-SPACE", adv); kb.on("keydown-ENTER", adv); kb.on("keydown-Z", adv); this.input.on("pointerdown", adv); });
    show();
  },

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
    this.tweens.add({ targets: c, alpha: 0, delay: secs * 1000, duration: 500, onComplete: () => { c.destroy(); if (this.capObj === c) this.capObj = null; } });
    this.capObj = c;
    return c;
  },

  hint(key, x, y) {
    const pre = this.hintPre || "";
    if (S.seen[pre + key] || this.hints[key]) return;
    this.hintsShown.add(pre + key);
    const h = txt(this, x, y, t("hint_" + key), { ox: 0.5, size: 9, color: C.yellow, depth: 630 });
    h.setBackgroundColor("#14101a").setPadding(2, 1, 2, 1);
    h.setX(Phaser.Math.Clamp(x, h.width / 2 + 2, W - h.width / 2 - 2));   // keep it on screen
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
    p.setX(Phaser.Math.Clamp(x, p.width / 2 + 2, W - p.width / 2 - 2));
    this.tweens.add({ targets: p, y: y - 12, alpha: 0, delay: 500, duration: 700, onComplete: () => p.destroy() });
  },

  buildHud() {
    this.spaceKey = this.input.keyboard.addKey("SPACE", false);   // the skill-check meter reads whether it is held
    this.add.image(0, 0, "ui_rule_banner").setOrigin(0).setDepth(900);
    this.ruleIcon = this.add.image(43, 11, "props_icons", "rule").setDepth(910);
    this.ruleTxt = txt(this, 60, 5, "", { color: C.yellow, depth: 910 });
    this.add.image(0, H - BAR, "ui_hud_bottom").setOrigin(0).setDepth(900);
    enHud(this);
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
    if (!this.over) this.meterTick(dt);
    this.padLabel();
    if (!this.over) this.tickNote();
    this.tickDread(dt);
    // a teaching hint under a caption waits for the caption to go
    const cap = this.capObj?.active ? this.capObj.getBounds() : null;
    for (const h of Object.values(this.hints)) if (h?.active) h.setVisible(!cap || !Phaser.Geom.Intersects.RectangleToRectangle(cap, h.getBounds()));
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
    const s = this.add.image(W / 2, H / 2, stampKey(key)).setDepth(960).setScale(3).setAlpha(0);
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
    const win = this.run.debt <= 0 && !this.run.act;     // in the story the finale decides how it ends
    // until this gig's boss is built, surviving its third night clears the act
    const act = this.run.act, actDone = this.run.shift === 4 && !S.acts[act];
    if (actDone) clearAct(act, this.run);
    this.time.delayedCall(2100, () => this.cameras.main.fadeOut(300, 20, 16, 26));
    this.time.delayedCall(2450, () => win ? this.scene.start("Result", { cause: "win" })
      : actDone ? this.scene.start("Board", { context: "clear", act }) : this.scene.start("Agency", { context: "next" }));
  },
};

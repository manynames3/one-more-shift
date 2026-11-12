import Phaser from "phaser";
import { W, H, BAR, C, txt, button } from "../ui.js";
import { S, t, won, MULT, hourly, GIG, ACTS } from "../state.js";
import * as snd from "../audio.js";
import { setActionLabel } from "../touchpad.js";

// How every new gig starts: the job lands on Sora's phone. Accept, and the next screen is the place
// itself (a title card with her walking in), then the briefing.
//   data.act   which gig
//   data.next  { scene, data } to go to after the title card
export default class Offer extends Phaser.Scene {
  constructor() { super("Offer"); }

  create(data) {
    setActionLabel("");
    this.act = data.act; this.next = data.next;
    const a = ACTS[this.act - 1];
    this.cameras.main.fadeIn(400, 20, 16, 26);
    snd.music("office"); snd.ambience(false);
    if (this.textures.exists("cu_sora_phone")) this.add.image(0, 0, "cu_sora_phone").setOrigin(0);
    else this.add.image(0, 0, "bg_street_night").setOrigin(0);
    this.add.rectangle(0, 0, W, BAR, 0x14101a).setOrigin(0);
    this.add.rectangle(0, H - BAR, W, BAR, 0x14101a).setOrigin(0);

    // the phone, slid up from the bottom right
    const P = this.add.container(214, H + 10);
    const g = this.add.graphics();
    g.fillStyle(0x14101a).fillRoundedRect(-1, -1, 92, 132, 9)
      .fillStyle(0x4a4458).fillRoundedRect(0, 0, 90, 130, 8)
      .fillStyle(0xf6f1e7).fillRect(5, 12, 80, 104)
      .fillStyle(0x2a2233).fillRect(5, 12, 80, 13)
      .fillStyle(0x7b7689).fillRect(38, 5, 14, 2).fillCircle(45, 123, 3);
    P.add(g);
    P.add(txt(this, 45, 13, t("appName"), { ox: 0.5, size: 9, color: C.yellow, shadow: false }));
    P.add(txt(this, 45, 28, t("newJob"), { ox: 0.5, size: 9, color: C.red2, shadow: false }));
    P.add(this.add.sprite(45, 52, "props_coin_spin", "coin_0").setScale(2).play("props_coin_spin_coin"));
    const m = MULT[this.act];
    P.add(txt(this, 45, 68, t("job_" + a.key), { ox: 0.5, color: C.ink, shadow: false }));
    P.add(txt(this, 45, 82, m ? t("offerPay", m, won(hourly(this.act))) : t("wageAll"), { ox: 0.5, size: 9, color: C.ink, shadow: false, wrap: 76 }));
    P.add(txt(this, 45, 96, this.act === 7 ? t("offerOne") : t("offerNights"), { ox: 0.5, size: 9, color: C.dim, shadow: false }));
    this.phone = P;
    this.tweens.add({ targets: P, y: BAR + 8, duration: 600, ease: "Back.easeOut", onComplete: () => this.ready() });
    snd.sfx("ring");
    txt(this, 12, BAR + 8, t("offerLine", this.act), { size: 9, color: C.white, wrap: 180 }).setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
  }

  ready() {
    snd.sfx("task");
    this.accept = button(this, 259, BAR + 116, "ui_btn_primary", t("accept"), () => this.go(), 30);
    this.input.keyboard.once("keydown-SPACE", () => this.go());
    this.input.keyboard.once("keydown-ENTER", () => this.go());
  }

  go() {
    if (this.done) return;
    this.done = true;
    snd.sfx("start");
    this.cameras.main.fadeOut(350, 20, 16, 26);
    this.time.delayedCall(380, () => this.scene.start("TitleCard", { act: this.act, next: this.next }));
  }
}

/** The place, with Sora walking in, and the act's name in the lower third. */
export class TitleCard extends Phaser.Scene {
  constructor() { super("TitleCard"); }

  create(data) {
    setActionLabel("");
    const a = ACTS[data.act - 1];
    const key = "tc_" + { store: "store", event: "event", delivery: "milk", cinema: "cinema", trial: "trial", site: "site", park: "park" }[a.key];
    this.cameras.main.fadeIn(500, 20, 16, 26);
    snd.music("off"); snd.ambience(true);
    this.add.image(0, 0, this.textures.exists(key) ? key : "bg_street_night").setOrigin(0);
    this.add.rectangle(0, 0, W, BAR, 0x14101a).setOrigin(0);
    this.add.rectangle(0, H - BAR, W, BAR, 0x14101a).setOrigin(0);
    const sora = this.add.sprite(-20, H - BAR - 4, "characters_sora", "right_walk_0").setOrigin(0.5, 1).play("characters_sora_right_walk");
    this.tweens.add({ targets: sora, x: 120, duration: 2200, onComplete: () => { sora.anims.stop(); sora.setFrame("up_walk_0"); } });
    const n = txt(this, W - 14, H - BAR - 40, t("act", data.act), { ox: 1, size: 9, color: C.white }).setAlpha(0);
    const name = txt(this, W - 14, H - BAR - 28, t("job_" + a.key) + " · " + t(GIG[data.act].place), { ox: 1, color: C.yellow }).setAlpha(0);
    this.tweens.add({ targets: [n, name], alpha: 1, delay: 500, duration: 500 });
    snd.sfx("bell", 0.4);
    const go = () => {
      if (this.done) return;
      this.done = true;
      this.cameras.main.fadeOut(400, 20, 16, 26);
      this.time.delayedCall(430, () => this.scene.start(data.next.scene, data.next.data));
    };
    this.time.delayedCall(3600, go);
    this.time.delayedCall(700, () => {
      this.input.keyboard.once("keydown-SPACE", go); this.input.keyboard.once("keydown-ENTER", go); this.input.once("pointerdown", go);
    });
  }
}

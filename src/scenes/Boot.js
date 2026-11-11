import Phaser from "phaser";
import manifest from "../../public/assets/manifest.json";
import { W, H, C, txt } from "../ui.js";
import { t } from "../state.js";

// Only what the game uses is loaded; the rest of the pack stays on the server.
const USED = new Set([
  "bg_title_bg", "bg_agency_office", "bg_agency_desk_fg", "bg_store_day", "bg_store_wrong", 
  "bg_store_counter", "bg_store_counter_wrong", "bg_death_bg",
  "characters_sora", "characters_kwak", "characters_halmae", "characters_daeri", "characters_jisu",
  "characters_deokgu", "characters_regular",
  "portraits_kwak", "portraits_regular",
  "props_icons", "props_items", "props_exclaim", "props_red_eyes", "props_shadow_blob", "props_static_overlay",
  "props_coin_spin", "props_sweat",
  "ui_logo", "ui_dialog_box", "ui_job_card", "ui_rule_banner", "ui_hud_bottom", "ui_debt_meter_fill",
  "ui_btn_primary", "ui_btn_secondary", "ui_btn_danger", "ui_stamp_success", "ui_stamp_fail", "ui_stamp_fired",
  "ui_paystub", "ui_vignette_red", "ui_vignette_dark",
]);

export const CAST = ["sora", "kwak", "halmae", "daeri", "jisu", "deokgu", "regular"];

export default class Boot extends Phaser.Scene {
  constructor() { super("Boot"); }

  preload() {
    const label = txt(this, W / 2, 78, t("loading"), { ox: 0.5, color: C.grey });
    const bar = this.add.rectangle(W / 2 - 40, 98, 0, 4, 0xffd42a).setOrigin(0, 0.5);
    this.add.rectangle(W / 2, 98, 84, 8).setStrokeStyle(1, 0x7b7689);
    this.load.on("progress", p => { bar.width = Math.round(80 * p); });
    this.load.on("complete", () => label.destroy());

    this.load.setPath("assets/");
    manifest.images.filter(i => USED.has(i.key)).forEach(i => this.load.image(i.key, i.png));
    manifest.atlases.filter(a => USED.has(a.key)).forEach(a => this.load.atlas(a.key, a.png, a.json));
  }

  create() {
    const mk = (key, name, n, rate, repeat = -1) => {
      if (!this.textures.get(key).has(`${name}_0`)) return;
      this.anims.create({
        key: `${key}_${name}`, frameRate: rate, repeat,
        frames: Array.from({ length: n }, (_, i) => ({ key, frame: `${name}_${i}` })),
      });
    };
    CAST.forEach(c => {
      const key = "characters_" + c;
      mk(key, "down_idle", 2, 2); mk(key, "down_walk", 4, 8); mk(key, "left_walk", 4, 8);
      mk(key, "right_walk", 4, 8); mk(key, "up_walk", 4, 8); mk(key, "scared", 2, 12);
      mk(key, "work", 2, 5); mk(key, "left_work", 2, 5); mk(key, "right_work", 2, 5);
    });
    mk("props_exclaim", "exclaim", 2, 4);
    mk("props_coin_spin", "coin", 6, 10);
    mk("props_static_overlay", "static", 4, 14);
    this.scene.start("Title");
  }
}

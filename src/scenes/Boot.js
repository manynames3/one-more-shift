import Phaser from "phaser";
import manifest from "../../public/assets/manifest.json";
import { W, H, C, txt } from "../ui.js";
import { t } from "../state.js";

// Only what the game uses is loaded; the rest of the pack stays on the server.
const USED = new Set([
  "bg_title_bg", "bg_agency_office", "bg_agency_desk_fg", "bg_store_day", "bg_store_wrong", 
  "bg_store_counter", "bg_store_counter_wrong", "bg_death_bg",
  "boss_ratking", "boss_rat", "boss_fx", "boss_mop",
  "bg_backroom", "bg_street_night", "props_door_staff", "props_box_stack", "props_box_closed", "props_trash_bag",
  "characters_sora", "characters_kwak", "characters_halmae", "characters_daeri", "characters_jisu",
  "characters_deokgu", "characters_regular",
  "portraits_kwak", "portraits_regular", "portraits_sora",
  "props_icons", "props_items", "props_exclaim", "props_red_eyes", "props_shadow_blob", "props_static_overlay",
  "props_coin_spin", "props_sweat", "props_register", "props_cctv", "props_wet_floor_sign", "props_time_clock",
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
    // Act 2 (night delivery)
    [["bg_delivery_hub", "bg/delivery_hub.png"], ["bg_apt_hall", "bg/apt_hall.png"], ["bg_stairwell", "bg/stairwell.png"],
      ["props_moped", "props/moped.png"], ["props_moped_b", "props/moped_b.png"], ["props_delivery_bag", "props/delivery_bag.png"],
      ["props_apt_door_open", "props/apt_door_open.png"], ["props_elevator_open", "props/elevator_open.png"],
      // Act 2 (night event)
      ["bg_event_plaza", "bg/event_plaza.png"], ["props_balloon", "props/balloon.png"], ["props_balloon_b", "props/balloon_b.png"], ["props_water", "props/water.png"]]
      .forEach(([k, f]) => this.load.image(k, f));
    this.load.atlas("props_mascot", "props/mascot.png", "props/mascot.json");
    this.load.atlas("props_kid", "props/kid.png", "props/kid.json");
    this.load.atlas("props_suit_boss", "props/suit_boss.png", "props/suit_boss.json");
    this.load.atlas("props_resident", "props/resident.png", "props/resident.json");
    this.load.atlas("props_screen_film", "props/screen_film.png", "props/screen_film.json");
    this.load.atlas("props_usher", "props/usher.png", "props/usher.json");
    this.load.atlas("characters_junho", "characters/junho.png", "characters/junho.json");
    this.load.atlas("portraits_junho", "portraits/junho.png", "portraits/junho.json");
    ["float", "kwak_boss"].forEach(k => this.load.atlas("props_" + k, `props/${k}.png`, `props/${k}.json`));
    [["bg_park", "bg/park.png"], ["bg_ending_dawn", "bg/ending_dawn.png"], ["bg_ending_desk", "bg/ending_desk.png"], ["bg_ending_note", "bg/ending_note.png"],
      ["props_note", "props/note.png"]].forEach(([k, f]) => this.load.image(k, f));
    ["nurse", "nurse_notag", "subject", "pill", "foreman"].forEach(k => this.load.atlas("props_" + k, `props/${k}.png`, `props/${k}.json`));
    [["bg_ward", "bg/ward.png"], ["bg_site", "bg/site.png"], ["props_hoist_closed", "props/hoist_closed.png"], ["props_hoist_rider", "props/hoist_rider.png"],
      ["props_load", "props/load.png"], ["props_brick", "props/brick.png"]].forEach(([k, f]) => this.load.image(k, f));
    [["bg_cinema_lobby", "bg/cinema_lobby.png"], ["bg_cinema_hall", "bg/cinema_hall.png"], ["bg_cinema_booth", "bg/cinema_booth.png"],
      ["props_beam", "props/beam.png"], ["props_reel", "props/reel.png"]].forEach(([k, f]) => this.load.image(k, f));
    [["bg_stairwell_scissor", "bg/stairwell_scissor.png"], ["bg_roof", "bg/roof.png"], ["bg_milk_depot", "bg/milk_depot.png"],
      ["bg_officetel_hall", "bg/officetel_hall.png"], ["props_milk_carrier", "props/milk_carrier.png"],
      ["props_officetel_door_open", "props/officetel_door_open.png"]].forEach(([k, f]) => this.load.image(k, f));
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
    mk("boss_ratking", "idle", 2, 3); mk("boss_ratking", "stun", 2, 6); mk("boss_ratking", "die", 2, 4, 0);
    mk("boss_rat", "run", 2, 10); mk("boss_fx", "swing", 3, 18, 0); mk("boss_fx", "star", 2, 6);
    this.scene.start("Title");
  }
}

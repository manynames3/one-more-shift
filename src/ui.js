// Shared drawing helpers: pixel text, buttons, input shortcuts.
import { S, saveSettings } from "./state.js";
import * as snd from "./audio.js";

export const W = 320, H = 180, BAR = 22;
export const C = {
  ink: "#14101a", ink2: "#2a2233", white: "#f6f1e7", yellow: "#ffd42a", red: "#ef3b4a", red2: "#c8202f",
  grey: "#b3aebd", dim: "#7b7689", green: "#7fc77a", orange: "#f8b84a",
};

/** Pixel text. size 11 (body) or 9 (small). ox = origin x (0 left, .5 centre, 1 right). */
export function txt(scene, x, y, s, o = {}) {
  const small = o.size === 9;
  const style = {
    fontFamily: small ? "Galmuri9" : "Galmuri11", fontSize: small ? "10px" : "12px",
    color: o.color || C.white, padding: { top: 1, bottom: 1 },
  };
  if (o.wrap) style.wordWrap = { width: o.wrap, useAdvancedWrap: true };
  const tx = scene.add.text(x, y - 1, s, style).setOrigin(o.ox ?? 0, 0);
  if (o.shadow !== false) tx.setShadow(1, 1, o.shadow || C.ink, 0, false, true);
  if (o.depth !== undefined) tx.setDepth(o.depth);
  if (o.spacing) tx.setLineSpacing(o.spacing);
  return tx;
}

/** Sprite button with a text label. Returns the container. */
export function button(scene, x, y, key, label, fn, depth = 950) {
  const img = scene.add.image(0, 0, key, "normal").setOrigin(0.5);
  const tx = txt(scene, 0, -7, label, { ox: 0.5 });
  const c = scene.add.container(x, y, [img, tx]).setDepth(depth).setSize(72, 18).setInteractive({ useHandCursor: true });
  const base = tx.y;
  c.on("pointerover", () => img.setFrame("hover"));
  c.on("pointerout", () => { img.setFrame("normal"); tx.y = base; });
  c.on("pointerup", () => { img.setFrame("hover"); tx.y = base; });
  c.on("pointerdown", (p, lx, ly, ev) => { ev.stopPropagation(); img.setFrame("pressed"); tx.y = base + 1; snd.init(); snd.sfx("ui"); fn(); });
  c.label = tx;
  return c;
}

/** Call fn on Space / Enter / Z or any tap that no button swallowed. */
export function onAdvance(scene, fn) {
  const go = () => { snd.init(); fn(); };
  scene.input.keyboard.on("keydown-SPACE", go);
  scene.input.keyboard.on("keydown-ENTER", go);
  scene.input.keyboard.on("keydown-Z", go);
  scene.input.on("pointerdown", go);
}

/** Sound toggle icon, bottom-right of the lower bar. */
export function soundToggle(scene) {
  const ic = scene.add.image(W - 12, H - 11, "props_icons", S.muted ? "sound_off" : "sound_on").setDepth(960)
    .setInteractive({ useHandCursor: true });
  const flip = () => {
    S.muted = !S.muted; saveSettings(); snd.init(); snd.setMuted(S.muted);
    ic.setFrame(S.muted ? "sound_off" : "sound_on");
  };
  ic.on("pointerdown", (p, lx, ly, ev) => { ev.stopPropagation(); flip(); });
  scene.input.keyboard.on("keydown-M", flip);
  return ic;
}

export const rand = (a, b) => a + Math.random() * (b - a);
export const pick = arr => arr[Math.floor(Math.random() * arr.length)];

// The job card, pay stub and HUD bar have their labels painted in Korean. In English, paint over them.
const EN_STUB = [[62, 0xe9e2c8, "PLACE"], [82, 0xf6f1e7, "SHIFT"], [102, 0xe9e2c8, "WAGE"], [122, 0xfff3a8, "TOTAL"], [142, 0xe9e2c8, "CAUSE"], [162, 0xf6f1e7, "DEBT LEFT"]];
export function enStub(scene, c) {
  if (S.lang !== "en") return;
  c.add(scene.add.rectangle(9, 36, 64, 16, 0xf6f1e7).setOrigin(0));
  c.add(txt(scene, 10, 39, "WAGE SLIP", { color: C.ink, shadow: false }));
  EN_STUB.forEach(([y, col, s]) => { c.add(scene.add.rectangle(8, y - 2, 52, 14, col).setOrigin(0)); c.add(txt(scene, 10, y, s, { size: 9, color: "#4a4458", shadow: false })); });
}
export function enCard(scene, c) {
  if (S.lang !== "en") return;
  c.add(scene.add.rectangle(20, 3, 80, 16, 0x2f4a9c).setOrigin(0));
  c.add(txt(scene, 60, 6, "TONIGHT'S JOB", { ox: 0.5, size: 9, color: C.white }));
  c.add(scene.add.rectangle(5, 23, 25, 26, 0xf6f1e7).setOrigin(0));
  c.add(txt(scene, 6, 24, "AT", { size: 9, color: "#4a4458", shadow: false }));
  c.add(txt(scene, 6, 38, "PAY", { size: 9, color: "#4a4458", shadow: false }));
  c.add(scene.add.rectangle(10, 50, 23, 12, 0xc8202f).setOrigin(0).setStrokeStyle(1, 0x14101a));
  c.add(txt(scene, 21, 51, "RULE", { ox: 0.5, size: 9, color: C.white, shadow: false }));
}
export function enHud(scene) {
  if (S.lang !== "en") return;
  scene.add.rectangle(200, H - 22 + 4, 24, 14, 0x14101a).setOrigin(0).setDepth(905);
  txt(scene, 222, H - 22 + 6, "DEBT", { ox: 1, size: 9, color: C.red, depth: 906 });
}

/** English stamps: the painted ones say 퇴근 성공 / 해고 / 퇴근 실패. Made once at boot from the originals. */
const STAMP_EN = {
  ui_stamp_success: { text: "CLOCKED OUT", ink: "#3b8a5a", bg: "#f6f1e7", r: [6, 6, 60, 16], font: '10px "Galmuri9"' },
  ui_stamp_fail: { text: "FAILED", ink: "#c8202f", bg: "#f6f1e7", r: [6, 6, 60, 16], font: '12px "Galmuri11"' },
  ui_stamp_fired: { text: "FIRED", ink: "#f6f1e7", bg: "#c8202f", r: [5, 5, 62, 18], font: '12px "Galmuri11"' },
};
export function makeEnglishStamps(scene) {
  texMgr = scene.textures;
  for (const [key, o] of Object.entries(STAMP_EN)) {
    if (!scene.textures.exists(key) || scene.textures.exists(key + "_en")) continue;
    const src = scene.textures.get(key).getSourceImage();
    const cv = scene.textures.createCanvas(key + "_en", src.width, src.height), g = cv.getContext();
    g.imageSmoothingEnabled = false;
    g.drawImage(src, 0, 0);
    g.fillStyle = o.bg; g.fillRect(...o.r);
    // draw the words on a scratch canvas, then keep only solid pixels so the font stays crisp
    const tc = document.createElement("canvas"); tc.width = src.width; tc.height = src.height;
    const tg = tc.getContext("2d");
    tg.font = o.font; tg.textAlign = "center"; tg.textBaseline = "middle"; tg.fillStyle = o.ink;
    tg.fillText(o.text, Math.round(src.width / 2), Math.round(o.r[1] + o.r[3] / 2) + 1);
    const d = tg.getImageData(0, 0, tc.width, tc.height), a = d.data;
    for (let i = 3; i < a.length; i += 4) a[i] = a[i] >= 110 ? 255 : 0;
    tg.putImageData(d, 0, 0);
    g.drawImage(tc, 0, 0);
    cv.refresh();
  }
}
/** English versions of close-ups with words painted in: [x, y, w, h] to repaint, the sample point for its
 *  fill (or a colour), the English, its ink. A dark fill gets the cream outlined look of the original label. */
const ART_EN = {
  cu_sora_desk: [
    { r: [43, 112, 50, 11], fill: "#1c1724", text: "RULES 1-99", ink: "#fff3a8" },
    { r: [224, 143, 51, 11], fill: "#ffd42a", text: "KWAK", ink: "#14101a" },
  ],
  cu_kwak_offer: [
    { r: [55, 89, 36, 11], fill: [52, 92], text: "CONTRACT", ink: "#4a4458" },
    { r: [222, 139, 45, 11], fill: "#ffd42a", text: "KWAK", ink: "#14101a" },
  ],
};
function inkText(g, w, h, text, ink, font, cx, cy) {
  const tc = document.createElement("canvas"); tc.width = w; tc.height = h;
  const tg = tc.getContext("2d");
  tg.font = font; tg.textAlign = "center"; tg.textBaseline = "middle"; tg.fillStyle = ink;
  tg.fillText(text, cx, cy);
  const d = tg.getImageData(0, 0, w, h), a = d.data;
  for (let i = 3; i < a.length; i += 4) a[i] = a[i] >= 110 ? 255 : 0;
  tg.putImageData(d, 0, 0);
  g.drawImage(tc, 0, 0);
}
export function makeEnglishArt(scene) {
  for (const [key, patches] of Object.entries(ART_EN)) {
    if (!scene.textures.exists(key) || scene.textures.exists(key + "_en")) continue;
    const src = scene.textures.get(key).getSourceImage();
    const cv = scene.textures.createCanvas(key + "_en", src.width, src.height), g = cv.getContext();
    g.imageSmoothingEnabled = false; g.drawImage(src, 0, 0);
    for (const p of patches) {
      let fill = p.fill;
      if (Array.isArray(fill)) { const [r, gg, b] = g.getImageData(fill[0], fill[1], 1, 1).data; fill = `rgb(${r},${gg},${b})`; }
      g.fillStyle = fill; g.fillRect(...p.r);
      inkText(g, src.width, src.height, p.text, p.ink, '10px "Galmuri9"', p.r[0] + p.r[2] / 2, p.r[1] + p.r[3] / 2 + 1);
    }
    cv.refresh();
  }
}
/** A texture in the current language: its _en version when playing in English and one exists. */
export const artKey = key => (S.lang === "en" && texMgr?.exists(key + "_en") ? key + "_en" : key);

let texMgr = null;
/** The stamp texture for the current language. */
export const stampKey = key => (S.lang === "en" && texMgr?.exists(key + "_en") ? key + "_en" : key);

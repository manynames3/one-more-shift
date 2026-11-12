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

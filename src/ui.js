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

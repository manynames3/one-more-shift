// "Flashes: off" for players sensitive to strobing: camera flashes are dropped, shakes are softened,
// and the scenes that strobe use a steady dim instead. Saved per device.
import Phaser from "phaser";

export const CALM = { on: (() => { try { return localStorage.getItem("oms.calm") === "on"; } catch { return false; } })() };

export function setCalm(on) {
  CALM.on = on;
  try { localStorage.setItem("oms.calm", on ? "on" : "off"); } catch { /* private mode */ }
}

export function installCalm() {
  const Cam = Phaser.Cameras.Scene2D.Camera.prototype;
  const flash = Cam.flash, shake = Cam.shake;
  Cam.flash = function (...a) { return CALM.on ? this : flash.apply(this, a); };
  Cam.shake = function (dur, k = 0.05, ...rest) { return shake.call(this, dur, CALM.on ? k * 0.25 : k, ...rest); };
}

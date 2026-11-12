// On-screen controls for phones and tablets: a d-pad on the left and an action button on the right.
// They press the same keys the keyboard does (arrows and Space), so every scene works with them as-is.
// Tap-to-walk still works; this is for players who'd rather steer.
const KEYS = {
  left: { key: "ArrowLeft", code: "ArrowLeft", keyCode: 37 },
  right: { key: "ArrowRight", code: "ArrowRight", keyCode: 39 },
  up: { key: "ArrowUp", code: "ArrowUp", keyCode: 38 },
  down: { key: "ArrowDown", code: "ArrowDown", keyCode: 40 },
  act: { key: " ", code: "Space", keyCode: 32 },
};

function send(type, k) {
  const e = new KeyboardEvent(type, { key: k.key, code: k.code, bubbles: true, cancelable: true });
  // Phaser reads keyCode, which the event constructor won't set
  Object.defineProperty(e, "keyCode", { get: () => k.keyCode });
  Object.defineProperty(e, "which", { get: () => k.keyCode });
  window.dispatchEvent(e);
}

const CSS = `
#pad { position: fixed; inset: 0; pointer-events: none; z-index: 10; font: 14px "Galmuri11", monospace; }
#pad .b { position: absolute; pointer-events: auto; display: flex; align-items: center; justify-content: center;
  width: 50px; height: 50px; border-radius: 12px; color: #f6f1e7; background: rgba(42, 34, 51, .55);
  border: 2px solid rgba(246, 241, 231, .35); touch-action: none; -webkit-tap-highlight-color: transparent; }
#pad .b.on { background: rgba(255, 212, 42, .55); border-color: #ffd42a; color: #14101a; }
#pad .act { width: 72px; height: 72px; border-radius: 50%; font-size: 16px; }
#pad .hide { width: 30px; height: 30px; border-radius: 8px; font-size: 11px; opacity: .7; }
#pad.off .b:not(.hide) { display: none; }
#pad.menu .b { display: none; }
`;

let actBtn = null, lastLabel = "A", padEl = null, padWanted = true;
/** The pad only shows while playing; menus and story scenes are tap-to-advance. */
export function showPad(on) {
  padWanted = on;
  if (padEl) padEl.classList.toggle("menu", !on);
}
/** Pixels the pad needs at each side in landscape, so it never covers the game (0 when there's no pad). */
export function padGutters() {
  if (!padEl || padEl.classList.contains("off") || window.innerHeight >= window.innerWidth) return [0, 0];
  return [170, 96];
}
/** Show what the A button does right now (a short word), or "A". */
export function setActionLabel(s) {
  s = s || "A";
  if (!actBtn || s === lastLabel) return;
  lastLabel = s; actBtn.textContent = s;
  actBtn.style.fontSize = s.length > 3 ? "11px" : s.length > 1 ? "13px" : "16px";
}

export function initTouchpad() {
  const touch = window.matchMedia("(pointer: coarse)").matches || "ontouchstart" in window;
  if (!touch) return;
  const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
  const pad = document.createElement("div"); pad.id = "pad"; padEl = pad;
  if (!padWanted) pad.classList.add("menu");
  let off = false;
  try { off = localStorage.getItem("oms.pad") === "off"; } catch { /* private mode */ }
  if (off) pad.classList.add("off");
  const S = 52, L = "max(10px, env(safe-area-inset-left))", R = "max(12px, env(safe-area-inset-right))", B = "max(14px, env(safe-area-inset-bottom))";
  const btn = (name, label, css, cls = "") => {
    const el = document.createElement("div");
    el.className = "b " + cls; el.textContent = label; el.style.cssText = css;
    const k = KEYS[name];
    const down = ev => { ev.preventDefault(); el.setPointerCapture?.(ev.pointerId); el.classList.add("on"); send("keydown", k); };
    const up = ev => { ev.preventDefault(); if (!el.classList.contains("on")) return; el.classList.remove("on"); send("keyup", k); };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("lostpointercapture", up);
    pad.appendChild(el);
    return el;
  };
  // d-pad, bottom-left
  btn("left", "◀", `left:${L}; bottom:calc(${B} + ${S}px);`);
  btn("right", "▶", `left:calc(${L} + ${2 * S}px); bottom:calc(${B} + ${S}px);`);
  btn("up", "▲", `left:calc(${L} + ${S}px); bottom:calc(${B} + ${2 * S}px);`);
  btn("down", "▼", `left:calc(${L} + ${S}px); bottom:${B};`);
  // action, bottom-right
  actBtn = btn("act", "A", `right:${R}; bottom:calc(${B} + ${S / 2}px);`, "act");
  // the rotate tip would sit under the pad
  const rot = document.getElementById("rotate"); if (rot) { rot.style.bottom = "auto"; rot.style.top = "56px"; }
  // show / hide the pad
  const hide = document.createElement("div");
  hide.className = "b hide"; hide.textContent = off ? "🎮" : "×";
  hide.style.cssText = `right:${R}; top:max(10px, env(safe-area-inset-top));`;
  hide.addEventListener("pointerdown", ev => {
    ev.preventDefault();
    off = !off; pad.classList.toggle("off", off); hide.textContent = off ? "🎮" : "×";
    try { localStorage.setItem("oms.pad", off ? "off" : "on"); } catch { /* private mode */ }
    window.dispatchEvent(new Event("resize"));   // the game can use the freed space
  });
  pad.appendChild(hide);
  // pause, top left
  const pz = document.createElement("div");
  pz.className = "b hide pz"; pz.textContent = "II";
  pz.style.cssText = `left:${L}; top:max(10px, env(safe-area-inset-top));`;
  pz.addEventListener("pointerdown", ev => { ev.preventDefault(); send("keydown", { key: "p", code: "KeyP", keyCode: 80 }); });
  pad.appendChild(pz);
  document.body.appendChild(pad);
}

import Phaser from "phaser";
import { W, H } from "./ui.js";
import { S } from "./state.js";
import Boot from "./scenes/Boot.js";
import Title from "./scenes/Title.js";
import Agency from "./scenes/Agency.js";
import Shift from "./scenes/Shift.js";
import Result from "./scenes/Result.js";
import Board from "./scenes/Board.js";
import Delivery from "./scenes/Delivery.js";

async function start() {
  // Text is drawn with the pixel fonts, so they must be ready before the first scene.
  try {
    await Promise.all([document.fonts.load('12px "Galmuri11"', "가A"), document.fonts.load('10px "Galmuri9"', "가A")]);
  } catch { /* fall back to system font */ }

  const game = new Phaser.Game({
    type: Phaser.AUTO,
    parent: "game",
    width: W, height: H,
    backgroundColor: "#14101a",
    pixelArt: true, roundPixels: true, antialias: false,
    scale: { mode: Phaser.Scale.NONE, width: W, height: H },
    input: { activePointers: 2 },
    scene: [Boot, Title, Agency, Shift, Result, Board, Delivery],
  });

  // Largest scale that fits the window and lands on whole device pixels.
  const fit = () => {
    const dpr = window.devicePixelRatio || 1;
    const s = Math.max(1, Math.floor(Math.min(window.innerWidth / W, window.innerHeight / H) * dpr)) / dpr;
    game.scale.setZoom(s);
    game.scale.refresh();
  };
  fit();
  window.addEventListener("resize", fit);
  window.addEventListener("orientationchange", () => setTimeout(fit, 200));
  window.__game = game; window.__S = S;   // handy for debugging from the console
}
start();

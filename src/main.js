import Phaser from "phaser";
import { initTouchpad, padGutters } from "./touchpad.js";
import { FilmFX, applyFilm } from "./filmfx.js";
import { W, H } from "./ui.js";
import { S } from "./state.js";
import Boot from "./scenes/Boot.js";
import Title from "./scenes/Title.js";
import Agency from "./scenes/Agency.js";
import Shift from "./scenes/Shift.js";
import Result from "./scenes/Result.js";
import Board from "./scenes/Board.js";
import Delivery from "./scenes/Delivery.js";
import Event from "./scenes/Event.js";
import Cinema from "./scenes/Cinema.js";
import Ward from "./scenes/Ward.js";
import Site from "./scenes/Site.js";
import Park from "./scenes/Park.js";
import Ending from "./scenes/Ending.js";
import Offer, { TitleCard } from "./scenes/Offer.js";

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
    pipeline: { FilmFX },
    scene: [Boot, Title, Agency, Shift, Result, Board, Delivery, Event, Cinema, Ward, Site, Park, Ending, Offer, TitleCard],
  });

  // Largest scale that fits the window and lands on whole device pixels.
  const fit = () => {
    const dpr = window.devicePixelRatio || 1;
    // landscape phones: keep the game between the d-pad and the A button
    const [gl, gr] = padGutters();
    const el = document.getElementById("game");
    if (el) { el.style.paddingLeft = gl + "px"; el.style.paddingRight = gr + "px"; el.style.boxSizing = "border-box"; }
    const fitS = Math.min((window.innerWidth - gl - gr) / W, window.innerHeight / H);
    let s = Math.max(1, Math.floor(fitS * dpr)) / dpr;
    // narrow portrait phones: whole-pixel scaling leaves the game tiny, so fill the width instead
    if (window.innerHeight > window.innerWidth && s < fitS * 0.9) s = fitS;
    game.scale.setZoom(s);
    game.scale.refresh();
  };
  initTouchpad();
  fit();
  window.addEventListener("resize", fit);
  window.addEventListener("orientationchange", () => setTimeout(fit, 200));
  const rot = document.getElementById("rotate");
  if (rot) rot.textContent = S.lang === "ko" ? "화면을 가로로 돌리면 더 커집니다" : "Rotate your phone for a bigger view";
  applyFilm(game);
  window.__game = game; window.__S = S;   // handy for debugging from the console
}
start();

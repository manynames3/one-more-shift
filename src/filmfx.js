// A soft "broadcast" look over the whole game, to sit closer to an animated-on-TV pixel style:
// slight colour fringing (red and blue pulled apart by a pixel), a touch of softening, faint scanlines,
// lifted blacks and a gentle vignette. WebGL only; switch it off with F (remembered).
import Phaser from "phaser";

const FRAG = `
precision mediump float;
uniform sampler2D uMainSampler;
uniform vec2 uRes;
uniform float uOn;
varying vec2 outTexCoord;
void main() {
  vec2 uv = outTexCoord;
  vec4 c = texture2D(uMainSampler, uv);
  if (uOn < 0.5) { gl_FragColor = c; return; }
  vec2 px = 1.0 / uRes;
  // colour fringe: red from the left, blue from the right
  float r = texture2D(uMainSampler, uv - vec2(px.x, 0.0)).r;
  float b = texture2D(uMainSampler, uv + vec2(px.x, 0.0)).b;
  vec3 col = vec3(mix(c.r, r, 0.38), c.g, mix(c.b, b, 0.38));
  // softening
  vec3 n = (texture2D(uMainSampler, uv + vec2(px.x, 0.0)).rgb + texture2D(uMainSampler, uv - vec2(px.x, 0.0)).rgb
          + texture2D(uMainSampler, uv + vec2(0.0, px.y)).rgb + texture2D(uMainSampler, uv - vec2(0.0, px.y)).rgb) * 0.25;
  col = mix(col, n, 0.14);
  // faint scanlines, lifted blacks, warm-cool grade, vignette
  float line = mod(floor(uv.y * uRes.y), 2.0);
  col *= 1.0 - 0.05 * line;
  col = col * 0.94 + vec3(0.035, 0.028, 0.045);
  vec2 d = uv - 0.5;
  col *= 1.0 - 0.28 * dot(d, d);
  gl_FragColor = vec4(col, c.a);
}`;

export class FilmFX extends Phaser.Renderer.WebGL.Pipelines.PostFXPipeline {
  constructor(game) { super({ game, name: "FilmFX", fragShader: FRAG }); }
  onPreRender() {
    this.set2f("uRes", this.renderer.width, this.renderer.height);
    this.set1f("uOn", FilmFX.on ? 1 : 0);
  }
}
FilmFX.on = (() => { try { return localStorage.getItem("oms.film") !== "off"; } catch { return true; } })();

/** Put the filter on every scene's camera, and bind F to toggle it. */
export function applyFilm(game) {
  game.events.once(Phaser.Core.Events.READY, () => {
    if (game.renderer.type !== Phaser.WEBGL) return;
    game.scene.scenes.forEach(s => s.sys.events.on("create", () => {
    s.cameras.main.setPostPipeline(FilmFX);
    s.input.keyboard?.on("keydown-F", () => {
      FilmFX.on = !FilmFX.on;
      try { localStorage.setItem("oms.film", FilmFX.on ? "on" : "off"); } catch { /* private mode */ }
    });
    }));
  });
}

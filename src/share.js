import { S } from "./state.js";
// Renders the pay stub as a 720x960 PNG and shares or downloads it.
const SCALE = 4;

export function renderPayStub(scene, rows, stampKey) {
  const src = scene.textures.get("ui_paystub").getSourceImage();
  const stamp = scene.textures.get(stampKey).getSourceImage();
  const cv = document.createElement("canvas");
  cv.width = src.width * SCALE; cv.height = src.height * SCALE;
  const g = cv.getContext("2d");
  g.imageSmoothingEnabled = false;
  g.fillStyle = "#14101a"; g.fillRect(0, 0, cv.width, cv.height);
  g.drawImage(src, 0, 0, cv.width, cv.height);
  g.textBaseline = "top";
  // English: paint over the Korean labels baked into the stub
  if (S.lang === "en") {
    g.fillStyle = "#f6f1e7"; g.fillRect(9 * SCALE, 36 * SCALE, 64 * SCALE, 16 * SCALE);
    g.font = `${12 * SCALE}px "Galmuri11"`; g.fillStyle = "#14101a"; g.fillText("WAGE SLIP", 10 * SCALE, 38 * SCALE);
    [[62, "#e9e2c8", "PLACE"], [82, "#f6f1e7", "SHIFT"], [102, "#e9e2c8", "WAGE"], [122, "#fff3a8", "TOTAL"], [142, "#e9e2c8", "CAUSE"], [162, "#f6f1e7", "DEBT LEFT"]].forEach(([y, c, s]) => {
      g.fillStyle = c; g.fillRect(8 * SCALE, (y - 2) * SCALE, 52 * SCALE, 14 * SCALE);
      g.font = `${10 * SCALE}px "Galmuri9"`; g.fillStyle = "#4a4458"; g.fillText(s, 10 * SCALE, (y - 1) * SCALE);
    });
  }
  rows.forEach((v, i) => {
    const small = v.length > 13;
    g.font = small ? `${10 * SCALE}px "Galmuri9"` : `${12 * SCALE}px "Galmuri11"`;
    g.fillStyle = i === 4 || i === 5 ? "#c8202f" : "#14101a";
    g.fillText(v, 66 * SCALE, (61 + 20 * i) * SCALE);
  });
  g.fillStyle = "#f6f1e7"; g.fillRect(100 * SCALE, 179 * SCALE, 74 * SCALE, 28 * SCALE);
  g.drawImage(stamp, 100 * SCALE, 179 * SCALE, stamp.width * SCALE, stamp.height * SCALE);
  return cv;
}

function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

/** Share the pay stub (and the death replay GIF, if any). Returns "share" or "download". */
export async function sharePayStub(scene, rows, stampKey, text, gif = null) {
  const cv = renderPayStub(scene, rows, stampKey);
  const blob = await new Promise(res => cv.toBlob(res, "image/png"));
  const files = [new File([blob], "one-more-shift-paystub.png", { type: "image/png" })];
  if (gif) files.unshift(new File([gif], "one-more-shift-replay.gif", { type: "image/gif" }));
  const url = location.href.split("#")[0];
  const body = { text: `${text}\n${url}` };
  for (const set of [files, files.slice(-1)]) {          // some apps take only one file
    if (navigator.canShare && navigator.canShare({ files: set })) {
      try { await navigator.share({ ...body, files: set }); return "share"; }
      catch (e) { if (e.name === "AbortError") return "share"; }
    }
  }
  files.forEach((f, i) => setTimeout(() => download(f, f.name), i * 400));
  return "download";
}

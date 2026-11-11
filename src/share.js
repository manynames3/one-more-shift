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

/** Returns "share" when the system share sheet was used, "download" otherwise. */
export async function sharePayStub(scene, rows, stampKey, text) {
  const cv = renderPayStub(scene, rows, stampKey);
  const blob = await new Promise(res => cv.toBlob(res, "image/png"));
  const file = new File([blob], "one-more-shift-paystub.png", { type: "image/png" });
  const url = location.href.split("#")[0];
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try { await navigator.share({ files: [file], text: `${text}\n${url}` }); return "share"; }
    catch (e) { if (e.name === "AbortError") return "share"; }
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = file.name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  return "download";
}

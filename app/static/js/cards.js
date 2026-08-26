/* Visuel de carte canvas (§13) — mi-rappette du rendu serveur,
   mais calqué pour les exports (story, carré, paysage). */

const SIZES = {
  story: [1080, 1920],
  square: [1080, 1080],
  landscape: [1200, 630],
};
const MAX_CHARS = { story: 1400, square: 900, landscape: 420 };
const C = {
  ink: "#14110d",
  panel: "#1c1712",
  ivory: "#f0e6d0",
  gold: "#b08d3e",
  goldSoft: "#c8a663",
  muted: "#9a8767",
};

function spacingText(ctx, text, font, color, cx, cy, spacing) {
  ctx.save();
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textBaseline = "alphabetic";
  let total = 0;
  for (const ch of text) total += ctx.measureText(ch).width + spacing;
  let x = cx - (total - spacing) / 2;
  for (const ch of text) {
    ctx.fillText(ch, x, cy);
    x += ctx.measureText(ch).width + spacing;
  }
  ctx.restore();
}

function ornamentRow(ctx, cx, cy, halfLen, color) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - halfLen, cy);
  ctx.lineTo(cx - 16, cy);
  ctx.moveTo(cx + 16, cy);
  ctx.lineTo(cx + halfLen, cy);
  ctx.stroke();
  ctx.beginPath();
  const d = 6;
  ctx.moveTo(cx, cy - d);
  ctx.lineTo(cx + d, cy);
  ctx.lineTo(cx, cy + d);
  ctx.lineTo(cx - d, cy);
  ctx.closePath();
  ctx.stroke();
  ctx.restore();
}

function wrap(ctx, text, maxWidth) {
  const words = text.split(/\s+/);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const trial = cur ? cur + " " + w : w;
    if (ctx.measureText(trial).width <= maxWidth) cur = trial;
    else {
      if (cur) lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  return lines;
}

export function renderCard(canvas, entry, format = "story") {
  const [W, H] = SIZES[format] || SIZES.story;
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  const s = W / 1200;

  ctx.fillStyle = C.ink;
  ctx.fillRect(0, 0, W, H);

  // vignette douce
  const g = ctx.createRadialGradient(W / 2, H / 3, H / 8, W / 2, H / 3, H);
  g.addColorStop(0, "rgba(60,45,20,0.5)");
  g.addColorStop(1, "rgba(0,0,0,0.3)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  const margin = 45 * s;
  ctx.strokeStyle = C.gold;
  ctx.lineWidth = 3;
  ctx.strokeRect(margin, margin, W - 2 * margin, H - 2 * margin);
  ctx.lineWidth = 1;
  ctx.strokeRect(margin + 12, margin + 12, W - 2 * margin - 24, H - 2 * margin - 24);

  const innerW = W - 2 * margin - 60;
  ctx.textBaseline = "alphabetic";
  let y = margin + 46 * s;

  spacingText(ctx, "LE GRAND PHILOSOPHE", `700 ${26 * s}px Fraunces, Georgia, serif`,
              C.gold, W / 2, y, 6 * s);
  y += 46 * s;
  ornamentRow(ctx, W / 2, y, innerW * 0.3, C.gold);
  y += 46 * s;

  // corps avec capitale ornée
  let text = entry.text || "";
  const limit = MAX_CHARS[format] || MAX_CHARS.story;
  if (text.length > limit) {
    text = text.slice(0, limit).replace(/\s+\S*$/, "") + "…";
  }
  text = text.replace(/^#+\s*/m, "").replace(/\n+/g, " ").trim();

  const bodySize = 30 * s;
  const lineH = bodySize * 1.55;
  ctx.font = `${bodySize}px "EB Garamond", Georgia, serif`;

  const capSize = bodySize * 2.6;
  const first = text[0] || "";
  const rest = text.slice(1);
  ctx.font = `500 ${capSize}px Fraunces, Georgia, serif`;
  ctx.fillStyle = C.goldSoft;
  ctx.fillText(first, margin + 30, y + capSize * 0.45);
  const capW = ctx.measureText(first).width + 14 * s;

  ctx.font = `${bodySize}px "EB Garamond", Georgia, serif`;
  ctx.fillStyle = C.ivory;
  const tx = margin + 30 + capW;
  const attrH = entry.attribution ? 150 * s : 0;
  const lines = wrap(ctx, rest, innerW - capW);
  const maxLines = Math.max(1, Math.floor((H - y - margin - 60 * s - attrH) / lineH));
  // Sur le format story, le bloc de texte est centré verticalement.
  if (format === "story") {
    const totalH = Math.min(lines.length, maxLines) * lineH + capSize;
    y = Math.max(y, (H - totalH - margin * 2 - attrH) / 2);
  }
  for (const line of lines.slice(0, maxLines)) {
    ctx.fillText(line, tx, y + bodySize);
    y += lineH;
  }

  if (entry.attribution) {
    y = H - margin - 150 * s;
    ctx.font = `italic ${bodySize * 0.85}px "EB Garamond", Georgia, serif`;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "right";
    const attrLines = wrap(ctx, entry.attribution, innerW).slice(0, 2);
    let ay = y;
    for (const line of attrLines) {
      ctx.fillText(line, W - margin - 30, ay);
      ay += bodySize;
    }
    ctx.textAlign = "left";
    // badge anti-confusion (§9.2)
    const badge = "citation humoristique · attribution fictive";
    ctx.font = `${13 * s}px Inter, system-ui, sans-serif`;
    const bw = ctx.measureText(badge).width + 28 * s;
    const bx = W / 2 - bw / 2;
    const by = H - margin - 78 * s;
    ctx.strokeStyle = C.gold;
    ctx.lineWidth = 1;
    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(bx, by, bx + bw, by + 30 * s, 14 * s);
      ctx.stroke();
    } else {
      ctx.strokeRect(bx, by, bw, 30 * s);
    }
    ctx.fillStyle = C.gold;
    ctx.fillText(badge, bx + 14 * s, by + 20 * s);
  }

  const fy = H - margin - 46 * s;
  ornamentRow(ctx, W / 2, fy, innerW * 0.25, C.gold);
  spacingText(ctx, "LEGRANDPHILOSOPHE", `${13 * s}px Inter, sans-serif`, C.muted, W / 2, fy + 18 * s, 4 * s);
}

export function downloadCard(canvas, filename = "grande-reflexion.png") {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, "image/png");
}

export async function copyCard(canvas) {
  const blob = await new Promise((r) => canvas.toBlob(r, "image/png"));
  if (!blob) throw new Error("canvas vide");
  await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
}

export async function shareCard(canvas, title) {
  const blob = await new Promise((r) => canvas.toBlob(r, "image/png"));
  if (navigator.canShare?.({ files: [new File([blob], "reflexion.png", { type: "image/png" })] })) {
    await navigator.share({ title, files: [new File([blob], "reflexion.png", { type: "image/png" })] });
  } else {
    await shareFallback(title);
  }
}

async function shareFallback(title) {
  const text = window.location.href;
  if (navigator.share) await navigator.share({ title, text });
}

export async function publishCard(entry) {
  const res = await fetch("/api/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input_text: entry.input,
      generated_text: entry.text,
      attribution: entry.attribution,
      mode: entry.mode,
      styles: entry.params?.styles || [],
    }),
  });
  if (!res.ok) throw new Error("publication impossible");
  const data = await res.json();
  return data.path; // /carte/<id>
}

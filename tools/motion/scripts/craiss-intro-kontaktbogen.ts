// ============================================================
// Einzelbilder rund um jeden Flaggen-Wischer + erstes/letztes Sprech-Bild je Shot
//   npx tsx scripts/craiss-intro-kontaktbogen.ts <vorschau-03.mp4> <kontaktbogen.jpg>
// ============================================================
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import layoutJson from "../src/clients/craiss/projects/viele-jahre/intro-layout.json";

const [video, out] = process.argv.slice(2);
if (!video || !out) throw new Error("Aufruf: <vorschau-03.mp4> <kontaktbogen.jpg>");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "craiss-intro-"));
const frames = new Set<number>();
for (const w of layoutJson.wipes) {
  for (let f = w.cutFrame - 2 - w.inFrames; f <= w.cutFrame + w.outFrames + 1; f++) if (f >= 0) frames.add(f);
}
for (const s of layoutJson.shots) {
  frames.add(s.speechRecIn);
  frames.add(s.speechRecOut - 1);
}
const liste = [...frames].sort((a, b) => a - b);
const args: string[] = [];
for (const f of liste) {
  const png = path.join(dir, `f${String(f).padStart(4, "0")}.png`);
  execFileSync("ffmpeg", ["-nostdin", "-v", "error", "-y", "-i", video, "-vf", `select=eq(n\\,${f}),scale=240:-2`, "-frames:v", "1", png]);
  args.push("-label", `F${f}`, png);
}
execFileSync("montage", ["-font", "/System/Library/Fonts/Supplemental/Arial.ttf", "-pointsize", "11", ...args, "-tile", "10x", "-geometry", "+3+3", out]);
console.log(`Kontaktbogen ${out}: ${liste.length} Bilder`);

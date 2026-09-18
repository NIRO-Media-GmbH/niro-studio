// ============================================================
// Kontaktbogen je Schlagwort-Chip aus einem Vorschau-Render
//   npx tsx scripts/craiss-chip-kontaktbogen.ts <01..05> <vorschau.mp4> <kontaktbogen.jpg>
// Bilder bei Start + 0,5 s und Ende − 0,4 s jedes Chips.
// ============================================================
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import * as v01 from "../src/clients/craiss/projects/erster-tag/schlagwoerter";
import * as v02 from "../src/clients/craiss/projects/arbeitsalltag/schlagwoerter";
import * as v03 from "../src/clients/craiss/projects/viele-jahre/schlagwoerter";
import * as v04 from "../src/clients/craiss/projects/funnel/schlagwoerter";
import * as v05 from "../src/clients/craiss/projects/testimonial/schlagwoerter";

const MODS = { "01": v01, "02": v02, "03": v03, "04": v04, "05": v05 } as const;
const [id, video, out] = process.argv.slice(2);
const mod = MODS[id as keyof typeof MODS];
if (!mod || !video || !out) throw new Error("Aufruf: <01..05> <vorschau.mp4> <kontaktbogen.jpg>");

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "craiss-chips-"));
const args: string[] = [];
mod.KEYWORDS.forEach((k, i) => {
  for (const [tag, t] of [["a", k.startSec + 0.5], ["b", k.endSec - 0.4]] as const) {
    const f = path.join(dir, `${String(i).padStart(2, "0")}${tag}.png`);
    execFileSync("ffmpeg", ["-nostdin", "-v", "error", "-y", "-ss", t.toFixed(2), "-i", video, "-frames:v", "1", "-vf", "scale=360:-2", f]);
    args.push("-label", `${k.text} @ ${t.toFixed(2)} s`, f);
  }
});
execFileSync("montage", ["-font", "/System/Library/Fonts/Supplemental/Arial.ttf", "-pointsize", "12", ...args, "-tile", "4x", "-geometry", "+6+6", out]);
console.log(`Kontaktbogen ${out}: ${mod.KEYWORDS.length} Chips`);

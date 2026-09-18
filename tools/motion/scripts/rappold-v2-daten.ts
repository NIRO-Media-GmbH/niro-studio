// ============================================================
// Rappold Video 2 — Daten aus dem Schnitt V1 erzeugen
//   npx tsx scripts/rappold-v2-daten.ts
// Quellen (Charge _intern/animation-video-2): Scribe-Wortzeiten des Schnitts,
// Vision-Gesichtsboxen aller 1440 Frames (gesichter/faces_alle.tsv).
// ============================================================
import fs from "node:fs";
import path from "node:path";

const INTERN = "/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/_intern/animation-video-2";
const ZIEL = path.resolve(__dirname, "../src/clients/rappold/projects/mechatroniker/daten-generiert.ts");
const FPS = 25;
const SCHNITT_FRAMES = 1440;
const BASE_H = 1920;

// Wortlaut-Korrekturen, belegt durch Original-Interview (FX3_1011/FX3_1013) + Whisper large-v3
const KORREKTUREN: Record<number, { erwartet: string; neu: string | null }> = {
  56: { erwartet: '"Ja', neu: "„Ja," },
  58: { erwartet: "bin", neu: null },
  61: { erwartet: 'Arbeitsplatz."', neu: "Arbeitsplatz.“" },
  90: { erwartet: '"Okay,', neu: "„Okay," },
  93: { erwartet: "ich.", neu: "ich.“" },
  105: { erwartet: 'eingestellt."', neu: "eingestellt." },
  111: { erwartet: "Stunde,", neu: "Stunde" },
  112: { erwartet: "jetzt", neu: "bis" },
  175: { erwartet: "man", neu: "dann" },
  177: { erwartet: "ja", neu: "ich" },
};

type Typ = "nah" | "totale" | "broll";
// Erstes Frame jeder Einstellung; Zoom-Blur-Übergänge zählen zur alten Einstellung
const EINSTELLUNGEN: [number, Typ, string][] = [
  [0, "nah", "Hannes"], [34, "totale", "Hannes"], [56, "nah", "Hannes"],
  [123, "broll", "Drohne"], [140, "broll", "Drohne"], [158, "broll", "Fassade"],
  [187, "nah", "Hannes"], [206, "totale", "Hannes"], [219, "broll", "VW-Eingang"],
  [266, "nah", "Christos"], [284, "totale", "Christos"], [304, "broll", "VW-Pylon"],
  [332, "nah", "Christos"], [361, "broll", "Halle Multivan"], [379, "broll", "Multivan Seite"],
  [394, "broll", "Hebebühne Fernbedienung"], [411, "broll", "Auto auf Bühne"], [429, "totale", "Hannes"],
  [531, "nah", "Hannes"], [585, "totale", "Christos"], [600, "broll", "Christos Wuchtmaschine"],
  [622, "broll", "Wuchtmaschine"], [644, "broll", "Christos Reifen"], [668, "broll", "Unterboden"],
  [694, "broll", "Handschuh"], [709, "broll", "Hannes Vermessung"], [731, "broll", "Radklammer"],
  [758, "broll", "Sensor"], [780, "broll", "Vermessungs-Bildschirm"], [809, "nah", "Hannes"],
  [834, "totale", "Christos"], [871, "broll", "Hände Bauteil"], [901, "broll", "Hannes und Christos Motor"],
  [930, "nah", "Christos"], [959, "totale", "Christos"], [984, "broll", "Hannes und Christos am Auto"],
  [1009, "nah", "Christos"], [1025, "broll", "Schlagschrauber"], [1041, "broll", "Radnabe"],
  [1061, "broll", "Reifenwechsel"], [1083, "totale", "Hannes"], [1145, "broll", "Rad"],
  [1155, "broll", "Reifen dunkel"], [1169, "totale", "Christos"], [1195, "nah", "Christos"],
  [1252, "totale", "Christos"], [1278, "broll", "Abklatschen"], [1296, "totale", "Hannes"],
  [1380, "nah", "Hannes"],
];
// VW-Nabendeckel wird in der Radnaben-Einstellung als Gesicht erkannt
const FALSCHE_GESICHTER = new Set(["Radnabe"]);

type Box = { y0: number; y1: number; c: number };
const scribe = JSON.parse(fs.readFileSync(path.join(INTERN, "transcript/video2_v1.words.json"), "utf8")) as {
  words: { text: string; start: number; end: number }[];
};
const worte: { text: string; start: number; end: number }[] = [];
scribe.words.forEach((w, i) => {
  const k = KORREKTUREN[i];
  if (k && w.text !== k.erwartet) throw new Error(`Wort ${i}: erwartet ${k.erwartet}, gefunden ${w.text}`);
  if (k && k.neu === null) return;
  worte.push({ text: k ? (k.neu as string) : w.text, start: w.start, end: w.end });
});

const gesichter = new Map<number, Box[]>();
for (const zeile of fs.readFileSync(path.join(INTERN, "gesichter/faces_alle.tsv"), "utf8").trim().split("\n")) {
  const [datei, boxen = ""] = zeile.split("\t");
  gesichter.set(
    Number(datei.slice(0, 5)),
    boxen.split(";").filter(Boolean).map((b) => {
      const [, y0, , y1, c] = b.split(",").map(Number);
      return { y0, y1, c };
    }),
  );
}

const einstellungen = EINSTELLUNGEN.map(([von, typ, motiv], i) => {
  const bis = i + 1 < EINSTELLUNGEN.length ? EINSTELLUNGEN[i + 1][0] : SCHNITT_FRAMES;
  let kinn = -1;
  let stirn = 2;
  if (!FALSCHE_GESICHTER.has(motiv)) {
    for (let f = von; f < bis; f++) {
      for (const g of gesichter.get(f) ?? []) {
        if (g.c < 0.6 || g.y1 - g.y0 < 0.04) continue;
        kinn = Math.max(kinn, g.y1);
        stirn = Math.min(stirn, g.y0);
      }
    }
  }
  const ohne = kinn < 0;
  return {
    id: `E${String(i + 1).padStart(2, "0")}`,
    von,
    bis,
    typ,
    motiv,
    // Vereinigung aller Gesichtsboxen der Einstellung (Basis-px): oberste Stirn, tiefstes Kinn
    gesichtOben: ohne ? null : Math.max(0, Math.round(stirn * BASE_H)),
    kinnY: ohne ? null : Math.round(kinn * BASE_H),
  };
});

fs.mkdirSync(path.dirname(ZIEL), { recursive: true });
fs.writeFileSync(
  ZIEL,
  `// AUTOMATISCH ERZEUGT von scripts/rappold-v2-daten.ts — nicht von Hand ändern
export const FPS = ${FPS};
export const SCHNITT_FRAMES = ${SCHNITT_FRAMES};

export type Wort = { text: string; start: number; end: number };
export const WORTE: Wort[] = ${JSON.stringify(worte)};

export type EinstellungTyp = "nah" | "totale" | "broll";
export type Einstellung = { id: string; von: number; bis: number; typ: EinstellungTyp; motiv: string; gesichtOben: number | null; kinnY: number | null };
export const EINSTELLUNGEN: Einstellung[] = ${JSON.stringify(einstellungen, null, 1)};
`,
);
console.log(`${worte.length} Wörter, ${einstellungen.length} Einstellungen → ${path.relative(process.cwd(), ZIEL)}`);

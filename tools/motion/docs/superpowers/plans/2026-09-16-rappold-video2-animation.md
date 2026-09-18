# Rappold Video 2 „Kfz-Mechatroniker" — Animationen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine Alpha-Datei (ProRes 4444, 2160×3840, 25 fps, 1565 Frames = Schnitt V1 57,6 s + 5 s Endcard) mit allen Grafiken und Untertiteln im Stil „Freie Typo" für `Video 2 - Kfz-Mechatroniker - Recruiting_V1`.

**Architecture:** Neuer Motion-Client `rappold`. Ein Generator-Skript macht aus Scribe-Wortzeiten (mit belegten Korrekturen) und Vision-Gesichtsboxen eine TS-Datendatei (Wörter, Einstellungen mit Kinnlinie). Untertitel- und Grafik-Plan sind handgepflegte TS-Daten; reine Logik (Timing, Layout, Schriftmetrik) liegt in kleinen Modulen mit `node:test`-Tests, die auch die Regeln prüfen (Kinn + 110 px, Grenzen, Kollisionen, Abdeckung aller Wörter). Drei Renderer (Untertitel, Grafiken, Endcard) auf einer 1080er-Basisbühne, die uniform auf die Leinwand skaliert.

**Tech Stack:** Remotion 4.0.519, React 18, zod, TypeScript; Tests `npx tsx --test`; Prüfwerkzeuge Python 3 + ffmpeg + ImageMagick + Swift/Vision (vorhanden in der Charge).

**Spec:** `tools/motion/docs/superpowers/specs/2026-09-16-rappold-video2-animation-design.md`

## Global Constraints

- Arbeitsverzeichnis für alle Befehle: `/Users/jansantos/NIRO Studio/tools/motion`.
- Charge: `/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09` (im Plan `$CHARGE`; in zsh immer ausgeschrieben/quoted verwenden).
- Farben nur aus `src/clients/rappold/lib.ts`: `BLAU #0D69B3`, `ANTHRAZIT #434F4F`, `HELLGRAU #EBE9E8`, `WEISS`. Schrift `RappoldOpenSans` (Open Sans v29, Schnitte 600 und 800).
- Basis-Bühne 1080×1920. Textoberkante ≥ Kinn der Einstellung + 110 px; Unterkante ≤ 1500 px; Rand links/rechts ≥ 54 px; Grafikbreite ≤ 972 px, Untertitelzeile ≤ 920 px.
- Nur `transform` und `opacity` animieren (Ausnahme Endcard-Grund: `filter: blur` auf einem Standbild). Kein Bounce, kein Overshoot.
- Nie ein Wort vor Wortanfang − 0,08 s zeigen; ganze Sinneinheiten; keine Dopplung mit Grafiken.
- `(M/W/D)` an jedem Berufstitel in CTA/Endcard.
- Commits nur nach ausdrücklicher Freigabe durch Jan/David (Studio-Regel) — kein Commit-Schritt ohne Rückfrage.
- Renders mit `--public-dir=public-rappold` bzw. aus dem Bundle `build-rappold`; Renders nach `$CHARGE/Ergebnisse/Renders/`.

## File Structure

| Datei | Verantwortung |
|---|---|
| Create `src/clients/rappold/brand.json` | CI-Werte für den Client |
| Create `src/clients/rappold/lib.ts` | Farben, Font-Stack, Basis-Maße, Schatten (rein, testbar) |
| Create `src/clients/rappold/fonts.ts` | lädt die Website-WOFF2 (Seiteneffekt, nur Renderer) |
| Create `src/clients/rappold/metriken.ts` | Laufweiten Open Sans 600/800, `textBreite`, `umbrechen` |
| Create `scripts/rappold-v2-daten.ts` | Generator: Wörter + Einstellungen → `daten-generiert.ts` |
| Create `src/clients/rappold/projects/mechatroniker/daten-generiert.ts` | erzeugt, nie von Hand ändern |
| Create `src/clients/rappold/projects/mechatroniker/untertitel-plan.ts` | Sätze, Seiten, Heroes, ausgeblendete Sätze |
| Create `src/clients/rappold/projects/mechatroniker/grafik-plan.ts` | Grafiken mit Zeiten, Texten, Positionen |
| Create `src/clients/rappold/projects/mechatroniker/timing.ts` | Satzfenster, Seitenwechsel, Einblendung |
| Create `src/clients/rappold/projects/mechatroniker/layout.ts` | Zeilenbau, Höhen, Grafikmaße, Gleiten |
| Create `…/mechatroniker/{metriken,timing,layout,plan}.test.ts` | Tests |
| Create `…/mechatroniker/Untertitel.tsx`, `Grafiken.tsx`, `Endcard.tsx`, `Composition.tsx` | Renderer + Komposition |
| Modify `src/Root.tsx` | Ordner „Rappold" mit Vorschau + Alpha |
| Create `$CHARGE/_intern/animation-video-2/qa/*.py` | Gesichts-, Luma-Check, Kontaktbogen |
| Modify `$CHARGE/Protokoll.md` | Protokoll-Pflicht |

---

### Task 1: Client-Grundlage, Schriftmetrik, Datengenerator

**Files:**
- Create: `src/clients/rappold/brand.json`, `src/clients/rappold/lib.ts`, `src/clients/rappold/fonts.ts`, `src/clients/rappold/metriken.ts`
- Create: `scripts/rappold-v2-daten.ts` → erzeugt `src/clients/rappold/projects/mechatroniker/daten-generiert.ts`
- Test: `src/clients/rappold/metriken.test.ts`

**Interfaces:**
- Produces: `BLAU, ANTHRAZIT, HELLGRAU, WEISS, FONT, BASE_W=1080, BASE_H=1920, RAND_X=54, TEXT_BREITE=972, GRENZE_UNTEN=1500, KINN_ABSTAND=110, SCHATTEN, SCHATTEN_BLAU` (lib.ts); `type Schnitt = "600"|"800"`, `textBreite(text, schnitt, px, sperrungEm?) → number`, `umbrechen(worte: string[], schnitt, px, maxBreite, sperrungEm?) → number[][]` (metriken.ts); `FPS, SCHNITT_FRAMES, type Wort {text,start,end}, WORTE, type Einstellung {id,von,bis,typ,motiv,kinnY}, EINSTELLUNGEN` (daten-generiert.ts).

- [ ] **Step 1: Assets prüfen** — Fonts `public/clients/rappold/fonts/OpenSans-600.woff2`, `OpenSans-800.woff2` und Logos `public/clients/rappold/rappold-logo.svg`, `rappold-logo-weiss.svg` liegen bereits (Session 16.09.). Nicht benötigte Schnitte löschen:

```bash
rm -f public/clients/rappold/fonts/OpenSans-regular.woff2 public/clients/rappold/fonts/OpenSans-700.woff2 && ls public/clients/rappold/fonts
```

- [ ] **Step 2: `brand.json`, `lib.ts`, `fonts.ts` anlegen**

```json
{
  "name": "Autohaus Rappold GmbH",
  "colors": { "primary": "#0D69B3", "secondary": "#434F4F", "accent": "#EBE9E8", "background": "#FFFFFF", "text": "#FFFFFF" },
  "fonts": { "heading": "Open Sans", "body": "Open Sans" },
  "logo": "clients/rappold/rappold-logo.svg",
  "style": { "borderRadius": 0, "animationSpeed": "normal" }
}
```

```ts
// src/clients/rappold/lib.ts
// ============================================================
// Autohaus Rappold — CI und Basis-Maße
// Farben aus dem Logo (autohaus-rappold.de, im Chat bestätigt 16.09.2026),
// Schrift Open Sans v29 von der Website (public/clients/rappold/fonts).
// ============================================================
export const BLAU = "#0D69B3";
export const ANTHRAZIT = "#434F4F";
export const HELLGRAU = "#EBE9E8";
export const WEISS = "#FFFFFF";

export const FONT = '"RappoldOpenSans", "Open Sans", Arial, sans-serif';

// Basis-Bühne 1080×1920 — die Komposition skaliert uniform auf die Leinwand
export const BASE_W = 1080;
export const BASE_H = 1920;
export const RAND_X = 54;
export const TEXT_BREITE = BASE_W - 2 * RAND_X;
export const GRENZE_UNTEN = 1500; // darunter liegt die Plattform-UI
export const KINN_ABSTAND = 110;

export const SCHATTEN = "0 3px 18px rgba(0,0,0,0.45), 0 1px 3px rgba(0,0,0,0.5)";
// Blaue Glyphen brauchen einen dunklen Hof, sonst verschwinden sie auf mittelgrauem Grund
export const SCHATTEN_BLAU = "0 0 26px rgba(0,0,0,0.6), 0 0 8px rgba(0,0,0,0.35), 0 2px 4px rgba(0,0,0,0.45)";
```

```ts
// src/clients/rappold/fonts.ts — lädt Open Sans (Website-Dateien) für alle Rappold-Kompositionen
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

for (const [weight, datei] of [["600", "OpenSans-600.woff2"], ["800", "OpenSans-800.woff2"]] as const) {
  loadFont({ family: "RappoldOpenSans", url: staticFile(`clients/rappold/fonts/${datei}`), weight, format: "woff2" });
}
```

- [ ] **Step 3: Laufweiten-Tabelle erzeugen** (WOFF v1 aus dem Scratchpad, fontTools im transcribe-venv; WOFF2 braucht Brotli, das fehlt)

```bash
"/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" - <<'EOF'
import json
from fontTools.ttLib import TTFont
S = "/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/729ca146-885b-48f3-b941-68751ddf9096/scratchpad"
tab = {}
for w in ["600", "800"]:
    f = TTFont(f"{S}/OpenSans-{w}.woff"); upm = f["head"].unitsPerEm; cmap = f.getBestCmap(); hmtx = f["hmtx"]
    chars = "".join(chr(c) for c in range(32, 127)) + "ÄÖÜäöüß„“”–·…"
    tab[w] = {c: round(hmtx[cmap[ord(c)]][0] / upm, 4) for c in chars if ord(c) in cmap}
open("src/clients/rappold/laufweiten.json", "w").write(json.dumps(tab, ensure_ascii=False))
print({k: len(v) for k, v in tab.items()})
EOF
```

- [ ] **Step 4: Test für `metriken.ts` schreiben**

```ts
// src/clients/rappold/metriken.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { textBreite, umbrechen } from "./metriken";

test("Laufweite entspricht der fontTools-Messung", () => {
  // gemessen 16.09.: KFZ-MECHATRONIKER = 10,971 em im Schnitt 800
  assert.ok(Math.abs(textBreite("KFZ-MECHATRONIKER", "800", 100) - 1097.1) < 1);
  assert.ok(textBreite("AB", "800", 100, 0.1) > textBreite("AB", "800", 100));
});

test("Umbruch: passt → eine Zeile, sonst ausgewogene zwei Zeilen", () => {
  assert.deepEqual(umbrechen(["Bin", "seit", "2013"], "600", 56, 920), [[0, 1, 2]]);
  const worte = "Also wenn du Schrauber bist und Bock auf eine moderne Werkstatt".split(" ");
  const zeilen = umbrechen(worte, "600", 56, 920);
  assert.equal(zeilen.length, 2);
  const breite = (z: number[]) => textBreite(z.map((i) => worte[i]).join(" "), "600", 56);
  assert.ok(Math.abs(breite(zeilen[0]) - breite(zeilen[1])) < 260, "Zeilen etwa gleich lang");
  assert.ok(zeilen.every((z) => breite(z) <= 920));
});
```

- [ ] **Step 5: Test laufen lassen → FAIL** (`Cannot find module './metriken'`)

Run: `npx tsx --test src/clients/rappold/metriken.test.ts`

- [ ] **Step 6: `metriken.ts` implementieren**

```ts
// src/clients/rappold/metriken.ts
// Laufweiten Open Sans v29 (em) aus den Website-WOFF-Dateien (fontTools, 16.09.2026).
// Grundlage für Zeilenumbruch und Maß-Prüfungen ohne Browser.
import LAUFWEITEN from "./laufweiten.json";

export type Schnitt = "600" | "800";
const ERSATZ_EM = 0.62;
const tabelle = LAUFWEITEN as Record<Schnitt, Record<string, number>>;

export const textBreite = (text: string, schnitt: Schnitt, px: number, sperrungEm = 0): number => {
  let em = 0;
  let n = 0;
  for (const c of text) {
    em += tabelle[schnitt][c] ?? ERSATZ_EM;
    n++;
  }
  return (em + sperrungEm * n) * px;
};

const zeilenBreite = (worte: string[], von: number, bis: number, schnitt: Schnitt, px: number, sperrungEm: number) =>
  textBreite(worte.slice(von, bis).join(" "), schnitt, px, sperrungEm);

// Gieriger Umbruch; ergibt das genau zwei Zeilen, wird der Bruch ausgewogen gesetzt.
export const umbrechen = (worte: string[], schnitt: Schnitt, px: number, maxBreite: number, sperrungEm = 0): number[][] => {
  const starts: number[] = [0];
  for (let i = 1; i < worte.length; i++) {
    if (zeilenBreite(worte, starts[starts.length - 1], i + 1, schnitt, px, sperrungEm) > maxBreite) starts.push(i);
  }
  if (starts.length === 2) {
    let besterBruch = starts[1];
    let besteMax = Infinity;
    for (let k = 1; k < worte.length; k++) {
      const a = zeilenBreite(worte, 0, k, schnitt, px, sperrungEm);
      const b = zeilenBreite(worte, k, worte.length, schnitt, px, sperrungEm);
      if (a <= maxBreite && b <= maxBreite && Math.max(a, b) < besteMax) {
        besteMax = Math.max(a, b);
        besterBruch = k;
      }
    }
    starts[1] = besterBruch;
  }
  return starts.map((s, k) => Array.from({ length: (starts[k + 1] ?? worte.length) - s }, (_, j) => s + j));
};
```

- [ ] **Step 7: Test laufen lassen → PASS**

Run: `npx tsx --test src/clients/rappold/metriken.test.ts`

- [ ] **Step 8: Generator `scripts/rappold-v2-daten.ts` anlegen**

```ts
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
  if (!FALSCHE_GESICHTER.has(motiv)) {
    for (let f = von; f < bis; f++) {
      for (const g of gesichter.get(f) ?? []) if (g.c >= 0.6 && g.y1 - g.y0 >= 0.04) kinn = Math.max(kinn, g.y1);
    }
  }
  return { id: `E${String(i + 1).padStart(2, "0")}`, von, bis, typ, motiv, kinnY: kinn < 0 ? null : Math.round(kinn * BASE_H) };
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
export type Einstellung = { id: string; von: number; bis: number; typ: EinstellungTyp; motiv: string; kinnY: number | null };
export const EINSTELLUNGEN: Einstellung[] = ${JSON.stringify(einstellungen, null, 1)};
`,
);
console.log(`${worte.length} Wörter, ${einstellungen.length} Einstellungen → ${path.relative(process.cwd(), ZIEL)}`);
```

- [ ] **Step 9: Generator laufen lassen**

Run: `npx tsx scripts/rappold-v2-daten.ts`
Expected: `204 Wörter, 49 Einstellungen → src/clients/rappold/projects/mechatroniker/daten-generiert.ts`

---

### Task 2: Timing und Layout

**Files:**
- Create: `src/clients/rappold/projects/mechatroniker/timing.ts`, `layout.ts`
- Create (Typen, Inhalt folgt in Task 3): `untertitel-plan.ts`, `grafik-plan.ts` mit leeren Listen
- Test: `timing.test.ts`, `layout.test.ts`

**Interfaces:**
- Consumes: `Wort`, `textBreite`, `umbrechen`, `TEXT_BREITE`.
- Produces (untertitel-plan.ts): `type HeroFarbe = "weiss"|"blau"`, `type Satz = {id, text, von, bis, seiten: number[], hero?: {von,bis,farbe}[], aus?: string, gross?: boolean, nachlaufSek?: number, abdunkeln?: number}`, `SAETZE: Satz[]`.
- Produces (grafik-plan.ts): `type Farbe`, `type Segment {text, farbe}`, `type TitelZeile {segmente, px}`, `type Grafik {id, von, bis, y, ausrichtung: "links"|"rechts", kicker?, zeilen, unterzeile?, abdunkeln?, stehenBleiben?, gleiten?: {abFrame, nachY, dauer}}`, `GRAFIKEN: Grafik[]`, `DAUER_FRAMES = 1565`.
- Produces (timing.ts): `VORLAUF_SEK=0.08, EINBLEND_FRAMES=5, HERO_FRAMES=7, NACHLAUF_SEK=0.6, AUSBLEND_FRAMES=5, MIN_LETZTES_WORT_SEK=0.4`, `type Fenster {von, bis}`, `satzFenster(satz, worte, naechster, fps)`, `sichtbareSaetze(saetze, worte, fps)`, `seitenIndex(satz, worte, t)`, `seitenFenster(satz, worte, fenster, fps)`, `einblendung(start, frame, fps, dauer?)`.
- Produces (layout.ts): `UT_PX=56, UT_ZEILENHOEHE=1.18, UT_BREITE=920, UT_UNTERKANTE=1440, HERO_PX_MAX=150, HERO_ZEILENHOEHE=1.08, HERO_SPERRUNG=-0.02, TITEL_ZEILENHOEHE=1.08, KICKER_PX=30, KICKER_SPERRUNG=0.18, KICKER_ABSTAND=12, LINIE_W=64, LINIE_H=8, LINIE_ABSTAND=16, UNTERZEILE_PX=38, UNTERZEILE_SPERRUNG=0.12, UNTERZEILE_ABSTAND=8`, `type Zeile {worte, hero, px}`, `seitenBereich`, `anzeigeText`, `seitenZeilen`, `zeilenHoehe`, `seitenHoehe`, `seitenOben`, `grafikHoehe`, `grafikBreite`, `grafikY(g, frame)`.

- [ ] **Step 1: Typ-Dateien anlegen**

```ts
// src/clients/rappold/projects/mechatroniker/untertitel-plan.ts
export type HeroFarbe = "weiss" | "blau";
export type Satz = {
  id: string;
  text: string; // Kontrolle: muss den Wörtern von..bis entsprechen
  von: number; // Wortindex (inklusive)
  bis: number;
  seiten: number[]; // Wortindex je Seitenanfang; erster = von
  hero?: { von: number; bis: number; farbe: HeroFarbe }[]; // höchstens eins je Seite
  aus?: string; // Satz erscheint nicht — Grund (Dopplung mit Grafik)
  gross?: boolean; // erstes Wort groß (Übergabe: Grafik trägt den Satzanfang)
  nachlaufSek?: number; // Standzeit nach dem letzten Wort (Standard 0,6 s)
  abdunkeln?: number; // lokale Abdunklung 0–0,4
};
export const SAETZE: Satz[] = [];
```

```ts
// src/clients/rappold/projects/mechatroniker/grafik-plan.ts
export const DAUER_FRAMES = 1565; // Schnitt V1 1440 + Endcard 125
export type Farbe = "weiss" | "blau";
export type Segment = { text: string; farbe: Farbe };
export type TitelZeile = { segmente: Segment[]; px: number };
export type Grafik = {
  id: string;
  von: number; // erstes Frame (Einstieg beginnt hier)
  bis: number; // exklusiv; Ausstieg in den letzten 6 Frames
  y: number; // Oberkante (Basis-px)
  ausrichtung: "links" | "rechts";
  kicker?: string;
  zeilen: TitelZeile[];
  unterzeile?: Segment[];
  abdunkeln?: number;
  stehenBleiben?: boolean; // kein Ausstieg (CTA läuft in die Endcard)
  gleiten?: { abFrame: number; nachY: number; dauer: number };
};
export const GRAFIKEN: Grafik[] = [];
```

- [ ] **Step 2: Tests schreiben**

```ts
// src/clients/rappold/projects/mechatroniker/timing.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { einblendung, satzFenster, seitenFenster, seitenIndex } from "./timing";
import type { Satz } from "./untertitel-plan";

const W = [
  { text: "Eins", start: 1.0, end: 1.2 },
  { text: "zwei", start: 1.5, end: 1.7 },
  { text: "drei.", start: 1.6, end: 2.0 },
  { text: "Vier.", start: 2.6, end: 3.0 },
];
const satz: Satz = { id: "a", text: "Eins zwei drei.", von: 0, bis: 2, seiten: [0, 2] };
const naechster: Satz = { id: "b", text: "Vier.", von: 3, bis: 3, seiten: [3] };

test("Satzfenster: Vorlauf 0,08 s, Nachlauf 0,6 s, gekappt vor dem nächsten Satz", () => {
  assert.deepEqual(satzFenster(satz, W, null, 25), { von: 23, bis: 65 });
  assert.deepEqual(satzFenster(satz, W, naechster, 25), { von: 23, bis: 62 });
  assert.deepEqual(satzFenster({ ...satz, nachlaufSek: 0.1 }, W, null, 25), { von: 23, bis: 53 });
});

test("Seitenwechsel wartet, bis das letzte Wort der Seite 0,4 s stand", () => {
  assert.equal(seitenIndex(satz, W, 1.7), 0);
  assert.equal(seitenIndex(satz, W, 1.83), 1);
  assert.deepEqual(seitenFenster(satz, W, { von: 23, bis: 65 }, 25), [{ von: 23, bis: 46 }, { von: 46, bis: 65 }]);
});

test("Wort-Einblendung: 0 bis Wortanfang − 0,08 s, 1 nach 5 Frames", () => {
  assert.equal(einblendung(2.0, 48, 25), 0);
  assert.equal(einblendung(2.0, 53, 25), 1);
});
```

```ts
// src/clients/rappold/projects/mechatroniker/layout.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { anzeigeText, grafikHoehe, grafikY, seitenOben, seitenZeilen, UT_BREITE } from "./layout";
import { textBreite } from "../../metriken";
import type { Satz } from "./untertitel-plan";
import type { Grafik } from "./grafik-plan";

const W = "Man hat viel Platz, man kann sich ausbreiten,".split(" ").map((text, i) => ({ text, start: i, end: i + 0.5 }));

test("Anzeige: Hero versal ohne Komma, Übergabe mit großem Anfang", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0], gross: true };
  assert.equal(anzeigeText(W, s, 0, false), "Man");
  assert.equal(anzeigeText(W, s, 3, true), "PLATZ");
  assert.equal(anzeigeText(W, { ...s, von: 1 }, 1, false), "Hat");
});

test("Seite mit Hero in der Mitte: Grundzeile, Hero, Grundzeile", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0], hero: [{ von: 2, bis: 3, farbe: "weiss" }] };
  const z = seitenZeilen(s, 0, W);
  assert.deepEqual(z.map((l) => l.hero), [null, "weiss", null]);
  assert.deepEqual(z[1].worte, [2, 3]);
  assert.equal(z[1].px, 150);
  assert.ok(seitenOben(z) < 1440 - 150);
});

test("Grundzeilen passen in die Untertitel-Breite", () => {
  const s: Satz = { id: "x", text: "", von: 0, bis: 6, seiten: [0] };
  for (const z of seitenZeilen(s, 0, W)) {
    assert.ok(textBreite(z.worte.map((i) => W[i].text).join(" "), "600", z.px) <= UT_BREITE);
  }
});

test("Grafik: Höhe aus Bausteinen, Gleiten mit Ease", () => {
  const g: Grafik = { id: "g", von: 0, bis: 100, y: 850, ausrichtung: "links", kicker: "K", zeilen: [{ segmente: [{ text: "T", farbe: "weiss" }], px: 100 }], gleiten: { abFrame: 50, nachY: 650, dauer: 10 } };
  assert.equal(Math.round(grafikHoehe(g)), Math.round(30 * 1.2 + 12 + 8 + 16 + 100 * 1.08));
  assert.equal(grafikY(g, 40), 850);
  assert.equal(grafikY(g, 60), 650);
  assert.ok(grafikY(g, 55) < 850 && grafikY(g, 55) > 650);
});
```

- [ ] **Step 3: Tests laufen lassen → FAIL** (Module fehlen)

Run: `npx tsx --test src/clients/rappold/projects/mechatroniker/timing.test.ts src/clients/rappold/projects/mechatroniker/layout.test.ts`

- [ ] **Step 4: `timing.ts` implementieren**

```ts
// src/clients/rappold/projects/mechatroniker/timing.ts
import type { Wort } from "./daten-generiert";
import type { Satz } from "./untertitel-plan";

export const VORLAUF_SEK = 0.08;
export const EINBLEND_FRAMES = 5;
export const HERO_FRAMES = 7;
export const NACHLAUF_SEK = 0.6;
export const AUSBLEND_FRAMES = 5;
export const MIN_LETZTES_WORT_SEK = 0.4;
const ABSTAND_SEK = 0.05;

export type Fenster = { von: number; bis: number }; // Frames, bis exklusiv

export const satzFenster = (satz: Satz, worte: Wort[], naechster: Satz | null, fps: number): Fenster => {
  const von = Math.round((worte[satz.von].start - VORLAUF_SEK) * fps);
  let bisSek = worte[satz.bis].end + (satz.nachlaufSek ?? NACHLAUF_SEK);
  if (naechster) bisSek = Math.min(bisSek, worte[naechster.von].start - VORLAUF_SEK - ABSTAND_SEK);
  return { von, bis: Math.round(bisSek * fps) };
};

export const sichtbareSaetze = (saetze: Satz[], worte: Wort[], fps: number) => {
  const aktiv = saetze.filter((s) => !s.aus);
  return aktiv.map((satz, k) => ({ satz, fenster: satzFenster(satz, worte, aktiv[k + 1] ?? null, fps) }));
};

const wechselSek = (satz: Satz, worte: Wort[], k: number): number => {
  const p = satz.seiten[k];
  return Math.max(worte[p].start - VORLAUF_SEK, worte[p - 1].start - VORLAUF_SEK + MIN_LETZTES_WORT_SEK);
};

export const seitenIndex = (satz: Satz, worte: Wort[], t: number): number => {
  let idx = 0;
  for (let k = 1; k < satz.seiten.length; k++) if (t >= wechselSek(satz, worte, k)) idx = k;
  return idx;
};

// Sichtbarkeitsfenster jeder Seite (für Prüfungen)
export const seitenFenster = (satz: Satz, worte: Wort[], fenster: Fenster, fps: number): Fenster[] =>
  satz.seiten.map((_, k) => ({
    von: k === 0 ? fenster.von : Math.ceil(wechselSek(satz, worte, k) * fps - 1e-6),
    bis: k + 1 < satz.seiten.length ? Math.ceil(wechselSek(satz, worte, k + 1) * fps - 1e-6) : fenster.bis,
  }));

export const einblendung = (start: number, frame: number, fps: number, dauer = EINBLEND_FRAMES): number => {
  const ab = Math.round((start - VORLAUF_SEK) * fps);
  return Math.min(1, Math.max(0, (frame - ab) / dauer));
};
```

- [ ] **Step 5: `layout.ts` implementieren**

```ts
// src/clients/rappold/projects/mechatroniker/layout.ts
import { Easing, interpolate } from "remotion";
import { TEXT_BREITE } from "../../lib";
import { textBreite, umbrechen } from "../../metriken";
import type { Wort } from "./daten-generiert";
import type { Grafik } from "./grafik-plan";
import type { HeroFarbe, Satz } from "./untertitel-plan";

export const UT_PX = 56;
export const UT_ZEILENHOEHE = 1.18;
export const UT_BREITE = 920;
export const UT_UNTERKANTE = 1440;
export const HERO_PX_MAX = 150;
export const HERO_ZEILENHOEHE = 1.08;
export const HERO_SPERRUNG = -0.02;
export const TITEL_ZEILENHOEHE = 1.08;
export const KICKER_PX = 30;
export const KICKER_SPERRUNG = 0.18;
export const KICKER_ABSTAND = 12;
export const LINIE_W = 64;
export const LINIE_H = 8;
export const LINIE_ABSTAND = 16;
export const UNTERZEILE_PX = 38;
export const UNTERZEILE_SPERRUNG = 0.12;
export const UNTERZEILE_ABSTAND = 8;

export type Zeile = { worte: number[]; hero: HeroFarbe | null; px: number };

const bereich = (von: number, bisExkl: number) => Array.from({ length: Math.max(0, bisExkl - von) }, (_, k) => von + k);

export const seitenBereich = (satz: Satz, seite: number): [number, number] => [satz.seiten[seite], satz.seiten[seite + 1] ?? satz.bis + 1];

export const anzeigeText = (worte: Wort[], satz: Satz, i: number, hero: boolean): string => {
  let t = worte[i].text;
  if (satz.gross && i === satz.von) t = t.charAt(0).toUpperCase() + t.slice(1);
  return hero ? t.replace(/[,:;]+$/, "").toUpperCase() : t;
};

export const seitenZeilen = (satz: Satz, seite: number, worte: Wort[]): Zeile[] => {
  const [a, b] = seitenBereich(satz, seite);
  const hero = satz.hero?.find((h) => h.von >= a && h.bis < b);
  const teile = hero
    ? [
        { idx: bereich(a, hero.von), hero: null },
        { idx: bereich(hero.von, hero.bis + 1), hero: hero.farbe },
        { idx: bereich(hero.bis + 1, b), hero: null },
      ].filter((t) => t.idx.length > 0)
    : [{ idx: bereich(a, b), hero: null }];
  const zeilen: Zeile[] = [];
  for (const t of teile) {
    if (t.hero) {
      const text = t.idx.map((i) => anzeigeText(worte, satz, i, true)).join(" ");
      const px = Math.min(HERO_PX_MAX, Math.floor(TEXT_BREITE / textBreite(text, "800", 1, HERO_SPERRUNG)));
      zeilen.push({ worte: t.idx, hero: t.hero, px });
    } else {
      const texte = t.idx.map((i) => anzeigeText(worte, satz, i, false));
      for (const z of umbrechen(texte, "600", UT_PX, UT_BREITE)) zeilen.push({ worte: z.map((k) => t.idx[k]), hero: null, px: UT_PX });
    }
  }
  return zeilen;
};

export const zeilenHoehe = (z: Zeile): number => z.px * (z.hero ? HERO_ZEILENHOEHE : UT_ZEILENHOEHE);
export const seitenHoehe = (zeilen: Zeile[]): number => zeilen.reduce((s, z) => s + zeilenHoehe(z), 0);
export const seitenOben = (zeilen: Zeile[]): number => UT_UNTERKANTE - seitenHoehe(zeilen);

export const grafikHoehe = (g: Grafik): number =>
  (g.kicker ? KICKER_PX * 1.2 + KICKER_ABSTAND : 0) +
  LINIE_H +
  LINIE_ABSTAND +
  g.zeilen.reduce((s, z) => s + z.px * TITEL_ZEILENHOEHE, 0) +
  (g.unterzeile ? UNTERZEILE_ABSTAND + UNTERZEILE_PX * 1.25 : 0);

export const grafikBreite = (g: Grafik): number =>
  Math.max(
    ...g.zeilen.map((z) => textBreite(z.segmente.map((s) => s.text).join(""), "800", z.px, HERO_SPERRUNG)),
    g.kicker ? textBreite(g.kicker, "600", KICKER_PX, KICKER_SPERRUNG) : 0,
    g.unterzeile ? textBreite(g.unterzeile.map((s) => s.text).join(""), "600", UNTERZEILE_PX, UNTERZEILE_SPERRUNG) : 0,
  );

export const grafikY = (g: Grafik, frame: number): number => {
  if (!g.gleiten) return g.y;
  const p = interpolate(frame, [g.gleiten.abFrame, g.gleiten.abFrame + g.gleiten.dauer], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  return g.y + (g.gleiten.nachY - g.y) * p;
};
```

- [ ] **Step 6: Tests laufen lassen → PASS**

Run: `npx tsx --test src/clients/rappold/projects/mechatroniker/timing.test.ts src/clients/rappold/projects/mechatroniker/layout.test.ts`

---

### Task 3: Untertitel- und Grafik-Plan mit Regelprüfung

**Files:**
- Modify: `untertitel-plan.ts` (Liste `SAETZE`), `grafik-plan.ts` (Liste `GRAFIKEN`)
- Test: `src/clients/rappold/projects/mechatroniker/plan.test.ts`

**Interfaces:**
- Consumes: alles aus Task 1–2.
- Produces: gefüllte `SAETZE` (Wortindizes beziehen sich auf die korrigierten `WORTE`, 204 Stück) und `GRAFIKEN`.

- [ ] **Step 1: Regel-Test schreiben**

```ts
// src/clients/rappold/projects/mechatroniker/plan.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { GRENZE_UNTEN, KINN_ABSTAND, RAND_X, TEXT_BREITE } from "../../lib";
import { EINSTELLUNGEN, FPS, SCHNITT_FRAMES, WORTE } from "./daten-generiert";
import { DAUER_FRAMES, GRAFIKEN } from "./grafik-plan";
import { grafikBreite, grafikHoehe, grafikY, seitenOben, seitenZeilen, UT_UNTERKANTE, zeilenHoehe } from "./layout";
import { seitenFenster, sichtbareSaetze } from "./timing";
import { SAETZE } from "./untertitel-plan";

const MIN_LUECKE = 16;
const einstellungenIm = (von: number, bis: number) => EINSTELLUNGEN.filter((e) => e.von < bis && von < e.bis);

// Belegung je Frame: [oben, unten] aller sichtbaren Textblöcke
type Block = { id: string; oben: number; unten: number };
const bloeckeJeFrame = (): Map<number, Block[]> => {
  const karte = new Map<number, Block[]>();
  const add = (f: number, b: Block) => karte.set(f, [...(karte.get(f) ?? []), b]);
  for (const { satz, fenster } of sichtbareSaetze(SAETZE, WORTE, FPS)) {
    seitenFenster(satz, WORTE, fenster, FPS).forEach((sf, k) => {
      const oben = seitenOben(seitenZeilen(satz, k, WORTE));
      for (let f = sf.von; f < sf.bis; f++) add(f, { id: `${satz.id}/${k}`, oben, unten: UT_UNTERKANTE });
    });
  }
  for (const g of GRAFIKEN) {
    for (let f = g.von; f < g.bis; f++) add(f, { id: g.id, oben: grafikY(g, f), unten: grafikY(g, f) + grafikHoehe(g) });
  }
  return karte;
};

test("jedes Wort gehört genau einem Satz, Text stimmt", () => {
  let erwartet = 0;
  for (const s of SAETZE) {
    assert.equal(s.von, erwartet, `${s.id} beginnt bei ${s.von}, erwartet ${erwartet}`);
    assert.equal(WORTE.slice(s.von, s.bis + 1).map((w) => w.text).join(" "), s.text, s.id);
    erwartet = s.bis + 1;
  }
  assert.equal(erwartet, WORTE.length);
});

test("Seiten und Heroes sind gültig", () => {
  for (const s of SAETZE) {
    assert.equal(s.seiten[0], s.von, s.id);
    s.seiten.forEach((p, k) => k > 0 && assert.ok(p > s.seiten[k - 1] && p <= s.bis, s.id));
    for (const h of s.hero ?? []) {
      const seite = s.seiten.filter((p) => p <= h.von).length - 1;
      const ende = (s.seiten[seite + 1] ?? s.bis + 1) - 1;
      assert.ok(h.bis <= ende && h.von <= h.bis, `${s.id}: Hero über Seitengrenze`);
    }
    s.seiten.forEach((_, k) => {
      const z = seitenZeilen(s, k, WORTE);
      assert.ok(z.filter((l) => !l.hero).length <= 2 || z.some((l) => l.hero), `${s.id}/${k}: mehr als 2 Grundzeilen`);
      assert.ok(z.length <= 3, `${s.id}/${k}: mehr als 3 Zeilen`);
    });
  }
});

test("Kinn-Regel für Untertitel und Grafiken", () => {
  for (const [f, bloecke] of bloeckeJeFrame()) {
    if (f >= SCHNITT_FRAMES) continue;
    const e = einstellungenIm(f, f + 1)[0];
    if (e.kinnY === null) continue;
    for (const b of bloecke) assert.ok(b.oben >= e.kinnY + KINN_ABSTAND, `${b.id} @${f} (${e.id} ${e.motiv}): oben ${Math.round(b.oben)} < Kinn ${e.kinnY} + ${KINN_ABSTAND}`);
  }
});

test("Grenzen: unten, Breite, Dauer", () => {
  for (const g of GRAFIKEN) {
    assert.ok(g.von < g.bis && g.bis <= DAUER_FRAMES, g.id);
    assert.ok(Math.max(g.y, g.gleiten?.nachY ?? g.y) + grafikHoehe(g) <= GRENZE_UNTEN, `${g.id} zu tief`);
    assert.ok(grafikBreite(g) <= TEXT_BREITE, `${g.id} zu breit: ${Math.round(grafikBreite(g))}`);
  }
  assert.ok(UT_UNTERKANTE <= GRENZE_UNTEN && RAND_X >= 54);
  for (const s of SAETZE.filter((x) => !x.aus)) s.seiten.forEach((_, k) => seitenZeilen(s, k, WORTE).forEach((z) => assert.ok(zeilenHoehe(z) > 0)));
});

test("keine Überlappung gleichzeitig sichtbarer Blöcke", () => {
  for (const [f, bloecke] of bloeckeJeFrame()) {
    for (let i = 0; i < bloecke.length; i++) {
      for (let j = i + 1; j < bloecke.length; j++) {
        const [a, b] = [bloecke[i], bloecke[j]];
        const frei = a.unten + MIN_LUECKE <= b.oben || b.unten + MIN_LUECKE <= a.oben;
        assert.ok(frei, `@${f}: ${a.id} [${Math.round(a.oben)}–${Math.round(a.unten)}] ↔ ${b.id} [${Math.round(b.oben)}–${Math.round(b.unten)}]`);
      }
    }
  }
});

test("(M/W/D) an jedem Berufstitel außerhalb der Namens-Grafiken", () => {
  for (const g of GRAFIKEN.filter((x) => x.zeilen.some((z) => z.segmente.some((s) => s.text.includes("MECHATRONIKER"))))) {
    assert.ok(g.unterzeile?.some((s) => s.text === "(M/W/D)"), g.id);
  }
});

test("ausgeblendete Sätze nennen ihre Grafik", () => {
  for (const s of SAETZE.filter((x) => x.aus)) assert.ok(GRAFIKEN.some((g) => s.aus!.includes(g.id)), `${s.id}: ${s.aus}`);
});
```

- [ ] **Step 2: Test laufen lassen → FAIL** (leere Pläne: „jedes Wort gehört genau einem Satz" schlägt fehl)

Run: `npx tsx --test src/clients/rappold/projects/mechatroniker/plan.test.ts`

- [ ] **Step 3: `SAETZE` füllen** (Wortindizes = korrigierte Liste; Hook-Heroes NUMMER/ERSETZBAR/WICHTIG, VIEL PLATZ, VERSTANDEN)

```ts
export const SAETZE: Satz[] = [
  { id: "ut-01", text: "Also ich war in anderen Betrieben, da war man eine Nummer, war man ersetzbar.", von: 0, bis: 13, seiten: [0, 6, 11], hero: [{ von: 10, bis: 10, farbe: "weiss" }, { von: 13, bis: 13, farbe: "weiss" }] },
  { id: "ut-02", text: "Hier weiß man, man ist wichtig.", von: 14, bis: 19, seiten: [14], hero: [{ von: 19, bis: 19, farbe: "blau" }] },
  { id: "ut-03", text: "Ich bin der Hannes.", von: 20, bis: 23, seiten: [20], aus: "g-hannes" },
  { id: "ut-04", text: "Bin seit 2013 hier im Autohaus Rappold.", von: 24, bis: 30, seiten: [24], nachlaufSek: 0.1 },
  { id: "ut-05", text: "Ich bin Christos. Ich bin Kfz-Mechatroniker,", von: 31, bis: 36, seiten: [31], aus: "g-christos" },
  { id: "ut-06", text: "bin seit fünf Jahren beim Autohaus Rappold.", von: 37, bis: 43, seiten: [37], gross: true, nachlaufSek: 0.2 },
  { id: "ut-07", text: "Wenn ich jetzt hier morgens in die Halle reinkomme, denke ich mir: „Ja, geil, wieder am Arbeitsplatz.“", von: 44, bis: 60, seiten: [44, 53] },
  { id: "ut-08", text: "Also es ist wirklich so, ich freue mich auf die Arbeit.", von: 61, bis: 71, seiten: [61] },
  { id: "ut-09", text: "Man hat viel Platz, man kann sich ausbreiten, man hat so seinen eigenen Platz, wo man sagt: „Okay, hier arbeite ich.“", von: 72, bis: 92, seiten: [72, 80, 86], hero: [{ von: 74, bis: 75, farbe: "weiss" }] },
  { id: "ut-10", text: "Hier habe ich in einer halben Stunde ein Auto vermessen und eingestellt.", von: 93, bis: 104, seiten: [93, 100] },
  { id: "ut-11", text: "Früher dauerte es halt eine Stunde bis anderthalb.", von: 105, bis: 112, seiten: [105] },
  { id: "ut-12", text: "Und auch mit der Geschäftsleitung, wenn es da mal Probleme gibt, persönliche oder auch geschäftliche Probleme, kann man eigentlich immer hingehen und fragen, reden.", von: 113, bis: 136, seiten: [113, 118, 124, 129] },
  { id: "ut-13", text: "Man fühlt sich immer verstanden.", von: 137, bis: 141, seiten: [137], hero: [{ von: 141, bis: 141, farbe: "blau" }] },
  { id: "ut-14", text: "Da wird dir auch keine Steine in den Weg gelegt, wenn du mal zwei Stunden länger brauchst.", von: 142, bis: 158, seiten: [142, 152] },
  { id: "ut-15", text: "Mit den Leuten will ich weiterhin zusammenarbeiten, weil es hat drei Jahre super gepasst und dann weiß ich auch, dass es länger hält.", von: 159, bis: 181, seiten: [159, 166, 173] },
  { id: "ut-16", text: "Also wenn du Schrauber bist und Bock auf eine moderne Werkstatt hast, komm vorbei,", von: 182, bis: 195, seiten: [182, 187] },
  { id: "ut-17", text: "trag dich ein.", von: 196, bis: 198, seiten: [196], aus: "g-cta-eintragen" },
  { id: "ut-18", text: "Wir freuen uns auf dich.", von: 199, bis: 203, seiten: [199] },
];
```

- [ ] **Step 4: `GRAFIKEN` füllen** (Startwerte; Positionen werden in Step 5 anhand der Testmeldungen justiert)

```ts
const w = (text: string): Segment => ({ text, farbe: "weiss" });
const b = (text: string): Segment => ({ text, farbe: "blau" });

export const GRAFIKEN: Grafik[] = [
  { id: "g-seit-1911", von: 138, bis: 187, y: 1000, ausrichtung: "links", kicker: "AUTOHAUS RAPPOLD · BLAUFELDEN", zeilen: [{ segmente: [w("SEIT 1911")], px: 190 }] },
  { id: "g-hannes", von: 193, bis: 266, y: 1060, ausrichtung: "links", zeilen: [{ segmente: [w("HANNES")], px: 116 }], unterzeile: [w("KFZ-MECHATRONIKER")] },
  { id: "g-christos", von: 275, bis: 361, y: 1060, ausrichtung: "links", zeilen: [{ segmente: [w("CHRISTOS")], px: 116 }], unterzeile: [w("KFZ-MECHATRONIKER")] },
  { id: "g-frage", von: 366, bis: 396, y: 800, ausrichtung: "links", zeilen: [{ segmente: [w("WERKSTATT")], px: 150 }, { segmente: [w("WIE 1995?")], px: 150 }] },
  { id: "g-antwort", von: 396, bis: 429, y: 810, ausrichtung: "links", zeilen: [{ segmente: [w("MODERNER")], px: 120 }, { segmente: [b("ARBEITSPLATZ.")], px: 120 }] },
  { id: "g-familie", von: 1034, bis: 1083, y: 860, ausrichtung: "links", zeilen: [{ segmente: [w("FAMILIENGEFÜHRT")], px: 96 }], unterzeile: [w("RUND 30 MITARBEITENDE")] },
  { id: "g-qualitaet", von: 1085, bis: 1145, y: 800, ausrichtung: "rechts", zeilen: [{ segmente: [b("QUALITÄT")], px: 150 }, { segmente: [w("VOR QUANTITÄT")], px: 110 }] },
  { id: "g-teamgeist", von: 1252, bis: 1296, y: 830, ausrichtung: "links", zeilen: [{ segmente: [w("ECHTER")], px: 140 }, { segmente: [b("TEAMGEIST")], px: 140 }] },
  { id: "g-cta-titel", von: 1307, bis: DAUER_FRAMES, y: 850, ausrichtung: "links", kicker: "OFFENE STELLE", zeilen: [{ segmente: [w("KFZ-MECHATRONIKER")], px: 84 }], unterzeile: [b("(M/W/D)")], stehenBleiben: true, gleiten: { abFrame: 1440, nachY: 640, dauer: 14 } },
  { id: "g-cta-eintragen", von: 1395, bis: DAUER_FRAMES, y: 1110, ausrichtung: "links", zeilen: [{ segmente: [b("JETZT EINTRAGEN")], px: 104 }], stehenBleiben: true, gleiten: { abFrame: 1440, nachY: 940, dauer: 14 } },
];
```

- [ ] **Step 5: Tests laufen lassen, Meldungen beheben, bis PASS** — Kinn-Verletzungen: Grafik-`y` erhöhen oder Titel-`px` senken; Überlappung Untertitel ↔ Grafik: Grafik nach oben (nur wenn Kinn-Regel erfüllt) oder Satzfenster über `nachlaufSek`/Grafik-`von` entzerren. Nie eine Regel im Test lockern.

Run: `npx tsx --test src/clients/rappold/projects/mechatroniker/*.test.ts src/clients/rappold/metriken.test.ts`
Expected: alle PASS

---

### Task 4: Renderer, Komposition, Registrierung

**Files:**
- Create: `…/mechatroniker/Untertitel.tsx`, `Grafiken.tsx`, `Endcard.tsx`, `Composition.tsx`
- Modify: `src/Root.tsx` (Import + `<Folder name="Rappold">` vor dem schließenden Kunden-Folder)
- Assets: Proxy + Standbild in `$CHARGE/Material/Video/`, Symlink `public/projects/rappold-recruiting`, Spiegel `public-rappold`

**Interfaces:**
- Consumes: Pläne, Timing, Layout, Lib.
- Produces: Kompositionen `Rappold-V2-Mechatroniker-Vorschau` (1080×1920, Schnitt darunter) und `Rappold-V2-Mechatroniker-Alpha` (2160×3840, transparent); Props `zeigeSchnitt`, `zeigeUntertitel`, `zeigeGrafiken`, `endcardUrl`.

- [ ] **Step 1: Assets erzeugen**

```bash
CH="/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/Material/Video"
ffmpeg -v error -y -i "$CH/Video 2 - Kfz-Mechatroniker - Recruiting_V1.mp4" -c:v libx264 -crf 20 -g 25 -keyint_min 25 -sc_threshold 0 -pix_fmt yuv420p -c:a aac -b:a 128k "$CH/Video2_V1_proxy.mp4"
ffmpeg -v error -y -i "$CH/Video 2 - Kfz-Mechatroniker - Recruiting_V1.mp4" -vf "select=eq(n\,1439)" -frames:v 1 -q:v 2 "$CH/Video2_V1_letztes-bild.jpg"
ln -sfn "../../../../projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/Material/Video" public/projects/rappold-recruiting
ls -la public/projects/rappold-recruiting/
```

- [ ] **Step 2: `Untertitel.tsx`**

```tsx
// src/clients/rappold/projects/mechatroniker/Untertitel.tsx
import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BASE_W, BLAU, FONT, SCHATTEN, SCHATTEN_BLAU, WEISS } from "../../lib";
import { WORTE } from "./daten-generiert";
import { anzeigeText, HERO_SPERRUNG, seitenOben, seitenZeilen, zeilenHoehe } from "./layout";
import { AUSBLEND_FRAMES, einblendung, EINBLEND_FRAMES, HERO_FRAMES, seitenIndex, sichtbareSaetze, type Fenster } from "./timing";
import { SAETZE, type Satz } from "./untertitel-plan";

const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const PLAN = sichtbareSaetze(SAETZE, WORTE, 25);

const SatzBlock: React.FC<{ satz: Satz; fenster: Fenster }> = ({ satz, fenster }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const seite = seitenIndex(satz, WORTE, frame / fps);
  const zeilen = seitenZeilen(satz, seite, WORTE);
  const oben = seitenOben(zeilen);
  const aus = interpolate(frame, [fenster.bis - AUSBLEND_FRAMES, fenster.bis], [1, 0], CLAMP);
  return (
    <div style={{ position: "absolute", left: 0, top: oben, width: BASE_W, opacity: aus, fontFamily: FONT }}>
      {satz.abdunkeln ? (
        <div style={{ position: "absolute", left: 40, right: 40, top: -60, bottom: -60, background: `radial-gradient(closest-side, rgba(0,0,0,${satz.abdunkeln}), rgba(0,0,0,0))` }} />
      ) : null}
      {zeilen.map((z, k) => (
        <div key={k} style={{ position: "relative", height: zeilenHoehe(z), display: "flex", justifyContent: "center", alignItems: "center", whiteSpace: "nowrap" }}>
          {z.worte.map((i, n) => {
            const text = anzeigeText(WORTE, satz, i, z.hero !== null);
            const leer = n < z.worte.length - 1 ? "0.26em" : 0;
            if (z.hero) {
              const p = einblendung(WORTE[i].start, frame, fps, EINBLEND_FRAMES);
              const s = interpolate(einblendung(WORTE[z.worte[0]].start, frame, fps, HERO_FRAMES), [0, 1], [0.94, 1], { ...CLAMP, easing: EASE_OUT });
              const blau = z.hero === "blau";
              return (
                <span key={i} style={{ display: "inline-block", marginRight: leer, fontWeight: 800, fontSize: z.px, lineHeight: 1, letterSpacing: `${HERO_SPERRUNG}em`, color: blau ? BLAU : WEISS, textShadow: blau ? SCHATTEN_BLAU : SCHATTEN, opacity: p, transform: `scale(${s})` }}>
                  {text}
                </span>
              );
            }
            const p = interpolate(einblendung(WORTE[i].start, frame, fps), [0, 1], [0, 1], { ...CLAMP, easing: EASE_OUT });
            return (
              <span key={i} style={{ display: "inline-block", marginRight: leer, fontWeight: 600, fontSize: z.px, lineHeight: 1, color: WEISS, textShadow: SCHATTEN, opacity: p, transform: `translateY(${(1 - p) * 12}px)` }}>
                {text}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

export const Untertitel: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {PLAN.filter(({ fenster }) => frame >= fenster.von && frame < fenster.bis).map(({ satz, fenster }) => (
        <SatzBlock key={satz.id} satz={satz} fenster={fenster} />
      ))}
    </>
  );
};
```

- [ ] **Step 3: `Grafiken.tsx`**

```tsx
// src/clients/rappold/projects/mechatroniker/Grafiken.tsx
import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { BLAU, FONT, RAND_X, SCHATTEN, SCHATTEN_BLAU, WEISS } from "../../lib";
import { GRAFIKEN, type Grafik, type Segment, type TitelZeile } from "./grafik-plan";
import { grafikY, HERO_SPERRUNG, KICKER_ABSTAND, KICKER_PX, KICKER_SPERRUNG, LINIE_ABSTAND, LINIE_H, LINIE_W, TITEL_ZEILENHOEHE, UNTERZEILE_ABSTAND, UNTERZEILE_PX, UNTERZEILE_SPERRUNG } from "./layout";

const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const AUSSTIEG_FRAMES = 6;

const farbe = (s: Segment) => (s.farbe === "blau" ? { color: BLAU, textShadow: SCHATTEN_BLAU } : { color: WEISS, textShadow: SCHATTEN });

// Titelzeile wischt aus einer Maske hoch; nach dem Einstieg ohne Maske (Schatten nicht gekappt)
const MaskenZeile: React.FC<{ zeile: TitelZeile; start: number }> = ({ zeile, start }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, start + 10], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <div style={{ position: "relative", height: zeile.px * TITEL_ZEILENHOEHE, overflow: p < 1 ? "hidden" : "visible" }}>
      <div style={{ transform: `translateY(${(1 - p) * 110}%)`, fontWeight: 800, fontSize: zeile.px, lineHeight: TITEL_ZEILENHOEHE, letterSpacing: `${HERO_SPERRUNG}em`, whiteSpace: "nowrap" }}>
        {zeile.segmente.map((s, i) => (
          <span key={i} style={farbe(s)}>
            {s.text}
          </span>
        ))}
      </div>
    </div>
  );
};

const Titelblock: React.FC<{ g: Grafik }> = ({ g }) => {
  const frame = useCurrentFrame();
  const f = frame - g.von;
  const rechts = g.ausrichtung === "rechts";
  const linie = interpolate(f, [0, 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const kicker = interpolate(f, [2, 10], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const titelStart = g.von + (g.kicker ? 6 : 3);
  const unterStart = titelStart + g.zeilen.length * 3 + 5;
  const unter = interpolate(frame, [unterStart, unterStart + 8], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const aus = g.stehenBleiben ? 0 : interpolate(frame, [g.bis - AUSSTIEG_FRAMES, g.bis], [0, 1], { ...CLAMP, easing: Easing.in(Easing.cubic) });
  return (
    <div style={{ position: "absolute", top: grafikY(g, frame), [rechts ? "right" : "left"]: RAND_X, textAlign: rechts ? "right" : "left", fontFamily: FONT, opacity: 1 - aus, transform: `translateY(${-12 * aus}px)` }}>
      {g.abdunkeln ? <div style={{ position: "absolute", inset: "-80px -60px", background: `radial-gradient(closest-side, rgba(0,0,0,${g.abdunkeln}), rgba(0,0,0,0))` }} /> : null}
      {g.kicker ? (
        <div style={{ position: "relative", height: KICKER_PX * 1.2, marginBottom: KICKER_ABSTAND, fontWeight: 600, fontSize: KICKER_PX, lineHeight: 1.2, letterSpacing: `${KICKER_SPERRUNG}em`, color: WEISS, textShadow: SCHATTEN, whiteSpace: "nowrap", opacity: kicker, transform: `translateY(${(1 - kicker) * 10}px)` }}>
          {g.kicker}
        </div>
      ) : null}
      <div style={{ position: "relative", width: LINIE_W, height: LINIE_H, marginBottom: LINIE_ABSTAND, marginLeft: rechts ? "auto" : 0, background: BLAU, boxShadow: "0 2px 10px rgba(0,0,0,0.35)", transform: `scaleX(${linie})`, transformOrigin: rechts ? "right" : "left" }} />
      {g.zeilen.map((z, k) => (
        <MaskenZeile key={k} zeile={z} start={titelStart + k * 3} />
      ))}
      {g.unterzeile ? (
        <div style={{ position: "relative", marginTop: UNTERZEILE_ABSTAND, height: UNTERZEILE_PX * 1.25, fontWeight: 600, fontSize: UNTERZEILE_PX, lineHeight: 1.25, letterSpacing: `${UNTERZEILE_SPERRUNG}em`, whiteSpace: "nowrap", opacity: unter, transform: `translateY(${(1 - unter) * 10}px)` }}>
          {g.unterzeile.map((s, i) => (
            <span key={i} style={farbe(s)}>
              {s.text}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
};

export const Grafiken: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {GRAFIKEN.filter((g) => frame >= g.von && frame < g.bis).map((g) => (
        <Titelblock key={g.id} g={g} />
      ))}
    </>
  );
};
```

- [ ] **Step 4: `Endcard.tsx`**

```tsx
// src/clients/rappold/projects/mechatroniker/Endcard.tsx
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { BASE_H, BASE_W, FONT, RAND_X, SCHATTEN, WEISS } from "../../lib";
import { SCHNITT_FRAMES } from "./daten-generiert";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);

// Deckend ab dem Schnitt-Ende: letztes Schnittbild wird weich und dunkel, Logo + URL bauen sich auf.
// CTA-Titel und „JETZT EINTRAGEN" gleiten aus Grafiken.tsx hierher (grafik-plan: gleiten).
export const Endcard: React.FC<{ url: string }> = ({ url }) => {
  const frame = useCurrentFrame();
  if (frame < SCHNITT_FRAMES) return null;
  const f = frame - SCHNITT_FRAMES;
  const weich = interpolate(f, [0, 14], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });
  const logo = interpolate(f, [8, 22], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const link = interpolate(f, [18, 30], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <AbsoluteFill style={{ width: BASE_W, height: BASE_H, overflow: "hidden", backgroundColor: "#101212" }}>
      <Img
        src={staticFile("projects/rappold-recruiting/Video2_V1_letztes-bild.jpg")}
        style={{ position: "absolute", left: 0, top: 0, width: BASE_W, height: BASE_H, objectFit: "cover", filter: `blur(${weich * 28}px)`, transform: `scale(${1 + weich * 0.12})` }}
      />
      <AbsoluteFill style={{ backgroundColor: `rgba(12,14,14,${weich * 0.6})` }} />
      <Img
        src={staticFile("clients/rappold/rappold-logo-weiss.svg")}
        style={{ position: "absolute", left: RAND_X, top: 330, width: 560, opacity: logo, transform: `translateY(${(1 - logo) * 16}px)` }}
      />
      <div style={{ position: "absolute", left: RAND_X, top: 1086, fontFamily: FONT, fontWeight: 600, fontSize: 40, letterSpacing: "0.02em", color: WEISS, textShadow: SCHATTEN, whiteSpace: "nowrap", opacity: link, transform: `translateY(${(1 - link) * 10}px)` }}>
        {url}
      </div>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 5: `Composition.tsx`**

```tsx
// src/clients/rappold/projects/mechatroniker/Composition.tsx
// ============================================================
// Autohaus Rappold · Video 2 „Kfz-Mechatroniker" — Grafiken + Untertitel „Freie Typo"
// Spec: docs/superpowers/specs/2026-09-16-rappold-video2-animation-design.md
// Zeiten = Frames im Schnitt V1 (1440 Frames) + 5 s Endcard.
// ============================================================
import "../../fonts";
import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig } from "remotion";
import { z } from "zod";
import { ReviewOverlay } from "../../../../components/layout/ReviewOverlay";
import { getDimensions } from "../../../../core/format-utils";
import { projectPropsSchema } from "../../../../core/schemas";
import { BASE_H, BASE_W } from "../../lib";
import { SCHNITT_FRAMES } from "./daten-generiert";
import { Endcard } from "./Endcard";
import { DAUER_FRAMES } from "./grafik-plan";
import { Grafiken } from "./Grafiken";
import { Untertitel } from "./Untertitel";

export const rappoldV2Schema = projectPropsSchema.extend({
  zeigeSchnitt: z.boolean().describe("Schnitt V1 darunter (nur Vorschau)"),
  zeigeGrafiken: z.boolean().describe("Grafiken + Endcard"),
  zeigeUntertitel: z.boolean().describe("Untertitel"),
  endcardUrl: z.string().describe("URL auf der Endcard"),
});
export type RappoldV2Props = z.infer<typeof rappoldV2Schema>;

export const rappoldV2VorschauDefaults: RappoldV2Props = {
  format: "portrait",
  fps: 25,
  durationInSeconds: DAUER_FRAMES / 25,
  transparent: false,
  review: { showGuides: false, showSafeZone: true, showFaceZone: true, showGrid: false, guideOpacity: 0.35 },
  zeigeSchnitt: true,
  zeigeGrafiken: true,
  zeigeUntertitel: true,
  endcardUrl: "autohaus-rappold.de/karriere",
};

// Lieferung: EINE Alpha-Datei mit allen Grafiken + Untertiteln (wie Craiss „Alpha-Komplett")
export const rappoldV2AlphaDefaults: RappoldV2Props = { ...rappoldV2VorschauDefaults, format: "portrait-4k", transparent: true, zeigeSchnitt: false };

export const calculateRappoldV2 = ({ props }: { props: RappoldV2Props }) => ({ ...getDimensions(props.format), fps: 25, durationInFrames: DAUER_FRAMES });

export const RappoldV2Mechatroniker: React.FC<RappoldV2Props> = (p) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: p.transparent ? "transparent" : "#000" }}>
      {p.zeigeSchnitt ? (
        <Sequence durationInFrames={SCHNITT_FRAMES} name="Schnitt V1">
          <OffthreadVideo src={staticFile("projects/rappold-recruiting/Video2_V1_proxy.mp4")} style={{ width: "100%", height: "100%" }} />
        </Sequence>
      ) : null}
      <div style={{ position: "absolute", left: 0, top: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
        {p.zeigeGrafiken ? <Endcard url={p.endcardUrl} /> : null}
        {p.zeigeGrafiken ? <Grafiken /> : null}
        {p.zeigeUntertitel ? <Untertitel /> : null}
      </div>
      {p.review?.showGuides ? (
        <ReviewOverlay showSafeZone={p.review.showSafeZone} showFaceZone={p.review.showFaceZone} showGrid={p.review.showGrid} faceZone={p.review.faceZone} guideOpacity={p.review.guideOpacity} />
      ) : null}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 6: `Root.tsx` erweitern** — Import oben, Folder am Ende der Kunden-Folder (nach `Taxodia`):

```tsx
import { RappoldV2Mechatroniker, rappoldV2Schema, rappoldV2VorschauDefaults, rappoldV2AlphaDefaults, calculateRappoldV2 } from "./clients/rappold/projects/mechatroniker/Composition";
```

```tsx
        <Folder name="Rappold">
          <Composition id="Rappold-V2-Mechatroniker-Vorschau" component={RappoldV2Mechatroniker} schema={rappoldV2Schema} defaultProps={rappoldV2VorschauDefaults} calculateMetadata={calculateRappoldV2} />
          <Composition id="Rappold-V2-Mechatroniker-Alpha" component={RappoldV2Mechatroniker} schema={rappoldV2Schema} defaultProps={rappoldV2AlphaDefaults} calculateMetadata={calculateRappoldV2} />
        </Folder>
```

- [ ] **Step 7: Typprüfung**

Run: `npx tsc --noEmit 2>&1 | grep -E "rappold|Root.tsx" ; echo exit=$?`
Expected: keine Rappold-/Root-Fehler (grep ohne Treffer)

- [ ] **Step 8: Spiegel + Bundle**

```bash
rsync -a --delete --exclude='*.mov' --exclude='*.mp4' --exclude='*.wav' --exclude='projects/' public/ public-rappold/
mkdir -p public-rappold/projects/rappold-recruiting
cp "/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/Material/Video/Video2_V1_letztes-bild.jpg" public-rappold/projects/rappold-recruiting/
npx remotion bundle src/index.ts --public-dir=public-rappold --out-dir=build-rappold
```

---

### Task 5: Stil-Stills zur Freigabe (Checkpoint mit dem User)

**Files:**
- Create: `$CHARGE/_intern/animation-video-2/qa/stills.sh`
- Output: `$CHARGE/_intern/animation-video-2/qa/stills/*.png`, Kontaktbogen `qa/stil-freigabe.jpg`

- [ ] **Step 1: Stills rendern und über den Schnitt legen** (Hook-Hero, SEIT 1911, Name, Frage, Antwort, VIEL PLATZ, FAMILIENGEFÜHRT, QUALITÄT, TEAMGEIST, CTA, Endcard)

```bash
#!/bin/bash
# qa/stills.sh — Alpha-Stills (1080×1920) über Schnitt-Frames legen
set -euo pipefail
Q="$(cd "$(dirname "$0")" && pwd)"; CH="$Q/../../.."; M="/Users/jansantos/NIRO Studio/tools/motion"
V="$CH/Material/Video/Video 2 - Kfz-Mechatroniker - Recruiting_V1.mp4"
mkdir -p "$Q/stills"
FRAMES=(50 105 160 240 385 415 610 1000 1060 1110 1275 1420 1470 1540)
for F in "${FRAMES[@]}"; do
  (cd "$M" && npx remotion still build-rappold Rappold-V2-Mechatroniker-Alpha "$Q/stills/a_$F.png" --frame=$F --scale=0.5 --log=error)
  if [ "$F" -lt 1440 ]; then
    ffmpeg -v error -y -i "$V" -vf "select=eq(n\,$F)" -frames:v 1 "$Q/stills/v_$F.png"
    magick "$Q/stills/v_$F.png" "$Q/stills/a_$F.png" -composite "$Q/stills/k_$F.png"
  else
    cp "$Q/stills/a_$F.png" "$Q/stills/k_$F.png"
  fi
done
ARGS=(); for F in "${FRAMES[@]}"; do ARGS+=(-label "$F" "$Q/stills/k_$F.png"); done
montage "${ARGS[@]}" -font /System/Library/Fonts/Supplemental/Arial.ttf -pointsize 22 -tile 7x -geometry 360x640+4+4 -background "#222" -fill white "$Q/stil-freigabe.jpg"
```

Run: `bash "$CHARGE/_intern/animation-video-2/qa/stills.sh"`

- [ ] **Step 2: Kontaktbogen selbst sichten** (Lesbarkeit, Gesichter frei, Hierarchie, Doktrin §10) und offensichtliche Fehler vor der Vorlage beheben.

- [ ] **Step 3: Checkpoint** — Kontaktbogen dem User zeigen, Freigabe oder Änderungen abwarten.

---

### Task 6: Prüfung über alle Frames

**Files:**
- Create: `$CHARGE/_intern/animation-video-2/qa/gesichtscheck.py`, `qa/luma.py`
- Output: `qa/alpha/*.png` (Prüfrender 1080×1920), `qa/bericht.md`

- [ ] **Step 1: Prüfrender (PNG-Sequenz, nur Schnittbereich)**

Run: `npx remotion render build-rappold Rappold-V2-Mechatroniker-Alpha "$CHARGE/_intern/animation-video-2/qa/alpha" --sequence --image-format=png --scale=0.5 --frames=0-1439 --log=error`

- [ ] **Step 2: Gesichts-Check**

```python
# qa/gesichtscheck.py — Abstand Gesichtsbox (Vision, +12 % Kinn, +8 % seitlich) ↔ Alpha-Maske > 50 %
import glob, os, sys
import numpy as np
from PIL import Image
Q = os.path.dirname(os.path.abspath(__file__))
faces = {}
for line in open(os.path.join(Q, "../gesichter/faces_alle.tsv")):
    name, *rest = line.rstrip("\n").split("\t")
    boxes = [list(map(float, b.split(","))) for b in (rest[0] if rest else "").split(";") if b]
    faces[int(name[:5])] = [b for b in boxes if b[4] >= 0.6]
IGNORIERE = set(range(1041, 1061))  # Radnabe: VW-Deckel als Gesicht erkannt
kritisch = []
for f in range(1440):
    p = os.path.join(Q, "alpha", f"element-{f:04d}.png")
    if not os.path.exists(p) or f in IGNORIERE: continue
    a = np.array(Image.open(p).getchannel("A")) > 127
    if not a.any(): continue
    ys, xs = np.nonzero(a)
    for x0, y0, x1, y1, c in faces.get(f, []):
        w, h = x1 - x0, y1 - y0
        bx0, bx1 = max(0, (x0 - 0.08 * w) * 1080), min(1080, (x1 + 0.08 * w) * 1080)
        by0, by1 = max(0, y0 * 1920), min(1920, (y1 + 0.12 * h) * 1920)
        dx = np.maximum(np.maximum(bx0 - xs, xs - bx1), 0)
        dy = np.maximum(np.maximum(by0 - ys, ys - by1), 0)
        d = float(np.sqrt(dx * dx + dy * dy).min())
        if d < 60: kritisch.append((f, round(d), (round(bx0), round(by0), round(bx1), round(by1))))
print(f"kritische Frames: {len(kritisch)}")
for k in kritisch[:40]: print(k)
sys.exit(1 if kritisch else 0)
```

Run: `"/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" "$CHARGE/_intern/animation-video-2/qa/gesichtscheck.py"`
Expected: `kritische Frames: 0` (Dateinamen der Sequenz vorher mit `ls qa/alpha | head -2` prüfen und das Muster anpassen)

- [ ] **Step 3: Luma-Check der Textflächen**

```python
# qa/luma.py — mittlere Helligkeit des Schnitts unter jedem Textpixel-Cluster je Element-Fenster
import os, subprocess
import numpy as np
from PIL import Image
Q = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(Q, "../../../Material/Video/Video 2 - Kfz-Mechatroniker - Recruiting_V1.mp4")
os.makedirs(os.path.join(Q, "luma"), exist_ok=True)
ergebnis = []
for f in range(0, 1440, 5):
    ap = os.path.join(Q, "alpha", f"element-{f:04d}.png")
    a = np.array(Image.open(ap).getchannel("A")) > 127
    if not a.any(): continue
    vp = os.path.join(Q, "luma", f"v_{f}.png")
    if not os.path.exists(vp):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", V, "-vf", f"select=eq(n\\,{f})", "-frames:v", "1", vp], check=True)
    v = np.array(Image.open(vp).convert("L")).astype(float)
    # Bänder: zusammenhängende Zeilenbereiche mit Text
    zeilen = np.nonzero(a.any(axis=1))[0]
    baender, start = [], zeilen[0]
    for i in range(1, len(zeilen)):
        if zeilen[i] - zeilen[i - 1] > 24: baender.append((start, zeilen[i - 1])); start = zeilen[i]
    baender.append((start, zeilen[-1]))
    for y0, y1 in baender:
        m = a[y0:y1 + 1]
        umgebung = v[y0:y1 + 1][m]
        ergebnis.append((f, int(y0), int(y1), round(float(umgebung.mean())), round(float(np.percentile(umgebung, 90)))))
hell = [e for e in ergebnis if e[3] > 150 or e[4] > 210]
print(f"Bänder: {len(ergebnis)}, hell: {len(hell)}")
for e in hell: print(e)
```

Run: `"/Users/jansantos/NIRO Studio/tools/transcribe/venv/bin/python" "$CHARGE/_intern/animation-video-2/qa/luma.py"`
Expected: Liste heller Bänder → betroffene Sätze/Grafiken bekommen `abdunkeln: 0.3`, Test + Stills wiederholen.

- [ ] **Step 4: Befunde beheben**, Tests erneut (`npx tsx --test …`), Bundle neu (`npx remotion bundle …`), Schritte 1–3 wiederholen bis sauber.

---

### Task 7: Final-Render, Übergabe, Protokoll

**Files:**
- Output: `$CHARGE/Ergebnisse/Renders/Video2_Kfz-Mechatroniker_Alpha_Komplett_v1.mov`
- Modify: `$CHARGE/Protokoll.md`

- [ ] **Step 1: Guides aus prüfen** — `rappoldV2AlphaDefaults.review.showGuides === false` (Default in Composition.tsx).

- [ ] **Step 2: Render**

Run: `npx remotion render build-rappold Rappold-V2-Mechatroniker-Alpha "/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/Recruiting und Imagefilm/2026-09 Dreh 02.09/Ergebnisse/Renders/Video2_Kfz-Mechatroniker_Alpha_Komplett_v1.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`

- [ ] **Step 3: Render verifizieren** — `ffprobe` (2160×3840, 25 fps, 1565 Frames, `yuva444p12le`/Alpha vorhanden), Stichproben-Frames extrahieren und gegen die Stills vergleichen.

- [ ] **Step 4: `Protokoll.md` fortschreiben** (Datum, was animiert, Datei, CI-/Design-Entscheidungen, Wortlaut-Korrekturen, Offenes: Endcard-URL, „geil", „QUALITÄT VOR QUANTITÄT").

- [ ] **Step 5: Im Chat bilanzieren** und Ablage auf dem NAS (`03_Medien/02_Assets/07_Animation/`) anbieten — nur nach Zustimmung kopieren. Commit nur nach Freigabe.

---

## Abweichungen bei der Umsetzung (16.09.2026)

Der Code im Repo ist maßgeblich; diese Punkte weichen von den Blöcken oben ab:

- **Gesichtsregel erweitert:** Generator schreibt zusätzlich `gesichtOben` je Einstellung; Test „Gesichter frei" akzeptiert Text unter Kinn + 110 px **oder** Unterkante ≤ Stirn − 60 px (E24 Unterboden: Gesicht unten im Bild).
- **Untertitel-Unterkante je Einstellung** statt je Seite: `UT_UNTERKANTE_JE_EINSTELLUNG = { E24: 1080 }` in `untertitel-plan.ts`, `utUnterkante(frame)` und `seitenOben(zeilen, unterkante)` in `layout.ts`; Standard-Unterkante 1460 (statt 1440).
- **Umbruch mit Wortbindung:** `umbrechen` bestraft Zeilenenden nach Artikel/Präposition/Konjunktion/Zahl und Adjektiv vor Nomen, bevorzugt Satzzeichen.
- **Größen nach Stil-Stills:** Untertitel 62 px, Kicker 34 px, Unterzeile 44 px; Namen 100 px (Gesichts-Check E10/E13), `ohneLinie` für „JETZT EINTRAGEN", CTA-Seiten `[182, 187, 194]`.
- **Abdunklung** als eigener Baustein `src/clients/rappold/Abdunklung.tsx` (weich gezeichnetes Rechteck, textblockgroß) statt Radialverlauf.
- **Blaue Glyphen nur auf dunklem Grund** (Lesbarkeits-Check): ARBEITSPLATZ, VERSTANDEN, TEAMGEIST weiß; blau bleiben WICHTIG, QUALITÄT, JETZT EINTRAGEN; (M/W/D) weiß.
- **Prüfwerkzeuge:** `qa/gesichtscheck.py` liest `qa/alpha/%04d.png` (alphaextract des 1080er-Prüfrenders `qa/pruef_1080.mov`); zusätzlich `qa/lesbarkeit.py` (WCAG-Kontrast je Textzeile nach Compositing, Warnung < 3,0). Stills und Kontaktbogen entstehen aus dem Vorschau-MP4 statt aus Einzel-Stills.
- Endcard-Logo 700 px breit bei y 290, URL bei y 1100.
- **Seitenwechsel ohne Flackern:** `einblendung` startet mit 1/dauer im ersten Frame, `wortDeckkraft` lässt das erste Wort jeder Seite sofort voll stehen; Regeltest „kein Flackern" (19 Tests).
- **JETZT EINTRAGEN bei y 1215** (unter dem Rappold-Aufdruck auf Hannes' T-Shirt).
- **Export mit eingebrannten Animationen:** ffmpeg-overlay des 1080er-Alpha-Renders über den Schnitt (`tpad` 5 s, `apad`), H.264 CRF 16 + AAC 320 kbps → `Ergebnisse/Renders/` und NAS `04_Exportiert/Video 2 - Kfz-Mechatroniker - Recruiting/`.
- **Feedback-Runde 1 (16.09. mittags):** Namen und Gleit-CTA entfernt (`gleiten`, `utUnterkante` raus); CTA-Karte in `Endcard.tsx` (Anthrazit/Blau-Wisch ab `SCHNITT_FRAMES − 16`, Prop `endcardFarbe`), Karten-Grafiken `g-karte-titel`/`g-karte-eintragen` mit `linienFarbe: "weiss"`; `Satz.blau` (Wörter in Blau/800, `umbrechen` mit Schnitt je Wort), `Satz.unterkanteJeSeite` + `Satz.wechselSek` statt Lage je Einstellung; `ausblendFrames` (harter Wechsel bei direktem Anschluss); Abdunklung je Wort/Grafikzeile; neue Regeltests „springen nur auf Schnitt", „nie während Sprache ausblenden", „blaue Wörter nur auf Personen-Einstellungen" (25 Tests).

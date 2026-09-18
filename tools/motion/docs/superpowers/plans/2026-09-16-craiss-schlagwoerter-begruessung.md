# Craiss Schlagwort-Chips + Begrüßungs-Intro 03 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In allen 5 Craiss-Ads die Satz-Untertitel durch rote Schlagwort-Chips ersetzen und Video 03 ein neues Intro geben (HALLO, Begrüßung je Sprache, Flaggen-Wischer über das ganze Bild, Titel-Chip), inklusive verlängerter Begrüßungs-Montage in einer Resolve-Kopie.

**Architecture:** Phase A baut eine reine Datenebene (`schlagwoerter.ts` je Video, geprüft von `validateKeywords`) und eine Chip-Ebene aus dem vorhandenen `RedChip`; die Vorschau schaltet per `subtitleStyle` um. Phase B liest in einer Resolve-Kopie die Quell-Stellen der Begrüßungen, berechnet daraus `intro-layout.json` (einzige Wahrheit für Schnittframes und Wischer), baut die Montage in der Kopie und steuert damit die Remotion-Komponenten `GreetingIntro`/`FlagPanel`. Phase C rendert die Alpha-Dateien v2.

**Tech Stack:** Remotion 4.0.519, React 18, zod, TypeScript, Tests mit `npx tsx --test` (node:test); Python 3 im AutoCut-venv (`tools/autocut/venv/bin/python`) mit `niro_autocut.resolve_api.connect()`; DaVinci Resolve Studio 21.1 Scripting-API; ffmpeg, ImageMagick `montage`.

**Spec:** `tools/motion/docs/superpowers/specs/2026-09-16-craiss-schlagwoerter-begruessung-design.md`

## Global Constraints

- Resolve-Projekt `01_Projekt_4_Ads`; **Schreiben nur in Kopien** (Freigabe 16.09.). Jedes schreibende Skript prüft den Projektnamen und schreibt nur in Timelines, deren Name mit `Claude 03 Begrüßung` beginnt. Das Original `03_Viele_Jahre_Viele_Geschichten_V3` bleibt unberührt.
- Nie schreiben, während der User in Resolve abspielt: vor Task 5, 7, 8, 9, 14 den User im Chat fragen, ob gerade abgespielt wird; Timeline-Wechsel ankündigen. Jedes Skript setzt aktive Timeline und Media-Pool-Ordner des Users zurück.
- **Keine Commits** ohne ausdrückliche Freigabe des Users (im Repo liegen fremde, uncommittete Änderungen).
- Chip-Look = `RedChip` aus Video 05 (Laski Slab Bold 42 px, weiß auf `#CD202C`). Regeln: ≤ 32 Zeichen, Chip-Breite ≤ 972 px, Standzeit 1,5–3,5 s, ≥ 0,3 s Abstand zum nächsten Chip, kein Überlapp mit Sperrfenstern, `offsetY` = größtes `y` der überdeckten Sätze − 990.
- Wischer: Farben wie `FLAG_RECTS` in `lib.tsx`, letzter Wischer Craiss-Rot `#CD202C`; voll deckend auf `cutFrame − 1` und `cutFrame`; **eine Person wird beim Sprechen nie verdeckt** (1 Frame Puffer, bei Thomas 0).
- Remotion-Footage immer als H.264-Proxy (10-bit-HEVC seekt im Render falsch).
- Renders und Stills mit `--public-dir=public-craiss` und explizitem freiem `--port` (sporadischer Abbruch „got no response" → einfach neu starten). zsh: Flags immer ausschreiben, keine `$VAR`-Flaglisten.
- Alpha-Lieferung: ProRes 4444 mit Alpha, 2160×3840, 25 fps, Dateiname `0X_<Name>_Alpha_Komplett_v2.mov` in `Ergebnisse/Renders/` der Charge.
- Alle Befehle mit `npx` laufen in `tools/motion` (`cd "/Users/jansantos/NIRO Studio/tools/motion"`).

## Dateistruktur

| Datei | Aufgabe |
|---|---|
| `src/clients/craiss/lib.tsx` (ändern) | + `chipSchema`, `ChipProps`, `CHIP_BOX_STYLE`, `RedChip` (aus Video 05 verschoben) |
| `src/clients/craiss/projects/testimonial/Composition.tsx` (ändern) | nutzt `RedChip`/`chipSchema` aus `lib.tsx` |
| `src/clients/craiss/captionMix/keywords.ts` (neu) | Schema, Regeln (`validateKeywords`), `shiftKeywords`, `shiftBlocked` |
| `src/clients/craiss/captionMix/keywords.test.ts` (neu) | Regel-Tests |
| `src/clients/craiss/projects/<video>/schlagwoerter.ts` (neu, ×5) | `DURATION_SEC`, `BLOCKED`, `KEYWORDS` je Video (reine Daten) |
| `src/clients/craiss/captionMix/schlagwoerter-daten.test.ts` (neu) | echte Daten aller 5 Videos gegen die Regeln |
| `src/clients/craiss/KeywordChips.tsx` (neu) | `KeywordChipsLayer` (Bühne 1080×1920, je Chip eine `Sequence`) |
| `src/clients/craiss/projects/<video>/CompositionSubtitled.tsx` (ändern, ×5) | `BLOCKED`/`DURATION_SEC` aus `schlagwoerter.ts`, + `<Video>KeywordLayer` |
| `src/clients/craiss/projects/vorschau/Composition.tsx` (ändern) | `subtitleStyle: "schlagwort" \| "neu" \| "alt"`, 03 auf neuen Schnitt |
| `scripts/craiss-chip-kontaktbogen.ts` (neu) | Kontaktbogen je Chip aus einem Vorschau-Render |
| `src/clients/craiss/intro/wipeTiming.ts` + `.test.ts` (neu) | Layout-Schema, `wipeOffset`, `greetingIndexAt` |
| `src/clients/craiss/intro/FlagWipe.tsx` (neu) | `FlagPanel` (Vollbild-Flagge je Land) |
| `src/clients/craiss/intro/GreetingIntro.tsx` (neu) | Wischer-Folge + HALLO + Begrüßungs-Chip |
| `src/clients/craiss/projects/viele-jahre/intro-layout.json` (erzeugt) | Schnittframes, Wischer, Shots, Titel-Chip |
| `src/clients/craiss/projects/viele-jahre/Composition.tsx` (ändern) | Hook → Intro + Titel-Chip, alle Zeiten + D, neuer Footage-Proxy |
| `scripts/craiss-intro-kontaktbogen.ts` (neu) | Einzelbilder rund um jeden Wischer |
| `projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/rk_common.py` (neu) | Verbindung, Projekt-/Kopie-Prüfung, User-Zustand, `stand.json` |
| `…/_intern/resolve/r1_kopie_export.py` … `r8_alpha_einsetzen.py` (neu) | Resolve-Schritte 1–8 |

---

## Phase A — Schlagwort-Chips (01–05)

### Task 1: `RedChip` nach `lib.tsx` verschieben

**Files:**
- Modify: `tools/motion/src/clients/craiss/lib.tsx` (am Dateiende anhängen)
- Modify: `tools/motion/src/clients/craiss/projects/testimonial/Composition.tsx` (lokales `chipSchema` Z. 51–56 und Block „Roter Text-Chip" Z. 151–206 löschen, Import ergänzen)
- Test: Still-Vergleich vorher/nachher

**Interfaces:**
- Produces: `export const chipSchema` (zod `{ text, startSec, endSec, offsetY }`), `export type ChipProps`, `export const CHIP_BOX_STYLE: React.CSSProperties`, `export const RedChip: React.FC<{ chip: ChipProps }>` — Zeit 0 = Beginn der umgebenden `Sequence`, Position `top: 990 + offsetY` in der 1080×1920-Bühne.

- [ ] **Step 1: Referenz-Still vor der Änderung**

```bash
mkdir -p "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review"
npx remotion still src/index.ts Craiss-Testimonial "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/redchip-vorher.png" --frame=110 --public-dir=public-craiss --port=3144
```
Expected: PNG geschrieben (Frame 110 = 4,4 s, Chip „JEDER TAG IST EIN GUTER TAG." sichtbar).

- [ ] **Step 2: `RedChip` in `lib.tsx` anhängen**

```tsx
// =============================================================
// RedChip — roter Text-Chip (Zitate Video 05, Schlagwörter 01–05,
// Begrüßung/Titel Video 03). Ruhig: SOFT-Feder nur auf Skalierung,
// Deckkraft linear. Zeit 0 = Beginn der umgebenden Sequence.
// =============================================================

export const chipSchema = z.object({
  text: z.string().describe("Text"),
  startSec: z.number().step(0.04).describe("Start (Sek)"),
  endSec: z.number().step(0.04).describe("Ende inkl. Ausblenden (Sek)"),
  offsetY: z.number().step(1).describe("Y-Offset (px, Basis 1920)"),
});

export type ChipProps = z.infer<typeof chipSchema>;

export const CHIP_BOX_STYLE: React.CSSProperties = {
  backgroundColor: RED,
  borderRadius: 6,
  padding: "14px 34px",
  fontFamily: FONT_BOLD,
  fontSize: 42,
  letterSpacing: 2,
  color: WHITE,
  textTransform: "uppercase",
  whiteSpace: "nowrap",
  boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
};

export const RedChip: React.FC<{ chip: ChipProps }> = ({ chip }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const F = (sec: number) => Math.round(sec * fps);
  const durFrames = F(chip.endSec - chip.startSec);

  const inP = spring({ frame, fps, config: SOFT });
  const scale = interpolate(inP, [0, 1], [0.95, 1]);
  const inOp = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outOp = interpolate(frame, [durFrames - F(0.32), durFrames - 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const op = inOp * outOp;
  if (op <= 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 990 + chip.offsetY,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div style={{ ...CHIP_BOX_STYLE, opacity: op, transform: `scale(${scale})` }}>{chip.text}</div>
    </div>
  );
};
```

- [ ] **Step 3: Video 05 umstellen**

In `projects/testimonial/Composition.tsx`: den Block `const chipSchema = z.object({ … });` (Z. 51–56) und den ganzen Abschnitt `// Roter Text-Chip (Hook / Zitate) — kompakt, Lower-Third` bis zum Ende von `const RedChip …` (Z. 151–206) löschen. Im Import aus `"../../lib"` `RedChip,` und `chipSchema,` ergänzen. Die Verwendung `<RedChip chip={chip} />` und `z.array(chipSchema)` bleiben unverändert.

- [ ] **Step 4: Typen prüfen**

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 5: Still nach der Änderung vergleichen**

```bash
npx remotion still src/index.ts Craiss-Testimonial "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/redchip-nachher.png" --frame=110 --public-dir=public-craiss --port=3144
magick compare -metric AE "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/redchip-vorher.png" "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/redchip-nachher.png" null: 2>&1
```
Expected: `0` (pixelgleich).

---

### Task 2: Schlagwort-Regeln `keywords.ts` (TDD)

**Files:**
- Create: `tools/motion/src/clients/craiss/captionMix/keywords.ts`
- Test: `tools/motion/src/clients/craiss/captionMix/keywords.test.ts`

**Interfaces:**
- Consumes: `type BlockedRange = { startSec: number; durationSec: number }` aus `src/clients/craiss/Subtitles.tsx`.
- Produces: `keywordSchema`, `type Keyword = { text: string; startSec: number; endSec: number; offsetY: number }`, `KEYWORD_MAX_CHARS = 32`, `KEYWORD_MIN_SEC = 1.5`, `KEYWORD_MAX_SEC = 3.5`, `KEYWORD_MIN_GAP_SEC = 0.3`, `validateKeywords(list: Keyword[], blocked: BlockedRange[]): string[]`, `shiftKeywords(list: Keyword[], sec: number): Keyword[]`, `shiftBlocked(list: BlockedRange[], sec: number): BlockedRange[]`.

- [ ] **Step 1: Failing Tests schreiben**

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { shiftBlocked, shiftKeywords, validateKeywords, type Keyword } from "./keywords";

const kw = (over: Partial<Keyword>): Keyword => ({ text: "KINDERLEICHT", startSec: 5, endSec: 7, offsetY: 160, ...over });

test("gültige Liste hat keine Fehler", () => {
  assert.deepEqual(validateKeywords([kw({}), kw({ text: "NUR 10 MINUTEN", startSec: 7.3, endSec: 9 })], []), []);
});

test("zu langer Text", () => {
  const errs = validateKeywords([kw({ text: "X".repeat(33) })], []);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /33 Zeichen/);
});

test("Dauer unter 1,5 s und über 3,5 s", () => {
  assert.match(validateKeywords([kw({ endSec: 6.4 })], [])[0], /Dauer 1\.40/);
  assert.match(validateKeywords([kw({ endSec: 8.6 })], [])[0], /Dauer 3\.60/);
});

test("Grenzwerte 1,5 s und 3,5 s sind erlaubt", () => {
  assert.deepEqual(validateKeywords([kw({ endSec: 6.5 })], []), []);
  assert.deepEqual(validateKeywords([kw({ endSec: 8.5 })], []), []);
});

test("Abstand unter 0,3 s zum vorigen Chip", () => {
  const errs = validateKeywords([kw({}), kw({ text: "B", startSec: 7.2, endSec: 9 })], []);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /Abstand/);
});

test("Überlapp mit Sperrfenster", () => {
  const errs = validateKeywords([kw({})], [{ startSec: 6.5, durationSec: 2 }]);
  assert.equal(errs.length, 1);
  assert.match(errs[0], /Sperrfenster 6\.50–8\.50/);
});

test("Chip, der genau am Sperrfenster endet, ist erlaubt", () => {
  assert.deepEqual(validateKeywords([kw({})], [{ startSec: 7, durationSec: 1 }]), []);
});

test("shiftKeywords und shiftBlocked verschieben auf 2 Nachkommastellen", () => {
  assert.deepEqual(shiftKeywords([kw({ startSec: 12.86, endSec: 16.36 })], 1.36), [kw({ startSec: 14.22, endSec: 17.72 })]);
  assert.deepEqual(shiftBlocked([{ startSec: 7.84, durationSec: 3.76 }], 1.36), [{ startSec: 9.2, durationSec: 3.76 }]);
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `npx tsx --test src/clients/craiss/captionMix/keywords.test.ts`
Expected: FAIL („Cannot find module './keywords'").

- [ ] **Step 3: Implementierung**

```ts
// ============================================================
// Craiss Schlagwort-Chips — Schema und Prüfregeln
// Spec: docs/superpowers/specs/2026-09-16-craiss-schlagwoerter-begruessung-design.md
// ============================================================
import { z } from "zod";
import type { BlockedRange } from "../Subtitles";

export const KEYWORD_MAX_CHARS = 32;
export const KEYWORD_MIN_SEC = 1.5;
export const KEYWORD_MAX_SEC = 3.5;
export const KEYWORD_MIN_GAP_SEC = 0.3;
const EPS = 0.005;

export const keywordSchema = z.object({
  text: z.string(),
  startSec: z.number(),
  endSec: z.number(),
  offsetY: z.number(),
});

export type Keyword = z.infer<typeof keywordSchema>;

const r2 = (v: number) => Math.round(v * 100) / 100;

export const shiftKeywords = (list: Keyword[], sec: number): Keyword[] =>
  list.map((k) => ({ ...k, startSec: r2(k.startSec + sec), endSec: r2(k.endSec + sec) }));

export const shiftBlocked = (list: BlockedRange[], sec: number): BlockedRange[] =>
  list.map((b) => ({ ...b, startSec: r2(b.startSec + sec) }));

export const validateKeywords = (list: Keyword[], blocked: BlockedRange[]): string[] => {
  const errors: string[] = [];
  list.forEach((k, i) => {
    const name = `„${k.text}"`;
    const chars = [...k.text].length;
    if (chars > KEYWORD_MAX_CHARS) errors.push(`${name}: ${chars} Zeichen > ${KEYWORD_MAX_CHARS}`);
    const dur = k.endSec - k.startSec;
    if (dur < KEYWORD_MIN_SEC - EPS || dur > KEYWORD_MAX_SEC + EPS) {
      errors.push(`${name}: Dauer ${dur.toFixed(2)} s außerhalb ${KEYWORD_MIN_SEC}–${KEYWORD_MAX_SEC} s`);
    }
    const prev = list[i - 1];
    if (prev && k.startSec < prev.endSec + KEYWORD_MIN_GAP_SEC - EPS) {
      errors.push(`${name}: Abstand zu „${prev.text}" < ${KEYWORD_MIN_GAP_SEC} s`);
    }
    for (const b of blocked) {
      const bEnd = b.startSec + b.durationSec;
      if (k.startSec < bEnd - EPS && k.endSec > b.startSec + EPS) {
        errors.push(`${name}: überlappt Sperrfenster ${b.startSec.toFixed(2)}–${bEnd.toFixed(2)} s`);
      }
    }
  });
  return errors;
};
```

- [ ] **Step 4: Tests laufen lassen**

Run: `npx tsx --test src/clients/craiss/captionMix/keywords.test.ts`
Expected: PASS (8 Tests).

---

### Task 3: Schlagwort-Daten je Video

**Files:**
- Create: `tools/motion/src/clients/craiss/projects/erster-tag/schlagwoerter.ts`
- Create: `tools/motion/src/clients/craiss/projects/arbeitsalltag/schlagwoerter.ts`
- Create: `tools/motion/src/clients/craiss/projects/viele-jahre/schlagwoerter.ts`
- Create: `tools/motion/src/clients/craiss/projects/funnel/schlagwoerter.ts`
- Create: `tools/motion/src/clients/craiss/projects/testimonial/schlagwoerter.ts`
- Test: `tools/motion/src/clients/craiss/captionMix/schlagwoerter-daten.test.ts`

**Interfaces:**
- Consumes: `Keyword`, `validateKeywords` (Task 2); `BlockedRange`.
- Produces je Video: `DURATION_SEC: number`, `BLOCKED: BlockedRange[]`, `KEYWORDS: Keyword[]`; zusätzlich in `viele-jahre`: `DURATION_SEC_V3 = 51.6`, `BLOCKED_V3`, `KEYWORDS_V3` (Zeiten des V3-Schnitts; Phase A: `BLOCKED = BLOCKED_V3`, `KEYWORDS = KEYWORDS_V3`).

Werte: Start = Wortanfang des Ankerworts aus `captions/<id>.plan.json`, Ende nach den Regeln (Satzende, bei kurzen Sätzen bis +1,0 s, gekappt bei 3,5 s, vor dem nächsten Chip/Sperrfenster). Berechnet am 16.09. aus den Plänen.

- [ ] **Step 1: Daten-Test schreiben**

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { validateKeywords } from "./keywords";
import * as v01 from "../projects/erster-tag/schlagwoerter";
import * as v02 from "../projects/arbeitsalltag/schlagwoerter";
import * as v03 from "../projects/viele-jahre/schlagwoerter";
import * as v04 from "../projects/funnel/schlagwoerter";
import * as v05 from "../projects/testimonial/schlagwoerter";

const VIDEOS = { "01": v01, "02": v02, "03": v03, "04": v04, "05": v05 };

for (const [id, v] of Object.entries(VIDEOS)) {
  test(`Schlagwörter ${id} halten die Regeln`, () => {
    assert.deepEqual(validateKeywords(v.KEYWORDS, v.BLOCKED), []);
  });
}

test("Anzahl Chips wie freigegeben (3/6/6/4/3)", () => {
  assert.deepEqual(
    Object.values(VIDEOS).map((v) => v.KEYWORDS.length),
    [3, 6, 6, 4, 3],
  );
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `npx tsx --test src/clients/craiss/captionMix/schlagwoerter-daten.test.ts`
Expected: FAIL (Module fehlen).

- [ ] **Step 3: `erster-tag/schlagwoerter.ts`**

```ts
// Schlagwort-Chips Video 01 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/erster-tag-v3.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 29.6;
const CTA_START = 24.32;

// Hook (0,24–3,6 s) und CTA (ab 24,32 s) wie in Craiss-ErsterTag
export const BLOCKED: BlockedRange[] = [
  { startSec: 0.24, durationSec: 3.6 - 0.24 },
  { startSec: CTA_START, durationSec: DURATION_SEC - CTA_START },
];

export const KEYWORDS: Keyword[] = [
  { text: "KINDERLEICHT – FÜR JUNG UND ALT", startSec: 8.5, endSec: 11.73, offsetY: 190 }, // „kinderleicht" · cc-02 + cc-03 (y 900/1180)
  { text: "WIR WEISEN DICH EIN", startSec: 14.02, endSec: 16.47, offsetY: 240 }, // „eingewiesen" · cc-05
  { text: "FRAGEN? EINFACH ANRUFEN.", startSec: 16.9, endSec: 19.84, offsetY: 260 }, // „Fragen" · cc-06
];
```

- [ ] **Step 4: `arbeitsalltag/schlagwoerter.ts`**

```ts
// Schlagwort-Chips Video 02 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/arbeitsalltag-v3.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 74.08; // Neuexport 11.09. 18:42: 1853 Frames (Endshot +1s)

export const BLOCKED: BlockedRange[] = [
  { startSec: 0, durationSec: 3.0 }, // Hook „MEIN ARBEITSALLTAG / BEI CRAISS"
  { startSec: 61.6, durationSec: DURATION_SEC - 61.6 }, // CTA
];

export const KEYWORDS: Keyword[] = [
  { text: "JEDEN TAG ZU HAUSE", startSec: 6.74, endSec: 10.0, offsetY: 110 }, // „jeden" · cc-02
  { text: "NAH- UND FERNVERKEHR", startSec: 11.54, endSec: 13.04, offsetY: 210 }, // „Nah-" · cc-03
  { text: "ALLE INFOS PER TABLET", startSec: 21.18, endSec: 24.68, offsetY: 160 }, // „Tablet" · cc-05
  { text: "NEUER, SCHÖNER LKW", startSec: 30.82, endSec: 33.3, offsetY: 190 }, // „neu" · cc-06 + „Schöner Lkw." (y 1150/1180)
  { text: "WERKSTATT: NUR 10 MINUTEN", startSec: 44.06, endSec: 46.82, offsetY: 190 }, // „zehn" · cc-09
  { text: "24/7 ERREICHBAR", startSec: 48.12, endSec: 51.62, offsetY: 190 }, // „24/7" · cc-10
];
```

- [ ] **Step 5: `viele-jahre/schlagwoerter.ts` (Stand V3-Schnitt)**

```ts
// Schlagwort-Chips Video 03 + Sperrfenster (Spec 2026-09-16).
// *_V3 = Zeiten des Kunden-Schnitts V3 (Mix-Plan captions/viele-jahre-v3.plan.json).
// BLOCKED/KEYWORDS = Zeiten des aktuell gelieferten Schnitts (Phase B: + Verlängerung D).
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC_V3 = 51.6;

export const BLOCKED_V3: BlockedRange[] = [
  { startSec: 0, durationSec: 2.72 }, // Hook „VIELE JAHRE / VIELE GESCHICHTEN" (Overlay 0,24–2,72)
  { startSec: 7.84, durationSec: 3.76 }, // Laender-Flaggen (Overlay 7,84–11,6)
  { startSec: 46.64, durationSec: DURATION_SEC_V3 - 46.64 }, // CTA (Overlay ab 46,64)
];

export const KEYWORDS_V3: Keyword[] = [
  { text: "FRÜHER SELBST KEIN DEUTSCH", startSec: 12.86, endSec: 16.36, offsetY: 160 }, // „früher" · cc-08
  { text: "KOMMUNIKATION? KEIN PROBLEM.", startSec: 25.24, endSec: 26.8, offsetY: 210 }, // „kein" · cc-10
  { text: "RESPEKTVOLL UND LERNBEREIT", startSec: 28.52, endSec: 30.8, offsetY: 110 }, // „respektvoll" · cc-11
  { text: "ÜBER 50 JAHRE BEI CRAISS", startSec: 32.5, endSec: 34.82, offsetY: 160 }, // „Fünfzig" · cc-13
  { text: "TROTZ RENTE AM STEUER", startSec: 36.24, endSec: 39.74, offsetY: 160 }, // „Rente" · cc-14
  { text: "DU BIST KEINE ZAHL.", startSec: 44.24, endSec: 45.74, offsetY: 190 }, // „Du" · cc-16
];

export const DURATION_SEC = DURATION_SEC_V3;
export const BLOCKED = BLOCKED_V3;
export const KEYWORDS = KEYWORDS_V3;
```

- [ ] **Step 6: `funnel/schlagwoerter.ts`**

```ts
// Schlagwort-Chips Video 04 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/funnel-v4.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 59.08;

export const BLOCKED: BlockedRange[] = [
  // 2026-09-11 exakt = Sequenzen von Craiss-Funnel (auf V4 ausgerichtet, per
  // Differenz animiert − ohne Animation bestätigt). Dauern als Literale, damit
  // Math.floor in freeWindows nicht an Rundungsresten einen Frame verliert.
  { startSec: 0.64, durationSec: 2.48 }, // Chef-Namenskarte "MICHAEL CRAISS"
  { startSec: 5.24, durationSec: 1.4 }, // Standort-Chip "MUEHLACKER"
  { startSec: 21.0, durationSec: 1.68 }, // Swipe-Transition
  { startSec: 23.76, durationSec: 3.56 }, // Namenskarte "EVA"
  { startSec: 32.48, durationSec: 3.04 }, // "KEIN LEBENSLAUF / KEIN ANSCHREIBEN"
  { startSec: 35.72, durationSec: 1.36 }, // Schritt 1 "TRAG DICH EIN"
  { startSec: 37.08, durationSec: 2.44 }, // Schritt 2 "TELEFONAT"
  { startSec: 39.56, durationSec: 3.96 }, // Phone-Chip "SEI ERREICHBAR"
  { startSec: 46.88, durationSec: 2.44 }, // Schritt 3 "PERSÖNLICHES KENNENLERNEN"
  { startSec: 50.32, durationSec: 2.6 }, // Outro "WORAUF WARTEST DU?"
  { startSec: 54.72, durationSec: DURATION_SEC - 54.72 }, // CTA
];

export const KEYWORDS: Keyword[] = [
  { text: "FAMILIENUNTERNEHMEN", startSec: 6.68, endSec: 8.18, offsetY: 160 }, // „Familienunternehmen" · cc-03 (nach Mühlacker-Chip)
  { text: "KEIN 08/15-JOB", startSec: 14.7, endSec: 16.46, offsetY: 160 }, // „0815-Arbeitsverhältnis" · cc-04ba
  { text: "BEI UNS ANKOMMEN", startSec: 17.56, endSec: 19.41, offsetY: 160 }, // „schauen" · cc-04bb
  { text: "SO EINFACH STARTEST DU", startSec: 30.1, endSec: 32.22, offsetY: 190 }, // „starten" · cc-08a
];
```

- [ ] **Step 7: `testimonial/schlagwoerter.ts`**

```ts
// Schlagwort-Chips Video 05 + Sperrfenster (Spec 2026-09-16).
// Start = Wortanfang des Ankerworts (captions/testimonial-v2.plan.json),
// offsetY = größtes y der überdeckten Sätze − 990.
import type { BlockedRange } from "../../Subtitles";
import type { Keyword } from "../../captionMix/keywords";

export const DURATION_SEC = 52.56; // Neuexport 11.09. 18:46: 1315 Frames

export const BLOCKED: BlockedRange[] = [
  // 2026-09-11: Mix-Look zeigt nur ganze Sätze → Sperren exakt = Sequenzen von
  // Craiss-Testimonial v3 (Hook, Chips, Flaggen, CTA; Dauern als Literale).
  { startSec: 0, durationSec: 2.28 }, // Hook „ICH MAG MEINE ARBEIT / LKW-FAHRER BEI CRAISS"
  { startSec: 3.32, durationSec: 2.48 }, // Zitat „JEDER TAG IST EIN GUTER TAG."
  { startSec: 6.88, durationSec: 1.92 }, // Zitat „DIE FREIHEIT. DIE RUHE."
  // „KEIN STRESS." entfaellt ab Overlay v3 (Kundenfeedback) — kein Sperrfenster.
  // ab 16,96s −0,52s (Neuexport 18:46 ohne „Kein Stress")
  { startSec: 28.44, durationSec: 1.88 }, // Zitat „JEDEN TAG ZU HAUSE."
  { startSec: 34.88, durationSec: 1.72 }, // Zitat „BEI CRAISS PASST'S."
  { startSec: 39.64, durationSec: 3.88 }, // Laender-Flaggen (HU/CZ/RO/LT)
  { startSec: 46.12, durationSec: DURATION_SEC - 46.12 }, // CTA auf dem Drohnen-Endshot
];

export const KEYWORDS: Keyword[] = [
  { text: "KINDHEITSTRAUM LKW", startSec: 10.94, endSec: 12.84, offsetY: 160 }, // „Bei (Kleine)" · cc-04a (Adrian)
  { text: "WERKSTATT: NUR 10 MINUTEN", startSec: 20.52, endSec: 22.02, offsetY: 160 }, // „zehn" · cc-05 (Jakub)
  { text: "TROTZ RENTE AM STEUER", startSec: 32.68, endSec: 34.84, offsetY: 190 }, // „Rente" · cc-08 (Opa Didi)
];
```

- [ ] **Step 8: Tests laufen lassen**

Run: `npx tsx --test src/clients/craiss/captionMix/keywords.test.ts src/clients/craiss/captionMix/schlagwoerter-daten.test.ts`
Expected: PASS (8 + 6 Tests).

- [ ] **Step 9: `CompositionSubtitled.tsx` auf die Daten umstellen (×5)**

- `erster-tag/CompositionSubtitled.tsx`: die Konstanten `HOOK_BLOCK`, `DURATION_SEC`, `CTA_START`, `CTA_BLOCK` (Z. 40–45) löschen; `import { BLOCKED, DURATION_SEC } from "./schlagwoerter";` ergänzen; beide Vorkommen `[HOOK_BLOCK, CTA_BLOCK]` durch `BLOCKED` ersetzen.
- `arbeitsalltag/`, `funnel/`, `testimonial/CompositionSubtitled.tsx`: die Zeile `const DURATION_SEC = …;` und den Block `export const BLOCKED: BlockedRange[] = [ … ];` samt den Kommentarzeilen direkt darüber löschen; `import { BLOCKED, DURATION_SEC } from "./schlagwoerter";` ergänzen. (`BLOCKED` wird sonst nirgends importiert — `scripts/craiss-captions.ts` erwähnt es nur im Kommentar.)
- `viele-jahre/CompositionSubtitled.tsx`: `const DURATION_SEC = 51.6;` und den `BLOCKED`-Block löschen; `import { BLOCKED_V3, DURATION_SEC_V3 } from "./schlagwoerter";`; `DURATION_SEC` → `DURATION_SEC_V3` (Defaults) und `blocked={BLOCKED}` → `blocked={BLOCKED_V3}` (Mix- und Leisten-Ebene).

Run: `npx tsc --noEmit`
Expected: keine Fehler.

---

### Task 4: Chip-Ebene, Vorschau-Umschalter, Kontaktbögen 01/02/04/05

**Files:**
- Create: `tools/motion/src/clients/craiss/KeywordChips.tsx`
- Modify: 5× `projects/<video>/CompositionSubtitled.tsx` (+ `<Video>KeywordLayer`)
- Modify: `tools/motion/src/clients/craiss/projects/vorschau/Composition.tsx`
- Create: `tools/motion/scripts/craiss-chip-kontaktbogen.ts`

**Interfaces:**
- Consumes: `RedChip`, `BASE_W`, `BASE_H` (lib), `Keyword`, `KEYWORDS` je Video.
- Produces: `KeywordChipsLayer: React.FC<{ keywords: Keyword[] }>`; `CraissErsterTagKeywordLayer`, `CraissArbeitsalltagKeywordLayer`, `CraissVieleJahreKeywordLayer`, `CraissFunnelKeywordLayer`, `CraissTestimonialKeywordLayer` (je `React.FC`); `craissVorschauSchema.subtitleStyle: "schlagwort" | "neu" | "alt"` (Standard `"schlagwort"`).

- [ ] **Step 1: `KeywordChips.tsx`**

```tsx
// ============================================================
// Craiss Schlagwort-Chips — Ebene über dem Schnitt (Spec 2026-09-16).
// Ersetzt in der Lieferung die Satz-Untertitel; je Chip eine Sequence.
// ============================================================
import React from "react";
import { Sequence, useVideoConfig } from "remotion";
import { BASE_H, BASE_W, RedChip } from "./lib";
import type { Keyword } from "./captionMix/keywords";

export const KeywordChipsLayer: React.FC<{ keywords: Keyword[] }> = ({ keywords }) => {
  const { fps, width } = useVideoConfig();
  const f = (sec: number) => Math.round(sec * fps);
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: BASE_W,
        height: BASE_H,
        transform: `scale(${width / BASE_W})`,
        transformOrigin: "top left",
      }}
    >
      {keywords.map((k) => (
        <Sequence key={`${k.text}-${k.startSec}`} from={f(k.startSec)} durationInFrames={f(k.endSec) - f(k.startSec)} name={`Schlagwort: ${k.text}`}>
          <RedChip chip={k} />
        </Sequence>
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Ebene je Video exportieren**

In jeder der 5 `CompositionSubtitled.tsx` nach den Importen ergänzen (Komponentenname je Video: `CraissErsterTagKeywordLayer`, `CraissArbeitsalltagKeywordLayer`, `CraissVieleJahreKeywordLayer`, `CraissFunnelKeywordLayer`, `CraissTestimonialKeywordLayer`):

```tsx
import { KeywordChipsLayer } from "../../KeywordChips";
import { KEYWORDS } from "./schlagwoerter";

// Schlagwort-Chips (Spec 2026-09-16) — ersetzen in der Lieferung die Satz-Untertitel
export const CraissErsterTagKeywordLayer: React.FC = () => <KeywordChipsLayer keywords={KEYWORDS} />;
```

- [ ] **Step 3: Vorschau umstellen**

In `projects/vorschau/Composition.tsx`:

```tsx
// Importe je Video um die KeywordLayer erweitern, z. B.:
import { CraissErsterTagKeywordLayer, CraissErsterTagMixLayer, CraissErsterTagSubtitleLayer } from "../erster-tag/CompositionSubtitled";
// (analog Arbeitsalltag, VieleJahre, Funnel, Testimonial)

// Schema:
  subtitleStyle: z
    .enum(["schlagwort", "neu", "alt"])
    .describe("Untertitel-Look (schlagwort = Chips 16.09., neu = Mix 11.09., alt = Leiste 07.09.)"),

// VIDEOS-Typ:
  { src: string; seconds: number; Overlay: React.FC; Subs: React.FC; MixSubs?: React.FC; KeywordSubs: React.FC }

// je Eintrag ergänzen:
    KeywordSubs: CraissErsterTagKeywordLayer, // "01"
    KeywordSubs: CraissArbeitsalltagKeywordLayer, // "02"
    KeywordSubs: CraissVieleJahreKeywordLayer, // "03"
    KeywordSubs: CraissFunnelKeywordLayer, // "04"
    KeywordSubs: CraissTestimonialKeywordLayer, // "05"

// Defaults:
  subtitleStyle: "schlagwort" as const,

// Rendern (ersetzt die bisherige Untertitel-Zeile):
      {showSubtitles &&
        (subtitleStyle === "schlagwort" ? (
          <v.KeywordSubs />
        ) : subtitleStyle === "neu" && v.MixSubs ? (
          <v.MixSubs />
        ) : (
          <v.Subs />
        ))}
```

Run: `npx tsc --noEmit`
Expected: keine Fehler.

- [ ] **Step 4: Kontaktbogen-Skript**

`scripts/craiss-chip-kontaktbogen.ts`:

```ts
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
```

- [ ] **Step 5: Prüf-Renders mit Guides (halbe Größe) und Kontaktbögen**

```bash
npx remotion render src/index.ts Craiss-Vorschau-01-ErsterTag "../../projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/_intern/review/01_schlagwoerter_guides.mp4" --codec=h264 --crf=23 --scale=0.5 --public-dir=public-craiss --port=3145 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
npx tsx scripts/craiss-chip-kontaktbogen.ts 01 "../../projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/_intern/review/01_schlagwoerter_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/_intern/review/01_schlagwoerter_kontakt.jpg"
npx remotion render src/index.ts Craiss-Vorschau-02-Arbeitsalltag "../../projects/Craiss Logistik/4 Ads/2026-08 Einblick Arbeitsalltag/_intern/review/02_schlagwoerter_guides.mp4" --codec=h264 --crf=23 --scale=0.5 --public-dir=public-craiss --port=3146 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
npx tsx scripts/craiss-chip-kontaktbogen.ts 02 "../../projects/Craiss Logistik/4 Ads/2026-08 Einblick Arbeitsalltag/_intern/review/02_schlagwoerter_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Einblick Arbeitsalltag/_intern/review/02_schlagwoerter_kontakt.jpg"
npx remotion render src/index.ts Craiss-Vorschau-04-Funnel "../../projects/Craiss Logistik/4 Ads/2026-08 Funnel Video/_intern/review/04_schlagwoerter_guides.mp4" --codec=h264 --crf=23 --scale=0.5 --public-dir=public-craiss --port=3147 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
npx tsx scripts/craiss-chip-kontaktbogen.ts 04 "../../projects/Craiss Logistik/4 Ads/2026-08 Funnel Video/_intern/review/04_schlagwoerter_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Funnel Video/_intern/review/04_schlagwoerter_kontakt.jpg"
npx remotion render src/index.ts Craiss-Vorschau-05-Testimonial "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/05_schlagwoerter_guides.mp4" --codec=h264 --crf=23 --scale=0.5 --public-dir=public-craiss --port=3148 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
npx tsx scripts/craiss-chip-kontaktbogen.ts 05 "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/05_schlagwoerter_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/_intern/review/05_schlagwoerter_kontakt.jpg"
```
Expected: 4 Kontaktbögen. Mit dem Read-Tool ansehen und für jeden Chip prüfen: Gesicht/Hals frei (rote Face-Zone nicht berührt), innerhalb der grünen Safe Zone, Chip einzeilig und nicht angeschnitten, keine Überschneidung mit Zitat-Chips, Schritten, Namenskarten oder Flaggen. Verstößt ein Chip: `offsetY` in `schlagwoerter.ts` in 10-px-Schritten anpassen (tiefer = größer, Unterkante ≤ 1500 px), Tests aus Task 3 Step 8 erneut laufen lassen, Render + Kontaktbogen wiederholen.

---

## Phase B — Intro Video 03

Alle Python-Skripte liegen in `projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/` und laufen mit
`"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "<Skriptpfad>"` (Resolve muss laufen, Projekt `01_Projekt_4_Ads` offen, „External scripting = Local").

### Task 5: Resolve-Kopie anlegen und exportieren

**Files:**
- Create: `…/_intern/resolve/rk_common.py`
- Create: `…/_intern/resolve/r1_kopie_export.py`

**Interfaces:**
- Produces: `rk_common` mit `FPS`, `PROJEKT`, `ORIGINAL`, `KOPIE_PREFIX`, `CHARGE`, `INTERN`, `STAND`, `LAYOUT`, `STUDIO`, `lade_stand() -> dict`, `speichere_stand(**werte) -> dict`, `projekt() -> (resolve, project)`, `timeline(p, name)`, `kopie(p)`, `items(t, kind, idx) -> list`, `finde_mpi(p, pfad)`, `class UserZustand(p)` mit `.zuruecksetzen()`; `stand.json` mit `kopie`, `otio`, `xml`.

- [ ] **Step 1: `rk_common.py`**

```python
"""Resolve-Hilfen für den Begrüßungs-Umbau Video 03 (Spec 2026-09-16).
Regeln: nur Projekt 01_Projekt_4_Ads, schreiben NUR in eigenen Kopien (Name beginnt mit KOPIE_PREFIX),
aktive Timeline und Media-Pool-Ordner des Users am Ende zurücksetzen, nie während der Wiedergabe schreiben."""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

STUDIO = Path("/Users/jansantos/NIRO Studio")
sys.path.insert(0, str(STUDIO / "tools/autocut/src"))
from niro_autocut.resolve_api import connect  # noqa: E402

FPS = 25
PROJEKT = "01_Projekt_4_Ads"
ORIGINAL = "03_Viele_Jahre_Viele_Geschichten_V3"
KOPIE_PREFIX = "Claude 03 Begrüßung"
CHARGE = STUDIO / "projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten"
INTERN = CHARGE / "_intern/resolve"
STAND = INTERN / "stand.json"
LAYOUT = STUDIO / "tools/motion/src/clients/craiss/projects/viele-jahre/intro-layout.json"


def lade_stand() -> dict:
    return json.loads(STAND.read_text()) if STAND.exists() else {}


def speichere_stand(**werte) -> dict:
    stand = lade_stand() | werte
    INTERN.mkdir(parents=True, exist_ok=True)
    STAND.write_text(json.dumps(stand, ensure_ascii=False, indent=1))
    return stand


def projekt():
    r = connect()
    p = r.GetProjectManager().GetCurrentProject()
    if p is None:
        raise SystemExit("Resolve liefert kein Projekt (beschäftigt?) — kurz warten, nie ein Projekt laden.")
    if p.GetName() != PROJEKT:
        raise SystemExit(f"Offen ist '{p.GetName()}', freigegeben ist '{PROJEKT}' — abgebrochen, nichts geschrieben.")
    print(f"Projekt: {p.GetName()}")
    return r, p


def timeline(p, name: str):
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == name:
            return t
    raise SystemExit(f"Timeline '{name}' nicht gefunden.")


def kopie(p):
    name = lade_stand().get("kopie") or ""
    if not name.startswith(KOPIE_PREFIX):
        raise SystemExit("Keine eigene Kopie in stand.json — zuerst r1_kopie_export.py.")
    return timeline(p, name)


def items(t, kind: str, idx: int) -> list:
    return list(t.GetItemListInTrack(kind, idx) or [])


def finde_mpi(p, pfad: str):
    """Media-Pool-Eintrag zu einem Dateipfad über die Interview-Timelines (dort liegen alle FX3-Clips)."""
    ziel = unicodedata.normalize("NFC", pfad)
    namen = sorted((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)),
                   key=lambda t: not t.GetName().startswith("Interview_"))
    for t in namen:
        for kind in ("video", "audio"):
            for j in range(1, t.GetTrackCount(kind) + 1):
                for it in items(t, kind, j):
                    m = it.GetMediaPoolItem()
                    if m and unicodedata.normalize("NFC", m.GetClipProperty("File Path") or "") == ziel:
                        return m
    raise SystemExit(f"Kein Media-Pool-Eintrag für {pfad}")


class UserZustand:
    """Aktive Timeline und Media-Pool-Ordner des Users merken und zurücksetzen (WORKFLOW-Resolve Regel 5)."""

    def __init__(self, p):
        self.p = p
        self.tl = p.GetCurrentTimeline()
        ordner = p.GetMediaPool().GetCurrentFolder()
        self.ordner_id = ordner.GetUniqueId() if ordner else None

    def _suche(self, ordner, uid):
        if ordner.GetUniqueId() == uid:
            return ordner
        for sub in ordner.GetSubFolderList() or []:
            treffer = self._suche(sub, uid)
            if treffer:
                return treffer
        return None

    def zuruecksetzen(self) -> None:
        if self.tl:
            self.p.SetCurrentTimeline(self.tl)
        if self.ordner_id:
            mp = self.p.GetMediaPool()
            ordner = self._suche(mp.GetRootFolder(), self.ordner_id)
            if ordner:
                mp.SetCurrentFolder(ordner)
        print(f"User-Zustand zurück: Timeline '{self.tl.GetName() if self.tl else None}'")
```

- [ ] **Step 2: `r1_kopie_export.py`**

```python
"""Schritt 1: Kopie von 03 V3 anlegen (Original bleibt unberührt) und als OTIO + FCP-7-XML exportieren —
der Inhalt von „Compound Clip 1" ist per API nicht lesbar, die Exporte nennen Quelle und In/Out der vier Shots."""
import datetime

from rk_common import INTERN, KOPIE_PREFIX, ORIGINAL, UserZustand, items, projekt, speichere_stand, timeline

r, p = projekt()
user = UserZustand(p)
try:
    orig = timeline(p, ORIGINAL)
    name = f"{KOPIE_PREFIX} {datetime.datetime.now():%Y-%m-%d %H%M}"
    k = orig.DuplicateTimeline(name)
    if not k or k.GetName() != name:
        raise SystemExit("DuplicateTimeline fehlgeschlagen.")
    for kind in ("video", "audio"):
        for i in range(1, orig.GetTrackCount(kind) + 1):
            a, b = len(items(orig, kind, i)), len(items(k, kind, i))
            if a != b:
                raise SystemExit(f"Kopie weicht ab: {kind} {i} Original {a} / Kopie {b} Items")
    INTERN.mkdir(parents=True, exist_ok=True)
    otio, xml = INTERN / "kopie_export.otio", INTERN / "kopie_export.xml"
    ok_otio = bool(k.Export(str(otio), r.EXPORT_OTIO))
    ok_xml = bool(k.Export(str(xml), r.EXPORT_FCP_7_XML))
    if not (ok_otio or ok_xml):
        p.SetCurrentTimeline(k)
        ok_otio = bool(k.Export(str(otio), r.EXPORT_OTIO))
        ok_xml = bool(k.Export(str(xml), r.EXPORT_FCP_7_XML))
    speichere_stand(kopie=name, otio=str(otio) if ok_otio else None, xml=str(xml) if ok_xml else None)
    print(f"Kopie '{name}' angelegt · OTIO {ok_otio} · XML {ok_xml}")
finally:
    user.zuruecksetzen()
```

- [ ] **Step 3: Ausführen (vorher im Chat fragen, ob der User gerade abspielt)**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r1_kopie_export.py"`
Expected: `Projekt: 01_Projekt_4_Ads`, `Kopie 'Claude 03 Begrüßung 2026-09-16 HHMM' angelegt · OTIO True · XML True` (mindestens einer True), `User-Zustand zurück: Timeline '…'`.

- [ ] **Step 4: Readback per MCP (lesend)**

`mcp__davinci-resolve__run_script`: aktive Timeline muss wieder die des Users sein; Kopie existiert mit gleicher Spur- und Item-Zahl wie das Original.

```python
tl = project.GetCurrentTimeline()
names = [project.GetTimelineByIndex(i).GetName() for i in range(1, project.GetTimelineCount() + 1)]
result = {"aktiv": tl.GetName() if tl else None, "kopien": [n for n in names if n.startswith("Claude 03 Begrüßung")]}
```

---

### Task 6: Intro-Layout berechnen

**Files:**
- Create: `…/_intern/resolve/r2_intro_layout.py`
- Create (erzeugt): `tools/motion/src/clients/craiss/projects/viele-jahre/intro-layout.json`, `…/_intern/resolve/handles.jpg`

**Interfaces:**
- Consumes: `stand.json` (`otio`, `xml`) aus Task 5.
- Produces: `intro-layout.json` mit `fps`, `shiftFrames` (D), `montageFrames` (L), `altMontageFrames` (68), `wipes[5] {country, cutFrame, inFrames, outFrames}`, `greetings[4] {text, fromFrame}`, `helloToFrame`, `titleChip {text, fromFrame, toFrame, offsetY}`, `sfx[5] {country, recFrame}`, `shots[4] {person, country, text, file, altSrcIn, altSrcOut, altRecIn, altRecOut, srcIn, srcOut, recIn, recOut, speechRecIn, speechRecOut, audioSrcIn, audioSrcOut, audioRecIn}`; alle Frames relativ zum neuen Timeline-Start (Neu-Frame 0).

- [ ] **Step 1: `r2_intro_layout.py`**

```python
"""Schritt 2: Quell-Stellen der vier Begrüßungen aus dem Export lesen, Sprechbereiche per Pegel messen und
intro-layout.json schreiben (neue Shot-Längen, Schnittframes, Wischer, Ton, Swooshes, Titel-Chip).
Harte Regel: Kein Wischer deckt eine Person, während sie spricht (1 Frame Puffer; Thomas: 0)."""
from __future__ import annotations

import json
import math
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from array import array
from pathlib import Path
from urllib.parse import unquote, urlparse

from rk_common import FPS, INTERN, LAYOUT, STUDIO, lade_stand, speichere_stand

PERSONEN = [("Jakub", "PL", "DZIEŃ DOBRY"), ("Victor", "HU", "SZIASZTOK"),
            ("Adrian", "RO", "BUNĂ ZIUA"), ("Jan", "CZ", "ZDRAVÍM")]
WIPES = [("PL", 0, 4), ("HU", 4, 4), ("RO", 4, 4), ("CZ", 4, 4), ("CRAISS", 6, 2)]  # (Land, Einlauf, Auslauf)
PUFFER = 1
ALT_MONTAGE = 68           # Compound Clip 1: 0–2,72 s
THOMAS_AB = 3              # Thomas spricht 3 Frames nach dem alten Schnitt (Scribe „Wir" 2,839 s)
KAMERAWECHSEL_ALT = 131    # a7-Perspektive bei 5,24 s (Szenenerkennung 16.09.)
MUSIK_LUFT = 38            # Left-Offset der Musik auf A3
TITEL = "VIELE SPRACHEN. EIN TEAM."
TITEL_OFFSET_Y = 160       # Mix-Plan cc-05: y 1150
DREH = STUDIO / "projects/Craiss/4 Ads/2026-08 Dreh/_intern"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"


def pfad(url: str) -> str:
    return unicodedata.normalize("NFC", unquote(urlparse(url).path))


def shots_otio(datei: Path) -> list[dict] | None:
    d = json.loads(datei.read_text())
    video = [t for t in d["tracks"]["children"] if t.get("kind") == "Video"]
    erstes = video[0]["children"][0]
    if not erstes["OTIO_SCHEMA"].startswith("Stack"):
        return None
    spur = next(t for t in erstes["children"] if t.get("kind") == "Video")
    shots, pos = [], 0
    for c in spur["children"]:
        dauer = round(c["source_range"]["duration"]["value"])
        if c["OTIO_SCHEMA"].startswith("Clip"):
            ref = c.get("media_reference") or c["media_references"][c.get("active_media_reference_key", "DEFAULT_MEDIA")]
            basis = round(ref["available_range"]["start_time"]["value"]) if ref.get("available_range") else 0
            quelle = round(c["source_range"]["start_time"]["value"]) - basis
            shots.append({"file": pfad(ref["target_url"]), "altSrcIn": quelle, "altSrcOut": quelle + dauer,
                          "altRecIn": pos, "altRecOut": pos + dauer})
        pos += dauer
    return shots


def shots_xml(datei: Path) -> list[dict] | None:
    root = ET.parse(datei).getroot()
    dateien = {f.get("id"): f.findtext("pathurl") for f in root.iter("file") if f.findtext("pathurl")}
    nested = None
    for ci in root.iter("clipitem"):
        if (ci.findtext("name") or "").startswith("Compound Clip") and ci.find("sequence") is not None:
            nested = ci.find("sequence")
            break
    if nested is None:
        nested = next((s for s in root.iter("sequence") if (s.findtext("name") or "").startswith("Compound Clip")), None)
    if nested is None:
        return None
    shots = []
    for ci in nested.find("media/video/track").findall("clipitem"):
        fid = ci.find("file").get("id")
        shots.append({"file": pfad(dateien[fid]), "altSrcIn": int(ci.findtext("in")), "altSrcOut": int(ci.findtext("out")),
                      "altRecIn": int(ci.findtext("start")), "altRecOut": int(ci.findtext("end"))})
    return shots


def pegel(datei: str, von: int, bis: int) -> list[float]:
    """RMS in dBFS je Frame (40 ms) für die Quellframes [von, bis)."""
    roh = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{von / FPS:.3f}", "-t", f"{(bis - von) / FPS:.3f}",
                          "-i", datei, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    werte = array("h")
    werte.frombytes(roh)
    n = 16000 // FPS
    out = []
    for i in range(0, len(werte) - n + 1, n):
        block = werte[i:i + n]
        rms = math.sqrt(sum(v * v for v in block) / n) / 32768
        out.append(20 * math.log10(max(rms, 1e-6)))
    return out


def sprechbereich(s: dict) -> tuple[int, int]:
    """Erster/letzter Sprech-Frame im alten Shot: Pegel ≥ Spitze − 18 dB (mindestens −45 dBFS)."""
    lv = pegel(s["file"], s["altSrcIn"], s["altSrcOut"])
    schwelle = max(max(lv) - 18, -45)
    idx = [i for i, v in enumerate(lv) if v >= schwelle]
    return s["altSrcIn"] + idx[0], s["altSrcIn"] + idx[-1] + 1


def scribe(datei: str, von: int, bis: int) -> str:
    index = json.loads((DREH / "transcripts_index.json").read_text())
    e = next((x for x in index if x["name"] == Path(datei).name), None)
    if not e:
        return "(kein Scribe)"
    woerter = json.loads((DREH / "cache" / f"{e['fingerprint']}.scribe.json").read_text())["words"]
    return " ".join(f"{w['text']}@{w['start'] * FPS:.0f}–{w['end'] * FPS:.0f}" for w in woerter
                    if von / FPS - 0.2 <= w["start"] <= bis / FPS + 0.2) or "(keine Wörter)"


stand = lade_stand()
shots = shots_otio(Path(stand["otio"])) if stand.get("otio") else None
if not shots and stand.get("xml"):
    shots = shots_xml(Path(stand["xml"]))
if not shots or len(shots) != 4 or shots[-1]["altRecOut"] != ALT_MONTAGE:
    raise SystemExit(f"Compound-Inhalt nicht lesbar oder unerwartet: {shots}")

neu, cut = [], 0
for i, (s, (person, land, text)) in enumerate(zip(shots, PERSONEN)):
    sp_in, sp_out = sprechbereich(s)
    vor = WIPES[i][2] + 1 + PUFFER          # Auslauf + Halte-Frame + Puffer
    nach = WIPES[i + 1][1] + 1 + PUFFER     # Einlauf + Halte-Frame + Puffer
    src_in, src_out = sp_in - vor, sp_out + nach
    if src_in < 0:
        raise SystemExit(f"{person}: zu wenig Material vor dem Sprechen")
    laenge = src_out - src_in
    a_in, a_out = max(src_in, sp_in - 1), min(src_out, sp_out + 1)
    neu.append({"person": person, "country": land, "text": text, "file": s["file"],
                **{k: s[k] for k in ("altSrcIn", "altSrcOut", "altRecIn", "altRecOut")},
                "srcIn": src_in, "srcOut": src_out, "recIn": cut, "recOut": cut + laenge,
                "speechRecIn": cut + (sp_in - src_in), "speechRecOut": cut + (sp_out - src_in),
                "audioSrcIn": a_in, "audioSrcOut": a_out, "audioRecIn": cut + (a_in - src_in)})
    print(f"{person}: Sprechen {sp_in}–{sp_out} (alt {s['altSrcIn']}–{s['altSrcOut']}) · neu {src_in}–{src_out} = {laenge} F"
          f" · Scribe: {scribe(s['file'], s['altSrcIn'], s['altSrcOut'])}")
    cut += laenge

L = cut
D = L - ALT_MONTAGE
wipes = [{"country": land, "cutFrame": neu[i]["recIn"] if i < 4 else L, "inFrames": ein, "outFrames": aus}
         for i, (land, ein, aus) in enumerate(WIPES)]

for i, s in enumerate(neu):
    frei = set(range(s["speechRecIn"] - PUFFER, s["speechRecOut"] + PUFFER))
    for w in (wipes[i], wipes[i + 1]):
        gedeckt = set(range(w["cutFrame"] - 1 - w["inFrames"], w["cutFrame"] + w["outFrames"] + 1))
        if gedeckt & frei:
            raise SystemExit(f"Regelbruch: Wischer {w['country']} deckt {s['person']} beim Sprechen")
if THOMAS_AB < wipes[4]["outFrames"] + 1:
    raise SystemExit("Roter Wischer deckt Thomas beim ersten Wort")
if D > MUSIK_LUFT:
    raise SystemExit(f"Verlängerung {D} F > Musik-Luft {MUSIK_LUFT} F — Ein-/Auslauf kürzen")

layout = {
    "fps": FPS, "shiftFrames": D, "montageFrames": L, "altMontageFrames": ALT_MONTAGE,
    "wipes": wipes,
    "greetings": [{"text": s["text"], "fromFrame": 0 if i == 0 else s["recIn"] - 1} for i, s in enumerate(neu)],
    "helloToFrame": L - 1,
    "titleChip": {"text": TITEL, "fromFrame": L + 1, "toFrame": KAMERAWECHSEL_ALT + D, "offsetY": TITEL_OFFSET_Y},
    "sfx": [{"country": w["country"], "recFrame": max(0, w["cutFrame"] - 1 - w["inFrames"])} for w in wipes],
    "shots": neu,
}
LAYOUT.write_text(json.dumps(layout, ensure_ascii=False, indent=1) + "\n")
speichere_stand(shiftFrames=D, montageFrames=L)

bilder = []
for s in neu:
    for tag, f in (("Start", s["srcIn"]), ("Sprechen an", s["srcIn"] + s["speechRecIn"] - s["recIn"]),
                   ("Sprechen aus", s["srcIn"] + s["speechRecOut"] - s["recIn"] - 1), ("Ende", s["srcOut"] - 1)):
        png = INTERN / f"handle_{s['person']}_{tag.replace(' ', '_')}.png"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{f / FPS:.3f}", "-i", s["file"],
                        "-frames:v", "1", "-vf", "scale=270:-2", str(png)], check=True)
        bilder += ["-label", f"{s['person']} {tag} F{f}", str(png)]
subprocess.run(["montage", "-font", FONT, "-pointsize", "12", *bilder, "-tile", "4x", "-geometry", "+4+4",
                str(INTERN / "handles.jpg")], check=True)
print(f"Layout: Montage {L} F (alt {ALT_MONTAGE}), D = {D} F = {D / FPS:.2f} s → {LAYOUT}")
```

- [ ] **Step 2: Ausführen**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r2_intro_layout.py"`
Expected: vier Zeilen (Jakub, Victor, Adrian, Jan) mit plausiblen Sprechbereichen (Scribe-Wörter liegen darin; Adrian ohne Scribe), `Layout: Montage … F (alt 68), D = … F` mit D ≤ 38.

- [ ] **Step 3: Luft-Bilder prüfen**

`…/_intern/resolve/handles.jpg` mit dem Read-Tool ansehen: In „Start" und „Ende" steht dieselbe Person ruhig in derselben Einstellung wie beim Sprechen (kein Gang aus dem Bild, kein Blick zur Seite, keine fremde Person). Wenn nicht: `PUFFER` bleibt, aber `WIPES` für diesen Übergang auf Ein-/Auslauf 3 setzen, Step 2 wiederholen; reicht das nicht, den User fragen.

- [ ] **Step 4: Layout-Test**

`tools/motion/src/clients/craiss/intro/wipeTiming.test.ts` gibt es erst in Task 10 — hier nur Sichtprüfung der JSON: `wipes[0].cutFrame == 0`, `wipes[4].cutFrame == montageFrames`, `greetings[i].fromFrame == wipes[i].cutFrame - 1` für i ≥ 1, `titleChip.toFrame == 131 + shiftFrames`.

---

### Task 7: Platz vorn schaffen (nur Kopie)

**Files:**
- Create: `…/_intern/resolve/r3_platz_vorn.py`

**Interfaces:**
- Consumes: `intro-layout.json.shiftFrames` (D), `stand.json.kopie`.
- Produces: `stand.json.neu_start_frame` = absoluter Frame von Neu-Frame 0, `stand.json.weg` = `"start_tc"` oder `"handgriff"`. Danach gilt in der Kopie: alter Inhalt liegt bei `neu_start_frame + D + (alter Relativ-Frame)`.

- [ ] **Step 1: `r3_platz_vorn.py`**

```python
"""Schritt 3: In der Kopie vorn D Frames Platz schaffen, ohne einen Clip zu verändern.
Probe: früherer Start-Timecode. Hält Resolve die absoluten Clip-Positionen, bleibt es dabei.
Sonst Start-TC zurück; der User verschiebt in der Kopie alle Clips geschlossen um +D Frames,
danach prüft `--nach-handgriff` jeden Clip gegen das Original."""
import json
import sys

from rk_common import FPS, LAYOUT, ORIGINAL, items, kopie, projekt, speichere_stand, timeline


def tc(frames: int) -> str:
    h, rest = divmod(frames, 3600 * FPS)
    m, rest = divmod(rest, 60 * FPS)
    s, f = divmod(rest, FPS)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def positionen(t) -> dict:
    return {(kind, i, j): it.GetStart() for kind in ("video", "audio")
            for i in range(1, t.GetTrackCount(kind) + 1) for j, it in enumerate(items(t, kind, i))}


D = json.loads(LAYOUT.read_text())["shiftFrames"]
r, p = projekt()
k = kopie(p)

if "--nach-handgriff" in sys.argv:
    orig = timeline(p, ORIGINAL)
    o, n = positionen(orig), positionen(k)
    o0, n0 = orig.GetStartFrame(), k.GetStartFrame()
    falsch = [key for key in o if key not in n or (n[key] - n0) != (o[key] - o0) + D]
    if falsch:
        raise SystemExit(f"{len(falsch)} Clips nicht um genau {D} Frames verschoben, z. B. {falsch[:5]}")
    speichere_stand(neu_start_frame=n0, weg="handgriff")
    print(f"OK: alle {len(o)} Clips um {D} Frames verschoben.")
    sys.exit(0)

vorher, start = positionen(k), k.GetStartFrame()
if not k.SetStartTimecode(tc(start - D)):
    raise SystemExit("SetStartTimecode abgelehnt.")
if k.GetStartFrame() == start - D and positionen(k) == vorher:
    speichere_stand(neu_start_frame=start - D, weg="start_tc")
    print(f"OK: Start-TC {tc(start - D)}, alle Clips an ihrer Position — {D} Frames Platz vorn.")
else:
    k.SetStartTimecode(tc(start))
    zurueck = positionen(k) == vorher and k.GetStartFrame() == start
    print(f"Start-TC verschiebt die Clips mit (zurückgesetzt: {zurueck}).\n"
          f"Handgriff nötig: In '{k.GetName()}' alle Clips markieren (Cmd+A), '+{D}' tippen, Enter. "
          f"Danach: r3_platz_vorn.py --nach-handgriff")
    sys.exit(2)
```

- [ ] **Step 2: Ausführen (vorher Wiedergabe abfragen)**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r3_platz_vorn.py"`
Expected: entweder `OK: Start-TC …` (Exit 0) oder die Handgriff-Anweisung (Exit 2). Bei Exit 2: dem User die Anweisung im Chat geben, warten, dann mit `--nach-handgriff` erneut ausführen → `OK: alle … Clips um D Frames verschoben.`

- [ ] **Step 3: Befund festhalten**

Das gemessene Verhalten von `SetStartTimecode` (hält Positionen ja/nein) in `tools/resolve/WORKFLOW-Resolve.md` → Abschnitt „Gemessenes Verhalten 21.1.0.14" als eigener Punkt ergänzen.

---

### Task 8: Begrüßungs-Montage in der Kopie bauen

**Files:**
- Create: `…/_intern/resolve/r4_intro_bauen.py`

**Interfaces:**
- Consumes: `intro-layout.json` (`shots`, `sfx`, `shiftFrames`), `stand.json.neu_start_frame`.
- Produces: in der Kopie V3 = 4 Bild-Clips, A2 = 4 Ton-Clips, A3 = Musik-Kopf, A5 = 5 Swooshes; deaktiviert: Compound Clip (V1/A1), alle Clips auf V6 und V9; Mark In/Out = Neu-Frame 0 bis 1291 + D.

- [ ] **Step 1: `r4_intro_bauen.py`**

```python
"""Schritt 4: Neue Begrüßungs-Montage in der Kopie bauen (nur Kopie!).
V3 Bild · A2 Ton (nur Sprechen) · A3 Musik-Kopf aus demselben Song · A5 Swoosh je Wischer.
Compound Clip (V1/A1), altes Overlay (V6) und Alpha v1 (V9) nur deaktivieren. Readback je Item."""
import json

from rk_common import LAYOUT, UserZustand, finde_mpi, items, kopie, lade_stand, projekt

L = json.loads(LAYOUT.read_text())
stand = lade_stand()
if stand.get("neu_start_frame") is None:
    raise SystemExit("Erst r3_platz_vorn.py.")
BASIS = int(stand["neu_start_frame"])
D = int(L["shiftFrames"])
ALT_ENDE = 1291  # Mark Out des V3-Schnitts (relativ)

r, p = projekt()
k = kopie(p)
if any(it.GetStart() < BASIS + L["montageFrames"] for it in items(k, "video", 3)):
    raise SystemExit("V3 ist vorn schon belegt — Skript lief bereits? Zustand erst lesen.")

musik = items(k, "audio", 3)[0]
swoosh_alt = next(it for it in items(k, "audio", 4) if "swishes" in it.GetMediaPoolItem().GetName())
if musik.GetLeftOffset() < D:
    raise SystemExit(f"Musik hat nur {musik.GetLeftOffset()} Frames Luft, gebraucht {D}.")

user = UserZustand(p)
try:
    p.SetCurrentTimeline(k)
    infos = []
    for s in L["shots"]:
        m = finde_mpi(p, s["file"])
        infos.append({"mediaPoolItem": m, "startFrame": s["srcIn"], "endFrame": s["srcOut"],
                      "recordFrame": BASIS + s["recIn"], "trackIndex": 3, "mediaType": 1})
        infos.append({"mediaPoolItem": m, "startFrame": s["audioSrcIn"], "endFrame": s["audioSrcOut"],
                      "recordFrame": BASIS + s["audioRecIn"], "trackIndex": 2, "mediaType": 2})
    links = int(musik.GetLeftOffset())
    infos.append({"mediaPoolItem": musik.GetMediaPoolItem(), "startFrame": links - D, "endFrame": links,
                  "recordFrame": BASIS, "trackIndex": 3, "mediaType": 2})
    for sfx in L["sfx"]:
        infos.append({"mediaPoolItem": swoosh_alt.GetMediaPoolItem(), "startFrame": 0, "endFrame": 10,
                      "recordFrame": BASIS + sfx["recFrame"], "trackIndex": 5, "mediaType": 2})

    p.GetMediaPool().SetSelectedClip(infos[0]["mediaPoolItem"])
    neu = p.GetMediaPool().AppendToTimeline(infos) or []
    if len(neu) != len(infos):
        raise SystemExit(f"AppendToTimeline: {len(neu)} von {len(infos)} Items gesetzt — Kopie in Resolve prüfen.")
    for info, it in zip(infos, neu):
        soll = (info["recordFrame"], info["endFrame"] - info["startFrame"])
        ist = (int(it.GetStart()), int(it.GetDuration()))
        if soll != ist:
            raise SystemExit(f"Readback {it.GetName()} Spur {info['trackIndex']}: Soll {soll}, Ist {ist}")

    musik_vol = (musik.GetProperty() or {}).get("AudioVolume")
    swoosh_vol = (swoosh_alt.GetProperty() or {}).get("AudioVolume")
    for info, it in zip(infos, neu):
        if info["mediaPoolItem"] == musik.GetMediaPoolItem() and musik_vol is not None:
            it.SetProperty("AudioVolume", musik_vol)
        if info["mediaPoolItem"] == swoosh_alt.GetMediaPoolItem() and swoosh_vol is not None:
            it.SetProperty("AudioVolume", swoosh_vol)

    aus = [it for it in items(k, "video", 1) + items(k, "audio", 1)
           if it.GetStart() == BASIS + D and it.GetName().startswith("Compound Clip")]
    aus += items(k, "video", 6) + items(k, "video", 9)
    for it in aus:
        it.SetClipEnabled(False)
    noch_an = [it.GetName() for it in aus if it.GetClipEnabled()]
    if noch_an:
        raise SystemExit(f"Nicht deaktiviert: {noch_an} — später erneut (Clip im Inspector offen?).")
    k.SetMarkInOut(0, ALT_ENDE + D)
    print(f"Gebaut: {len(neu)} Items · deaktiviert {len(aus)} · Mark {k.GetMarkInOut()}")
finally:
    user.zuruecksetzen()
```

- [ ] **Step 2: Ausführen (vorher im Chat: „Ich schalte kurz auf die Kopie — bitte nicht abspielen.")**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r4_intro_bauen.py"`
Expected: `Gebaut: 14 Items · deaktiviert 5 · Mark {…}` (4 Bild + 4 Ton + 1 Musik-Kopf + 5 Swooshes; deaktiviert: Compound Clip V1 + A1, 2 Clips auf V6, 1 Clip auf V9), danach `User-Zustand zurück`. Weicht ein Item ab, bricht das Skript mit Readback-Meldung ab.

- [ ] **Step 3: Readback per MCP (lesend)**

```python
k = None
for i in range(1, project.GetTimelineCount() + 1):
    t = project.GetTimelineByIndex(i)
    if t.GetName().startswith("Claude 03 Begrüßung"):
        k = t
s0 = k.GetStartFrame()
def row(it):
    return [it.GetStart() - s0, it.GetDuration(), it.GetName(), it.GetClipEnabled()]
result = {"start_tc": k.GetStartTimecode(), "V1": [row(i) for i in (k.GetItemListInTrack("video", 1) or [])[:3]],
          "V3": [row(i) for i in (k.GetItemListInTrack("video", 3) or [])[:6]],
          "A2": [row(i) for i in (k.GetItemListInTrack("audio", 2) or [])],
          "A3": [row(i) for i in (k.GetItemListInTrack("audio", 3) or [])],
          "A5": [row(i) for i in (k.GetItemListInTrack("audio", 5) or [])],
          "aktiv": project.GetCurrentTimeline().GetName(), "marks": k.GetMarkInOut()}
```
Expected: V3 beginnt bei 0 mit 4 aneinanderliegenden Shots bis `montageFrames`; Compound Clip bei `D` deaktiviert; A3 = Musik-Kopf 0…D + Original ab D; aktive Timeline = die des Users.

- [ ] **Step 4: Tonspur-Hinweis**

Keine neuen Tonspuren angelegt (A2/A3/A5 stammen aus der Vorlage) — Stereo-Fixer-Hinweis entfällt. Im Chat erwähnen, dass der „Low Airy Whoosh" auf A4 unverändert bei der alten Position liegt und beim Abhören geprüft werden sollte.

---

### Task 9: Export ohne Animation und Grading-Vergleich

**Files:**
- Create: `…/_intern/resolve/r5_export_ohne_animation.py`
- Create: `…/_intern/resolve/r6_grading_vergleich.py`
- Create: `…/_intern/resolve/r7_grade_kopieren.py`
- Create (erzeugt): `…/Material/Video/ohne-Animation/03_Viele_Jahre_Viele_Geschichten_Begruessung.<ext>` + `…/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4`

**Interfaces:**
- Consumes: Kopie aus Task 8; `intro-layout.json.shots`.
- Produces: `stand.json.export_ohne_animation`, `stand.json.proxy`, `stand.json.proxy_frames` (= 1291 + D).

- [ ] **Step 1: `r5_export_ohne_animation.py`**

```python
"""Schritt 5: Kopie ohne Animation exportieren (Quick Export „H.264 Master" → Ergebnisse/Export),
als Remotion-Quelle nach Material/Video/ohne-Animation kopieren und H.264-Proxy 1080×1920 bauen."""
import datetime
import json
import shutil
import subprocess

from rk_common import CHARGE, LAYOUT, UserZustand, items, kopie, projekt, speichere_stand

D = json.loads(LAYOUT.read_text())["shiftFrames"]
r, p = projekt()
k = kopie(p)
for idx in (6, 9):
    if any(it.GetClipEnabled() for it in items(k, "video", idx)):
        raise SystemExit(f"V{idx} hat noch aktive Grafik-Clips — erst r4_intro_bauen.py.")

name = f"03_Viele_Jahre_Begruessung_ohneAnim_{datetime.datetime.now():%Y%m%d_%H%M}"
ziel = CHARGE / "Ergebnisse/Export"
ziel.mkdir(parents=True, exist_ok=True)
user = UserZustand(p)
try:
    p.SetCurrentTimeline(k)
    if k.GetIsTrackEnabled("video", 8):
        k.SetTrackEnable("video", 8, False)   # Safezone-Bild (nur Kopie)
    status = p.RenderWithQuickExport("H.264 Master", {"TargetDir": str(ziel), "CustomName": name, "EnableUpload": False})
    print("QuickExport:", status)
finally:
    user.zuruecksetzen()

datei = next(ziel.glob(name + ".*"), None)
if not datei:
    raise SystemExit("Export-Datei fehlt.")
quelle = CHARGE / "Material/Video/ohne-Animation" / ("03_Viele_Jahre_Viele_Geschichten_Begruessung" + datei.suffix)
shutil.copy2(datei, quelle)
proxy = CHARGE / "Material/Video/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(quelle), "-vf", "scale=1080:1920",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", str(proxy)], check=True)
frames = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                             "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(proxy)],
                            capture_output=True, text=True, check=True).stdout.strip())
speichere_stand(export_ohne_animation=str(quelle), proxy=str(proxy), proxy_frames=frames)
print(f"Export {datei.name} → {quelle.name} · Proxy {frames} Frames (Soll {1291 + D})")
```

- [ ] **Step 2: Ausführen (Timeline-Wechsel ankündigen)**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r5_export_ohne_animation.py"`
Expected: `Proxy N Frames (Soll N)` mit gleichen Zahlen. Weichen sie ab: Mark In/Out der Kopie per MCP lesen und korrigieren (nur Kopie), Step 2 wiederholen.

- [ ] **Step 3: `r6_grading_vergleich.py`**

```python
"""Schritt 6: Farbe der neuen Montage (Kopie-Export) mit der alten (V3-Export ohne Animation) vergleichen:
mittleres RGB je Shot auf demselben Quellbild (Mitte des Sprechens). Abweichung > 6 (0–255) = Grading fehlt."""
import json
import subprocess
from pathlib import Path

from rk_common import CHARGE, FPS, LAYOUT, lade_stand

L = json.loads(LAYOUT.read_text())
ALT = CHARGE / "Material/Video/ohne-Animation/03_Viele_Jahre_Viele_Geschichten_V3.mp4"
NEU = Path(lade_stand()["export_ohne_animation"])


def mittel(datei: Path, frame: int) -> list[float]:
    roh = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(datei), "-vf",
                          f"select=eq(n\\,{frame}),scale=64:114", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(roh) // 3
    return [sum(roh[c::3]) / n for c in range(3)]


schlecht = 0
for s in L["shots"]:
    q = s["srcIn"] + (s["speechRecIn"] + s["speechRecOut"]) // 2 - s["recIn"]
    alt_frame = s["altRecIn"] + (q - s["altSrcIn"])
    neu_frame = s["recIn"] + (q - s["srcIn"])
    if not (s["altRecIn"] <= alt_frame < s["altRecOut"]):
        alt_frame = (s["altRecIn"] + s["altRecOut"]) // 2
        q = s["altSrcIn"] + alt_frame - s["altRecIn"]
        neu_frame = s["recIn"] + (q - s["srcIn"])
    a, b = mittel(ALT, alt_frame), mittel(NEU, neu_frame)
    delta = max(abs(x - y) for x, y in zip(a, b))
    schlecht += delta > 6
    print(f"{s['person']}: alt F{alt_frame} {[round(x) for x in a]} · neu F{neu_frame} {[round(x) for x in b]} · Δmax {delta:.1f}")
print("GRADING OK" if not schlecht else f"GRADING WEICHT AB ({schlecht} Shots)")
```

- [ ] **Step 4: Ausführen**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r6_grading_vergleich.py"`
Expected: `GRADING OK`. Bei `GRADING WEICHT AB` weiter mit Step 5, sonst Task 10.

- [ ] **Step 5: `r7_grade_kopieren.py` (nur bei Abweichung)**

```python
"""Schritt 7: Grade des Compound Clips (Knoten auf dem Compound-Item) auf die neuen Shots kopieren — nur Kopie."""
import json

from rk_common import LAYOUT, UserZustand, items, kopie, lade_stand, projekt

L = json.loads(LAYOUT.read_text())
BASIS, D = int(lade_stand()["neu_start_frame"]), int(L["shiftFrames"])
r, p = projekt()
k = kopie(p)
comp = next(it for it in items(k, "video", 1) if it.GetStart() == BASIS + D and it.GetName().startswith("Compound Clip"))
neue = [it for it in items(k, "video", 3) if it.GetStart() < BASIS + L["montageFrames"]]
user = UserZustand(p)
try:
    p.SetCurrentTimeline(k)
    print("CopyGrades:", comp.CopyGrades(neue), "auf", len(neue), "Shots")
finally:
    user.zuruecksetzen()
```

Run r7, dann r5 und r6 erneut. Ist das Ergebnis weiterhin `GRADING WEICHT AB`, liegt das Grading in den Clips innerhalb des Compound Clips: den User bitten, auf der Color-Seite den Grade eines Begrüßungs-Shots aus dem Compound auf die 4 neuen Shots in der Kopie zu übertragen; danach r5 + r6 erneut.

---

### Task 10: Wischer-Timing, Flaggen-Fläche, Intro-Komponente (TDD)

**Files:**
- Create: `tools/motion/src/clients/craiss/intro/wipeTiming.ts`
- Test: `tools/motion/src/clients/craiss/intro/wipeTiming.test.ts`
- Create: `tools/motion/src/clients/craiss/intro/FlagWipe.tsx`
- Create: `tools/motion/src/clients/craiss/intro/GreetingIntro.tsx`

**Interfaces:**
- Consumes: `intro-layout.json` (Task 6), `CHIP_BOX_STYLE`, `FONT_BLACK`, `WHITE`, `RED`, `BASE_W`, `BASE_H` (lib).
- Produces: `countrySchema`, `wipeSchema`, `introLayoutSchema`, `type Wipe`, `type IntroLayout`, `wipeOffset(frame: number, w: Wipe): number | null` (1 = rechts draußen, 0 = deckt voll, −1 = links draußen, null = unsichtbar), `greetingIndexAt(frame: number, greetings: { fromFrame: number }[]): number`, `FlagPanel: React.FC<{ country: Wipe["country"]; offset: number }>`, `GreetingIntro: React.FC<{ layout: IntroLayout }>`, `introEndFrame(layout: IntroLayout): number` (erster Frame nach dem letzten Wischer).

- [ ] **Step 1: Failing Tests**

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { greetingIndexAt, introEndFrame, introLayoutSchema, wipeOffset, type Wipe } from "./wipeTiming";

const HU: Wipe = { country: "HU", cutFrame: 30, inFrames: 4, outFrames: 4 };

test("Einlauf beginnt inFrames vor dem Halten, davor unsichtbar", () => {
  assert.equal(wipeOffset(24, HU), null);
  assert.ok(wipeOffset(25, HU)! > 0.9);
});

test("hält auf cutFrame − 1 und cutFrame voll deckend", () => {
  assert.equal(wipeOffset(29, HU), 0);
  assert.equal(wipeOffset(30, HU), 0);
});

test("Einlauf und Auslauf fallen monoton", () => {
  const ein = [25, 26, 27, 28].map((f) => wipeOffset(f, HU)!);
  ein.forEach((v, i) => {
    assert.ok(v > 0 && v < 1);
    if (i) assert.ok(v < ein[i - 1]);
  });
  const aus = [31, 32, 33, 34].map((f) => wipeOffset(f, HU)!);
  aus.forEach((v, i) => {
    assert.ok(v < 0 && v > -1);
    if (i) assert.ok(v < aus[i - 1]);
  });
  assert.equal(wipeOffset(35, HU), null);
});

test("erster Wischer ohne Einlauf deckt Frame 0", () => {
  const PL: Wipe = { country: "PL", cutFrame: 0, inFrames: 0, outFrames: 4 };
  assert.equal(wipeOffset(0, PL), 0);
  assert.ok(wipeOffset(1, PL)! < 0);
  assert.equal(wipeOffset(5, PL), null);
});

test("roter Wischer: 6 Frames Einlauf, 2 Frames Auslauf", () => {
  const R: Wipe = { country: "CRAISS", cutFrame: 100, inFrames: 6, outFrames: 2 };
  assert.equal(wipeOffset(92, R), null);
  assert.ok(wipeOffset(93, R)! > 0);
  assert.ok(wipeOffset(102, R)! < 0);
  assert.equal(wipeOffset(103, R), null);
});

test("greetingIndexAt", () => {
  const g = [{ fromFrame: 0 }, { fromFrame: 29 }, { fromFrame: 55 }];
  assert.equal(greetingIndexAt(0, g), 0);
  assert.equal(greetingIndexAt(28, g), 0);
  assert.equal(greetingIndexAt(29, g), 1);
  assert.equal(greetingIndexAt(80, g), 2);
});

test("intro-layout.json passt zum Schema und ist in sich stimmig", () => {
  const datei = path.join(__dirname, "../projects/viele-jahre/intro-layout.json");
  const L = introLayoutSchema.parse(JSON.parse(fs.readFileSync(datei, "utf8")));
  assert.equal(L.wipes[0].cutFrame, 0);
  assert.equal(L.wipes[4].cutFrame, L.montageFrames);
  L.greetings.forEach((g, i) => assert.equal(g.fromFrame, i === 0 ? 0 : L.wipes[i].cutFrame - 1));
  assert.equal(L.helloToFrame, L.montageFrames - 1);
  assert.equal(L.titleChip.toFrame, 131 + L.shiftFrames);
  assert.equal(introEndFrame(L), L.montageFrames + L.wipes[4].outFrames + 1);
});
```

- [ ] **Step 2: Tests laufen lassen**

Run: `npx tsx --test src/clients/craiss/intro/wipeTiming.test.ts`
Expected: FAIL („Cannot find module './wipeTiming'").

- [ ] **Step 3: `wipeTiming.ts`**

```ts
// ============================================================
// Craiss Video 03 — Intro-Layout (aus dem Resolve-Umbau) und Wischer-Timing.
// Voll deckend auf cutFrame − 1 und cutFrame; Einlauf ease-in, Auslauf ease-out.
// ============================================================
import { z } from "zod";

export const countrySchema = z.enum(["PL", "HU", "RO", "CZ", "CRAISS"]);

export const wipeSchema = z.object({
  country: countrySchema,
  cutFrame: z.number().int(),
  inFrames: z.number().int().min(0),
  outFrames: z.number().int().min(1),
});

export const introLayoutSchema = z
  .object({
    fps: z.literal(25),
    shiftFrames: z.number().int().min(0),
    montageFrames: z.number().int(),
    wipes: z.array(wipeSchema).length(5),
    greetings: z.array(z.object({ text: z.string(), fromFrame: z.number().int() })).length(4),
    helloToFrame: z.number().int(),
    titleChip: z.object({ text: z.string(), fromFrame: z.number().int(), toFrame: z.number().int(), offsetY: z.number() }),
  })
  .passthrough();

export type Wipe = z.infer<typeof wipeSchema>;
export type IntroLayout = z.infer<typeof introLayoutSchema>;

export const wipeOffset = (frame: number, w: Wipe): number | null => {
  const holdStart = w.cutFrame - 1;
  if (frame >= holdStart && frame <= w.cutFrame) return 0;
  if (frame < holdStart) {
    const k = frame - (holdStart - w.inFrames) + 1; // 1..inFrames
    if (k < 1) return null;
    const p = k / (w.inFrames + 1);
    return 1 - p * p;
  }
  const k = frame - w.cutFrame; // 1..outFrames
  if (k > w.outFrames) return null;
  const p = k / (w.outFrames + 1);
  return -(1 - (1 - p) * (1 - p));
};

export const greetingIndexAt = (frame: number, greetings: { fromFrame: number }[]): number => {
  let idx = -1;
  greetings.forEach((g, i) => {
    if (frame >= g.fromFrame) idx = i;
  });
  return idx;
};

export const introEndFrame = (layout: IntroLayout): number =>
  Math.max(...layout.wipes.map((w) => w.cutFrame + w.outFrames)) + 1;
```

- [ ] **Step 4: Tests laufen lassen**

Run: `npx tsx --test src/clients/craiss/intro/wipeTiming.test.ts`
Expected: PASS (7 Tests).

- [ ] **Step 5: `FlagWipe.tsx`**

```tsx
// ============================================================
// Vollbild-Flagge für die Wischer in Video 03 (Farben wie FLAG_RECTS).
// Streifen 2 px überlappend und crispEdges → keine Haarlinien im Alpha.
// ============================================================
import React from "react";
import { BASE_H, BASE_W, RED } from "../lib";
import type { Wipe } from "./wipeTiming";

const W = BASE_W;
const H = BASE_H;
const O = 2;

const Band: React.FC<{ x: number; y: number; w: number; h: number; fill: string }> = ({ x, y, w, h, fill }) => (
  <rect x={x} y={y} width={w} height={h} fill={fill} shapeRendering="crispEdges" />
);

const PANELS: Record<Wipe["country"], React.ReactElement> = {
  PL: (
    <>
      <Band x={0} y={0} w={W} h={H / 2 + O} fill="#FFFFFF" />
      <Band x={0} y={H / 2} w={W} h={H / 2} fill="#DC143C" />
    </>
  ),
  HU: (
    <>
      <Band x={0} y={0} w={W} h={H / 3 + O} fill="#CD2A3E" />
      <Band x={0} y={H / 3} w={W} h={H / 3 + O} fill="#FFFFFF" />
      <Band x={0} y={(2 * H) / 3} w={W} h={H / 3} fill="#436F4D" />
    </>
  ),
  RO: (
    <>
      <Band x={0} y={0} w={W / 3 + O} h={H} fill="#002B7F" />
      <Band x={W / 3} y={0} w={W / 3 + O} h={H} fill="#FCD116" />
      <Band x={(2 * W) / 3} y={0} w={W / 3} h={H} fill="#CE1126" />
    </>
  ),
  CZ: (
    <>
      <Band x={0} y={0} w={W} h={H / 2 + O} fill="#FFFFFF" />
      <Band x={0} y={H / 2} w={W} h={H / 2} fill="#D7141A" />
      <polygon points={`0,0 ${W / 2},${H / 2} 0,${H}`} fill="#11457E" />
    </>
  ),
  CRAISS: <Band x={0} y={0} w={W} h={H} fill={RED} />,
};

export const FlagPanel: React.FC<{ country: Wipe["country"]; offset: number }> = ({ country, offset }) => (
  <svg
    width={W}
    height={H}
    viewBox={`0 0 ${W} ${H}`}
    style={{ position: "absolute", top: 0, left: 0, transform: `translateX(${offset * W}px)` }}
  >
    {PANELS[country]}
  </svg>
);
```

- [ ] **Step 6: `GreetingIntro.tsx`**

```tsx
// ============================================================
// Video 03 — Begrüßungs-Intro: Flaggen-Wischer (unten), darüber groß HALLO
// und der Begrüßungs-Chip, dessen Text unter voll deckender Flagge wechselt.
// Frames absolut ab Video-Start (Sequence from 0).
// ============================================================
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { CHIP_BOX_STYLE, FONT_BLACK, WHITE } from "../lib";
import { FlagPanel } from "./FlagWipe";
import { greetingIndexAt, wipeOffset, type IntroLayout } from "./wipeTiming";

const HELLO_TOP = 900; // Basis 1920: Bereich der alten Headline (Hook „lower" 940)

export const GreetingIntro: React.FC<{ layout: IntroLayout }> = ({ layout }) => {
  const frame = useCurrentFrame();
  const g = greetingIndexAt(frame, layout.greetings);
  const op = interpolate(frame, [layout.helloToFrame - 4, layout.helloToFrame], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <>
      {layout.wipes.map((w) => {
        const off = wipeOffset(frame, w);
        return off === null ? null : <FlagPanel key={w.country} country={w.country} offset={off} />;
      })}
      {g >= 0 && op > 0 ? (
        <div
          style={{
            position: "absolute",
            top: HELLO_TOP,
            left: 0,
            right: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 22,
            opacity: op,
          }}
        >
          <div
            style={{
              fontFamily: FONT_BLACK,
              fontSize: 150,
              lineHeight: 1,
              color: WHITE,
              textTransform: "uppercase",
              textShadow: "0 4px 26px rgba(0,0,0,0.55)",
            }}
          >
            HALLO
          </div>
          <div style={CHIP_BOX_STYLE}>{layout.greetings[g].text}</div>
        </div>
      ) : null}
    </>
  );
};
```

Run: `npx tsc --noEmit`
Expected: keine Fehler.

---

### Task 11: Video 03 auf den neuen Schnitt umstellen

**Files:**
- Modify: `tools/motion/src/clients/craiss/projects/viele-jahre/Composition.tsx`
- Modify: `tools/motion/src/clients/craiss/projects/viele-jahre/schlagwoerter.ts`
- Modify: `tools/motion/src/clients/craiss/projects/vorschau/Composition.tsx` (Eintrag „03")

**Interfaces:**
- Consumes: `introLayoutSchema`, `introEndFrame`, `GreetingIntro` (Task 10); `RedChip`, `chipSchema` (Task 1); `shiftKeywords`, `shiftBlocked` (Task 2); `stand.json.proxy_frames` (Task 9).
- Produces: `craissVieleJahreSchema` ohne `hook`, mit `titleChip: chipSchema`; `export const VIELE_JAHRE_SECONDS: number`; `export const INTRO_SHIFT_FRAMES: number`; `schlagwoerter.ts` (03) mit `BLOCKED`/`KEYWORDS`/`DURATION_SEC` des neuen Schnitts.

- [ ] **Step 1: `schlagwoerter.ts` (03) auf den neuen Schnitt**

Die drei letzten Zeilen (`export const DURATION_SEC = DURATION_SEC_V3;` … `export const KEYWORDS = KEYWORDS_V3;`) ersetzen durch:

```ts
import introJson from "./intro-layout.json";
import { shiftBlocked, shiftKeywords } from "../../captionMix/keywords";

const SHIFT_SEC = introJson.shiftFrames / introJson.fps;
const r2 = (v: number) => Math.round(v * 100) / 100;

// Neuer Schnitt (Kopie „Claude 03 Begrüßung …"): alles hinter der Montage + D
export const DURATION_SEC = r2(DURATION_SEC_V3 + SHIFT_SEC);
export const BLOCKED: BlockedRange[] = [
  { startSec: 0, durationSec: introJson.titleChip.toFrame / introJson.fps }, // Begrüßung, Wischer, Titel-Chip
  ...shiftBlocked([BLOCKED_V3[1]], SHIFT_SEC), // Laender-Flaggen
  { startSec: r2(46.64 + SHIFT_SEC), durationSec: r2(DURATION_SEC - (46.64 + SHIFT_SEC)) }, // CTA
];
export const KEYWORDS: Keyword[] = shiftKeywords(KEYWORDS_V3, SHIFT_SEC);
```
(Die beiden Importe an den Dateianfang zu den anderen Importen stellen.)

Run: `npx tsx --test src/clients/craiss/captionMix/schlagwoerter-daten.test.ts`
Expected: PASS.

- [ ] **Step 2: `viele-jahre/Composition.tsx`**

Änderungen:

```tsx
// Importe: Hook und hookSchema aus "../../lib" entfernen, RedChip und chipSchema ergänzen; dazu:
import introJson from "./intro-layout.json";
import { GreetingIntro } from "../../intro/GreetingIntro";
import { introEndFrame, introLayoutSchema } from "../../intro/wipeTiming";

const INTRO = introLayoutSchema.parse(introJson);
export const INTRO_SHIFT_FRAMES = INTRO.shiftFrames;
const SHIFT_SEC = INTRO.shiftFrames / INTRO.fps;
const r2 = (v: number) => Math.round(v * 100) / 100;

// Schema: `hook: hookSchema.describe("Hook"),` ersetzen durch
  titleChip: chipSchema.describe("Titel-Chip nach der Begrüßung"),

// Kunden-Schnitt V3 hatte 1291 Frames; die Kopie „Claude 03 Begrüßung" ist um D länger.
const VIDEO_SECONDS = (1291 + INTRO.shiftFrames) / INTRO.fps;
export const VIELE_JAHRE_SECONDS = VIDEO_SECONDS;

// Defaults: `hook: {…}` löschen und ergänzen
  titleChip: {
    text: INTRO.titleChip.text,
    startSec: INTRO.titleChip.fromFrame / INTRO.fps,
    endSec: INTRO.titleChip.toFrame / INTRO.fps,
    offsetY: INTRO.titleChip.offsetY,
  },
// flags: jedes items[i].startSec, flags.startSec und flags.endSec als r2(<alter Wert> + SHIFT_SEC)
// cta: startSec: r2(46.64 + SHIFT_SEC)

const FOOTAGE_SRC =
  "projects/craiss-viele-jahre/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4";

// Komponente: Parameter `hook` durch `titleChip` ersetzen; die Hook-Sequence ersetzen durch
          <Sequence from={0} durationInFrames={introEndFrame(INTRO)} name="Begrüßung + Flaggen-Wischer">
            <GreetingIntro layout={INTRO} />
          </Sequence>

          <Sequence
            from={s(titleChip.startSec)}
            durationInFrames={s(titleChip.endSec) - s(titleChip.startSec)}
            name="Titel-Chip"
          >
            <RedChip chip={titleChip} />
          </Sequence>
```
Den Kopfkommentar der Datei um eine Zeile ergänzen: „Seit 2026-09-16: Intro mit Flaggen-Wischern (intro-layout.json), Titel-Chip, alles hinter der Montage + D (Kopie „Claude 03 Begrüßung")."

- [ ] **Step 3: Vorschau-Eintrag 03**

```tsx
import { CraissVieleJahre, craissVieleJahreDefaults, INTRO_SHIFT_FRAMES, VIELE_JAHRE_SECONDS } from "../viele-jahre/Composition";

  "03": {
    src: "projects/craiss-viele-jahre/ohne-Animation/proxy/03_Viele_Jahre_Viele_Geschichten_Begruessung_ohneAnim_proxy.mp4",
    seconds: VIELE_JAHRE_SECONDS,
    Overlay: () => <CraissVieleJahre {...craissVieleJahreDefaults} footage={NO_FOOTAGE} />,
    // Satz-Untertitel sind auf den V3-Schnitt getimt → um die Verlängerung D versetzt zeigen
    Subs: () => (
      <Sequence from={INTRO_SHIFT_FRAMES} layout="none">
        <CraissVieleJahreSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />
      </Sequence>
    ),
    MixSubs: () => (
      <Sequence from={INTRO_SHIFT_FRAMES} layout="none">
        <CraissVieleJahreMixLayer />
      </Sequence>
    ),
    KeywordSubs: CraissVieleJahreKeywordLayer,
  },
```

- [ ] **Step 4: Typen und alle Tests**

Run: `npx tsc --noEmit && npx tsx --test src/clients/craiss/captionMix/*.test.ts src/clients/craiss/intro/*.test.ts`
Expected: keine Typfehler, alle Tests PASS.

- [ ] **Step 5: Länge gegen den Proxy prüfen**

Run: `/usr/bin/python3 -c "import json; print(json.load(open('/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/stand.json'))['proxy_frames'])"`
Expected: gleich `1291 + shiftFrames` (= `VIDEO_SECONDS × 25`).

---

### Task 12: Prüfung Video 03 und Abnahme aller Vorschauen

**Files:**
- Create: `tools/motion/scripts/craiss-intro-kontaktbogen.ts`

**Interfaces:**
- Consumes: `intro-layout.json`, Vorschau-Render 03.

- [ ] **Step 1: `craiss-intro-kontaktbogen.ts`**

```ts
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
```

- [ ] **Step 2: Vorschau 03 rendern (volle Vorschau-Größe, mit Guides) und Kontaktbögen**

```bash
npx remotion render src/index.ts Craiss-Vorschau-03-VieleJahre "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/review/03_intro_guides.mp4" --codec=h264 --crf=20 --public-dir=public-craiss --port=3149 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
npx tsx scripts/craiss-intro-kontaktbogen.ts "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/review/03_intro_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/review/03_intro_kontakt.jpg"
npx tsx scripts/craiss-chip-kontaktbogen.ts 03 "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/review/03_intro_guides.mp4" "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/review/03_schlagwoerter_kontakt.jpg"
```
Expected: zwei Kontaktbögen. Prüfen (Read-Tool):
- Auf `cutFrame − 1` und `cutFrame` jedes Wischers ist das Bild komplett mit der Flagge gedeckt (Schnitt unsichtbar).
- Auf den Sprech-Bildern jedes Shots ist die Person unverdeckt; die Begrüßung im Chip passt zur Person (Jakub PL, Victor HU, Adrian RO, Jan CZ).
- HALLO + Chip liegen unter den Gesichtern, innerhalb der Safe Zone; HALLO blendet vor dem roten Wischer aus; der Titel-Chip steht über Thomas unterhalb des Kinns und ist vor dem Kamerawechsel weg.
- Flaggen-Passage und CTA sitzen auf den verschobenen Stellen (Flaggen zur Aufzählung, CTA auf dem Drohnen-Endshot).
Befunde beheben (HELLO_TOP, `offsetY`, Ein-/Auslauf in `r2_intro_layout.py` → dann Task 6–9 und 11 erneut), bis alles stimmt.

- [ ] **Step 3: Abnahme durch den User**

Im Chat melden: Studio starten (`npm run studio` in `tools/motion`), Ordner `Craiss → Vorschau-Neu`, alle 5 Vorschauen ansehen (Standard `subtitleStyle = schlagwort`), in Resolve die Kopie „Claude 03 Begrüßung …" anhören (Musik-Übergang vorn, Swooshes, „Low Airy Whoosh"). **Erst nach Freigabe weiter mit Phase C.**

---

## Phase C — Lieferung

### Task 13: Alpha-Renders v2

**Files:**
- Create (Renders): je Charge `Ergebnisse/Renders/0X_<Name>_Alpha_Komplett_v2.mov`

- [ ] **Step 1: Rendern (einzeln, bei „got no response" einfach wiederholen)**

```bash
npx remotion render src/index.ts Craiss-Alpha-01-ErsterTag "../../projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/Ergebnisse/Renders/01_ErsterTag_Alpha_Komplett_v2.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444 --public-dir=public-craiss --port=3151
npx remotion render src/index.ts Craiss-Alpha-02-Arbeitsalltag "../../projects/Craiss Logistik/4 Ads/2026-08 Einblick Arbeitsalltag/Ergebnisse/Renders/02_Arbeitsalltag_Alpha_Komplett_v2.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444 --public-dir=public-craiss --port=3152
npx remotion render src/index.ts Craiss-Alpha-03-VieleJahre "../../projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/Ergebnisse/Renders/03_VieleJahre_Alpha_Komplett_v2.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444 --public-dir=public-craiss --port=3153
npx remotion render src/index.ts Craiss-Alpha-04-Funnel "../../projects/Craiss Logistik/4 Ads/2026-08 Funnel Video/Ergebnisse/Renders/04_Funnel_Alpha_Komplett_v2.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444 --public-dir=public-craiss --port=3154
npx remotion render src/index.ts Craiss-Alpha-05-Testimonial "../../projects/Craiss Logistik/4 Ads/2026-08 Testimonial Video/Ergebnisse/Renders/05_Testimonial_Alpha_Komplett_v2.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444 --public-dir=public-craiss --port=3155
```

- [ ] **Step 2: Format und Länge prüfen**

```bash
for f in "../../projects/Craiss Logistik/4 Ads/"*/Ergebnisse/Renders/*_Alpha_Komplett_v2.mov; do echo "== $f"; ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,nb_read_frames -of default=nw=1 "$f"; done
```
Expected: je Datei `prores`, Profil 4444, `yuva444p12le`, 2160×3840, 25/1; Frames 01: 751, 02: 1853, 03: 1291 + `shiftFrames`, 04: 1478, 05: 1315 (wie v1, 03 um D länger).

- [ ] **Step 3: Flacker-Prüfung**

```bash
for f in "../../projects/Craiss Logistik/4 Ads/"*/Ergebnisse/Renders/*_Alpha_Komplett_v2.mov; do echo "== $f"; bash scripts/flicker-check.sh "$f"; done
```
Expected: Kandidaten nur an Ein-/Ausblendungen, Chip-Wechseln und (03) Wischer-Kanten; jeden anderen Kandidaten per Einzelbild prüfen.

- [ ] **Step 4: Alpha leer, wo keine Grafik steht**

Frames ohne Grafik: 01 → 325 (13,0 s), 02 → 425 (17,0 s), 03 → 500 + `shiftFrames`, 04 → 500 (20,0 s), 05 → 400 (16,0 s).

```bash
/usr/bin/python3 - <<'EOF'
import json, subprocess
from pathlib import Path
base = Path("/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads")
D = json.load(open("/Users/jansantos/NIRO Studio/tools/motion/src/clients/craiss/projects/viele-jahre/intro-layout.json"))["shiftFrames"]
for charge, name, frame in [("2026-08 Dein erster Tag", "01_ErsterTag", 325), ("2026-08 Einblick Arbeitsalltag", "02_Arbeitsalltag", 425),
                            ("2026-08 Viele Jahre Viele Geschichten", "03_VieleJahre", 500 + D), ("2026-08 Funnel Video", "04_Funnel", 500),
                            ("2026-08 Testimonial Video", "05_Testimonial", 400)]:
    mov = base / charge / "Ergebnisse/Renders" / f"{name}_Alpha_Komplett_v2.mov"
    png = base / charge / "_intern/review/alpha_leer.png"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(mov), "-vf", f"select=eq(n\\,{frame}),alphaextract",
                    "-frames:v", "1", str(png)], check=True)
    maxi = subprocess.run(["magick", str(png), "-format", "%[fx:maxima]", "info:"], capture_output=True, text=True).stdout
    print(name, frame, "Alpha-Maximum", maxi)
EOF
```
Expected: `Alpha-Maximum 0` für alle fünf Dateien.

---

### Task 14: Alpha v2 in die Resolve-Kopie (03)

**Files:**
- Create: `…/_intern/resolve/r8_alpha_einsetzen.py`

- [ ] **Step 1: `r8_alpha_einsetzen.py`**

```python
"""Schritt 8: 03_VieleJahre_Alpha_Komplett_v2.mov importieren (eigener Bin unter 03_GRAPHICS) und in der Kopie
auf eine neue oberste Spur „NIRO Alpha Komplett v2" ab Neu-Frame 0 legen — nur Kopie."""
import datetime

from rk_common import CHARGE, UserZustand, kopie, lade_stand, projekt

DATEI = CHARGE / "Ergebnisse/Renders/03_VieleJahre_Alpha_Komplett_v2.mov"
BASIS = int(lade_stand()["neu_start_frame"])
r, p = projekt()
k = kopie(p)
mp = p.GetMediaPool()
user = UserZustand(p)
try:
    root = mp.GetRootFolder()
    grafik = next((f for f in root.GetSubFolderList() or [] if f.GetName() == "03_GRAPHICS"), root)
    ordner = mp.AddSubFolder(grafik, f"Claude Alpha Komplett v2 {datetime.datetime.now():%Y-%m-%d %H%M}")
    mp.SetCurrentFolder(ordner)
    clips = mp.ImportMedia([str(DATEI)]) or []
    if len(clips) != 1:
        raise SystemExit(f"Import lieferte {len(clips)} Clips.")
    p.SetCurrentTimeline(k)
    if not k.AddTrack("video"):
        raise SystemExit("Videospur nicht angelegt.")
    spur = k.GetTrackCount("video")
    k.SetTrackName("video", spur, "NIRO Alpha Komplett v2")
    dauer = int(clips[0].GetClipProperty("Frames"))
    neu = mp.AppendToTimeline([{"mediaPoolItem": clips[0], "startFrame": 0, "endFrame": dauer,
                                "recordFrame": BASIS, "trackIndex": spur, "mediaType": 1}]) or []
    if len(neu) != 1 or (int(neu[0].GetStart()), int(neu[0].GetDuration())) != (BASIS, dauer):
        raise SystemExit(f"Readback Alpha: {[(i.GetStart(), i.GetDuration()) for i in neu]}")
    print(f"Alpha v2 auf V{spur} ab Frame {BASIS}, {dauer} Frames, Bin '{ordner.GetName()}'")
finally:
    user.zuruecksetzen()
```

- [ ] **Step 2: Ausführen (Wiedergabe abfragen)**

Run: `"/Users/jansantos/NIRO Studio/tools/autocut/venv/bin/python" "/Users/jansantos/NIRO Studio/projects/Craiss Logistik/4 Ads/2026-08 Viele Jahre Viele Geschichten/_intern/resolve/r8_alpha_einsetzen.py"`
Expected: `Alpha v2 auf V10 ab Frame …, 1291 + D Frames`, User-Zustand zurück.

- [ ] **Step 3: 01, 02, 04, 05**

Im Chat fragen: v2-Dateien für 01/02/04/05 in eigene Kopien der Timelines legen (analog, Kopie-Präfix je Video) oder dem Cutter überlassen; NAS-Ablage (`03_Medien/02_Assets/07_Animation/<Videoordner>/`, ohne Tonspur) nur nach ausdrücklicher Freigabe.

---

### Task 15: Protokolle, Doku, Memory

**Files:**
- Modify: `projects/Craiss Logistik/4 Ads/<Charge>/Protokoll.md` (×5)
- Modify: `tools/resolve/WORKFLOW-Resolve.md` (Gemessenes Verhalten: `SetStartTimecode`, OTIO/XML-Export von Compound Clips, `CopyGrades` wenn genutzt)
- Modify: Memory `craiss-recruiting.md` + Index-Zeile in `MEMORY.md`

- [ ] **Step 1: Protokolle**

Je Charge ein Eintrag „## 2026-09-16 — Schlagwort-Chips statt Untertitel (Kundenfeedback)" mit: Chips (Anzahl, Texte), Vorschau-Umschalter, gelieferte Datei `…_Alpha_Komplett_v2.mov` (Frames, Prüfungen), Offenes (Einsetzen in Resolve/NAS). Für 03 zusätzlich: Kopie-Name, Weg „start_tc"/„handgriff", D, neue Shot-Quellen (aus `intro-layout.json`), Grading-Befund, Proxy-Pfad, Titel „VIELE SPRACHEN. EIN TEAM.".

- [ ] **Step 2: Resolve-Doku**

Unter „Gemessenes Verhalten 21.1.0.14" die Befunde aus Task 5, 7 und 9 als je einen Punkt ergänzen (z. B. „`SetStartTimecode` auf einer Kopie: Clips behalten ihre absolute Position" oder „… wandern mit").

- [ ] **Step 3: Memory**

`craiss-recruiting.md`: Stand 16.09. ergänzen (Chips geliefert als v2, Kopie-Name 03, D, Weg, offene Punkte); Index-Zeile in `MEMORY.md` kurz aktualisieren.

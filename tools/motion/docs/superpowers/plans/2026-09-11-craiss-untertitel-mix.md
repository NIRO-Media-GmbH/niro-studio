# Craiss Untertitel-Mix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Neuer, abwechslungsreicher Untertitel-Look („Mix": Grundzeile, Hero-Wort in drei Varianten, Wort-Kasten, Glas-Wort) für Craiss Video 01, sichtbar in `Craiss → Vorschau-Neu` mit Umschalter alt/neu.

**Architecture:** Ein handgepflegter Plan pro Video (`captions/<id>.plan.json`, Cue = Satz) wird aus den bestehenden Caption-Seiten erzeugt und von Hand mit Treatment/Zone/Hero-Wort versehen. Reine Logik (Schema, Prüfregeln, Layout-Zonen, Timing, Plan-Erzeugung) liegt in kleinen TS-Modulen mit `node:test`-Tests; ein Remotion-Renderer (`CaptionMix.tsx`) zeichnet den Plan. Die Vorschau-Komposition bekommt ein Prop `subtitleStyle`.

**Tech Stack:** Remotion 4.0.519, React 18, zod, TypeScript; Tests mit `npx tsx --test` (Node 24 `node:test`, keine neue Abhängigkeit).

**Spec:** `tools/motion/docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md`

## Global Constraints

- Arbeitsverzeichnis für alle Befehle: `/Users/jansantos/NIRO Studio/tools/motion`.
- Fonts/Farben nur aus `src/clients/craiss/lib.tsx`: `FONT_BLACK`, `FONT_BOLD`, `WHITE`, `RED` (`#CD202C`), `CRAISS_BLUE` (`#002F5F`), Feder `SOFT`.
- Animiert werden nur `transform` und `opacity`; Deckkraft linear (`interpolate`), Federn (`spring` mit `SOFT`) nur auf Transforms; kein Bounce.
- Basis-Bühne 1080×1920; Unterkante aller Blöcke ≤ 1500 px; seitlicher Rand 54 px; Oberkante ≥ `chinY` + 110 px.
- Ein Satz erscheint nur, wenn er vom ersten bis zum letzten Wort in einem freien Fenster liegt (Sperrfenster = bestehende `BLOCKED`-Listen).
- Nie ein Wort vor seinem Wortanfang − 0,08 s zeigen.
- „Kein Stress" wird nicht eingeblendet (steht bereits in der drop-Liste von `scripts/craiss-captions.ts`).
- Commits nur, wenn Jan/David es ausdrücklich freigeben (Studio-Regel) — die Commit-Schritte unten sind entsprechend markiert.
- Keine Dateien unter `/Volumes/NIRO-SSD-03/...` ändern.

## File Structure

| Datei | Verantwortung |
|---|---|
| Create `src/clients/craiss/captionMix/layout.ts` | Zonen → Blockposition, Grenzwerte, geschätzte Blockhöhen |
| Create `src/clients/craiss/captionMix/plan.ts` | zod-Schema des Plans, Typen, `validatePlan` |
| Create `src/clients/craiss/captionMix/timing.ts` | Satz-Sichtbarkeit, Wort-Einblendung, aktive Seite/Wort |
| Create `src/clients/craiss/captionMix/buildPlan.ts` | Caption-Seiten → Satz-Cues |
| Create `src/clients/craiss/captionMix/*.test.ts` | Tests der vier Logik-Module |
| Create `scripts/craiss-caption-plan.ts` | CLI: Plan erzeugen (`--force`) / prüfen (`--check`) |
| Create `src/clients/craiss/captionMix/CaptionMix.tsx` | Remotion-Renderer `CaptionMixTrack` |
| Create `src/clients/craiss/captions/erster-tag-v3.plan.json` | Plan Video 01 (erzeugt + von Hand gesetzt) |
| Modify `src/clients/craiss/projects/erster-tag/CompositionSubtitled.tsx` | `CraissErsterTagMixLayer` exportieren |
| Modify `src/clients/craiss/projects/vorschau/Composition.tsx` | Prop `subtitleStyle`, Mix-Layer für 01 |
| Modify `projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/Protokoll.md` | Protokoll-Pflicht |

---

### Task 1: Layout-Zonen

**Files:**
- Create: `src/clients/craiss/captionMix/layout.ts`
- Test: `src/clients/craiss/captionMix/layout.test.ts`

**Interfaces:**
- Produces: `BASE_W`, `MARGIN_X`, `SIDE_WIDTH`, `BOTTOM_LIMIT`, `CHIN_GAP`, `ZONE_DEFAULT_TOP`, `BLOCK_HEIGHT`, `type Align`, `type BlockBox`, `resolveBlock(zone: Zone, y?: number): BlockBox`. Typen `Zone`/`Treatment` kommen aus Task 2 (`plan.ts`) — in Task 1 als lokale Union deklarieren und in Task 2 auf den Import umstellen ist NICHT nötig: `layout.ts` importiert sie per `import type` aus `./plan`, deshalb Task 1 und 2 zusammen kompilieren (Tests von Task 1 laufen erst nach Step 3 von Task 2 grün).

- [ ] **Step 1: Test schreiben**

```ts
// src/clients/craiss/captionMix/layout.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveBlock, BASE_W, MARGIN_X, SIDE_WIDTH, ZONE_DEFAULT_TOP } from "./layout";

test("top: volle Breite, zentriert, Standardhöhe", () => {
  assert.deepEqual(resolveBlock("top"), { top: ZONE_DEFAULT_TOP.top, left: MARGIN_X, width: BASE_W - 2 * MARGIN_X, align: "center" });
});

test("side-l links bündig, side-r rechts bündig", () => {
  assert.deepEqual(resolveBlock("side-l"), { top: 700, left: 54, width: SIDE_WIDTH, align: "left" });
  assert.deepEqual(resolveBlock("side-r"), { top: 700, left: 1080 - 54 - SIDE_WIDTH, width: SIDE_WIDTH, align: "right" });
});

test("y überschreibt die Standardhöhe", () => {
  assert.equal(resolveBlock("chest", 1234).top, 1234);
  assert.equal(resolveBlock("chest").top, 1150);
});
```

- [ ] **Step 2: Implementierung**

```ts
// src/clients/craiss/captionMix/layout.ts
// ============================================================
// Craiss Untertitel-Mix — Zonen und Grenzwerte (Basis 1080×1920)
// Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import type { Treatment, Zone } from "./plan";

export const BASE_W = 1080;
export const MARGIN_X = 54;
export const SIDE_WIDTH = 620;
export const BOTTOM_LIMIT = 1500; // darunter liegt die Plattform-UI
export const CHIN_GAP = 110; // Mindestabstand Oberkante ↔ Kinn

// top 18–32 %, side 30–55 %, chest = Nahaufnahme Brusthöhe
export const ZONE_DEFAULT_TOP: Record<Zone, number> = {
  top: 400,
  "side-l": 700,
  "side-r": 700,
  chest: 1150,
};

// Geschätzte Blockhöhen (px) für die Unterkanten-Prüfung
export const BLOCK_HEIGHT: Record<Treatment, number> = {
  rail: 130, // zwei Zeilen Grundzeile
  "hero-white": 300, // Grundzeile + Hero 130 px + Grundzeile
  "hero-red": 260,
  "hero-blue": 220,
  wordbox: 280, // Grundzeile + Kastenwort bzw. zwei Kastenzeilen
};

export type Align = "center" | "left" | "right";
export type BlockBox = { top: number; left: number; width: number; align: Align };

export const resolveBlock = (zone: Zone, y?: number): BlockBox => {
  const top = y ?? ZONE_DEFAULT_TOP[zone];
  if (zone === "side-l") return { top, left: MARGIN_X, width: SIDE_WIDTH, align: "left" };
  if (zone === "side-r") return { top, left: BASE_W - MARGIN_X - SIDE_WIDTH, width: SIDE_WIDTH, align: "right" };
  return { top, left: MARGIN_X, width: BASE_W - 2 * MARGIN_X, align: "center" };
};
```

- [ ] **Step 3: weiter mit Task 2** (Tests laufen dort gemeinsam).

---

### Task 2: Plan-Schema und Prüfregeln

**Files:**
- Create: `src/clients/craiss/captionMix/plan.ts`
- Test: `src/clients/craiss/captionMix/plan.test.ts`

**Interfaces:**
- Consumes: `resolveBlock`, `BLOCK_HEIGHT`, `BOTTOM_LIMIT`, `CHIN_GAP` aus Task 1.
- Produces: `zoneSchema`, `treatmentSchema`, `tokenSchema`, `glassSchema`, `planCueSchema`, `captionPlanSchema`; Typen `Zone`, `Treatment`, `PlanToken`, `PlanCue`, `CaptionPlan`; `validatePlan(plan: CaptionPlan): string[]`; `HERO_TREATMENTS: ReadonlySet<Treatment>`.

- [ ] **Step 1: Test schreiben**

```ts
// src/clients/craiss/captionMix/plan.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { captionPlanSchema, validatePlan, type PlanCue } from "./plan";

const tok = (text: string, start: number) => ({ text, start, end: start + 0.3 });
const cue = (over: Partial<PlanCue>): PlanCue => ({
  id: "cc-01",
  start: 1,
  end: 3,
  tokens: [tok("Das", 1.08), tok("ist", 1.4), tok("kinderleicht", 1.8), tok("gebaut.", 2.3)],
  pages: [0],
  treatment: "rail",
  zone: "chest",
  glass: null,
  ...over,
});

test("gültiger Plan parst und hat keine Fehler", () => {
  const plan = captionPlanSchema.parse({ video: "x", cues: [cue({})] });
  assert.deepEqual(validatePlan(plan), []);
});

test("Hero ohne heroIndex ist ein Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ treatment: "hero-white" })] });
  assert.match(errs.join("\n"), /heroIndex/);
});

test("zwei Hero-Sätze hintereinander mit gleicher Variante sind ein Fehler", () => {
  const errs = validatePlan({
    video: "x",
    cues: [
      cue({ id: "cc-01", treatment: "hero-red", heroIndex: 2 }),
      cue({ id: "cc-02", start: 3, end: 5, treatment: "rail" }),
      cue({ id: "cc-03", start: 5, end: 7, treatment: "hero-red", heroIndex: 2 }),
    ],
  });
  assert.match(errs.join("\n"), /cc-03: gleiche Hero-Variante/);
});

test("Hero über eine Seitengrenze ist ein Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ treatment: "hero-blue", heroIndex: 1, heroCount: 2, pages: [0, 2] })] });
  assert.match(errs.join("\n"), /Seitengrenze/);
});

test("mehr als zwei Glas-Wörter sind ein Fehler", () => {
  const glass = { text: "IMMER", startSec: 1.5, zone: "top" as const };
  const errs = validatePlan({
    video: "x",
    cues: [1, 2, 3].map((n) => cue({ id: `cc-0${n}`, start: n * 2, end: n * 2 + 1.9, glass: { ...glass, startSec: n * 2 + 0.5 } })),
  });
  assert.match(errs.join("\n"), /Glas-Wörter: 3 > 2/);
});

test("Oberkante zu nah am Kinn und Unterkante zu tief sind Fehler", () => {
  assert.match(validatePlan({ video: "x", cues: [cue({ y: 800, chinY: 720 })] }).join("\n"), /zu nah am Kinn/);
  assert.match(validatePlan({ video: "x", cues: [cue({ y: 1400 })] }).join("\n"), /Unterkante 1530 > 1500/);
});

test("überlappende Sätze und ungültige pages sind Fehler", () => {
  const errs = validatePlan({ video: "x", cues: [cue({ id: "cc-01" }), cue({ id: "cc-02", start: 2.5, end: 4, pages: [1] })] });
  assert.match(errs.join("\n"), /cc-02: überlappt cc-01/);
  assert.match(errs.join("\n"), /cc-02: pages ungültig/);
});
```

- [ ] **Step 2: Tests laufen lassen — müssen scheitern**

Run: `npx tsx --test src/clients/craiss/captionMix/layout.test.ts src/clients/craiss/captionMix/plan.test.ts`
Expected: FAIL (`Cannot find module './plan'`)

- [ ] **Step 3: Implementierung**

```ts
// src/clients/craiss/captionMix/plan.ts
// ============================================================
// Craiss Untertitel-Mix — Plan-Schema und Prüfregeln
// Ein Cue = ein Satz. Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import { z } from "zod";
import { BLOCK_HEIGHT, BOTTOM_LIMIT, CHIN_GAP, resolveBlock } from "./layout";

export const zoneSchema = z.enum(["top", "side-l", "side-r", "chest"]);
export const treatmentSchema = z.enum(["rail", "hero-white", "hero-red", "hero-blue", "wordbox"]);
export const tokenSchema = z.object({ text: z.string(), start: z.number(), end: z.number() });
export const glassSchema = z.object({
  text: z.string(),
  startSec: z.number(),
  zone: zoneSchema,
  y: z.number().optional(),
});
export const planCueSchema = z.object({
  id: z.string(),
  start: z.number(),
  end: z.number(),
  tokens: z.array(tokenSchema).min(1),
  pages: z.array(z.number().int()).min(1),
  treatment: treatmentSchema,
  heroIndex: z.number().int().optional(),
  heroCount: z.number().int().min(1).optional(),
  boxIndices: z.array(z.number().int()).optional(),
  zone: zoneSchema,
  y: z.number().optional(),
  chinY: z.number().optional(),
  glass: glassSchema.nullable().optional(),
});
export const captionPlanSchema = z.object({ video: z.string(), cues: z.array(planCueSchema) });

export type Zone = z.infer<typeof zoneSchema>;
export type Treatment = z.infer<typeof treatmentSchema>;
export type PlanToken = z.infer<typeof tokenSchema>;
export type PlanCue = z.infer<typeof planCueSchema>;
export type CaptionPlan = z.infer<typeof captionPlanSchema>;

export const HERO_TREATMENTS: ReadonlySet<Treatment> = new Set(["hero-white", "hero-red", "hero-blue"]);

const pageOf = (pages: number[], index: number) => pages.filter((p) => p <= index).length - 1;

export const validatePlan = (plan: CaptionPlan): string[] => {
  const errors: string[] = [];
  let lastHero: Treatment | null = null;
  let glassCount = 0;

  plan.cues.forEach((cue, i) => {
    const prev = plan.cues[i - 1];
    if (prev && cue.start < prev.end - 0.001) errors.push(`${cue.id}: überlappt ${prev.id}`);

    const pagesOk =
      cue.pages[0] === 0 &&
      cue.pages.every((p, k) => k === 0 || p > cue.pages[k - 1]) &&
      cue.pages.every((p) => p < cue.tokens.length);
    if (!pagesOk) errors.push(`${cue.id}: pages ungültig`);

    if (HERO_TREATMENTS.has(cue.treatment)) {
      const from = cue.heroIndex;
      const count = cue.heroCount ?? 1;
      if (from === undefined || from < 0 || from + count > cue.tokens.length) {
        errors.push(`${cue.id}: heroIndex fehlt oder außerhalb`);
      } else if (pagesOk && pageOf(cue.pages, from) !== pageOf(cue.pages, from + count - 1)) {
        errors.push(`${cue.id}: Hero-Wortgruppe liegt über einer Seitengrenze`);
      }
      if (lastHero === cue.treatment) errors.push(`${cue.id}: gleiche Hero-Variante wie der vorige Hero-Satz`);
      lastHero = cue.treatment;
    }

    if (cue.boxIndices?.some((b) => b < 0 || b >= cue.tokens.length)) errors.push(`${cue.id}: boxIndices außerhalb`);

    const box = resolveBlock(cue.zone, cue.y);
    const bottom = box.top + BLOCK_HEIGHT[cue.treatment];
    if (bottom > BOTTOM_LIMIT) errors.push(`${cue.id}: Unterkante ${bottom} > ${BOTTOM_LIMIT}`);
    if (cue.chinY !== undefined && box.top < cue.chinY + CHIN_GAP) {
      errors.push(`${cue.id}: Oberkante ${box.top} zu nah am Kinn (${cue.chinY} + ${CHIN_GAP})`);
    }

    if (cue.glass) {
      glassCount++;
      if (cue.glass.startSec < cue.start || cue.glass.startSec >= cue.end) errors.push(`${cue.id}: Glas-Start außerhalb des Satzes`);
    }
  });

  if (glassCount > 2) errors.push(`Glas-Wörter: ${glassCount} > 2`);
  return errors;
};
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `npx tsx --test src/clients/craiss/captionMix/layout.test.ts src/clients/craiss/captionMix/plan.test.ts`
Expected: `ℹ pass 10`, `ℹ fail 0`

- [ ] **Step 5: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captionMix/layout.ts src/clients/craiss/captionMix/layout.test.ts src/clients/craiss/captionMix/plan.ts src/clients/craiss/captionMix/plan.test.ts
git commit -m "feat(craiss): Untertitel-Mix — Plan-Schema, Prüfregeln, Layout-Zonen"
```

---

### Task 3: Timing

**Files:**
- Create: `src/clients/craiss/captionMix/timing.ts`
- Test: `src/clients/craiss/captionMix/timing.test.ts`

**Interfaces:**
- Consumes: `freeWindows(blocked, fps, durationInFrames, minGapFrames)` und `type BlockedRange` aus `src/clients/craiss/Subtitles.tsx` (bestehend).
- Produces: `LEAD_SEC = 0.08`, `REVEAL_FRAMES = 5`, `type FrameWindow = { from: number; to: number }`, `cueWindow(cue: { start: number; end: number; tokens: { end: number }[] }, windows: FrameWindow[], fps: number): FrameWindow | null`, `revealProgress(tokenStart: number, frame: number, fps: number): number`, `activeTokenIndex(tokens: { start: number }[], t: number): number`, `currentPageIndex(pages: number[], tokens: { start: number }[], t: number): number`, `pageTokenRange(pages: number[], tokenCount: number, pageIdx: number): [number, number]`; Re-Export `freeWindows`, `BlockedRange`.

- [ ] **Step 1: Test schreiben**

```ts
// src/clients/craiss/captionMix/timing.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { activeTokenIndex, cueWindow, currentPageIndex, pageTokenRange, revealProgress } from "./timing";

const FPS = 25;
const cue = { start: 4.0, end: 6.0, tokens: [{ end: 4.5 }, { end: 5.4 }] };

test("Satz komplett im freien Fenster → sichtbar, am Fensterende gekappt", () => {
  assert.deepEqual(cueWindow(cue, [{ from: 90, to: 145 }], FPS), { from: 100, to: 145 });
});

test("Satzanfang oder letztes Wort unter einer Grafik → Satz entfällt", () => {
  assert.equal(cueWindow(cue, [{ from: 105, to: 200 }], FPS), null);
  assert.equal(cueWindow(cue, [{ from: 90, to: 130 }], FPS), null);
});

test("Wort-Einblendung: 0 vor Wortanfang−0,08 s, 1 nach 5 Frames", () => {
  assert.equal(revealProgress(2.0, 47, FPS), 0);
  assert.equal(revealProgress(2.0, 48, FPS), 0);
  assert.equal(revealProgress(2.0, 53, FPS), 1);
});

test("aktives Wort und aktuelle Seite", () => {
  const toks = [{ start: 1.0 }, { start: 1.5 }, { start: 2.0 }, { start: 2.6 }];
  assert.equal(activeTokenIndex(toks, 0.9), -1);
  assert.equal(activeTokenIndex(toks, 1.49), 1);
  assert.equal(currentPageIndex([0, 2], toks, 1.9), 0);
  assert.equal(currentPageIndex([0, 2], toks, 1.93), 1);
  assert.deepEqual(pageTokenRange([0, 2], 4, 0), [0, 2]);
  assert.deepEqual(pageTokenRange([0, 2], 4, 1), [2, 4]);
});
```

- [ ] **Step 2: Test laufen lassen — muss scheitern**

Run: `npx tsx --test src/clients/craiss/captionMix/timing.test.ts`
Expected: FAIL (`Cannot find module './timing'`)

- [ ] **Step 3: Implementierung**

```ts
// src/clients/craiss/captionMix/timing.ts
// ============================================================
// Craiss Untertitel-Mix — Timing (Sichtbarkeit, Wort-Einblendung, Seiten)
// ============================================================
import { freeWindows, type BlockedRange } from "../Subtitles";

export { freeWindows, type BlockedRange };

export const LEAD_SEC = 0.08; // Wort erscheint so viel vor seinem Anfang
export const REVEAL_FRAMES = 5;

export type FrameWindow = { from: number; to: number };

// Ganze Sinneinheiten: sichtbar nur, wenn der Satz vom Anfang bis zum Ende
// des letzten Worts in EINEM freien Fenster liegt. Der Nachlauf nach dem
// letzten Wort darf am Fensterende gekappt werden.
export const cueWindow = (
  cue: { start: number; end: number; tokens: { end: number }[] },
  windows: FrameWindow[],
  fps: number,
): FrameWindow | null => {
  const from = Math.round(cue.start * fps);
  const lastWordEnd = Math.round(cue.tokens[cue.tokens.length - 1].end * fps);
  const to = Math.round(cue.end * fps);
  const w = windows.find((win) => win.from <= from && lastWordEnd <= win.to);
  return w ? { from, to: Math.min(to, w.to) } : null;
};

export const revealProgress = (tokenStart: number, frame: number, fps: number): number => {
  const at = Math.round((tokenStart - LEAD_SEC) * fps);
  return Math.min(1, Math.max(0, (frame - at) / REVEAL_FRAMES));
};

export const activeTokenIndex = (tokens: { start: number }[], t: number): number => {
  let idx = -1;
  tokens.forEach((tok, i) => {
    if (t >= tok.start - 0.02) idx = i;
  });
  return idx;
};

export const currentPageIndex = (pages: number[], tokens: { start: number }[], t: number): number => {
  let idx = 0;
  pages.forEach((p, k) => {
    if (t >= tokens[p].start - LEAD_SEC) idx = k;
  });
  return idx;
};

export const pageTokenRange = (pages: number[], tokenCount: number, pageIdx: number): [number, number] => [
  pages[pageIdx],
  pages[pageIdx + 1] ?? tokenCount,
];
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `npx tsx --test src/clients/craiss/captionMix/timing.test.ts`
Expected: `ℹ pass 4`, `ℹ fail 0`

- [ ] **Step 5: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captionMix/timing.ts src/clients/craiss/captionMix/timing.test.ts
git commit -m "feat(craiss): Untertitel-Mix — Timing (ganze Sätze, Wort-Einblendung)"
```

---

### Task 4: Plan-Erzeugung und CLI

**Files:**
- Create: `src/clients/craiss/captionMix/buildPlan.ts`
- Test: `src/clients/craiss/captionMix/buildPlan.test.ts`
- Create: `scripts/craiss-caption-plan.ts`

**Interfaces:**
- Consumes: `type CaptionPage` aus `src/clients/craiss/Subtitles.tsx`; `captionPlanSchema`, `validatePlan`, `type CaptionPlan`, `type PlanCue` aus Task 2.
- Produces: `buildPlanFromPages(video: string, pages: CaptionPage[]): CaptionPlan`; CLI `npx tsx scripts/craiss-caption-plan.ts <id…> [--force] [--check]`, schreibt `src/clients/craiss/captions/<id>.plan.json`.

- [ ] **Step 1: Test schreiben**

```ts
// src/clients/craiss/captionMix/buildPlan.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildPlanFromPages } from "./buildPlan";

const page = (start: number, end: number, words: string[]) => ({
  start,
  end,
  tokens: words.map((text, i) => ({ text, start: start + 0.08 + i * 0.3, end: start + 0.3 + i * 0.3 })),
});

test("Seiten werden bis zum Satzende zu einem Cue zusammengefasst", () => {
  const plan = buildPlanFromPages("v", [
    page(1.0, 2.0, ["Keiner", "hat", "Probleme,", "egal"]),
    page(2.0, 3.1, ["ob", "jung", "oder", "alt."]),
    page(3.2, 4.0, ["Jeder", "kommt", "klar", "damit."]),
  ]);
  assert.equal(plan.cues.length, 2);
  assert.deepEqual(plan.cues[0].pages, [0, 4]);
  assert.equal(plan.cues[0].tokens.length, 8);
  assert.equal(plan.cues[0].id, "cc-01");
  assert.equal(plan.cues[1].id, "cc-02");
  assert.equal(plan.cues[0].treatment, "rail");
  assert.equal(plan.cues[0].zone, "chest");
});

test("Satzende wird auf den Beginn des nächsten Satzes gekappt", () => {
  const plan = buildPlanFromPages("v", [page(1.0, 2.6, ["Du", "bist", "keine", "Zahl."]), page(2.5, 3.5, ["Das", "ist", "wichtig."])]);
  assert.equal(plan.cues[0].end, 2.5);
});
```

- [ ] **Step 2: Test laufen lassen — muss scheitern**

Run: `npx tsx --test src/clients/craiss/captionMix/buildPlan.test.ts`
Expected: FAIL (`Cannot find module './buildPlan'`)

- [ ] **Step 3: Implementierung `buildPlan.ts`**

```ts
// src/clients/craiss/captionMix/buildPlan.ts
// ============================================================
// Craiss Untertitel-Mix — Caption-Seiten (2–5 Wörter) → Satz-Cues
// Standard: Grundzeile auf Brusthöhe; Treatments setzt man danach von Hand.
// ============================================================
import type { CaptionPage } from "../Subtitles";
import type { CaptionPlan, PlanCue } from "./plan";

const SENTENCE_END = /[.!?]["“”]?$/;

export const buildPlanFromPages = (video: string, pages: CaptionPage[]): CaptionPlan => {
  const cues: PlanCue[] = [];
  let group: CaptionPage[] = [];

  const flush = () => {
    if (group.length === 0) return;
    const starts: number[] = [];
    let n = 0;
    for (const p of group) {
      starts.push(n);
      n += p.tokens.length;
    }
    cues.push({
      id: `cc-${String(cues.length + 1).padStart(2, "0")}`,
      start: group[0].start,
      end: group[group.length - 1].end,
      tokens: group.flatMap((p) => p.tokens),
      pages: starts,
      treatment: "rail",
      zone: "chest",
      glass: null,
    });
    group = [];
  };

  for (const page of pages) {
    group.push(page);
    if (SENTENCE_END.test(page.tokens[page.tokens.length - 1].text)) flush();
  }
  flush();

  for (let i = 0; i < cues.length - 1; i++) cues[i].end = Math.min(cues[i].end, cues[i + 1].start);
  return { video, cues };
};
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `npx tsx --test src/clients/craiss/captionMix/buildPlan.test.ts`
Expected: `ℹ pass 2`, `ℹ fail 0`

- [ ] **Step 5: CLI schreiben**

```ts
// scripts/craiss-caption-plan.ts
// ============================================================
// Craiss Untertitel-Mix — Plan erzeugen / prüfen
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3          (neu, falls nicht vorhanden)
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --force  (überschreiben)
//   npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --check  (Prüfregeln + Anteile)
// Quelle: src/clients/craiss/captions/<id>.json (scripts/craiss-captions.ts)
// ============================================================
import fs from "node:fs";
import path from "node:path";
import { buildPlanFromPages } from "../src/clients/craiss/captionMix/buildPlan";
import { captionPlanSchema, validatePlan } from "../src/clients/craiss/captionMix/plan";

const DIR = path.resolve(__dirname, "../src/clients/craiss/captions");
const args = process.argv.slice(2);
const force = args.includes("--force");
const check = args.includes("--check");
const ids = args.filter((a) => !a.startsWith("--"));

for (const id of ids) {
  const planPath = path.join(DIR, `${id}.plan.json`);

  if (check) {
    const plan = captionPlanSchema.parse(JSON.parse(fs.readFileSync(planPath, "utf8")));
    const errors = validatePlan(plan);
    const counts: Record<string, number> = {};
    for (const c of plan.cues) counts[c.treatment] = (counts[c.treatment] ?? 0) + 1;
    const glass = plan.cues.filter((c) => c.glass).length;
    console.log(`${id}: ${plan.cues.length} Sätze — ${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(", ")}, Glas ${glass}`);
    for (const e of errors) console.log(`  ✗ ${e}`);
    if (errors.length === 0) console.log("  ✓ keine Fehler");
    else process.exitCode = 1;
    continue;
  }

  if (fs.existsSync(planPath) && !force) {
    console.log(`${id}: Plan existiert schon — mit --force überschreiben`);
    continue;
  }
  const pages = JSON.parse(fs.readFileSync(path.join(DIR, `${id}.json`), "utf8")).pages;
  const plan = buildPlanFromPages(id, pages);
  fs.writeFileSync(planPath, JSON.stringify(plan, null, 1) + "\n");
  console.log(`${id}: ${plan.cues.length} Sätze → ${planPath}`);
  for (const c of plan.cues) {
    console.log(`  ${c.id} ${c.start.toFixed(2)}–${c.end.toFixed(2)}  ${c.tokens.map((t, i) => `${i}:${t.text}`).join(" ")}`);
  }
}
```

- [ ] **Step 6: Plan für Video 01 erzeugen**

Run: `npx tsx scripts/craiss-caption-plan.ts erster-tag-v3`
Expected (Wortindizes vor dem Doppelpunkt):
```
erster-tag-v3: 6 Sätze → …/captions/erster-tag-v3.plan.json
  cc-01 4.08–5.66…  0:Arbeiten 1:Tablet, 2:wo 3:ist 4:Büro, 5:wo 6:ist 7:Werkstatt, 8:Autowäsche.
  cc-02 7.80–9.43  0:Das 1:ist 2:kinderleicht 3:gebaut.
  cc-03 9.48–11.73  0:Keiner 1:hat 2:Probleme, 3:egal 4:ob 5:jung 6:oder 7:alt.
  cc-04 11.78–12.80  0:Jeder 1:kommt 2:klar 3:damit.
  cc-05 12.80–16.47  0:Die 1:Fahrer 2:werden 3:ja 4:auch 5:von 6:uns 7:eingewiesen, 8:wie … 13:haben.
  cc-06 16.52–19.84  0:Und 1:bei 2:Fragen 3:können 4:sie 5:sich 6:immer 7:übers 8:Telefon 9:melden.
```
(`cc-01` endet bei 7,75 s.) Weichen Indizes ab, die Werte in Task 6 Step 1 entsprechend anpassen.

- [ ] **Step 7: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captionMix/buildPlan.ts src/clients/craiss/captionMix/buildPlan.test.ts scripts/craiss-caption-plan.ts src/clients/craiss/captions/erster-tag-v3.plan.json
git commit -m "feat(craiss): Untertitel-Mix — Plan-Erzeugung + Plan Video 01"
```

---

### Task 5: Renderer `CaptionMix.tsx`

**Files:**
- Create: `src/clients/craiss/captionMix/CaptionMix.tsx`

**Interfaces:**
- Consumes: `resolveBlock`, `type Align` (Task 1); `type CaptionPlan`, `type PlanCue`, `type PlanToken`, `type Zone` (Task 2); `cueWindow`, `revealProgress`, `activeTokenIndex`, `currentPageIndex`, `pageTokenRange`, `freeWindows`, `LEAD_SEC`, `type BlockedRange` (Task 3); `FONT_BLACK`, `FONT_BOLD`, `WHITE`, `RED`, `CRAISS_BLUE`, `SOFT` aus `../lib`.
- Produces: `CaptionMixTrack: React.FC<{ plan: CaptionPlan; blocked: BlockedRange[]; minGapSec?: number }>` — zeichnet auf einer 1080×1920-Bühne (Aufrufer skaliert).

- [ ] **Step 1: Implementierung**

```tsx
// src/clients/craiss/captionMix/CaptionMix.tsx
// ============================================================
// Craiss Untertitel-Mix — Renderer
// Grundzeile (Wort für Wort) · Hero-Wort weiß/rot/blau · Wort-Kasten ·
// Glas-Wort. Nur transform + opacity; Deckkraft linear, SOFT-Feder nur auf
// Transforms. Spec: docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md
// ============================================================
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CRAISS_BLUE, FONT_BLACK, FONT_BOLD, RED, SOFT, WHITE } from "../lib";
import { resolveBlock, type Align } from "./layout";
import type { CaptionPlan, PlanCue, PlanToken, Zone } from "./plan";
import {
  LEAD_SEC,
  activeTokenIndex,
  cueWindow,
  currentPageIndex,
  freeWindows,
  pageTokenRange,
  revealProgress,
  type BlockedRange,
} from "./timing";

const SHADOW = "0 3px 18px rgba(0,0,0,0.55)";
const CARD_SHADOW = "0 8px 28px rgba(0,0,0,0.35)";
const EXIT_FRAMES = 5;
const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const FLEX: Record<Align, "center" | "flex-start" | "flex-end"> = { center: "center", left: "flex-start", right: "flex-end" };

// Deckkraft auf glatte 1 schnappen (Flicker-Regel, siehe Subtitles.tsx)
const settle = (v: number) => (v > 0.999 ? 1 : v);
const display = (tokens: PlanToken[]) =>
  tokens.map((t) => t.text).join(" ").replace(/[.,!?;:]+$/, "").toUpperCase();
const appearFrame = (start: number, fps: number) => Math.round((start - LEAD_SEC) * fps);

// --- Grundzeile: jedes Wort erscheint an seinem Anfang (12 px Anstieg) ---
const RailWord: React.FC<{ token: PlanToken }> = ({ token }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = revealProgress(token.start, frame, fps);
  const rise = spring({ frame: frame - appearFrame(token.start, fps), fps, config: SOFT });
  // Unsichtbare Wörter behalten ihren Platz → Zeile springt nicht beim Aufbau
  return (
    <span style={{ display: "inline-block", opacity: settle(p), transform: `translateY(${(1 - rise) * 12}px)` }}>
      {token.text}
    </span>
  );
};

const RailLine: React.FC<{ tokens: PlanToken[]; align: Align }> = ({ tokens, align }) => (
  <div style={{ fontFamily: FONT_BOLD, fontSize: 52, lineHeight: 1.2, color: WHITE, textShadow: SHADOW, textAlign: align }}>
    {tokens.map((t, i) => (
      <React.Fragment key={i}>
        <RailWord token={t} />
        {i < tokens.length - 1 ? " " : null}
      </React.Fragment>
    ))}
  </div>
);

// --- Hero-Wort: landet ruhig am Wortanfang (Skalierung 0,94 → 1, 24 px) ---
const HERO_STYLE: Record<"hero-white" | "hero-red" | "hero-blue", React.CSSProperties> = {
  "hero-white": { fontFamily: FONT_BLACK, fontSize: 130, lineHeight: 1.02, color: WHITE, textShadow: SHADOW },
  "hero-red": {
    fontFamily: FONT_BLACK, fontSize: 96, lineHeight: 1.05, color: WHITE,
    backgroundColor: RED, padding: "10px 26px", borderRadius: 6, boxShadow: CARD_SHADOW,
  },
  "hero-blue": {
    fontFamily: FONT_BOLD, fontSize: 64, lineHeight: 1.1, letterSpacing: 2, color: WHITE,
    backgroundColor: CRAISS_BLUE, padding: "10px 24px", borderRadius: 6, boxShadow: CARD_SHADOW,
  },
};

const HeroWord: React.FC<{ tokens: PlanToken[]; variant: keyof typeof HERO_STYLE }> = ({ tokens, variant }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = appearFrame(tokens[0].start, fps);
  const op = interpolate(frame, [at, at + 5], [0, 1], CLAMP);
  const s = spring({ frame: frame - at, fps, config: SOFT });
  return (
    <div
      style={{
        display: "inline-block",
        opacity: settle(op),
        transform: `translateY(${(1 - s) * 24}px) scale(${0.94 + 0.06 * s})`,
        ...HERO_STYLE[variant],
      }}
    >
      {display(tokens)}
    </div>
  );
};

// --- Wort-Kasten ---
const BOX_WORD_STYLE: React.CSSProperties = { fontFamily: FONT_BLACK, fontSize: 110, lineHeight: 1.1, color: WHITE, textTransform: "uppercase" };

// Aufzählung: ausgewähltes Wort im roten Kasten, ersetzt das vorige
const BoxWord: React.FC<{ token: PlanToken }> = ({ token }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = appearFrame(token.start, fps);
  const op = interpolate(frame, [at, at + 5], [0, 1], CLAMP);
  const s = spring({ frame: frame - at, fps, config: SOFT });
  return (
    <div
      style={{
        display: "inline-block", opacity: settle(op), transform: `scale(${0.94 + 0.06 * s})`,
        backgroundColor: RED, padding: "6px 28px", borderRadius: 6, boxShadow: CARD_SHADOW, ...BOX_WORD_STYLE,
      }}
    >
      {display([token])}
    </div>
  );
};

// Hervorhebung: alle Wörter groß, Kasten blendet in 6 Frames zum gesprochenen Wort
const HighlightWord: React.FC<{ token: PlanToken; next?: PlanToken }> = ({ token, next }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const on = appearFrame(token.start, fps);
  const wordOp = interpolate(frame, [on, on + 5], [0, 1], CLAMP);
  const boxIn = interpolate(frame, [on, on + 6], [0, 1], CLAMP);
  const off = next ? appearFrame(next.start, fps) : null;
  const boxOut = off === null ? 0 : interpolate(frame, [off, off + 6], [0, 1], CLAMP);
  const boxOp = boxIn * (1 - boxOut);
  return (
    <span style={{ position: "relative", display: "inline-block", padding: "2px 16px", margin: "4px 0" }}>
      <span
        style={{
          position: "absolute", inset: 0, backgroundColor: RED, borderRadius: 6,
          opacity: settle(boxOp), transform: `scaleX(${0.92 + 0.08 * boxOp})`,
        }}
      />
      <span style={{ position: "relative", opacity: settle(wordOp), textShadow: boxOp > 0.5 ? "none" : SHADOW }}>
        {token.text.replace(/[.,!?;:]+$/, "")}
      </span>
    </span>
  );
};

const WordBoxContent: React.FC<{ cue: PlanCue; page: PlanToken[]; t: number; align: Align }> = ({ cue, page, t, align }) => {
  if (cue.boxIndices && cue.boxIndices.length > 0) {
    const active = [...cue.boxIndices].reverse().find((i) => t >= cue.tokens[i].start - LEAD_SEC);
    return (
      <>
        <RailLine tokens={page} align={align} />
        {active !== undefined ? <BoxWord key={active} token={cue.tokens[active]} /> : null}
      </>
    );
  }
  return (
    <div style={{ ...BOX_WORD_STYLE, textAlign: align }}>
      {page.map((tok, i) => (
        <React.Fragment key={i}>
          <HighlightWord token={tok} next={page[i + 1]} />
          {i < page.length - 1 ? " " : null}
        </React.Fragment>
      ))}
    </div>
  );
};

// --- Inhalt eines Satzes: aktuelle Seite je nach Treatment ---
const CueContent: React.FC<{ cue: PlanCue; t: number; align: Align }> = ({ cue, t, align }) => {
  const pageIdx = currentPageIndex(cue.pages, cue.tokens, t);
  const [a, b] = pageTokenRange(cue.pages, cue.tokens.length, pageIdx);
  const page = cue.tokens.slice(a, b);

  if (cue.treatment === "wordbox") return <WordBoxContent cue={cue} page={page} t={t} align={align} />;

  if (cue.treatment !== "rail" && cue.heroIndex !== undefined) {
    const h0 = cue.heroIndex;
    const h1 = h0 + (cue.heroCount ?? 1);
    if (h0 >= a && h1 <= b) {
      const before = cue.tokens.slice(a, h0);
      const after = cue.tokens.slice(h1, b);
      return (
        <>
          {before.length > 0 ? <RailLine tokens={before} align={align} /> : null}
          <HeroWord tokens={cue.tokens.slice(h0, h1)} variant={cue.treatment} />
          {after.length > 0 ? <RailLine tokens={after} align={align} /> : null}
        </>
      );
    }
  }
  return <RailLine tokens={page} align={align} />;
};

// --- Glas-Wort: groß, 40 % Weiß mit feinem Rand, in freier Fläche ---
const GlassWord: React.FC<{ text: string; startSec: number; zone: Zone; y?: number; exitOp: number }> = ({ text, startSec, zone, y, exitOp }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = Math.round(startSec * fps);
  const op = interpolate(frame, [at, at + 10], [0, 1], CLAMP);
  const scale = interpolate(frame, [at, at + 10], [1.02, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const box = resolveBlock(zone, y);
  return (
    <div style={{ position: "absolute", top: box.top, left: box.left, width: box.width, textAlign: box.align, opacity: settle(op * exitOp) }}>
      <span
        style={{
          display: "inline-block", fontFamily: FONT_BLACK, fontSize: 230, lineHeight: 1,
          color: "rgba(255,255,255,0.4)", WebkitTextStroke: "1.5px rgba(255,255,255,0.75)",
          textTransform: "uppercase", transform: `scale(${scale})`,
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const CaptionMixTrack: React.FC<{ plan: CaptionPlan; blocked: BlockedRange[]; minGapSec?: number }> = ({
  plan,
  blocked,
  minGapSec = 0.5,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const windows = freeWindows(blocked, fps, durationInFrames, Math.round(minGapSec * fps));
  const t = frame / fps;

  const cue = plan.cues.find((c) => t >= c.start && t < c.end);
  if (!cue) return null;
  const win = cueWindow(cue, windows, fps);
  if (!win || frame < win.from || frame >= win.to) return null;

  const exitOp = interpolate(frame, [win.to - EXIT_FRAMES, win.to], [1, 0], CLAMP);
  const box = resolveBlock(cue.zone, cue.y);

  return (
    <>
      {cue.glass && t >= cue.glass.startSec ? (
        <GlassWord text={cue.glass.text} startSec={cue.glass.startSec} zone={cue.glass.zone} y={cue.glass.y} exitOp={exitOp} />
      ) : null}
      <div
        style={{
          position: "absolute", top: box.top, left: box.left, width: box.width,
          display: "flex", flexDirection: "column", alignItems: FLEX[box.align], gap: 14,
          textAlign: box.align, opacity: settle(exitOp),
        }}
      >
        <CueContent cue={cue} t={t} align={box.align} />
      </div>
    </>
  );
};
```

- [ ] **Step 2: Typprüfung**

Run: `npx tsc --noEmit -p .`
Expected: keine Ausgabe, Exit 0

- [ ] **Step 3: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captionMix/CaptionMix.tsx
git commit -m "feat(craiss): Untertitel-Mix — Renderer"
```

---

### Task 6: Plan Video 01 setzen, Vorschau anbinden

**Files:**
- Modify: `src/clients/craiss/captions/erster-tag-v3.plan.json`
- Modify: `src/clients/craiss/projects/erster-tag/CompositionSubtitled.tsx` (neuer Export am Dateiende)
- Modify: `src/clients/craiss/projects/vorschau/Composition.tsx`

**Interfaces:**
- Consumes: `CaptionMixTrack` (Task 5), `captionPlanSchema` (Task 2), `HOOK_BLOCK`/`CTA_BLOCK`/`BASE_W`/`BASE_H` (bestehend in `erster-tag/CompositionSubtitled.tsx`).
- Produces: `CraissErsterTagMixLayer: React.FC`; Vorschau-Prop `subtitleStyle: "neu" | "alt"` (Standard `"neu"`); `VIDEOS[id].MixSubs?: React.FC`.

- [ ] **Step 1: Treatments und Positionen für 01 setzen**

Werte aus dem freigegebenen Beispiel; Kinnhöhen aus den Einzelbildern pro Shot (Fahrer-Nahaufnahme 8,6 s Kinn ≈ 720 px, Tomasz-Nahaufnahme 10,3–11,8 s ≈ 1000 px, Fahrer-Nahaufnahme 13,9–14,8 s ≈ 1000 px, Tomasz am Telefon 16,3–18,1 s ≈ 1100 px).

```bash
node -e '
const fs = require("fs");
const f = "src/clients/craiss/captions/erster-tag-v3.plan.json";
const p = JSON.parse(fs.readFileSync(f, "utf8"));
const set = (id, o) => Object.assign(p.cues.find((c) => c.id === id), o);
set("cc-01", { treatment: "wordbox", boxIndices: [4, 7, 8], zone: "chest", y: 1100 });
set("cc-02", { treatment: "hero-white", heroIndex: 2, heroCount: 1, zone: "chest", y: 900, chinY: 720 });
set("cc-03", { treatment: "hero-red", heroIndex: 5, heroCount: 3, zone: "chest", y: 1180, chinY: 1000 });
set("cc-04", { treatment: "rail", zone: "chest", y: 1050, chinY: 700 });
set("cc-05", { treatment: "hero-blue", heroIndex: 7, heroCount: 1, zone: "chest", y: 1230, chinY: 1000 });
set("cc-06", { treatment: "rail", zone: "chest", y: 1250, chinY: 1100, glass: { text: "IMMER", startSec: 18.12, zone: "top", y: 120 } });
fs.writeFileSync(f, JSON.stringify(p, null, 1) + "\n");
'
npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --check
```
Expected:
```
erster-tag-v3: 6 Sätze — wordbox 1, hero-white 1, hero-red 1, rail 2, hero-blue 1, Glas 1
  ✓ keine Fehler
```

- [ ] **Step 2: Mix-Layer für 01 exportieren** — am Ende von `src/clients/craiss/projects/erster-tag/CompositionSubtitled.tsx` anhängen, Importe oben ergänzen:

```tsx
// Importe oben ergänzen:
import planJson from "../../captions/erster-tag-v3.plan.json";
import { CaptionMixTrack } from "../../captionMix/CaptionMix";
import { captionPlanSchema } from "../../captionMix/plan";
```

```tsx
// Am Dateiende:
// Neuer Untertitel-Look „Mix" (Spec 2026-09-11) — nur Spur, ohne Footage
const mixPlan = captionPlanSchema.parse(planJson);

export const CraissErsterTagMixLayer: React.FC = () => {
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: BASE_W, height: BASE_H, transform: `scale(${width / BASE_W})`, transformOrigin: "top left" }}>
      <CaptionMixTrack plan={mixPlan} blocked={[HOOK_BLOCK, CTA_BLOCK]} />
    </div>
  );
};
```

- [ ] **Step 3: Vorschau um Umschalter erweitern** — in `src/clients/craiss/projects/vorschau/Composition.tsx`:

Import ergänzen:
```tsx
import { CraissErsterTagMixLayer, CraissErsterTagSubtitleLayer } from "../erster-tag/CompositionSubtitled";
```
(ersetzt die bisherige Importzeile für `CraissErsterTagSubtitleLayer`)

Schema ergänzen:
```tsx
export const craissVorschauSchema = projectPropsSchema.extend({
  video: z.enum(VIDEO_IDS).describe("Video"),
  showAnimation: z.boolean().describe("Animationen zeigen"),
  showSubtitles: z.boolean().describe("Untertitel zeigen"),
  subtitleStyle: z.enum(["neu", "alt"]).describe("Untertitel-Look (neu = Mix, alt = Leiste 07.09.)"),
});
```

Typ von `VIDEOS` erweitern und Eintrag 01 ergänzen:
```tsx
const VIDEOS: Record<
  VideoId,
  { src: string; seconds: number; Overlay: React.FC; Subs: React.FC; MixSubs?: React.FC }
> = {
  "01": {
    src: "projects/craiss-erster-tag/ohne-Animation/proxy/01_Dein_erster_Tag_bei_uns_V3_ohneAnim_proxy.mp4",
    seconds: 30.04,
    Overlay: () => <CraissErsterTag {...craissErsterTagDefaults} footage={NO_FOOTAGE} />,
    Subs: () => <CraissErsterTagSubtitleLayer subtitles={SUBTITLE_DEFAULTS} />,
    MixSubs: CraissErsterTagMixLayer,
  },
```

Defaults ergänzen (in `craissVorschauDefaults` nach `showSubtitles: true,`):
```tsx
  subtitleStyle: "neu" as const,
```

Komponente: Props um `subtitleStyle` erweitern und die Untertitel-Zeile ersetzen:
```tsx
export const CraissVorschau: React.FC<CraissVorschauProps> = ({
  video,
  showAnimation,
  showSubtitles,
  subtitleStyle,
  review,
}) => {
```
```tsx
      {showSubtitles && (subtitleStyle === "neu" && v.MixSubs ? <v.MixSubs /> : <v.Subs />)}
```

- [ ] **Step 4: Typprüfung und alle Tests**

Run: `npx tsc --noEmit -p . && npx tsx --test src/clients/craiss/captionMix/*.test.ts`
Expected: tsc ohne Ausgabe; `ℹ pass 16`, `ℹ fail 0`

- [ ] **Step 5: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captions/erster-tag-v3.plan.json src/clients/craiss/projects/erster-tag/CompositionSubtitled.tsx src/clients/craiss/projects/vorschau/Composition.tsx
git commit -m "feat(craiss): Untertitel-Mix für Video 01 in Vorschau-Neu"
```

---

### Task 7: Sichtprüfung Video 01 und Übergabe

**Files:**
- Modify (nur bei Befund): `src/clients/craiss/captions/erster-tag-v3.plan.json` (`y`, `zone`, `glass`)
- Modify: `projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/Protokoll.md`

**Interfaces:**
- Consumes: Komposition `Craiss-Vorschau-01-ErsterTag` (Studio läuft auf Port 3000; Renders mit `--public-dir=public-craiss`).

- [ ] **Step 1: Kontrollvideo mit Guides rendern**

```bash
K=/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/3cc23e1a-54a1-4e83-bc8c-34a1d4b1994e/scratchpad/mix01
mkdir -p "$K"
rsync -a --exclude='*.mov' --exclude='*.mp4' --exclude='*.wav' public/ public-craiss/
npx remotion render src/index.ts Craiss-Vorschau-01-ErsterTag "$K/mix01.mp4" --scale=0.5 --codec=h264 --crf=20 --public-dir=public-craiss --port=3222 --props='{"review":{"showGuides":true,"showSafeZone":true,"showFaceZone":true,"showGrid":false,"guideOpacity":0.35}}'
```
Expected: `mix01.mp4`, 540×960, 751 Frames. Bei „Visited …/index.html but got no response" denselben Befehl erneut starten.

- [ ] **Step 2: Kontaktbogen je Satz (Anfang + 8 Frames, Mitte, Ende − 6 Frames)**

```bash
K=/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/3cc23e1a-54a1-4e83-bc8c-34a1d4b1994e/scratchpad/mix01
node -e '
const p = require("./src/clients/craiss/captions/erster-tag-v3.plan.json");
for (const c of p.cues) {
  const a = Math.round(c.start * 25) + 8, b = Math.round(c.end * 25) - 6, m = Math.round((a + b) / 2);
  console.log(`${c.id} ${a} ${m} ${b}`);
}' | while read id a m b; do
  for f in $a $m $b; do ffmpeg -v error -y -ss $(echo "$f/25" | bc -l | sed 's/^\./0./') -i "$K/mix01.mp4" -frames:v 1 "$K/${id}_$(printf %04d $f).png"; done
done
montage -font /System/Library/Fonts/Supplemental/Arial.ttf -label '%t' -pointsize 12 "$K"/cc-*.png -tile 6x -geometry 270x480+3+3 -background '#222' -fill white "$K/kontaktbogen.jpg"
```
Expected: `kontaktbogen.jpg` mit 18 Bildern.

- [ ] **Step 3: Kontaktbogen ansehen und gegen die Checkliste prüfen**

Pro Bild:
- Kein Text in der roten Gesichtszone, Hals frei (Oberkante sichtbar unter dem Kinn).
- Alles innerhalb der grünen Safe-Zone-Seiten, Unterkante über der unteren UI-Zone.
- Hero/Kasten-Wörter vollständig lesbar, keine Überlappung mit Tablet-/Handy-Displays, die gerade Inhalt zeigen.
- Glas „IMMER" (cc-06 Ende) überlagert nicht den Kopf des telefonierenden Fahrers.
- Kein Wort vor dem Sprechen sichtbar (Anfangsbild zeigt nur die ersten Wörter).

Befund → `y`/`zone` im Plan ändern (bei Glas-Kollision `y` verkleinern oder `glass` auf `null` setzen), dann `npx tsx scripts/craiss-caption-plan.ts erster-tag-v3 --check` und Step 1–3 wiederholen.

- [ ] **Step 4: Studio öffnen**

Browser-Pane: `http://localhost:3000/Craiss-Vorschau-01-ErsterTag`; im Props-Panel `subtitleStyle` zwischen `neu` und `alt` umschalten und bei 8,5 s (Hero), 10,8 s (roter Kasten), 18,5 s (Glas) prüfen, dass beide Looks erscheinen.

- [ ] **Step 5: Protokoll fortschreiben** — an `projects/Craiss Logistik/4 Ads/2026-08 Dein erster Tag/Protokoll.md` anhängen:

```markdown
## 2026-09-11 — Untertitel-Look „Mix" (Video 01, Vorschau)

- Spec `tools/motion/docs/superpowers/specs/2026-09-11-craiss-untertitel-mix-design.md`,
  Plan `tools/motion/docs/superpowers/plans/2026-09-11-craiss-untertitel-mix.md`.
- Neu: `src/clients/craiss/captionMix/` (Schema/Prüfregeln, Layout, Timing,
  Plan-Erzeugung, Renderer) + `scripts/craiss-caption-plan.ts`.
- Plan `captions/erster-tag-v3.plan.json`: Aufzählung BÜRO/WERKSTATT/AUTOWÄSCHE
  (Wort-Kasten), KINDERLEICHT (weiß), JUNG ODER ALT (rot), EINGEWIESEN (blau),
  Glas IMMER im Himmel; Positionen je Satz gegen Kontaktbogen geprüft.
- Vorschau `Craiss-Vorschau-01-ErsterTag`: Prop `subtitleStyle` neu/alt.

**Offen:** Abnahme 01 → Videos 02–05 nach demselben System → Alpha-Renders.
```

- [ ] **Step 6: Commit (nur nach Freigabe)**

```bash
git add src/clients/craiss/captions/erster-tag-v3.plan.json
git commit -m "fix(craiss): Untertitel-Mix 01 — Positionen nach Sichtprüfung"
```

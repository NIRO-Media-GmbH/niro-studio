// ============================================================
// Craiss Generation Logistik — Untertitel-Seiten aus Wort-Timings
// Videos 01-05 der "4 Ads"-Serie (jeweils V3/V4-Schnitt, der bereits
// Hook/CTA/Grafiken eingebrannt hat).
//
// Quelle: Scribe-JSON aus _intern/cache (Wort-Timings, nie geschaetzt —
// docs/cinematic-captions.md Abschnitt 1). Gleiche Gruppierungs-Logik wie
// scripts/sw-captions.ts (2-5 Woerter/Seite, Bruch an Pause/Satzende/
// Komma+Pause, Einzelwoerter werden angehaengt).
//
// Sperrzeiten (BLOCKED) sind KEINE Root.tsx-Defaults — die V3/V4-Schnitte
// sind neuer als die dortigen defaultProps und weichen in Dauer/Timing
// spuerbar ab (z. B. Video 02: -9,5s, Video 03: +5,7s). Alle Zeiten unten
// sind per Kontaktbogen (Frame-Sampling alle 2s + Nachschaerfen an Schnitten)
// gegen den tatsaechlichen Proxy verifiziert (2026-09-07).
//
// Aufruf: npx tsx scripts/craiss-captions.ts [id ...]   (ohne Argument: alle)
// ============================================================

import fs from "node:fs";
import path from "node:path";

type Word = { text: string; start: number; end: number };
type Page = { start: number; end: number; tokens: Word[] };

const ROOT = path.resolve(__dirname, "..");
const PROJECTS = path.resolve(ROOT, "../../projects/Craiss Logistik/4 Ads");
const OUT_SRC = path.join(ROOT, "src/clients/craiss/captions");

const FPS = 25;
const MAX_WORDS = 5;
const MAX_CHARS = 30;
const PAUSE_BREAK = 0.45;
const COMMA_PAUSE = 0.2;
const LEAD_IN = 0.08;
const TAIL = 0.6;
const GAP_TO_NEXT = 0.05;
const MIN_GAP_FRAMES = 15;
const MIN_VISIBLE_FRAMES = 10;

const FILLERS = new Set(["äh", "ähm", "ehm", "hm", "mh", "eh", "ah"]);

const DANGLING = new Set([
  "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer",
  "und", "oder", "aber", "wie", "als", "dass", "weil", "wenn", "ob",
  "bei", "von", "vom", "mit", "auf", "in", "im", "an", "am", "zu", "zum", "zur", "für", "nach", "vor", "aus",
  "nur", "auch", "noch", "dann", "so", "es", "ich", "wir", "du", "ihr", "man", "sich", "mir", "dir", "uns",
]);

type VideoConfig = {
  id: string;
  charge: string; // Ordnername unter PROJECTS
  scribeFile: string; // Datei in <charge>/_intern/cache/
  durationSec: number; // aus Proxy-Framezahl / FPS, minus Sicherheitsmarge
  blocked: [number, number][]; // [startSec, durationSec] — Hook/Chips/Flaggen/CTA
  fixes: Array<[string, string]>; // ASR-Korrekturen, wie sw-captions.ts
  drop: string[]; // Phrasen, die dopplen (David-Regel) und rausfliegen
};

const VIDEOS: VideoConfig[] = [
  {
    id: "erster-tag-v3",
    charge: "2026-08 Dein erster Tag",
    scribeFile: "01_Dein_erster_Tag_bei_uns_V3.scribe.json",
    durationSec: 29.6,
    blocked: [
      [0.24, 3.6 - 0.24], // Hook
      [24.32, 29.6 - 24.32], // CTA
    ],
    // UT-Korrektur 2026-09-11 (Abnahme): „Arbeit am Tablet"
    fixes: [["Arbeiten Tablet,", "Arbeit am Tablet,"]],
    // dopplt Hook „DEIN ERSTER TAG / BEI UNS"; liegt ohnehin fast komplett
    // unter dem Hook-Fenster.
    drop: ["Erster Tag, lerne alles."],
  },
  {
    id: "arbeitsalltag-v3",
    charge: "2026-08 Einblick Arbeitsalltag",
    scribeFile: "02_Einblick_in_meinen_Arbeitsalltag_V3.scribe.json",
    durationSec: 73.08,
    blocked: [
      [0, 3.0], // Hook „MEIN ARBEITSALLTAG / BEI CRAISS"
      [61.6, 73.08 - 61.6], // CTA (Schnitt auf Drohnen-Endshot ~61,65s)
    ],
    fixes: [
      ["Firma Kreis,", "Firma Craiss,"],
      ["bei Kreis.", "bei Craiss."],
      ["meine Family.", "meine Familie."],
    ],
    // Kundenfeedback: Fokus „kein Stress" deutlich reduzieren (2026-09-11)
    drop: ["Kein Stress."],
  },
  {
    id: "viele-jahre-v3",
    charge: "2026-08 Viele Jahre Viele Geschichten",
    scribeFile: "03_Viele_Jahre_Viele_Geschichten_V3.scribe.json",
    durationSec: 51.6,
    blocked: [
      [0, 3.0], // Hook „VIELE JAHRE / VIELE GESCHICHTEN"
      [7.6, 11.8 - 7.6], // Laender-Flaggen (HU/CZ/RO/LT)
      [46.6, 51.6 - 46.6], // CTA (Schnitt ~46,65s)
    ],
    fixes: [
      ["Kreis ist gute", "Craiss ist gute"],
      ["bei Kreis, was optimal", "bei Craiss, was optimal"],
    ],
    drop: [],
  },
  {
    id: "funnel-v4",
    charge: "2026-08 Funnel Video",
    scribeFile: "04_Funnel_Video_V4.scribe.json",
    durationSec: 59.08,
    blocked: [
      [0, 4.68], // Chef-Namenskarte „MICHAEL CRAISS"
      [6.4, 8.2 - 6.4], // Standort-Chip „MÜHLACKER"
      [22.16, 24.24 - 22.16], // Swipe-Transition
      [24.64, 28.6 - 24.64], // Namenskarte „EVA"
      [33.36, 36.8 - 33.36], // „KEIN LEBENSLAUF / KEIN ANSCHREIBEN"
      [36.6, 40.8 - 36.6], // Schritte 1+2 („TRAG DICH EIN" / „TELEFONAT")
      [40.44, 44.8 - 40.44], // Phone-Chip „SEI ERREICHBAR" (ueberlappt Schritt 2)
      [47.76, 50.6 - 47.76], // Schritt 3 „PERSÖNLICHES KENNENLERNEN"
      [51.2, 54.2 - 51.2], // Outro „WORAUF WARTEST DU?"
      [54.6, 59.08 - 54.6], // End-Logo (kein separates CTA-Overlay im Video)
    ],
    fixes: [
      ["Michael Kreis.", "Michael Craiss."],
      ["Logistikunternehmens Kreis", "Logistikunternehmens Craiss"],
      ["Hauptansprechpartnerinnen bei Kreis,", "Hauptansprechpartnerinnen bei Craiss,"],
    ],
    // dopplt die Outro-Grafik „WORAUF WARTEST DU?" (51,2–54,2s), die direkt
    // im Anschluss steht.
    drop: ["Also, worauf wartest du?"],
  },
  {
    id: "testimonial-v2",
    charge: "2026-08 Testimonial Video",
    scribeFile: "05_Testimonial_Video_V2.scribe.json",
    durationSec: 52.92,
    blocked: [
      // = BLOCKED in projects/testimonial/CompositionSubtitled.tsx (Overlay v3)
      [0, 2.48], // Hook „ICH MAG MEINE ARBEIT / LKW-FAHRER BEI CRAISS"
      [3.5, 5.7 - 3.5], // Zitat-Chip „JEDER TAG IST EIN GUTER TAG."
      [6.86, 8.8 - 6.86], // Zitat-Chip „DIE FREIHEIT. DIE RUHE."
      [28.2, 31.7 - 28.2], // Zitat-Chip „JEDEN TAG ZU HAUSE." (+ doppelnder Satz)
      [35.3, 37.3 - 35.3], // Zitat-Chip „BEI CRAISS PASST'S."
      [39.3, 46.0 - 39.3], // Laender-Flaggen (HU/CZ/RO/LT)
      [46.0, 52.92 - 46.0], // CTA (Drohnen-Endshot ab 46,52s)
    ],
    fixes: [
      ["Firma Kreis arbeite", "Firma Craiss arbeite"],
      ["Bei Kreis passt optimal", "Bei Craiss passt optimal"],
    ],
    // Kundenfeedback: „Kein Stress" muss nicht zusaetzlich eingeblendet
    // werden — weder als Chip noch als Untertitel (2026-09-11)
    drop: ["Kein Stress."],
  },
];

const norm = (s: string) => s.toLowerCase().replace(/[.,!?;:"„“”‚‘’()]/g, "").trim();
const isSentenceEnd = (t: string) => /[.!?]$/.test(t);
const hasComma = (t: string) => /[,;:]$/.test(t);
const charCount = (ws: Word[]) => ws.reduce((n, w) => n + w.text.length, 0) + Math.max(0, ws.length - 1);
const trailingPunct = (s: string) => {
  const m = s.match(/[.,!?;:]+$/);
  return m ? m[0] : "";
};

const parseScribe = (file: string): Word[] => {
  const json = JSON.parse(fs.readFileSync(file, "utf8")) as {
    words: Array<{ text: string; start: number; end: number }>;
  };
  return json.words
    .map((w) => ({ text: w.text.trim(), start: w.start, end: w.end }))
    .filter((w) => w.text !== "");
};

const applyPhrase = (words: Word[], from: string, to: string | null): Word[] => {
  const pat = from.split(/\s+/).map(norm);
  const out: Word[] = [];
  let i = 0;
  let hits = 0;
  while (i < words.length) {
    let match = true;
    for (let k = 0; k < pat.length; k++) {
      if (!words[i + k] || norm(words[i + k].text) !== pat[k]) {
        match = false;
        break;
      }
    }
    if (!match) {
      out.push(words[i]);
      i++;
      continue;
    }
    hits++;
    const span = words.slice(i, i + pat.length);
    const punct = trailingPunct(span[span.length - 1].text);
    if (to !== null) {
      const reps = to.split(/\s+/);
      const s0 = span[0].start;
      const s1 = span[span.length - 1].end;
      if (reps.length === span.length) {
        reps.forEach((r, k) => out.push({ text: r, start: span[k].start, end: span[k].end }));
      } else {
        const step = (s1 - s0) / reps.length;
        reps.forEach((r, k) => out.push({ text: r, start: s0 + step * k, end: s0 + step * (k + 1) }));
      }
    } else if (punct && out.length > 0) {
      const prev = out[out.length - 1];
      if (!trailingPunct(prev.text)) prev.text += punct;
    }
    i += pat.length;
  }
  if (hits === 0) console.warn(`  ! Korrektur ohne Treffer: "${from}"`);
  return out;
};

const clean = (words: Word[], cfg: VideoConfig): Word[] => {
  let w = words.filter((x) => !FILLERS.has(norm(x.text)));
  for (const d of cfg.drop) w = applyPhrase(w, d, null);
  for (const [from, to] of cfg.fixes) w = applyPhrase(w, from, to);
  return w;
};

const group = (words: Word[]): Page[] => {
  const groups: Word[][] = [];
  let cur: Word[] = [];
  for (const w of words) {
    if (cur.length > 0) {
      const prev = cur[cur.length - 1];
      const gap = w.start - prev.end;
      const brk =
        cur.length >= MAX_WORDS ||
        charCount([...cur, w]) > MAX_CHARS ||
        gap >= PAUSE_BREAK ||
        isSentenceEnd(prev.text) ||
        (hasComma(prev.text) && gap >= COMMA_PAUSE);
      if (brk) {
        groups.push(cur);
        cur = [];
      }
    }
    cur.push(w);
  }
  if (cur.length) groups.push(cur);

  for (let i = 0; i < groups.length; i++) {
    if (groups[i].length !== 1) continue;
    const w = groups[i][0];
    const prev = groups[i - 1];
    const next = groups[i + 1];
    const fitsPrev =
      prev &&
      !isSentenceEnd(prev[prev.length - 1].text) &&
      w.start - prev[prev.length - 1].end < PAUSE_BREAK &&
      charCount([...prev, w]) <= MAX_CHARS + 6 &&
      prev.length < MAX_WORDS + 1;
    const fitsNext =
      next &&
      !isSentenceEnd(w.text) &&
      next[0].start - w.end < PAUSE_BREAK &&
      charCount([w, ...next]) <= MAX_CHARS + 6 &&
      next.length < MAX_WORDS + 1;
    if (fitsPrev) {
      prev.push(w);
      groups.splice(i, 1);
      i--;
    } else if (fitsNext) {
      next.unshift(w);
      groups.splice(i, 1);
      i--;
    }
  }

  for (let i = 0; i < groups.length - 1; i++) {
    const cur = groups[i];
    const next = groups[i + 1];
    for (let guard = 0; guard < 2; guard++) {
      const last = cur[cur.length - 1];
      if (cur.length < 3) break;
      if (!DANGLING.has(norm(last.text)) || trailingPunct(last.text)) break;
      if (next[0].start - last.end >= PAUSE_BREAK) break;
      if (next.length >= MAX_WORDS + 1 || charCount([last, ...next]) > MAX_CHARS + 6) break;
      next.unshift(cur.pop()!);
    }
  }

  const all = groups.flat();
  all.forEach((w, i) => {
    const prev = all[i - 1];
    if (i === 0 || (prev && isSentenceEnd(prev.text))) {
      w.text = w.text.charAt(0).toUpperCase() + w.text.slice(1);
    }
  });

  const pages: Page[] = groups.map((g) => ({
    start: Math.max(0, g[0].start - LEAD_IN),
    end: g[g.length - 1].end + TAIL,
    tokens: g,
  }));
  for (let i = 0; i < pages.length - 1; i++) {
    pages[i].end = Math.min(pages[i].end, pages[i + 1].start - GAP_TO_NEXT);
    if (pages[i].end < pages[i].tokens[pages[i].tokens.length - 1].end) {
      pages[i].end = pages[i].tokens[pages[i].tokens.length - 1].end;
    }
  }
  return pages;
};

const freeWindows = (blocked: [number, number][], durationSec: number) => {
  const ranges = blocked
    .map(([st, du]) => {
      const from = Math.floor(st * FPS);
      return { from, to: from + Math.floor(du * FPS) };
    })
    .sort((a, b) => a.from - b.from);
  const merged: { from: number; to: number }[] = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r.from <= last.to) last.to = Math.max(last.to, r.to);
    else merged.push({ ...r });
  }
  const total = Math.floor(durationSec * FPS);
  const free: { from: number; to: number }[] = [];
  let cursor = 0;
  for (const r of merged) {
    if (r.from > cursor) free.push({ from: cursor, to: r.from });
    cursor = Math.max(cursor, r.to);
  }
  if (cursor < total) free.push({ from: cursor, to: total });
  return free.filter((w) => w.to - w.from >= MIN_GAP_FRAMES);
};

const visibility = (p: Page, windows: { from: number; to: number }[]) => {
  const a = Math.round(p.start * FPS);
  const b = Math.round(p.end * FPS);
  let vis = 0;
  for (const w of windows) {
    const lo = Math.max(a, w.from);
    const hi = Math.min(b, w.to);
    if (hi - lo >= MIN_VISIBLE_FRAMES) vis += hi - lo;
  }
  if (vis === 0) return "  ·  ";
  if (vis >= b - a - 1) return "SICHT";
  return `${String(Math.round((100 * vis) / (b - a))).padStart(3)}% `;
};

const fmt = (t: number) => t.toFixed(2).padStart(6);

const run = (cfg: VideoConfig) => {
  const cache = path.join(PROJECTS, cfg.charge, "_intern/cache");
  const outIntern = path.join(PROJECTS, cfg.charge, "_intern/captions");
  const raw = parseScribe(path.join(cache, cfg.scribeFile));
  console.log(`\n== ${cfg.id}  (scribe: ${cfg.scribeFile}, ${raw.length} Woerter)`);
  const words = clean(raw, cfg);
  const pages = group(words);

  const r3 = (n: number) => Math.round(n * 1000) / 1000;
  const json = {
    video: cfg.id,
    source: cfg.scribeFile,
    generated: new Date().toISOString().slice(0, 10),
    pages: pages.map((p) => ({
      start: r3(p.start),
      end: r3(p.end),
      tokens: p.tokens.map((t) => ({ text: t.text, start: r3(t.start), end: r3(t.end) })),
    })),
  };
  fs.mkdirSync(OUT_SRC, { recursive: true });
  fs.mkdirSync(outIntern, { recursive: true });
  fs.writeFileSync(path.join(OUT_SRC, `${cfg.id}.json`), JSON.stringify(json, null, 1) + "\n");
  fs.writeFileSync(path.join(outIntern, `${cfg.id}.json`), JSON.stringify(json, null, 1) + "\n");

  const windows = freeWindows(cfg.blocked, cfg.durationSec);
  const lines = pages.map(
    (p, i) =>
      `${String(i + 1).padStart(3)}  ${fmt(p.start)} – ${fmt(p.end)}  ${visibility(p, windows)} ${p.tokens.map((t) => t.text).join(" ")}`,
  );
  const visibleCount = pages.filter((p) => visibility(p, windows).trim() !== "·").length;
  const winTxt = windows.map((w) => `${(w.from / FPS).toFixed(2)}–${(w.to / FPS).toFixed(2)}`).join(", ");
  const head =
    `# ${cfg.id} — ${cfg.scribeFile}\n# ${pages.length} Seiten, ${words.length} Woerter; ` +
    `${visibleCount} Seiten (ganz oder teils) sichtbar\n# freie Fenster (s): ${winTxt || "keine"}\n` +
    `# Spalte: SICHT = ganz sichtbar, nn% = teilweise, · = liegt komplett unter Grafik\n`;
  const txt = `${head}\n${lines.join("\n")}\n`;
  console.log(head);
  console.log(lines.join("\n"));
  fs.writeFileSync(path.join(outIntern, `${cfg.id}.txt`), txt);
};

const wanted = process.argv.slice(2);
for (const cfg of VIDEOS) {
  if (wanted.length && !wanted.includes(cfg.id)) continue;
  run(cfg);
}

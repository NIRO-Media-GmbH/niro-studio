// ============================================================
// SW Projektentwicklung / Solar-Wissen — Untertitel-Seiten aus Wort-Timings
//
// Quelle pro Video: Kunden-SRT auf Wortebene (02/03/04/07) oder Scribe-JSON
// aus _intern/cache (01/05 — dort fehlten Wortzeiten im gelieferten Material).
// Ausgabe: src/clients/sw-projektentwicklung/captions/<id>.json (wird von den
// Kompositionen importiert) + lesbare Kontrollfassung in _intern/captions/.
//
// Aufruf: npx tsx scripts/sw-captions.ts [id ...]   (ohne Argument: alle)
// ============================================================

import fs from "node:fs";
import path from "node:path";

type Word = { text: string; start: number; end: number };
type Page = { start: number; end: number; tokens: Word[] };

const ROOT = path.resolve(__dirname, "..");
const CHARGE = path.resolve(
  ROOT,
  "../../projects/SW-Projektentwicklung/Solar-Wissen/2026-08 Reels",
);
const TRANSKRIPT = path.join(CHARGE, "Material/Transkript");
const CACHE = path.join(CHARGE, "_intern/cache");
const OUT_SRC = path.join(ROOT, "src/clients/sw-projektentwicklung/captions");
const OUT_INTERN = path.join(CHARGE, "_intern/captions");

// Gruppierungs-Regeln (docs/cinematic-captions.md, Abschnitt 1):
// 2–5 Woerter pro Seite, Bruch an Pause / Satzende / Komma+Pause.
const MAX_WORDS = 5;
const MAX_CHARS = 30;
const PAUSE_BREAK = 0.45; // s Stille => neue Seite
const COMMA_PAUSE = 0.2; // Komma + so viel Pause => neue Seite
const LEAD_IN = 0.08; // Seite oeffnet vor dem ersten Wort
const TAIL = 0.6; // Seite steht nach dem letzten Wort nach
const GAP_TO_NEXT = 0.05;

const FILLERS = new Set(["äh", "ähm", "ehm", "hm", "mh", "eh", "ah"]);

type VideoConfig = {
  id: string;
  source: { kind: "srt"; file: string } | { kind: "scribe"; file: string };
  // Phrasen-Korrekturen der Spracherkennung: [gehoert, gemeint]. Der Abgleich
  // ignoriert Gross/Kleinschreibung und Satzzeichen, das Satzzeichen des
  // letzten Wortes bleibt erhalten. Unterschiedliche Wortzahl ist erlaubt —
  // die Zeiten werden dann gleichmaessig ueber die Spanne verteilt.
  fixes: Array<[string, string]>;
  // Woerter, die komplett entfallen (Versprecher, Abbrueche) — als Phrase.
  drop?: string[];
};

// Szenen-Sperrzeiten (Start, Dauer in s) — identisch mit den defaultProps in
// Root.tsx. Dienen hier NUR der Sichtbarkeits-Auswertung in der Kontrollfassung;
// die Komposition selbst rechnet mit ihren echten Props.
type Scene = [number, number];

const VIDEOS: (VideoConfig & { durationSec: number; scenes: Scene[] })[] = [
  {
    id: "gottwollshausen",
    source: { kind: "scribe", file: "01_Projekt-Gottwolfshausen_V1.scribe.json" },
    durationSec: 53.53,
    scenes: [[1.3, 4.0], [6.2, 4.0], [10.9, 2.9], [14.2, 2.8], [18.9, 3.3], [22.2, 2.0], [25.6, 15.9], [41.8, 4.4], [46.8, 6.7]],
    fixes: [
      ["vierundfünfzig", "54"],
      ["installiere", "installieren"],
      ["Bau-Solarmodule", "Bauer-Solarmodule"],
      ["vierhundertsechzig Watt", "460 Watt"],
      ["achtzehn Kilowattstunde", "18 Kilowattstunden"],
      ["vierundzwanzigtausend Kilowattstunde", "24.000 Kilowattstunden"],
      ["was wir hier produziert", "was wir hier produzieren"],
      ["fünfundzwanzig Kilowattpeak", "25 Kilowatt-Peak"],
      ["sechshundert Euro", "600 Euro"],
      ["siebzig Prozent", "70 Prozent"],
    ],
    drop: [],
  },
  {
    id: "bifaziale-module",
    source: { kind: "srt", file: "02_Bifaziale_Solarmodule_V1.srt" },
    durationSec: 35.967,
    scenes: [[0, 2.4], [3.4, 3.2], [8.0, 5.0], [14.0, 2.4], [18.6, 5.4], [25.0, 6.3], [32.8, 3.2]],
    fixes: [
      ["Gebüte", "Gemüter"],
      ["vor Solarmodule", "vor Solarmodulen"],
      ["das Modulo", "das Modul"],
      ["mitten in Garten", "mitten in den Garten"],
      ["Mit denen Module", "Mit diesen Modulen"],
      ["mit Standardmodule", "mit Standardmodulen"],
    ],
    drop: [],
  },
  {
    id: "bauer-solar",
    source: { kind: "srt", file: "03_BauerSolar-Modul_V1.srt" },
    durationSec: 56.0,
    scenes: [[3.1, 3.3], [7.4, 3.0], [10.9, 3.6], [15.2, 2.9], [18.6, 5.8], [25.1, 4.6], [29.7, 5.4], [36.3, 3.4], [40.0, 3.6], [43.8, 5.9], [49.9, 4.1], [54.0, 2.0]],
    fixes: [
      ["460 Watt Solarmodul", "460-Watt-Solarmodul"],
      ["Solar-Zaun-Verwender", "Solar-Zaun verwenden"],
      ["Zusätzlich wir hier", "Zusätzlich haben wir hier"],
      ["Also das sind die extrem robust", "Also die sind extrem robust"],
      ["vorherrige", "vorherige"],
    ],
    drop: [],
  },
  {
    id: "flachdach",
    source: { kind: "srt", file: "04_Flachdach-Erklaerung_V1.srt" },
    durationSec: 79.47,
    scenes: [[0.9, 6.2], [10.9, 5.6], [18.8, 3.6], [25.6, 3.6], [29.2, 2.4], [32.4, 5.0], [39.3, 6.4], [46.9, 4.6], [53.6, 5.6], [60.9, 4.4], [67.6, 4.2], [76.3, 3.2]],
    fixes: [
      ["Also mir hat nachher", "Also man hat nachher"],
      ["man legt das Flachdach", "man belegt das Flachdach"],
      ["Ost-West-Pfauenlage", "Ost-West-PV-Anlage"],
      ["wir legt es", "wir legen es"],
      ["aufgewinkelt werden durchdringt beim Dach", "aufgewinkelt. Nichts durchdringt das Dach"],
      ["reingeklegt", "reingelegt"],
      ["oder ähnliches", "oder Ähnliches"],
      ["ist quasi denn hier hinten", "Es ist quasi dann hier hinten"],
      ["Wind net hinten", "Wind nicht hinten"],
      ["Beispiel net", "Beispiel nicht"],
      ["Angrifffläche", "Angriffsfläche"],
    ],
    // Stelle 60,6–64,8 s ist von der Spracherkennung nicht sinnvoll zu lesen
    // („dass die Net komplett wegwählen, weil habe ich …") und liegt komplett
    // unter der Unterschied-Szene (60,9–65,3 s) — entfaellt statt zu raten.
    drop: ["dass die Net komplett wegwählen, weil habe ich natürlich eine Angrifffläche"],
  },
  {
    id: "smartino",
    source: { kind: "scribe", file: "05_Hotel-Smartino_V1.scribe.json" },
    durationSec: 49.25,
    scenes: [[2.3, 2.9], [6.3, 3.0], [10.5, 5.4], [16.15, 3.7], [21.4, 3.4], [27.2, 4.3], [35.3, 3.1], [39.4, 6.5], [46.0, 3.25]],
    fixes: [
      ["sechzig Prozent", "60 Prozent"],
      ["zwischen fünfundsechzig und siebzig", "zwischen 65 und 70"],
      ["hundertvierundvierzig Module", "144 Modulen"],
      ["dreiundsechzig Kilowatt Peak", "63 Kilowatt-Peak"],
      ["siebzigtausend Kilowattstunde", "70.000 Kilowattstunden"],
      ["fünfundzwanzigtausend", "25.000"],
      ["bei grad mal", "bei gerade mal"],
      ["wirklich 'n Vorzeige-PV-Anlage", "wirklich eine Vorzeige-PV-Anlage"],
      ["ist 'n richtig", "ist ein richtig"],
      ["mal 'ne Analyse", "mal eine Analyse"],
    ],
    drop: [],
  },
  {
    id: "recruiting",
    source: { kind: "srt", file: "07_Recruiting-Elektromeister_V1.srt" },
    durationSec: 25.63,
    scenes: [[0.3, 2.3], [2.6, 5.7], [8.45, 2.9], [11.6, 4.7], [16.55, 2.9], [19.6, 3.15], [22.8, 2.83]],
    fixes: [
      ["Elektromaster", "Elektromeister"],
      ["Fotoverteilkeinlage in einfamilienhäuser", "Photovoltaikanlagen in Einfamilienhäusern"],
      ["das komplizierte Stär", "das Komplizierteste"],
      ["dann du bei uns", "dann bist du bei uns"],
      [
        "Gewerbe ein extra ein Arschchutzanschließer, Tarishaltgeräteanschließer",
        "Gewerbeanlagen anschließen, NA-Schutz anschließen, Tarifschaltgeräte anschließen.",
      ],
      ["Teamleiter das für dich", "Teamleiter. Wenn das für dich"],
      ["pascht", "passt"],
    ],
    drop: [],
  },
];

// Woerter, mit denen eine Seite nicht enden soll (haengender Artikel/Praeposition).
const DANGLING = new Set([
  "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer",
  "und", "oder", "aber", "wie", "als", "dass", "weil", "wenn", "ob",
  "bei", "von", "vom", "mit", "auf", "in", "im", "an", "am", "zu", "zum", "zur", "für", "nach", "vor", "aus",
  "nur", "auch", "noch", "dann", "so", "es", "ich", "wir", "du", "ihr", "man", "sich", "mir", "dir", "uns",
  "hier", "quasi", "jetzt", "diese", "dieser", "dieses", "unsere", "unser", "deine", "dein", "meine",
]);

// ------------------------------------------------------------ Parser

const srtTime = (s: string): number => {
  const m = s.trim().match(/^(\d+):(\d+):(\d+)[,.](\d+)$/);
  if (!m) throw new Error(`SRT-Zeit unlesbar: ${s}`);
  return +m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4] / 1000;
};

// Kunden-SRTs laufen ab 01:00:00,000 (Timecode-Nullpunkt der Kamera).
const SRT_ZERO = 3600;

const parseSrt = (file: string): Word[] => {
  const raw = fs.readFileSync(file, "utf8").replace(/\r/g, "");
  const blocks = raw.split(/\n\s*\n/);
  const words: Word[] = [];
  for (const block of blocks) {
    const lines = block.split("\n").filter((l) => l.trim() !== "");
    const timeIdx = lines.findIndex((l) => l.includes("-->"));
    if (timeIdx < 0) continue;
    const [a, b] = lines[timeIdx].split("-->");
    const start = Math.max(0, srtTime(a) - SRT_ZERO);
    const end = Math.max(start, srtTime(b) - SRT_ZERO);
    const text = lines.slice(timeIdx + 1).join(" ").trim();
    if (!text) continue;
    // Mehrwort-Cues (z. B. "Weil da", oder der Smartino-Schluss) gleichmaessig
    // ueber die Cue-Spanne verteilen — besser als alle Woerter auf einen Punkt.
    const parts = text.split(/\s+/);
    const span = Math.max(end - start, 0.12 * parts.length);
    parts.forEach((p, i) => {
      words.push({
        text: p,
        start: start + (span * i) / parts.length,
        end: start + (span * (i + 1)) / parts.length,
      });
    });
  }
  return words;
};

const parseScribe = (file: string): Word[] => {
  const json = JSON.parse(fs.readFileSync(file, "utf8")) as {
    words: Array<{ text: string; start: number; end: number }>;
  };
  return json.words
    .map((w) => ({ text: w.text.trim(), start: w.start, end: w.end }))
    .filter((w) => w.text !== "");
};

// ------------------------------------------------------------ Korrekturen

const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[.,!?;:"„“”‚‘’()]/g, "")
    .trim();

const trailingPunct = (s: string) => {
  const m = s.match(/[.,!?;:]+$/);
  return m ? m[0] : "";
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
        reps.forEach((r, k) =>
          out.push({ text: k === reps.length - 1 ? r + punct : r, start: span[k].start, end: span[k].end }),
        );
      } else {
        const step = (s1 - s0) / reps.length;
        reps.forEach((r, k) =>
          out.push({
            text: k === reps.length - 1 ? r + punct : r,
            start: s0 + step * k,
            end: s0 + step * (k + 1),
          }),
        );
      }
    } else if (punct && out.length > 0) {
      // Phrase entfaellt — Satzzeichen wandert ans vorige Wort.
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
  for (const d of cfg.drop ?? []) w = applyPhrase(w, d, null);
  for (const [from, to] of cfg.fixes) w = applyPhrase(w, from, to);
  return w;
};

// ------------------------------------------------------------ Gruppierung

const isSentenceEnd = (t: string) => /[.!?]$/.test(t);
const hasComma = (t: string) => /[,;:]$/.test(t);
const charCount = (ws: Word[]) => ws.reduce((n, w) => n + w.text.length, 0) + Math.max(0, ws.length - 1);

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

  // Einzelwoerter nicht allein stehen lassen: an den Nachbarn haengen, wenn
  // dort Platz ist und keine lange Pause dazwischen liegt.
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

  // Haengende Funktionswoerter („… der | andere sagt") ans naechste Blatt
  // schieben, solange dort Platz ist und keine Pause dazwischen liegt.
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

  // Satzanfaenge gross schreiben (ASR liefert nach Cue-Grenzen oft klein).
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

// ------------------------------------------------------------ Ausgabe

const fmt = (t: number) => t.toFixed(2).padStart(6);

// Sichtbarkeit einer Seite gegen die Szenen-Sperrzeiten — gleiche Rechnung wie
// in Subtitles.tsx (Frames, Math.floor fuer Szenen, Math.round fuer Seiten).
const FPS = 30;
const MIN_GAP_FRAMES = 15;
const MIN_VISIBLE_FRAMES = 10;

const freeWindows = (scenes: Scene[], durationSec: number) => {
  const ranges = scenes
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

const run = (cfg: (typeof VIDEOS)[number]) => {
  const srcFile =
    cfg.source.kind === "srt"
      ? path.join(TRANSKRIPT, cfg.source.file)
      : path.join(CACHE, cfg.source.file);
  const raw = cfg.source.kind === "srt" ? parseSrt(srcFile) : parseScribe(srcFile);
  console.log(`\n== ${cfg.id}  (${cfg.source.kind}: ${cfg.source.file}, ${raw.length} Woerter)`);
  const words = clean(raw, cfg);
  const pages = group(words);

  const r3 = (n: number) => Math.round(n * 1000) / 1000;
  const json = {
    video: cfg.id,
    source: cfg.source.file,
    generated: new Date().toISOString().slice(0, 10),
    pages: pages.map((p) => ({
      start: r3(p.start),
      end: r3(p.end),
      tokens: p.tokens.map((t) => ({ text: t.text, start: r3(t.start), end: r3(t.end) })),
    })),
  };
  fs.mkdirSync(OUT_SRC, { recursive: true });
  fs.mkdirSync(OUT_INTERN, { recursive: true });
  fs.writeFileSync(path.join(OUT_SRC, `${cfg.id}.json`), JSON.stringify(json, null, 1) + "\n");
  fs.writeFileSync(path.join(OUT_INTERN, `${cfg.id}.json`), JSON.stringify(json, null, 1) + "\n");

  const windows = freeWindows(cfg.scenes, cfg.durationSec);
  const lines = pages.map(
    (p, i) =>
      `${String(i + 1).padStart(3)}  ${fmt(p.start)} – ${fmt(p.end)}  ${visibility(p, windows)} ${p.tokens.map((t) => t.text).join(" ")}`,
  );
  const visibleCount = pages.filter((p) => visibility(p, windows).trim() !== "·").length;
  const winTxt = windows.map((w) => `${(w.from / FPS).toFixed(2)}–${(w.to / FPS).toFixed(2)}`).join(", ");
  const head =
    `# ${cfg.id} — ${cfg.source.file}\n# ${pages.length} Seiten, ${words.length} Woerter; ` +
    `${visibleCount} Seiten (ganz oder teils) sichtbar\n# freie Fenster (s): ${winTxt || "keine"}\n` +
    `# Spalte: SICHT = ganz sichtbar, nn% = teilweise, · = liegt komplett unter einer Animation\n`;
  const txt = `${head}\n${lines.join("\n")}\n`;
  console.log(head);
  fs.writeFileSync(path.join(OUT_INTERN, `${cfg.id}.txt`), txt);
  console.log(lines.join("\n"));
};

const wanted = process.argv.slice(2);
for (const cfg of VIDEOS) {
  if (wanted.length && !wanted.includes(cfg.id)) continue;
  run(cfg);
}

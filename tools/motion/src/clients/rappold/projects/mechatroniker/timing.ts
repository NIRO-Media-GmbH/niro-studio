// ============================================================
// Rappold Video 2 — Untertitel-Timing (Satzfenster, Seitenwechsel, Wort-Einblendung)
// ============================================================
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

// Ausblenden nur in Sprechpausen: reicht die Zeit nach dem letzten Wort nicht, wird hart
// gewechselt (0 Frames) — nie während laufender Sprache blenden (Befund 16.09.: 11 Sätze).
export const ausblendFrames = (satz: Satz, worte: Wort[], fenster: Fenster, fps: number): number =>
  Math.max(0, Math.min(AUSBLEND_FRAMES, fenster.bis - Math.ceil(worte[satz.bis].end * fps - 1e-6)));

export const sichtbareSaetze = (saetze: Satz[], worte: Wort[], fps: number) => {
  const aktiv = saetze.filter((s) => !s.aus);
  return aktiv.map((satz, k) => ({ satz, fenster: satzFenster(satz, worte, aktiv[k + 1] ?? null, fps) }));
};

// Nächste Seite erst, wenn ihr erstes Wort beginnt UND das letzte Wort der Seite davor 0,4 s stand
// Override (wechselSek je Seite) z. B. damit ein Seitenwechsel genau auf einem Schnitt liegt —
// nie vor dem Wortanfang − Vorlauf.
const wechselSek = (satz: Satz, worte: Wort[], k: number): number => {
  const p = satz.seiten[k];
  const frueh = worte[p].start - VORLAUF_SEK;
  const override = satz.wechselSek?.[k];
  if (override !== undefined) return Math.max(frueh, override);
  return Math.max(frueh, worte[p - 1].start - VORLAUF_SEK + MIN_LETZTES_WORT_SEK);
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

// Erstes Frame (Wortanfang − 0,08 s) zeigt das Wort schon mit 1/dauer Deckkraft —
// sonst bleibt beim Seitenwechsel ein leeres Frame stehen (Befund 16.09.: 22 Stellen)
export const einblendung = (start: number, frame: number, fps: number, dauer = EINBLEND_FRAMES): number => {
  const ab = Math.round((start - VORLAUF_SEK) * fps);
  return Math.min(1, Math.max(0, (frame - ab + 1) / dauer));
};

// Erstes Wort einer Seite steht sofort voll, damit der Seitenwechsel nicht durch ein
// (fast) leeres Frame flackert; die weiteren Wörter blenden über EINBLEND_FRAMES auf.
export const wortDeckkraft = (start: number, ersteDerSeite: boolean, frame: number, fps: number): number =>
  einblendung(start, frame, fps, ersteDerSeite ? 1 : EINBLEND_FRAMES);

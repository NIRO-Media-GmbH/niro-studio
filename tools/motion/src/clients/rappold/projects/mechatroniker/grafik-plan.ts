// ============================================================
// Rappold Video 2 — Grafik-Plan „Freie Typo" (Zeiten in Frames des Schnitts V1)
// Inhalte belegt: siehe Spec docs/superpowers/specs/2026-09-16-rappold-video2-animation-design.md
// Blaue Glyphen nur auf dunklem Grund (T-Shirts) — auf B-Roll weiß + blaue Linie (Lesbarkeits-Check 16.09.)
// Feedback 16.09. nachmittags: Namen raus, CTA als eigene Farbkarte nach dem Schnitt (Übergang in Endcard.tsx).
// ============================================================
export const DAUER_FRAMES = 1565; // Schnitt V1 1440 + CTA-Karte 125
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
  ohneLinie?: boolean;
  linienFarbe?: Farbe; // Standard blau; auf der blauen CTA-Karte weiß
  zeilen: TitelZeile[];
  unterzeile?: Segment[];
  abdunkeln?: number;
  stehenBleiben?: boolean; // kein Ausstieg (CTA-Karte bis zum Ende)
};
const w = (text: string): Segment => ({ text, farbe: "weiss" });
const b = (text: string): Segment => ({ text, farbe: "blau" });

export const GRAFIKEN: Grafik[] = [
  { id: "g-seit-1911", von: 138, bis: 186, y: 1110, ausrichtung: "links", abdunkeln: 0.5, kicker: "AUTOHAUS RAPPOLD · BLAUFELDEN", zeilen: [{ segmente: [w("SEIT 1911")], px: 190 }] },
  { id: "g-frage", von: 366, bis: 396, y: 800, ausrichtung: "links", zeilen: [{ segmente: [w("WERKSTATT")], px: 150 }, { segmente: [w("WIE 1995?")], px: 150 }] },
  { id: "g-antwort", von: 396, bis: 429, y: 810, ausrichtung: "links", abdunkeln: 0.45, zeilen: [{ segmente: [w("MODERNER")], px: 120 }, { segmente: [w("ARBEITSPLATZ.")], px: 120 }] },
  { id: "g-familie", von: 1034, bis: 1083, y: 860, ausrichtung: "links", zeilen: [{ segmente: [w("FAMILIENGEFÜHRT")], px: 96 }], unterzeile: [w("RUND 30 MITARBEITENDE")] },
  { id: "g-qualitaet", von: 1085, bis: 1145, y: 860, ausrichtung: "rechts", zeilen: [{ segmente: [b("QUALITÄT")], px: 150 }, { segmente: [w("VOR QUANTITÄT")], px: 110 }] },
  { id: "g-teamgeist", von: 1252, bis: 1296, y: 830, ausrichtung: "links", abdunkeln: 0.4, zeilen: [{ segmente: [w("ECHTER")], px: 140 }, { segmente: [w("TEAMGEIST")], px: 140 }] },
  // CTA-Karte (Farbfläche ab Schnitt-Ende)
  { id: "g-karte-titel", von: 1444, bis: DAUER_FRAMES, y: 730, ausrichtung: "links", kicker: "OFFENE STELLE", linienFarbe: "weiss", zeilen: [{ segmente: [w("KFZ-MECHATRONIKER")], px: 88 }], unterzeile: [w("(M/W/D)")], stehenBleiben: true },
  { id: "g-karte-eintragen", von: 1452, bis: DAUER_FRAMES, y: 1040, ausrichtung: "links", ohneLinie: true, zeilen: [{ segmente: [w("JETZT EINTRAGEN")], px: 110 }], stehenBleiben: true },
];

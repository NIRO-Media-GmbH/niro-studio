// ============================================================
// Rappold Video 2 — Untertitel-Plan (Sätze, Seiten, Heroes, blaue Wörter)
// Wortindizes beziehen sich auf WORTE in daten-generiert.ts (Schnitt V1, korrigiert).
// Regeln: ganze Sinneinheiten, keine Dopplung mit Grafiken (aus = Grafik-ID),
// Lage fest je Seite, Lagewechsel nur auf einem Schnitt (Feedback 16.09.: Sprung bei 0:27).
// ============================================================
export type HeroFarbe = "weiss" | "blau";
export type Satz = {
  id: string;
  text: string; // Kontrolle: muss den Wörtern von..bis entsprechen
  von: number; // Wortindex (inklusive)
  bis: number;
  seiten: number[]; // Wortindex je Seitenanfang; erster = von
  hero?: { von: number; bis: number; farbe: HeroFarbe }[]; // höchstens eins je Seite
  blau?: number[]; // Grundzeilen-Wörter in Blau (nur auf Personen-Einstellungen)
  aus?: string; // Satz erscheint nicht — ID der Grafik, die ihn trägt
  gross?: boolean; // erstes Wort groß (Übergabe: Grafik trägt den Satzanfang)
  nachlaufSek?: number; // Standzeit nach dem letzten Wort (Standard 0,6 s)
  unterkanteJeSeite?: Record<number, number>; // abweichende Lage einer Seite (Gesicht unten im Bild)
  wechselSek?: Record<number, number>; // Seitenwechsel auf einen Schnitt legen
  abdunkeln?: number; // zeilengroße Abdunklung 0–0,5
};

export const SAETZE: Satz[] = [
  { id: "ut-01", text: "Also ich war in anderen Betrieben, da war man eine Nummer, war man ersetzbar.", von: 0, bis: 13, seiten: [0, 6, 11], hero: [{ von: 10, bis: 10, farbe: "weiss" }, { von: 13, bis: 13, farbe: "weiss" }] },
  { id: "ut-02", text: "Hier weiß man, man ist wichtig.", von: 14, bis: 19, seiten: [14], hero: [{ von: 19, bis: 19, farbe: "blau" }], nachlaufSek: 0.14 },
  { id: "ut-03", text: "Ich bin der Hannes.", von: 20, bis: 23, seiten: [20] },
  { id: "ut-04", text: "Bin seit 2013 hier im Autohaus Rappold.", von: 24, bis: 30, seiten: [24], nachlaufSek: 0.1, abdunkeln: 0.35 },
  { id: "ut-05", text: "Ich bin Christos.", von: 31, bis: 33, seiten: [31] },
  { id: "ut-06", text: "Ich bin Kfz-Mechatroniker, bin seit fünf Jahren beim Autohaus Rappold.", von: 34, bis: 43, seiten: [34, 37], nachlaufSek: 0.2, abdunkeln: 0.35 },
  { id: "ut-07", text: "Wenn ich jetzt hier morgens in die Halle reinkomme, denke ich mir: „Ja, geil, wieder am Arbeitsplatz.“", von: 44, bis: 60, seiten: [44, 53] },
  { id: "ut-08", text: "Also es ist wirklich so, ich freue mich auf die Arbeit.", von: 61, bis: 71, seiten: [61], blau: [71] },
  // Seite 2 liegt in E24 (Christos' Gesicht unten im Bild) oben — Wechsel genau auf dem Schnitt 26,72 s
  { id: "ut-09", text: "Man hat viel Platz, man kann sich ausbreiten, man hat so seinen eigenen Platz, wo man sagt: „Okay, hier arbeite ich.“", von: 72, bis: 92, seiten: [72, 80, 86], hero: [{ von: 74, bis: 75, farbe: "weiss" }], unterkanteJeSeite: { 2: 1083 }, wechselSek: { 2: 26.72 }, abdunkeln: 0.35 },
  { id: "ut-10", text: "Hier habe ich in einer halben Stunde ein Auto vermessen und eingestellt.", von: 93, bis: 104, seiten: [93, 100], abdunkeln: 0.5 },
  { id: "ut-11", text: "Früher dauerte es halt eine Stunde bis anderthalb.", von: 105, bis: 112, seiten: [105] },
  { id: "ut-12", text: "Und auch mit der Geschäftsleitung, wenn es da mal Probleme gibt, persönliche oder auch geschäftliche Probleme, kann man eigentlich immer hingehen und fragen, reden.", von: 113, bis: 136, seiten: [113, 118, 124, 129], blau: [117] },
  { id: "ut-13", text: "Man fühlt sich immer verstanden.", von: 137, bis: 141, seiten: [137], hero: [{ von: 141, bis: 141, farbe: "weiss" }], abdunkeln: 0.4 },
  { id: "ut-14", text: "Da wird dir auch keine Steine in den Weg gelegt, wenn du mal zwei Stunden länger brauchst.", von: 142, bis: 158, seiten: [142, 152], abdunkeln: 0.3 },
  { id: "ut-15", text: "Mit den Leuten will ich weiterhin zusammenarbeiten, weil es hat drei Jahre super gepasst und dann weiß ich auch, dass es länger hält.", von: 159, bis: 181, seiten: [159, 166, 173] },
  { id: "ut-16", text: "Also wenn du Schrauber bist und Bock auf eine moderne Werkstatt hast, komm vorbei, trag dich ein.", von: 182, bis: 198, seiten: [182, 187, 194], blau: [185] },
  { id: "ut-18", text: "Wir freuen uns auf dich.", von: 199, bis: 203, seiten: [199] },
];

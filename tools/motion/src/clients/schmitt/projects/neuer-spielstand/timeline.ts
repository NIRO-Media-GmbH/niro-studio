// ============================================================
// Schnittliste „Neuer Spielstand“ V2 — Segmente, Ton, Untertitel, HUD, Musik
// Alle Zeiten in Sekunden relativ zum Anfang des genannten Segments;
// „start“ ist der Startscreen (beginnt bei 0 s).
// Dialog = saubere Sprachdateien, auf die Scribe-Wortzeiten der Clips gelegt
// (Clip-Ton ist stumm: die Seedance-Tonspuren enthalten generierte Musik).
// Gesamtlänge 1124 Bilder = 44,96 s (Vorgabe: höchstens 45 s).
// ============================================================

export type SegmentData = {
  id: string;
  kind: "shot" | "ladescreen" | "cta" | "logo";
  src: string;
  seconds: number;
  trimStart?: number;
  kicker?: string;
  title?: string;
  hint?: string;
  perks?: string[];
  button?: string;
  url?: string;
};
export type SoundData = {
  type: "sfx" | "dialog";
  seg: string;
  at: number;
  src: string;
  volume: number;
  duration: number;
  fadeIn: number;
  fadeOut: number;
};
export type CueData = { seg: string; start: number; end: number; speaker: string; text: string };
export type HudData = {
  kind: "minimap" | "toast";
  seg: string;
  at: number;
  untilSeg: string;
  until: number;
  kicker?: string;
  text?: string;
  icon?: "pin" | "key" | "truck" | "route";
  routeSeg?: string;
  routeAt?: number;
};
export type MusicData = {
  src: string; // leer = keine Musik
  dropInSong: number; // Sekunde des Drops im Song
  hitSeg: string; // Drop landet hier …
  hitAt: number; // … bei dieser Sekunde (LKW fährt los)
  volume: number;
  duckTo: number; // Musik unter Dialog
  fadeIn: number;
  fadeOut: number;
};

export const SEGMENTS: SegmentData[] = [
  { id: "shot1", kind: "shot", src: "shots/shot1_A_take3.mp4", seconds: 5.04 },
  { id: "shot2", kind: "shot", src: "shots/shot2_B_take3.mp4", seconds: 6.04 },
  {
    id: "lade",
    kind: "ladescreen",
    src: "ladescreen/ladescreen_luca.jpg",
    seconds: 2.0,
    kicker: "Neue Quest",
    title: "Hol dir deinen Schlüssel",
    hint: "Ziel: Dispo",
  },
  // endet vor Bild 108 des Clips: dort springt die Kamera und die Disponenten verschwinden
  { id: "shot3", kind: "shot", src: "shots/shot3_A_take3.mp4", seconds: 4.53 },
  // erste Sekunde (Anlauf über den Hof) gekürzt; endet weiter auf dem letzten Bild = Startbild von 4b
  { id: "shot4a", kind: "shot", src: "shots/shot4a_A_take3.mp4", trimStart: 1.0, seconds: 4.04 },
  { id: "shot4b", kind: "shot", src: "shots/shot4b_A_take2.mp4", seconds: 5.04 },
  // Luftbild: endet, sobald Gebäude und LKW auf der Straße zu sehen sind
  { id: "shot5", kind: "shot", src: "shots/shot5_A_take1.mp4", seconds: 4.2 },
  // Fahrerkabine, Take 3 (Take 1 zeigt ab 4,4 s eine Palme vor dem Fenster)
  { id: "shot6", kind: "shot", src: "shots/shot6_A_take3.mp4", seconds: 4.96 },
  {
    id: "cta",
    kind: "cta",
    src: "cta/cta_bg.jpg",
    seconds: 3.8,
    kicker: "Dein Spielstand wartet",
    title: "Berufskraftfahrer",
    hint: "(m/w/d)",
    perks: ["30 Tage Urlaub", "Job Rad", "Werkswohnung"], // wörtlich laut schmitt.jobs (Stand 11.09.2026)
    button: "Jetzt bewerben",
    url: "schmitt.jobs",
  },
  // Logo-Datei fehlt noch (leer = Wortmarken-Platzhalter)
  { id: "logo", kind: "logo", src: "", seconds: 2.0, url: "schmitt.jobs" },
];

const sfx = (seg: string, at: number, name: string, volume: number, duration: number, fadeIn = 0.01, fadeOut = 0.08): SoundData => ({
  type: "sfx",
  seg,
  at,
  src: `sfx/norm/${name}.wav`,
  volume,
  duration,
  fadeIn,
  fadeOut,
});
const dialog = (seg: string, at: number, name: string, duration: number): SoundData => ({
  type: "dialog",
  seg,
  at,
  src: `audio/dialog/${name}.wav`,
  volume: 1,
  duration,
  fadeIn: 0.01,
  fadeOut: 0.05,
});

export const SOUNDS: SoundData[] = [
  // Startscreen: Menü erscheint, Cursor-Ticks, Einrasten, Zoom-through
  sfx("start", 0.22, "ui_whoosh_in2", 0.45, 1.2, 0.02, 0.3),
  ...[1.0, 1.28, 1.56, 1.84, 2.12].map((at) => sfx("start", at, "ui_tick", 0.35, 0.5)),
  sfx("start", 2.3, "ui_confirm2", 0.55, 1.2, 0.01, 0.3),
  sfx("start", 2.95, "ui_zoom", 0.6, 1.5, 0.02, 0.45),
  // Shot 1: Hof am Abend, Schritte, Ausbilderin
  sfx("shot1", 0.0, "amb_hof", 0.5, 8.0, 0.4, 1.2),
  sfx("shot1", 1.7, "schritte_asphalt", 0.35, 6.0, 0.3, 0.8),
  dialog("shot1", 0.04, "shot1_ausbilderin_helena", 1.84),
  // Shot 2: Glastür, Foyer, Dialog im Gehen
  sfx("shot2", 2.6, "glastuer", 0.45, 2.5, 0.01, 0.3),
  sfx("shot2", 3.5, "amb_foyer", 0.5, 2.54, 0.4, 0.3),
  dialog("shot2", 2.33, "shot2_ausbilderin_helena", 2.48),
  dialog("shot2", 4.72, "shot2_luca_jasper", 1.28),
  // Ladescreen
  sfx("lade", 0.0, "lade_swell", 0.45, 2.0, 0.15, 0.35),
  // Shot 3: Dispo, Schlüssel, Item-Hinweis, „Gute Fahrt!“
  sfx("shot3", 0.0, "amb_dispo", 0.45, 4.53, 0.25, 0.12),
  sfx("shot3", 2.55, "schluessel", 0.7, 1.5, 0.01, 0.2),
  sfx("shot3", 2.8, "item_erhalten", 0.35, 1.0, 0.01, 0.15),
  dialog("shot3", 3.66, "shot3_disponentin", 1.04),
  // Shot 4a: Hof, Stapler, Schritte, Fahrertür
  sfx("shot4a", 0.0, "amb_hof", 0.45, 8.0, 0.08, 2.0),
  sfx("shot4a", 0.0, "stapler", 0.3, 3.0, 0.1, 1.0),
  sfx("shot4a", 0.0, "schritte_asphalt", 0.35, 2.4, 0.05, 0.3),
  sfx("shot4a", 2.3, "lkw_tuer", 0.6, 3.5, 0.01, 0.4),
  // Shot 4b: Motorstart und Anfahren (hier landet der Musik-Drop)
  sfx("shot4b", 0.0, "lkw_start", 0.55, 6.0, 0.05, 1.0),
  // Shot 5: LKW auf der Straße aus der Luft
  sfx("shot5", 0.0, "lkw_strasse", 0.55, 4.2, 0.8, 0.25),
  // Shot 6: Fahrerkabine, Luca spricht in die Kamera
  sfx("shot6", 0.0, "fahrerkabine", 0.45, 4.96, 0.03, 0.3),
  dialog("shot6", 2.44, "shot6_luca_jasper", 2.32),
  // CTA: Einblenden, Benefits, Button
  sfx("cta", 0.0, "cta_whoosh", 0.55, 1.2, 0.01, 0.25),
  ...[0.9, 1.05, 1.2].map((at) => sfx("cta", at, "perk_blip", 0.4, 0.6)),
  sfx("cta", 2.6, "ui_confirm2", 0.6, 1.2, 0.01, 0.3),
  // Logo: Sting beginnt kurz vor der Logo-Karte und klingt bis zum Ende aus
  sfx("cta", 3.55, "logo_sting", 0.65, 2.25, 0.02, 0.6),
];

export const CUES: CueData[] = [
  { seg: "shot1", start: 0.04, end: 2.46, speaker: "Ausbilderin", text: "Erster Tag? Dann komm mal mit." },
  { seg: "shot2", start: 2.38, end: 3.93, speaker: "Ausbilderin", text: "Dein Schlüssel hängt in der Dispo." },
  { seg: "shot2", start: 3.98, end: 4.71, speaker: "Ausbilderin", text: "Hol ihn dir!" },
  { seg: "shot2", start: 4.76, end: 5.79, speaker: "Luca", text: "Bin dabei." },
  { seg: "shot3", start: 3.68, end: 4.53, speaker: "Disponentin", text: "Gute Fahrt!" },
  { seg: "shot6", start: 2.42, end: 3.73, speaker: "Luca", text: "Worauf wartest du?" },
  { seg: "shot6", start: 3.78, end: 4.96, speaker: "Luca", text: "Bewirb dich jetzt!" },
];

export const HUD: HudData[] = [
  { kind: "minimap", seg: "shot1", at: 0.6, untilSeg: "shot2", until: 5.79 },
  { kind: "toast", seg: "shot1", at: 0.9, untilSeg: "shot1", until: 3.4, kicker: "Standort", text: "Schmitt Gruppe · Vellberg", icon: "pin" },
  { kind: "minimap", seg: "shot3", at: 0.3, untilSeg: "shot3", until: 4.53 },
  { kind: "toast", seg: "shot3", at: 2.8, untilSeg: "shot3", until: 4.53, kicker: "Neues Item", text: "LKW-Schlüssel erhalten", icon: "key" },
  { kind: "minimap", seg: "shot4a", at: 0.0, untilSeg: "shot4b", until: 4.9, routeSeg: "shot4b", routeAt: 1.25 },
  { kind: "toast", seg: "shot4a", at: 0.35, untilSeg: "shot4a", until: 2.4, kicker: "Ziel", text: "Steig in deinen LKW", icon: "truck" },
  { kind: "toast", seg: "shot4b", at: 1.25, untilSeg: "shot4b", until: 4.3, kicker: "Neue Route", text: "Route zum Ziel", icon: "route" },
];

// Song fehlt noch (nur mit legaler Datei): Drop auf das Anfahren in Shot 4b legen
export const MUSIC: MusicData = {
  src: "",
  dropInSong: 0,
  hitSeg: "shot4b",
  hitAt: 1.25,
  volume: 0.6,
  duckTo: 0.3,
  fadeIn: 1.5,
  fadeOut: 1.8,
};

// ============================================================
// Schnittliste „Neuer Spielstand“ V3 — Segmente, Ton, Untertitel, HUD, Quest-Log, Musik
// Alle Zeiten in Sekunden relativ zum Anfang des genannten Segments;
// „start“ ist der Startscreen (beginnt bei 0 s).
// Dialog = saubere Sprachdateien, auf die Scribe-Wortzeiten der Clips gelegt
// (Clip-Ton ist stumm: die Seedance-Tonspuren enthalten generierte Musik).
// V3 nach Kundenfeedback (16.09.): Quest-Kette mit Papieren im Büro und Beladen im Lager,
// Schlusssatz „Und um das nächste Level zu erreichen: Bewirb dich jetzt!“, echtes Logo.
// V4 (16.09.): harte Schnitte versteckt — Übergangsclips Büro → Halle → Hof und Luftbild → Kabine,
// CTA als Pausemenü auf dem letzten Kabinenbild, Ausklang in die Logo-Karte; Musik „NEXT ONE“
// aus der NIRO-Library (Artlist) mit Drop auf dem Einrasten im Startscreen und beim Losfahren.
// ============================================================

export type SegmentData = {
  id: string;
  kind: "shot" | "ladescreen" | "cta" | "logo";
  src: string;
  seconds: number;
  trimStart?: number;
  overlap?: number;
  pause?: boolean;
  kicker?: string;
  title?: string;
  hint?: string;
  quests?: string[];
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
export type QuestData = {
  label: string;
  steps: { seg: string; at: number }[];
  progress?: { seg: string; from: number; to: number };
  doneSeg: string;
  doneAt: number;
};
export type QuestLogData = {
  title: string;
  fromSeg: string;
  from: number;
  untilSeg: string;
  until: number;
  quests: QuestData[];
};
export type MusicData = {
  src: string; // leer = keine Musik
  dropInSong: number; // Sekunde des Drops im Song
  hitSeg: string; // Drop landet hier …
  hitAt: number; // … bei dieser Sekunde (LKW fährt los)
  volume: number;
  boostAfterHit: number; // Faktor ab dem Drop
  duckTo: number; // Musik unter Dialog
  fadeIn: number;
  fadeOut: number;
};

// Zeitpunkte der neuen Clips (Sekunden im Clip, nach Sichtung der Takes gesetzt)
// Take 3: Klemmbrett mit Papieren (passt zur Beladeszene), Übergabe 2,7–3,1 s;
// Satz ungekürzt auf die Lippen gelegt (Scribe Clip „Deine“ 0,68 s, „Fahrt“ bis 3,28 s; Versatz 0,65 s ±0,07)
const S3B = { clip: "shots/shot3b_A_take3.mp4", seconds: 5.04, line: 0.65, handover: 2.9, done: 3.35 };
// Take 1: Stapler lädt die Palette in den Auflieger, Luca hakt ab, Daumen hoch bei 3,6 s, Kamera fährt aufs Klemmbrett
const LADEN = { clip: "shots/laden_A_take1.mp4", seconds: 5.04, done: 3.7 };
// Satz in zwei Teilen auf die Lippen gelegt (Scribe Clip: „Und“ 2,52 s, „bewirb“ 4,86 s; Abweichung ≤ 80 ms)
const S6 = { clip: "shots/shot6_L_take1.mp4", seconds: 6.04, part1: 2.5, part2: 4.65 };
// Übergangsclips (Seedance, Start = letztes Bild davor, Ziel = erstes Bild danach), 97 Bilder = 4,04 s
// Brücke 1 Take 1: Flur → Halle, ruhig (Szenenwert ≤ 0,19 beim Schwenk aufs Rampentor), Ziel-SSIM 0,68
// Brücke 2 Take 3 (5 s, 121 Bilder): Takes 1–2 mit Sprung/Palmen, 4–5 mit schwachem Start- bzw. Zielbild;
// Take 3 durchgehend (≤ 0,04), Start-SSIM 0,96, Ziel-SSIM 0,69
// Brücke 3 Take 3: Sturzflug hinter den LKW, seitlich an die Kabine, durchs Beifahrerfenster (≤ 0,07), Ziel-SSIM 0,78
const BR1 = { clip: "shots/bruecke1_take1.mp4", seconds: 4.04 };
const BR2 = { clip: "shots/bruecke2_take3.mp4", seconds: 5.04 };
const BR3 = { clip: "shots/bruecke3_take3.mp4", seconds: 4.04 };
// Überblendungen: am Brückenende 0,16 s (Zielbild nicht pixelgenau), am Brückenanfang 0,12 s (Startbild neu gerendert)
const XF = 0.16;
const XF_IN = 0.12;

export const SEGMENTS: SegmentData[] = [
  { id: "shot1", kind: "shot", src: "shots/shot1_A_take3.mp4", seconds: 5.04 },
  { id: "shot2", kind: "shot", src: "shots/shot2_B_take3.mp4", seconds: 6.04 },
  {
    id: "lade",
    kind: "ladescreen",
    src: "ladescreen/ladescreen_luca.jpg",
    // Länge so gewählt, dass zwischen der Landung in Shot 1 (3,3 s) und dem Losfahren genau 42,0 s liegen
    // = Abstand der beiden Drops im Song (87 Bilder; Shot 4b beginnt bei Bild 1101 → Drop bei 45,30 s)
    seconds: 3.48,
    kicker: "Neue Quests",
    title: "Deine erste Tour",
    quests: ["Schlüssel & Papiere holen", "LKW beladen", "Losfahren"],
  },
  // Schlüssel vom Brett: endet auf Clip-Bild 83, bevor die Disponentin spricht (= Startbild von Shot 3b)
  { id: "shot3", kind: "shot", src: "shots/shot3_A_take3.mp4", seconds: 3.52 },
  { id: "shot3b", kind: "shot", src: S3B.clip, seconds: S3B.seconds },
  // Kamera folgt Luca durch den Flur in die Halle
  { id: "bruecke1", kind: "shot", src: BR1.clip, seconds: BR1.seconds, overlap: XF_IN },
  { id: "laden", kind: "shot", src: LADEN.clip, seconds: LADEN.seconds, overlap: XF },
  // Luca geht aus der Halle auf den Hof
  { id: "bruecke2", kind: "shot", src: BR2.clip, seconds: BR2.seconds, overlap: XF_IN },
  // erste Sekunde (Anlauf über den Hof) gekürzt = Zielbild der Brücke; endet auf dem letzten Bild = Startbild von 4b
  { id: "shot4a", kind: "shot", src: "shots/shot4a_A_take3.mp4", trimStart: 1.0, seconds: 4.04, overlap: XF },
  { id: "shot4b", kind: "shot", src: "shots/shot4b_A_take2.mp4", seconds: 5.04 },
  // Luftbild: endet auf Clip-Bild 99 = Startbild der Brücke in die Kabine
  { id: "shot5", kind: "shot", src: "shots/shot5_A_take1.mp4", seconds: 4.2 },
  // Sturzflug aus der Luft durchs Beifahrerfenster in die Kabine
  { id: "bruecke3", kind: "shot", src: BR3.clip, seconds: BR3.seconds, overlap: XF_IN },
  { id: "shot6", kind: "shot", src: S6.clip, seconds: S6.seconds, overlap: XF },
  {
    id: "cta",
    kind: "cta",
    src: "cta/cta_shot6_ende.jpg", // letztes Kabinenbild → Pausemenü ohne Bildsprung
    pause: true,
    seconds: 3.8,
    kicker: "Dein Spielstand wartet",
    title: "Berufskraftfahrer",
    hint: "(m/w/d)",
    perks: ["30 Tage Urlaub", "Job Rad", "Werkswohnung"], // wörtlich laut schmitt.jobs (Stand 11.09.2026)
    button: "Jetzt bewerben",
    url: "schmitt.jobs",
  },
  // offizielles Logo von schmitt-vellberg.de (einfarbig weiß), Freigabe 16.09.2026
  { id: "logo", kind: "logo", src: "logo/logo_gruppe_weiss.svg", seconds: 2.0, url: "schmitt.jobs" },
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
  // Ladescreen: Swell, je Quest-Zeile ein Tick
  sfx("lade", 0.0, "lade_swell", 0.45, 3.0, 0.15, 0.9),
  ...[0.45, 0.61, 0.77].map((at) => sfx("lade", at, "ui_tick", 0.3, 0.5)),
  // Shot 3 + 3b: Dispo-Atmo bis in den Flur, Schlüssel (Quest 1/2), Papiere (Quest 2/2 ✓)
  sfx("shot3", 0.0, "amb_dispo_lang", 0.45, 3.52 + S3B.seconds + 1.2, 0.25, 1.2),
  // Hand am Brett ab Clip-Bild 70 (2,92 s), Schlüssel ab Bild 81 in der Hand (3,38 s)
  sfx("shot3", 2.95, "schluessel", 0.7, 1.5, 0.01, 0.2),
  sfx("shot3", 3.35, "perk_blip", 0.35, 0.6),
  sfx("shot3b", S3B.handover - 0.3, "papier_mappe", 0.6, 1.5, 0.01, 0.25),
  sfx("shot3b", S3B.done, "quest_done", 0.45, 1.2, 0.01, 0.25),
  dialog("shot3b", S3B.line, "shot3b_disponentin_vera", 2.64),
  // Brücke 1: Schritte im Flur, die Halle öffnet sich; Hallen-Atmo läuft bis auf den Hof
  sfx("bruecke1", 0.0, "flur_zur_halle", 0.5, 4.0, 0.2, 0.4),
  sfx("bruecke1", 2.2, "amb_halle", 0.45, 10.0, 1.0, 1.2),
  // Beladen: Stapler, Quest ✓
  sfx("laden", 0.15, "halle_laden", 0.6, LADEN.seconds - 0.15, 0.05, 0.3),
  sfx("laden", LADEN.done, "quest_done", 0.45, 1.2, 0.01, 0.25),
  // Brücke 2: raus auf den Hof; Hof-Atmo blendet ein
  sfx("bruecke2", 0.0, "halle_zum_hof", 0.55, 4.0, 0.2, 0.4),
  sfx("bruecke2", 2.0, "amb_hof", 0.45, 8.0, 1.5, 2.0),
  // Shot 4a: Stapler, Schritte, Fahrertür
  sfx("shot4a", 0.0, "stapler", 0.3, 3.0, 0.3, 1.0),
  sfx("shot4a", 0.0, "schritte_asphalt", 0.35, 2.4, 0.2, 0.3),
  sfx("shot4a", 2.3, "lkw_tuer", 0.6, 3.5, 0.01, 0.4),
  // Shot 4b: Motorstart und Anfahren (hier landet der Musik-Drop), Quest „Losfahren“ ✓
  sfx("shot4b", 0.0, "lkw_start", 0.55, 6.0, 0.05, 1.0),
  sfx("shot4b", 1.25, "quest_done", 0.4, 1.2, 0.01, 0.25),
  // Shot 5 + Brücke 3: LKW auf der Straße aus der Luft, Sturzflug in die Kabine
  sfx("shot5", 0.0, "lkw_strasse", 0.55, 6.0, 0.8, 1.6),
  sfx("bruecke3", 0.0, "luft_sturzflug", 0.65, 4.0, 0.3, 0.4),
  // Shot 6: Fahrerkabine, Luca spricht in die Kamera
  sfx("shot6", 0.0, "fahrerkabine", 0.45, 6.0, 0.5, 0.3),
  dialog("shot6", S6.part1, "shot6_level_teil1", 1.95),
  dialog("shot6", S6.part2, "shot6_level_teil2", 1.17),
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
  { seg: "shot3b", start: 0.6, end: 2.32, speaker: "Disponentin", text: "Deine Papiere." },
  { seg: "shot3b", start: 2.42, end: 3.88, speaker: "Disponentin", text: "Gute Fahrt!" },
  { seg: "shot6", start: S6.part1 - 0.04, end: S6.part2 + 0.1, speaker: "Luca", text: "Und um das nächste Level zu erreichen:" },
  { seg: "shot6", start: S6.part2 + 0.15, end: S6.seconds, speaker: "Luca", text: "Bewirb dich jetzt!" },
];

export const HUD: HudData[] = [
  { kind: "minimap", seg: "shot1", at: 0.6, untilSeg: "shot2", until: 5.79 },
  { kind: "toast", seg: "shot1", at: 0.9, untilSeg: "shot1", until: 3.4, kicker: "Standort", text: "Schmitt Gruppe · Vellberg", icon: "pin" },
  { kind: "minimap", seg: "shot3", at: 0.3, untilSeg: "shot4b", until: 4.9, routeSeg: "shot4b", routeAt: 1.25 },
];

export const QUESTLOG: QuestLogData = {
  title: "Deine erste Tour",
  fromSeg: "shot3",
  from: 0.25,
  untilSeg: "shot4b",
  until: 3.4,
  quests: [
    {
      label: "Schlüssel & Papiere holen",
      steps: [
        { seg: "shot3", at: 3.35 },
        { seg: "shot3b", at: S3B.handover },
      ],
      doneSeg: "shot3b",
      doneAt: S3B.done,
    },
    { label: "LKW beladen", steps: [], progress: { seg: "laden", from: 0.3, to: LADEN.done }, doneSeg: "laden", doneAt: LADEN.done },
    { label: "Losfahren", steps: [], doneSeg: "shot4b", doneAt: 1.25 },
  ],
};

// Frank Bentley – „NEXT ONE“ (Instrumental), Artlist, aus der NIRO-Musik-Library (Recruiting & Ads), 120 BPM.
// Drops nach kurzer Stille bei 32,075 s und 74,075 s (Hüllkurve gemessen) → zweiter Drop aufs Anfahren,
// der erste landet damit auf der Landung in Shot 1 (3,3 s, Zoom-through mit Lichtblitz).
// Lautheit: Song −9,4 LUFS, Dialog −19,4 LUFS → Bett ≈ −22 LUFS (0,24), unter Dialog −8 dB (0,4).
export const MUSIC: MusicData = {
  src: "musik/frank_bentley_next_one_instrumental.wav",
  dropInSong: 74.075,
  hitSeg: "shot4b",
  hitAt: 1.26,
  volume: 0.24,
  boostAfterHit: 1.25,
  duckTo: 0.4,
  fadeIn: 0.6,
  fadeOut: 2.0,
};

/**
 * Werkzeuge.tsx — subtil herabfallende Werkzeug-Silhouetten (MAN Wartezimmervideo)
 * =============================================================================
 * David-Review 2 / Punkt 10: Während der Spotlight-Momente sollen sehr dezent
 * Werkzeug-Silhouetten (Ring-/Maulschlüssel, Sechskant-Mutter, Zahnrad,
 * Schraube, Steckschlüssel-Nuss, Zange) SEHR LANGSAM von oben herabsinken.
 * Nie ablenkend, nie dominant über dem Video-Fenster.
 *
 * NUTZUNG (Beispiel in Composition.tsx, INNERHALB des Spotlight-Layers und
 * IMMER HINTER/UNTER dem Video-Fenster einsortieren — also vor dem Fenster
 * im JSX, damit es im z-Stack darunter liegt):
 *
 *     const tLok = frame / fps;                 // Sekunden seit Spotlight-Start
 *     const dauer = s.ende - s.start;           // Spotlight-Länge in Sekunden
 *     <Werkzeuge
 *       progress={tLok / dauer}                 // 0..1 über den Spotlight
 *       opacity={0.07 * env}                    // env = Spotlight-Hüllkurve
 *       farbe={WHITE}                           // oder MAN_RED
 *       zyklen={dauer / 26}                     // konstantes Tempo je Spotlight
 *     />
 *
 * - `opacity` mit der Spotlight-Hüllkurve multiplizieren → weiches Ein-/Ausblenden.
 * - `progress` darf beliebig laufen (auch > 1 oder < 0): jedes Werkzeug wird
 *   modulo gewrappt UND ist am Wrap-Punkt sowohl ausgeblendet als auch komplett
 *   außerhalb des Bildes → keine Sprünge, loop-sicher.
 * - Deterministisch: feste Tabelle `WERKZEUG_INSTANZEN`, kein Math.random zur
 *   Laufzeit (Remotion muss Frame-für-Frame identisch rendern).
 * - Rein präsentational: kein useCurrentFrame, keine Remotion-Imports — die
 *   Zeit kommt ausschließlich über `progress` von außen.
 */

import React from "react";

// Bühnenmaß der 16:9-Komposition (Composition.tsx: BASE_W / BASE_H)
const STAGE_W = 1920;
const STAGE_H = 1080;

// --- Formen: flache, geschlossene Vektor-Silhouetten, technisch-präzise ------
// Jede Form hat ihre eigene viewBox; mehrere Pfade pro Form vereinigen sich
// visuell (gleiche Füllfarbe). Löcher (Muttern-Bohrung, Ringschlüssel-Auge,
// Zahnrad-Nabe) liegen als Sub-Pfad IM SELBEN `d` und werden per evenodd
// ausgestanzt.

export type WerkzeugForm =
  | "ringschluessel"
  | "mutter"
  | "zahnrad"
  | "schraube"
  | "nuss"
  | "zange";

interface FormDef {
  /** viewBox-Maß [Breite, Höhe] */
  vb: [number, number];
  /** ein oder mehrere Pfade, alle mit fill-rule evenodd gerendert */
  pfade: string[];
}

/**
 * Zahnrad-Kontur (Trapez-Zähne auf Fußkreis-Bögen) + Nabenbohrung.
 * Reine Funktion, wird EINMAL beim Modul-Load ausgewertet → deterministisch.
 */
const zahnradPfad = (
  zaehne: number,
  rAussen: number,
  rFuss: number,
  rNabe: number,
): string => {
  const cx = 50;
  const cy = 50;
  const schritt = (Math.PI * 2) / zaehne;
  const wKopf = schritt * 0.2;
  const wFuss = schritt * 0.34;
  const P = (r: number, a: number) =>
    `${(cx + r * Math.cos(a)).toFixed(2)} ${(cy + r * Math.sin(a)).toFixed(2)}`;

  let ersterFuss = "";
  let d = "";
  for (let k = 0; k < zaehne; k++) {
    const a = -Math.PI / 2 + k * schritt;
    const p0 = P(rFuss, a - wFuss);
    const p1 = P(rAussen, a - wKopf);
    const p2 = P(rAussen, a + wKopf);
    const p3 = P(rFuss, a + wFuss);
    if (k === 0) {
      ersterFuss = p0;
      d += `M ${p0}`;
    } else {
      d += ` A ${rFuss} ${rFuss} 0 0 1 ${p0}`;
    }
    d += ` L ${p1} L ${p2} L ${p3}`;
  }
  d += ` A ${rFuss} ${rFuss} 0 0 1 ${ersterFuss} Z`;
  // Nabenbohrung (evenodd stanzt sie aus)
  d +=
    ` M ${cx} ${cy - rNabe}` +
    ` A ${rNabe} ${rNabe} 0 1 0 ${cx} ${cy + rNabe}` +
    ` A ${rNabe} ${rNabe} 0 1 0 ${cx} ${cy - rNabe} Z`;
  return d;
};

export /**
 * Baut eine geschlossene Kontur aus einer Mittellinie mit punktweiser
 * Halbbreite [x, y, halbbreite]. Für Werkzeuge, die sich entlang einer Achse
 * verjüngen und verbreitern (Zangenschenkel). Reine Funktion, Modul-Load.
 */
const bandPfad = (punkte: readonly (readonly [number, number, number])[]): string => {
  const n = punkte.length;
  const rechts: string[] = [];
  const links: string[] = [];
  for (let i = 0; i < n; i++) {
    const [x, y] = punkte[i];
    const [xv, yv] = punkte[Math.max(0, i - 1)];
    const [xn, yn] = punkte[Math.min(n - 1, i + 1)];
    const dx = xn - xv;
    const dy = yn - yv;
    const len = Math.hypot(dx, dy) || 1;
    // Normale zur Tangente
    const nx = dy / len;
    const ny = -dx / len;
    const hw = punkte[i][2];
    rechts.push(`${(x + nx * hw).toFixed(2)} ${(y + ny * hw).toFixed(2)}`);
    links.push(`${(x - nx * hw).toFixed(2)} ${(y - ny * hw).toFixed(2)}`);
  }
  links.reverse();
  return `M ${rechts.join(" L ")} L ${links.join(" L ")} Z`;
};

/** Zangenschenkel: Backe oben (geschlossen, keilförmig), massiger Kopf am
 *  Gelenk, gespreizter Griff unten. Die beiden Schenkel berühren sich an der
 *  Spitze (x = 37) und verschmelzen am Gelenk zum Kopf. */
const ZANGE_SCHENKEL: readonly (readonly [number, number, number])[] = [
  [33.5, 6, 3.5],
  [34.5, 26, 5.5],
  [35.5, 46, 8],
  [35, 62, 12],
  [41, 82, 7.5],
  [50, 108, 6.5],
  [57, 132, 6],
];

/** an der Mittelachse x = 37 gespiegelt */
const spiegle = (
  pts: readonly (readonly [number, number, number])[],
  achse: number,
): readonly (readonly [number, number, number])[] =>
  pts.map(([x, y, hw]) => [2 * achse - x, y, hw] as const);

export const FORMEN: Record<WerkzeugForm, FormDef> = {
  /** Ring-Maul-Schlüssel: Ringauge (Sechskant-Loch) oben, verjüngter Schaft,
   *  Maul mit tiefem Schlitz unten. */
  ringschluessel: {
    vb: [32, 150],
    pfade: [
      // Ringauge oben: Außenkreis r14 um (16,17), Sechskant-Loch R8,4
      "M 2 17 A 14 14 0 1 0 30 17 A 14 14 0 1 0 2 17 Z " +
        "M 16 8.6 L 23.27 12.8 L 23.27 21.2 L 16 25.4 L 8.73 21.2 L 8.73 12.8 Z",
      // Schaft, leicht verjüngt
      "M 10.6 26 L 21.4 26 L 20.6 110 L 11.4 110 Z",
      // Maul unten: gerundeter Kopf, tiefer und leicht angestellter Schlitz
      "M 16 112 A 14 14 0 0 1 30 126 L 30 148 L 22 148 L 21 125.5 " +
        "L 11 125.5 L 10 148 L 2 148 L 2 126 A 14 14 0 0 1 16 112 Z",
    ],
  },

  /** Sechskant-Mutter: Schlüsselweite über Eck, zentrale Bohrung. */
  mutter: {
    vb: [100, 100],
    pfade: [
      "M 50 4 L 89.84 27 L 89.84 73 L 50 96 L 10.16 73 L 10.16 27 Z " +
        "M 50 27 A 23 23 0 1 0 50 73 A 23 23 0 1 0 50 27 Z",
    ],
  },

  /** Zahnrad: 12 Zähne, Nabenbohrung. */
  zahnrad: {
    vb: [100, 100],
    pfade: [zahnradPfad(12, 47, 37, 15)],
  },

  /** Sechskantschraube: Kopf, Bund, Gewindeschaft mit Zahnflanken, Spitze. */
  schraube: {
    vb: [44, 120],
    pfade: [
      "M 12 4 L 32 4 L 42 18 L 32 32 L 12 32 L 2 18 Z",
      "M 15 31 L 29 31 L 29 39 L 15 39 Z",
      "M 16 39 L 28 39 L 26 46 L 28 53 L 26 60 L 28 67 L 26 74 L 28 81 " +
        "L 26 88 L 28 95 L 26 102 L 27 108 L 22 116 L 17 108 L 18 102 " +
        "L 16 95 L 18 88 L 16 81 L 18 74 L 16 67 L 18 60 L 16 53 L 18 46 Z",
    ],
  },

  /** Steckschlüssel-Nuss, Draufsicht: Außenring + Sechskant-Aufnahme. */
  nuss: {
    vb: [100, 100],
    pfade: [
      "M 50 6 A 44 44 0 1 0 50 94 A 44 44 0 1 0 50 6 Z " +
        "M 50 16 A 34 34 0 1 0 50 84 A 34 34 0 1 0 50 16 Z " +
        "M 50 22 L 74.25 36 L 74.25 64 L 50 78 L 25.75 64 L 25.75 36 Z",
    ],
  },

  /** Kombizange: zwei gekreuzte Schenkel, Backen oben geöffnet, Gelenkbolzen. */
  zange: {
    vb: [74, 142],
    pfade: [
      // Schenkel A: Backe oben links, Kopf am Gelenk, Griff unten rechts
      bandPfad(ZANGE_SCHENKEL),
      // Schenkel B: an x = 37 gespiegelt
      bandPfad(spiegle(ZANGE_SCHENKEL, 37)),
    ],
  },
};

// --- Instanz-Tabelle (fest, deterministisch) --------------------------------
// x   = Canvas-x der Mitte (Bühne 1920 breit); Schwerpunkt bewusst LINKS
//       (Grafikfläche) und RECHTS AUSSEN, nur wenige Teile queren die Mitte
//       672–1248 — dort liegt im Spotlight das Video-Fenster.
// size = längste Kante in px (60–220)
// v    = Fallgeschwindigkeit relativ (Anteil einer vollen Bahn je Zyklus)
// ph   = Startphase 0..1 (verteilt die Teile über die Bahn)
// rot  = Startdrehung in Grad
// dreh = Eigendrehung über eine volle Bahn in Grad (bewusst wenige Grad)
// drift= horizontale Drift über eine volle Bahn in px
// blur = Weichzeichnung in px (Tiefenstaffelung: kleiner/ferner = weicher)
// op   = relative Deckkraft (multipliziert die Gesamt-Opazität)

interface WerkzeugInstanz {
  form: WerkzeugForm;
  x: number;
  size: number;
  v: number;
  ph: number;
  rot: number;
  dreh: number;
  drift: number;
  blur: number;
  op: number;
}

const WERKZEUG_INSTANZEN: readonly WerkzeugInstanz[] = [
  // --- linke Bildhälfte (Grafikfläche) ---
  { form: "ringschluessel", x: 128, size: 208, v: 0.62, ph: 0.07, rot: -14, dreh: 9, drift: 16, blur: 3, op: 1.0 },
  { form: "mutter", x: 296, size: 96, v: 0.38, ph: 0.52, rot: 12, dreh: -7, drift: -12, blur: 5, op: 0.72 },
  { form: "zahnrad", x: 214, size: 150, v: 0.5, ph: 0.81, rot: 6, dreh: 11, drift: 9, blur: 4, op: 0.85 },
  { form: "schraube", x: 430, size: 176, v: 0.55, ph: 0.29, rot: 21, dreh: -8, drift: -14, blur: 3, op: 0.9 },
  { form: "nuss", x: 372, size: 74, v: 0.31, ph: 0.66, rot: -9, dreh: 6, drift: 11, blur: 6, op: 0.6 },
  { form: "zange", x: 560, size: 196, v: 0.58, ph: 0.14, rot: -17, dreh: 10, drift: -9, blur: 3, op: 0.95 },
  { form: "mutter", x: 78, size: 132, v: 0.45, ph: 0.38, rot: 27, dreh: -5, drift: 13, blur: 4, op: 0.8 },
  { form: "ringschluessel", x: 618, size: 88, v: 0.34, ph: 0.9, rot: 33, dreh: 7, drift: -7, blur: 6, op: 0.62 },
  { form: "zahnrad", x: 470, size: 64, v: 0.27, ph: 0.2, rot: -4, dreh: 12, drift: 6, blur: 7, op: 0.55 },
  { form: "schraube", x: 168, size: 108, v: 0.42, ph: 0.73, rot: -25, dreh: 6, drift: -11, blur: 5, op: 0.7 },

  // --- Mitte: nur kleine, sehr weiche, sehr schwache Teile (Fenster-Zone) ---
  { form: "mutter", x: 812, size: 70, v: 0.29, ph: 0.44, rot: 15, dreh: -6, drift: 8, blur: 8, op: 0.4 },
  { form: "nuss", x: 1094, size: 62, v: 0.24, ph: 0.86, rot: -11, dreh: 5, drift: -6, blur: 9, op: 0.34 },

  // --- rechte Bildhälfte / rechter Rand ---
  { form: "zahnrad", x: 1712, size: 184, v: 0.6, ph: 0.11, rot: 8, dreh: -10, drift: -15, blur: 3, op: 1.0 },
  { form: "ringschluessel", x: 1458, size: 142, v: 0.48, ph: 0.6, rot: 24, dreh: 8, drift: 10, blur: 4, op: 0.82 },
  { form: "schraube", x: 1856, size: 96, v: 0.36, ph: 0.33, rot: -19, dreh: -7, drift: 12, blur: 6, op: 0.66 },
  { form: "zange", x: 1332, size: 168, v: 0.53, ph: 0.95, rot: 13, dreh: 9, drift: -8, blur: 4, op: 0.88 },
  { form: "mutter", x: 1620, size: 78, v: 0.3, ph: 0.24, rot: -30, dreh: 5, drift: 7, blur: 7, op: 0.58 },
  { form: "nuss", x: 1790, size: 128, v: 0.44, ph: 0.69, rot: 5, dreh: -9, drift: -10, blur: 4, op: 0.76 },
] as const;

// --- Helfer -----------------------------------------------------------------

/** Sanfte 0→1-Kurve (smoothstep), geklemmt. */
const glatt = (t: number): number => {
  const c = t < 0 ? 0 : t > 1 ? 1 : t;
  return c * c * (3 - 2 * c);
};

/** Modulo, das auch für negative Werte in [0,1) landet. */
const wrap01 = (v: number): number => ((v % 1) + 1) % 1;

/** Ein-/Ausblendbreite am Bahnanfang/-ende (Anteil der Bahn). */
const KANTE = 0.16;

// --- Komponente -------------------------------------------------------------

export interface WerkzeugeProps {
  /** Fortschritt, üblicherweise 0..1 über den Spotlight. Beliebige Werte
   *  erlaubt (wird gewrappt), monoton steigend erwartet. */
  progress: number;
  /** Gesamt-Deckkraft, Zielkorridor 0,04–0,09. Default 0,07.
   *  Zum Ein-/Ausblenden einfach mit der Spotlight-Hüllkurve multiplizieren. */
  opacity?: number;
  /** Silhouetten-Farbe, z. B. "#FFFFFF" oder MAN-Rot "#E30045". Default weiß. */
  farbe?: string;
  /** Wie viele volle Fallbahnen ein Werkzeug mit v=1 über progress 0..1
   *  zurücklegt. Default 1. Für gleiches Tempo in verschieden langen
   *  Spotlights: `dauerInSekunden / 26`. */
  zyklen?: number;
  /** Bühnenmaß, Default 1920×1080 (16:9-Master). */
  breite?: number;
  hoehe?: number;
}

/**
 * Herabsinkende Werkzeug-Silhouetten für die Spotlight-Momente.
 * Füllt den Elternbereich (position: absolute, inset: 0), keine Pointer-Events.
 */
export const Werkzeuge: React.FC<WerkzeugeProps> = ({
  progress,
  opacity = 0.07,
  farbe = "#FFFFFF",
  zyklen = 1,
  breite = STAGE_W,
  hoehe = STAGE_H,
}) => {
  if (opacity <= 0.0005) return null;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      {WERKZEUG_INSTANZEN.map((w, i) => {
        const def = FORMEN[w.form];
        const [vbW, vbH] = def.vb;
        const lang = Math.max(vbW, vbH);
        const bW = (w.size * vbW) / lang;
        const bH = (w.size * vbH) / lang;

        // Bahn: von oberhalb des Bildes bis unterhalb, u = 0..1
        const u = wrap01(progress * w.v * zyklen + w.ph);
        const ueber = Math.max(bW, bH) * 0.75 + 60;
        const y = -ueber + u * (hoehe + 2 * ueber);
        const x = (w.x / STAGE_W) * breite + w.drift * (u - 0.5);
        const rot = w.rot + w.dreh * (u - 0.5);

        // Am Bahnanfang/-ende auf 0 → Wrap ist unsichtbar (zusätzlich liegt
        // das Teil dort komplett außerhalb des Bildes). Loop-sicher.
        const fade = glatt(u / KANTE) * glatt((1 - u) / KANTE);
        const op = opacity * w.op * fade;
        if (op <= 0.0005) return null;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - bW / 2,
              top: y - bH / 2,
              width: bW,
              height: bH,
              opacity: op,
              filter: `blur(${w.blur}px)`,
              transform: `rotate(${rot.toFixed(3)}deg)`,
              willChange: "transform",
            }}
          >
            <svg
              width={bW}
              height={bH}
              viewBox={`0 0 ${vbW} ${vbH}`}
              xmlns="http://www.w3.org/2000/svg"
              style={{ display: "block", overflow: "visible" }}
            >
              {def.pfade.map((d, k) => (
                <path key={k} d={d} fill={farbe} fillRule="evenodd" />
              ))}
            </svg>
          </div>
        );
      })}
    </div>
  );
};

export default Werkzeuge;

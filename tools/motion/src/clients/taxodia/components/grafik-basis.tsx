// ============================================================
// Taxodia x Steuerkanzlei Ludwig — Bausteine der Grafikebene (15.09.2026)
// Helle Karten im Look von taxodia.de (Weiß, Schwarz, Grün), Akzent je Marke:
// Taxodia-Grün für Taxodia-Fakten und Flammann, Ludwig-Grün für die Kanzlei.
// CI gemessen (computed styles, 15.09.): taxodia.de/ueberblick → Grün #9ABC44,
// Band #7B9636, Überschriften-Grün #667D2D, Flächen #F8F9F2 / #E2E9C9, Schrift „Como"
// (Kaufschrift, Webfont-Lizenz) → Ersatz Urbanist (Google Fonts, OFL; engster Vergleich).
// lbl-bw.de/netzwerk → Grün #73AA17, Dunkelgrün #125746.
// Raster 1920×1080, Komposition skaliert auf 3840×2160.
// ============================================================

import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { loadFont as loadUrbanist } from "@remotion/google-fonts/Urbanist";

export const { fontFamily: URBANIST } = loadUrbanist("normal", {
  weights: ["500", "700", "800"],
  subsets: ["latin", "latin-ext"],
});

// --- CI ---
export const TAXODIA_GRUEN = "#9ABC44";
export const TAXODIA_BAND = "#7B9636";
export const TAXODIA_TIEF = "#667D2D";
export const TAXODIA_HELL = "#E2E9C9";
export const TAXODIA_CREME = "#F8F9F2";
export const LUDWIG_GRUEN = "#73AA17";
export const LUDWIG_TIEF = "#125746";
export const SCHWARZ = "#000000";

// --- Raster ---
export const BASE_W = 1920;
export const BASE_H = 1080;
export const RAND_X = 112;
export const RAND_UNTEN = 118;

export const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const EASE_OUT = Easing.bezier(0.2, 0.7, 0.2, 1);
export const EASE_IN = Easing.in(Easing.cubic);

export const rein = (frame: number, start: number, dauer: number) =>
  interpolate(frame, [start, start + dauer], [0, 1], { ...CLAMP, easing: EASE_OUT });

/** firm-settle: 0,92 → 1,02 → 1 */
export const setzen = (frame: number, start: number) =>
  interpolate(frame, [start, start + 8, start + 13], [0.92, 1.02, 1], { ...CLAMP, easing: EASE_OUT });

export function hexA(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export type Marke = "taxodia" | "ludwig";

export function markenFarben(m: Marke) {
  return m === "taxodia"
    ? { akzent: TAXODIA_GRUEN, tief: TAXODIA_TIEF, linie: `linear-gradient(180deg, ${TAXODIA_GRUEN}, ${TAXODIA_BAND})` }
    : { akzent: LUDWIG_GRUEN, tief: LUDWIG_TIEF, linie: `linear-gradient(180deg, ${LUDWIG_GRUEN}, ${LUDWIG_TIEF})` };
}

export type Position = "unten-links" | "unten-rechts";

// ------------------------------------------------------------
// Helle Karte: Wipe von links + Rise, Abgang schneller (Doktrin: 0,6 s rein / 0,36 s raus)
// Keine CSS-Border (Alpha-Falle), Akzentbalken als eigene Fläche.
// ------------------------------------------------------------

export const HelleKarte: React.FC<{
  dauer: number;
  marke: Marke;
  position?: Position;
  minBreite?: number;
  radius?: number;
  padding?: string;
  children: React.ReactNode;
}> = ({ dauer, marke, position = "unten-links", minBreite, radius = 18, padding = "32px 44px 34px 52px", children }) => {
  const frame = useCurrentFrame();
  const { linie } = markenFarben(marke);
  const ab = interpolate(frame, [dauer - 10, dauer - 1], [0, 1], { ...CLAMP, easing: EASE_IN });
  const k = rein(frame, 0, 15);
  const wipe = interpolate(k, [0, 1], [100, 0]);
  const y = interpolate(k, [0, 1], [24, 0]) + ab * 14;
  const links = position === "unten-links";
  return (
    <div
      style={{
        position: "absolute",
        ...(links ? { left: RAND_X } : { right: RAND_X }),
        bottom: RAND_UNTEN,
        minWidth: minBreite,
        transform: `translateY(${y}px)`,
        opacity: 1 - ab,
        // Wipe von der Außenkante zur Bildmitte; Rand für den Schatten
        clipPath: links
          ? `inset(-60px calc(${wipe}% - ${(1 - wipe / 100) * 90}px) -110px -90px round ${radius}px)`
          : `inset(-60px -90px -110px calc(${wipe}% - ${(1 - wipe / 100) * 90}px) round ${radius}px)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: radius,
          background: hexA("#FFFFFF", 0.96),
          boxShadow: `0 20px 56px ${hexA("#141A08", 0.3)}`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 9,
          borderRadius: `${radius}px 0 0 ${radius}px`,
          background: linie,
        }}
      />
      <div style={{ position: "relative", padding, fontFamily: URBANIST, color: SCHWARZ }}>{children}</div>
    </div>
  );
};

// ------------------------------------------------------------
// Text-Bausteine (Animationen relativ zum Karten-Start)
// ------------------------------------------------------------

export const Kicker: React.FC<{ text: string; marke: Marke; start?: number; groesse?: number; sperrung?: number }> = ({
  text,
  marke,
  start = 6,
  groesse = 19,
  sperrung = 2.8,
}) => {
  const frame = useCurrentFrame();
  const k = rein(frame, start, 12);
  return (
    <div
      style={{
        fontWeight: 800,
        fontSize: groesse,
        letterSpacing: sperrung,
        textTransform: "uppercase",
        color: markenFarben(marke).tief,
        whiteSpace: "nowrap",
        opacity: k,
        transform: `translateY(${(1 - k) * 10}px)`,
      }}
    >
      {text}
    </div>
  );
};

/** Wortweise Kaskade; mehrere Zeilen laufen als eine durchgehende Kaskade. Wörter in `gruen` bekommen die Markenfarbe. */
export const WortKaskade: React.FC<{
  zeilen: string[];
  start: number;
  versatz?: number;
  groesse?: number;
  gewicht?: number;
  zeilenhoehe?: number;
  sperrung?: number;
  marginTop?: number;
  farbe?: string;
  gruen?: string[];
  gruenFarbe?: string;
  ausrichtung?: "left" | "center" | "right";
}> = ({
  zeilen,
  start,
  versatz = 3,
  groesse = 50,
  gewicht = 700,
  zeilenhoehe = 1.08,
  sperrung = -0.6,
  marginTop = 14,
  farbe = SCHWARZ,
  gruen = [],
  gruenFarbe = TAXODIA_GRUEN,
  ausrichtung = "left",
}) => {
  const frame = useCurrentFrame();
  let index = 0;
  return (
    <div style={{ marginTop, fontWeight: gewicht, fontSize: groesse, lineHeight: zeilenhoehe, letterSpacing: sperrung, textAlign: ausrichtung }}>
      {zeilen.map((zeile, zi) => {
        const woerter = zeile.split(" ");
        return (
          <div key={zi} style={{ whiteSpace: "nowrap" }}>
            {woerter.map((wort, wi) => {
              const w = rein(frame, start + index * versatz, 11);
              index += 1;
              return (
                <span
                  key={wi}
                  style={{
                    display: "inline-block",
                    marginRight: wi < woerter.length - 1 ? groesse * 0.24 : 0,
                    color: gruen.includes(wort) ? gruenFarbe : farbe,
                    opacity: w,
                    transform: `translateY(${(1 - w) * 16}px)`,
                  }}
                >
                  {wort}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

export function wortAnzahl(zeilen: string[]): number {
  return zeilen.reduce((n, z) => n + z.split(" ").length, 0);
}

export const Textzeile: React.FC<{
  text: string;
  start: number;
  groesse?: number;
  gewicht?: number;
  farbe?: string;
  sperrung?: number;
  marginTop?: number;
  ausrichtung?: "left" | "center" | "right";
}> = ({ text, start, groesse = 28, gewicht = 500, farbe = hexA("#000000", 0.78), sperrung = 0.2, marginTop = 10, ausrichtung = "left" }) => {
  const frame = useCurrentFrame();
  const b = rein(frame, start, 11);
  return (
    <div
      style={{
        marginTop,
        fontWeight: gewicht,
        fontSize: groesse,
        lineHeight: 1.25,
        letterSpacing: sperrung,
        color: farbe,
        whiteSpace: "nowrap",
        textAlign: ausrichtung,
        opacity: b,
        transform: `translateY(${(1 - b) * 8}px)`,
      }}
    >
      {text}
    </div>
  );
};

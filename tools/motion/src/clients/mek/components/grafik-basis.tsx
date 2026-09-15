// ============================================================
// MEK — gemeinsame Bausteine der Imagefilm-Grafikebene
// Glas-Karte (Wipe + Rise + Abgang), Kicker, Akzentlinie, Wort-Kaskade,
// Textzeilen. Werte = Zertifikats-Karten v1 (14.09.2026), 1920er-Raster.
// ============================================================

import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";

export const { fontFamily: ROBOTO } = loadRoboto("normal", {
  weights: ["300", "700"],
  subsets: ["latin", "latin-ext"],
});

// --- CI (Logo-SVGs der Häuser, Messung 01.09.) ---
export const NAVY_ELISABETH = "#002854";
export const NAVY_MARIEN = "#0E335E";
export const RAMPE_HELL = "#EBECF2";
export const RAMPE_MITTE = "#B2B9CC";
export const RAMPE_TIEF = "#818DAB";
export const WARM_HELL = "#F3EADC";
export const WARM_RAND = "#E2D3BC";

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

/** firm-settle: 0,9 → 1,03 → 1 */
export const setzen = (frame: number, start: number) =>
  interpolate(frame, [start, start + 8, start + 13], [0.9, 1.03, 1], { ...CLAMP, easing: EASE_OUT });

export function hexA(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** Elisabeth kühl, Marien warm, Verbund beide (Linie läuft von kühl nach warm). */
export type Temperatur = "kuehl" | "warm" | "beide";

export function kartenFarben(t: Temperatur) {
  const warm = t === "warm";
  return {
    navyA: warm ? NAVY_MARIEN : NAVY_ELISABETH,
    navyB: warm ? NAVY_ELISABETH : NAVY_MARIEN,
    rand: warm ? WARM_RAND : RAMPE_MITTE,
    glanz: warm ? WARM_HELL : RAMPE_HELL,
    linie:
      t === "kuehl"
        ? `linear-gradient(90deg, ${RAMPE_HELL}, ${RAMPE_TIEF})`
        : t === "warm"
          ? `linear-gradient(90deg, ${WARM_HELL}, ${WARM_RAND})`
          : `linear-gradient(90deg, ${RAMPE_HELL}, ${RAMPE_TIEF} 48%, ${WARM_RAND})`,
  };
}

// ------------------------------------------------------------
// Glas-Karte: Fläche + editorial Wipe von links + Rise, Abgang schneller
// ------------------------------------------------------------

export const GlasKarte: React.FC<{
  dauer: number;
  temperatur: Temperatur;
  position?: "unten-rechts" | "unten-links" | "unten-mitte";
  versatzX?: number;
  versatzY?: number;
  /** feste Breite im 1920er-Raster; ohne Angabe passt sich die Karte dem Inhalt an */
  breite?: number;
  minBreite?: number;
  children: React.ReactNode;
}> = ({ dauer, temperatur, position = "unten-rechts", versatzX = 0, versatzY = 0, breite, minBreite, children }) => {
  const frame = useCurrentFrame();
  const { navyA, navyB, rand, glanz } = kartenFarben(temperatur);

  const abStart = dauer - 12;
  const ab = interpolate(frame, [abStart, abStart + 9], [0, 1], { ...CLAMP, easing: EASE_IN });

  const k = rein(frame, 0, 15);
  const wipe = interpolate(k, [0, 1], [100, 0]);
  const karteY = interpolate(k, [0, 1], [26, 0]) - ab * 14;

  const mitte = position === "unten-mitte";
  const seite =
    position === "unten-links"
      ? { left: RAND_X + versatzX }
      : mitte
        ? { left: `calc(50% + ${versatzX}px)` }
        : { right: RAND_X - versatzX };

  return (
    <div
      style={{
        position: "absolute",
        ...seite,
        bottom: RAND_UNTEN - versatzY,
        width: breite,
        minWidth: minBreite,
        transform: mitte ? `translate(-50%, ${karteY}px)` : `translateY(${karteY}px)`,
        opacity: 1 - ab,
        // Wipe von links; Clip-Rand am Ende −90 px, damit der Schatten nirgends hart abgeschnitten wird
        clipPath: `inset(-60px calc(${wipe}% - ${(1 - wipe / 100) * 90}px) -120px -90px round 22px)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: 22,
          background: `linear-gradient(158deg, ${hexA(navyA, 0.8)} 0%, ${hexA(navyB, 0.66)} 100%)`,
          boxShadow: `inset 0 0 0 1.5px ${hexA(rand, 0.42)}, 0 26px 70px ${hexA("#000A1E", 0.36)}`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: 22,
          background: `radial-gradient(120% 90% at 0% 0%, ${hexA(glanz, 0.14)} 0%, ${hexA(glanz, 0)} 55%)`,
        }}
      />
      <div style={{ position: "relative", padding: "38px 44px 40px 44px", fontFamily: ROBOTO, color: "#FFFFFF" }}>
        {children}
      </div>
    </div>
  );
};

// ------------------------------------------------------------
// Text-Bausteine (Animationen relativ zum Karten-Start)
// ------------------------------------------------------------

export const Kicker: React.FC<{ text: string; start?: number; groesse?: number; sperrung?: number }> = ({
  text,
  start = 7,
  groesse = 18,
  sperrung = 3.4,
}) => {
  const frame = useCurrentFrame();
  const k = rein(frame, start, 12);
  return (
    <div
      style={{
        fontWeight: 700,
        fontSize: groesse,
        letterSpacing: sperrung,
        textTransform: "uppercase",
        color: hexA("#FFFFFF", 0.8),
        whiteSpace: "nowrap",
        opacity: k,
        transform: `translateY(${(1 - k) * 12}px)`,
      }}
    >
      {text}
    </div>
  );
};

export const Akzentlinie: React.FC<{
  linie: string;
  start?: number;
  breite?: number;
  zentriert?: boolean;
  rechts?: boolean;
}> = ({ linie, start = 11, breite = 64, zentriert = false, rechts = false }) => {
  const frame = useCurrentFrame();
  const r = rein(frame, start, 12);
  return (
    <div
      style={{
        marginTop: 14,
        marginLeft: zentriert || rechts ? "auto" : undefined,
        marginRight: zentriert ? "auto" : undefined,
        width: breite,
        height: 3,
        borderRadius: 2,
        background: linie,
        transform: `scaleX(${r})`,
        transformOrigin: zentriert ? "50% 50%" : rechts ? "100% 50%" : "0 50%",
      }}
    />
  );
};

/** Wortweise Kaskade; mehrere Zeilen laufen als eine durchgehende Kaskade. */
export const WortKaskade: React.FC<{
  zeilen: string[];
  start: number;
  versatz?: number;
  groesse?: number;
  zeilenhoehe?: number;
  sperrung?: number;
  marginTop?: number;
  ausrichtung?: "left" | "center" | "right";
}> = ({ zeilen, start, versatz = 3, groesse = 52, zeilenhoehe = 1.06, sperrung = -1, marginTop = 26, ausrichtung = "left" }) => {
  const frame = useCurrentFrame();
  let index = 0;
  return (
    <div
      style={{
        marginTop,
        fontWeight: 700,
        fontSize: groesse,
        lineHeight: zeilenhoehe,
        letterSpacing: sperrung,
        textAlign: ausrichtung,
      }}
    >
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
                    marginRight: wi < woerter.length - 1 ? groesse * 0.25 : 0,
                    opacity: w,
                    transform: `translateY(${(1 - w) * 18}px)`,
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
  deckkraft?: number;
  sperrung?: number;
  marginTop?: number;
  ausrichtung?: "left" | "center" | "right";
}> = ({ text, start, groesse = 29, deckkraft = 0.94, sperrung = 0.3, marginTop = 12, ausrichtung = "left" }) => {
  const frame = useCurrentFrame();
  const b = rein(frame, start, 11);
  return (
    <div
      style={{
        marginTop,
        fontWeight: 300,
        fontSize: groesse,
        lineHeight: 1.25,
        letterSpacing: sperrung,
        color: hexA("#FFFFFF", deckkraft),
        whiteSpace: "nowrap",
        textAlign: ausrichtung,
        opacity: b,
        transform: `translateY(${(1 - b) * 10}px)`,
      }}
    >
      {text}
    </div>
  );
};
